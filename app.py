import hashlib
import re
from collections import Counter
from datetime import datetime
from io import BytesIO

import pdfplumber
import qrcode
import requests
import streamlit as st
from PIL import Image
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate

# =========================
# CONFIG
# =========================
st.set_page_config(page_title="CitatIA", page_icon="📚", layout="wide")

# 🔗 URL da API do Google Sheets (Apps Script)
URL_GOOGLE_SHEETS = "https://script.google.com/macros/s/AKfycbyHRCrD5-A_JHtaUDXsGWQ22ul9ml5vvK3YYFzIE43jjCdip0dBMFH_Jmd8w971PLte/exec"

# APIs bibliográficas
SEMANTIC_API = "https://api.semanticscholar.org/graph/v1/paper/search"
CROSSREF_API = "https://api.crossref.org/works"

# User-Agent recomendado pelo Crossref (inclua email/contato)
CROSSREF_HEADERS = {
    "User-Agent": "CitatIA/1.0 (mailto:contato@exemplo.com)"
}

# Stopwords simples (PT + algumas EN comuns)
STOP_WORDS = {
    "a","o","os","as","um","uma","uns","umas","de","do","da","dos","das","em","no","na","nos","nas","por","para","com",
    "sem","sob","sobre","entre","e","ou","mas","que","se","sua","seu","suas","seus","ao","aos","à","às","como","mais",
    "menos","muito","muitos","muita","muitas","já","ainda","também","tão","não","sim","ser","estar","ter","há","foi",
    "são","era","foram","este","esta","isso","essa","aquele","aquela","aquilo","their","the","and","from","this","that",
    "into","with","without","for","of","in","on","to","an","is","are","was","were","be","been"
}

AREA_KEYWORDS = {
    "Inteligência Artificial e Computação": {"ai", "machine", "learning", "deep", "neural", "algorithm", "computing", "data"},
    "Saúde e Biomedicina": {"health", "clinical", "disease", "medical", "patient", "cancer", "biomedical", "drug"},
    "Sustentabilidade e Meio Ambiente": {"climate", "sustainability", "carbon", "energy", "environment", "renewable", "emission"},
    "Negócios e Economia": {"economy", "finance", "market", "business", "management", "innovation", "productivity"},
    "Educação e Ciências Sociais": {"education", "social", "policy", "learning", "inequality", "public", "society"},
}


# =========================
# GOOGLE SHEETS
# =========================
def salvar_email_google_sheets(nome: str, email: str, codigo_verificacao: str) -> None:
    dados = {"nome": nome, "email": email, "codigo": codigo_verificacao}
    try:
        response = requests.post(
            URL_GOOGLE_SHEETS,
            json=dados,
            headers={"Content-Type": "application/json"},
            timeout=20,
        )
        if response.text.strip().lower() == "sucesso":
            st.success("✅ E-mail, nome e código registrados com sucesso!")
        else:
            st.error(f"❌ Erro ao salvar dados no Google Sheets: {response.text}")
    except requests.RequestException as exc:
        st.error(f"❌ Erro na conexão com o Google Sheets: {exc}")


def verificar_codigo_google_sheets(codigo_digitado: str) -> bool:
    try:
        response = requests.get(f"{URL_GOOGLE_SHEETS}?codigo={codigo_digitado}", timeout=20)
        return response.text.strip() == "Valido"
    except requests.RequestException as exc:
        st.error(f"❌ Erro na conexão com o Google Sheets: {exc}")
        return False


def gerar_codigo_verificacao(texto: str) -> str:
    return hashlib.md5(texto.encode("utf-8")).hexdigest()[:10].upper()


# =========================
# TEXT / NLP
# =========================
def infer_areas_from_text(texto: str):
    words = set(re.findall(r"\b\w+\b", (texto or "").lower()))
    detected = [area for area, kws in AREA_KEYWORDS.items() if words.intersection(kws)]
    return detected if detected else ["Multidisciplinar"]


def clean_html_tags(txt: str) -> str:
    return re.sub(r"<[^>]+>", " ", txt or "")


def get_year_from_crossref(item: dict):
    for key in ["published-print", "published-online", "created", "issued"]:
        date_parts = item.get(key, {}).get("date-parts", [])
        if date_parts and date_parts[0]:
            return date_parts[0][0]
    return None


def identify_theme(user_text: str):
    words = re.findall(r"\b\w+\b", user_text or "")
    keywords = [w.lower() for w in words if w.lower() not in STOP_WORDS and len(w) > 3]
    top = Counter(keywords).most_common(12)
    tema = ", ".join([w for w, _ in top]) if top else "Tema não identificado (texto insuficiente)"
    return tema, [w for w, _ in top]


def extract_text_from_pdf_bytes(pdf_bytes: bytes) -> str:
    if not pdf_bytes:
        return ""
    text_chunks = []
    try:
        with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
            for page in pdf.pages:
                text_chunks.append(page.extract_text() or "")
    except Exception:
        return ""
    return "\n".join(text_chunks).strip()


# =========================
# APIS (com cache)
# =========================
@st.cache_data(ttl=60 * 30, show_spinner=False)  # 30 min
def get_popular_articles(query: str, limit: int = 30):
    articles = []

    # Semantic Scholar
    semantic_params = {
        "query": query,
        "limit": limit,
        "fields": "title,abstract,url,externalIds,citationCount,year,fieldsOfStudy",
    }
    try:
        resp = requests.get(SEMANTIC_API, params=semantic_params, timeout=20)
        if resp.status_code == 200:
            for item in resp.json().get("data", []):
                title = item.get("title", "") or ""
                abstract = item.get("abstract") or ""
                articles.append(
                    {
                        "title": title,
                        "abstract": abstract,
                        "phrase": f"{title}. {abstract}",
                        "doi": (item.get("externalIds") or {}).get("DOI", "N/A"),
                        "link": item.get("url", "N/A"),
                        "citationCount": item.get("citationCount", 0) or 0,
                        "year": item.get("year"),
                        "areas": item.get("fieldsOfStudy") or infer_areas_from_text(f"{title} {abstract}"),
                        "source": "SemanticScholar",
                    }
                )
    except requests.RequestException:
        pass

    # Crossref
    crossref_params = {"query": query, "rows": limit, "sort": "is-referenced-by-count", "order": "desc"}
    try:
        resp = requests.get(CROSSREF_API, params=crossref_params, headers=CROSSREF_HEADERS, timeout=20)
        if resp.status_code == 200:
            for item in resp.json().get("message", {}).get("items", []):
                title = (item.get("title") or [""])[0] or ""
                abstract = clean_html_tags(item.get("abstract", "") or "")
                articles.append(
                    {
                        "title": title,
                        "abstract": abstract,
                        "phrase": f"{title}. {abstract}",
                        "doi": item.get("DOI", "N/A"),
                        "link": item.get("URL", "N/A"),
                        "citationCount": int(item.get("is-referenced-by-count", 0) or 0),
                        "year": get_year_from_crossref(item),
                        "areas": item.get("subject") or infer_areas_from_text(f"{title} {abstract}"),
                        "source": "Crossref",
                    }
                )
    except requests.RequestException:
        pass

    # Dedup (por DOI; senão por título)
    deduped = {}
    for a in articles:
        key = a["doi"] if a["doi"] != "N/A" else a["title"].strip().lower()
        if not key:
            continue
        if key not in deduped or a["citationCount"] > deduped[key]["citationCount"]:
            deduped[key] = a

    result = sorted(deduped.values(), key=lambda x: x.get("citationCount", 0), reverse=True)
    return result[:limit]


def extract_top_keywords(articles, limit=15):
    text = " ".join((a.get("phrase", "") or "") for a in (articles or [])[:20])
    words = re.findall(r"\b\w+\b", text.lower())
    words = [w for w in words if w not in STOP_WORDS and len(w) > 3]
    return [w for w, _ in Counter(words).most_common(limit)]


def get_publication_statistics(articles):
    years = [a.get("year") for a in (articles or []) if isinstance(a.get("year"), int)]
    yearly_counts = dict(sorted(Counter(years).items()))
    total = len(articles or [])
    current_year = datetime.now().year
    recent = sum(1 for y in years if y >= current_year - 3)
    recency_ratio = (recent / total * 100) if total else 0
    return yearly_counts, recency_ratio


def analyze_citation_landscape(articles, article_keywords):
    citations = [a.get("citationCount", 0) for a in (articles or [])]
    total_citations = sum(citations)
    mean_citations = round((total_citations / len(citations)) if citations else 0, 2)
    top_articles = sorted((articles or []), key=lambda x: x.get("citationCount", 0), reverse=True)[:10]

    area_counter = Counter()
    for item in (articles or []):
        for area in item.get("areas", []) or []:
            area_counter[area] += int(item.get("citationCount", 0) or 0)

    hot_keywords = set(extract_top_keywords(top_articles, limit=20))
    overlap = len(set(article_keywords or []).intersection(hot_keywords))
    overlap_ratio = overlap / len(article_keywords) if article_keywords else 0

    return {
        "top_articles": top_articles,
        "total_citations": total_citations,
        "mean_citations": mean_citations,
        "top_areas": area_counter.most_common(5),
        "keyword_overlap_ratio": overlap_ratio,
    }


def evaluate_article_relevance(total_articles: int, overlap_ratio: float, recency_ratio: float):
    # Heurística simples e estável (sem PyTorch)
    saturation_penalty = min(total_articles / 40, 1) * 35
    probability = 55 + (overlap_ratio * 30) + (recency_ratio * 0.25) - saturation_penalty
    probability = max(5, min(95, probability))

    if probability >= 75:
        desc = "Probabilidade alta: bom alinhamento com tópicos de maior impacto e recência favorável."
    elif probability >= 45:
        desc = "Probabilidade moderada: há potencial, mas vale reforçar novidade, método e posicionamento."
    else:
        desc = "Probabilidade baixa: o tema parece saturado e/ou pouco conectado aos tópicos mais citados recentemente."

    return round(probability, 2), desc


# =========================
# PDF REPORT
# =========================
def generate_report(tema, probabilidade, descricao, top_keywords, yearly_counts, recency_ratio, landscape, output_path="report.pdf"):
    doc = SimpleDocTemplate(output_path, pagesize=A4)
    styles = getSampleStyleSheet()
    justified = ParagraphStyle("Justified", parent=styles["BodyText"], alignment=4, spaceAfter=10)

    content = [
        Paragraph("<b>Relatório de Análise de Citação - CitatIA</b>", styles["Title"]),
        Paragraph(f"<b>Tema identificado:</b> {tema}", justified),
        Paragraph(f"<b>Aderência ao estado da arte (proxy):</b> {landscape['keyword_overlap_ratio']*100:.2f}%", justified),
        Paragraph(f"<b>Potencial do tema:</b> {probabilidade}%", justified),
        Paragraph(f"<b>Análise:</b> {descricao}", justified),
        Paragraph(f"<b>Média de citações no corpus:</b> {landscape['mean_citations']}", justified),
        Paragraph(f"<b>Total de citações no corpus:</b> {landscape['total_citations']}", justified),
        Paragraph("<b>Áreas com maior concentração de citações:</b>", styles["Heading3"]),
    ]

    for area, weighted_citations in landscape["top_areas"]:
        content.append(Paragraph(f"• {area}: {weighted_citations} citações (ponderado)", justified))

    content.append(Paragraph("<b>Tendência temporal (anos disponíveis):</b>", styles["Heading3"]))
    if yearly_counts:
        for year, count in yearly_counts.items():
            content.append(Paragraph(f"• {year}: {count} registros", justified))
    else:
        content.append(Paragraph("• Sem dados de ano suficientes nas APIs para estimar tendência.", justified))

    content.append(Paragraph(f"<b>Participação de artigos recentes (3 anos):</b> {recency_ratio:.2f}%", justified))

    content.append(Paragraph("<b>Palavras mais recorrentes nos artigos mais citados:</b>", styles["Heading3"]))
    if top_keywords:
        for word in top_keywords:
            content.append(Paragraph(f"• {word}", justified))
    else:
        content.append(Paragraph("• Nenhuma palavra-chave relevante detectada.", justified))

    content.append(Paragraph("<b>Top 10 artigos (por citações):</b>", styles["Heading3"]))
    if landscape["top_articles"]:
        for item in landscape["top_articles"]:
            content.append(
                Paragraph(
                    f"• {item.get('title','Sem título')}<br/>"
                    f"<b>Fonte:</b> {item.get('source','N/A')}<br/>"
                    f"<b>DOI:</b> {item.get('doi','N/A')}<br/>"
                    f"<b>Link:</b> {item.get('link','N/A')}<br/>"
                    f"<b>Citações:</b> {item.get('citationCount',0)}",
                    justified,
                )
            )
    else:
        content.append(Paragraph("• Nenhum artigo retornado pelas APIs no momento.", justified))

    doc.build(content)


# =========================
# PIX DONATION
# =========================
def gerar_qr_code_pix(payload: str):
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=10, border=4)
    qr.add_data(payload)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return Image.open(buffer)


def render_donation_section():
    payload = "00020126400014br.gov.bcb.pix0118peas8810@gmail.com520400005303986540520.005802BR5925PEDRO EMILIO AMADOR SALOM6013TEOFILO OTONI62200516PEASTECHNOLOGIES6304C9DB"
    st.markdown("---")
    st.markdown(
        """
        <h3 style='color: green;'>💚 Apoie Este Projeto com um Pix!</h3>
        <p>Temos custos com servidores, desenvolvimento e APIs. Se este site está te ajudando, considere uma contribuição de <strong>R$ 20,00</strong>.</p>
        <p><strong>Chave Pix:</strong> <span style='color: blue;'>peas8810@gmail.com</span></p>
        <p><strong>Nome do recebedor:</strong> PEAS TECHNOLOGIES</p>
        """,
        unsafe_allow_html=True,
    )
    st.image(gerar_qr_code_pix(payload), caption="📲 Escaneie o QR Code para doar via Pix (R$ 20,00)", width=300)
    st.success("🙏 Obrigado! Sua ajuda mantém este projeto vivo.")


# =========================
# UI
# =========================
def main():
    st.title("📚 CitatIA - Potencializador de Artigos")

    # ===== Registro
    with st.expander("📋 Registro de Usuário (opcional)", expanded=False):
        nome = st.text_input("Nome completo", key="nome")
        email = st.text_input("E-mail", key="email")
        if st.button("Salvar Dados", key="btn_salvar"):
            if nome and email:
                codigo = gerar_codigo_verificacao(email)
                salvar_email_google_sheets(nome, email, codigo)
                st.success(f"Código de verificação gerado: **{codigo}**")
            else:
                st.warning("⚠️ Preencha nome e e-mail.")

    # ===== Upload e análise
    st.subheader("📄 Enviar PDF para análise")
    uploaded_file = st.file_uploader("Envie o arquivo PDF", type="pdf")

    if uploaded_file:
        st.info("🔍 Extraindo texto do PDF...")
        pdf_bytes = uploaded_file.getvalue()
        user_text = extract_text_from_pdf_bytes(pdf_bytes)

        if not user_text or len(user_text) < 200:
            st.error("Não consegui extrair texto suficiente do PDF. Se ele for escaneado (imagem), será necessário OCR.")
            st.stop()

        tema, article_keywords = identify_theme(user_text)

        with st.spinner("Consultando bases (Semantic Scholar + Crossref)..."):
            articles = get_popular_articles(tema, limit=30)

        top_keywords = extract_top_keywords(articles, limit=15)
        landscape = analyze_citation_landscape(articles, article_keywords)
        yearly_counts, recency_ratio = get_publication_statistics(articles)
        probabilidade, descricao = evaluate_article_relevance(len(articles), landscape["keyword_overlap_ratio"], recency_ratio)

        col1, col2 = st.columns(2)
        with col1:
            st.success(f"✅ Tema identificado: {tema}")
            st.write(f"🏷️ Aderência (proxy): **{landscape['keyword_overlap_ratio']*100:.2f}%**")
            st.write(f"📈 Potencial do tema: **{probabilidade}%**")
            st.write(f"ℹ️ {descricao}")

        with col2:
            st.write("**Áreas com maior concentração de citações (ponderado):**")
            if landscape["top_areas"]:
                for area, count in landscape["top_areas"]:
                    st.write(f"• {area}: {count}")
            else:
                st.write("• Sem dados suficientes.")

            st.write("**Participação de artigos recentes (3 anos):**")
            st.write(f"• {recency_ratio:.2f}%")

        st.write("---")
        st.write("**Palavras mais recorrentes nos artigos mais citados:**")
        if top_keywords:
            st.write(", ".join(top_keywords))
        else:
            st.write("Nenhuma palavra-chave relevante encontrada.")

        st.write("---")
        st.write("**Top 10 artigos por citações:**")
        if landscape["top_articles"]:
            for item in landscape["top_articles"]:
                st.write(
                    f"• **{item.get('title','Sem título')}** "
                    f"(Citações: {item.get('citationCount',0)}) | "
                    f"DOI: {item.get('doi','N/A')} | "
                    f"Fonte: {item.get('source','N/A')}"
                )
        else:
            st.write("Nenhum artigo retornado pelas APIs.")

        # ===== PDF Report
        generate_report(tema, probabilidade, descricao, top_keywords, yearly_counts, recency_ratio, landscape)
        with open("report.pdf", "rb") as f:
            st.download_button("📥 Baixar Relatório (PDF)", f, file_name="report.pdf", mime="application/pdf")

    # ===== Verificação de código
    st.header("🔐 Verificar Autenticidade")
    codigo_digitado = st.text_input("Digite o código de verificação:", key="codigo_digitado")
    if st.button("Verificar Código", key="btn_verificar"):
        if codigo_digitado.strip() and verificar_codigo_google_sheets(codigo_digitado.strip()):
            st.success("✅ Documento Autêntico e Original!")
        else:
            st.error("❌ Código inválido ou documento não encontrado.")

    st.markdown("---\nPowered By - PEAS.Co")
    render_donation_section()


if __name__ == "__main__":
    main()

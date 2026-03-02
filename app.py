import hashlib
import math
import re
from collections import Counter, defaultdict
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
# STREAMLIT CONFIG
# =========================
st.set_page_config(page_title="CitatIA", page_icon="📚", layout="wide")

# =========================
# ENDPOINTS
# =========================
URL_GOOGLE_SHEETS = "https://script.google.com/macros/s/AKfycbyHRCrD5-A_JHtaUDXsGWQ22ul9ml5vvK3YYFzIE43jjCdip0dBMFH_Jmd8w971PLte/exec"
SEMANTIC_API = "https://api.semanticscholar.org/graph/v1/paper/search"
CROSSREF_API = "https://api.crossref.org/works"

# Crossref recomenda User-Agent com contato
CROSSREF_HEADERS = {"User-Agent": "CitatIA/1.0 (mailto:contato@seu-email.com)"}

# =========================
# STOPWORDS (sem NLTK, para não quebrar deploy)
# =========================
STOP_WORDS_PT = {
    "a","o","os","as","um","uma","uns","umas","de","do","da","dos","das","em","no","na","nos","nas","por","para","com",
    "sem","sob","sobre","entre","e","ou","mas","que","se","sua","seu","suas","seus","ao","aos","à","às","como","mais",
    "menos","muito","muitos","muita","muitas","já","ainda","também","tão","não","sim","ser","estar","ter","há","foi",
    "são","era","foram","este","esta","isso","essa","aquele","aquela","aquilo","num","numa","nuns","numas","cada",
    "onde","quando","porque","porquê","qual","quais","quem","cujo","cujos","cuja","cujas","até","após","antes"
}
STOP_WORDS_EN = {
    "the","and","from","this","that","with","have","has","had","into","without","for","of","in","on","to","an","is",
    "are","was","were","be","been","being","as","at","by","it","its","their","they","them","we","our","you","your",
    "he","she","his","her","not","no","yes","but","or","if","then","than","also","can","could","may","might","will",
    "would","should","a","about","between","over","under","after","before","during","such","these","those"
}
STOP_WORDS = STOP_WORDS_PT | STOP_WORDS_EN

# =========================
# ÁREAS E BASELINES (proxy)
# =========================
AREA_KEYWORDS = {
    "Computer Science": {"ai", "machine", "learning", "deep", "neural", "algorithm", "model", "data"},
    "Medicine": {"health", "clinical", "disease", "medical", "patient", "therapy", "drug", "cancer"},
    "Environmental Science": {"climate", "sustainability", "carbon", "energy", "environment", "renewable", "emission"},
    "Economics & Business": {"economy", "finance", "market", "business", "management", "innovation", "policy"},
    "Social Sciences": {"education", "social", "inequality", "public", "society", "behavior"},
}

FIELD_BASELINES = {
    "Computer Science": 18,
    "Medicine": 30,
    "Environmental Science": 20,
    "Economics & Business": 16,
    "Social Sciences": 14,
    "Multidisciplinary": 18,
}

# =========================
# GOOGLE SHEETS
# =========================
def salvar_email_google_sheets(nome: str, email: str, codigo_verificacao: str) -> None:
    try:
        response = requests.post(
            URL_GOOGLE_SHEETS,
            json={"nome": nome, "email": email, "codigo": codigo_verificacao},
            headers={"Content-Type": "application/json"},
            timeout=20,
        )
        if response.text.strip() == "Sucesso":
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
# UTILIDADES
# =========================
def infer_areas_from_text(texto: str):
    words = set(re.findall(r"\b\w+\b", (texto or "").lower()))
    matched = [area for area, kws in AREA_KEYWORDS.items() if words.intersection(kws)]
    return matched if matched else ["Multidisciplinary"]


def get_year_from_crossref(item: dict):
    for key in ["published-print", "published-online", "created", "issued"]:
        parts = item.get(key, {}).get("date-parts", [])
        if parts and parts[0]:
            return parts[0][0]
    return None


def strip_html(txt: str) -> str:
    return re.sub(r"<[^>]+>", " ", txt or "")


def extract_text_from_pdf_bytes(pdf_bytes: bytes) -> str:
    if not pdf_bytes:
        return ""
    text = []
    try:
        with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
            for page in pdf.pages:
                text.append(page.extract_text() or "")
    except Exception:
        return ""
    return "\n".join(text).strip()


def identify_theme(user_text: str):
    words = re.findall(r"\b\w+\b", (user_text or "").lower())
    words = [w for w in words if w not in STOP_WORDS and len(w) > 3 and not w.isdigit()]
    top = Counter(words).most_common(12)
    tema = ", ".join([w for w, _ in top]) if top else "Tema não identificado"
    return tema, [w for w, _ in top]


@st.cache_data(ttl=60 * 30, show_spinner=False)  # 30 min
def get_popular_phrases(query: str, limit: int = 60):
    articles = []

    # Semantic Scholar
    semantic_params = {
        "query": query,
        "limit": limit,
        "fields": "title,abstract,url,externalIds,citationCount,year,fieldsOfStudy,venue",
    }
    try:
        resp = requests.get(SEMANTIC_API, params=semantic_params, timeout=20)
        if resp.status_code == 200:
            for item in resp.json().get("data", []):
                title = item.get("title", "") or ""
                abstract = item.get("abstract") or ""
                venue = item.get("venue") or "N/A"
                articles.append(
                    {
                        "title": title,
                        "abstract": abstract,
                        "phrase": f"{title}. {abstract}",
                        "doi": (item.get("externalIds") or {}).get("DOI", "N/A"),
                        "link": item.get("url", "N/A"),
                        "citationCount": int(item.get("citationCount", 0) or 0),
                        "year": item.get("year"),
                        "areas": item.get("fieldsOfStudy") or infer_areas_from_text(f"{title} {abstract}"),
                        "source": venue,
                        "publisher": "Semantic Scholar",
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
                abstract = strip_html(item.get("abstract", "") or "")
                source = (item.get("container-title") or ["N/A"])[0]
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
                        "source": source,
                        "publisher": item.get("publisher", "N/A"),
                    }
                )
    except requests.RequestException:
        pass

    # Dedup
    dedup = {}
    for art in articles:
        key = art["doi"] if art["doi"] != "N/A" else art["title"].strip().lower()
        if not key:
            continue
        if key not in dedup or art["citationCount"] > dedup[key]["citationCount"]:
            dedup[key] = art

    ranked = sorted(dedup.values(), key=lambda x: x.get("citationCount", 0), reverse=True)
    return ranked[:limit]


def extract_top_keywords(articles, limit: int = 20):
    text = " ".join(item.get("phrase", "") for item in (articles or [])[:30])
    words = re.findall(r"\b\w+\b", text.lower())
    words = [w for w in words if w not in STOP_WORDS and len(w) > 3 and not w.isdigit()]
    return [word for word, _ in Counter(words).most_common(limit)]


def get_publication_statistics(articles):
    years = [item.get("year") for item in (articles or []) if isinstance(item.get("year"), int)]
    yearly = dict(sorted(Counter(years).items()))
    total = len(articles or [])
    current_year = datetime.now().year
    recent = sum(1 for y in years if y >= current_year - 3)
    recency_ratio = (recent / total * 100) if total else 0

    trend_momentum = 0.0
    if yearly:
        older = sum(v for y, v in yearly.items() if y <= current_year - 4)
        newer = sum(v for y, v in yearly.items() if y >= current_year - 3)
        denom = max(older, 1)
        trend_momentum = ((newer - older) / denom) * 100

    return yearly, recency_ratio, round(trend_momentum, 2)


def _compute_h_index(citations):
    ordered = sorted(citations, reverse=True)
    h = 0
    for idx, c in enumerate(ordered, start=1):
        if c >= idx:
            h = idx
    return h


def _compute_g_index(citations):
    ordered = sorted(citations, reverse=True)
    total = 0
    g = 0
    for idx, c in enumerate(ordered, start=1):
        total += c
        if total >= idx * idx:
            g = idx
    return g


def _compute_source_metrics(articles):
    grouped = defaultdict(list)
    for a in (articles or []):
        grouped[a.get("source", "N/A")].append(a)

    source_rows = []
    for source, items in grouped.items():
        cites = [i.get("citationCount", 0) for i in items]
        source_rows.append(
            {
                "source": source,
                "docs": len(items),
                "citations": sum(cites),
                "avg_citations": round(sum(cites) / max(len(cites), 1), 2),
            }
        )

    ranked = sorted(source_rows, key=lambda x: (x["citations"], x["avg_citations"]), reverse=True)
    quartile_size = max(math.ceil(len(ranked) / 4), 1)
    for idx, row in enumerate(ranked):
        q = min((idx // quartile_size) + 1, 4)
        row["quartile"] = f"Q{q}"
    return ranked[:15]


def analyze_citation_landscape(articles, article_keywords):
    citations = [a.get("citationCount", 0) for a in (articles or [])]
    top_articles = sorted((articles or []), key=lambda x: x.get("citationCount", 0), reverse=True)[:15]

    area_counter = Counter()
    area_fwci = defaultdict(list)
    for item in (articles or []):
        c = item.get("citationCount", 0)
        for area in (item.get("areas") or ["Multidisciplinary"]):
            area_counter[area] += c
            baseline = FIELD_BASELINES.get(area, FIELD_BASELINES["Multidisciplinary"])
            area_fwci[area].append(c / baseline)

    hot_keywords = set(extract_top_keywords(top_articles, limit=25))
    overlap = len(set(article_keywords or []).intersection(hot_keywords))
    overlap_ratio = overlap / len(article_keywords) if article_keywords else 0

    total = sum(citations)
    top10 = sum(sorted(citations, reverse=True)[:10])
    concentration_ratio = (top10 / total * 100) if total else 0

    fwci_values = []
    for item in (articles or []):
        first_area = (item.get("areas") or ["Multidisciplinary"])[0]
        fwci_values.append(item.get("citationCount", 0) / FIELD_BASELINES.get(first_area, 18))

    median = 0
    if citations:
        ordered = sorted(citations)
        median = ordered[len(ordered) // 2]

    return {
        "top_articles": top_articles,
        "total_citations": total,
        "mean_citations": round((total / len(citations)) if citations else 0, 2),
        "median_citations": median,
        "h_index": _compute_h_index(citations),
        "g_index": _compute_g_index(citations),
        "top_areas": area_counter.most_common(8),
        "area_fwci": {k: round(sum(v) / len(v), 2) for k, v in area_fwci.items()},
        "keyword_overlap_ratio": overlap_ratio,
        "citation_concentration_top10": round(concentration_ratio, 2),
        "fwci_proxy": round(sum(fwci_values) / len(fwci_values), 2) if fwci_values else 0,
        "source_metrics": _compute_source_metrics(articles),
    }


def evaluate_article_relevance(total_articles, overlap_ratio, recency_ratio, fwci_proxy, trend_momentum):
    saturation_penalty = min(total_articles / 80, 1) * 25

    score = 45
    score += overlap_ratio * 25
    score += (recency_ratio / 100) * 15
    score += min(fwci_proxy / 2, 1) * 10
    score += min(max(trend_momentum, -100), 200) / 200 * 10
    score -= saturation_penalty
    score = max(5, min(99, score))

    if score >= 80:
        txt = "Potencial muito alto (faixa Q1): tema quente, bom alinhamento semântico e impacto relativo acima da média."
    elif score >= 65:
        txt = "Potencial alto (faixa Q2): bom fit com frentes de citação e tendência favorável."
    elif score >= 50:
        txt = "Potencial moderado (faixa Q3): recomenda-se reforçar novelty, método e posicionamento internacional."
    else:
        txt = "Potencial baixo (faixa Q4): tema pode estar saturado/fora do foco de maior impacto no momento."

    return round(score, 2), txt


# =========================
# PDF REPORT
# =========================
def generate_report(
    tema,
    top_keywords,
    yearly_counts,
    recency_ratio,
    trend_momentum,
    landscape,
    score,
    descricao,
    output_path="report.pdf",
):
    doc = SimpleDocTemplate(output_path, pagesize=A4)
    styles = getSampleStyleSheet()
    body = ParagraphStyle("Body", parent=styles["BodyText"], alignment=4, spaceAfter=8)

    content = [
        Paragraph("<b>Relatório Bibliométrico Avançado (Scopus/WoS-like) - CitatIA</b>", styles["Title"]),
        Paragraph(f"<b>Tema principal:</b> {tema}", body),
        Paragraph(f"<b>Score de potencial (proxy CiteScore/JCR):</b> {score}%", body),
        Paragraph(f"<b>Diagnóstico:</b> {descricao}", body),
        Paragraph(
            f"<b>FWCI Proxy:</b> {landscape['fwci_proxy']} | <b>h-index:</b> {landscape['h_index']} | <b>g-index:</b> {landscape['g_index']}",
            body,
        ),
        Paragraph(f"<b>Concentração de citações top-10:</b> {landscape['citation_concentration_top10']}%", body),
        Paragraph("<b>Áreas mais citadas:</b>", styles["Heading3"]),
    ]

    for area, cites in landscape["top_areas"]:
        fwci = landscape["area_fwci"].get(area, 0)
        content.append(Paragraph(f"• {area}: {cites} citações | FWCI área: {fwci}", body))

    content.append(Paragraph("<b>Tendência temporal:</b>", styles["Heading3"]))
    if yearly_counts:
        for year, count in yearly_counts.items():
            content.append(Paragraph(f"• {year}: {count} publicações", body))
    else:
        content.append(Paragraph("• Sem dados suficientes de ano para tendência.", body))

    content.append(
        Paragraph(
            f"<b>Recência (3 anos):</b> {recency_ratio:.2f}% | <b>Momentum:</b> {trend_momentum:.2f}%",
            body,
        )
    )

    content.append(Paragraph("<b>Palavras dominantes nos artigos mais citados:</b>", styles["Heading3"]))
    for w in top_keywords:
        content.append(Paragraph(f"• {w}", body))

    content.append(Paragraph("<b>Top fontes (proxy quartil):</b>", styles["Heading3"]))
    for src in landscape["source_metrics"][:10]:
        content.append(
            Paragraph(
                f"• {src['source']} | Docs: {src['docs']} | Citações: {src['citations']} | Média: {src['avg_citations']} | Quartil: {src['quartile']}",
                body,
            )
        )

    content.append(Paragraph("<b>Artigos mais citados:</b>", styles["Heading3"]))
    for item in landscape["top_articles"][:10]:
        content.append(
            Paragraph(
                f"• {item.get('title', 'Sem título')}<br/>"
                f"<b>DOI:</b> {item.get('doi', 'N/A')}<br/>"
                f"<b>Fonte:</b> {item.get('source', 'N/A')}<br/>"
                f"<b>Citações:</b> {item.get('citationCount', 0)}",
                body,
            )
        )

    doc.build(content)


# =========================
# PIX / QR
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
        <p>Temos custos com infraestrutura, APIs e indexação. Contribua com <strong>R$ 20,00</strong>.</p>
        <p><strong>Chave Pix:</strong> <span style='color: blue;'>peas8810@gmail.com</span></p>
        <p><strong>Recebedor:</strong> PEAS TECHNOLOGIES</p>
        """,
        unsafe_allow_html=True,
    )
    st.image(gerar_qr_code_pix(payload), caption="QR Code Pix (R$ 20,00)", width=300)


# =========================
# APP
# =========================
def main():
    st.title("CitatIA - Benchmark Bibliométrico (CiteScore/JCR-like)")

    # Registro
    with st.expander("📋 Registro de Usuário", expanded=False):
        nome = st.text_input("Nome completo")
        email = st.text_input("E-mail")
        if st.button("Salvar Dados"):
            if nome and email:
                codigo = gerar_codigo_verificacao(email)
                salvar_email_google_sheets(nome, email, codigo)
                st.success(f"Código de verificação gerado: **{codigo}**")
            else:
                st.warning("⚠️ Preencha todos os campos.")

    # Upload do PDF
    st.subheader("📄 Enviar PDF para análise")
    uploaded_file = st.file_uploader("Envie o arquivo PDF", type="pdf")

    if uploaded_file:
        st.info("🔍 Extraindo texto do PDF...")
        user_text = extract_text_from_pdf_bytes(uploaded_file.getvalue())

        if not user_text or len(user_text) < 200:
            st.error("Não foi possível extrair texto suficiente do PDF. Se for escaneado, será necessário OCR.")
            st.stop()

        tema, article_keywords = identify_theme(user_text)

        with st.spinner("Consultando bases (Semantic Scholar + Crossref)..."):
            articles = get_popular_phrases(tema, limit=60)

        if not articles:
            st.error("Não foi possível recuperar artigos nas bases externas para este tema.")
            st.stop()

        top_keywords = extract_top_keywords(articles, limit=20)
        yearly, recency_ratio, trend_momentum = get_publication_statistics(articles)
        landscape = analyze_citation_landscape(articles, article_keywords)
        score, descricao = evaluate_article_relevance(
            total_articles=len(articles),
            overlap_ratio=landscape["keyword_overlap_ratio"],
            recency_ratio=recency_ratio,
            fwci_proxy=landscape["fwci_proxy"],
            trend_momentum=trend_momentum,
        )

        st.success(f"✅ Tema identificado: {tema}")
        st.metric("Score de Potencial", f"{score}%")
        st.write(descricao)

        st.write("### Indicadores bibliométricos")
        st.write(
            f"Média de citações no corpus: **{landscape['mean_citations']}** | "
            f"Total de citações no corpus: **{landscape['total_citations']}**"
        )
        st.write(
            f"FWCI proxy: **{landscape['fwci_proxy']}** | h-index: **{landscape['h_index']}** | "
            f"g-index: **{landscape['g_index']}** | Concentração top-10: **{landscape['citation_concentration_top10']}%**"
        )
        st.write(f"Recência (3 anos): **{recency_ratio:.2f}%** | Momentum anual: **{trend_momentum:.2f}%**")

        st.write("### Áreas mais citadas")
        for area, c in landscape["top_areas"]:
            st.write(f"• {area}: {c} citações | FWCI área: {landscape['area_fwci'].get(area, 0)}")

        st.write("### Palavras mais recorrentes")
        for word in top_keywords:
            st.write(f"• {word}")

        st.write("### Top fontes (proxy de quartil)")
        for row in landscape["source_metrics"][:10]:
            st.write(
                f"• {row['source']} | Docs: {row['docs']} | Citações: {row['citations']} | "
                f"Média: {row['avg_citations']} | {row['quartile']}"
            )

        st.write("### Artigos mais citados")
        for item in landscape["top_articles"][:10]:
            st.write(
                f"• {item.get('title','Sem título')} | Fonte: {item.get('source','N/A')} | "
                f"Citações: {item.get('citationCount',0)}"
            )

        # Relatório PDF
        generate_report(
            tema=tema,
            top_keywords=top_keywords,
            yearly_counts=yearly,
            recency_ratio=recency_ratio,
            trend_momentum=trend_momentum,
            landscape=landscape,
            score=score,
            descricao=descricao,
        )
        with open("report.pdf", "rb") as f:
            st.download_button("📥 Baixar Relatório (PDF)", f, "report.pdf", mime="application/pdf")

    # Verificação
    st.header("🔐 Verificar Autenticidade")
    codigo = st.text_input("Digite o código de verificação")
    if st.button("Verificar Código"):
        if codigo.strip() and verificar_codigo_google_sheets(codigo.strip()):
            st.success("✅ Documento Autêntico e Original!")
        else:
            st.error("❌ Código inválido ou documento falsificado.")

    st.markdown("---\nPowered By - PEAS.Co")
    render_donation_section()


if __name__ == "__main__":
    main()

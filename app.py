diff --git a/app.py b/app.py
index 4d5d2934ceeb47d74b5680ea9e74c50b919e679c..4c5a9272fe5a58dff0d742d24e77ccd626f17499 100644
--- a/app.py
+++ b/app.py
@@ -1,313 +1,339 @@
-import streamlit as st
-import random
 import hashlib
-import pdfplumber
+import re
 from collections import Counter
+from datetime import datetime
+from io import BytesIO
+
+import pdfplumber
+import qrcode
+import requests
+import streamlit as st
 from nltk.corpus import stopwords
+from PIL import Image
 from reportlab.lib.pagesizes import A4
+from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
 from reportlab.platypus import Paragraph, SimpleDocTemplate
-from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
-import nltk
-import re
-import requests
-import torch
-import torch.nn as nn
-import torch.nn.functional as F
-from datetime import datetime, timedelta
-
-nltk.download('stopwords')
-
-STOP_WORDS = set(stopwords.words('portuguese'))
 
 # 🔗 URL da API do Google Sheets
 URL_GOOGLE_SHEETS = "https://script.google.com/macros/s/AKfycbyHRCrD5-A_JHtaUDXsGWQ22ul9ml5vvK3YYFzIE43jjCdip0dBMFH_Jmd8w971PLte/exec"
 
-# URLs das APIs
+# APIs bibliográficas
 SEMANTIC_API = "https://api.semanticscholar.org/graph/v1/paper/search"
 CROSSREF_API = "https://api.crossref.org/works"
 
-# =============================
-# 📋 Função para Salvar E-mails e Código de Verificação no Google Sheets
-# =============================
-def salvar_email_google_sheets(nome, email, codigo_verificacao):
-    dados = {
-        "nome": nome,
-        "email": email,
-        "codigo": codigo_verificacao
+AREA_KEYWORDS = {
+    "Inteligência Artificial e Computação": {"ai", "machine", "learning", "deep", "neural", "algorithm", "computing", "data"},
+    "Saúde e Biomedicina": {"health", "clinical", "disease", "medical", "patient", "cancer", "biomedical", "drug"},
+    "Sustentabilidade e Meio Ambiente": {"climate", "sustainability", "carbon", "energy", "environment", "renewable", "emission"},
+    "Negócios e Economia": {"economy", "finance", "market", "business", "management", "innovation", "productivity"},
+    "Educação e Ciências Sociais": {"education", "social", "policy", "learning", "inequality", "public", "society"},
+}
+
+try:
+    STOP_WORDS = set(stopwords.words("portuguese"))
+except LookupError:
+    STOP_WORDS = {
+        "para", "com", "mais", "como", "este", "essa", "isso", "são", "ser", "sobre", "entre", "pela", "pelo",
+        "uma", "que", "dos", "das", "por", "sem", "nos", "nas", "the", "and", "from", "this", "that",
     }
+
+
+def salvar_email_google_sheets(nome, email, codigo_verificacao):
+    dados = {"nome": nome, "email": email, "codigo": codigo_verificacao}
     try:
-        headers = {'Content-Type': 'application/json'}
-        response = requests.post(URL_GOOGLE_SHEETS, json=dados, headers=headers)
+        response = requests.post(URL_GOOGLE_SHEETS, json=dados, headers={"Content-Type": "application/json"}, timeout=20)
         if response.text.strip() == "Sucesso":
             st.success("✅ E-mail, nome e código registrados com sucesso!")
         else:
             st.error(f"❌ Erro ao salvar dados no Google Sheets: {response.text}")
-    except Exception as e:
-        st.error(f"❌ Erro na conexão com o Google Sheets: {e}")
+    except requests.RequestException as exc:
+        st.error(f"❌ Erro na conexão com o Google Sheets: {exc}")
+
 
-# =============================
-# 🔎 Função para Verificar Código de Verificação na Planilha
-# =============================
 def verificar_codigo_google_sheets(codigo_digitado):
     try:
-        response = requests.get(f"{URL_GOOGLE_SHEETS}?codigo={codigo_digitado}")
-        if response.text.strip() == "Valido":
-            return True
-        else:
-            return False
-    except Exception as e:
-        st.error(f"❌ Erro na conexão com o Google Sheets: {e}")
+        response = requests.get(f"{URL_GOOGLE_SHEETS}?codigo={codigo_digitado}", timeout=20)
+        return response.text.strip() == "Valido"
+    except requests.RequestException as exc:
+        st.error(f"❌ Erro na conexão com o Google Sheets: {exc}")
         return False
 
-# =============================
-# 🔐 Função para Gerar Código de Verificação
-# =============================
+
 def gerar_codigo_verificacao(texto):
     return hashlib.md5(texto.encode()).hexdigest()[:10].upper()
 
-# Função para obter artigos mais citados
-def get_popular_phrases(query, limit=10):
-    suggested_phrases = []
-
-    # Pesquisa na API Semantic Scholar
-    semantic_params = {"query": query, "limit": limit, "fields": "title,abstract,url,externalIds,citationCount"}
-    semantic_response = requests.get(SEMANTIC_API, params=semantic_params)
-    if semantic_response.status_code == 200:
-        semantic_data = semantic_response.json().get("data", [])
-        for item in semantic_data:
-            suggested_phrases.append({
-                "phrase": f"{item.get('title', '')}. {item.get('abstract', '')}",
-                "doi": item['externalIds'].get('DOI', 'N/A'),
-                "link": item.get('url', 'N/A'),
-                "citationCount": item.get('citationCount', 0)
-            })
-
-    # Pesquisa na API CrossRef
-    crossref_params = {"query": query, "rows": limit}
-    crossref_response = requests.get(CROSSREF_API, params=crossref_params)
-    if crossref_response.status_code == 200:
-        crossref_data = crossref_response.json().get("message", {}).get("items", [])
-        for item in crossref_data:
-            suggested_phrases.append({
-                "phrase": f"{item.get('title', [''])[0]}. {item.get('abstract', '')}",
-                "doi": item.get('DOI', 'N/A'),
-                "link": item.get('URL', 'N/A'),
-                "citationCount": item.get('is-referenced-by-count', 0)
-            })
-
-    # Ordenar por número de citações
-    suggested_phrases.sort(key=lambda x: x.get('citationCount', 0), reverse=True)
-
-    return suggested_phrases
-
-# Função para extrair as 10 palavras mais importantes dos artigos
-def extract_top_keywords(suggested_phrases):
-    all_text = " ".join([item['phrase'] for item in suggested_phrases])
-    words = re.findall(r'\b\w+\b', all_text.lower())
-    words = [word for word in words if word not in STOP_WORDS and len(word) > 3]  # Filtra stopwords e palavras curtas
-    word_freq = Counter(words).most_common(10)
-    return [word for word, freq in word_freq]
-
-# Função para simular estatísticas de publicações mensais
-def get_publication_statistics(total_articles):
-    start_date = datetime.now() - timedelta(days=365)  # Último ano
-    publication_dates = [start_date + timedelta(days=random.randint(0, 365)) for _ in range(total_articles)]
-    monthly_counts = Counter([date.strftime("%Y-%m") for date in publication_dates])
-    proportion_per_100 = (total_articles / 100) * 100  # Normaliza para 100
-    return monthly_counts, proportion_per_100
-
-# Modelo PyTorch para prever chance de ser referência
-class ArticlePredictor(nn.Module):
-    def __init__(self):
-        super(ArticlePredictor, self).__init__()
-        self.fc1 = nn.Linear(1, 16)
-        self.fc2 = nn.Linear(16, 8)
-        self.fc3 = nn.Linear(8, 1)
-
-    def forward(self, x):
-        x = torch.relu(self.fc1(x))
-        x = torch.relu(self.fc2(x))
-        x = torch.sigmoid(self.fc3(x))
-        return x
-
-# Avalia a probabilidade do artigo se tornar uma referência
-def evaluate_article_relevance(publication_count):
-    model = ArticlePredictor()
-    data = torch.tensor([[publication_count]], dtype=torch.float32)
-    probability = model(data).item() * 100  # Probabilidade em porcentagem
-
-    if probability >= 70:
-        descricao = "A probabilidade de este artigo se tornar uma referência é alta. Isso ocorre porque há poucas publicações sobre o tema, o que aumenta as chances de destaque."
-    elif 30 <= probability < 70:
-        descricao = "A probabilidade de este artigo se tornar uma referência é moderada. O tema tem uma quantidade equilibrada de publicações, o que mantém as chances de destaque em um nível intermediário."
+
+def infer_areas_from_text(texto):
+    words = set(re.findall(r"\b\w+\b", texto.lower()))
+    detected = [area for area, kws in AREA_KEYWORDS.items() if words.intersection(kws)]
+    return detected if detected else ["Multidisciplinar"]
+
+
+def get_year_from_crossref(item):
+    for key in ["published-print", "published-online", "created", "issued"]:
+        date_parts = item.get(key, {}).get("date-parts", [])
+        if date_parts and date_parts[0]:
+            return date_parts[0][0]
+    return None
+
+
+def get_popular_phrases(query, limit=30):
+    articles = []
+
+    semantic_params = {
+        "query": query,
+        "limit": limit,
+        "fields": "title,abstract,url,externalIds,citationCount,year,fieldsOfStudy",
+    }
+    try:
+        resp = requests.get(SEMANTIC_API, params=semantic_params, timeout=20)
+        if resp.status_code == 200:
+            for item in resp.json().get("data", []):
+                title = item.get("title", "")
+                abstract = item.get("abstract") or ""
+                articles.append(
+                    {
+                        "title": title,
+                        "abstract": abstract,
+                        "phrase": f"{title}. {abstract}",
+                        "doi": (item.get("externalIds") or {}).get("DOI", "N/A"),
+                        "link": item.get("url", "N/A"),
+                        "citationCount": item.get("citationCount", 0),
+                        "year": item.get("year"),
+                        "areas": item.get("fieldsOfStudy") or infer_areas_from_text(f"{title} {abstract}"),
+                    }
+                )
+    except requests.RequestException:
+        pass
+
+    crossref_params = {"query": query, "rows": limit, "sort": "is-referenced-by-count", "order": "desc"}
+    try:
+        resp = requests.get(CROSSREF_API, params=crossref_params, timeout=20)
+        if resp.status_code == 200:
+            for item in resp.json().get("message", {}).get("items", []):
+                title = item.get("title", [""])[0]
+                abstract = re.sub(r"<[^>]+>", " ", item.get("abstract", "") or "")
+                articles.append(
+                    {
+                        "title": title,
+                        "abstract": abstract,
+                        "phrase": f"{title}. {abstract}",
+                        "doi": item.get("DOI", "N/A"),
+                        "link": item.get("URL", "N/A"),
+                        "citationCount": item.get("is-referenced-by-count", 0),
+                        "year": get_year_from_crossref(item),
+                        "areas": item.get("subject") or infer_areas_from_text(f"{title} {abstract}"),
+                    }
+                )
+    except requests.RequestException:
+        pass
+
+    deduped = {}
+    for article in articles:
+        key = article["doi"] if article["doi"] != "N/A" else article["title"].strip().lower()
+        if key not in deduped or article["citationCount"] > deduped[key]["citationCount"]:
+            deduped[key] = article
+
+    result = sorted(deduped.values(), key=lambda x: x.get("citationCount", 0), reverse=True)
+    return result[:limit]
+
+
+def extract_top_keywords(suggested_phrases, limit=15):
+    text = " ".join(item.get("phrase", "") for item in suggested_phrases[:20])
+    words = re.findall(r"\b\w+\b", text.lower())
+    words = [w for w in words if w not in STOP_WORDS and len(w) > 3]
+    return [word for word, _ in Counter(words).most_common(limit)]
+
+
+def get_publication_statistics(articles):
+    years = [item.get("year") for item in articles if isinstance(item.get("year"), int)]
+    yearly_counts = dict(sorted(Counter(years).items()))
+    total = len(articles)
+    recent = sum(1 for y in years if y >= datetime.now().year - 3)
+    recency_ratio = (recent / total * 100) if total else 0
+    return yearly_counts, recency_ratio
+
+
+def identify_theme(user_text):
+    words = re.findall(r"\b\w+\b", user_text)
+    keywords = [word.lower() for word in words if word.lower() not in STOP_WORDS and len(word) > 3]
+    top = Counter(keywords).most_common(10)
+    return ", ".join([word for word, _ in top]), [word for word, _ in top]
+
+
+def analyze_citation_landscape(articles, article_keywords):
+    citations = [item.get("citationCount", 0) for item in articles]
+    total_citations = sum(citations)
+    mean_citations = round((total_citations / len(citations)) if citations else 0, 2)
+    top_articles = sorted(articles, key=lambda x: x.get("citationCount", 0), reverse=True)[:10]
+
+    area_counter = Counter()
+    for item in articles:
+        for area in item.get("areas", []):
+            area_counter[area] += item.get("citationCount", 0)
+
+    hot_keywords = set(extract_top_keywords(top_articles, limit=20))
+    overlap = len(set(article_keywords).intersection(hot_keywords))
+    overlap_ratio = overlap / len(article_keywords) if article_keywords else 0
+
+    return {
+        "top_articles": top_articles,
+        "total_citations": total_citations,
+        "mean_citations": mean_citations,
+        "top_areas": area_counter.most_common(5),
+        "keyword_overlap_ratio": overlap_ratio,
+    }
+
+
+def evaluate_article_relevance(total_articles, overlap_ratio, recency_ratio):
+    saturation_penalty = min(total_articles / 40, 1) * 35
+    probability = 55 + (overlap_ratio * 30) + (recency_ratio * 0.25) - saturation_penalty
+    probability = max(5, min(95, probability))
+
+    if probability >= 75:
+        desc = "A probabilidade de este artigo se tornar referência é alta: o texto está alinhado aos tópicos mais citados e o tema está aquecido recentemente."
+    elif probability >= 45:
+        desc = "A probabilidade é moderada: há bom potencial, mas é recomendável reforçar diferenciais metodológicos e posicionamento."
     else:
-        descricao = "A probabilidade de este artigo se tornar uma referência é baixa. Há muitas publicações sobre o tema, o que reduz as chances de destaque."
+        desc = "A probabilidade é baixa no cenário atual: o tema parece saturado ou pouco conectado aos tópicos de maior impacto recente."
+
+    return round(probability, 2), desc
 
-    return round(probability, 2), descricao
 
-# Função para extrair texto de um arquivo PDF
 def extract_text_from_pdf(pdf_path):
     text = ""
     with pdfplumber.open(pdf_path) as pdf:
         for page in pdf.pages:
             text += page.extract_text() or ""
     return text.strip()
 
-# Função para identificar o tema principal do artigo
-def identify_theme(user_text):
-    words = re.findall(r'\b\w+\b', user_text)
-    keywords = [word.lower() for word in words if word.lower() not in STOP_WORDS]
-    keyword_freq = Counter(keywords).most_common(10)
-    return ", ".join([word for word, freq in keyword_freq])
 
-# Função para gerar relatório detalhado
-def generate_report(suggested_phrases, top_keywords, tema, probabilidade, descricao, monthly_counts, proportion_per_100, output_path="report.pdf"):
+def generate_report(tema, probabilidade, descricao, top_keywords, yearly_counts, recency_ratio, landscape, output_path="report.pdf"):
     doc = SimpleDocTemplate(output_path, pagesize=A4)
     styles = getSampleStyleSheet()
-
-    justified_style = ParagraphStyle(
-        'Justified',
-        parent=styles['BodyText'],
-        alignment=4,  # Alinhamento justificado
-        spaceAfter=10,
-    )
+    justified = ParagraphStyle("Justified", parent=styles["BodyText"], alignment=4, spaceAfter=10)
 
     content = [
-        Paragraph("<b>Relatório de Sugestão de Melhorias no Artigo - CitatIA - PEAS.Co</b>", styles['Title']),
-        Paragraph(f"<b>Tema Identificado com base nas principais palavras do artigo:</b> {tema}", justified_style),
-        Paragraph(f"<b>Probabilidade do artigo ser uma referência:</b> {probabilidade}%", justified_style),
-        Paragraph(f"<b>Explicação:</b> {descricao}", justified_style)
+        Paragraph("<b>Relatório de Análise de Citação - CitatIA</b>", styles["Title"]),
+        Paragraph(f"<b>Tema identificado:</b> {tema}", justified),
+        Paragraph(f"<b>Qualidade estimada (aderência ao estado da arte):</b> {landscape['keyword_overlap_ratio']*100:.2f}%", justified),
+        Paragraph(f"<b>Potencial do tema:</b> {probabilidade}%", justified),
+        Paragraph(f"<b>Análise:</b> {descricao}", justified),
+        Paragraph(f"<b>Média de citações no corpus:</b> {landscape['mean_citations']}", justified),
+        Paragraph(f"<b>Total de citações no corpus:</b> {landscape['total_citations']}", justified),
+        Paragraph("<b>Áreas com maior concentração de citações:</b>", styles["Heading3"]),
     ]
 
-    content.append(Paragraph("<b>Estatísticas de Publicações:</b>", styles['Heading3']))
-    content.append(Paragraph("<b>Publicações de artigos com mesmo tema:</b>", justified_style))
-    for month, count in monthly_counts.items():
-        content.append(Paragraph(f"• {month}: {count} publicações", justified_style))
-    content.append(Paragraph(f"<b>Proporção de publicações a cada 100 artigos:</b> {proportion_per_100:.2f}%", justified_style))
+    for area, weighted_citations in landscape["top_areas"]:
+        content.append(Paragraph(f"• {area}: {weighted_citations} citações", justified))
 
-    content.append(Paragraph("<b>Artigos mais acessados, baixados e/ou citados com base no tema:</b>", styles['Heading3']))
-    if suggested_phrases:
-        for item in suggested_phrases:
-            content.append(Paragraph(f"• {item['phrase']}<br/><b>DOI:</b> {item['doi']}<br/><b>Link:</b> {item['link']}<br/><b>Citações:</b> {item.get('citationCount', 'N/A')}", justified_style))
+    content.append(Paragraph("<b>Tendência temporal:</b>", styles["Heading3"]))
+    for year, count in yearly_counts.items():
+        content.append(Paragraph(f"• {year}: {count} publicações", justified))
+    content.append(Paragraph(f"<b>Participação de artigos recentes (3 anos):</b> {recency_ratio:.2f}%", justified))
 
-    content.append(Paragraph("<b>Palavras-chave mais citadas nos artigos mais acessados:</b>", styles['Heading3']))
-    if top_keywords:
-        for word in top_keywords:
-            content.append(Paragraph(f"• {word}", justified_style))
-    else:
-        content.append(Paragraph("Nenhuma palavra-chave relevante encontrada.", justified_style))
+    content.append(Paragraph("<b>Palavras mais recorrentes nos artigos mais citados:</b>", styles["Heading3"]))
+    for word in top_keywords:
+        content.append(Paragraph(f"• {word}", justified))
+
+    content.append(Paragraph("<b>Artigos mais citados:</b>", styles["Heading3"]))
+    for item in landscape["top_articles"]:
+        content.append(
+            Paragraph(
+                f"• {item.get('title', 'Sem título')}<br/><b>DOI:</b> {item.get('doi', 'N/A')}<br/><b>Link:</b> {item.get('link', 'N/A')}<br/><b>Citações:</b> {item.get('citationCount', 0)}",
+                justified,
+            )
+        )
 
     doc.build(content)
 
-# Interface com Streamlit
+
+def gerar_qr_code_pix(payload):
+    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=10, border=4)
+    qr.add_data(payload)
+    qr.make(fit=True)
+    img = qr.make_image(fill_color="black", back_color="white")
+    buffer = BytesIO()
+    img.save(buffer, format="PNG")
+    buffer.seek(0)
+    return Image.open(buffer)
+
+
+def render_donation_section():
+    payload = "00020126400014br.gov.bcb.pix0118peas8810@gmail.com520400005303986540520.005802BR5925PEDRO EMILIO AMADOR SALOM6013TEOFILO OTONI62200516PEASTECHNOLOGIES6304C9DB"
+    st.markdown("---")
+    st.markdown(
+        """
+        <h3 style='color: green;'>💚 Apoie Este Projeto com um Pix!</h3>
+        <p>Temos custos com servidores, desenvolvimento e APIs. Se este site está te ajudando, considere uma contribuição de <strong>R$ 20,00</strong>.</p>
+        <p><strong>Chave Pix:</strong> <span style='color: blue;'>peas8810@gmail.com</span></p>
+        <p><strong>Nome do recebedor:</strong> PEAS TECHNOLOGIES</p>
+        """,
+        unsafe_allow_html=True,
+    )
+    st.image(gerar_qr_code_pix(payload), caption="📲 Escaneie o QR Code para doar via Pix (R$ 20,00)", width=300)
+    st.success("🙏 Obrigado a todos que já contribuíram! Sua ajuda mantém este projeto vivo!")
+
+
 def main():
-    st.title("CitatIA - Potencializador de Artigos - PEAS.Co")
-    
-    # Registro de usuário
+    st.title("CitatIA - Potencializador de Artigos")
+
     st.subheader("📋 Registro de Usuário")
     nome = st.text_input("Nome completo")
     email = st.text_input("E-mail")
     if st.button("Salvar Dados"):
         if nome and email:
-            codigo_verificacao = gerar_codigo_verificacao(email)
-            salvar_email_google_sheets(nome, email, codigo_verificacao)
-            st.success(f"Código de verificação gerado: **{codigo_verificacao}**")
+            codigo = gerar_codigo_verificacao(email)
+            salvar_email_google_sheets(nome, email, codigo)
+            st.success(f"Código de verificação gerado: **{codigo}**")
         else:
             st.warning("⚠️ Por favor, preencha todos os campos.")
 
-    # Upload do PDF
-    uploaded_file = st.file_uploader("Envie o arquivo PDF", type='pdf')
+    uploaded_file = st.file_uploader("Envie o arquivo PDF", type="pdf")
     if uploaded_file:
-        with open("uploaded_article.pdf", "wb") as f:
-            f.write(uploaded_file.getbuffer())
-        st.info("🔍 Analisando o arquivo...")
+        with open("uploaded_article.pdf", "wb") as file:
+            file.write(uploaded_file.getbuffer())
 
         user_text = extract_text_from_pdf("uploaded_article.pdf")
-        tema = identify_theme(user_text)
-
-        # Buscando artigos e frases populares com base no tema identificado
-        suggested_phrases = get_popular_phrases(tema, limit=10)
-        # Extrair as 10 palavras mais importantes dos artigos
-        top_keywords = extract_top_keywords(suggested_phrases)
-        # Calculando a probabilidade com base nas referências encontradas
-        publication_count = len(suggested_phrases)
-        probabilidade, descricao = evaluate_article_relevance(publication_count)
-        # Gerar estatísticas de publicações
-        monthly_counts, proportion_per_100 = get_publication_statistics(publication_count)
+        tema, article_keywords = identify_theme(user_text)
+        articles = get_popular_phrases(tema, limit=30)
+        top_keywords = extract_top_keywords(articles, limit=15)
+        landscape = analyze_citation_landscape(articles, article_keywords)
+        yearly_counts, recency_ratio = get_publication_statistics(articles)
+        probabilidade, descricao = evaluate_article_relevance(len(articles), landscape["keyword_overlap_ratio"], recency_ratio)
 
         st.success(f"✅ Tema identificado: {tema}")
-        st.write(f"📈 Probabilidade do artigo ser uma referência: {probabilidade}%")
+        st.write(f"🏷️ Qualidade estimada: {landscape['keyword_overlap_ratio']*100:.2f}%")
+        st.write(f"📈 Potencial do tema: {probabilidade}%")
         st.write(f"ℹ️ {descricao}")
-        st.write("<b>Estatísticas de Publicações:</b>", unsafe_allow_html=True)
-        for month, count in monthly_counts.items():
-            st.write(f"• {month}: {count} publicações")
-        st.write(f"<b>Proporção de publicações a cada 100 artigos:</b> {proportion_per_100:.2f}%", unsafe_allow_html=True)
-        st.write("<b>Palavras-chave mais citadas:</b>", unsafe_allow_html=True)
-        if top_keywords:
-            for word in top_keywords:
-                st.write(f"• {word}")
-        else:
-            st.write("Nenhuma palavra-chave relevante encontrada.")
 
-        # Gerar e exibir link para download do relatório
-        generate_report(suggested_phrases, top_keywords, tema, probabilidade, descricao, monthly_counts, proportion_per_100)
+        st.write("<b>Áreas de maior citação:</b>", unsafe_allow_html=True)
+        for area, count in landscape["top_areas"]:
+            st.write(f"• {area}: {count} citações")
+
+        st.write("<b>Palavras mais recorrentes:</b>", unsafe_allow_html=True)
+        for word in top_keywords:
+            st.write(f"• {word}")
+
+        st.write("<b>Artigos mais citados:</b>", unsafe_allow_html=True)
+        for item in landscape["top_articles"]:
+            st.write(f"• {item['title']} | Citações: {item.get('citationCount', 0)} | DOI: {item.get('doi', 'N/A')}")
+
+        generate_report(tema, probabilidade, descricao, top_keywords, yearly_counts, recency_ratio, landscape)
         with open("report.pdf", "rb") as file:
             st.download_button("📥 Baixar Relatório", file, "report.pdf")
 
-    # Verificação de código
     st.header("Verificar Autenticidade")
     codigo_digitado = st.text_input("Digite o código de verificação:")
     if st.button("Verificar Código"):
         if verificar_codigo_google_sheets(codigo_digitado):
             st.success("✅ Documento Autêntico e Original!")
         else:
             st.error("❌ Código inválido ou documento falsificado.")
 
-    # Texto explicativo ao final da página
-    st.markdown("""
-    ---
-    Powered By - PEAS.Co
-    """)
+    st.markdown("---\nPowered By - PEAS.Co")
+    render_donation_section()
 
 
 if __name__ == "__main__":
     main()
-
-def gerar_qr_code_pix(payload):
-    import qrcode
-    from io import BytesIO
-    from PIL import Image
-
-    qr = qrcode.QRCode(
-        version=1,
-        error_correction=qrcode.constants.ERROR_CORRECT_M,
-        box_size=10,
-        border=4,
-    )
-    qr.add_data(payload)
-    qr.make(fit=True)
-    img = qr.make_image(fill_color="black", back_color="white")
-    buffer = BytesIO()
-    img.save(buffer, format="PNG")
-    buffer.seek(0)
-    return Image.open(buffer)
-
-# --- Payload Pix Oficial ---
-payload = "00020126400014br.gov.bcb.pix0118peas8810@gmail.com520400005303986540520.005802BR5925PEDRO EMILIO AMADOR SALOM6013TEOFILO OTONI62200516PEASTECHNOLOGIES6304C9DB"
-
-# --- Seção de Doação via Pix ---
-st.markdown("---")
-st.markdown(
-    """
-    <h3 style='color: green;'>💚 Apoie Este Projeto com um Pix!</h3>
-    <p>Temos custos com servidores, desenvolvimento e APIs. Se este site está te ajudando, considere uma contribuição de <strong>R$ 20,00</strong>.</p>
-    <p><strong>Chave Pix:</strong> <span style='color: blue;'>pesas8810@gmail.com</span></p>
-    <p><strong>Nome do recebedor:</strong> PEAS TECHNOLOGIES</p>
-    """,
-    unsafe_allow_html=True
-)
-
-qr_img = gerar_qr_code_pix(payload)
-st.image(qr_img, caption="📲 Escaneie o QR Code para doar via Pix (R$ 20,00)", width=300)
-
-st.success("🙏 Obrigado a todos que já contribuíram! Sua ajuda mantém este projeto vivo!")

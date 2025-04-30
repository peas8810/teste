import re
import numpy as np
import pandas as pd
import pdfplumber
from fpdf import FPDF
from transformers import RobertaTokenizer, RobertaForSequenceClassification
import torch
import streamlit as st
import io
import requests
import hashlib
from datetime import datetime

# 🔗 URL da API gerada no Google Sheets
URL_GOOGLE_SHEETS = "https://script.google.com/macros/s/AKfycbyTpbWDxWkNRh_ZIlHuAVwZaCC2ODqTmo0Un7ZDbgzrVQBmxlYYKuoYf6yDigAPHZiZ/exec"

# =============================
# 📋 Função para Salvar E-mails no Google Sheets
# =============================
def salvar_email_google_sheets(nome, email, codigo="N/A"):
    dados = {
        "nome": nome,
        "email": email,
        "codigo": codigo
    }
    try:
        headers = {'Content-Type': 'application/json'}
        response = requests.post(URL_GOOGLE_SHEETS, json=dados, headers=headers)
        if response.text.strip() == "Sucesso":
            st.success("✅ Seus dados foram registrados com sucesso!")
        else:
            st.error(f"❌ Falha ao salvar no Google Sheets: {response.text}")
    except Exception as e:
        st.error(f"❌ Erro na conexão com o Google Sheets: {e}")

# =============================
# 💾 Carregamento do Modelo Roberta
# =============================
@st.cache(allow_output_mutation=True)
def load_model():
    tokenizer = RobertaTokenizer.from_pretrained('roberta-base')
    model = RobertaForSequenceClassification.from_pretrained('roberta-base')
    return tokenizer, model

try:
    tokenizer, model = load_model()
except Exception as e:
    st.error(f"Falha ao carregar o modelo Roberta: {e}")
    st.stop()

# =============================
# 🔧 Funções de Análise de Texto
# =============================
def preprocess_text(text):
    text = text.lower()
    text = re.sub(r'[^a-zA-Z0-9\s]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def analyze_text_roberta(text):
    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True, max_length=512)
    outputs = model(**inputs)
    logits = outputs.logits
    probability = torch.softmax(logits, dim=1)[0, 1].item()
    return probability * 100  # porcentagem

def calculate_entropy(text):
    probabilities = np.array([text.count(c) / len(text) for c in set(text)])
    return -np.sum(probabilities * np.log2(probabilities))

def analyze_text(text):
    clean = preprocess_text(text)
    entropy = calculate_entropy(clean)
    roberta_score = analyze_text_roberta(clean)
    final_score = (roberta_score * 0.7) + (100 * (1 - entropy / 6) * 0.3)
    return {
        'IA (estimada)': f"{final_score:.2f}%",
        'Entropia': f"{entropy:.2f}",
        'Roberta (IA)': f"{roberta_score:.2f}%"
    }

# =============================
# 📄 Funções de PDF
# =============================
def extract_text_from_pdf(pdf_file):
    text = ""
    with pdfplumber.open(io.BytesIO(pdf_file.read())) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""
    return text

class PDFReport(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 16)
        self.cell(0, 10, 'Relatório TotalIA - PEAS.Co', ln=True, align='C')
        self.ln(5)

    def add_results(self, results):
        self.set_font('Arial', '', 12)
        for k, v in results.items():
            self.cell(0, 8, f"{k}: {v}", ln=True)
        self.ln(5)

def generate_pdf_report(results):
    pdf = PDFReport()
    pdf.add_page()
    pdf.multi_cell(0, 8, 'Este relatório apresenta uma estimativa sobre a probabilidade de o texto ter sido gerado por IA.')
    pdf.ln(5)
    pdf.add_results(results)
    filename = "relatorio_IA.pdf"
    pdf.output(filename, 'F')
    return filename

# =============================
# 🖥️ Interface Streamlit
# =============================
st.title("🔍 TotalIA - Detecção de Texto por IA")
st.write("Faça o upload de um PDF para análise:")

uploaded = st.file_uploader("Escolha um arquivo PDF", type="pdf")
if uploaded:
    texto = extract_text_from_pdf(uploaded)
    resultados = analyze_text(texto)

    st.subheader("🔎 Resultados da Análise")
    for key, val in resultados.items():
        st.write(f"**{key}:** {val}")

    report_path = generate_pdf_report(resultados)
    with open(report_path, "rb") as f:
        st.download_button("📥 Baixar Relatório em PDF", f.read(), "relatorio_IA.pdf", "application/pdf")

# =============================
# 📋 Registro de Usuário (ao final)
# =============================
st.markdown("---")
st.subheader("📋 Registro de Usuário")
nome = st.text_input("Nome completo", key="nome")
email = st.text_input("E-mail", key="email")
if st.button("Registrar meus dados"):
    if nome and email:
        salvar_email_google_sheets(nome, email)
    else:
        st.warning("⚠️ Preencha ambos os campos antes de registrar.")

# =============================
# 📣 Seção de Propaganda
# =============================
st.markdown("---")
st.subheader("Publicidade - Anuncie Aqui")
st.write("📧 Envie sua proposta para: peas8810@gmail.com")
# Exemplo de banner — substitua pela sua URL
image_url = "https://via.placeholder.com/728x90.png?text=Anuncie+aqui"
st.image(image_url, use_container_width=True)
st.markdown("### Visite nosso site de parceiros")
st.components.v1.iframe("https://example.com", height=200)

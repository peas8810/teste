# 🍀 TotalIA Adaptado para o Padrão PlagIA - PEAS.Co
# =============================

import streamlit as st
import requests
import PyPDF2
import difflib
import re
import numpy as np
from fpdf import FPDF
from io import BytesIO
import hashlib
from datetime import datetime, date
from PIL import Image
import qrcode
import pdfplumber
import torch
from transformers import RobertaTokenizer, RobertaForSequenceClassification

# 🔗 URL da API gerada no Google Sheets
URL_GOOGLE_SHEETS = "https://script.google.com/macros/s/AKfycbyTpbWDxWkNRh_ZIlHuAVwZaCC2ODqTmo0Un7ZDbgzrVQBmxlYYKuoYf6yDigAPHZiZ/exec"

# =============================
# 📋 Funções Auxiliares
# =============================
def salvar_email_google_sheets(nome, email, codigo):
    dados = {"nome": nome, "email": email, "codigo": codigo, "data": str(date.today())}
    try:
        headers = {'Content-Type': 'application/json'}
        response = requests.post(URL_GOOGLE_SHEETS, json=dados, headers=headers)
        return response.text.strip() == "Sucesso"
    except:
        return False

def gerar_codigo_verificacao(texto):
    return hashlib.md5(texto.encode()).hexdigest()[:10].upper()

@st.cache_resource
def carregar_modelo_roberta():
    tokenizer = RobertaTokenizer.from_pretrained('roberta-base')
    model = RobertaForSequenceClassification.from_pretrained('roberta-base')
    return tokenizer, model

def limpar_texto(texto):
    texto = texto.lower()
    texto = re.sub(r'[^a-zA-Z0-9\s]', '', texto)
    return re.sub(r'\s+', ' ', texto).strip()

def calcular_entropia(texto):
    probs = np.array([texto.count(c) / len(texto) for c in set(texto)])
    return -np.sum(probs * np.log2(probs))

def avaliar_texto_roberta(texto, tokenizer, model):
    inputs = tokenizer(texto, return_tensors="pt", truncation=True, padding=True, max_length=512)
    outputs = model(**inputs)
    prob = torch.softmax(outputs.logits, dim=1)[0, 1].item()
    return prob * 100

def extrair_texto_pdf(file):
    texto = ""
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            texto += page.extract_text() or ""
    return texto.strip()

class PDF(FPDF):
    def _encode_text(self, text):
        try:
            return text.encode('latin-1', 'replace').decode('latin-1')
        except:
            return ''.join(c if ord(c) < 256 else '?' for c in text)

    def header(self):
        self.set_font('Arial', 'B', 16)
        self.cell(0, 10, self._encode_text("Relatório TotalIA - PEAS.Co"), ln=True, align='C')
        self.ln(5)

    def body(self, dados):
        self.set_font('Arial', '', 12)
        for k, v in dados.items():
            self.cell(0, 8, self._encode_text(f"{k}: {v}"), ln=True)
        self.ln(5)

    def explicacao(self, valor_roberta):
        texto = f"""
        A 'Avaliação Roberta' indica a probabilidade de que um texto tenha sido escrito por IA. Valor observado: {valor_roberta}
        O modelo RoBerta analisa padrões linguísticos, coesão e conectores textuais.
        Interpretações:
        - Roberta 0% a 30%: Texto humano
        - 30% a 60%: Zona de incerteza
        - 60% a 100%: Texto com alta probabilidade de ter sido gerado por IA.
        """
        self.multi_cell(0, 8, self._encode_text(texto))


# =============================
# 💻 Interface Streamlit
# =============================

st.title("🔍 TotalIA - Verificação de Texto por Inteligência Artificial")

if "consultas" not in st.session_state:
    st.session_state["consultas"] = 0

st.markdown(f"**Consultas restantes nesta sessão: {4 - st.session_state['consultas']}**")

nome = st.text_input("Nome completo")
email = st.text_input("E-mail")
arquivo_pdf = st.file_uploader("📄 Envie um arquivo PDF", type=["pdf"])

if st.button("🔍 Analisar Texto"):
    if not nome or not email:
        st.warning("⚠️ Nome e e-mail obrigatórios.")
    elif not arquivo_pdf:
        st.warning("⚠️ Envie um PDF.")
    elif st.session_state["consultas"] >= 4:
        st.error("❌ Limite de 4 consultas atingido. Recarregue a página para reiniciar.")
    else:
        texto = extrair_texto_pdf(arquivo_pdf)
        texto_limpo = limpar_texto(texto)
        entropia = calcular_entropia(texto_limpo)
        tokenizer, model = carregar_modelo_roberta()
        score_roberta = avaliar_texto_roberta(texto_limpo, tokenizer, model)
        score_final = (score_roberta * 0.7) + (100 * (1 - entropia / 6) * 0.3)

        resultados = {
            "IA (Estimada)": f"{score_final:.2f}%",
            "Entropia": f"{entropia:.2f}",
            "Roberta (IA)": f"{score_roberta:.2f}%"
        }

        st.success("✅ Análise concluída!")
        for k, v in resultados.items():
            st.write(f"**{k}:** {v}")

        codigo = gerar_codigo_verificacao(texto_limpo)
        salvar_email_google_sheets(nome, email, codigo)

        pdf = PDF()
        pdf.add_page()
        pdf.body(resultados)
        pdf.explicacao(resultados['Roberta (IA)'])
        caminho = "/tmp/relatorio_totalia.pdf"
        pdf.output(caminho, 'F')
        with open(caminho, "rb") as f:
            st.download_button("📥 Baixar Relatório PDF", f, "relatorio_totalia.pdf")

        st.session_state["consultas"] += 1

# --- Apoio via Pix ---
payload = "00020126400014br.gov.bcb.pix0118pesas8810@gmail.com520400005303986540520.005802BR5925PEDRO EMILIO AMADOR SALOM6013TEOFILO OTONI62200516PEASTECHNOLOGIES6304C9DB"

def gerar_qr_code_pix(payload):
    qr = qrcode.QRCode(box_size=10, border=4)
    qr.add_data(payload)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return Image.open(buffer)

st.markdown("---")
st.markdown("""
<h3 style='color: green;'>💚 Apoie Este Projeto com um Pix!</h3>
<p>Temos custos com servidores e IA. Considere uma doação de <strong>R$ 20,00</strong>.</p>
<p><strong>Chave Pix:</strong> <span style='color: blue;'>pesas8810@gmail.com</span></p>
<p><strong>Nome do recebedor:</strong> PEAS TECHNOLOGIES</p>
""", unsafe_allow_html=True)

qr_img = gerar_qr_code_pix(payload)
st.image(qr_img, caption="📲 Escaneie o QR Code para doar via Pix (R$ 20,00)", width=300)
st.success("🙏 Obrigado pela sua contribuição!")

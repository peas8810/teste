# appy.py (Streamlit Interface)
import streamlit as st
import requests
import os
from io import BytesIO

API_URL = "https://geral-pdf.onrender.com"  # URL da API FastAPI

st.set_page_config(page_title="Conversor de Documentos", layout="centered")
st.title("📄 Conversor de Documentos com IA")

abas = [
    ("Word → PDF", "/word-para-pdf", ["doc", "docx", "odt", "rtf"], True),
    ("Word → PDF (Lote)", "/word-para-pdf", ["doc", "docx", "odt", "rtf"], True),
    ("PDF → Word", "/pdf-para-word", ["pdf"], False),
    ("PDF → JPG", "/pdf-para-jpg", ["pdf"], False),
    ("Imagem → PDF", "/jpg-para-pdf", ["jpg", "jpeg", "png"], True),
    ("Juntar PDF", "/juntar-pdfs", ["pdf"], True),
    ("Dividir PDF", "/dividir-pdf", ["pdf"], False),
    ("OCR em PDF", "/ocr-pdf", ["pdf"], False),
    ("OCR em Imagens", "/ocr-imagem", ["jpg", "jpeg", "png"], True),
    ("PDF → PDF/A", "/pdf-para-pdfa", ["pdf"], False)
]

aba_escolhida = st.selectbox("Escolha a funcionalidade:", [a[0] for a in abas])
selecionada = next(a for a in abas if a[0] == aba_escolhida)

multiplos = selecionada[3]
tipos = selecionada[2]
endpoint = selecionada[1]

arquivos = st.file_uploader("Envie o(s) arquivo(s):", type=tipos, accept_multiple_files=multiplos)

if st.button("🔄 Processar"):
    if not arquivos:
        st.warning("Por favor, envie ao menos um arquivo válido.")
    else:
        with st.spinner("Processando com IA..."):
            try:
                files = [
                    ("files", (arq.name, BytesIO(arq.getvalue()), arq.type)) for arq in arquivos if arq is not None
                ]

                if not files:
                    st.error("Erro: Nenhum arquivo válido para processar.")
                else:
                    response = requests.post(API_URL + endpoint, files=files)

                    if response.status_code == 200:
                        content_type = response.headers.get("content-type", "")

                        if "application/json" in content_type:
                            dados = response.json()
                            chaves = dados.get("arquivos") or dados.get("imagens")
                            if chaves:
                                for caminho in chaves:
                                    nome = os.path.basename(caminho)
                                    st.success(f"✅ Arquivo gerado: {nome}")
                            else:
                                st.json(dados)
                        else:
                            st.download_button("📥 Baixar Resultado", data=response.content, file_name="resultado")
                    else:
                        st.error(f"Erro: {response.status_code} - {response.text}")
            except Exception as e:
                st.error(f"Erro ao processar: {str(e)}")

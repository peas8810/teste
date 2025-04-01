# -*- coding: utf-8 -*-

# ============================================
# 📅 Importações
# ============================================
import streamlit as st
import os
import shutil
import subprocess
import zipfile
import requests
from io import BytesIO
from PIL import Image
from PyPDF2 import PdfMerger, PdfReader, PdfWriter
from pdf2docx import Converter
from pdf2image import convert_from_path
import pytesseract
import img2pdf
import re
import tempfile
import time
from typing import List

# Configuração do Streamlit
st.set_page_config(page_title="Conversor de Documentos", page_icon="📄", layout="wide")

# Diretório de trabalho
@st.cache_resource
def get_work_dir():
    temp_dir = tempfile.mkdtemp(prefix="doc_converter_")
    os.makedirs(temp_dir, exist_ok=True)
    return temp_dir

WORK_DIR = get_work_dir()

# OCR
pytesseract.pytesseract.tesseract_cmd = shutil.which("tesseract") or "/usr/bin/tesseract"

# ============================================
# 🧼 Utilitários
# ============================================
def sanitize_filename(filename: str) -> str:
    return re.sub(r'[^a-zA-Z0-9_.-]', '_', filename)

def salvar_arquivos(uploaded_files) -> List[str]:
    caminhos = []
    for uploaded_file in uploaded_files:
        nome_limpo = sanitize_filename(uploaded_file.name)
        caminho = os.path.join(WORK_DIR, nome_limpo)
        with open(caminho, "wb") as f:
            f.write(uploaded_file.getbuffer())
        caminhos.append(caminho)
    return caminhos

def limpar_diretorio():
    for filename in os.listdir(WORK_DIR):
        try:
            file_path = os.path.join(WORK_DIR, filename)
            if os.path.isfile(file_path):
                os.unlink(file_path)
        except Exception as e:
            st.error(f"Erro ao excluir {file_path}: {e}")

def criar_link_download(nome_arquivo: str, label: str):
    caminho = os.path.join(WORK_DIR, nome_arquivo)
    with open(caminho, "rb") as f:
        st.download_button(label=label, data=f, file_name=nome_arquivo, mime="application/octet-stream")

# ============================================
# 🔄 Conversão Word → Imagem → PDF com PHP
# ============================================
def word_para_pdf_php():
    st.header("📄 Word → Imagem → PDF (via PHPWord + DomPDF)")
    arquivos = st.file_uploader("Carregue arquivos Word (.docx)", type=["docx"], accept_multiple_files=True)

    if arquivos and st.button("Converter para PDF"):
        with st.spinner("Convertendo arquivos com PHP..."):
            for arquivo in arquivos:
                nome_docx = sanitize_filename(arquivo.name)
                nome_pdf = nome_docx.replace(".docx", ".pdf")
                caminho_docx = os.path.join(WORK_DIR, nome_docx)
                caminho_pdf = os.path.join(WORK_DIR, nome_pdf)

                # Salva o arquivo
                with open(caminho_docx, "wb") as f:
                    f.write(arquivo.getbuffer())

                # Chama o script PHP
                try:
                    resultado = subprocess.run(
                        ["php", "/mnt/data/converter.php", caminho_docx, caminho_pdf],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True
                    )

                    if resultado.returncode == 0 and os.path.exists(caminho_pdf):
                        st.success(f"{nome_docx} convertido com sucesso!")
                        criar_link_download(nome_pdf, f"📥 Baixar {nome_pdf}")
                    else:
                        st.error(f"Erro ao converter {nome_docx}.")
                        st.text_area("Detalhes do erro", resultado.stderr)
                except Exception as e:
                    st.error(f"Erro ao chamar PHP: {str(e)}")

# ============================================
# 🏠 Interface Principal
# ============================================
def main():
    st.title("📄 Conversor de Documentos com PHP")
    st.sidebar.title("Menu")

    opcao = st.sidebar.selectbox("Escolha a operação:", [
        "Word para PDF (via PHPWord + DomPDF)"
    ])

    if opcao == "Word para PDF (via PHPWord + DomPDF)":
        word_para_pdf_php()

    if st.sidebar.button("🧹 Limpar arquivos temporários"):
        limpar_diretorio()
        st.sidebar.success("Arquivos temporários limpos!")

if __name__ == "__main__":
    main()

# app.py (Streamlit Interface)
import streamlit as st
import requests
import os
from io import BytesIO

API_URL = "https://geral-pdf.onrender.com"  # URL da API FastAPI

st.set_page_config(page_title="Conversor de Documentos", layout="centered")
st.title("📄 Conversor de Documentos")

# Configuração das abas
abas = [
    ("Word → PDF", "/word-para-pdf", ["doc", "docx", "odt", "rtf"], True),
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

arquivos = st.file_uploader(
    "Envie o(s) arquivo(s):",
    type=tipos,
    accept_multiple_files=multiplos
)

if st.button("🔄 Processar"):
    if not arquivos:
        st.warning("Por favor, envie ao menos um arquivo válido.")
    else:
        with st.spinner("Processando..."):
            try:
                # Converter para lista se for único arquivo
                if not isinstance(arquivos, list):
                    arquivos = [arquivos]

                # Preparar arquivos para envio
                files = []
                for arq in arquivos:
                    if arq is not None:
                        files.append(("files", (arq.name, arq.getvalue(), arq.type)))

                # Enviar para API
                response = requests.post(
                    API_URL + endpoint,
                    files=files,
                    timeout=60  # Aumentar timeout para processamentos demorados
                )

                if response.status_code == 200:
                    content_type = response.headers.get("content-type", "")

                    if "application/json" in content_type:
                        dados = response.json()
                        if "arquivos" in dados or "imagens" in dados:
                            arquivos_gerados = dados.get("arquivos", []) + dados.get("imagens", [])
                            if arquivos_gerados:
                                for caminho in arquivos_gerados:
                                    nome = os.path.basename(caminho)
                                    # Tentar baixar o arquivo gerado
                                    try:
                                        download_response = requests.get(f"{API_URL}/download?path={caminho}")
                                        if download_response.status_code == 200:
                                            st.download_button(
                                                label=f"📥 Baixar {nome}",
                                                data=download_response.content,
                                                file_name=nome
                                            )
                                        else:
                                            st.success(f"✅ Arquivo gerado: {nome}")
                                    except:
                                        st.success(f"✅ Arquivo gerado: {nome}")
                            else:
                                st.error("Nenhum arquivo foi gerado durante o processamento.")
                        else:
                            st.error("Resposta inesperada da API.")
                    elif "application/pdf" in content_type or "image/" in content_type or "application/vnd.openxmlformats-officedocument.wordprocessingml.document" in content_type:
                        extensao = "pdf" if "application/pdf" in content_type else "docx" if "application/vnd.openxmlformats-officedocument.wordprocessingml.document" in content_type else "jpg"
                        st.download_button(
                            label="📥 Baixar Resultado",
                            data=response.content,
                            file_name=f"resultado.{extensao}"
                        )
                    else:
                        st.error("Tipo de resposta não suportado.")
                else:
                    st.error(f"Erro na API: {response.status_code} - {response.text}")
            except Exception as e:
                st.error(f"Erro ao processar: {str(e)}")

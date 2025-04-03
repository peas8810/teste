# app.py (Streamlit)
import streamlit as st
import requests
import os

st.set_page_config(page_title="Conversor de Documentos", layout="centered")
st.title("📄 Conversor de Documentos com IA")

# APIs separadas por serviço
API_RENDER = "https://geral-pdf.onrender.com"
API_WORD = "https://testepdf-production.up.railway.app"
API_JPG = "https://testejpeg-production.up.railway.app"

abas = [
    ("Word → PDF", API_WORD + "/convert", ["doc", "docx"], False),
    ("PDF → JPG", API_JPG + "/pdf-para-jpg", ["pdf"], False),
    ("PDF → Word", API_RENDER + "/pdf-para-word", ["pdf"], False),
    ("Imagem → PDF", API_RENDER + "/jpg-para-pdf", ["jpg", "jpeg", "png"], True),
    ("Juntar PDF", API_RENDER + "/juntar-pdfs", ["pdf"], True),
    ("Dividir PDF", API_RENDER + "/dividir-pdf", ["pdf"], False),
    ("OCR em PDF", API_RENDER + "/ocr-pdf", ["pdf"], False),
    ("OCR em Imagem", API_RENDER + "/ocr-imagem", ["jpg", "jpeg", "png"], True),
    ("PDF → PDF/A", API_RENDER + "/pdf-para-pdfa", ["pdf"], False)
]

aba_escolhida = st.selectbox("Escolha a funcionalidade:", [a[0] for a in abas])
nome, endpoint, tipos, multiplo = next(a for a in abas if a[0] == aba_escolhida)

arquivos = st.file_uploader("Envie o(s) arquivo(s):", type=tipos, accept_multiple_files=multiplo)

if st.button("🔄 Processar"):
    if not arquivos:
        st.warning("Por favor, envie ao menos um arquivo.")
    else:
        with st.spinner("Processando..."):
            try:
                if not isinstance(arquivos, list):
                    arquivos = [arquivos]

                files = []
                key = "files" if multiplo or nome not in ["PDF → Word", "OCR em PDF", "PDF → JPG", "PDF → PDF/A"] else "file"
                for arq in arquivos:
                    files.append((key, (arq.name, arq.read(), arq.type)))

                response = requests.post(endpoint, files=files)

                if response.status_code == 200:
                    content_type = response.headers.get("content-type", "")
                    if "application/json" in content_type:
                        dados = response.json()
                        chaves = dados.get("arquivos") or dados.get("imagens")
                        if chaves:
                            for item in chaves:
                                nome_arquivo = os.path.basename(item)
                                st.success(f"✅ Arquivo gerado: {nome_arquivo}")
                        else:
                            st.info("✅ Processado, mas nenhum arquivo retornado.")
                            st.json(dados)
                    else:
                        st.download_button("📥 Baixar Resultado", data=response.content, file_name="resultado")
                else:
                    st.error(f"Erro {response.status_code}: {response.text}")
            except Exception as e:
                st.error(f"Erro ao processar: {e}")

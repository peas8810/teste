# ============================================
# 📅 Importações
# ============================================
import streamlit as st
import os
import shutil
import re
import zipfile
import requests
from io import BytesIO
from PIL import Image
from PyPDF2 import PdfMerger, PdfReader, PdfWriter
from pdf2docx import Converter
from pdf2image import convert_from_path
import pytesseract
import img2pdf
import subprocess
import unicodedata
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from typing import List, Optional, Tuple

# Configuração de cache para melhor performance
st.set_page_config(page_title="Conversor de Documentos", page_icon="📄", layout="wide")

# ============================================
# 🔐 Configurações de Segurança (Mover para variáveis de ambiente)
# ============================================
# NOTA: Em produção, substitua por variáveis de ambiente ou um serviço de gerenciamento de segredos
CLIENT_ID = st.secrets.get("MS_GRAPH_CLIENT_ID", "3290c2d6-65ed-4a1d-bac3-93882999cb21")
TENANT_ID = st.secrets.get("MS_GRAPH_TENANT_ID", "eef3c8f5-161e-4227-b779-7bb58821ba2d")
CLIENT_SECRET = st.secrets.get("MS_GRAPH_CLIENT_SECRET", "04H8Q~4Pklz1rb4SItbigqnY5s9zkrU_U3WF4a1B")
SCOPE = "https://graph.microsoft.com/.default"
AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"
GRAPH_ENDPOINT = "https://graph.microsoft.com/v1.0/me/drive/root:/{path}:/content"

# ============================================
# 📁 Configuração de diretórios temporários
# ============================================
@st.cache_resource
def get_work_dir():
    """Cria e retorna um diretório temporário seguro para processamento"""
    temp_dir = tempfile.mkdtemp(prefix="doc_converter_")
    os.makedirs(temp_dir, exist_ok=True)
    return temp_dir

WORK_DIR = get_work_dir()

# Configuração do Tesseract OCR
pytesseract.pytesseract.tesseract_cmd = shutil.which("tesseract") or "/usr/bin/tesseract"

# ============================================
# 🛠️ Utilitários Avançados
# ============================================
def sanitize_filename(filename: str) -> str:
    """Sanitiza nomes de arquivos removendo caracteres especiais e normalizando"""
    # Normaliza caracteres unicode (remove acentos)
    filename = unicodedata.normalize('NFKD', filename).encode('ascii', 'ignore').decode('ascii')
    
    # Remove caracteres especiais
    filename = re.sub(r'[^\w\-_. ]', '', filename)
    
    # Substitui espaços por underscores
    filename = filename.replace(' ', '_')
    
    # Limita o tamanho do nome
    max_length = 100
    if len(filename) > max_length:
        name, ext = os.path.splitext(filename)
        filename = name[:max_length - len(ext)] + ext
    
    return filename

def salvar_arquivos(uploaded_files) -> List[str]:
    """Salva arquivos carregados no diretório de trabalho com nomes sanitizados"""
    caminhos = []
    for uploaded_file in uploaded_files:
        nome_sanitizado = sanitize_filename(uploaded_file.name)
        caminho = os.path.join(WORK_DIR, nome_sanitizado)
        
        try:
            with open(caminho, "wb") as f:
                f.write(uploaded_file.getbuffer())
            caminhos.append(caminho)
        except Exception as e:
            st.error(f"Erro ao salvar arquivo {uploaded_file.name}: {str(e)}")
    
    return caminhos

def limpar_diretorio():
    """Limpa o diretório de trabalho de forma segura"""
    try:
        for filename in os.listdir(WORK_DIR):
            file_path = os.path.join(WORK_DIR, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                st.warning(f"Não foi possível excluir {file_path}: {str(e)}")
    except Exception as e:
        st.error(f"Erro ao limpar diretório: {str(e)}")

def criar_link_download(nome_arquivo: str, label: str, mime_type: str = "application/octet-stream"):
    """Cria um botão de download para o arquivo processado"""
    try:
        file_path = os.path.join(WORK_DIR, nome_arquivo)
        with open(file_path, "rb") as f:
            st.download_button(
                label=label,
                data=f,
                file_name=nome_arquivo,
                mime=mime_type,
                key=f"download_{nome_arquivo}_{time.time()}"  # Chave única para evitar caching
            )
    except Exception as e:
        st.error(f"Erro ao criar link de download: {str(e)}")

# ============================================
# 🔑 Autenticação com Microsoft Graph (Melhorada)
# ============================================
@st.cache_data(ttl=3600)  # Cache do token por 1 hora
def obter_token():
    try:
        data = {
            "client_id": CLIENT_ID,
            "scope": "https://graph.microsoft.com/.default",
            "client_secret": CLIENT_SECRET,
            "grant_type": "client_credentials"
        }
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        resposta = requests.post(AUTHORITY, data=data, headers=headers, timeout=10)
        resposta.raise_for_status()
        
        token = resposta.json().get("access_token")
        if not token:
            st.error("Token de acesso não recebido")
            return None
            
        return token
    except Exception as e:
        st.error(f"Erro na autenticação: {str(e)}")
        return None

# ============================================
# 📄 Word → PDF via Microsoft Graph (Melhorada)
# ============================================
def upload_arquivo_graph(token: str, file_content: bytes, file_name: str) -> Tuple[bool, str]:
    """Faz upload de arquivo para o Microsoft Graph"""
    try:
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/octet-stream"
        }
        
        upload_url = GRAPH_ENDPOINT.format(path=file_name)
        response = requests.put(upload_url, headers=headers, data=file_content, timeout=30)
        
        if response.status_code in (200, 201):
            return True, response.json().get("id", "")
        else:
            error_msg = response.json().get("error", {}).get("message", "Erro desconhecido")
            return False, f"Status {response.status_code}: {error_msg}"
    except Exception as e:
        return False, str(e)

def converter_word_pdf_graph(token: str, file_id: str, output_name: str) -> Tuple[bool, bytes]:
    """Converte documento Word para PDF usando Microsoft Graph"""
    try:
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        convert_url = f"https://graph.microsoft.com/v1.0/me/drive/items/{file_id}/content?format=pdf"
        response = requests.get(convert_url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            return True, response.content
        else:
            error_msg = response.json().get("error", {}).get("message", "Erro desconhecido")
            return False, f"Status {response.status_code}: {error_msg}".encode()
    except Exception as e:
        return False, str(e).encode()

def word_para_pdf():
    st.header("Word para PDF (.docx)")
    arquivos = st.file_uploader("Carregue arquivos Word", type=["docx"], accept_multiple_files=True)

    if arquivos and st.button("Converter para PDF"):
        token = obter_token()
        if not token:
            st.error("Falha na autenticação")
            return

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/octet-stream"
        }

        for arquivo in arquivos:
            nome_limpo = sanitize_filename(arquivo.name)
            nome_base = os.path.splitext(nome_limpo)[0]
            pdf_nome = f"{nome_base}.pdf"

            try:
                # 1. Upload para local temporário
                upload_url = "https://graph.microsoft.com/v1.0/drive/root:/ConversorTemp/" + nome_limpo + ":/content"
                
                upload = requests.put(
                    upload_url,
                    headers=headers,
                    data=arquivo.getvalue()
                )

                if upload.status_code not in (200, 201):
                    error_msg = upload.json().get("error", {}).get("message", "Erro desconhecido")
                    raise Exception(f"Upload falhou: {error_msg}")

                # 2. Converter para PDF
                file_id = upload.json().get("id")
                pdf_url = f"https://graph.microsoft.com/v1.0/drive/items/{file_id}/content?format=pdf"
                
                pdf_res = requests.get(pdf_url, headers=headers)
                if pdf_res.status_code != 200:
                    raise Exception("Conversão falhou")

                # 3. Salvar resultado
                with open(os.path.join(WORK_DIR, pdf_nome), "wb") as f:
                    f.write(pdf_res.content)

                st.success(f"Conversão concluída: {pdf_nome}")
                criar_link_download(pdf_nome, f"📥 Baixar {pdf_nome}")

            except Exception as e:
                st.error(f"Erro ao processar {arquivo.name}: {str(e)}")

# ============================================
# 📤 Outras Funcionalidades (Melhoradas)
# ============================================
def pdf_para_word():
    """Converte PDF para Word (DOCX)"""
    st.header("📄 PDF para Word (.docx)")
    st.warning("Nota: A conversão pode não preservar perfeitamente o layout em documentos complexos.")
    
    uploaded_file = st.file_uploader(
        "Carregue um arquivo PDF", 
        type=["pdf"],
        accept_multiple_files=False,
        help="PDFs com até 50 páginas para melhor performance"
    )
    
    if not uploaded_file:
        return
    
    if st.button("Converter para Word", key="pdf_to_word"):
        try:
            with st.spinner("Convertendo PDF para Word..."):
                caminho = salvar_arquivos([uploaded_file])[0]
                nome_base = os.path.splitext(os.path.basename(caminho))[0]
                saida = os.path.join(WORK_DIR, f"{nome_base}.docx")
                
                # Usa ThreadPool para evitar bloqueio da interface
                with ThreadPoolExecutor() as executor:
                    future = executor.submit(Converter(caminho).convert, saida)
                    future.result()  # Espera a conclusão
                
                st.success("Conversão concluída!")
                criar_link_download(
                    f"{nome_base}.docx", 
                    f"📥 Baixar {nome_base}.docx",
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )
        except Exception as e:
            st.error(f"Erro na conversão: {str(e)}")

def pdf_para_jpg():
    """Converte PDF para imagens JPG"""
    st.header("📄 PDF para JPG")
    st.info("Cada página do PDF será convertida em uma imagem separada.")
    
    uploaded_file = st.file_uploader(
        "Carregue um arquivo PDF",
        type=["pdf"],
        accept_multiple_files=False,
        help="PDFs com até 20 páginas para melhor performance"
    )
    
    if not uploaded_file:
        return
    
    if st.button("Converter para JPG", key="pdf_to_jpg"):
        try:
            with st.spinner("Convertendo PDF para imagens..."):
                caminho = salvar_arquivos([uploaded_file])[0]
                nome_base = os.path.splitext(os.path.basename(caminho))[0]
                
                # Configuração para melhor qualidade
                imagens = convert_from_path(
                    caminho,
                    dpi=300,
                    fmt='jpeg',
                    thread_count=4,
                    poppler_path=shutil.which("poppler") or "/usr/bin"
                )
                
                # Cria um ZIP com todas as imagens
                zip_nome = f"pdf_images_{nome_base}.zip"
                zip_path = os.path.join(WORK_DIR, zip_nome)
                
                with zipfile.ZipFile(zip_path, 'w') as zipf:
                    for i, img in enumerate(imagens):
                        img_nome = f"{nome_base}_pag{i+1}.jpg"
                        img_path = os.path.join(WORK_DIR, img_nome)
                        img.save(img_path, "JPEG", quality=90)
                        zipf.write(img_path, img_nome)
                
                st.success(f"Convertido {len(imagens)} páginas!")
                criar_link_download(zip_nome, "📥 Baixar todas as imagens (ZIP)", "application/zip")
                
        except Exception as e:
            st.error(f"Erro na conversão: {str(e)}")

def juntar_pdf():
    """Junta múltiplos PDFs em um único arquivo"""
    st.header("🔗 Juntar PDFs")
    st.info("Os PDFs serão unidos na ordem em que são carregados.")
    
    uploaded_files = st.file_uploader(
        "Carregue os PDFs para juntar",
        type=["pdf"],
        accept_multiple_files=True,
        help="Selecione 2 ou mais arquivos PDF"
    )
    
    if not uploaded_files or len(uploaded_files) < 2:
        return
    
    # Ordenar arquivos (opcional)
    if st.checkbox("Ordenar arquivos alfabeticamente"):
        uploaded_files.sort(key=lambda x: x.name)
    
    if st.button("Juntar PDFs", key="merge_pdfs"):
        try:
            with st.spinner("Unindo PDFs..."):
                caminhos = salvar_arquivos(uploaded_files)
                nome_saida = "merged_" + "_".join([os.path.splitext(f.name)[0] for f in uploaded_files[:3]]) + ".pdf"
                if len(nome_saida) > 100:  # Limita tamanho do nome
                    nome_saida = "merged_resultado.pdf"
                
                saida = os.path.join(WORK_DIR, nome_saida)
                
                merger = PdfMerger()
                for c in caminhos:
                    merger.append(c)
                merger.write(saida)
                merger.close()
                
                st.success(f"PDFs unidos em {nome_saida}!")
                criar_link_download(nome_saida, f"📥 Baixar {nome_saida}", "application/pdf")
                
        except Exception as e:
            st.error(f"Erro ao unir PDFs: {str(e)}")

def dividir_pdf():
    """Divide um PDF em páginas individuais"""
    st.header("✂️ Dividir PDF")
    st.info("Cada página do PDF será salva como um arquivo separado.")
    
    uploaded_file = st.file_uploader(
        "Carregue um PDF para dividir",
        type=["pdf"],
        accept_multiple_files=False,
        help="PDFs com até 50 páginas para melhor performance"
    )
    
    if not uploaded_file:
        return
    
    if st.button("Dividir PDF", key="split_pdf"):
        try:
            with st.spinner("Dividindo PDF..."):
                caminho = salvar_arquivos([uploaded_file])[0]
                nome_base = os.path.splitext(os.path.basename(caminho))[0]
                
                reader = PdfReader(caminho)
                total_paginas = len(reader.pages)
                
                # Cria um ZIP com todas as páginas
                zip_nome = f"split_{nome_base}.zip"
                zip_path = os.path.join(WORK_DIR, zip_nome)
                
                with zipfile.ZipFile(zip_path, 'w') as zipf:
                    for i, page in enumerate(reader.pages):
                        writer = PdfWriter()
                        writer.add_page(page)
                        nome_saida = f"{nome_base}_pag{i+1}.pdf"
                        out_path = os.path.join(WORK_DIR, nome_saida)
                        
                        with open(out_path, "wb") as f:
                            writer.write(f)
                        
                        zipf.write(out_path, nome_saida)
                
                st.success(f"PDF dividido em {total_paginas} páginas!")
                criar_link_download(zip_nome, f"📥 Baixar todas as páginas (ZIP)", "application/zip")
                
        except Exception as e:
            st.error(f"Erro ao dividir PDF: {str(e)}")

def ocr_pdf():
    """Extrai texto de PDFs usando OCR"""
    st.header("🔍 OCR em PDF (Reconhecimento de Texto)")
    st.warning("Nota: O processo pode ser lento para PDFs grandes ou com muitas páginas.")
    
    uploaded_file = st.file_uploader(
        "Carregue um PDF para extrair texto",
        type=["pdf"],
        accept_multiple_files=False,
        help="PDFs com até 20 páginas para melhor performance"
    )
    
    if not uploaded_file:
        return
    
    # Opções de configuração
    col1, col2 = st.columns(2)
    with col1:
        linguagem = st.selectbox("Idioma do texto", ["por", "eng", "spa", "fra", "deu"], index=0)
    with col2:
        dpi = st.slider("Qualidade (DPI)", 200, 600, 300)
    
    if st.button("Extrair Texto (OCR)", key="ocr_pdf"):
        try:
            with st.spinner("Processando OCR..."):
                caminho = salvar_arquivos([uploaded_file])[0]
                nome_base = os.path.splitext(os.path.basename(caminho))[0]
                nome_saida = f"ocr_{nome_base}.txt"
                txt_path = os.path.join(WORK_DIR, nome_saida)
                
                # Configuração do OCR
                config_tesseract = f'--oem 3 --psm 6 -l {linguagem}'
                
                imagens = convert_from_path(
                    caminho,
                    dpi=dpi,
                    thread_count=4,
                    poppler_path=shutil.which("poppler") or "/usr/bin"
                )
                
                texto = ""
                progress_bar = st.progress(0)
                
                for i, img in enumerate(imagens):
                    progress = (i + 1) / len(imagens)
                    progress_bar.progress(progress)
                    
                    texto += f"\n\n--- Página {i+1} ---\n\n"
                    texto += pytesseract.image_to_string(img, config=config_tesseract)
                
                with open(txt_path, "w", encoding="utf-8") as f:
                    f.write(texto)
                
                progress_bar.empty()
                st.success("Texto extraído com sucesso!")
                criar_link_download(nome_saida, f"📥 Baixar texto extraído", "text/plain")
                
        except Exception as e:
            st.error(f"Erro no OCR: {str(e)}")

def ocr_imagem():
    """Extrai texto de imagens usando OCR"""
    st.header("🖼️ OCR em Imagens (Reconhecimento de Texto)")
    
    uploaded_files = st.file_uploader(
        "Carregue imagens para extrair texto",
        type=["jpg", "jpeg", "png", "bmp", "tiff"],
        accept_multiple_files=True,
        help="Formatos suportados: JPG, PNG, BMP, TIFF"
    )
    
    if not uploaded_files:
        return
    
    # Opções de configuração
    col1, col2 = st.columns(2)
    with col1:
        linguagem = st.selectbox("Idioma do texto", ["por", "eng", "spa", "fra", "deu"], index=0)
    with col2:
        dpi = st.slider("Qualidade (DPI)", 200, 600, 300) if st.checkbox("Redimensionar imagem") else None
    
    if st.button("Extrair Texto (OCR)", key="ocr_images"):
        try:
            with st.spinner("Processando imagens..."):
                caminhos = salvar_arquivos(uploaded_files)
                nome_saida = "ocr_images.txt"
                txt_path = os.path.join(WORK_DIR, nome_saida)
                
                config_tesseract = f'--oem 3 --psm 6 -l {linguagem}'
                texto = ""
                progress_bar = st.progress(0)
                
                for i, caminho in enumerate(caminhos):
                    progress = (i + 1) / len(caminhos)
                    progress_bar.progress(progress)
                    
                    try:
                        img = Image.open(caminho)
                        
                        # Redimensiona se necessário
                        if dpi:
                            img = img.resize(
                                (int(img.width * dpi / 72), int(img.height * dpi / 72)),
                                Image.Resampling.LANCZOS
                            )
                        
                        texto += f"\n\n--- Imagem {i+1}: {os.path.basename(caminho)} ---\n\n"
                        texto += pytesseract.image_to_string(img, config=config_tesseract)
                    except Exception as img_error:
                        st.warning(f"Erro ao processar imagem {i+1}: {str(img_error)}")
                        continue
                
                with open(txt_path, "w", encoding="utf-8") as f:
                    f.write(texto)
                
                progress_bar.empty()
                st.success("Texto extraído com sucesso!")
                criar_link_download(nome_saida, "📥 Baixar texto extraído", "text/plain")
                
        except Exception as e:
            st.error(f"Erro no OCR: {str(e)}")

def jpg_para_pdf():
    """Converte imagens para PDF"""
    st.header("🖼️ Imagens para PDF")
    st.info("Todas as imagens serão combinadas em um único PDF.")
    
    uploaded_files = st.file_uploader(
        "Carregue imagens para converter em PDF",
        type=["jpg", "jpeg", "png", "bmp", "tiff"],
        accept_multiple_files=True,
        help="Formatos suportados: JPG, PNG, BMP, TIFF"
    )
    
    if not uploaded_files:
        return
    
    # Opções de configuração
    tamanho_pagina = st.selectbox(
        "Tamanho da página",
        ["A4", "A3", "Letter", "Legal", "Personalizado"],
        index=0
    )
    
    orientacao = st.radio(
        "Orientação",
        ["Retrato", "Paisagem"],
        index=0
    )
    
    if st.button("Converter para PDF", key="images_to_pdf"):
        try:
            with st.spinner("Criando PDF..."):
                caminhos = salvar_arquivos(uploaded_files)
                nome_saida = "images_combined.pdf"
                caminho_pdf = os.path.join(WORK_DIR, nome_saida)
                
                # Configuração do tamanho da página
                if tamanho_pagina == "A4":
                    pagesize = img2pdf.get_fixed_dpi_a4size()
                elif tamanho_pagina == "A3":
                    pagesize = img2pdf.get_fixed_dpi_a3size()
                elif tamanho_pagina == "Letter":
                    pagesize = img2pdf.get_fixed_dpi_lettersize()
                elif tamanho_pagina == "Legal":
                    pagesize = img2pdf.get_fixed_dpi_legalsize()
                else:
                    pagesize = None  # Usa tamanho da imagem
                
                # Configuração de layout
                layout_fun = img2pdf.get_layout_fun(
                    pagesize=pagesize,
                    orientation=orientacao.lower()
                ) if pagesize else None
                
                # Converte imagens para PDF
                with open(caminho_pdf, "wb") as f:
                    if layout_fun:
                        f.write(img2pdf.convert(
                            [Image.open(img).filename for img in caminhos],
                            layout_fun=layout_fun
                        ))
                    else:
                        f.write(img2pdf.convert(
                            [Image.open(img).filename for img in caminhos]
                        ))
                
                st.success("PDF criado com sucesso!")
                criar_link_download(nome_saida, "📥 Baixar PDF", "application/pdf")
                
        except Exception as e:
            st.error(f"Erro ao converter imagens para PDF: {str(e)}")

def pdf_para_pdfa():
    """Converte PDF para padrão PDF/A (arquivável)"""
    st.header("📄 PDF para PDF/A (Arquivável)")
    st.warning("Nota: Requer Ghostscript instalado no servidor.")
    
    uploaded_file = st.file_uploader(
        "Carregue um PDF para converter para PDF/A",
        type=["pdf"],
        accept_multiple_files=False,
        help="PDFs com até 50 páginas para melhor performance"
    )
    
    if not uploaded_file:
        return
    
    # Opções de conversão
    pdfa_version = st.selectbox(
        "Versão PDF/A",
        ["PDF/A-1", "PDF/A-2", "PDF/A-3"],
        index=1
    )
    
    if st.button("Converter para PDF/A", key="pdf_to_pdfa"):
        try:
            with st.spinner("Convertendo para PDF/A..."):
                caminho = salvar_arquivos([uploaded_file])[0]
                nome_base = os.path.splitext(os.path.basename(caminho))[0]
                nome_saida = f"pdfa_{nome_base}.pdf"
                saida = os.path.join(WORK_DIR, nome_saida)
                
                # Configura Ghostscript
                gs_path = shutil.which("gs") or "/usr/bin/gs"
                pdfa_num = pdfa_version.split("-")[1][0]  # 1, 2 ou 3
                
                comando = [
                    gs_path,
                    f"-dPDFA={pdfa_num}",
                    "-dBATCH",
                    "-dNOPAUSE",
                    "-dNOOUTERSAVE",
                    "-sProcessColorModel=DeviceRGB",
                    "-sDEVICE=pdfwrite",
                    "-sPDFACompatibilityPolicy=1",
                    f"-sOutputFile={saida}",
                    caminho
                ]
                
                # Executa Ghostscript
                resultado = subprocess.run(
                    comando,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                
                if os.path.exists(saida) and resultado.returncode == 0:
                    st.success("PDF/A gerado com sucesso!")
                    criar_link_download(nome_saida, f"📥 Baixar {nome_saida}", "application/pdf")
                else:
                    st.error("Falha na conversão para PDF/A.")
                    if resultado.stderr:
                        st.text_area("Detalhes do erro:", value=resultado.stderr, height=100)
        except Exception as e:
            st.error(f"Erro ao executar Ghostscript: {str(e)}")

# ============================================
# 🏠 Interface Principal
# ============================================
def main():
    st.title("📄 Conversor de Documentos Avançado")
    st.markdown("""
    **Ferramenta completa para conversão entre diversos formatos de documentos.**
    """)
    
    # Menu lateral
    with st.sidebar:
        st.title("🔧 Menu")
        opcao = st.selectbox(
            "Selecione a operação",
            [
                "Word para PDF",
                "PDF para Word",
                "PDF para JPG",
                "Juntar PDFs",
                "Dividir PDF",
                "OCR em PDF",
                "OCR em Imagens",
                "Imagens para PDF",
                "PDF para PDF/A"
            ],
            index=0
        )
        
        st.markdown("---")
        if st.button("🧹 Limpar arquivos temporários"):
            limpar_diretorio()
            st.success("Arquivos temporários removidos!")
        
        st.markdown("---")
        st.markdown("""
        **📌 Dicas:**
        - Arquivos grandes podem demorar mais para processar
        - Para melhor qualidade no OCR, use imagens nítidas
        - O Word para PDF usa a API da Microsoft
        """)
        
        st.markdown("---")
        st.markdown("🛠️ Desenvolvido com Streamlit")
    
    # Roteamento das funções
    if opcao == "Word para PDF":
        word_para_pdf()
    elif opcao == "PDF para Word":
        pdf_para_word()
    elif opcao == "PDF para JPG":
        pdf_para_jpg()
    elif opcao == "Juntar PDFs":
        juntar_pdf()
    elif opcao == "Dividir PDF":
        dividir_pdf()
    elif opcao == "OCR em PDF":
        ocr_pdf()
    elif opcao == "OCR em Imagens":
        ocr_imagem()
    elif opcao == "Imagens para PDF":
        jpg_para_pdf()
    elif opcao == "PDF para PDF/A":
        pdf_para_pdfa()

if __name__ == "__main__":
    main()

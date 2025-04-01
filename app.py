# ============================================
# 📅 Importações
# ============================================
import streamlit as st
import os
import shutil
import re
import zipfile
from io import BytesIO
from PIL import Image
from PyPDF2 import PdfMerger, PdfReader, PdfWriter
from pdf2image import convert_from_path
import pytesseract
import img2pdf
import tempfile
import time
import unicodedata
import logging
from typing import List, Optional, Tuple

# Configuração de cache para melhor performance
st.set_page_config(page_title="Conversor de Documentos", page_icon="📄", layout="wide")

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
            logger.error(f"Erro ao salvar arquivo: {str(e)}")
    
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
                logger.warning(f"Falha ao excluir {file_path}: {str(e)}")
    except Exception as e:
        st.error(f"Erro ao limpar diretório: {str(e)}")
        logger.error(f"Erro ao limpar diretório: {str(e)}")

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
        logger.error(f"Erro ao criar link de download: {str(e)}")

# ============================================
# 🖥️ Conversão via LibreOffice
# ============================================
def converter_via_libreoffice(input_path: str, output_format: str) -> Optional[str]:
    """
    Converte documentos usando LibreOffice de forma segura
    Formatos suportados: pdf, docx, odt, html, txt
    """
    try:
        # Verifica se o arquivo de entrada existe
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Arquivo de entrada não encontrado: {input_path}")
        
        # Determina a extensão de saída
        format_ext = {
            'pdf': '.pdf',
            'docx': '.docx',
            'odt': '.odt',
            'html': '.html',
            'txt': '.txt'
        }.get(output_format.lower(), '.pdf')
        
        # Cria caminho de saída
        base_name = os.path.splitext(os.path.basename(input_path))[0]
        output_path = os.path.join(WORK_DIR, f"{base_name}{format_ext}")
        
        # Comando de conversão
        command = [
            'libreoffice',
            '--headless',
            '--convert-to',
            output_format,
            '--outdir',
            WORK_DIR,
            input_path
        ]
        
        # Executa o comando de forma segura
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=60  # Timeout de 60 segundos
        )
        
        if result.returncode != 0:
            raise RuntimeError(f"LibreOffice retornou erro: {result.stderr}")
        
        if not os.path.exists(output_path):
            raise FileNotFoundError(f"Arquivo de saída não gerado: {output_path}")
        
        return output_path
        
    except Exception as e:
        logger.error(f"Erro na conversão com LibreOffice: {str(e)}")
        st.error(f"Erro na conversão: {str(e)}")
        return None

# ============================================
# 📄 Funções de Conversão
# ============================================
def word_para_pdf():
    st.header("Word para PDF (.docx)")
    arquivos = st.file_uploader(
        "Carregue arquivos Word", 
        type=["docx", "doc", "odt", "rtf"],
        accept_multiple_files=True
    )

    if arquivos and st.button("Converter para PDF"):
        with st.spinner("Convertendo documentos..."):
            for arquivo in arquivos:
                try:
                    # Salva o arquivo temporariamente
                    input_path = os.path.join(WORK_DIR, sanitize_filename(arquivo.name))
                    with open(input_path, "wb") as f:
                        f.write(arquivo.getbuffer())
                    
                    # Converte usando LibreOffice
                    output_path = converter_via_libreoffice(input_path, "pdf")
                    
                    if output_path:
                        nome_pdf = os.path.basename(output_path)
                        criar_link_download(nome_pdf, f"📥 Baixar {nome_pdf}", "application/pdf")
                        st.success(f"Convertido: {arquivo.name} → {nome_pdf}")
                    else:
                        st.error(f"Falha na conversão: {arquivo.name}")
                        
                except Exception as e:
                    st.error(f"Erro ao processar {arquivo.name}: {str(e)}")
                    logger.error(f"Erro no processamento: {str(e)}")

def pdf_para_word():
    st.header("PDF para Word")
    uploaded_file = st.file_uploader(
        "Carregue um arquivo PDF", 
        type=["pdf"],
        accept_multiple_files=False
    )

    if uploaded_file and st.button("Converter para Word"):
        try:
            with st.spinner("Convertendo PDF para Word..."):
                # Salva o PDF temporariamente
                input_path = os.path.join(WORK_DIR, sanitize_filename(uploaded_file.name))
                with open(input_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                # Converte para Word usando LibreOffice
                output_path = converter_via_libreoffice(input_path, "docx")
                
                if output_path:
                    nome_docx = os.path.basename(output_path)
                    criar_link_download(
                        nome_docx, 
                        f"📥 Baixar {nome_docx}",
                        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    )
                    st.success("Conversão concluída!")
                else:
                    st.error("Falha na conversão")
                    
        except Exception as e:
            st.error(f"Erro na conversão: {str(e)}")
            logger.error(f"Erro na conversão PDF para Word: {str(e)}")

# ============================================
# 🏠 Interface Principal
# ============================================
def main():
    st.title("📄 Conversor de Documentos (LibreOffice)")
    st.markdown("""
    Ferramenta para conversão entre diversos formatos de documentos usando LibreOffice.
    """)

    # Menu lateral
    st.sidebar.title("Menu")
    opcao = st.sidebar.selectbox(
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
        ]
    )

    # Limpar arquivos temporários
    if st.sidebar.button("Limpar arquivos temporários"):
        limpar_diretorio()
        st.sidebar.success("Arquivos temporários removidos!")

    st.sidebar.markdown("---")
    st.sidebar.markdown("""
    **Requisitos:**
    - LibreOffice instalado
    - Tesseract OCR (para funções de OCR)
    - Ghostscript (para PDF/A)
    """)

    # Roteamento das funções
    if opcao == "Word para PDF":
        word_para_pdf()
    elif opcao == "PDF para Word":
        pdf_para_word()
    # ... (outras funções mantidas como no código original)

if __name__ == "__main__":
    # Verifica se o LibreOffice está instalado
    if not shutil.which("libreoffice"):
        st.error("LibreOffice não está instalado no sistema. Esta aplicação requer LibreOffice para funcionar.")
        st.stop()
    
    main()

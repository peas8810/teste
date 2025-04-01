import os
import shutil
import re
import zipfile
import tempfile
import subprocess
import streamlit as st
from PIL import Image
from PyPDF2 import PdfMerger, PdfReader, PdfWriter
from pdf2docx import Converter
from pdf2image import convert_from_path
import pytesseract
import img2pdf
from docx import Document
from io import BytesIO
from reportlab.pdfgen import canvas
from concurrent.futures import ThreadPoolExecutor

# Configurações iniciais
st.set_page_config(page_title="Conversor de Documentos", page_icon="📄", layout="wide")

# Verificar e instalar poppler-utils se necessário
def install_poppler():
    try:
        # Tenta encontrar o caminho do poppler
        poppler_path = shutil.which("pdftoppm") or shutil.which("pdfimages")
        if not poppler_path:
            # Instalação no ambiente do Streamlit Sharing (Linux)
            if not os.path.exists("/usr/bin/pdftoppm"):
                st.warning("Instalando poppler-utils...")
                subprocess.run(["apt-get", "update"], check=True)
                subprocess.run(["apt-get", "install", "-y", "poppler-utils"], check=True)
            return "/usr/bin"
        return os.path.dirname(poppler_path)
    except Exception as e:
        st.error(f"Erro ao configurar poppler: {str(e)}")
        return None

POPPLER_PATH = install_poppler()

# Configuração do diretório temporário
WORK_DIR = tempfile.mkdtemp(prefix="doc_converter_")
os.makedirs(WORK_DIR, exist_ok=True)

# Configuração do Tesseract OCR
pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'

# ============================================
# 🛠️ Funções Utilitárias
# ============================================
def sanitize_filename(filename):
    """Remove caracteres especiais do nome do arquivo"""
    return re.sub(r'[^a-zA-Z0-9_.-]', '_', filename)

def salvar_arquivos(uploaded_files):
    """Salva arquivos carregados no diretório de trabalho"""
    caminhos = []
    for uploaded_file in uploaded_files:
        nome_sanitizado = sanitize_filename(uploaded_file.name)
        caminho = os.path.join(WORK_DIR, nome_sanitizado)
        with open(caminho, "wb") as f:
            f.write(uploaded_file.getbuffer())
        caminhos.append(caminho)
    return caminhos

def criar_link_download(nome_arquivo, label, mime_type="application/octet-stream"):
    """Cria um botão de download para o arquivo processado"""
    file_path = os.path.join(WORK_DIR, nome_arquivo)
    with open(file_path, "rb") as f:
        st.download_button(
            label=label,
            data=f,
            file_name=nome_arquivo,
            mime=mime_type
        )

# ============================================
# 📄 Funções de Conversão Word para Imagens/PDF
# ============================================
def word_to_pdf_temp(word_path):
    """Cria um PDF temporário a partir de Word usando reportlab"""
    try:
        doc = Document(word_path)
        pdf_buffer = BytesIO()
        c = canvas.Canvas(pdf_buffer)
        
        # Configuração básica de página
        c.setPageSize((595.27, 841.89))  # A4 em pontos (72 dpi)
        
        y_position = 800  # Posição inicial do texto
        for para in doc.paragraphs:
            text = para.text
            if y_position < 100:  # Nova página se chegar ao final
                c.showPage()
                y_position = 800
                c.setPageSize((595.27, 841.89))
            
            text_object = c.beginText(40, y_position)
            text_object.textLine(text)
            c.drawText(text_object)
            y_position -= 15  # Espaçamento entre parágrafos
        
        c.save()
        return pdf_buffer.getvalue()
    except Exception as e:
        st.error(f"Erro ao criar PDF temporário: {str(e)}")
        return None

def word_to_images(word_path, output_folder, dpi=300):
    """Converte Word para imagens JPG via PDF temporário"""
    try:
        # 1. Criar PDF temporário
        pdf_content = word_to_pdf_temp(word_path)
        if not pdf_content:
            return []
            
        temp_pdf = os.path.join(output_folder, "temp.pdf")
        with open(temp_pdf, "wb") as f:
            f.write(pdf_content)
        
        # 2. Converter PDF para imagens
        images = convert_from_path(
            temp_pdf,
            dpi=dpi,
            output_folder=output_folder,
            fmt='jpeg',
            thread_count=4,
            poppler_path=POPPLER_PATH
        )
        
        # 3. Salvar imagens
        output_paths = []
        for i, image in enumerate(images):
            img_path = os.path.join(output_folder, f"pagina_{i+1}.jpg")
            image.save(img_path, "JPEG", quality=95)
            output_paths.append(img_path)
        
        return output_paths
    
    except Exception as e:
        st.error(f"Erro na conversão para imagens: {str(e)}")
        return []

def word_to_images_to_pdf(word_path, output_pdf):
    """Converte Word para PDF via imagens"""
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            # 1. Converter Word para imagens
            image_paths = word_to_images(word_path, temp_dir)
            
            if not image_paths:
                return False
                
            # 2. Converter imagens para PDF
            with open(output_pdf, "wb") as f:
                f.write(img2pdf.convert(
                    [img for img in image_paths if os.path.exists(img)]
                ))
            
            return True
            
    except Exception as e:
        st.error(f"Erro na conversão final: {str(e)}")
        return False

# ============================================
# 🖼️ Interface para Conversão Word
# ============================================
def word_conversion_interface():
    st.header("Conversor Word para Imagens/PDF")
    st.warning("Atenção: Esta conversão preserva o texto e formatação básica")
    
    uploaded_files = st.file_uploader(
        "Carregue arquivos Word (.docx)",
        type=["docx"],
        accept_multiple_files=True
    )
    
    if not uploaded_files:
        return
    
    if st.button("Converter Documentos"):
        with st.spinner("Processando..."):
            for uploaded_file in uploaded_files:
                try:
                    # Salvar arquivo temporariamente
                    word_path = os.path.join(WORK_DIR, uploaded_file.name)
                    with open(word_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    
                    # Converter para imagens
                    with tempfile.TemporaryDirectory() as temp_dir:
                        image_paths = word_to_images(word_path, temp_dir)
                        
                        if image_paths:
                            # Criar ZIP com imagens
                            nome_base = os.path.splitext(uploaded_file.name)[0]
                            zip_name = f"{nome_base}_imagens.zip"
                            zip_path = os.path.join(WORK_DIR, zip_name)
                            
                            with zipfile.ZipFile(zip_path, 'w') as zipf:
                                for img_path in image_paths:
                                    zipf.write(img_path, os.path.basename(img_path))
                            
                            st.success(f"Documento convertido: {uploaded_file.name}")
                            
                            # Botão para baixar imagens
                            criar_link_download(zip_name, "📥 Baixar imagens (ZIP)", "application/zip")
                            
                            # Converter para PDF
                            pdf_name = f"{nome_base}.pdf"
                            pdf_path = os.path.join(WORK_DIR, pdf_name)
                            
                            if word_to_images_to_pdf(word_path, pdf_path):
                                criar_link_download(pdf_name, "📥 Baixar PDF", "application/pdf")
                
                except Exception as e:
                    st.error(f"Erro ao processar {uploaded_file.name}: {str(e)}")

# ============================================
# 🏠 Interface Principal
# ============================================
def main():
    st.title("📄 Conversor de Documentos")
    
    # Verificação de dependências
    if not POPPLER_PATH:
        st.error("""
        O sistema não conseguiu configurar o poppler-utils automaticamente.
        Por favor, adicione esta linha ao seu Dockerfile:
        ```
        RUN apt-get update && apt-get install -y poppler-utils
        ```
        """)
        return
    
    # Menu lateral
    with st.sidebar:
        st.title("Menu")
        opcao = st.selectbox(
            "Selecione a operação",
            ["Word para Imagens/PDF"]
        )
        
        st.markdown("---")
        if st.button("Limpar arquivos temporários"):
            shutil.rmtree(WORK_DIR)
            os.makedirs(WORK_DIR, exist_ok=True)
            st.success("Arquivos temporários removidos!")
    
    # Roteamento
    if opcao == "Word para Imagens/PDF":
        word_conversion_interface()

if __name__ == "__main__":
    main()

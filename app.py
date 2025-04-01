import os
import shutil
import re
import zipfile
import tempfile
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

# Diretório temporário
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
# 📄 Funções de Conversão Word para Imagens e PDF
# ============================================
def word_to_images(word_path, output_folder, dpi=300):
    """
    Converte Word para imagens JPG (uma por página) mantendo todas as características
    
    1. Converte Word para PDF usando python-docx + reportlab (para texto)
    2. Converte o PDF para imagens JPG
    
    Args:
        word_path: Caminho para o arquivo Word
        output_folder: Pasta para salvar as imagens
        dpi: Resolução das imagens (300 por padrão)
    
    Returns:
        Lista de caminhos das imagens geradas
    """
    try:
        # 1. Extrair texto do Word
        doc = Document(word_path)
        text = "\n".join([para.text for para in doc.paragraphs])
        
        # 2. Criar PDF temporário
        pdf_buffer = BytesIO()
        c = canvas.Canvas(pdf_buffer)
        
        # Configurar página A4
        c.setPageSize((595.27, 841.89))  # A4 em pontos (72 dpi)
        
        # Adicionar texto ao PDF
        text_object = c.beginText(40, 800)
        for line in text.split('\n'):
            text_object.textLine(line)
        c.drawText(text_object)
        c.save()
        
        # Salvar PDF temporário
        temp_pdf = os.path.join(output_folder, "temp.pdf")
        with open(temp_pdf, "wb") as f:
            f.write(pdf_buffer.getvalue())
        
        # 3. Converter PDF para imagens
        images = convert_from_path(
            temp_pdf,
            dpi=dpi,
            output_folder=output_folder,
            fmt='jpeg',
            thread_count=4
        )
        
        # Salvar imagens
        output_paths = []
        for i, image in enumerate(images):
            img_path = os.path.join(output_folder, f"pagina_{i+1}.jpg")
            image.save(img_path, "JPEG", quality=95)
            output_paths.append(img_path)
        
        return output_paths
    
    except Exception as e:
        st.error(f"Erro na conversão: {str(e)}")
        return []

def word_to_images_to_pdf(word_path, output_pdf):
    """
    Converte Word para PDF via imagens (preserva layout visual)
    
    1. Converte Word para imagens
    2. Combina imagens em um PDF
    
    Args:
        word_path: Caminho para o arquivo Word
        output_pdf: Caminho para o PDF de saída
    """
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            # 1. Converter Word para imagens
            image_paths = word_to_images(word_path, temp_dir)
            
            if not image_paths:
                return False
                
            # 2. Converter imagens para PDF
            with open(output_pdf, "wb") as f:
                f.write(img2pdf.convert(
                    [Image.open(img).filename for img in image_paths]
                ))
            
            return True
            
    except Exception as e:
        st.error(f"Erro na conversão final: {str(e)}")
        return False

# ============================================
# 🖼️ Interface para Conversão Word para Imagens/PDF
# ============================================
def word_para_imagens_pdf():
    st.header("Word para Imagens/PDF")
    st.info("Converte documentos Word para imagens JPG (uma por página) e depois para PDF")
    
    uploaded_files = st.file_uploader(
        "Carregue arquivos Word (.docx)",
        type=["docx"],
        accept_multiple_files=True
    )
    
    if not uploaded_files:
        return
    
    if st.button("Converter para Imagens e PDF"):
        with st.spinner("Processando arquivos..."):
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
                            
                            st.success(f"Documento {uploaded_file.name} convertido em {len(image_paths)} páginas!")
                            
                            # Botão para baixar imagens
                            criar_link_download(zip_name, "📥 Baixar imagens (ZIP)", "application/zip")
                            
                            # Converter imagens para PDF
                            pdf_name = f"{nome_base}_from_images.pdf"
                            pdf_path = os.path.join(WORK_DIR, pdf_name)
                            
                            if word_to_images_to_pdf(word_path, pdf_path):
                                criar_link_download(pdf_name, "📥 Baixar PDF", "application/pdf")
                
                except Exception as e:
                    st.error(f"Erro ao processar {uploaded_file.name}: {str(e)}")

# ============================================
# 🔄 Funções de Conversão Existentes (simplificadas)
# ============================================
def pdf_para_word():
    st.header("PDF para Word")
    uploaded_file = st.file_uploader("Carregue um PDF", type=["pdf"])
    if uploaded_file and st.button("Converter para Word"):
        try:
            caminho = salvar_arquivos([uploaded_file])[0]
            nome_base = os.path.splitext(uploaded_file.name)[0]
            saida = os.path.join(WORK_DIR, f"{nome_base}.docx")
            
            cv = Converter(caminho)
            cv.convert(saida)
            cv.close()
            
            criar_link_download(f"{nome_base}.docx", "📥 Baixar Word", 
                               "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        except Exception as e:
            st.error(f"Erro: {str(e)}")

def pdf_para_jpg():
    st.header("PDF para JPG")
    uploaded_file = st.file_uploader("Carregue um PDF", type=["pdf"])
    if uploaded_file and st.button("Converter para JPG"):
        try:
            caminho = salvar_arquivos([uploaded_file])[0]
            imagens = convert_from_path(caminho)
            
            nome_base = os.path.splitext(uploaded_file.name)[0]
            zip_name = f"{nome_base}_imagens.zip"
            zip_path = os.path.join(WORK_DIR, zip_name)
            
            with zipfile.ZipFile(zip_path, 'w') as zipf:
                for i, img in enumerate(imagens):
                    img_path = os.path.join(WORK_DIR, f"pagina_{i+1}.jpg")
                    img.save(img_path, "JPEG")
                    zipf.write(img_path, f"pagina_{i+1}.jpg")
            
            criar_link_download(zip_name, "📥 Baixar imagens (ZIP)", "application/zip")
        except Exception as e:
            st.error(f"Erro: {str(e)}")

# ============================================
# 🏠 Interface Principal
# ============================================
def main():
    st.title("📄 Conversor de Documentos Avançado")
    
    # Menu lateral
    with st.sidebar:
        st.title("Menu")
        opcao = st.selectbox(
            "Selecione a operação",
            [
                "Word para Imagens/PDF",
                "PDF para Word",
                "PDF para JPG",
                # Outras opções podem ser adicionadas aqui
            ]
        )
        
        st.markdown("---")
        if st.button("Limpar arquivos temporários"):
            shutil.rmtree(WORK_DIR)
            os.makedirs(WORK_DIR, exist_ok=True)
            st.success("Arquivos temporários removidos!")
    
    # Roteamento
    if opcao == "Word para Imagens/PDF":
        word_para_imagens_pdf()
    elif opcao == "PDF para Word":
        pdf_para_word()
    elif opcao == "PDF para JPG":
        pdf_para_jpg()

if __name__ == "__main__":
    main()

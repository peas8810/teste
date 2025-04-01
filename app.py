import os
import shutil
import re
import zipfile
from io import BytesIO
from PIL import Image
from PyPDF2 import PdfMerger, PdfReader, PdfWriter
from pdf2docx import Converter
from pdf2image import convert_from_path
import pytesseract
import img2pdf
import streamlit as st
from docx import Document
from reportlab.pdfgen import canvas
import tempfile
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
# 📄 Funções de Conversão
# ============================================
def word_para_pdf():
    st.header("Word para PDF")
    st.warning("Conversão básica de texto (sem formatação complexa)")
    
    uploaded_files = st.file_uploader(
        "Carregue arquivos Word (.docx)",
        type=["docx"],
        accept_multiple_files=True
    )
    
    if uploaded_files and st.button("Converter para PDF"):
        for uploaded_file in uploaded_files:
            try:
                # Extrai texto do DOCX
                doc = Document(BytesIO(uploaded_file.getvalue()))
                text = "\n".join([para.text for para in doc.paragraphs])
                
                # Cria PDF com ReportLab
                buffer = BytesIO()
                c = canvas.Canvas(buffer)
                text_object = c.beginText(40, 800)
                
                for line in text.split('\n'):
                    text_object.textLine(line)
                
                c.drawText(text_object)
                c.save()
                
                # Salva o PDF
                nome_base = os.path.splitext(uploaded_file.name)[0]
                nome_saida = f"word_{nome_base}.pdf"
                caminho_pdf = os.path.join(WORK_DIR, nome_saida)
                
                with open(caminho_pdf, "wb") as f:
                    f.write(buffer.getvalue())
                
                st.success(f"Arquivo convertido: {nome_saida}")
                criar_link_download(nome_saida, f"Baixar {nome_saida}", "application/pdf")
                
            except Exception as e:
                st.error(f"Erro ao converter {uploaded_file.name}: {str(e)}")

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
                caminho = salvar_arquivos([uploaded_file])[0]
                nome_base = os.path.splitext(os.path.basename(caminho))[0]
                saida = os.path.join(WORK_DIR, f"{nome_base}.docx")
                
                # Usa ThreadPool para melhor performance
                with ThreadPoolExecutor() as executor:
                    future = executor.submit(Converter(caminho).convert, saida)
                    future.result()
                
                st.success("Conversão concluída!")
                criar_link_download(
                    f"{nome_base}.docx", 
                    f"Baixar {nome_base}.docx",
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )
        except Exception as e:
            st.error(f"Erro na conversão: {str(e)}")

def pdf_para_jpg():
    st.header("PDF para JPG")
    uploaded_file = st.file_uploader(
        "Carregue um arquivo PDF",
        type=["pdf"],
        accept_multiple_files=False
    )
    
    if uploaded_file and st.button("Converter para JPG"):
        try:
            caminho = salvar_arquivos([uploaded_file])[0]
            nome_base = os.path.splitext(os.path.basename(caminho))[0]
            
            imagens = convert_from_path(caminho)
            
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
            criar_link_download(zip_nome, "Baixar todas as imagens (ZIP)", "application/zip")
                
        except Exception as e:
            st.error(f"Erro ao converter PDF para imagens: {str(e)}")

def juntar_pdf():
    st.header("Juntar PDFs")
    uploaded_files = st.file_uploader(
        "Carregue os PDFs para juntar",
        type=["pdf"],
        accept_multiple_files=True
    )
    
    if uploaded_files and len(uploaded_files) >= 2 and st.button("Juntar PDFs"):
        try:
            caminhos = salvar_arquivos(uploaded_files)
            nome_saida = "merged_resultado.pdf"
            saida = os.path.join(WORK_DIR, nome_saida)
            
            merger = PdfMerger()
            for c in caminhos:
                merger.append(c)
            merger.write(saida)
            merger.close()
            
            st.success("PDFs unidos com sucesso!")
            criar_link_download(nome_saida, f"Baixar {nome_saida}", "application/pdf")
                
        except Exception as e:
            st.error(f"Erro ao unir PDFs: {str(e)}")

def dividir_pdf():
    st.header("Dividir PDF")
    uploaded_file = st.file_uploader(
        "Carregue um PDF para dividir",
        type=["pdf"],
        accept_multiple_files=False
    )
    
    if uploaded_file and st.button("Dividir PDF"):
        try:
            caminho = salvar_arquivos([uploaded_file])[0]
            nome_base = os.path.splitext(os.path.basename(caminho))[0]
            
            reader = PdfReader(caminho)
            
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
            
            st.success(f"PDF dividido em {len(reader.pages)} páginas!")
            criar_link_download(zip_nome, "Baixar todas as páginas (ZIP)", "application/zip")
                
        except Exception as e:
            st.error(f"Erro ao dividir PDF: {str(e)}")

def ocr_pdf():
    st.header("OCR em PDF")
    uploaded_file = st.file_uploader(
        "Carregue um PDF para extrair texto",
        type=["pdf"],
        accept_multiple_files=False
    )
    
    if uploaded_file and st.button("Extrair Texto (OCR)"):
        try:
            caminho = salvar_arquivos([uploaded_file])[0]
            nome_base = os.path.splitext(os.path.basename(caminho))[0]
            nome_saida = f"ocr_{nome_base}.txt"
            txt_path = os.path.join(WORK_DIR, nome_saida)
            
            imagens = convert_from_path(caminho)
            texto = ""
            
            progress_bar = st.progress(0)
            for i, img in enumerate(imagens):
                progress_bar.progress((i + 1) / len(imagens))
                texto += f"\n\n--- Página {i+1} ---\n\n"
                texto += pytesseract.image_to_string(img, lang='por')
            
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(texto)
            
            progress_bar.empty()
            st.success("Texto extraído com sucesso!")
            criar_link_download(nome_saida, "Baixar texto extraído", "text/plain")
                
        except Exception as e:
            st.error(f"Erro no OCR: {str(e)}")

def ocr_imagem():
    st.header("OCR em Imagens")
    uploaded_files = st.file_uploader(
        "Carregue imagens para extrair texto",
        type=["jpg", "jpeg", "png"],
        accept_multiple_files=True
    )
    
    if uploaded_files and st.button("Extrair Texto (OCR)"):
        try:
            caminhos = salvar_arquivos(uploaded_files)
            nome_saida = "ocr_images.txt"
            txt_path = os.path.join(WORK_DIR, nome_saida)
            
            texto = ""
            progress_bar = st.progress(0)
            
            for i, caminho in enumerate(caminhos):
                progress_bar.progress((i + 1) / len(caminhos))
                img = Image.open(caminho)
                texto += f"\n\n--- Imagem {i+1}: {os.path.basename(caminho)} ---\n\n"
                texto += pytesseract.image_to_string(img, lang='por')
            
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(texto)
            
            progress_bar.empty()
            st.success("Texto extraído com sucesso!")
            criar_link_download(nome_saida, "Baixar texto extraído", "text/plain")
                
        except Exception as e:
            st.error(f"Erro no OCR: {str(e)}")

def jpg_para_pdf():
    st.header("Imagens para PDF")
    uploaded_files = st.file_uploader(
        "Carregue imagens para converter em PDF",
        type=["jpg", "jpeg", "png"],
        accept_multiple_files=True
    )
    
    if uploaded_files and st.button("Converter para PDF"):
        try:
            caminhos = salvar_arquivos(uploaded_files)
            nome_saida = "images_combined.pdf"
            caminho_pdf = os.path.join(WORK_DIR, nome_saida)
            
            with open(caminho_pdf, "wb") as f:
                f.write(img2pdf.convert([Image.open(img).filename for img in caminhos]))
            
            st.success("PDF criado com sucesso!")
            criar_link_download(nome_saida, "Baixar PDF", "application/pdf")
                
        except Exception as e:
            st.error(f"Erro ao converter imagens para PDF: {str(e)}")

# ============================================
# 🏠 Interface Principal
# ============================================
def main():
    st.title("📄 Conversor de Documentos")
    
    # Menu lateral
    with st.sidebar:
        st.title("Menu")
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
                "Imagens para PDF"
            ]
        )
        
        st.markdown("---")
        if st.button("Limpar arquivos temporários"):
            shutil.rmtree(WORK_DIR)
            os.makedirs(WORK_DIR, exist_ok=True)
            st.success("Arquivos temporários removidos!")
    
    # Roteamento
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

if __name__ == "__main__":
    main()

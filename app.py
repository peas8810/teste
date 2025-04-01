# ============================================
# 📥 Importações
# ============================================
import streamlit as st
import os
import shutil
import zipfile
from io import BytesIO
from PyPDF2 import PdfMerger, PdfReader, PdfWriter
from pdf2docx import Converter
from PIL import Image
import pytesseract
from pdf2image import convert_from_path
import img2pdf
import mammoth
from xhtml2pdf import pisa

# ============================================
# 📁 Diretório de trabalho
# ============================================
WORK_DIR = "documentos"
os.makedirs(WORK_DIR, exist_ok=True)

# ============================================
# 💾 Funções utilitárias
# ============================================
def salvar_arquivos(uploaded_files):
    caminhos = []
    for uploaded_file in uploaded_files:
        caminho = os.path.join(WORK_DIR, uploaded_file.name)
        with open(caminho, "wb") as f:
            f.write(uploaded_file.getbuffer())
        caminhos.append(caminho)
    return caminhos

def limpar_diretorio():
    for filename in os.listdir(WORK_DIR):
        file_path = os.path.join(WORK_DIR, filename)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
        except Exception as e:
            st.error(f"Erro ao excluir {file_path}: {e}")

def criar_link_download(nome_arquivo, label):
    with open(os.path.join(WORK_DIR, nome_arquivo), "rb") as f:
        st.download_button(
            label=label,
            data=f,
            file_name=nome_arquivo,
            mime="application/octet-stream"
        )

# ============================================
# 📝 Word para PDF com mammoth + xhtml2pdf (compatível com Streamlit Cloud)
# ============================================
def word_para_pdf():
    st.header("Word para PDF (.docx → PDF)")
    uploaded_files = st.file_uploader("Carregue arquivos Word (.docx)", type=["docx"], accept_multiple_files=True)

    if uploaded_files and st.button("Converter para PDF"):
        caminhos = salvar_arquivos(uploaded_files)
        for caminho in caminhos:
            nome_base = os.path.splitext(os.path.basename(caminho))[0]
            html_path = os.path.join(WORK_DIR, f"{nome_base}.html")
            pdf_path = os.path.join(WORK_DIR, f"{nome_base}.pdf")

            try:
                # 1. Converte para HTML
                with open(caminho, "rb") as docx_file:
                    result = mammoth.convert_to_html(docx_file)
                    html = result.value
                with open(html_path, "w", encoding="utf-8") as f:
                    f.write(html)

                # 2. Gera PDF com xhtml2pdf
                with open(html_path, "r", encoding="utf-8") as f:
                    source_html = f.read()
                with open(pdf_path, "wb") as output_file:
                    pisa_status = pisa.CreatePDF(src=source_html, dest=output_file)

                if pisa_status.err:
                    st.error(f"Erro ao converter {nome_base}.docx para PDF.")
                else:
                    st.success(f"PDF gerado: {nome_base}.pdf")
                    criar_link_download(f"{nome_base}.pdf", f"📥 Baixar {nome_base}.pdf")

            except Exception as e:
                st.error(f"Erro ao processar {caminho}: {e}")

# ============================================
# 📤 Outras funcionalidades (sem alterações)
# ============================================
def pdf_para_word():
    st.header("PDF para Word")
    uploaded_file = st.file_uploader("Carregue um arquivo PDF", type=["pdf"])

    if uploaded_file and st.button("Converter para Word"):
        caminho = salvar_arquivos([uploaded_file])[0]
        nome_base = os.path.splitext(os.path.basename(caminho))[0]
        saida = os.path.join(WORK_DIR, f"{nome_base}.docx")

        try:
            cv = Converter(caminho)
            cv.convert(saida)
            cv.close()
            st.success("Conversão concluída!")
            criar_link_download(f"{nome_base}.docx", f"📥 Baixar {nome_base}.docx")
        except Exception as e:
            st.error(f"Erro: {e}")

def pdf_para_jpg():
    st.header("PDF para JPG")
    uploaded_file = st.file_uploader("Carregue um PDF", type=["pdf"])
    if uploaded_file and st.button("Converter para JPG"):
        caminho = salvar_arquivos([uploaded_file])[0]
        imagens = convert_from_path(caminho)
        for i, img in enumerate(imagens):
            nome = f"pagina_{i+1}.jpg"
            caminho_img = os.path.join(WORK_DIR, nome)
            img.save(caminho_img, "JPEG")
            st.success(f"Página {i+1} gerada!")
            criar_link_download(nome, f"📥 Baixar {nome}")

def juntar_pdf():
    st.header("Juntar PDFs")
    arquivos = st.file_uploader("Selecione múltiplos PDFs", type=["pdf"], accept_multiple_files=True)
    if arquivos and st.button("Juntar PDFs"):
        caminhos = salvar_arquivos(arquivos)
        saida = os.path.join(WORK_DIR, "unidos.pdf")
        merger = PdfMerger()
        for c in caminhos:
            merger.append(c)
        merger.write(saida)
        merger.close()
        st.success("PDF gerado com sucesso!")
        criar_link_download("unidos.pdf", "📥 Baixar unidos.pdf")

def dividir_pdf():
    st.header("Dividir PDF")
    arquivo = st.file_uploader("Selecione um PDF", type=["pdf"])
    if arquivo and st.button("Dividir"):
        caminho = salvar_arquivos([arquivo])[0]
        reader = PdfReader(caminho)
        for i, page in enumerate(reader.pages):
            writer = PdfWriter()
            writer.add_page(page)
            nome = f"pagina_{i+1}.pdf"
            out = os.path.join(WORK_DIR, nome)
            with open(out, "wb") as f:
                writer.write(f)
            st.success(f"Página {i+1} salva!")
            criar_link_download(nome, f"📥 Baixar {nome}")

def ocr_pdf():
    st.header("OCR em PDF")
    arquivo = st.file_uploader("PDF para OCR", type=["pdf"])
    if arquivo and st.button("Executar OCR"):
        caminho = salvar_arquivos([arquivo])[0]
        imagens = convert_from_path(caminho)
        texto = ""
        for i, img in enumerate(imagens):
            texto += f"\n\n--- Página {i+1} ---\n\n"
            texto += pytesseract.image_to_string(img, lang="por")
        saida = os.path.join(WORK_DIR, "ocr_pdf.txt")
        with open(saida, "w", encoding="utf-8") as f:
            f.write(texto)
        st.success("Texto extraído!")
        criar_link_download("ocr_pdf.txt", "📥 Baixar OCR")

def ocr_imagem():
    st.header("OCR em Imagens")
    imagens = st.file_uploader("Imagens", type=["jpg", "jpeg", "png"], accept_multiple_files=True)
    if imagens and st.button("Executar OCR"):
        caminhos = salvar_arquivos(imagens)
        texto = ""
        for i, caminho in enumerate(caminhos):
            img = Image.open(caminho)
            texto += f"\n\n--- Imagem {i+1} ---\n\n"
            texto += pytesseract.image_to_string(img, lang="por")
        saida = os.path.join(WORK_DIR, "ocr_img.txt")
        with open(saida, "w", encoding="utf-8") as f:
            f.write(texto)
        st.success("Texto extraído!")
        criar_link_download("ocr_img.txt", "📥 Baixar OCR")

def jpg_para_pdf():
    st.header("Imagens para PDF")
    imagens = st.file_uploader("Carregue imagens", type=["jpg", "jpeg", "png"], accept_multiple_files=True)
    if imagens and st.button("Converter"):
        caminhos = salvar_arquivos(imagens)
        nome_pdf = "img2pdf_resultado.pdf"
        pdf_path = os.path.join(WORK_DIR, nome_pdf)
        with open(pdf_path, "wb") as f:
            f.write(img2pdf.convert(caminhos))
        st.success("PDF criado!")
        criar_link_download(nome_pdf, f"📥 Baixar {nome_pdf}")

# ============================================
# 🚀 Interface principal
# ============================================
def main():
    st.title("📄 Conversor de Documentos")
    st.sidebar.title("Menu")
    opcoes = [
        "Word para PDF",
        "PDF para Word",
        "PDF para JPG",
        "Juntar PDFs",
        "Dividir PDF",
        "OCR em PDF",
        "OCR em Imagens",
        "Imagens para PDF"
    ]
    escolha = st.sidebar.selectbox("Escolha a operação:", opcoes)

    if escolha == "Word para PDF":
        word_para_pdf()
    elif escolha == "PDF para Word":
        pdf_para_word()
    elif escolha == "PDF para JPG":
        pdf_para_jpg()
    elif escolha == "Juntar PDFs":
        juntar_pdf()
    elif escolha == "Dividir PDF":
        dividir_pdf()
    elif escolha == "OCR em PDF":
        ocr_pdf()
    elif escolha == "OCR em Imagens":
        ocr_imagem()
    elif escolha == "Imagens para PDF":
        jpg_para_pdf()

    if st.sidebar.button("🧹 Limpar arquivos temporários"):
        limpar_diretorio()
        st.sidebar.success("Arquivos temporários limpos!")

if __name__ == "__main__":
    main()

import os
import shutil
import time
import zipfile
import subprocess
import uuid
import streamlit as st
from PyPDF2 import PdfMerger, PdfReader, PdfWriter
from pdf2docx import Converter
from PIL import Image
import pytesseract
from pdf2image import convert_from_path
import img2pdf

# Configurações iniciais
WORK_DIR = "documentos"
os.makedirs(WORK_DIR, exist_ok=True)

# Verifica e configura o Tesseract OCR (pode precisar de ajuste no seu sistema)
pytesseract.pytesseract.tesseract_cmd = r'/usr/bin/tesseract'

# Função para salvar arquivos enviados
def salvar_arquivos(uploaded_files):
    caminhos = []
    for uploaded_file in uploaded_files:
        # Limpa o nome do arquivo
        nome_base, extensao = os.path.splitext(uploaded_file.name)
        nome_limpo = (nome_base.replace(" ", "_")
                      .replace("ç", "c").replace("ã", "a")
                      .replace("á", "a").replace("é", "e")
                      .replace("í", "i").replace("ó", "o")
                      .replace("ú", "u").replace("ñ", "n")) + extensao.lower()
        
        caminho = os.path.join(WORK_DIR, nome_limpo)
        with open(caminho, "wb") as f:
            f.write(uploaded_file.getbuffer())
        caminhos.append(caminho)
    return caminhos

# Função para limpar arquivos temporários
def limpar_diretorio():
    for filename in os.listdir(WORK_DIR):
        file_path = os.path.join(WORK_DIR, filename)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
        except Exception as e:
            st.error(f"Erro ao limpar arquivo {file_path}: {e}")

# Função para baixar arquivos
def criar_link_download(nome_arquivo, label):
    with open(os.path.join(WORK_DIR, nome_arquivo), "rb") as f:
        st.download_button(
            label=label,
            data=f,
            file_name=nome_arquivo,
            mime="application/octet-stream"
        )

# Funções de conversão
# Função Word para PDF usando unoserver
def word_para_pdf():
    st.header("Word para PDF")
    uploaded_files = st.file_uploader(
        "Carregue arquivos Word (.doc, .docx, .odt)",
        type=["doc", "docx", "odt"],
        accept_multiple_files=True
    )
    
    if uploaded_files and st.button("Converter para PDF"):
        try:
            from unoserver import UnoConverter
        except ImportError:
            st.error("Biblioteca unoserver não encontrada. Instale com: pip install unoserver")
            return
            
        caminhos = salvar_arquivos(uploaded_files)
        conv = None
        
        try:
            conv = UnoConverter()
            for caminho in caminhos:
                nome_base = os.path.splitext(os.path.basename(caminho))[0]
                nome_saida = f"word_{nome_base}.pdf"
                saida = os.path.join(WORK_DIR, nome_saida)
                
                if os.path.exists(saida):
                    os.remove(saida)
                
                conv.convert(inpath=caminho, outpath=saida, convert_to="pdf")
                
                if os.path.exists(saida):
                    st.success(f"Arquivo convertido: {nome_saida}")
                    criar_link_download(nome_saida, f"Baixar {nome_saida}")
                else:
                    st.error(f"Falha ao converter: {caminho}")
        except Exception as e:
            st.error(f"Erro na conversão: {str(e)}")
        finally:
            if conv:
                try:
                    conv.__del__()
                except:
                    pass

def pdf_para_word():
    st.header("PDF para Word")
    uploaded_file = st.file_uploader(
        "Carregue um arquivo PDF",
        type=["pdf"],
        accept_multiple_files=False
    )
    
    if uploaded_file and st.button("Converter para Word"):
        caminho = salvar_arquivos([uploaded_file])[0]
        nome_base = os.path.splitext(os.path.basename(caminho))[0]
        nome_saida = f"pdf2docx_{nome_base}.docx"
        saida = os.path.join(WORK_DIR, nome_saida)
        
        # Remove arquivo existente se houver
        if os.path.exists(saida):
            os.remove(saida)
        
        try:
            cv = Converter(caminho)
            cv.convert(saida)
            cv.close()
            
            if os.path.exists(saida):
                st.success(f"Arquivo convertido: {nome_saida}")
                criar_link_download(nome_saida, f"Baixar {nome_saida}")
            else:
                st.error(f"Falha na conversão: {caminho}")
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
        caminho = salvar_arquivos([uploaded_file])[0]
        nome_base = os.path.splitext(os.path.basename(caminho))[0]
        
        try:
            imagens = convert_from_path(caminho)
            for i, img in enumerate(imagens):
                nome_saida = f"pdf2jpg_{nome_base}_pag{i+1}.jpg"
                caminho_img = os.path.join(WORK_DIR, nome_saida)
                img.save(caminho_img, "JPEG")
                st.success(f"Imagem gerada: {nome_saida}")
                criar_link_download(nome_saida, f"Baixar {nome_saida}")
        except Exception as e:
            st.error(f"Erro ao converter PDF para imagens: {str(e)}")

def juntar_pdf():
    st.header("Juntar PDFs")
    uploaded_files = st.file_uploader(
        "Carregue os PDFs para juntar",
        type=["pdf"],
        accept_multiple_files=True
    )
    
    if len(uploaded_files) >= 2 and st.button("Juntar PDFs"):
        caminhos = salvar_arquivos(uploaded_files)
        nome_saida = "merge_resultado.pdf"
        saida = os.path.join(WORK_DIR, nome_saida)
        
        # Remove arquivo existente se houver
        if os.path.exists(saida):
            os.remove(saida)
        
        try:
            merger = PdfMerger()
            for c in caminhos:
                merger.append(c)
            merger.write(saida)
            merger.close()
            
            if os.path.exists(saida):
                st.success("PDFs unidos com sucesso!")
                criar_link_download(nome_saida, f"Baixar {nome_saida}")
            else:
                st.error("Falha ao unir PDFs.")
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
        caminho = salvar_arquivos([uploaded_file])[0]
        nome_base = os.path.splitext(os.path.basename(caminho))[0]
        
        try:
            reader = PdfReader(caminho)
            for i, page in enumerate(reader.pages):
                writer = PdfWriter()
                writer.add_page(page)
                nome_saida = f"split_{nome_base}_pag{i+1}.pdf"
                out_path = os.path.join(WORK_DIR, nome_saida)
                with open(out_path, "wb") as f:
                    writer.write(f)
                st.success(f"Página gerada: {nome_saida}")
                criar_link_download(nome_saida, f"Baixar {nome_saida}")
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
        caminho = salvar_arquivos([uploaded_file])[0]
        nome_base = os.path.splitext(os.path.basename(caminho))[0]
        nome_saida = f"ocrpdf_{nome_base}.txt"
        txt_path = os.path.join(WORK_DIR, nome_saida)
        
        # Remove arquivo existente se houver
        if os.path.exists(txt_path):
            os.remove(txt_path)
        
        try:
            imagens = convert_from_path(caminho)
            texto = ""
            for i, img in enumerate(imagens):
                texto += f"\n\n--- Página {i+1} ---\n\n"
                texto += pytesseract.image_to_string(img, lang='por')
            
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(texto)
            
            if os.path.exists(txt_path):
                st.success("Texto extraído com sucesso!")
                criar_link_download(nome_saida, f"Baixar {nome_saida}")
            else:
                st.error("Falha ao extrair texto.")
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
        caminhos = salvar_arquivos(uploaded_files)
        nome_saida = "ocrimg_resultado.txt"
        txt_path = os.path.join(WORK_DIR, nome_saida)
        
        # Remove arquivo existente se houver
        if os.path.exists(txt_path):
            os.remove(txt_path)
        
        texto = ""
        for i, caminho in enumerate(caminhos):
            try:
                img = Image.open(caminho)
                texto += f"\n\n--- Imagem {i+1} ---\n\n"
                texto += pytesseract.image_to_string(img, lang='por')
            except Exception as e:
                st.error(f"Erro ao processar imagem {i+1}: {str(e)}")
        
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(texto)
        
        if os.path.exists(txt_path):
            st.success("Texto extraído com sucesso!")
            criar_link_download(nome_saida, f"Baixar {nome_saida}")
        else:
            st.error("Falha ao extrair texto das imagens.")

def jpg_para_pdf():
    st.header("Imagens para PDF")
    uploaded_files = st.file_uploader(
        "Carregue imagens para converter em PDF",
        type=["jpg", "jpeg", "png"],
        accept_multiple_files=True
    )
    
    if uploaded_files and st.button("Converter para PDF"):
        caminhos = salvar_arquivos(uploaded_files)
        nome_saida = "img2pdf_resultado.pdf"
        caminho_pdf = os.path.join(WORK_DIR, nome_saida)
        
        # Remove arquivo existente se houver
        if os.path.exists(caminho_pdf):
            os.remove(caminho_pdf)
        
        try:
            # Usando img2pdf para melhor qualidade
            with open(caminho_pdf, "wb") as f:
                f.write(img2pdf.convert([Image.open(img).filename for img in caminhos]))
            
            if os.path.exists(caminho_pdf):
                st.success("PDF gerado com sucesso!")
                criar_link_download(nome_saida, f"Baixar {nome_saida}")
            else:
                st.error("Falha ao gerar PDF.")
        except Exception as e:
            st.error(f"Erro ao converter imagens para PDF: {str(e)}")

def pdf_para_pdfa():
    st.header("PDF para PDF/A")
    uploaded_file = st.file_uploader(
        "Carregue um PDF para converter para PDF/A",
        type=["pdf"],
        accept_multiple_files=False
    )
    
    if uploaded_file and st.button("Converter para PDF/A"):
        caminho = salvar_arquivos([uploaded_file])[0]
        nome_base = os.path.splitext(os.path.basename(caminho))[0]
        nome_saida = f"pdfa_{nome_base}.pdf"
        saida = os.path.join(WORK_DIR, nome_saida)
        
        # Remove arquivo existente se houver
        if os.path.exists(saida):
            os.remove(saida)
        
        try:
            gs_path = shutil.which("gs") or "/usr/bin/gs"
            comando = [
                gs_path,
                "-dPDFA=2",
                "-dBATCH",
                "-dNOPAUSE",
                "-dNOOUTERSAVE",
                "-sProcessColorModel=DeviceRGB",
                "-sDEVICE=pdfwrite",
                "-sPDFACompatibilityPolicy=1",
                f"-sOutputFile={saida}",
                caminho
            ]
            
            resultado = subprocess.run(comando, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if os.path.exists(saida) and resultado.returncode == 0:
                st.success("PDF/A gerado com sucesso!")
                criar_link_download(nome_saida, f"Baixar {nome_saida}")
            else:
                st.error("Falha na conversão para PDF/A.")
                if resultado.stderr:
                    st.text(resultado.stderr.decode())
        except Exception as e:
            st.error(f"Erro ao executar Ghostscript: {str(e)}")

# Interface principal
def main():
    st.title("📄 Conversor de Documentos")
    st.markdown("""
    Ferramenta para conversão entre diversos formatos de documentos.
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
    
    # Rodapé
    st.sidebar.markdown("---")
    st.sidebar.markdown("Desenvolvido com Streamlit")
    
    # Executa a função selecionada
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

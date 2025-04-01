import streamlit as st
from docx import Document
from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import io
import os
import tempfile

# Configuração da página
st.set_page_config(page_title="Conversor Word para PDF via Imagens", layout="wide")

# Título do aplicativo
st.title("📄 Conversor Word para PDF via Imagens")

# Sidebar com informações
with st.sidebar:
    st.header("Sobre")
    st.write("""
    Este aplicativo converte documentos Word (.docx) em PDF, 
    passando por uma etapa intermediária de conversão para imagens.
    """)
    st.write("**Como usar:**")
    st.write("1. Faça upload do arquivo Word")
    st.write("2. Ajuste as configurações se necessário")
    st.write("3. Clique em 'Converter'")
    st.write("4. Baixe o PDF resultante")

# Função para renderizar texto como imagem
def text_to_image(text, font_size=20, page_width=800):
    # Usando uma fonte padrão (pode substituir por uma fonte específica se necessário)
    try:
        font = ImageFont.truetype("arial.ttf", font_size)
    except:
        font = ImageFont.load_default()
    
    # Calcula o tamanho necessário para a imagem
    lines = text.split('\n')
    line_heights = [font.getsize(line)[1] for line in lines]
    total_height = sum(line_heights) + 20  # Margem
    
    # Cria uma imagem em branco
    img = Image.new('RGB', (page_width, total_height), color=(255, 255, 255))
    d = ImageDraw.Draw(img)
    
    # Escreve o texto na imagem
    y = 10
    for line in lines:
        d.text((10, y), line, fill=(0, 0, 0), font=font)
        y += font.getsize(line)[1]
    
    return img

# Função principal de conversão
def convert_docx_to_pdf(docx_file, output_pdf):
    # Lê o documento Word
    doc = Document(docx_file)
    
    # Cria um PDF temporário
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_pdf:
        c = canvas.Canvas(tmp_pdf.name, pagesize=letter)
        width, height = letter
        
        # Processa cada parágrafo (versão simplificada)
        full_text = []
        for para in doc.paragraphs:
            if para.text.strip():
                full_text.append(para.text)
        
        # Junta todo o texto com quebras de linha
        document_text = '\n'.join(full_text)
        
        # Converte o texto em imagem
        img = text_to_image(document_text, page_width=int(width)-100)
        
        # Salva a imagem temporariamente
        with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp_img:
            img.save(tmp_img.name)
            
            # Adiciona a imagem ao PDF
            c.drawImage(tmp_img.name, 50, height - img.height - 50, 
                       width=img.width, height=img.height)
            c.showPage()
            c.save()
            
            # Remove a imagem temporária
            os.unlink(tmp_img.name)
    
    return tmp_pdf.name

# Interface principal
uploaded_file = st.file_uploader("Faça upload do arquivo Word (.docx)", type=["docx"])

if uploaded_file is not None:
    st.success("Arquivo carregado com sucesso!")
    
    # Mostra prévia do conteúdo (opcional)
    if st.checkbox("Mostrar conteúdo do arquivo"):
        doc = Document(uploaded_file)
        for para in doc.paragraphs:
            if para.text.strip():
                st.write(para.text)
    
    # Configurações (opcional)
    with st.expander("Configurações avançadas"):
        st.slider("Tamanho da fonte nas imagens", 10, 30, 20, key="font_size")
        st.slider("Largura da página (px)", 600, 1200, 800, key="page_width")
    
    # Botão de conversão
    if st.button("Converter para PDF"):
        with st.spinner("Convertendo documento..."):
            # Cria um arquivo temporário para o DOCX
            with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as tmp_docx:
                tmp_docx.write(uploaded_file.getbuffer())
                tmp_docx_path = tmp_docx.name
            
            # Converte
            pdf_path = convert_docx_to_pdf(tmp_docx_path, "output.pdf")
            
            # Remove o arquivo DOCX temporário
            os.unlink(tmp_docx_path)
            
            # Disponibiliza para download
            with open(pdf_path, "rb") as f:
                pdf_bytes = f.read()
            
            st.success("Conversão concluída!")
            st.download_button(
                label="Baixar PDF",
                data=pdf_bytes,
                file_name="documento_convertido.pdf",
                mime="application/pdf"
            )
            
            # Remove o PDF temporário
            os.unlink(pdf_path)
else:
    st.warning("Por favor, faça upload de um arquivo Word (.docx)")

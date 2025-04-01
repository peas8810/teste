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

# Função atualizada para renderizar texto como imagem
def text_to_image(text, font_size=20, page_width=800):
    try:
        # Tentar carregar fonte Arial, caso não exista, usar padrão
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except:
            font = ImageFont.load_default(size=font_size)
        
        lines = text.split('\n')
        line_heights = []
        
        # Método atualizado para calcular tamanho do texto
        for line in lines:
            bbox = font.getbbox(line)  # Novo método no Pillow 9+
            line_height = bbox[3] - bbox[1]  # altura (y1, y2)
            line_heights.append(line_height)
        
        total_height = sum(line_heights) + 20  # Margem
        
        img = Image.new('RGB', (page_width, total_height), color=(255, 255, 255))
        d = ImageDraw.Draw(img)
        
        y = 10
        for line, line_height in zip(lines, line_heights):
            d.text((10, y), line, fill=(0, 0, 0), font=font)
            y += line_height
        
        return img
    
    except Exception as e:
        st.error(f"Erro ao converter texto em imagem: {str(e)}")
        return None

# Função principal de conversão
def convert_docx_to_pdf(docx_file, output_pdf):
    try:
        doc = Document(docx_file)
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_pdf:
            c = canvas.Canvas(tmp_pdf.name, pagesize=letter)
            width, height = letter
            
            full_text = []
            for para in doc.paragraphs:
                if para.text.strip():
                    full_text.append(para.text)
            
            document_text = '\n'.join(full_text)
            
            img = text_to_image(document_text, page_width=int(width)-100)
            if img is None:
                return None
            
            with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp_img:
                img.save(tmp_img.name, "PNG")
                
                c.drawImage(tmp_img.name, 50, height - img.height - 50, 
                           width=img.width, height=img.height, preserveAspectRatio=True)
                c.showPage()
                c.save()
                
                os.unlink(tmp_img.name)
        
        return tmp_pdf.name
    
    except Exception as e:
        st.error(f"Erro na conversão do documento: {str(e)}")
        return None

# Interface principal
uploaded_file = st.file_uploader("Faça upload do arquivo Word (.docx)", type=["docx"])

if uploaded_file is not None:
    st.success("Arquivo carregado com sucesso!")
    
    # Configurações
    with st.expander("Configurações"):
        font_size = st.slider("Tamanho da fonte", 10, 30, 14)
        page_margin = st.slider("Margem da página (px)", 50, 200, 100)
    
    if st.button("Converter para PDF"):
        with st.spinner("Convertendo documento..."):
            with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as tmp_docx:
                tmp_docx.write(uploaded_file.getbuffer())
                tmp_docx_path = tmp_docx.name
            
            pdf_path = convert_docx_to_pdf(tmp_docx_path, "output.pdf")
            
            if pdf_path:
                with open(pdf_path, "rb") as f:
                    pdf_bytes = f.read()
                
                st.success("Conversão concluída com sucesso!")
                st.download_button(
                    label="⬇️ Baixar PDF",
                    data=pdf_bytes,
                    file_name="documento_convertido.pdf",
                    mime="application/pdf"
                )
                
                os.unlink(pdf_path)
            os.unlink(tmp_docx_path)
else:
    st.info("Por favor, faça upload de um arquivo Word (.docx)")

!apt-get install -y poppler-utils tesseract-ocr libreoffice

!pip install pdf2docx PyPDF2 pdfplumber Pillow img2pdf pytesseract pdf2image ipywidgets

!apt-get update
!apt-get install -y ghostscript
!which gs  # Verifica o caminho real

# ============================================
# 📅 Importações
# ============================================
import os
import shutil
import time
import zipfile
import subprocess
import uuid
from IPython.display import display, FileLink
import ipywidgets as widgets
from google.colab import files
from PyPDF2 import PdfMerger, PdfReader, PdfWriter
from pdf2docx import Converter
from PIL import Image
import pytesseract
from pdf2image import convert_from_path

# ============================================
# 📂 Diretório de Trabalho
# ============================================
POPPLER_PATH = "/usr/bin"
WORK_DIR = "documentos"
os.makedirs(WORK_DIR, exist_ok=True)

# ============================================
# 💾 Função para Salvar Arquivos (unificada)
# ============================================
def salvar_arquivos(upload_widget):
    caminhos = []
    for nome, arquivo in upload_widget.value.items():
        # Remove caracteres especiais e espaços do nome do arquivo
        nome_base, extensao = os.path.splitext(nome)
        nome_limpo = (nome_base.replace(" ", "_")
                      .replace("ç", "c").replace("ã", "a")
                      .replace("á", "a").replace("é", "e")
                      .replace("í", "i").replace("ó", "o")
                      .replace("ú", "u").replace("ñ", "n")) + extensao.lower()
        
        caminho = os.path.join(WORK_DIR, nome_limpo)
        with open(caminho, "wb") as f:
            f.write(arquivo["content"])
        caminhos.append(caminho)
    return caminhos

# ============================================
# 📄 Funções de Conversão com Prefixos Identificáveis
# ============================================

def word_para_pdf_interface():
    upload = widgets.FileUpload(accept='.doc,.docx,.odt,.rtf', multiple=False)
    botao = widgets.Button(description="Converter para PDF", button_style='success')
    output = widgets.Output()
    
    def ao_clicar(b):
        output.clear_output()
        with output:
            caminhos = salvar_arquivos(upload)
            if not caminhos:
                print("⚠️ Nenhum arquivo carregado.")
                return
                
            caminho = caminhos[0]
            nome_base = os.path.splitext(os.path.basename(caminho))[0]
            nome_saida = f"word_{nome_base}.pdf"
            saida = os.path.join(WORK_DIR, nome_saida)
            
            # Remove arquivo existente se houver
            if os.path.exists(saida):
                os.remove(saida)
            
            # Converte usando LibreOffice
            os.system(f"libreoffice --headless --convert-to pdf --outdir '{WORK_DIR}' '{caminho}'")
            
            # Renomeia o arquivo gerado para o padrão com prefixo
            temp_pdf = os.path.join(WORK_DIR, f"{nome_base}.pdf")
            if os.path.exists(temp_pdf):
                os.rename(temp_pdf, saida)
                
            if os.path.exists(saida):
                display(widgets.HTML(f"<b>✅ PDF Gerado:</b> {nome_saida}"))
            else:
                print(f"❌ Falha ao converter: {caminho}")
    
    botao.on_click(ao_clicar)
    return widgets.VBox([upload, botao, output])

def lote_word_para_pdf_interface():
    upload = widgets.FileUpload(accept='.doc,.docx,.odt,.rtf', multiple=True)
    botao = widgets.Button(description="Converter em Lote", button_style='success')
    output = widgets.Output()
    
    def ao_clicar(b):
        output.clear_output()
        with output:
            caminhos = salvar_arquivos(upload)
            if not caminhos:
                print("⚠️ Nenhum arquivo carregado.")
                return
                
            for caminho in caminhos:
                nome_base = os.path.splitext(os.path.basename(caminho))[0]
                nome_saida = f"lote_{nome_base}.pdf"
                saida = os.path.join(WORK_DIR, nome_saida)
                
                # Remove arquivo existente se houver
                if os.path.exists(saida):
                    os.remove(saida)
                
                # Converte usando LibreOffice
                os.system(f"libreoffice --headless --convert-to pdf --outdir '{WORK_DIR}' '{caminho}'")
                
                # Renomeia o arquivo gerado para o padrão com prefixo
                temp_pdf = os.path.join(WORK_DIR, f"{nome_base}.pdf")
                if os.path.exists(temp_pdf):
                    os.rename(temp_pdf, saida)
                    
                if os.path.exists(saida):
                    display(widgets.HTML(f"<b>✅ PDF Gerado:</b> {nome_saida}"))
                else:
                    print(f"❌ Falha ao converter: {caminho}")
    
    botao.on_click(ao_clicar)
    return widgets.VBox([upload, botao, output])

def pdf_para_word_interface():
    upload = widgets.FileUpload(accept='.pdf', multiple=False)
    botao = widgets.Button(description="Converter para Word", button_style='info')
    output = widgets.Output()
    
    def ao_clicar(b):
        output.clear_output()
        with output:
            caminhos = salvar_arquivos(upload)
            if not caminhos:
                print("⚠️ Nenhum arquivo carregado.")
                return
                
            caminho = caminhos[0]
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
                    display(widgets.HTML(f"<b>✅ Word Gerado:</b> {nome_saida}"))
                else:
                    print(f"❌ Falha na conversão: {caminho}")
            except Exception as e:
                print(f"❌ Erro na conversão: {str(e)}")
    
    botao.on_click(ao_clicar)
    return widgets.VBox([upload, botao, output])

def pdf_para_jpg_interface():
    upload = widgets.FileUpload(accept='.pdf', multiple=False)
    botao = widgets.Button(description="Converter para JPG", button_style='info')
    output = widgets.Output()
    
    def ao_clicar(b):
        output.clear_output()
        with output:
            caminhos = salvar_arquivos(upload)
            if not caminhos:
                print("⚠️ Nenhum arquivo carregado.")
                return
                
            caminho = caminhos[0]
            nome_base = os.path.splitext(os.path.basename(caminho))[0]
            
            try:
                imagens = convert_from_path(caminho, poppler_path=POPPLER_PATH)
                for i, img in enumerate(imagens):
                    nome_saida = f"pdf2jpg_{nome_base}_pag{i+1}.jpg"
                    caminho_img = os.path.join(WORK_DIR, nome_saida)
                    img.save(caminho_img, "JPEG")
                    display(widgets.HTML(f"<b>🖼️ Imagem Gerada:</b> {nome_saida}"))
            except Exception as e:
                print(f"❌ Erro ao converter PDF para imagens: {str(e)}")
    
    botao.on_click(ao_clicar)
    return widgets.VBox([upload, botao, output])

def juntar_pdf_interface():
    upload = widgets.FileUpload(accept='.pdf', multiple=True)
    botao = widgets.Button(description="Juntar PDFs", button_style='primary')
    output = widgets.Output()
    
    def ao_clicar(b):
        output.clear_output()
        with output:
            caminhos = salvar_arquivos(upload)
            if len(caminhos) < 2:
                print("⚠️ É necessário carregar pelo menos 2 arquivos PDF.")
                return
                
            nome_saida = "merge_resultado.pdf"
            saida = os.path.join(WORK_DIR, nome_saida)
            
            # Remove arquivo existente se houver
            if os.path.exists(saida):
                os.remove(saida)
            
            merger = PdfMerger()
            for c in caminhos:
                merger.append(c)
            merger.write(saida)
            merger.close()
            
            if os.path.exists(saida):
                display(widgets.HTML(f"<b>✅ PDF Unido Gerado:</b> {nome_saida}"))
            else:
                print("❌ Falha ao unir PDFs.")
    
    botao.on_click(ao_clicar)
    return widgets.VBox([upload, botao, output])

def dividir_pdf_interface():
    upload = widgets.FileUpload(accept='.pdf', multiple=False)
    botao = widgets.Button(description="Dividir PDF", button_style='warning')
    output = widgets.Output()
    
    def ao_clicar(b):
        output.clear_output()
        with output:
            caminhos = salvar_arquivos(upload)
            if not caminhos:
                print("⚠️ Nenhum arquivo carregado.")
                return
                
            caminho = caminhos[0]
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
                    display(widgets.HTML(f"<b>📄 Página Gerada:</b> {nome_saida}"))
            except Exception as e:
                print(f"❌ Erro ao dividir PDF: {str(e)}")
    
    botao.on_click(ao_clicar)
    return widgets.VBox([upload, botao, output])

def ocr_pdf_interface():
    upload = widgets.FileUpload(accept='.pdf', multiple=False)
    botao = widgets.Button(description="OCR em PDF", button_style='danger')
    output = widgets.Output()
    
    def ao_clicar(b):
        output.clear_output()
        with output:
            caminhos = salvar_arquivos(upload)
            if not caminhos:
                print("⚠️ Nenhum arquivo carregado.")
                return
                
            caminho = caminhos[0]
            nome_base = os.path.splitext(os.path.basename(caminho))[0]
            nome_saida = f"ocrpdf_{nome_base}.txt"
            txt_path = os.path.join(WORK_DIR, nome_saida)
            
            # Remove arquivo existente se houver
            if os.path.exists(txt_path):
                os.remove(txt_path)
            
            try:
                imagens = convert_from_path(caminho, poppler_path=POPPLER_PATH)
                texto = ""
                for i, img in enumerate(imagens):
                    texto += f"\n\n--- Página {i+1} ---\n\n"
                    texto += pytesseract.image_to_string(img, lang='por')
                
                with open(txt_path, "w", encoding="utf-8") as f:
                    f.write(texto)
                
                if os.path.exists(txt_path):
                    display(widgets.HTML(f"<b>✅ Texto Extraído:</b> {nome_saida}"))
                else:
                    print("❌ Falha ao extrair texto.")
            except Exception as e:
                print(f"❌ Erro no OCR: {str(e)}")
    
    botao.on_click(ao_clicar)
    return widgets.VBox([upload, botao, output])

def ocr_imagem_interface():
    upload = widgets.FileUpload(accept='.jpg,.jpeg,.png', multiple=True)
    botao = widgets.Button(description="OCR em Imagens", button_style='danger')
    output = widgets.Output()
    
    def ao_clicar(b):
        output.clear_output()
        with output:
            caminhos = salvar_arquivos(upload)
            if not caminhos:
                print("⚠️ Nenhuma imagem carregada.")
                return
                
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
                    print(f"❌ Erro ao processar imagem {i+1}: {str(e)}")
            
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(texto)
            
            if os.path.exists(txt_path):
                display(widgets.HTML(f"<b>✅ Texto Extraído:</b> {nome_saida}"))
            else:
                print("❌ Falha ao extrair texto das imagens.")
    
    botao.on_click(ao_clicar)
    return widgets.VBox([upload, botao, output])

def jpg_para_pdf_interface():
    upload = widgets.FileUpload(accept='.jpg,.jpeg,.png', multiple=True)
    botao = widgets.Button(description="Imagens para PDF", button_style='info')
    output = widgets.Output()
    
    def ao_clicar(b):
        output.clear_output()
        with output:
            caminhos = salvar_arquivos(upload)
            if not caminhos:
                print("⚠️ Nenhuma imagem carregada.")
                return
                
            nome_saida = "img2pdf_resultado.pdf"
            caminho_pdf = os.path.join(WORK_DIR, nome_saida)
            
            # Remove arquivo existente se houver
            if os.path.exists(caminho_pdf):
                os.remove(caminho_pdf)
            
            try:
                imagens = []
                for caminho in caminhos:
                    img = Image.open(caminho).convert("RGB")
                    imagens.append(img)
                
                if imagens:
                    imagens[0].save(caminho_pdf, save_all=True, append_images=imagens[1:])
                    
                    if os.path.exists(caminho_pdf):
                        display(widgets.HTML(f"<b>✅ PDF Gerado:</b> {nome_saida}"))
                    else:
                        print("❌ Falha ao gerar PDF.")
            except Exception as e:
                print(f"❌ Erro ao converter imagens para PDF: {str(e)}")
    
    botao.on_click(ao_clicar)
    return widgets.VBox([upload, botao, output])

def pdf_para_pdfa_interface():
    upload = widgets.FileUpload(accept='.pdf', multiple=False)
    botao = widgets.Button(description="Converter para PDF/A", button_style='warning')
    output = widgets.Output()
    
    def ao_clicar(b):
        output.clear_output()
        with output:
            caminhos = salvar_arquivos(upload)
            if not caminhos:
                print("⚠️ Nenhum arquivo carregado.")
                return
                
            caminho = caminhos[0]
            nome_base = os.path.splitext(os.path.basename(caminho))[0]
            nome_saida = f"pdfa_{nome_base}.pdf"
            saida = os.path.join(WORK_DIR, nome_saida)
            
            # Remove arquivo existente se houver
            if os.path.exists(saida):
                os.remove(saida)
            
            gs_path = "/usr/local/bin/gs" if os.path.exists("/usr/local/bin/gs") else "/usr/bin/gs"
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
            
            try:
                resultado = subprocess.run(comando, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                if os.path.exists(saida) and resultado.returncode == 0:
                    display(widgets.HTML(f"<b>✅ PDF/A Gerado:</b> {nome_saida}"))
                else:
                    print("❌ Falha na conversão para PDF/A.")
                    if resultado.stderr:
                        print("🔍 Erro:", resultado.stderr.decode())
            except Exception as e:
                print(f"❌ Erro ao executar Ghostscript: {str(e)}")
    
    botao.on_click(ao_clicar)
    return widgets.VBox([upload, botao, output])

# ============================================
# 📄 Baixar Arquivos por Prefixo (aba específica)
# ============================================
def baixar_arquivo_widget(prefixo):
    botao = widgets.Button(description="Baixar Arquivos da Aba", button_style='primary')
    output = widgets.Output()

    def ao_clicar(b):
        output.clear_output()
        with output:
            arquivos = [f for f in os.listdir(WORK_DIR)
                        if os.path.isfile(os.path.join(WORK_DIR, f))
                        and f.startswith(prefixo)]
            
            if not arquivos:
                print("❌ Nenhum arquivo correspondente encontrado.")
                return
                
            for arq in arquivos:
                caminho = os.path.join(WORK_DIR, arq)
                try:
                    files.download(caminho)
                    print(f"📥 Enviado para download: {arq}")
                except Exception as e:
                    print(f"❌ Erro ao baixar {arq}: {str(e)}")

    botao.on_click(ao_clicar)
    return widgets.VBox([botao, output])

# ============================================
# 📦 Botão para Baixar ZIP com Todos os Arquivos
# ============================================
def baixar_zip_widget():
    botao = widgets.Button(description="Baixar Tudo (ZIP)", button_style='success')
    output = widgets.Output()

    def ao_clicar(b):
        output.clear_output()
        with output:
            zip_path = os.path.join(WORK_DIR, "todos_os_arquivos.zip")
            
            # Remove arquivo ZIP existente se houver
            if os.path.exists(zip_path):
                os.remove(zip_path)
            
            with zipfile.ZipFile(zip_path, 'w') as zipf:
                for root, _, files_ in os.walk(WORK_DIR):
                    for file in files_:
                        if file != "todos_os_arquivos.zip":
                            full_path = os.path.join(root, file)
                            arcname = os.path.relpath(full_path, WORK_DIR)
                            zipf.write(full_path, arcname)
            
            if os.path.exists(zip_path):
                print("📦 ZIP criado com sucesso!")
                files.download(zip_path)
            else:
                print("❌ Falha ao gerar o ZIP.")

    botao.on_click(ao_clicar)
    return widgets.VBox([botao, output])

# ============================================
# 🔹 Interface com Abas
# ============================================
def montar_interface():
    def adicionar_utilitarios(funcao_interface, prefixo):
        return widgets.VBox([
            funcao_interface(),
            widgets.HTML("<hr>"),
            baixar_arquivo_widget(prefixo),
            baixar_zip_widget()
        ])

    abas = widgets.Tab()
    abas.children = [
        adicionar_utilitarios(word_para_pdf_interface, "word_"),
        adicionar_utilitarios(lote_word_para_pdf_interface, "lote_"),
        adicionar_utilitarios(pdf_para_word_interface, "pdf2docx_"),
        adicionar_utilitarios(pdf_para_jpg_interface, "pdf2jpg_"),
        adicionar_utilitarios(jpg_para_pdf_interface, "img2pdf_"),
        adicionar_utilitarios(juntar_pdf_interface, "merge_"),
        adicionar_utilitarios(dividir_pdf_interface, "split_"),
        adicionar_utilitarios(ocr_pdf_interface, "ocrpdf_"),
        adicionar_utilitarios(ocr_imagem_interface, "ocrimg_"),
        adicionar_utilitarios(pdf_para_pdfa_interface, "pdfa_")
    ]

    titulos = [
        "Word → PDF",
        "Word → PDF (Lote)",
        "PDF → Word",
        "PDF → JPG",
        "Imagem → PDF",
        "Juntar PDF",
        "Dividir PDF",
        "OCR em PDF",
        "OCR em Imagens",
        "PDF → PDF/A"
    ]

    for i, titulo in enumerate(titulos):
        abas.set_title(i, titulo)

    display(abas)

# ============================================
# ▶️ Executar Interface
# ============================================
montar_interface()

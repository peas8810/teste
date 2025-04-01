import streamlit as st
import subprocess
from pathlib import Path

# Título
st.title("📄 Conversor de Word para PDF")
st.write("Envie um arquivo `.docx` para convertê-lo em PDF.")

# Upload do arquivo
uploaded_file = st.file_uploader("Escolha o arquivo .docx", type=["docx"])

# Processamento
if uploaded_file is not None:
    temp_dir = Path("temp")
    temp_dir.mkdir(exist_ok=True)

    input_path = temp_dir / uploaded_file.name

    # Salvar o arquivo temporariamente
    with open(input_path, "wb") as f:
        f.write(uploaded_file.read())

    # Converter usando LibreOffice
    st.info("Convertendo com LibreOffice...")
    result = subprocess.run([
        "libreoffice", "--headless", "--convert-to", "pdf",
        str(input_path), "--outdir", str(temp_dir)
    ], capture_output=True)

    output_path = input_path.with_suffix(".pdf")

    # Verificar se o PDF foi criado com sucesso
    if output_path.exists():
        with open(output_path, "rb") as f:
            st.success("✅ Conversão concluída!")
            st.download_button(
                label="📥 Baixar PDF",
                data=f,
                file_name=output_path.name,
                mime="application/pdf"
            )
    else:
        st.error("❌ Erro na conversão. Verifique se o LibreOffice está instalado corretamente.")
        st.text(result.stderr.decode())

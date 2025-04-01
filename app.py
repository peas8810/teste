import streamlit as st
import subprocess
from pathlib import Path
import shutil

st.title("📄 Conversor de Word para PDF")
st.write("Envie um arquivo `.docx`. Se o LibreOffice estiver disponível, ele será usado para a conversão real. Caso contrário, será feita uma simulação.")

uploaded_file = st.file_uploader("Escolha o arquivo .docx", type=["docx"])

if uploaded_file is not None:
    temp_dir = Path("temp")
    temp_dir.mkdir(exist_ok=True)

    input_path = temp_dir / uploaded_file.name
    with open(input_path, "wb") as f:
        f.write(uploaded_file.read())

    output_path = input_path.with_suffix(".pdf")

    try:
        # Tenta converter com LibreOffice
        st.info("Tentando converter com LibreOffice...")
        result = subprocess.run([
            "libreoffice", "--headless", "--convert-to", "pdf",
            str(input_path), "--outdir", str(temp_dir)
        ], capture_output=True, check=True)

        if output_path.exists():
            st.success("✅ Conversão com LibreOffice concluída!")
        else:
            raise FileNotFoundError("PDF não foi gerado pelo LibreOffice.")

    except Exception as e:
        # Fallback: simula a conversão
        st.warning("⚠️ Não foi possível usar o LibreOffice. Simulando a conversão (arquivo renomeado para .pdf).")
        shutil.copy(input_path, output_path)

    # Oferece o arquivo (real ou simulado) para download
    with open(output_path, "rb") as f:
        st.download_button(
            label="📥 Baixar PDF",
            data=f,
            file_name=output_path.name,
            mime="application/pdf"
        )

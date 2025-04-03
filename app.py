import streamlit as st
import requests

API_URL = "https://geral-pdf.onrender.com"  # URL da API FastAPI

# Configuração da página
st.set_page_config(page_title="Conversor de Documentos", layout="centered")
st.title("📄 Conversor de Documentos")

# Configuração das funcionalidades
funcionalidades = [
    ("Word para PDF", "/word-para-pdf", ["doc", "docx", "odt", "rtf"], True),
    ("PDF para Word", "/pdf-para-word", ["pdf"], False),
    ("PDF para JPG", "/pdf-para-jpg", ["pdf"], False),
    ("Imagem para PDF", "/jpg-para-pdf", ["jpg", "jpeg", "png"], True),
    ("Juntar PDFs", "/juntar-pdfs", ["pdf"], True),
    ("Dividir PDF", "/dividir-pdf", ["pdf"], False),
    ("OCR em PDF", "/ocr-pdf", ["pdf"], False),
    ("OCR em Imagens", "/ocr-imagem", ["jpg", "jpeg", "png"], True),
    ("Converter para PDF/A", "/pdf-para-pdfa", ["pdf"], False)
]

# Interface do usuário
funcionalidade = st.selectbox("Escolha a funcionalidade:", [f[0] for f in funcionalidades])
selecionada = next(f for f in funcionalidades if f[0] == funcionalidade)

# Configurações baseadas na seleção
multiplos_arquivos = selecionada[3]
tipos_arquivos = selecionada[2]
endpoint_api = selecionada[1]

# Upload de arquivos
arquivos = st.file_uploader(
    "Envie o(s) arquivo(s):",
    type=tipos_arquivos,
    accept_multiple_files=multiplos_arquivos,
    help="Selecione os arquivos para processamento"
)

if st.button("🔄 Processar", type="primary"):
    if not arquivos:
        st.warning("Por favor, envie ao menos um arquivo válido.")
    else:
        with st.spinner("Processando seus arquivos..."):
            try:
                # Garantir que temos uma lista de arquivos
                arquivos_lista = arquivos if isinstance(arquivos, list) else [arquivos]

                # CORREÇÃO PRINCIPAL AQUI - FORMATO CORRETO
                arquivos_envio = []
                for arquivo in arquivos_lista:
                    if arquivo is not None:
                        file_tuple = ("files", (arquivo.name, arquivo.getvalue(), arquivo.type))
                        arquivos_envio.append(file_tuple)
                
                # Verificar se há arquivos para enviar
                if not arquivos_envio:
                    st.error("Nenhum arquivo válido para processar.")
                    st.stop()

                # Enviar requisição para a API
                resposta = requests.post(
                    f"{API_URL}{endpoint_api}",
                    files=arquivos_envio,
                    timeout=300
                )

                # Processar a resposta
                if resposta.status_code == 200:
                    tipo_conteudo = resposta.headers.get("content-type", "")
                    
                    if "application/json" in tipo_conteudo:
                        dados = resposta.json()
                        
                        if "arquivos" in dados or "imagens" in dados:
                            arquivos_processados = dados.get("arquivos", []) + dados.get("imagens", [])
                            
                            if arquivos_processados:
                                st.success("Processamento concluído com sucesso!")
                                for arquivo in arquivos_processados:
                                    nome_arquivo = os.path.basename(arquivo)
                                    link_download = f"{API_URL}{arquivo}"
                                    st.markdown(f"**Arquivo gerado:** {nome_arquivo}  \n[🔗 Baixar arquivo]({link_download})")
                            else:
                                st.error("Nenhum arquivo foi gerado durante o processamento.")
                        else:
                            st.error("Resposta inesperada da API.")
                            st.json(dados)
                    
                    elif any(t in tipo_conteudo for t in ["application/pdf", "image/", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]):
                        extensao = "pdf" if "application/pdf" in tipo_conteudo else "docx" if "application/vnd.openxmlformats-officedocument.wordprocessingml.document" in tipo_conteudo else "jpg"
                        st.download_button(
                            label="📥 Baixar Resultado",
                            data=resposta.content,
                            file_name=f"resultado.{extensao}",
                            mime=tipo_conteudo
                        )
                    else:
                        st.error("Tipo de resposta não suportado pela aplicação.")
                
                else:
                    st.error(f"Erro na API (HTTP {resposta.status_code}):")
                    st.text(resposta.text)
            
            except requests.exceptions.Timeout:
                st.error("O tempo de processamento excedeu o limite. Tente novamente com arquivos menores.")
            except Exception as e:
                st.error(f"Erro inesperado: {str(e)}")

# Adicionar informações de ajuda
st.sidebar.markdown("""
### Ajuda
- Para conversões em lote, selecione vários arquivos
- Arquivos grandes podem demorar mais para processar
- Problemas? Recarregue a página e tente novamente
""")

import streamlit as st
import requests
import hashlib
from datetime import datetime

# 🔗 URL da API do Google Sheets
URL_GOOGLE_SHEETS = "SUA_URL_DA_API_AQUI"

# =============================
# 📋 Função para Salvar E-mails e Código de Verificação no Google Sheets
# =============================
def salvar_email_google_sheets(nome, email, codigo_verificacao):
    dados = {
        "nome": nome,
        "email": email,
        "codigo": codigo_verificacao
    }
    try:
        headers = {'Content-Type': 'application/json'}
        response = requests.post(URL_GOOGLE_SHEETS, json=dados, headers=headers)

        if response.text.strip() == "Sucesso":
            st.success("✅ E-mail, nome e código registrados com sucesso!")
        else:
            st.error(f"❌ Erro ao salvar dados no Google Sheets: {response.text}")
    except Exception as e:
        st.error(f"❌ Erro na conexão com o Google Sheets: {e}")

# =============================
# 🔎 Função para Verificar Código de Verificação na Planilha
# =============================
def verificar_codigo_google_sheets(codigo_digitado):
    try:
        response = requests.get(f"{URL_GOOGLE_SHEETS}?codigo={codigo_digitado}")
        if response.text.strip() == "Valido":
            return True
        else:
            return False
    except Exception as e:
        st.error(f"❌ Erro na conexão com o Google Sheets: {e}")
        return False

# =============================
# 🔐 Função para Gerar Código de Verificação
# =============================
def gerar_codigo_verificacao(texto):
    return hashlib.md5(texto.encode()).hexdigest()[:10].upper()

# =============================
# 💻 Interface do Streamlit
# =============================
def main():
    st.title("Registro de Usuários - Google Sheets API")

    st.subheader("📋 Registro de Usuário")
    nome = st.text_input("Nome completo")
    email = st.text_input("E-mail")

    if st.button("Salvar Dados"):
        if nome and email:
            codigo_verificacao = gerar_codigo_verificacao(email)
            salvar_email_google_sheets(nome, email, codigo_verificacao)
            st.success(f"Código de verificação gerado: **{codigo_verificacao}**")
        else:
            st.warning("⚠️ Por favor, preencha todos os campos.")

    # Verificação de código
    st.header("Verificar Autenticidade")
    codigo_digitado = st.text_input("Digite o código de verificação:")

    if st.button("Verificar Código"):
        if verificar_codigo_google_sheets(codigo_digitado):
            st.success("✅ Documento Autêntico e Original!")
        else:
            st.error("❌ Código inválido ou documento falsificado.")

if __name__ == "__main__":
    main()

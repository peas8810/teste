# =============================
# 🍀 Sistema PlagIA - Versão Otimizada e Robusta
# Performance melhorada, cache eficiente e validação robusta
# PEAS.Co 2024
# =============================

import streamlit as st
import requests
import PyPDF2
import difflib
from fpdf import FPDF
from io import BytesIO
import hashlib
from datetime import datetime, date
from PIL import Image
import qrcode
import re
from collections import Counter
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import time
import json
from typing import Dict, List, Tuple, Optional
import logging
from functools import lru_cache
import threading
from concurrent.futures import ThreadPoolExecutor
import gc

# Configuração da página
st.set_page_config(
    page_title="PlagIA Professional - Detecção Avançada de Plágio",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 🔗 URL da API gerada no Google Sheets
URL_GOOGLE_SHEETS = "https://script.google.com/macros/s/AKfycbyTpbWDxWkNRh_ZIlHuAVwZaCC2ODqTmo0Un7ZDbgzrVQBmxlYYKuoYf6yDigAPHZiZ/exec"

# Configurações globais otimizadas
CONFIG = {
    'MAX_CONSULTAS_SESSAO': 4,
    'MIN_TEXT_LENGTH': 500,
    'MAX_TEXT_LENGTH': 50000,
    'MIN_WORDS': 50,
    'TIMEOUT_API': 15,
    'MAX_REFS': 20,
    'CACHE_TTL': 3600,
}

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =============================
# CSS Otimizado e Minificado
# =============================

@st.cache_data(ttl=CONFIG['CACHE_TTL'])
def load_optimized_css():
    return """
    <style>
    /* ... (mantém todo o CSS original sem alterações) ... */
    </style>
    """

# =============================
# Funções Auxiliares Otimizadas
# =============================

@st.cache_data(ttl=CONFIG['CACHE_TTL'])
def gerar_codigo_verificacao(texto: str) -> str:
    timestamp = str(int(time.time()))
    combined = texto[:1000] + timestamp
    return hashlib.md5(combined.encode()).hexdigest()[:10].upper()

@lru_cache(maxsize=128)
def validar_texto_robusto(texto: str) -> Tuple[bool, str]:
    # ... (mantém função original) ...
    return True, "Texto válido"

# ... demais funções de extração e limpeza mantidas sem alterações ...

@st.cache_data(ttl=CONFIG['CACHE_TTL'])
def buscar_referencias_crossref_otimizado(texto: str) -> List[Dict]:
    # ... (função original) ...
    return referencias

@lru_cache(maxsize=256)
def calcular_similaridade_otimizada(texto1: str, texto2: str) -> float:
    # ... (função original) ...
    return 0.0

# =============================
# Classe PDF Otimizada
# =============================

class PDFOtimizado(FPDF):
    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=15)

    def header(self):
        self.set_font('Arial', 'B', 14)
        self.cell(0, 10, self._encode_text("Relatório PlagIA Professional - PEAS.Co"), ln=True, align='C')
        self.ln(3)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')

    def add_section(self, title: str, content: str):
        if title:
            self.set_font('Arial', 'B', 12)
            self.cell(0, 8, self._encode_text(title), ln=True)
        self.set_font('Arial', '', 10)
        self.multi_cell(0, 6, self._encode_text(content))
        self.ln(3)

    def _encode_text(self, text: str) -> str:
        try:
            return str(text).encode('latin-1', 'replace').decode('latin-1')
        except:
            return ''.join(char if ord(char) < 128 else '?' for char in str(text))


def gerar_relatorio_otimizado(referencias_sim: List, nome: str, email: str, codigo: str) -> Optional[str]:
    try:
        pdf = PDFOtimizado()
        pdf.add_page()

        data_hora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        pdf.add_section("Dados do Solicitante", f"Nome: {nome}\nE-mail: {email}\nData: {data_hora}\nCódigo: {codigo}")

        if referencias_sim:
            total_refs = len(referencias_sim)
            max_sim = max([r[1] for r in referencias_sim]) * 100
            media_sim = np.mean([r[1] for r in referencias_sim]) * 100
            stats = f"Total de Referências: {total_refs}\nSimilaridade Máxima: {max_sim:.2f}%\nSimilaridade Média: {media_sim:.2f}%"
            pdf.add_section("Estatísticas", stats)

            # Adiciona as 10 referências com título, ano e link
            pdf.add_section("Top 10 Referências com Links", "")
            for i, (titulo, sim, link, doi, ano) in enumerate(referencias_sim[:10], 1):
                ref_text = f"{i}. {titulo}\nAno: {ano or 'N/A'}\nLink: {link or doi or 'N/A'}\nSimilaridade: {sim*100:.2f}%"
                pdf.add_section("", ref_text)
        else:
            pdf.add_section("Resultado", "Nenhuma referência encontrada na base de dados.")

        caminho = "/tmp/relatorio_otimizado.pdf"
        pdf.output(caminho, 'F')
        return caminho
    except Exception as e:
        logger.error(f"Erro ao gerar PDF: {e}")
        return None

# =============================
# Demais componentes (gráficos, métricas e interface) mantidos sem alterações
# =============================

# Interface principal simplificada para foco na geração de relatório

def main():
    st.markdown(load_optimized_css(), unsafe_allow_html=True)
    # ... interface original ...
    # Ao final do processamento: gerar pdf e oferecer download
    pdf_path = gerar_relatorio_otimizado(referencias_sim, nome, email, codigo)
    if pdf_path:
        with open(pdf_path, "rb") as f:
            st.download_button(
                "📄 Baixar Relatório PDF",
                f,
                "relatorio_plagia_otimizado.pdf",
                "application/pdf"
            )

if __name__ == "__main__":
    main()

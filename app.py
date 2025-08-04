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
    'MIN_TEXT_LENGTH': 500,  # Aumentado para garantir análise significativa
    'MAX_TEXT_LENGTH': 50000,
    'MIN_WORDS': 50,  # Mínimo de palavras
    'TIMEOUT_API': 15,  # Timeout para APIs
    'MAX_REFS': 20,  # Máximo de referências para processar
    'CACHE_TTL': 3600,  # Cache por 1 hora
}

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =============================
# CSS Otimizado e Minificado
# =============================

@st.cache_data(ttl=CONFIG['CACHE_TTL'])
def load_optimized_css():
    """CSS otimizado com carregamento em cache"""
    return """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    .main .block-container{padding-top:1rem;padding-bottom:2rem;max-width:1200px}
    html,body,[class*="css"]{font-family:'Inter',sans-serif}
    
    .hero-header{
        background:linear-gradient(-45deg,#667eea,#764ba2,#f093fb,#f5576c);
        background-size:400% 400%;
        animation:gradientShift 15s ease infinite;
        padding:2rem;border-radius:20px;margin-bottom:2rem;
        text-align:center;color:white;
        box-shadow:0 20px 40px rgba(0,0,0,0.1);
        position:relative;overflow:hidden
    }
    
    @keyframes gradientShift{
        0%{background-position:0% 50%}
        50%{background-position:100% 50%}
        100%{background-position:0% 50%}
    }
    
    .glass-card{
        background:rgba(255,255,255,0.25);
        backdrop-filter:blur(10px);border-radius:20px;
        border:1px solid rgba(255,255,255,0.18);
        padding:2rem;margin:1rem 0;
        box-shadow:0 8px 32px rgba(31,38,135,0.37);
        transition:all 0.3s ease
    }
    
    .metric-container{
        background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);
        border-radius:15px;padding:1.5rem;color:white;
        text-align:center;transition:all 0.3s ease;
        cursor:pointer;margin:0.5rem 0
    }
    
    .metric-container:hover{transform:scale(1.05)}
    
    .metric-value{font-size:2.5rem;font-weight:700;margin-bottom:0.5rem}
    .metric-label{font-size:0.9rem;opacity:0.9;text-transform:uppercase}
    
    .usage-counter{
        background:linear-gradient(135deg,#2196F3,#1976D2);
        color:white;padding:1rem;border-radius:15px;
        text-align:center;font-weight:bold;margin-bottom:1rem
    }
    
    .usage-counter.limit-reached{
        background:linear-gradient(135deg,#f44336,#d32f2f);
        animation:pulse 2s infinite
    }
    
    @keyframes pulse{0%{transform:scale(1)}50%{transform:scale(1.02)}100%{transform:scale(1)}}
    
    .stButton>button{
        background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);
        color:white;border:none;border-radius:25px;
        padding:0.75rem 2rem;font-weight:600;
        transition:all 0.3s ease;
        box-shadow:0 4px 15px rgba(102,126,234,0.3)
    }
    
    .stButton>button:hover{transform:translateY(-2px)}
    .stButton>button:disabled{background:#cccccc;transform:none}
    
    .sidebar-modern{
        background:linear-gradient(180deg,#f8f9fa 0%,#e9ecef 100%);
        border-radius:15px;padding:1.5rem;margin:1rem 0;
        border-left:4px solid #667eea;
        box-shadow:0 4px 15px rgba(0,0,0,0.1)
    }
    
    .analysis-section{
        background:#f8f9fa;padding:2rem;border-radius:15px;
        margin:1rem 0;border:1px solid #e9ecef;
        transition:all 0.3s ease
    }
    
    .recommendation-box{
        background:linear-gradient(135deg,#17a2b8,#138496);
        color:white;padding:1.5rem;border-radius:12px;
        margin:1rem 0;border-left:5px solid #0c5460
    }
    
    .loading-spinner{
        border:4px solid #f3f3f3;border-top:4px solid #667eea;
        border-radius:50%;width:40px;height:40px;
        animation:spin 1s linear infinite;margin:20px auto
    }
    
    @keyframes spin{0%{transform:rotate(0deg)}100%{transform:rotate(360deg)}}
    
    .error-message{
        background:#f8d7da;color:#721c24;padding:1rem;
        border-radius:8px;border:1px solid #f5c6cb;margin:1rem 0
    }
    
    .success-message{
        background:#d4edda;color:#155724;padding:1rem;
        border-radius:8px;border:1px solid #c3e6cb;margin:1rem 0
    }
    
    @media (max-width:768px){
        .hero-header{padding:1.5rem 1rem}
        .glass-card{padding:1.5rem;margin:0.5rem 0}
        .metric-value{font-size:2rem}
    }
    </style>
    """

# =============================
# Funções Auxiliares Otimizadas
# =============================

@st.cache_data(ttl=CONFIG['CACHE_TTL'])
def gerar_codigo_verificacao(texto: str) -> str:
    """Gera código de verificação único com cache"""
    timestamp = str(int(time.time()))
    combined = texto[:1000] + timestamp  # Limita texto para performance
    return hashlib.md5(combined.encode()).hexdigest()[:10].upper()

@lru_cache(maxsize=128)
def validar_texto_robusto(texto: str) -> Tuple[bool, str]:
    """Validação robusta de texto com cache"""
    if not texto or not isinstance(texto, str):
        return False, "Texto inválido ou vazio"
    
    texto_limpo = texto.strip()
    
    # Verificar comprimento mínimo
    if len(texto_limpo) < CONFIG['MIN_TEXT_LENGTH']:
        return False, f"Texto muito curto. Mínimo de {CONFIG['MIN_TEXT_LENGTH']} caracteres necessários. Atual: {len(texto_limpo)}"
    
    # Verificar comprimento máximo
    if len(texto_limpo) > CONFIG['MAX_TEXT_LENGTH']:
        return False, f"Texto muito longo. Máximo de {CONFIG['MAX_TEXT_LENGTH']} caracteres permitidos"
    
    # Verificar número de palavras
    palavras = len(texto_limpo.split())
    if palavras < CONFIG['MIN_WORDS']:
        return False, f"Texto com poucas palavras. Mínimo de {CONFIG['MIN_WORDS']} palavras necessárias. Atual: {palavras}"
    
    # Verificar se não é apenas espaços ou caracteres especiais
    texto_alfanum = re.sub(r'[^a-zA-Z0-9\s]', '', texto_limpo)
    if len(texto_alfanum.strip()) < CONFIG['MIN_TEXT_LENGTH'] * 0.5:
        return False, "Texto contém poucos caracteres alfanuméricos válidos"
    
    return True, "Texto válido"

def extrair_texto_pdf_otimizado(arquivo_pdf) -> str:
    """Extração otimizada de texto de PDF"""
    try:
        leitor_pdf = PyPDF2.PdfReader(arquivo_pdf)
        texto_completo = []
        
        # Limitar número de páginas para performance
        max_paginas = min(len(leitor_pdf.pages), 100)
        
        for i in range(max_paginas):
            try:
                pagina = leitor_pdf.pages[i]
                texto_pagina = pagina.extract_text()
                if texto_pagina:
                    texto_completo.append(texto_pagina)
            except Exception as e:
                logger.warning(f"Erro ao extrair página {i+1}: {e}")
                continue
        
        texto_final = " ".join(texto_completo)
        
        # Limpeza básica para performance
        texto_final = re.sub(r'\s+', ' ', texto_final)
        texto_final = texto_final.strip()
        
        return texto_final
        
    except Exception as e:
        logger.error(f"Erro ao processar PDF: {e}")
        return ""

@lru_cache(maxsize=64)
def limpar_texto_otimizado(texto_bruto: str) -> str:
    """Limpeza otimizada de texto com cache"""
    if not texto_bruto:
        return ""
    
    # Dividir em linhas e filtrar
    linhas = texto_bruto.splitlines()
    linhas_filtradas = []
    
    # Padrões para ignorar (compilados para performance)
    padroes_ignorar = [
        re.compile(r"^Página?\s*\d+$", re.IGNORECASE),
        re.compile(r"^doi\s*:", re.IGNORECASE),
        re.compile(r"^\d+$"),
        re.compile(r"^[A-Z\s]{2,}$"),
        re.compile(r"^www\.", re.IGNORECASE),
        re.compile(r"^http", re.IGNORECASE),
    ]
    
    capturar = False
    contador_linhas = Counter(linhas)
    
    for linha in linhas:
        linha = linha.strip()
        
        # Filtros básicos
        if not linha or len(linha) < 5:
            continue
            
        # Ignorar linhas muito repetidas
        if contador_linhas[linha] > 3:
            continue
        
        # Aplicar padrões de filtro
        ignorar = any(padrao.match(linha) for padrao in padroes_ignorar)
        if ignorar:
            continue
        
        # Ativar captura após resumo
        if re.search(r"\b(Resumo|Abstract|Introdução|Introduction)\b", linha, re.IGNORECASE):
            capturar = True
        
        if capturar:
            linhas_filtradas.append(linha)
        
        # Parar em referências
        if re.search(r"\b(Refer[eê]ncias|Bibliografia|References)\b", linha, re.IGNORECASE):
            break
        
        # Limitar para performance
        if len(linhas_filtradas) > 1000:
            break
    
    return " ".join(linhas_filtradas)

def salvar_email_google_sheets_otimizado(nome: str, email: str, codigo: str) -> bool:
    """Salvamento otimizado com timeout e retry"""
    dados = {
        "nome": nome[:100],  # Limitar tamanho
        "email": email[:100],
        "codigo": codigo,
        "data": str(date.today())
    }
    
    try:
        headers = {'Content-Type': 'application/json'}
        response = requests.post(
            URL_GOOGLE_SHEETS, 
            json=dados, 
            headers=headers, 
            timeout=CONFIG['TIMEOUT_API']
        )
        return response.text.strip() == "Sucesso"
    except requests.exceptions.RequestException as e:
        logger.error(f"Erro ao salvar no Google Sheets: {e}")
        return False

def verificar_codigo_google_sheets_otimizado(codigo: str) -> bool:
    """Verificação otimizada com timeout"""
    try:
        response = requests.get(
            f"{URL_GOOGLE_SHEETS}?codigo={codigo}", 
            timeout=CONFIG['TIMEOUT_API']
        )
        return response.text.strip() == "Valido"
    except requests.exceptions.RequestException as e:
        logger.error(f"Erro ao verificar código: {e}")
        return False

@st.cache_data(ttl=CONFIG['CACHE_TTL'])
def buscar_referencias_crossref_otimizado(texto: str) -> List[Dict]:
    """Busca otimizada de referências com cache"""
    if not texto or len(texto) < 100:
        return []
    
    # Extrair palavras-chave mais relevantes
    palavras = texto.split()[:20]  # Primeiras 20 palavras
    palavras_filtradas = [p for p in palavras if len(p) > 3 and p.isalpha()][:10]
    
    if not palavras_filtradas:
        return []
    
    query = "+".join(palavras_filtradas)
    url = f"https://api.crossref.org/works?query={query}&rows={CONFIG['MAX_REFS']}&sort=relevance"
    
    try:
        headers = {
            'User-Agent': 'PlagIA/2.0 (mailto:pesas8810@gmail.com)',
            'Accept': 'application/json'
        }
        
        response = requests.get(url, headers=headers, timeout=CONFIG['TIMEOUT_API'])
        response.raise_for_status()
        
        data = response.json()
        referencias = []
        
        for item in data.get("message", {}).get("items", []):
            titulo = item.get("title", ["Sem título"])[0] if item.get("title") else "Sem título"
            resumo = item.get("abstract", "")[:500]  # Limitar tamanho
            link = item.get("URL", "")
            doi = item.get("DOI", "")
            ano = ""
            
            # Extrair ano
            if "published-print" in item:
                try:
                    ano = str(item["published-print"]["date-parts"][0][0])
                except (IndexError, KeyError):
                    pass
            elif "published-online" in item:
                try:
                    ano = str(item["published-online"]["date-parts"][0][0])
                except (IndexError, KeyError):
                    pass
            
            referencias.append({
                "titulo": titulo[:200],  # Limitar tamanho
                "resumo": resumo,
                "link": link,
                "doi": doi,
                "ano": ano
            })
        
        return referencias
    
    except Exception as e:
        logger.error(f"Erro ao buscar referências: {e}")
        return []

@lru_cache(maxsize=256)
def calcular_similaridade_otimizada(texto1: str, texto2: str) -> float:
    """Cálculo otimizado de similaridade com cache"""
    if not texto1 or not texto2:
        return 0.0
    
    # Limitar tamanho dos textos para performance
    texto1_norm = re.sub(r'\s+', ' ', texto1.lower().strip())[:2000]
    texto2_norm = re.sub(r'\s+', ' ', texto2.lower().strip())[:2000]
    
    if not texto1_norm or not texto2_norm:
        return 0.0
    
    try:
        similarity = difflib.SequenceMatcher(None, texto1_norm, texto2_norm).ratio()
        return similarity
    except Exception as e:
        logger.error(f"Erro ao calcular similaridade: {e}")
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
    """Geração otimizada de relatório PDF"""
    try:
        pdf = PDFOtimizado()
        pdf.add_page()
        
        # Dados básicos
        data_hora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        pdf.add_section("Dados do Solicitante", f"Nome: {nome}\nE-mail: {email}\nData: {data_hora}\nCódigo: {codigo}")
        
        # Estatísticas
        if referencias_sim:
            total_refs = len(referencias_sim)
            max_sim = max([r[1] for r in referencias_sim]) * 100
            media_sim = np.mean([r[1] for r in referencias_sim]) * 100
            
            stats = f"Total de Referências: {total_refs}\nSimilaridade Máxima: {max_sim:.2f}%\nSimilaridade Média: {media_sim:.2f}%"
            pdf.add_section("Estatísticas", stats)
            
            # Top 5 referências (limitado para performance)
            pdf.add_section("Top 5 Referências", "")
            for i, (titulo, sim, link, doi, ano) in enumerate(referencias_sim[:5], 1):
                ref_text = f"{i}. {titulo[:100]}...\nSimilaridade: {sim*100:.2f}%"
                if ano:
                    ref_text += f"\nAno: {ano}"
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
# Visualizações Otimizadas
# =============================

@st.cache_data(ttl=CONFIG['CACHE_TTL'])
def criar_grafico_barras_otimizado(referencias_sim: List) -> Optional[go.Figure]:
    """Gráfico de barras otimizado com cache"""
    if not referencias_sim:
        return None
    
    try:
        # Limitar a 10 referências para performance
        refs = referencias_sim[:10]
        titulos = [ref[0][:40] + "..." if len(ref[0]) > 40 else ref[0] for ref in refs]
        similaridades = [ref[1] * 100 for ref in refs]
        
        fig = go.Figure(data=[
            go.Bar(
                x=similaridades,
                y=titulos,
                orientation='h',
                marker=dict(
                    color=similaridades,
                    colorscale='RdYlBu_r',
                    showscale=True
                )
            )
        ])
        
        fig.update_layout(
            title="Top 10 Referências por Similaridade",
            xaxis_title="Similaridade (%)",
            height=400,  # Reduzido para performance
            template="plotly_white",
            margin=dict(l=20, r=20, t=40, b=20)
        )
        
        return fig
    except Exception as e:
        logger.error(f"Erro ao criar gráfico: {e}")
        return None

def exibir_metricas_otimizadas(referencias_sim: List):
    """Métricas otimizadas sem gráficos pesados"""
    if not referencias_sim:
        st.warning("Nenhuma referência encontrada para análise.")
        return
    
    similaridades = [ref[1] for ref in referencias_sim]
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-value">{len(referencias_sim)}</div>
            <div class="metric-label">Total Referências</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        max_sim = max(similaridades) * 100
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-value">{max_sim:.1f}%</div>
            <div class="metric-label">Máxima</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        media_sim = np.mean(similaridades) * 100
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-value">{media_sim:.1f}%</div>
            <div class="metric-label">Média</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        refs_altas = len([s for s in similaridades if s > 0.3])
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-value">{refs_altas}</div>
            <div class="metric-label">Alta Similaridade</div>
        </div>
        """, unsafe_allow_html=True)

# =============================
# Interface Principal Otimizada
# =============================

def main():
    # Carregar CSS otimizado
    st.markdown(load_optimized_css(), unsafe_allow_html=True)
    
    # Header otimizado
    st.markdown("""
    <div class="hero-header">
        <h1 style="font-size: 2.5rem; margin-bottom: 0.5rem;">🔍 PlagIA Professional</h1>
        <p style="font-size: 1rem; margin: 0;">Sistema Otimizado de Detecção de Plágio</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Inicializar session state
    if "consultas" not in st.session_state:
        st.session_state["consultas"] = 0
    if "historico" not in st.session_state:
        st.session_state["historico"] = []
    
    # Sidebar otimizada
    with st.sidebar:
        st.markdown("""
        <div class="sidebar-modern">
            <h3>📊 Painel de Controle</h3>
        </div>
        """, unsafe_allow_html=True)
        
        consultas_restantes = CONFIG['MAX_CONSULTAS_SESSAO'] - st.session_state["consultas"]
        classe_contador = "limit-reached" if consultas_restantes <= 0 else ""
        
        st.markdown(f"""
        <div class="usage-counter {classe_contador}">
            <h4>Consultas Restantes</h4>
            <h2>{consultas_restantes}/{CONFIG['MAX_CONSULTAS_SESSAO']}</h2>
        </div>
        """, unsafe_allow_html=True)
        
        # Histórico simplificado
        if st.session_state["historico"]:
            st.markdown("### 📋 Histórico")
            for item in st.session_state["historico"][-3:]:  # Apenas últimos 3
                st.markdown(f"**{item['nome'][:20]}...** - {item['timestamp']}")
    
    # Layout principal otimizado
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        <div class="glass-card">
            <h3>📝 Registro do Usuário</h3>
        </div>
        """, unsafe_allow_html=True)
        
        nome = st.text_input("Nome completo", placeholder="Digite seu nome completo")
        email = st.text_input("E-mail", placeholder="Digite seu e-mail")
        
        st.markdown("""
        <div class="glass-card">
            <h3>📄 Upload do Documento</h3>
        </div>
        """, unsafe_allow_html=True)
        
        # Modificação para teste: permite carregar um arquivo de teste
        # Em um ambiente real, você usaria st.file_uploader
        arquivo_pdf = st.file_uploader("Envie o artigo em PDF", type=["pdf"])
        
        # Adicione um botão para carregar um PDF de teste (apenas para desenvolvimento/teste)
        if st.checkbox("Usar PDF de Teste (apenas para desenvolvimento)"):
            with open("/home/ubuntu/teste_curto.pdf", "rb") as f:
                arquivo_pdf = BytesIO(f.read())
                arquivo_pdf.name = "teste_curto.pdf" # Adiciona um nome ao BytesIO
                st.info("PDF de teste carregado: teste_curto.pdf")

        processar = st.button("🚀 Analisar Documento", disabled=(consultas_restantes <= 0))
    
    with col2:
        st.markdown("""
        <div class="glass-card">
            <h3>ℹ️ Sistema</h3>
            <p><strong>Versão:</strong> Otimizada 2.1</p>
            <p><strong>Performance:</strong> Melhorada</p>
            <p><strong>Cache:</strong> Ativo</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div class="recommendation-box">
            <h4>📋 Requisitos</h4>
            <ul>
                <li>Mínimo {CONFIG['MIN_TEXT_LENGTH']} caracteres</li>
                <li>Mínimo {CONFIG['MIN_WORDS']} palavras</li>
                <li>PDF com texto selecionável</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    # Processamento otimizado
    if processar:
        if not nome or not email:
            st.error("⚠️ Por favor, preencha nome e e-mail.")
            return
        
        if not arquivo_pdf:
            st.error("⚠️ Por favor, envie um arquivo PDF.")
            return
        
        if consultas_restantes <= 0:
            st.error("❌ Limite de consultas atingido.")
            return
        
        # Processamento com feedback otimizado
        progress_container = st.container()
        
        with progress_container:
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            try:
                # Extração de texto
                status_text.text("🔄 Extraindo texto do PDF...")
                progress_bar.progress(20)
                
                texto_extraido = extrair_texto_pdf_otimizado(arquivo_pdf)
                if not texto_extraido:
                    st.error("❌ Não foi possível extrair texto do PDF.")
                    return
                
                # Validação robusta
                status_text.text("🔍 Validando texto...")
                progress_bar.progress(30)
                
                valido, mensagem = validar_texto_robusto(texto_extraido)
                if not valido:
                    st.error(f"❌ {mensagem}")
                    return
                
                # Limpeza de texto
                status_text.text("🧹 Processando texto...")
                progress_bar.progress(40)
                
                texto_limpo = limpar_texto_otimizado(texto_extraido)
                
                # Validação pós-limpeza
                valido_limpo, mensagem_limpo = validar_texto_robusto(texto_limpo)
                if not valido_limpo:
                    st.error(f"❌ Após processamento: {mensagem_limpo}")
                    return
                
                # Busca de referências
                status_text.text("🔎 Buscando referências...")
                progress_bar.progress(60)
                
                referencias = buscar_referencias_crossref_otimizado(texto_limpo)
                
                if not referencias:
                    st.warning("⚠️ Nenhuma referência encontrada na base de dados.")
                    progress_bar.progress(100)
                    st.session_state["consultas"] += 1
                    return
                
                # Cálculo de similaridades
                status_text.text("📊 Calculando similaridades...")
                progress_bar.progress(80)
                
                referencias_sim = []
                for ref in referencias[:CONFIG['MAX_REFS']]:  # Limitar para performance
                    base_texto = f"{ref['titulo']} {ref['resumo']}"
                    sim = calcular_similaridade_otimizada(texto_limpo, base_texto)
                    referencias_sim.append((ref["titulo"], sim, ref["link"], ref["doi"], ref["ano"]))
                
                referencias_sim.sort(key=lambda x: x[1], reverse=True)
                
                # Finalização
                status_text.text("✅ Gerando resultados...")
                progress_bar.progress(90)
                
                codigo = gerar_codigo_verificacao(texto_limpo)
                salvar_email_google_sheets_otimizado(nome, email, codigo)
                
                # Adicionar ao histórico
                st.session_state["historico"].append({
                    "nome": nome,
                    "timestamp": datetime.now().strftime("%H:%M"),
                    "codigo": codigo
                })
                
                progress_bar.progress(100)
                time.sleep(0.5)
                
                # Limpar interface de progresso
                progress_container.empty()
                
                # Exibir resultados
                st.success(f"✅ Análise concluída! Código: **{codigo}**")
                
                # Métricas otimizadas
                st.markdown("### 📊 Resultados")
                exibir_metricas_otimizadas(referencias_sim)
                
                # Gráfico otimizado (opcional)
                if len(referencias_sim) > 0:
                    with st.expander("📈 Visualização Detalhada", expanded=False):
                        grafico = criar_grafico_barras_otimizado(referencias_sim)
                        if grafico:
                            st.plotly_chart(grafico, use_container_width=True)
                
                # Tabela simplificada
                if referencias_sim:
                    st.markdown("### 📋 Top 10 Referências")
                    
                    import pandas as pd
                    df_refs = pd.DataFrame([
                        {
                            "#": i+1,
                            "Título": ref[0][:60] + "..." if len(ref[0]) > 60 else ref[0],
                            "Similaridade": f"{ref[1]*100:.1f}%",
                            "Ano": ref[4] if ref[4] else "N/A"
                        }
                        for i, ref in enumerate(referencias_sim[:10])
                    ])
                    
                    st.dataframe(df_refs, use_container_width=True, hide_index=True)
                
                # Relatório PDF otimizado
                pdf_path = gerar_relatorio_otimizado(referencias_sim, nome, email, codigo)
                if pdf_path:
                    with open(pdf_path, "rb") as f:
                        st.download_button(
                            "📄 Baixar Relatório PDF",
                            f,
                            "relatorio_plagia_otimizado.pdf",
                            "application/pdf"
                        )
                
                # Incrementar contador
                st.session_state["consultas"] += 1
                
                # Limpeza de memória
                gc.collect()
                
            except Exception as e:
                logger.error(f"Erro durante processamento: {e}")
                st.error(f"❌ Erro durante o processamento: {str(e)}")
                progress_container.empty()
    
    # Seção de verificação otimizada
    st.markdown("---")
    st.markdown("### 🔍 Verificação de Código")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        codigo_input = st.text_input("Código de verificação", placeholder="Ex: A1B2C3D4E5")
    with col2:
        verificar = st.button("🔍 Verificar")
    
    if verificar and codigo_input:
        with st.spinner("Verificando..."):
            if verificar_codigo_google_sheets_otimizado(codigo_input):
                st.success("✅ Documento autêntico!")
            else:
                st.error("❌ Código inválido.")
    
    # Seção PIX simplificada
    st.markdown("---")
    st.markdown("""
    <div class="recommendation-box">
        <h3>🍀 Apoie o Projeto</h3>
        <p><strong>PIX:</strong> pesas8810@gmail.com | <strong>Valor:</strong> R$ 20,00</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()

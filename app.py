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
    'MIN_TEXT_LENGTH': 500,  # Mínimo de caracteres para análise
    'MAX_TEXT_LENGTH': 50000,
    'MIN_WORDS': 50,         # Mínimo de palavras
    'TIMEOUT_API': 15,       # Timeout para chamadas HTTP
    'MAX_REFS': 20,          # Máximo de referências retornadas
    'CACHE_TTL': 3600,       # Cache por 1 hora
}

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =============================
# CSS Otimizado e Minificado
# =============================
@st.cache_data(ttl=CONFIG['CACHE_TTL'])
def load_optimized_css():
    """Retorna o CSS minificado e carregado em cache"""
    return """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    .main .block-container{padding-top:1rem;padding-bottom:2rem;max-width:1200px}
    html,body,[class*="css"]{font-family:'Inter',sans-serif}
    .hero-header{background:linear-gradient(-45deg,#667eea,#764ba2,#f093fb,#f5576c);background-size:400% 400%;animation:gradientShift 15s ease infinite;padding:2rem;border-radius:20px;margin-bottom:2rem;text-align:center;color:white;box-shadow:0 20px 40px rgba(0,0,0,0.1);position:relative;overflow:hidden}
    @keyframes gradientShift{0%{background-position:0% 50%}50%{background-position:100% 50%}100%{background-position:0% 50%}}
    .glass-card{background:rgba(255,255,255,0.25);backdrop-filter:blur(10px);border-radius:20px;border:1px solid rgba(255,255,255,0.18);padding:2rem;margin:1rem 0;box-shadow:0 8px 32px rgba(31,38,135,0.37);transition:all 0.3s ease}
    .metric-container{background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);border-radius:15px;padding:1.5rem;color:white;text-align:center;transition:all 0.3s ease;cursor:pointer;margin:0.5rem 0}
    .metric-container:hover{transform:scale(1.05)}.metric-value{font-size:2.5rem;font-weight:700;margin-bottom:0.5rem}.metric-label{font-size:0.9rem;opacity:0.9;text-transform:uppercase}
    .usage-counter{background:linear-gradient(135deg,#2196F3,#1976D2);color:white;padding:1rem;border-radius:15px;text-align:center;font-weight:bold;margin-bottom:1rem}
    .usage-counter.limit-reached{background:linear-gradient(135deg,#f44336,#d32f2f);animation:pulse 2s infinite}
    @keyframes pulse{0%{transform:scale(1)}50%{transform:scale(1.02)}100%{transform:scale(1)}}
    .stButton>button{background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;border:none;border-radius:25px;padding:0.75rem 2rem;font-weight:600;transition:all 0.3s ease;box-shadow:0 4px 15px rgba(102,126,234,0.3)}
    .stButton>button:hover{transform:translateY(-2px)}.stButton>button:disabled{background:#cccccc;transform:none}
    .sidebar-modern{background:linear-gradient(180deg,#f8f9fa 0%,#e9ecef 100%);border-radius:15px;padding:1.5rem;margin:1rem 0;border-left:4px solid #667eea;box-shadow:0 4px 15px rgba(0,0,0,0.1)}
    .analysis-section{background:#f8f9fa;padding:2rem;border-radius:15px;margin:1rem 0;border:1px solid #e9ecef;transition:all 0.3s ease}
    .recommendation-box{background:linear-gradient(135deg,#17a2b8,#138496);color:white;padding:1.5rem;border-radius:12px;margin:1rem 0;border-left:5px solid #0c5460}
    .loading-spinner{border:4px solid #f3f3f3;border-top:4px solid #667eea;border-radius:50%;width:40px;height:40px;animation:spin 1s linear infinite;margin:20px auto}@keyframes spin{0%{transform:rotate(0deg)}100%{transform:rotate(360deg)}}
    .error-message{background:#f8d7da;color:#721c24;padding:1rem;border-radius:8px;border:1px solid #f5c6cb;margin:1rem 0}
    .success-message{background:#d4edda;color:#155724;padding:1rem;border-radius:8px;border:1px solid #c3e6cb;margin:1rem 0}
    @media (max-width:768px){.hero-header{padding:1.5rem 1rem}.glass-card{padding:1.5rem;margin:0.5rem 0}.metric-value{font-size:2rem}}
    </style>
    """

# =============================
# Funções Auxiliares Otimizadas
# =============================

@st.cache_data(ttl=CONFIG['CACHE_TTL'])
def gerar_codigo_verificacao(texto: str) -> str:
    """Gera código único de verificação"""
    timestamp = str(int(time.time()))
    combined = texto[:1000] + timestamp
    return hashlib.md5(combined.encode()).hexdigest()[:10].upper()

@lru_cache(maxsize=128)
def validar_texto_robusto(texto: str) -> Tuple[bool, str]:
    """Valida comprimento e conteúdo do texto"""
    if not texto or not isinstance(texto, str):
        return False, "Texto inválido ou vazio"
    texto_limpo = texto.strip()
    if len(texto_limpo) < CONFIG['MIN_TEXT_LENGTH']:
        return False, f"Texto muito curto. Mínimo de {CONFIG['MIN_TEXT_LENGTH']} caracteres. Atual: {len(texto_limpo)}"
    if len(texto_limpo) > CONFIG['MAX_TEXT_LENGTH']:
        return False, f"Texto muito longo. Máximo de {CONFIG['MAX_TEXT_LENGTH']} caracteres permitidos"
    palavras = len(texto_limpo.split())
    if palavras < CONFIG['MIN_WORDS']:
        return False, f"Texto com poucas palavras. Mínimo de {CONFIG['MIN_WORDS']} palavras. Atual: {palavras}"
    texto_alfanum = re.sub(r'[^a-zA-Z0-9\s]', '', texto_limpo)
    if len(texto_alfanum.strip()) < CONFIG['MIN_TEXT_LENGTH'] * 0.5:
        return False, "Texto contém poucos caracteres alfanuméricos válidos"
    return True, "Texto válido"


def extrair_texto_pdf_otimizado(arquivo_pdf) -> str:
    """Extrai texto de PDF de forma eficiente"""
    try:
        leitor = PyPDF2.PdfReader(arquivo_pdf)
        paginas = min(len(leitor.pages), 100)
        texto = []
        for i in range(paginas):
            try:
                p = leitor.pages[i].extract_text()
                if p:
                    texto.append(p)
            except Exception:
                continue
        retorno = " ".join(texto)
        retorno = re.sub(r'\s+', ' ', retorno).strip()
        return retorno
    except Exception as e:
        logger.error(f"Erro ao extrair PDF: {e}")
        return ""

@lru_cache(maxsize=64)
def limpar_texto_otimizado(texto_bruto: str) -> str:
    """Limpa header/footer e metadados do texto"""
    if not texto_bruto:
        return ""
    linhas = texto_bruto.splitlines()
    padroes = [
        re.compile(r"^Página?\s*\d+$", re.IGNORECASE),
        re.compile(r"^doi\s*:", re.IGNORECASE),
        re.compile(r"^www\.", re.IGNORECASE),
        re.compile(r"^http", re.IGNORECASE),
    ]
    filtradas = []
    capturar = False
    c = Counter(linhas)
    for l in linhas:
        l = l.strip()
        if not l or len(l) < 5 or c[l] > 3:
            continue
        if any(p.match(l) for p in padroes):
            continue
        if re.search(r"\b(Resumo|Abstract|Introdução|Introduction)\b", l, re.IGNORECASE):
            capturar = True
        if capturar:
            filtradas.append(l)
        if re.search(r"\b(Refer[eê]ncias|Bibliografia|References)\b", l, re.IGNORECASE):
            break
        if len(filtradas) > 1000:
            break
    return " ".join(filtradas)


def salvar_email_google_sheets_otimizado(nome: str, email: str, codigo: str) -> bool:
    dados = {"nome": nome[:100], "email": email[:100], "codigo": codigo, "data": str(date.today())}
    try:
        res = requests.post(URL_GOOGLE_SHEETS, json=dados, headers={'Content-Type':'application/json'}, timeout=CONFIG['TIMEOUT_API'])
        return res.text.strip() == "Sucesso"
    except Exception as e:
        logger.error(f"Erro Sheets: {e}")
        return False


def verificar_codigo_google_sheets_otimizado(codigo: str) -> bool:
    try:
        res = requests.get(f"{URL_GOOGLE_SHEETS}?codigo={codigo}", timeout=CONFIG['TIMEOUT_API'])
        return res.text.strip() == "Valido"
    except Exception as e:
        logger.error(f"Erro verificar código: {e}")
        return False

@st.cache_data(ttl=CONFIG['CACHE_TTL'])
def buscar_referencias_crossref_otimizado(texto: str) -> List[Dict]:
    if not texto or len(texto) < 100:
        return []
    palavras = texto.split()[:20]
    filt = [p for p in palavras if len(p)>3 and p.isalpha()][:10]
    query = "+".join(filt)
    url = f"https://api.crossref.org/works?query={query}&rows={CONFIG['MAX_REFS']}&sort=relevance"
    try:
        hdr = {'User-Agent':'PlagIA/2.0 (mailto:pesas8810@gmail.com)','Accept':'application/json'}
        r = requests.get(url, headers=hdr, timeout=CONFIG['TIMEOUT_API'])
        r.raise_for_status()
        items = r.json().get('message',{}).get('items',[])
        refs = []
        for item in items:
            t = item.get('title',['Sem título'])[0]
            resumo = item.get('abstract','')[:500]
            link = item.get('URL','')
            doi = item.get('DOI','')
            ano = ''
            pp = item.get('published-print') or item.get('published-online')
            if pp:
                try: ano = str(pp['date-parts'][0][0])
                except: pass
            refs.append({'titulo':t,'resumo':resumo,'link':link,'doi':doi,'ano':ano})
        return refs
    except Exception as e:
        logger.error(f"Erro buscar refs: {e}")
        return []

@lru_cache(maxsize=256)
def calcular_similaridade_otimizada(texto1: str, texto2: str) -> float:
    if not texto1 or not texto2: return 0.0
    t1 = re.sub(r'\s+',' ',texto1.lower().strip())[:2000]
    t2 = re.sub(r'\s+',' ',texto2.lower().strip())[:2000]
    try:
        return difflib.SequenceMatcher(None,t1,t2).ratio()
    except:
        return 0.0

# =============================
# Classe PDF Otimizada
# =============================
class PDFOtimizado(FPDF):
    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=15)
    def header(self):
        self.set_font('Arial','B',14)
        self.cell(0,10,self._encode_text("Relatório PlagIA Professional - PEAS.Co"),ln=True,align='C')
        self.ln(3)
    def footer(self):
        self.set_y(-15)
        self.set_font('Arial','I',8)
        self.cell(0,10,f'Página {self.page_no()}',0,0,'C')
    def add_section(self,title: str,content: str):
        if title:
            self.set_font('Arial','B',12)
            self.cell(0,8,self._encode_text(title),ln=True)
        self.set_font('Arial','',10)
        self.multi_cell(0,6,self._encode_text(content))
        self.ln(3)
    def _encode_text(self,text:str)->str:
        try:
            return str(text).encode('latin-1','replace').decode('latin-1')
        except:
            return ''.join(c if ord(c)<128 else '?' for c in str(text))

def gerar_relatorio_otimizado(referencias_sim: List, nome: str, email: str, codigo: str) -> Optional[str]:
    try:
        pdf = PDFOtimizado()
        pdf.add_page()
        dt = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        pdf.add_section("Dados do Solicitante",f"Nome: {nome}\nE-mail: {email}\nData: {dt}\nCódigo: {codigo}")
        if referencias_sim:
            total = len(referencias_sim)
            max_s = max(r[1] for r in referencias_sim)*100
            med_s = np.mean([r[1] for r in referencias_sim])*100
            stats = f"Total de Referências: {total}\nSimilaridade Máxima: {max_s:.2f}%\nSimilaridade Média: {med_s:.2f}%"
            pdf.add_section("Estatísticas",stats)
            pdf.add_section("Top 10 Referências com Links","")
            for i,(t,s,link,doi,ano) in enumerate(referencias_sim[:10],1):
                ref_txt = f"{i}. {t}\nAno: {ano or 'N/A'}\nLink: {link or doi or 'N/A'}\nSimilaridade: {s*100:.2f}%"
                pdf.add_section("",ref_txt)
        else:
            pdf.add_section("Resultado","Nenhuma referência encontrada.")
        path = "/tmp/relatorio_plagia_otimizado.pdf"
        pdf.output(path,'F')
        return path
    except Exception as e:
        logger.error(f"Erro gerar PDF: {e}")
        return None

# =============================
# Visualizações e Métricas
# =============================
@st.cache_data(ttl=CONFIG['CACHE_TTL'])
def criar_grafico_barras_otimizado(referencias_sim: List) -> Optional[go.Figure]:
    if not referencias_sim: return None
    refs = referencias_sim[:10]
    tit = [r[0][:40]+"..." if len(r[0])>40 else r[0] for r in refs]
    sim = [r[1]*100 for r in refs]
    fig = go.Figure(data=[go.Bar(x=sim,y=tit,orientation='h',marker=dict(color=sim,colorscale='RdYlBu_r',showscale=True))])
    fig.update_layout(title="Top 10 Referências por Similaridade",xaxis_title="Similaridade (%)",height=400,template="plotly_white",margin=dict(l=20,r=20,t=40,b=20))
    return fig

def exibir_metricas_otimizadas(referencias_sim: List):
    if not referencias_sim:
        st.warning("Nenhuma referência encontrada para análise.")
        return
    sims = [r[1] for r in referencias_sim]
    col1,col2,col3,col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-value">{len(sims)}</div>
            <div class="metric-label">Total Referências</div>
        </div>
        """,unsafe_allow_html=True)
    with col2:
        max_s = max(sims)*100
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-value">{max_s:.1f}%</div>
            <div class="metric-label">Máxima</div>
        </div>
        """,unsafe_allow_html=True)
    with col3:
        avg = np.mean(sims)*100
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-value">{avg:.1f}%</div>
            <div class="metric-label">Média</div>
        </div>
        """,unsafe_allow_html=True)
    with col4:
        alt = len([s for s in sims if s>0.3])
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-value">{alt}</div>
            <div class="metric-label">Alta Similaridade</div>
        </div>
        """,unsafe_allow_html=True)

# =============================
# Função Principal (Interface)
# =============================

def main():
    st.markdown(load_optimized_css(),unsafe_allow_html=True)
    st.markdown("""
    <div class="hero-header">
        <h1 style="font-size:2.5rem;margin-bottom:0.5rem;">🔍 PlagIA Professional</h1>
        <p style="font-size:1rem;margin:0;">Sistema Otimizado de Detecção de Plágio</p>
    </div>
    """,unsafe_allow_html=True)

    # Estado da sessão
    if "consultas" not in st.session_state:
        st.session_state["consultas"] = 0
    if "historico" not in st.session_state:
        st.session_state["historico"] = []

    # Sidebar
    with st.sidebar:
        st.markdown("""
        <div class="sidebar-modern">
            <h3>📊 Painel de Controle</h3>
        </div>
        """,unsafe_allow_html=True)
        rest = CONFIG['MAX_CONSULTAS_SESSAO'] - st.session_state["consultas"]
        cls = "limit-reached" if rest<=0 else ""
        st.markdown(f"""
        <div class="usage-counter {cls}">
            <h4>Consultas Restantes</h4>
            <h2>{rest}/{CONFIG['MAX_CONSULTAS_SESSAO']}</h2>
        </div>
        """,unsafe_allow_html=True)
        if st.session_state["historico"]:
            st.markdown("### 📋 Histórico")
            for i in st.session_state["historico"][-3:]:
                st.markdown(f"**{i['nome'][:20]}...** - {i['timestamp']}")

    # Layout
    col1,col2 = st.columns([2,1])
    with col1:
        st.markdown("""<div class="glass-card"><h3>📝 Registro do Usuário</h3></div>""",unsafe_allow_html=True)
        nome = st.text_input("Nome completo",placeholder="Digite seu nome completo")
        email = st.text_input("E-mail",placeholder="Digite seu e-mail")
        st.markdown("""<div class="glass-card"><h3>📄 Upload do Documento</h3></div>""",unsafe_allow_html=True)
        arquivo_pdf = st.file_uploader("Envie o artigo em PDF",type=["pdf"] )
        if st.checkbox("Usar PDF de Teste (apenas desenvolvimento)"):
            with open("/home/ubuntu/teste_curto.pdf","rb") as f:
                arquivo_pdf = BytesIO(f.read()); arquivo_pdf.name="teste_curto.pdf"
                st.info("PDF de teste carregado")
        processar = st.button("🚀 Analisar Documento",disabled=(rest<=0))
    with col2:
        st.markdown("""<div class="glass-card"><h3>ℹ️ Sistema</h3><p><strong>Versão:</strong> Otimizada 2.1</p><p><strong>Cache:</strong> Ativo</p></div>""",unsafe_allow_html=True)
        st.markdown(f"""<div class="recommendation-box"><h4>📋 Requisitos</h4><ul><li>Mínimo {CONFIG['MIN_TEXT_LENGTH']} caracteres</li><li>Mínimo {CONFIG['MIN_WORDS']} palavras</li><li>PDF com texto selecionável</li></ul></div>""",unsafe_allow_html=True)

    # Processar
    if processar:
        if not nome or not email:
            st.error("⚠️ Preencha nome e e-mail.")
            return
        if not arquivo_pdf:
            st.error("⚠️ Envie um PDF.")
            return
        if rest<=0:
            st.error("❌ Limite atingido.")
            return
        prog = st.container()
        with prog:
            bar = st.progress(0); stat = st.empty()
            try:
                stat.text("🔄 Extraindo texto..."); bar.progress(20)
                texto = extrair_texto_pdf_otimizado(arquivo_pdf)
                if not texto:
                    st.error("❌ Falha na extração."); return
                stat.text("🔍 Validando..."); bar.progress(30)
                ok,msg = validar_texto_robusto(texto)
                if not ok: st.error(f"❌ {msg}"); return
                stat.text("🧹 Limpando..."); bar.progress(40)
                clean = limpar_texto_otimizado(texto)
                ok2,msg2 = validar_texto_robusto(clean)
                if not ok2: st.error(f"❌ {msg2}"); return
                stat.text("🔎 Buscando referências..."); bar.progress(60)
                refs = buscar_referencias_crossref_otimizado(clean)
                if not refs:
                    st.warning("⚠️ Nenhuma referência encontrada."); bar.progress(100); st.session_state["consultas"]+=1; return
                stat.text("📊 Calculando similaridades..."); bar.progress(80)
                sim_list=[]
                for r in refs[:CONFIG['MAX_REFS']]:
                    base = f"{r['titulo']} {r['resumo']}"
                    s = calcular_similaridade_otimizada(clean, base)
                    sim_list.append((r['titulo'],s,r['link'],r['doi'],r['ano']))
                sim_list.sort(key=lambda x:x[1],reverse=True)
                stat.text("✅ Gerando resultados..."); bar.progress(90)
                code = gerar_codigo_verificacao(clean)
                salvar_email_google_sheets_otimizado(nome,email,code)
                st.session_state['historico'].append({'nome':nome,'timestamp':datetime.now().strftime('%H:%M'),'codigo':code})
                bar.progress(100); time.sleep(0.5)
                prog.empty()
                st.success(f"✅ Concluído! Código: **{code}**")
                st.markdown("### 📊 Resultados")
                exibir_metricas_otimizadas(sim_list)
                if sim_list:
                    with st.expander("📈 Visualização Detalhada",expanded=False):
                        fig = criar_grafico_barras_otimizado(sim_list)
                        if fig: st.plotly_chart(fig,use_container_width=True)
                if sim_list:
                    st.markdown("### 📋 Top 10 Referências")
                    import pandas as pd
                    df = pd.DataFrame([{"#":i+1,"Título":ref[0][:60]+("..." if len(ref[0])>60 else ""),"Similaridade":f"{ref[1]*100:.1f}%","Ano":(ref[4] or 'N/A')} for i,ref in enumerate(sim_list[:10])])
                    st.dataframe(df,use_container_width=True,hide_index=True)
                # Download do PDF
                pdf_p = gerar_relatorio_otimizado(sim_list,nome,email,code)
                if pdf_p:
                    with open(pdf_p,'rb') as f:
                        st.download_button("📄 Baixar Relatório PDF",f,"relatorio_plagia_otimizado.pdf","application/pdf")
                st.session_state['consultas']+=1
                gc.collect()
            except Exception as e:
                logger.error(f"Erro no processamento: {e}")
                st.error(f"❌ Erro: {e}")
                prog.empty()

    # Verificação de código
    st.markdown("---")
    st.markdown("### 🔍 Verificar Código")
    c1,c2 = st.columns([3,1])
    with c1:
        code_in = st.text_input("Código de verificação",placeholder="Ex: A1B2C3D4E5")
    with c2:
        btn_v = st.button("🔍 Verificar")
    if btn_v and code_in:
        with st.spinner("Verificando..."):
            if verificar_codigo_google_sheets_otimizado(code_in): st.success("✅ Documento autêntico!")
            else: st.error("❌ Código inválido.")

    # Seção PIX
   # QR Code para contribuição PIX
            pix_key = "pesas8810@gmail.com"
            qr_img = qrcode.make(f"pix:{pix_key}")
            buf_qr = BytesIO()
            qr_img.save(buf_qr, format="PNG")
            st.image(buf_qr.getvalue(), caption="💚 Apoie o Projeto via Pix", width=150)
            st.markdown(f"**Chave Pix:** {pix_key}")


if __name__ == "__main__":
    main()

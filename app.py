"""
TotalIA - Detecção Avançada de Texto Gerado por IA
Versão Melhorada com Algoritmos Otimizados
"""

import re
import numpy as np
import pdfplumber
from fpdf import FPDF
import torch
import streamlit as st
import io
import requests
from datetime import datetime
from collections import Counter
from typing import Dict, List, Tuple, Optional
import logging
from functools import lru_cache
import hashlib
import warnings

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Suprimir warnings desnecessários
warnings.filterwarnings("ignore", category=FutureWarning)

# Configurações
CONFIG = {
    'MIN_TEXT_LENGTH': 100,
    'MAX_TEXT_LENGTH': 50000,
    'CHUNK_SIZE': 5000,
    'CONFIDENCE_THRESHOLD': 0.7,
    'GOOGLE_SHEETS_URL': "https://script.google.com/macros/s/AKfycbyTpbWDxWkNRh_ZIlHuAVwZaCC2ODqTmo0Un7ZDbgzrVQBmxlYYKuoYf6yDigAPHZiZ/exec"
}

class TextValidator:
    """Classe para validação e pré-processamento de texto"""
    
    @staticmethod
    def validate_text(text: str) -> Tuple[bool, str]:
        """Valida se o texto é adequado para análise"""
        if not text or not text.strip():
            return False, "Texto vazio ou inválido"
        
        clean_text = text.strip()
        if len(clean_text) < CONFIG['MIN_TEXT_LENGTH']:
            return False, f"Texto muito curto. Mínimo: {CONFIG['MIN_TEXT_LENGTH']} caracteres"
        
        if len(clean_text) > CONFIG['MAX_TEXT_LENGTH']:
            return False, f"Texto muito longo. Máximo: {CONFIG['MAX_TEXT_LENGTH']} caracteres"
        
        return True, "Texto válido"
    
    @staticmethod
    def preprocess_text(text: str, preserve_structure: bool = True) -> str:
        """Pré-processa texto preservando características importantes"""
        if preserve_structure:
            # Preserva pontuação e estrutura para análise mais precisa
            text = re.sub(r'\s+', ' ', text)  # Normaliza espaços
            text = text.strip()
        else:
            # Limpeza mais agressiva quando necessário
            text = text.lower()
            text = re.sub(r'[^a-zA-Z0-9\s]', '', text)
            text = re.sub(r'\s+', ' ', text).strip()
        
        return text

class AdvancedMetrics:
    """Classe com métricas avançadas para detecção de IA"""
    
    @staticmethod
    def calculate_word_entropy(text: str) -> float:
        """Calcula entropia baseada em palavras (mais preciso que caracteres)"""
        words = text.lower().split()
        if len(words) < 10:
            return 0.0
        
        word_freq = Counter(words)
        total_words = len(words)
        
        entropy = -sum((freq/total_words) * np.log2(freq/total_words) 
                      for freq in word_freq.values())
        return entropy
    
    @staticmethod
    def calculate_lexical_diversity(text: str) -> float:
        """Calcula Type-Token Ratio (diversidade lexical)"""
        words = text.lower().split()
        if len(words) < 10:
            return 0.0
        
        unique_words = len(set(words))
        total_words = len(words)
        return unique_words / total_words
    
    @staticmethod
    def detect_repetition_patterns(text: str) -> float:
        """Detecta padrões repetitivos comuns em texto gerado por IA"""
        sentences = re.split(r'[.!?]+', text)
        if len(sentences) < 3:
            return 0.0
        
        # Detecta frases muito similares
        similarity_scores = []
        for i in range(len(sentences)-1):
            for j in range(i+1, len(sentences)):
                s1_words = set(sentences[i].lower().split())
                s2_words = set(sentences[j].lower().split())
                if len(s1_words) > 0 and len(s2_words) > 0:
                    similarity = len(s1_words & s2_words) / len(s1_words | s2_words)
                    similarity_scores.append(similarity)
        
        return np.mean(similarity_scores) if similarity_scores else 0.0
    
    @staticmethod
    def analyze_sentence_complexity(text: str) -> float:
        """Analisa complexidade das frases"""
        sentences = re.split(r'[.!?]+', text)
        if not sentences:
            return 0.0
        
        complexities = []
        for sentence in sentences:
            words = sentence.split()
            if len(words) > 0:
                # Métricas simples de complexidade
                avg_word_length = np.mean([len(word) for word in words])
                sentence_length = len(words)
                complexity = (avg_word_length * sentence_length) / 100
                complexities.append(complexity)
        
        return np.mean(complexities) if complexities else 0.0
    
    @staticmethod
    def detect_ai_patterns(text: str) -> float:
        """Detecta padrões linguísticos típicos de IA"""
        ai_indicators = [
            r'\b(além disso|portanto|consequentemente|dessa forma|por outro lado)\b',
            r'\b(é importante notar|vale ressaltar|cabe destacar)\b',
            r'\b(em resumo|em conclusão|para concluir)\b',
            r'\b(de acordo com|segundo|conforme)\b'
        ]
        
        text_lower = text.lower()
        total_indicators = 0
        words = len(text.split())
        
        for pattern in ai_indicators:
            matches = len(re.findall(pattern, text_lower))
            total_indicators += matches
        
        # Normaliza pela quantidade de palavras
        return (total_indicators / words) * 1000 if words > 0 else 0.0

class AIDetector:
    """Detector principal de IA com múltiplas métricas"""
    
    def __init__(self):
        self.metrics = AdvancedMetrics()
        self.validator = TextValidator()
    
    @lru_cache(maxsize=100)
    def _get_text_hash(self, text: str) -> str:
        """Gera hash do texto para cache"""
        return hashlib.md5(text.encode()).hexdigest()
    
    def analyze_text(self, text: str) -> Dict[str, float]:
        """Análise completa do texto com múltiplas métricas"""
        # Validação
        is_valid, message = self.validator.validate_text(text)
        if not is_valid:
            raise ValueError(message)
        
        # Pré-processamento
        clean_text = self.validator.preprocess_text(text, preserve_structure=True)
        
        # Cálculo das métricas
        metrics = {
            'word_entropy': self.metrics.calculate_word_entropy(clean_text),
            'lexical_diversity': self.metrics.calculate_lexical_diversity(clean_text),
            'repetition_score': self.metrics.detect_repetition_patterns(clean_text),
            'complexity_score': self.metrics.analyze_sentence_complexity(clean_text),
            'ai_patterns': self.metrics.detect_ai_patterns(clean_text)
        }
        
        # Cálculo do score final usando ensemble
        final_score = self._calculate_ensemble_score(metrics)
        confidence = self._calculate_confidence(metrics)
        
        return {
            'ai_probability': final_score,
            'confidence': confidence,
            'metrics': metrics,
            'interpretation': self._interpret_score(final_score, confidence)
        }
    
    def _calculate_ensemble_score(self, metrics: Dict[str, float]) -> float:
        """Calcula score final usando ensemble de métricas"""
        # Pesos baseados em importância empírica
        weights = {
            'word_entropy': 0.25,
            'lexical_diversity': 0.20,
            'repetition_score': 0.25,
            'complexity_score': 0.15,
            'ai_patterns': 0.15
        }
        
        # Normalização das métricas
        normalized_metrics = {
            'word_entropy': min(metrics['word_entropy'] / 10, 1.0),  # Normaliza entropia
            'lexical_diversity': 1.0 - metrics['lexical_diversity'],  # Inverte (baixa diversidade = mais IA)
            'repetition_score': metrics['repetition_score'],
            'complexity_score': min(metrics['complexity_score'] / 5, 1.0),
            'ai_patterns': min(metrics['ai_patterns'] / 10, 1.0)
        }
        
        # Cálculo weighted
        score = sum(normalized_metrics[key] * weights[key] for key in weights.keys())
        return min(score * 100, 100.0)  # Converte para porcentagem
    
    def _calculate_confidence(self, metrics: Dict[str, float]) -> float:
        """Calcula nível de confiança da predição"""
        # Confiança baseada na consistência das métricas
        values = list(metrics.values())
        std_dev = np.std(values)
        mean_val = np.mean(values)
        
        # Confiança inversamente proporcional ao desvio padrão
        confidence = max(0.5, 1.0 - (std_dev / (mean_val + 0.1)))
        return min(confidence * 100, 100.0)
    
    def _interpret_score(self, score: float, confidence: float) -> str:
        """Interpreta o score e fornece explicação"""
        if confidence < 50:
            return "Análise inconclusiva - texto pode ser ambíguo"
        elif score < 30:
            return "Baixa probabilidade de IA - provavelmente texto humano"
        elif score < 60:
            return "Probabilidade moderada de IA - análise adicional recomendada"
        else:
            return "Alta probabilidade de IA - muito provável que seja gerado por IA"

# =============================
# Funções de Interface e Utilidades
# =============================

def salvar_email_google_sheets(nome: str, email: str, codigo: str = "N/A") -> None:
    """Salva dados do usuário no Google Sheets com tratamento de erro melhorado"""
    dados = {"nome": nome, "email": email, "codigo": codigo}
    try:
        headers = {'Content-Type': 'application/json'}
        response = requests.post(CONFIG['GOOGLE_SHEETS_URL'], json=dados, headers=headers, timeout=10)
        
        if response.status_code == 200 and response.text.strip() == "Sucesso":
            st.success("✅ Seus dados foram registrados com sucesso!")
        else:
            st.error(f"❌ Falha ao salvar: {response.text}")
            logger.error(f"Erro Google Sheets: {response.status_code} - {response.text}")
    except requests.exceptions.Timeout:
        st.error("❌ Timeout na conexão com Google Sheets")
    except Exception as e:
        st.error(f"❌ Erro na conexão: {str(e)}")
        logger.error(f"Erro Google Sheets: {e}")

def extract_text_from_pdf(pdf_file) -> str:
    """Extrai texto de PDF com tratamento de erro melhorado"""
    try:
        text = ""
        with pdfplumber.open(io.BytesIO(pdf_file.read())) as pdf:
            for page_num, page in enumerate(pdf.pages):
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
                
                # Limite de páginas para evitar textos muito longos
                if len(text) > CONFIG['MAX_TEXT_LENGTH']:
                    st.warning(f"⚠️ Texto muito longo. Analisando apenas as primeiras {page_num + 1} páginas.")
                    break
        
        return text
    except Exception as e:
        st.error(f"❌ Erro ao extrair texto do PDF: {str(e)}")
        return ""

class ImprovedPDFReport(FPDF):
    """Classe melhorada para geração de relatórios PDF"""
    
    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=15)
    
    def _encode(self, txt: str) -> str:
        """Codificação melhorada para caracteres especiais"""
        txt = txt.replace('–', '-').replace('—', '-').replace('"', '"').replace('"', '"')
        try:
            return txt.encode('latin-1', 'replace').decode('latin-1')
        except Exception:
            return ''.join(c if ord(c) < 256 else '?' for c in txt)
    
    def header(self):
        """Cabeçalho do relatório"""
        self.set_font('Arial', 'B', 16)
        self.cell(0, 10, self._encode('Relatório TotalIA - Análise Avançada'), ln=True, align='C')
        self.ln(5)
    
    def add_analysis_results(self, results: Dict):
        """Adiciona resultados da análise ao PDF"""
        self.set_font('Arial', 'B', 14)
        self.cell(0, 10, self._encode('Resultados da Análise'), ln=True)
        self.ln(5)
        
        self.set_font('Arial', '', 12)
        
        # Resultado principal
        self.cell(0, 8, self._encode(f"Probabilidade de IA: {results['ai_probability']:.1f}%"), ln=True)
        self.cell(0, 8, self._encode(f"Nível de Confiança: {results['confidence']:.1f}%"), ln=True)
        self.cell(0, 8, self._encode(f"Interpretação: {results['interpretation']}"), ln=True)
        self.ln(5)
        
        # Métricas detalhadas
        self.set_font('Arial', 'B', 12)
        self.cell(0, 8, self._encode('Métricas Detalhadas:'), ln=True)
        self.set_font('Arial', '', 10)
        
        metrics = results['metrics']
        self.cell(0, 6, self._encode(f"• Entropia de Palavras: {metrics['word_entropy']:.2f}"), ln=True)
        self.cell(0, 6, self._encode(f"• Diversidade Lexical: {metrics['lexical_diversity']:.2f}"), ln=True)
        self.cell(0, 6, self._encode(f"• Padrões Repetitivos: {metrics['repetition_score']:.2f}"), ln=True)
        self.cell(0, 6, self._encode(f"• Complexidade: {metrics['complexity_score']:.2f}"), ln=True)
        self.cell(0, 6, self._encode(f"• Padrões de IA: {metrics['ai_patterns']:.2f}"), ln=True)

def generate_improved_pdf_report(results: Dict) -> str:
    """Gera relatório PDF melhorado"""
    pdf = ImprovedPDFReport()
    pdf.add_page()
    
    # Introdução
    intro = ('Este relatório apresenta uma análise avançada usando múltiplas métricas '
             'para determinar a probabilidade de o texto ter sido gerado por IA.')
    pdf.set_font('Arial', '', 12)
    pdf.multi_cell(0, 8, pdf._encode(intro))
    pdf.ln(5)
    
    # Resultados
    pdf.add_analysis_results(results)
    
    # Explicação das métricas
    pdf.ln(10)
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, pdf._encode('Explicação das Métricas'), ln=True)
    pdf.ln(2)
    
    explanation = (
        "Entropia de Palavras: Mede a diversidade vocabular. Valores baixos indicam repetitividade.\n\n"
        "Diversidade Lexical: Razão entre palavras únicas e total. IA tende a ter menor diversidade.\n\n"
        "Padrões Repetitivos: Detecta frases similares. IA frequentemente repete estruturas.\n\n"
        "Complexidade: Analisa estrutura das frases. IA pode ter padrões previsíveis.\n\n"
        "Padrões de IA: Detecta expressões típicas de texto gerado por IA.\n\n"
        "Interpretação dos Resultados:\n"
        "0-30%: Baixa probabilidade de IA\n"
        "30-60%: Probabilidade moderada\n"
        "60-100%: Alta probabilidade de IA"
    )
    
    pdf.set_font('Arial', '', 10)
    pdf.multi_cell(0, 6, pdf._encode(explanation))
    
    filename = "relatorio_ia_avancado.pdf"
    pdf.output(filename, 'F')
    return filename

# =============================
# Interface Streamlit Melhorada
# =============================

def main():
    """Função principal da aplicação"""
    st.set_page_config(
        page_title="TotalIA - Detecção Avançada de IA",
        page_icon="🔍",
        layout="wide"
    )
    
    st.title("🔍 TotalIA - Detecção Avançada de Texto Gerado por IA")
    st.markdown("### Análise com Múltiplas Métricas e Algoritmos Otimizados")
    
    # Inicializar detector
    detector = AIDetector()
    
    # Sidebar com informações
    with st.sidebar:
        st.header("ℹ️ Sobre a Análise")
        st.markdown("""
        **Métricas Utilizadas:**
        - Entropia de palavras
        - Diversidade lexical
        - Padrões repetitivos
        - Complexidade sintática
        - Detecção de padrões de IA
        
        **Melhorias Implementadas:**
        - Algoritmo ensemble
        - Validação robusta
        - Métricas avançadas
        - Análise de confiança
        """)
    
    # Opções de entrada
    input_method = st.radio(
        "Escolha o método de entrada:",
        ["Upload de PDF", "Texto Direto"]
    )
    
    texto_para_analise = ""
    
    if input_method == "Upload de PDF":
        uploaded_file = st.file_uploader("Escolha um arquivo PDF", type="pdf")
        if uploaded_file:
            with st.spinner("Extraindo texto do PDF..."):
                texto_para_analise = extract_text_from_pdf(uploaded_file)
                if texto_para_analise:
                    st.success(f"✅ Texto extraído: {len(texto_para_analise)} caracteres")
                    with st.expander("Visualizar texto extraído"):
                        st.text_area("Texto:", texto_para_analise[:1000] + "..." if len(texto_para_analise) > 1000 else texto_para_analise, height=200)
    
    else:
        texto_para_analise = st.text_area(
            "Cole o texto para análise:",
            height=200,
            placeholder="Cole aqui o texto que deseja analisar..."
        )
    
    # Análise
    if texto_para_analise and st.button("🔍 Analisar Texto", type="primary"):
        try:
            with st.spinner("Analisando texto com algoritmos avançados..."):
                resultados = detector.analyze_text(texto_para_analise)
            
            # Exibir resultados
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("📊 Resultado Principal")
                
                # Gauge visual para probabilidade
                prob = resultados['ai_probability']
                confidence = resultados['confidence']
                
                if prob < 30:
                    color = "green"
                elif prob < 60:
                    color = "orange"
                else:
                    color = "red"
                
                st.markdown(f"""
                <div style="text-align: center; padding: 20px; border: 2px solid {color}; border-radius: 10px;">
                    <h2 style="color: {color};">Probabilidade de IA: {prob:.1f}%</h2>
                    <p><strong>Confiança:</strong> {confidence:.1f}%</p>
                    <p><em>{resultados['interpretation']}</em></p>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.subheader("📈 Métricas Detalhadas")
                metrics = resultados['metrics']
                
                for metric_name, value in metrics.items():
                    metric_display = metric_name.replace('_', ' ').title()
                    st.metric(metric_display, f"{value:.2f}")
            
            # Gerar relatório PDF
            st.subheader("📄 Relatório Detalhado")
            report_path = generate_improved_pdf_report(resultados)
            
            with open(report_path, "rb") as f:
                st.download_button(
                    "📥 Baixar Relatório Completo (PDF)",
                    f.read(),
                    "relatorio_ia_avancado.pdf",
                    "application/pdf",
                    key="download_report"
                )
            
        except ValueError as e:
            st.error(f"❌ Erro de validação: {str(e)}")
        except Exception as e:
            st.error(f"❌ Erro na análise: {str(e)}")
            logger.error(f"Erro na análise: {e}")
    
    # Registro de usuário
    st.markdown("---")
    st.subheader("📋 Registro de Usuário")
    
    col1, col2 = st.columns(2)
    with col1:
        nome = st.text_input("Nome completo")
    with col2:
        email = st.text_input("E-mail")
    
    if st.button("Registrar dados"):
        if nome and email:
            salvar_email_google_sheets(nome, email)
        else:
            st.warning("⚠️ Preencha todos os campos.")
    
    # Seção de apoio (simplificada)
    st.markdown("---")
    st.markdown("### 💚 Apoie Este Projeto")
    st.info("Se esta ferramenta foi útil, considere apoiar o desenvolvimento!")

if __name__ == "__main__":
    main()

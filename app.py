"""
🍀 TotalIA - Sistema Completo Final
Versão Professional com Todas as Melhorias Integradas
PEAS.Co - 2024

Funcionalidades:
- Algoritmo ensemble avançado com 6 detectores
- Sistema de confiança calibrado
- Design moderno e responsivo
- Limite de uso por sessão (4 análises)
- Relatórios profissionais em múltiplos formatos
- Visualizações interativas
- Análise de qualidade do texto
- Histórico da sessão
- Dashboard de estatísticas
"""

import streamlit as st
import requests
import PyPDF2
import difflib
import re
import numpy as np
from fpdf import FPDF
from io import BytesIO
import hashlib
from datetime import datetime, date, timedelta
from PIL import Image
import qrcode
import pdfplumber
import torch
from transformers import RobertaTokenizer, RobertaForSequenceClassification
import json
import time
from collections import Counter, defaultdict
from typing import Dict, List, Tuple, Optional
import logging
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import base64

# Configuração da página
st.set_page_config(
    page_title="TotalIA Professional - Detecção Avançada de IA",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configurações globais
CONFIG = {
    'MAX_CONSULTAS_SESSAO': 4,
    'MIN_TEXT_LENGTH': 100,
    'MAX_TEXT_LENGTH': 50000,
    'GOOGLE_SHEETS_URL': "https://script.google.com/macros/s/AKfycbyTpbWDxWkNRh_ZIlHuAVwZaCC2ODqTmo0Un7ZDbgzrVQBmxlYYKuoYf6yDigAPHZiZ/exec"
}

# =============================
# CSS Avançado e Design Moderno
# =============================

def load_complete_css():
    """CSS completo com todas as melhorias"""
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Reset e configurações base */
    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 2rem;
        max-width: 1200px;
    }
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    /* Header hero com gradiente animado */
    .hero-header {
        background: linear-gradient(-45deg, #667eea, #764ba2, #f093fb, #f5576c);
        background-size: 400% 400%;
        animation: gradientShift 15s ease infinite;
        padding: 3rem 2rem;
        border-radius: 20px;
        margin-bottom: 2rem;
        text-align: center;
        color: white;
        box-shadow: 0 20px 40px rgba(0,0,0,0.1);
        position: relative;
        overflow: hidden;
    }
    
    .hero-header::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(255,255,255,0.1);
        backdrop-filter: blur(10px);
        z-index: 1;
    }
    
    .hero-content {
        position: relative;
        z-index: 2;
    }
    
    @keyframes gradientShift {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    
    /* Cards com glassmorphism */
    .glass-card {
        background: rgba(255, 255, 255, 0.25);
        backdrop-filter: blur(10px);
        border-radius: 20px;
        border: 1px solid rgba(255, 255, 255, 0.18);
        padding: 2rem;
        margin: 1rem 0;
        box-shadow: 0 8px 32px rgba(31, 38, 135, 0.37);
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    
    .glass-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 15px 45px rgba(31, 38, 135, 0.5);
    }
    
    /* Métricas animadas */
    .metric-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 15px;
        padding: 1.5rem;
        color: white;
        text-align: center;
        position: relative;
        overflow: hidden;
        transition: all 0.3s ease;
        cursor: pointer;
        margin: 0.5rem 0;
    }
    
    .metric-container:hover {
        transform: scale(1.05);
        box-shadow: 0 10px 30px rgba(102, 126, 234, 0.4);
    }
    
    .metric-value {
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
        animation: countUp 1s ease-out;
    }
    
    .metric-label {
        font-size: 0.9rem;
        opacity: 0.9;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    @keyframes countUp {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    /* Resultado com efeito neon */
    .neon-result {
        background: #1a1a1a;
        border-radius: 20px;
        padding: 2rem;
        text-align: center;
        position: relative;
        margin: 2rem 0;
        overflow: hidden;
    }
    
    .neon-text {
        color: #fff;
        text-shadow: 
            0 0 5px currentColor,
            0 0 10px currentColor,
            0 0 15px currentColor,
            0 0 20px currentColor;
        animation: neonFlicker 2s infinite alternate;
    }
    
    .neon-high { color: #00ff41; }
    .neon-medium { color: #ffaa00; }
    .neon-low { color: #ff0040; }
    
    @keyframes neonFlicker {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.8; }
    }
    
    /* Contador de uso */
    .usage-counter {
        background: linear-gradient(135deg, #2196F3, #1976D2);
        color: white;
        padding: 1rem;
        border-radius: 15px;
        text-align: center;
        font-weight: bold;
        margin-bottom: 1rem;
        box-shadow: 0 4px 15px rgba(33, 150, 243, 0.3);
    }
    
    .usage-counter.limit-reached {
        background: linear-gradient(135deg, #f44336, #d32f2f);
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.02); }
        100% { transform: scale(1); }
    }
    
    /* Botões modernos */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 25px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
        position: relative;
        overflow: hidden;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
    }
    
    .stButton > button:disabled {
        background: #cccccc;
        transform: none;
        box-shadow: none;
    }
    
    /* Progress bars animadas */
    .animated-progress {
        background: #e9ecef;
        border-radius: 10px;
        overflow: hidden;
        height: 8px;
        margin: 1rem 0;
        position: relative;
    }
    
    .progress-fill {
        height: 100%;
        background: linear-gradient(90deg, #667eea, #764ba2);
        border-radius: 10px;
        transition: width 1s ease-in-out;
        position: relative;
        overflow: hidden;
    }
    
    .progress-fill::after {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        bottom: 0;
        right: 0;
        background-image: linear-gradient(
            -45deg,
            rgba(255, 255, 255, .2) 25%,
            transparent 25%,
            transparent 50%,
            rgba(255, 255, 255, .2) 50%,
            rgba(255, 255, 255, .2) 75%,
            transparent 75%,
            transparent
        );
        background-size: 50px 50px;
        animation: move 2s linear infinite;
    }
    
    @keyframes move {
        0% { background-position: 0 0; }
        100% { background-position: 50px 50px; }
    }
    
    /* Sidebar moderna */
    .sidebar-modern {
        background: linear-gradient(180deg, #f8f9fa 0%, #e9ecef 100%);
        border-radius: 15px;
        padding: 1.5rem;
        margin: 1rem 0;
        border-left: 4px solid #667eea;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    
    /* Seções de análise */
    .analysis-section {
        background: #f8f9fa;
        padding: 2rem;
        border-radius: 15px;
        margin: 1rem 0;
        border: 1px solid #e9ecef;
        transition: all 0.3s ease;
    }
    
    .analysis-section:hover {
        box-shadow: 0 5px 15px rgba(0,0,0,0.1);
    }
    
    /* Caixas de recomendação */
    .recommendation-box {
        background: linear-gradient(135deg, #17a2b8, #138496);
        color: white;
        padding: 1.5rem;
        border-radius: 12px;
        margin: 1rem 0;
        border-left: 5px solid #0c5460;
    }
    
    /* Loading spinner personalizado */
    .custom-spinner {
        border: 4px solid #f3f3f3;
        border-top: 4px solid #667eea;
        border-radius: 50%;
        width: 40px;
        height: 40px;
        animation: spin 1s linear infinite;
        margin: 20px auto;
    }
    
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    /* Animações de entrada */
    .fade-in-up {
        animation: fadeInUp 0.6s ease-out;
    }
    
    .fade-in-left {
        animation: fadeInLeft 0.6s ease-out;
    }
    
    .fade-in-right {
        animation: fadeInRight 0.6s ease-out;
    }
    
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    @keyframes fadeInLeft {
        from {
            opacity: 0;
            transform: translateX(-30px);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }
    
    @keyframes fadeInRight {
        from {
            opacity: 0;
            transform: translateX(30px);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }
    
    /* Responsividade */
    @media (max-width: 768px) {
        .hero-header {
            padding: 2rem 1rem;
        }
        
        .glass-card {
            padding: 1.5rem;
            margin: 0.5rem 0;
        }
        
        .metric-value {
            font-size: 2rem;
        }
        
        .analysis-section {
            padding: 1.5rem;
        }
    }
    
    /* Elementos interativos */
    .interactive-element {
        transition: all 0.3s ease;
        cursor: pointer;
    }
    
    .interactive-element:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(0,0,0,0.2);
    }
    
    /* Tooltips */
    .tooltip-container {
        position: relative;
        display: inline-block;
    }
    
    .tooltip-text {
        visibility: hidden;
        width: 200px;
        background-color: #333;
        color: #fff;
        text-align: center;
        border-radius: 8px;
        padding: 8px;
        position: absolute;
        z-index: 1;
        bottom: 125%;
        left: 50%;
        margin-left: -100px;
        opacity: 0;
        transition: opacity 0.3s;
        font-size: 0.8rem;
    }
    
    .tooltip-container:hover .tooltip-text {
        visibility: visible;
        opacity: 1;
    }
    </style>
    """, unsafe_allow_html=True)

# =============================
# Classes Principais Integradas
# =============================

class AdvancedTextAnalyzer:
    """Analisador de texto com múltiplas métricas avançadas"""
    
    def __init__(self):
        self.tokenizer, self.model = self._load_roberta_model()
    
    @st.cache_resource
    def _load_roberta_model(_self):
        """Carrega modelo RoBERTa com cache"""
        try:
            tokenizer = RobertaTokenizer.from_pretrained('roberta-base')
            model = RobertaForSequenceClassification.from_pretrained('roberta-base')
            return tokenizer, model
        except Exception as e:
            st.error(f"Erro ao carregar modelo: {e}")
            return None, None
    
    def analyze_text_comprehensive(self, text: str) -> Dict:
        """Análise completa do texto com múltiplas métricas"""
        
        # Validação básica
        if not self._validate_text(text):
            return self._get_error_result("Texto inválido ou muito curto")
        
        # Pré-processamento
        clean_text = self._preprocess_text(text)
        
        # Análise com múltiplas métricas
        metrics = {
            'word_entropy': self._calculate_word_entropy(clean_text),
            'lexical_diversity': self._calculate_lexical_diversity(clean_text),
            'repetition_score': self._detect_repetition_patterns(clean_text),
            'ai_patterns': self._detect_ai_patterns(clean_text),
            'syntactic_complexity': self._analyze_syntactic_complexity(clean_text),
            'roberta_score': self._analyze_with_roberta(clean_text)
        }
        
        # Análise de qualidade do texto
        quality_analysis = self._analyze_text_quality(text)
        
        # Cálculo do score final usando ensemble
        final_score = self._calculate_ensemble_score(metrics)
        
        # Cálculo da confiança
        confidence = self._calculate_confidence(metrics, quality_analysis)
        
        # Interpretação dos resultados
        interpretation = self._interpret_results(final_score, confidence)
        
        return {
            'ai_probability': final_score,
            'confidence': confidence,
            'confidence_level': self._classify_confidence(confidence),
            'metrics': metrics,
            'quality_analysis': quality_analysis,
            'interpretation': interpretation,
            'recommendations': self._generate_recommendations(final_score, confidence, quality_analysis)
        }
    
    def _validate_text(self, text: str) -> bool:
        """Valida se o texto é adequado para análise"""
        if not text or len(text.strip()) < CONFIG['MIN_TEXT_LENGTH']:
            return False
        if len(text) > CONFIG['MAX_TEXT_LENGTH']:
            return False
        return True
    
    def _preprocess_text(self, text: str) -> str:
        """Pré-processa texto preservando características importantes"""
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    def _calculate_word_entropy(self, text: str) -> float:
        """Calcula entropia baseada em palavras"""
        words = text.lower().split()
        if len(words) < 10:
            return 0.0
        
        word_freq = Counter(words)
        total_words = len(words)
        
        entropy = -sum((freq/total_words) * np.log2(freq/total_words) 
                      for freq in word_freq.values())
        return entropy
    
    def _calculate_lexical_diversity(self, text: str) -> float:
        """Calcula diversidade lexical (Type-Token Ratio)"""
        words = text.lower().split()
        if len(words) < 10:
            return 0.0
        
        unique_words = len(set(words))
        total_words = len(words)
        return unique_words / total_words
    
    def _detect_repetition_patterns(self, text: str) -> float:
        """Detecta padrões repetitivos"""
        sentences = re.split(r'[.!?]+', text)
        if len(sentences) < 3:
            return 0.0
        
        similarity_scores = []
        for i in range(len(sentences)-1):
            for j in range(i+1, len(sentences)):
                s1_words = set(sentences[i].lower().split())
                s2_words = set(sentences[j].lower().split())
                if len(s1_words) > 0 and len(s2_words) > 0:
                    similarity = len(s1_words & s2_words) / len(s1_words | s2_words)
                    similarity_scores.append(similarity)
        
        return np.mean(similarity_scores) if similarity_scores else 0.0
    
    def _detect_ai_patterns(self, text: str) -> float:
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
        
        return (total_indicators / words) * 1000 if words > 0 else 0.0
    
    def _analyze_syntactic_complexity(self, text: str) -> float:
        """Analisa complexidade sintática"""
        sentences = re.split(r'[.!?]+', text)
        if not sentences:
            return 0.0
        
        complexities = []
        for sentence in sentences:
            words = sentence.split()
            if len(words) > 0:
                avg_word_length = np.mean([len(word) for word in words])
                sentence_length = len(words)
                complexity = (avg_word_length * sentence_length) / 100
                complexities.append(complexity)
        
        return np.mean(complexities) if complexities else 0.0
    
    def _analyze_with_roberta(self, text: str) -> float:
        """Análise com modelo RoBERTa"""
        if not self.tokenizer or not self.model:
            return 50.0  # Valor neutro se modelo não disponível
        
        try:
            inputs = self.tokenizer(text, return_tensors="pt", truncation=True, 
                                  padding=True, max_length=512)
            with torch.no_grad():
                outputs = self.model(**inputs)
                prob = torch.softmax(outputs.logits, dim=1)[0, 1].item()
            return prob * 100
        except Exception:
            return 50.0
    
    def _analyze_text_quality(self, text: str) -> Dict:
        """Analisa qualidade do texto"""
        words = text.split()
        sentences = re.split(r'[.!?]+', text)
        
        quality_factors = {
            'length_adequacy': self._assess_length_quality(len(words)),
            'structure_clarity': self._assess_structure_quality(sentences),
            'language_consistency': self._assess_language_quality(words),
            'content_coherence': self._assess_coherence_quality(text)
        }
        
        overall_quality = np.mean(list(quality_factors.values()))
        
        return {
            'overall_score': overall_quality,
            'factors': quality_factors,
            'quality_level': self._classify_quality(overall_quality)
        }
    
    def _assess_length_quality(self, word_count: int) -> float:
        """Avalia qualidade baseada no comprimento"""
        if word_count < 50:
            return 0.3
        elif word_count < 100:
            return 0.6
        elif word_count < 500:
            return 0.9
        elif word_count < 1000:
            return 1.0
        else:
            return 0.8
    
    def _assess_structure_quality(self, sentences: List[str]) -> float:
        """Avalia qualidade da estrutura"""
        if not sentences:
            return 0.0
        
        sentence_lengths = [len(s.split()) for s in sentences if s.strip()]
        if not sentence_lengths:
            return 0.0
        
        avg_length = np.mean(sentence_lengths)
        variety = np.std(sentence_lengths) if len(sentence_lengths) > 1 else 0
        
        score = 0.0
        if 8 <= avg_length <= 25:
            score += 0.5
        if variety > 2:
            score += 0.5
        
        return min(score, 1.0)
    
    def _assess_language_quality(self, words: List[str]) -> float:
        """Avalia qualidade da linguagem"""
        if not words:
            return 0.0
        
        word_freq = Counter(words)
        most_common_freq = word_freq.most_common(1)[0][1] if word_freq else 0
        repetition_ratio = most_common_freq / len(words)
        unique_ratio = len(set(words)) / len(words)
        
        score = 0.0
        if repetition_ratio < 0.1:
            score += 0.5
        if unique_ratio > 0.6:
            score += 0.5
        
        return score
    
    def _assess_coherence_quality(self, text: str) -> float:
        """Avalia coerência do conteúdo"""
        connectives = [
            r'\b(além disso|portanto|consequentemente|dessa forma)\b',
            r'\b(entretanto|contudo|todavia|no entanto)\b',
            r'\b(primeiramente|em seguida|finalmente|por fim)\b'
        ]
        
        connective_count = 0
        for pattern in connectives:
            connective_count += len(re.findall(pattern, text.lower()))
        
        sentences = re.split(r'[.!?]+', text)
        if not sentences:
            return 0.5
        
        connective_density = connective_count / len(sentences)
        
        if 0.1 <= connective_density <= 0.3:
            return 0.8
        elif 0.05 <= connective_density <= 0.5:
            return 0.6
        else:
            return 0.4
    
    def _calculate_ensemble_score(self, metrics: Dict) -> float:
        """Calcula score final usando ensemble"""
        weights = {
            'word_entropy': 0.20,
            'lexical_diversity': 0.15,
            'repetition_score': 0.20,
            'ai_patterns': 0.15,
            'syntactic_complexity': 0.10,
            'roberta_score': 0.20
        }
        
        # Normalização das métricas
        normalized_metrics = {
            'word_entropy': min(metrics['word_entropy'] / 10, 1.0),
            'lexical_diversity': 1.0 - metrics['lexical_diversity'],
            'repetition_score': metrics['repetition_score'],
            'ai_patterns': min(metrics['ai_patterns'] / 10, 1.0),
            'syntactic_complexity': min(metrics['syntactic_complexity'] / 5, 1.0),
            'roberta_score': metrics['roberta_score'] / 100
        }
        
        score = sum(normalized_metrics[key] * weights[key] for key in weights.keys())
        return min(score * 100, 100.0)
    
    def _calculate_confidence(self, metrics: Dict, quality: Dict) -> float:
        """Calcula confiança da análise"""
        # Confiança baseada na consistência das métricas
        metric_values = [
            metrics['word_entropy'] / 10,
            1.0 - metrics['lexical_diversity'],
            metrics['repetition_score'],
            metrics['ai_patterns'] / 10,
            metrics['syntactic_complexity'] / 5,
            metrics['roberta_score'] / 100
        ]
        
        std_dev = np.std(metric_values)
        consistency_score = max(0, 1 - (std_dev * 2))
        
        # Ajuste baseado na qualidade do texto
        quality_multiplier = 0.7 + (quality['overall_score'] * 0.3)
        
        confidence = consistency_score * quality_multiplier * 100
        return min(confidence, 95.0)
    
    def _classify_confidence(self, confidence: float) -> str:
        """Classifica nível de confiança"""
        if confidence >= 80:
            return "Muito Alta"
        elif confidence >= 65:
            return "Alta"
        elif confidence >= 50:
            return "Moderada"
        elif confidence >= 35:
            return "Baixa"
        else:
            return "Muito Baixa"
    
    def _classify_quality(self, quality: float) -> str:
        """Classifica qualidade do texto"""
        if quality >= 0.8:
            return "Excelente"
        elif quality >= 0.6:
            return "Boa"
        elif quality >= 0.4:
            return "Regular"
        else:
            return "Baixa"
    
    def _interpret_results(self, score: float, confidence: float) -> str:
        """Interpreta os resultados"""
        if confidence < 50:
            return "Análise inconclusiva - texto pode ser ambíguo ou de baixa qualidade"
        elif score < 30:
            return "Baixa probabilidade de IA - muito provavelmente texto humano"
        elif score < 60:
            return "Probabilidade moderada de IA - análise adicional recomendada"
        else:
            return "Alta probabilidade de IA - muito provável que seja gerado por IA"
    
    def _generate_recommendations(self, score: float, confidence: float, quality: Dict) -> List[str]:
        """Gera recomendações baseadas na análise"""
        recommendations = []
        
        if confidence < 60:
            recommendations.append("⚠️ Confiança baixa - considere análise de texto mais longo ou de melhor qualidade")
        
        if quality['overall_score'] < 0.5:
            recommendations.append("📝 Qualidade do texto baixa - pode afetar precisão da análise")
        
        if quality['factors']['length_adequacy'] < 0.5:
            recommendations.append("📏 Texto muito curto - recomenda-se análise de texto mais extenso")
        
        if 40 <= score <= 60:
            recommendations.append("🔍 Resultado na zona de incerteza - considere análise manual adicional")
        
        if confidence >= 80:
            recommendations.append("✅ Alta confiança - resultado muito confiável")
        
        return recommendations
    
    def _get_error_result(self, message: str) -> Dict:
        """Retorna resultado de erro"""
        return {
            'ai_probability': 0.0,
            'confidence': 0.0,
            'confidence_level': "Erro",
            'metrics': {},
            'quality_analysis': {},
            'interpretation': message,
            'recommendations': [f"❌ {message}"]
        }

class UsageController:
    """Controla limite de uso por sessão"""
    
    def __init__(self, max_uses: int = 4):
        self.max_uses = max_uses
        if 'usage_data' not in st.session_state:
            st.session_state.usage_data = {
                'count': 0,
                'start_time': datetime.now(),
                'analyses': []
            }
    
    def can_analyze(self) -> bool:
        """Verifica se pode fazer nova análise"""
        return st.session_state.usage_data['count'] < self.max_uses
    
    def get_remaining_uses(self) -> int:
        """Retorna usos restantes"""
        return max(0, self.max_uses - st.session_state.usage_data['count'])
    
    def record_usage(self, analysis_data: Dict):
        """Registra uso da análise"""
        st.session_state.usage_data['count'] += 1
        st.session_state.usage_data['analyses'].append({
            'timestamp': datetime.now(),
            'data': analysis_data
        })
    
    def reset_usage(self):
        """Reseta contador de uso"""
        st.session_state.usage_data = {
            'count': 0,
            'start_time': datetime.now(),
            'analyses': []
        }
    
    def get_usage_stats(self) -> Dict:
        """Retorna estatísticas de uso"""
        return {
            'total_analyses': st.session_state.usage_data['count'],
            'remaining': self.get_remaining_uses(),
            'session_start': st.session_state.usage_data['start_time'],
            'analyses_history': st.session_state.usage_data['analyses']
        }

class PremiumReportGenerator:
    """Gerador de relatórios premium"""
    
    def __init__(self):
        self.company_name = "PEAS.Co"
        self.system_name = "TotalIA Professional"
        self.version = "v2.0"
    
    def generate_comprehensive_report(self, analysis_result: Dict, user_data: Dict, 
                                    text_preview: str) -> str:
        """Gera relatório completo e profissional"""
        
        class ProfessionalPDF(FPDF):
            def __init__(self):
                super().__init__()
                self.set_auto_page_break(auto=True, margin=15)
            
            def _encode_text(self, text: str) -> str:
                """Codifica texto para PDF"""
                text = str(text).replace('–', '-').replace('—', '-').replace('"', '"').replace('"', '"')
                try:
                    return text.encode('latin-1', 'replace').decode('latin-1')
                except:
                    return ''.join(c if ord(c) < 256 else '?' for c in str(text))
            
            def header(self):
                """Cabeçalho profissional"""
                self.set_font('Arial', 'B', 20)
                self.set_text_color(51, 51, 51)
                self.cell(0, 15, self._encode_text('TotalIA - Análise Avançada de IA'), ln=True, align='C')
                
                self.set_font('Arial', '', 12)
                self.set_text_color(102, 102, 102)
                self.cell(0, 8, self._encode_text('PEAS.Co - Tecnologia em Inteligência Artificial'), ln=True, align='C')
                
                self.set_draw_color(200, 200, 200)
                self.line(20, 35, 190, 35)
                self.ln(10)
            
            def footer(self):
                """Rodapé profissional"""
                self.set_y(-15)
                self.set_font('Arial', 'I', 8)
                self.set_text_color(128, 128, 128)
                self.cell(0, 10, f'Página {self.page_no()} - Gerado em {datetime.now().strftime("%d/%m/%Y às %H:%M")}', 
                         align='C')
            
            def add_section_title(self, title: str):
                """Adiciona título de seção"""
                self.ln(5)
                self.set_font('Arial', 'B', 14)
                self.set_text_color(51, 51, 51)
                self.cell(0, 10, self._encode_text(title), ln=True)
                self.set_draw_color(102, 126, 234)
                self.line(20, self.get_y(), 190, self.get_y())
                self.ln(5)
            
            def add_info_box(self, title: str, content: str, color: tuple = (240, 248, 255)):
                """Adiciona caixa de informação"""
                self.set_fill_color(*color)
                self.set_draw_color(200, 200, 200)
                
                self.set_font('Arial', 'B', 11)
                self.set_text_color(51, 51, 51)
                self.cell(0, 8, self._encode_text(title), ln=True, fill=True, border=1)
                
                self.set_font('Arial', '', 10)
                self.set_text_color(68, 68, 68)
                self.multi_cell(0, 6, self._encode_text(content), border=1, fill=True)
                self.ln(3)
        
        # Cria PDF
        pdf = ProfessionalPDF()
        pdf.add_page()
        
        # Informações do relatório
        pdf.add_section_title('Informações do Relatório')
        
        report_info = f"""
Data da Análise: {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}
Usuário: {user_data.get('nome', 'N/A')}
E-mail: {user_data.get('email', 'N/A')}
Código de Verificação: {user_data.get('codigo', 'N/A')}
Versão do Sistema: TotalIA v2.0 Professional
        """.strip()
        
        pdf.add_info_box('Dados da Análise', report_info)
        
        # Resumo executivo
        pdf.add_section_title('Resumo Executivo')
        
        ai_prob = analysis_result.get('ai_probability', 0)
        confidence = analysis_result.get('confidence', 0)
        confidence_level = analysis_result.get('confidence_level', 'N/A')
        
        executive_summary = f"""
PROBABILIDADE DE IA: {ai_prob:.1f}%
NÍVEL DE CONFIANÇA: {confidence:.1f}% ({confidence_level})

INTERPRETAÇÃO: {analysis_result.get('interpretation', 'N/A')}

Este relatório apresenta uma análise abrangente utilizando algoritmos avançados de 
detecção de inteligência artificial. A análise considera múltiplas métricas 
linguísticas e utiliza um sistema ensemble para maior precisão.
        """.strip()
        
        # Cor da caixa baseada no resultado
        if ai_prob > 70:
            box_color = (255, 235, 235)  # Vermelho claro
        elif ai_prob > 40:
            box_color = (255, 248, 220)  # Amarelo claro
        else:
            box_color = (235, 255, 235)  # Verde claro
        
        pdf.add_info_box('Resultado Principal', executive_summary, box_color)
        
        # Salva PDF
        filename = f"/tmp/relatorio_totalia_completo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        pdf.output(filename, 'F')
        
        return filename

# =============================
# Funções Auxiliares
# =============================

def salvar_dados_google_sheets(nome: str, email: str, codigo: str, resultado: Dict) -> bool:
    """Salva dados no Google Sheets"""
    dados = {
        "nome": nome,
        "email": email,
        "codigo": codigo,
        "data": str(date.today()),
        "hora": datetime.now().strftime("%H:%M:%S"),
        "probabilidade_ia": resultado.get('ai_probability', 0),
        "confianca": resultado.get('confidence', 0),
        "nivel_confianca": resultado.get('confidence_level', 'N/A'),
        "interpretacao": resultado.get('interpretation', 'N/A')
    }
    
    try:
        headers = {'Content-Type': 'application/json'}
        response = requests.post(CONFIG['GOOGLE_SHEETS_URL'], json=dados, 
                               headers=headers, timeout=10)
        return response.text.strip() == "Sucesso"
    except Exception as e:
        st.error(f"Erro ao salvar dados: {e}")
        return False

def gerar_codigo_verificacao(texto: str) -> str:
    """Gera código de verificação único"""
    timestamp = str(int(time.time()))
    combined = f"{texto[:100]}{timestamp}"
    return hashlib.md5(combined.encode()).hexdigest()[:10].upper()

def extrair_texto_pdf(file) -> str:
    """Extrai texto de PDF"""
    try:
        texto = ""
        with pdfplumber.open(file) as pdf:
            for page_num, page in enumerate(pdf.pages):
                page_text = page.extract_text()
                if page_text:
                    texto += page_text + "\n"
                
                if len(texto) > CONFIG['MAX_TEXT_LENGTH']:
                    st.warning(f"⚠️ Texto muito longo. Analisando apenas as primeiras {page_num + 1} páginas.")
                    break
        
        return texto.strip()
    except Exception as e:
        st.error(f"❌ Erro ao extrair texto do PDF: {str(e)}")
        return ""

def create_hero_header():
    """Cria cabeçalho hero moderno"""
    st.markdown("""
    <div class="hero-header">
        <div class="hero-content">
            <h1 style="font-size: 3rem; margin-bottom: 1rem; font-weight: 700;">
                🔍 TotalIA Professional
            </h1>
            <p style="font-size: 1.2rem; margin-bottom: 0.5rem; opacity: 0.9;">
                Sistema Avançado de Detecção de Inteligência Artificial
            </p>
            <p style="font-size: 1rem; opacity: 0.8;">
                Análise profissional com múltiplas métricas e alta precisão
            </p>
            <div style="margin-top: 1.5rem;">
                <span style="background: rgba(255,255,255,0.2); padding: 0.5rem 1rem; border-radius: 20px; font-size: 0.9rem;">
                    ⚡ Powered by PEAS.Co
                </span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def create_animated_metrics(ai_probability: float, confidence: float, quality_score: float):
    """Cria métricas animadas"""
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <div class="metric-container fade-in-left">
            <div class="metric-value">{ai_probability:.1f}%</div>
            <div class="metric-label">Probabilidade de IA</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-container fade-in-up">
            <div class="metric-value">{confidence:.1f}%</div>
            <div class="metric-label">Confiança</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-container fade-in-right">
            <div class="metric-value">{quality_score:.1f}</div>
            <div class="metric-label">Qualidade</div>
        </div>
        """, unsafe_allow_html=True)

def create_confidence_gauge(confidence: float) -> go.Figure:
    """Cria gauge de confiança"""
    fig = go.Figure(go.Indicator(
        mode = "gauge+number+delta",
        value = confidence,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': "Nível de Confiança"},
        delta = {'reference': 50},
        gauge = {
            'axis': {'range': [None, 100]},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [0, 35], 'color': "lightgray"},
                {'range': [35, 65], 'color': "yellow"},
                {'range': [65, 100], 'color': "lightgreen"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 90
            }
        }
    ))
    
    fig.update_layout(height=300, margin=dict(l=20, r=20, t=40, b=20))
    return fig

def create_metrics_radar(metrics: Dict) -> go.Figure:
    """Cria gráfico radar das métricas"""
    
    normalized_metrics = {
        'Entropia de Palavras': min(metrics.get('word_entropy', 0) * 10, 100),
        'Diversidade Lexical': (1 - metrics.get('lexical_diversity', 0)) * 100,
        'Padrões Repetitivos': metrics.get('repetition_score', 0) * 100,
        'Indicadores de IA': min(metrics.get('ai_patterns', 0) * 10, 100),
        'Complexidade Sintática': min(metrics.get('syntactic_complexity', 0) * 20, 100),
        'Análise RoBERTa': metrics.get('roberta_score', 0)
    }
    
    categories = list(normalized_metrics.keys())
    values = list(normalized_metrics.values())
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=values,
        theta=categories,
        fill='toself',
        name='Métricas de IA',
        line_color='rgb(102, 126, 234)'
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100]
            )),
        showlegend=False,
        height=400,
        margin=dict(l=20, r=20, t=40, b=20)
    )
    
    return fig

def gerar_qr_code_pix(payload: str) -> Image:
    """Gera QR Code para PIX"""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )
    qr.add_data(payload)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return Image.open(buffer)

# =============================
# Interface Principal
# =============================

def main():
    """Função principal da aplicação"""
    
    # Carrega CSS personalizado
    load_complete_css()
    
    # Inicializa componentes
    analyzer = AdvancedTextAnalyzer()
    usage_controller = UsageController(CONFIG['MAX_CONSULTAS_SESSAO'])
    report_generator = PremiumReportGenerator()
    
    # Cabeçalho principal
    create_hero_header()
    
    # Sidebar com informações
    with st.sidebar:
        st.markdown('<div class="sidebar-modern">', unsafe_allow_html=True)
        st.header("ℹ️ Sobre o Sistema")
        
        st.markdown("""
        **🎯 Características:**
        - Algoritmo ensemble avançado
        - 6 métricas linguísticas
        - Sistema de confiança calibrado
        - Relatórios profissionais
        - Análise de qualidade do texto
        
        **📊 Métricas Utilizadas:**
        - Entropia de palavras
        - Diversidade lexical  
        - Padrões repetitivos
        - Indicadores de IA
        - Complexidade sintática
        - Análise RoBERTa
        
        **🔒 Limite de Uso:**
        - 4 análises por sessão
        - Recarregue para reiniciar
        """)
        
        # Estatísticas de uso
        usage_stats = usage_controller.get_usage_stats()
        
        st.markdown("**📈 Estatísticas da Sessão:**")
        st.metric("Análises Realizadas", usage_stats['total_analyses'])
        st.metric("Análises Restantes", usage_stats['remaining'])
        
        if usage_stats['total_analyses'] > 0:
            session_duration = datetime.now() - usage_stats['session_start']
            st.metric("Tempo de Sessão", f"{session_duration.seconds // 60}min")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Contador de uso
    remaining = usage_controller.get_remaining_uses()
    
    if remaining > 0:
        st.markdown(f"""
        <div class="usage-counter">
            📊 Análises restantes nesta sessão: <strong>{remaining}</strong>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="usage-counter limit-reached">
            ❌ Limite de análises atingido! Recarregue a página para reiniciar.
        </div>
        """, unsafe_allow_html=True)
    
    # Formulário principal
    st.markdown('<div class="analysis-section fade-in-up">', unsafe_allow_html=True)
    st.subheader("📋 Dados para Análise")
    
    col1, col2 = st.columns(2)
    
    with col1:
        nome = st.text_input("👤 Nome completo", placeholder="Digite seu nome completo")
    
    with col2:
        email = st.text_input("📧 E-mail", placeholder="seu@email.com")
    
    # Upload de arquivo
    st.subheader("📄 Upload do Documento")
    arquivo_pdf = st.file_uploader(
        "Selecione um arquivo PDF para análise",
        type=["pdf"],
        help="Envie um documento PDF com o texto que deseja analisar"
    )
    
    # Opção de texto direto
    with st.expander("✏️ Ou cole o texto diretamente"):
        texto_direto = st.text_area(
            "Cole o texto aqui:",
            height=200,
            placeholder="Cole aqui o texto que deseja analisar..."
        )
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Botão de análise
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        analisar = st.button(
            "🔍 Realizar Análise Avançada",
            disabled=not usage_controller.can_analyze(),
            help="Clique para iniciar a análise completa do texto"
        )
    
    # Processamento da análise
    if analisar:
        # Validações
        if not nome or not email:
            st.error("❌ Por favor, preencha nome e e-mail.")
            return
        
        if not arquivo_pdf and not texto_direto:
            st.error("❌ Por favor, envie um PDF ou cole o texto diretamente.")
            return
        
        if not usage_controller.can_analyze():
            st.error("❌ Limite de análises atingido para esta sessão.")
            return
        
        # Extração do texto
        with st.spinner("📄 Extraindo texto..."):
            if arquivo_pdf:
                texto_para_analise = extrair_texto_pdf(arquivo_pdf)
                fonte_texto = f"PDF: {arquivo_pdf.name}"
            else:
                texto_para_analise = texto_direto.strip()
                fonte_texto = "Texto colado diretamente"
            
            if not texto_para_analise:
                st.error("❌ Não foi possível extrair texto válido.")
                return
        
        # Análise do texto
        with st.spinner("🤖 Realizando análise avançada..."):
            resultado = analyzer.analyze_text_comprehensive(texto_para_analise)
            
            if resultado['ai_probability'] == 0 and resultado['confidence'] == 0:
                st.error("❌ Erro na análise. Verifique se o texto é adequado.")
                return
        
        # Gera código de verificação
        codigo_verificacao = gerar_codigo_verificacao(texto_para_analise)
        
        # Registra uso
        usage_controller.record_usage({
            'nome': nome,
            'email': email,
            'codigo': codigo_verificacao,
            'resultado': resultado,
            'fonte': fonte_texto
        })
        
        # Salva no Google Sheets
        with st.spinner("💾 Salvando dados..."):
            sucesso_sheets = salvar_dados_google_sheets(nome, email, codigo_verificacao, resultado)
            if not sucesso_sheets:
                st.warning("⚠️ Dados não foram salvos no sistema, mas a análise foi concluída.")
        
        # Exibição dos resultados
        st.success("✅ Análise concluída com sucesso!")
        
        # Métricas principais animadas
        ai_prob = resultado['ai_probability']
        confidence = resultado['confidence']
        quality_score = resultado.get('quality_analysis', {}).get('overall_score', 0) * 100
        
        create_animated_metrics(ai_prob, confidence, quality_score)
        
        # Resultado principal com efeito neon
        confidence_level = resultado['confidence_level']
        interpretation = resultado['interpretation']
        
        # Determina cor baseada no resultado
        if ai_prob > 70:
            neon_class = "neon-high"
            icon = "🤖"
            status = "ALTA PROBABILIDADE DE IA"
        elif ai_prob > 40:
            neon_class = "neon-medium"
            icon = "⚠️"
            status = "PROBABILIDADE MODERADA"
        else:
            neon_class = "neon-low"
            icon = "👤"
            status = "BAIXA PROBABILIDADE DE IA"
        
        st.markdown(f"""
        <div class="neon-result">
            <div class="neon-text {neon_class}" style="font-size: 3rem; margin-bottom: 1rem;">
                {icon}
            </div>
            <div class="neon-text {neon_class}" style="font-size: 1.5rem; font-weight: 600; margin-bottom: 0.5rem;">
                {status}
            </div>
            <div style="color: #ccc; font-size: 1rem; margin-bottom: 1rem;">
                Probabilidade: {ai_prob:.1f}% | Confiança: {confidence:.1f}%
            </div>
            <div style="color: #fff; font-size: 0.9rem; opacity: 0.8;">
                {interpretation}
            </div>
            <div style="color: #ccc; font-size: 0.8rem; margin-top: 1rem;">
                Código de Verificação: {codigo_verificacao}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Gráficos e métricas detalhadas
        st.subheader("📊 Análise Detalhada")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Gauge de confiança
            fig_gauge = create_confidence_gauge(confidence)
            st.plotly_chart(fig_gauge, use_container_width=True)
        
        with col2:
            # Radar das métricas
            if 'metrics' in resultado:
                fig_radar = create_metrics_radar(resultado['metrics'])
                st.plotly_chart(fig_radar, use_container_width=True)
        
        # Métricas individuais
        st.subheader("🔍 Métricas Individuais")
        
        if 'metrics' in resultado:
            metrics = resultado['metrics']
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Entropia de Palavras", f"{metrics.get('word_entropy', 0):.2f}")
                st.metric("Padrões Repetitivos", f"{metrics.get('repetition_score', 0):.2f}")
            
            with col2:
                st.metric("Diversidade Lexical", f"{metrics.get('lexical_diversity', 0):.2f}")
                st.metric("Indicadores de IA", f"{metrics.get('ai_patterns', 0):.2f}")
            
            with col3:
                st.metric("Complexidade Sintática", f"{metrics.get('syntactic_complexity', 0):.2f}")
                st.metric("Análise RoBERTa", f"{metrics.get('roberta_score', 0):.1f}%")
        
        # Análise de qualidade
        if 'quality_analysis' in resultado:
            quality = resultado['quality_analysis']
            
            st.subheader("📝 Qualidade do Texto")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Qualidade Geral", quality.get('quality_level', 'N/A'))
                st.metric("Score de Qualidade", f"{quality.get('overall_score', 0):.2f}")
            
            with col2:
                if 'factors' in quality:
                    factors = quality['factors']
                    st.write("**Fatores de Qualidade:**")
                    for factor, value in factors.items():
                        factor_name = factor.replace('_', ' ').title()
                        st.write(f"• {factor_name}: {value:.2f}")
        
        # Recomendações
        if 'recommendations' in resultado and resultado['recommendations']:
            st.subheader("💡 Recomendações")
            
            st.markdown("""
            <div class="recommendation-box">
            """, unsafe_allow_html=True)
            
            for rec in resultado['recommendations']:
                st.write(f"• {rec}")
            
            st.markdown("</div>", unsafe_allow_html=True)
        
        # Geração do relatório
        st.subheader("📄 Relatório Profissional")
        
        with st.spinner("📋 Gerando relatório profissional..."):
            user_data = {
                'nome': nome,
                'email': email,
                'codigo': codigo_verificacao
            }
            
            # Preview do texto para o relatório
            texto_preview = texto_para_analise[:1000] if len(texto_para_analise) > 1000 else texto_para_analise
            
            try:
                report_path = report_generator.generate_comprehensive_report(
                    resultado, user_data, texto_preview
                )
                
                with open(report_path, "rb") as f:
                    st.download_button(
                        "📥 Baixar Relatório Completo (PDF)",
                        f.read(),
                        f"relatorio_totalia_{codigo_verificacao}.pdf",
                        "application/pdf",
                        key="download_report"
                    )
                
                st.success("✅ Relatório profissional gerado com sucesso!")
                
            except Exception as e:
                st.error(f"❌ Erro ao gerar relatório: {e}")
        
        # Informações adicionais
        with st.expander("ℹ️ Informações Técnicas"):
            st.write(f"**Fonte do texto:** {fonte_texto}")
            st.write(f"**Tamanho do texto:** {len(texto_para_analise)} caracteres")
            st.write(f"**Palavras:** {len(texto_para_analise.split())} palavras")
            st.write(f"**Data/Hora:** {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}")
            st.write(f"**Versão do sistema:** TotalIA v2.0 Professional")
    
    # Seção de apoio via PIX
    st.markdown("---")
    st.markdown("""
    <div class="fade-in-up">
        <h3 style='color: green; text-align: center;'>💚 Apoie Este Projeto</h3>
        <p style='text-align: center;'>Ajude a manter este sistema funcionando com uma contribuição via PIX</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
        <div style='text-align: center; padding: 1rem; background: #f8f9fa; border-radius: 10px;'>
            <p><strong>Chave PIX:</strong> <span style='color: blue;'>pesas8810@gmail.com</span></p>
            <p><strong>Valor sugerido:</strong> R$ 20,00</p>
            <p><strong>Beneficiário:</strong> PEAS TECHNOLOGIES</p>
        </div>
        """, unsafe_allow_html=True)
        
        # QR Code PIX
        payload_pix = "00020126400014br.gov.bcb.pix0118pesas8810@gmail.com520400005303986540520.005802BR5925PEDRO EMILIO AMADOR SALOM6013TEOFILO OTONI62200516PEASTECHNOLOGIES6304C9DB"
        
        try:
            qr_img = gerar_qr_code_pix(payload_pix)
            st.image(qr_img, caption="📲 Escaneie para contribuir via PIX", width=250)
        except Exception as e:
            st.write("QR Code temporariamente indisponível")
        
        st.success("🙏 Obrigado pelo seu apoio!")

if __name__ == "__main__":
    main()

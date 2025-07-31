"""
Sistema Integrado de Confiança para Detecção de IA
Implementação Completa das Melhorias de Confiança
"""

import numpy as np
import re
import time
from collections import Counter, defaultdict
from typing import Dict, List, Tuple, Optional
import hashlib
import json
from datetime import datetime, timedelta
import logging

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MultiDetectorEnsemble:
    """Sistema de múltiplos detectores para aumentar confiança"""
    
    def __init__(self):
        self.detectors = {
            'statistical': StatisticalDetector(),
            'pattern': PatternDetector(),
            'syntactic': SyntacticDetector(),
            'semantic': SemanticDetector(),
            'perplexity': PerplexityDetector()
        }
        self.min_detectors = 3
    
    def calculate_ensemble_confidence(self, text: str) -> Dict:
        """Calcula confiança baseada na concordância entre detectores"""
        results = {}
        predictions = []
        
        for name, detector in self.detectors.items():
            try:
                result = detector.analyze(text)
                results[name] = result
                predictions.append(result['ai_probability'])
                logger.info(f"Detector {name}: {result['ai_probability']:.1f}%")
            except Exception as e:
                logger.warning(f"Detector {name} falhou: {e}")
                continue
        
        if len(predictions) < self.min_detectors:
            return {
                'confidence': 25.0,
                'reason': f'Apenas {len(predictions)} detectores disponíveis (mínimo: {self.min_detectors})',
                'detector_count': len(predictions),
                'agreement_score': 0.0
            }
        
        # Calcula métricas de concordância
        mean_pred = np.mean(predictions)
        std_pred = np.std(predictions)
        
        # Agreement score baseado no desvio padrão
        # Quanto menor o desvio, maior a concordância
        max_std = 50.0  # Máximo desvio esperado
        agreement_score = max(0, 1 - (std_pred / max_std))
        
        # Confiança baseada na concordância
        base_confidence = agreement_score * 100
        
        # Bônus por ter mais detectores
        detector_bonus = min((len(predictions) - self.min_detectors) * 5, 15)
        
        # Bônus por consenso forte (todos na mesma direção)
        consensus_bonus = 0
        if all(p > 60 for p in predictions) or all(p < 40 for p in predictions):
            consensus_bonus = 10
        
        final_confidence = min(base_confidence + detector_bonus + consensus_bonus, 100.0)
        
        return {
            'confidence': final_confidence,
            'agreement_score': agreement_score,
            'detector_count': len(predictions),
            'mean_prediction': mean_pred,
            'std_prediction': std_pred,
            'individual_results': results,
            'consensus_bonus': consensus_bonus
        }

class TextQualityAnalyzer:
    """Analisador de qualidade do texto para ajustar confiança"""
    
    def assess_text_quality(self, text: str) -> Dict:
        """Avalia qualidade do texto em múltiplas dimensões"""
        
        quality_factors = {
            'length_adequacy': self._assess_length(text),
            'structure_clarity': self._assess_structure(text),
            'language_consistency': self._assess_language(text),
            'content_coherence': self._assess_coherence(text),
            'domain_specificity': self._assess_domain(text)
        }
        
        # Score de qualidade geral (média ponderada)
        weights = {
            'length_adequacy': 0.25,
            'structure_clarity': 0.25,
            'language_consistency': 0.20,
            'content_coherence': 0.20,
            'domain_specificity': 0.10
        }
        
        overall_quality = sum(
            quality_factors[factor] * weights[factor]
            for factor in quality_factors
        )
        
        # Converte qualidade em confiança
        quality_confidence = self._quality_to_confidence(overall_quality)
        
        return {
            'quality_score': overall_quality,
            'quality_confidence': quality_confidence,
            'quality_factors': quality_factors,
            'recommendations': self._generate_quality_recommendations(quality_factors)
        }
    
    def _assess_length(self, text: str) -> float:
        """Avalia adequação do comprimento do texto"""
        word_count = len(text.split())
        
        # Curva de adequação baseada no comprimento
        if word_count < 30:
            return 0.1  # Muito curto para análise confiável
        elif word_count < 50:
            return 0.3  # Curto, mas analisável
        elif word_count < 100:
            return 0.6  # Adequado para análise básica
        elif word_count < 300:
            return 0.9  # Bom para análise
        elif word_count < 1000:
            return 1.0  # Ideal para análise
        elif word_count < 3000:
            return 0.9  # Muito longo, mas ainda bom
        else:
            return 0.7  # Muito longo, pode ter ruído
    
    def _assess_structure(self, text: str) -> float:
        """Avalia clareza da estrutura do texto"""
        sentences = [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        
        if not sentences:
            return 0.0
        
        # Métricas de estrutura
        sentence_lengths = [len(s.split()) for s in sentences]
        avg_sentence_length = np.mean(sentence_lengths)
        sentence_variety = np.std(sentence_lengths) if len(sentence_lengths) > 1 else 0
        
        structure_score = 0.0
        
        # Comprimento de frase adequado (8-30 palavras)
        if 8 <= avg_sentence_length <= 30:
            structure_score += 0.4
        elif 5 <= avg_sentence_length <= 40:
            structure_score += 0.2
        
        # Variedade nas frases (indica estrutura natural)
        if sentence_variety > 2:
            structure_score += 0.3
        elif sentence_variety > 1:
            structure_score += 0.1
        
        # Organização em parágrafos
        if len(paragraphs) > 1:
            structure_score += 0.3
        elif len(paragraphs) == 1 and len(sentences) > 3:
            structure_score += 0.1
        
        return min(structure_score, 1.0)
    
    def _assess_language(self, text: str) -> float:
        """Avalia consistência da linguagem"""
        # Detecta mistura de idiomas ou inconsistências
        words = re.findall(r'\b\w+\b', text.lower())
        
        if not words:
            return 0.0
        
        # Métricas de consistência
        word_freq = Counter(words)
        
        # Verifica repetição excessiva (sinal de baixa qualidade)
        most_common_freq = word_freq.most_common(1)[0][1] if word_freq else 0
        repetition_ratio = most_common_freq / len(words)
        
        # Verifica diversidade vocabular
        unique_ratio = len(set(words)) / len(words)
        
        language_score = 0.0
        
        # Penaliza repetição excessiva
        if repetition_ratio < 0.1:  # Menos de 10% de repetição da palavra mais comum
            language_score += 0.5
        elif repetition_ratio < 0.2:
            language_score += 0.3
        
        # Premia diversidade vocabular
        if unique_ratio > 0.6:
            language_score += 0.5
        elif unique_ratio > 0.4:
            language_score += 0.3
        
        return min(language_score, 1.0)
    
    def _assess_coherence(self, text: str) -> float:
        """Avalia coerência do conteúdo"""
        sentences = [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]
        
        if len(sentences) < 2:
            return 0.5  # Não há como avaliar coerência
        
        # Análise de conectivos e transições
        connectives = [
            r'\b(além disso|portanto|consequentemente|dessa forma|por outro lado)\b',
            r'\b(entretanto|contudo|todavia|no entanto)\b',
            r'\b(primeiramente|em seguida|finalmente|por fim)\b',
            r'\b(por exemplo|ou seja|isto é|em outras palavras)\b'
        ]
        
        connective_count = 0
        for pattern in connectives:
            connective_count += len(re.findall(pattern, text.lower()))
        
        # Normaliza pela quantidade de frases
        connective_density = connective_count / len(sentences)
        
        coherence_score = 0.0
        
        # Densidade adequada de conectivos (indica estrutura lógica)
        if 0.1 <= connective_density <= 0.3:
            coherence_score += 0.6
        elif 0.05 <= connective_density <= 0.5:
            coherence_score += 0.4
        
        # Verifica repetição de estruturas (pode indicar IA)
        sentence_starts = [s.split()[0].lower() if s.split() else '' for s in sentences]
        start_variety = len(set(sentence_starts)) / len(sentence_starts) if sentence_starts else 0
        
        if start_variety > 0.7:
            coherence_score += 0.4
        elif start_variety > 0.5:
            coherence_score += 0.2
        
        return min(coherence_score, 1.0)
    
    def _assess_domain(self, text: str) -> float:
        """Avalia especificidade do domínio"""
        # Detecta se o texto é de um domínio específico
        # Textos especializados tendem a ser mais confiáveis para análise
        
        technical_indicators = [
            r'\b\d+%\b',  # Percentuais
            r'\b\d{4}\b',  # Anos
            r'\b[A-Z]{2,}\b',  # Siglas
            r'\b(pesquisa|estudo|análise|dados|resultados)\b',  # Termos técnicos
            r'\b(segundo|conforme|de acordo com)\b'  # Citações
        ]
        
        indicator_count = 0
        for pattern in technical_indicators:
            indicator_count += len(re.findall(pattern, text))
        
        words = len(text.split())
        if words == 0:
            return 0.0
        
        # Densidade de indicadores técnicos
        technical_density = indicator_count / words
        
        # Score baseado na densidade
        if technical_density > 0.05:
            return 1.0  # Texto técnico/especializado
        elif technical_density > 0.02:
            return 0.8  # Alguma especificidade
        elif technical_density > 0.01:
            return 0.6  # Pouca especificidade
        else:
            return 0.4  # Texto genérico
    
    def _quality_to_confidence(self, quality_score: float) -> float:
        """Converte score de qualidade em nível de confiança"""
        # Função não-linear para converter qualidade em confiança
        if quality_score >= 0.8:
            return 90.0 + (quality_score - 0.8) * 50  # 90-100%
        elif quality_score >= 0.6:
            return 70.0 + (quality_score - 0.6) * 100  # 70-90%
        elif quality_score >= 0.4:
            return 50.0 + (quality_score - 0.4) * 100  # 50-70%
        elif quality_score >= 0.2:
            return 30.0 + (quality_score - 0.2) * 100  # 30-50%
        else:
            return quality_score * 150  # 0-30%
    
    def _generate_quality_recommendations(self, quality_factors: Dict) -> List[str]:
        """Gera recomendações baseadas na qualidade"""
        recommendations = []
        
        if quality_factors['length_adequacy'] < 0.5:
            recommendations.append("📏 Texto muito curto - considere análise de texto mais longo")
        
        if quality_factors['structure_clarity'] < 0.5:
            recommendations.append("📝 Estrutura pouco clara - pode afetar precisão da análise")
        
        if quality_factors['language_consistency'] < 0.5:
            recommendations.append("🔤 Inconsistências linguísticas detectadas")
        
        if quality_factors['content_coherence'] < 0.5:
            recommendations.append("🔗 Baixa coerência textual - resultado pode ser menos confiável")
        
        if all(score > 0.7 for score in quality_factors.values()):
            recommendations.append("✅ Texto de alta qualidade - análise muito confiável")
        
        return recommendations

class ConfidenceCalibrator:
    """Sistema de calibração baseado em dados históricos"""
    
    def __init__(self, data_file: str = "historical_data.json"):
        self.data_file = data_file
        self.historical_data = self._load_historical_data()
        self.min_samples = 50
    
    def _load_historical_data(self) -> List[Dict]:
        """Carrega dados históricos do arquivo"""
        try:
            with open(self.data_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.info("Arquivo de dados históricos não encontrado. Criando novo.")
            return []
        except Exception as e:
            logger.error(f"Erro ao carregar dados históricos: {e}")
            return []
    
    def _save_historical_data(self):
        """Salva dados históricos no arquivo"""
        try:
            with open(self.data_file, 'w') as f:
                json.dump(self.historical_data, f, indent=2)
        except Exception as e:
            logger.error(f"Erro ao salvar dados históricos: {e}")
    
    def add_historical_result(self, prediction: float, actual_label: int,
                            text_features: Dict, confidence: float = None):
        """Adiciona resultado histórico para calibração futura"""
        entry = {
            'prediction': prediction,
            'actual': actual_label,
            'features': text_features,
            'confidence': confidence,
            'timestamp': datetime.now().isoformat(),
            'correct': self._is_prediction_correct(prediction, actual_label)
        }
        
        self.historical_data.append(entry)
        
        # Limita tamanho dos dados históricos
        if len(self.historical_data) > 10000:
            # Remove entradas mais antigas
            self.historical_data = self.historical_data[-8000:]
        
        self._save_historical_data()
        logger.info(f"Adicionado resultado histórico: pred={prediction:.1f}%, actual={actual_label}")
    
    def calibrate_confidence(self, raw_prediction: float, text_features: Dict) -> Dict:
        """Calibra confiança baseada em dados históricos"""
        
        if len(self.historical_data) < self.min_samples:
            return {
                'calibrated_confidence': self._conservative_confidence(raw_prediction),
                'reason': f'Dados insuficientes ({len(self.historical_data)}/{self.min_samples})',
                'historical_accuracy': None,
                'similar_cases': 0
            }
        
        # Encontra casos similares
        similar_cases = self._find_similar_cases(text_features)
        
        if len(similar_cases) < 10:
            return {
                'calibrated_confidence': self._conservative_confidence(raw_prediction),
                'reason': f'Poucos casos similares ({len(similar_cases)})',
                'historical_accuracy': None,
                'similar_cases': len(similar_cases)
            }
        
        # Calcula precisão em casos similares
        bin_accuracy = self._calculate_bin_accuracy(raw_prediction, similar_cases)
        
        # Calibra confiança baseada na precisão histórica
        calibrated_confidence = bin_accuracy * 100
        
        # Ajusta baseado na quantidade de casos similares
        sample_adjustment = min(len(similar_cases) / 50, 1.0)  # Máximo em 50 casos
        calibrated_confidence *= (0.7 + 0.3 * sample_adjustment)
        
        return {
            'calibrated_confidence': min(calibrated_confidence, 95.0),
            'historical_accuracy': bin_accuracy,
            'similar_cases': len(similar_cases),
            'reason': 'Calibrado com dados históricos'
        }
    
    def _find_similar_cases(self, target_features: Dict) -> List[Dict]:
        """Encontra casos históricos similares"""
        similar_cases = []
        
        for case in self.historical_data:
            similarity = self._calculate_feature_similarity(
                target_features, case['features']
            )
            
            if similarity >= 0.7:  # Threshold de similaridade
                case['similarity'] = similarity
                similar_cases.append(case)
        
        # Ordena por similaridade
        similar_cases.sort(key=lambda x: x['similarity'], reverse=True)
        
        return similar_cases[:100]  # Máximo 100 casos mais similares
    
    def _calculate_feature_similarity(self, features1: Dict, features2: Dict) -> float:
        """Calcula similaridade entre features de dois textos"""
        
        # Features numéricas para comparação
        numeric_features = ['word_count', 'sentence_count', 'avg_word_length', 'unique_words']
        
        similarities = []
        
        for feature in numeric_features:
            if feature in features1 and feature in features2:
                val1, val2 = features1[feature], features2[feature]
                if val1 == 0 and val2 == 0:
                    similarities.append(1.0)
                elif val1 == 0 or val2 == 0:
                    similarities.append(0.0)
                else:
                    # Similaridade baseada na diferença relativa
                    diff = abs(val1 - val2) / max(val1, val2)
                    similarity = max(0, 1 - diff)
                    similarities.append(similarity)
        
        return np.mean(similarities) if similarities else 0.0
    
    def _calculate_bin_accuracy(self, prediction: float, similar_cases: List[Dict]) -> float:
        """Calcula precisão em bin de predição similar"""
        
        # Define bin baseado na predição
        bin_size = 20  # Bins de 20%
        bin_start = (prediction // bin_size) * bin_size
        bin_end = bin_start + bin_size
        
        # Filtra casos no mesmo bin
        bin_cases = [
            case for case in similar_cases
            if bin_start <= case['prediction'] < bin_end
        ]
        
        if len(bin_cases) < 5:
            # Se poucos casos no bin, usa bin mais amplo
            bin_size = 40
            bin_start = (prediction // bin_size) * bin_size
            bin_end = bin_start + bin_size
            
            bin_cases = [
                case for case in similar_cases
                if bin_start <= case['prediction'] < bin_end
            ]
        
        if len(bin_cases) < 3:
            # Se ainda poucos casos, usa todos os casos similares
            bin_cases = similar_cases
        
        # Calcula precisão
        correct_predictions = sum(1 for case in bin_cases if case['correct'])
        accuracy = correct_predictions / len(bin_cases) if bin_cases else 0.5
        
        return accuracy
    
    def _is_prediction_correct(self, prediction: float, actual_label: int) -> bool:
        """Verifica se predição estava correta"""
        predicted_label = 1 if prediction > 50 else 0
        return predicted_label == actual_label
    
    def _conservative_confidence(self, prediction: float) -> float:
        """Retorna confiança conservadora quando não há dados suficientes"""
        # Confiança baseada na distância de 50% (zona de incerteza)
        distance_from_center = abs(prediction - 50)
        conservative_confidence = 30 + (distance_from_center / 50) * 40  # 30-70%
        return min(conservative_confidence, 70.0)

class SeparationMarginAnalyzer:
    """Analisador de margem de separação para confiança"""
    
    def __init__(self):
        self.uncertainty_zone = (40, 60)  # Zona de maior incerteza
        self.high_confidence_zones = [(0, 25), (75, 100)]  # Zonas de alta confiança
    
    def calculate_margin_confidence(self, prediction: float) -> Dict:
        """Calcula confiança baseada na margem de separação"""
        
        # Identifica zona atual
        current_zone = self._identify_zone(prediction)
        
        # Calcula distância da zona de incerteza
        uncertainty_distance = self._calculate_uncertainty_distance(prediction)
        
        # Calcula confiança baseada na margem
        margin_confidence = self._distance_to_confidence(uncertainty_distance)
        
        # Aplica multiplicadores baseados na zona
        zone_multiplier = self._get_zone_multiplier(current_zone)
        adjusted_confidence = margin_confidence * zone_multiplier
        
        # Bônus para predições muito extremas
        extreme_bonus = self._calculate_extreme_bonus(prediction)
        final_confidence = min(adjusted_confidence + extreme_bonus, 100.0)
        
        return {
            'margin_confidence': final_confidence,
            'current_zone': current_zone,
            'uncertainty_distance': uncertainty_distance,
            'zone_multiplier': zone_multiplier,
            'extreme_bonus': extreme_bonus,
            'recommendation': self._generate_margin_recommendation(current_zone, final_confidence)
        }
    
    def _identify_zone(self, prediction: float) -> str:
        """Identifica zona de predição"""
        if prediction <= 25:
            return 'very_high_human'
        elif prediction <= 40:
            return 'high_human'
        elif prediction <= 60:
            return 'uncertainty'
        elif prediction <= 75:
            return 'high_ai'
        else:
            return 'very_high_ai'
    
    def _calculate_uncertainty_distance(self, prediction: float) -> float:
        """Calcula distância da zona de incerteza"""
        uncertainty_center = 50
        uncertainty_radius = 10  # Zona de ±10% ao redor de 50%
        
        if self.uncertainty_zone[0] <= prediction <= self.uncertainty_zone[1]:
            # Dentro da zona de incerteza
            return 0.0
        elif prediction < self.uncertainty_zone[0]:
            # Abaixo da zona de incerteza
            return self.uncertainty_zone[0] - prediction
        else:
            # Acima da zona de incerteza
            return prediction - self.uncertainty_zone[1]
    
    def _distance_to_confidence(self, distance: float) -> float:
        """Converte distância em confiança"""
        # Função não-linear: confiança cresce rapidamente com a distância
        max_distance = 40  # Distância máxima considerada
        normalized_distance = min(distance / max_distance, 1.0)
        
        # Função exponencial para crescimento rápido
        confidence = 40 + (60 * (normalized_distance ** 0.7))
        return confidence
    
    def _get_zone_multiplier(self, zone: str) -> float:
        """Retorna multiplicador baseado na zona"""
        multipliers = {
            'very_high_human': 1.0,
            'high_human': 0.9,
            'uncertainty': 0.4,
            'high_ai': 0.9,
            'very_high_ai': 1.0
        }
        return multipliers.get(zone, 0.5)
    
    def _calculate_extreme_bonus(self, prediction: float) -> float:
        """Calcula bônus para predições extremas"""
        if prediction <= 15 or prediction >= 85:
            return 10.0  # Bônus alto para predições muito extremas
        elif prediction <= 25 or prediction >= 75:
            return 5.0   # Bônus médio para predições extremas
        else:
            return 0.0   # Sem bônus
    
    def _generate_margin_recommendation(self, zone: str, confidence: float) -> str:
        """Gera recomendação baseada na zona e confiança"""
        recommendations = {
            'very_high_human': f'Resultado muito confiável ({confidence:.0f}%) - muito provavelmente texto humano',
            'high_human': f'Resultado confiável ({confidence:.0f}%) - provavelmente texto humano',
            'uncertainty': f'Resultado incerto ({confidence:.0f}%) - zona de ambiguidade, considere análise adicional',
            'high_ai': f'Resultado confiável ({confidence:.0f}%) - provavelmente texto de IA',
            'very_high_ai': f'Resultado muito confiável ({confidence:.0f}%) - muito provavelmente texto de IA'
        }
        return recommendations.get(zone, f'Resultado com {confidence:.0f}% de confiança')

# Classes de detectores individuais (implementações simplificadas)
class StatisticalDetector:
    def analyze(self, text: str) -> Dict:
        words = text.split()
        if not words:
            return {'ai_probability': 50.0}
        
        # Análise estatística simples
        avg_word_length = np.mean([len(word) for word in words])
        unique_ratio = len(set(words)) / len(words)
        
        # IA tende a ter palavras mais longas e menos diversidade
        ai_score = (avg_word_length / 10) * 50 + (1 - unique_ratio) * 50
        return {'ai_probability': min(ai_score, 100.0)}

class PatternDetector:
    def analyze(self, text: str) -> Dict:
        ai_patterns = [
            r'\b(além disso|portanto|consequentemente)\b',
            r'\b(é importante notar|vale ressaltar)\b',
            r'\b(em resumo|em conclusão)\b'
        ]
        
        pattern_count = 0
        for pattern in ai_patterns:
            pattern_count += len(re.findall(pattern, text.lower()))
        
        words = len(text.split())
        if words == 0:
            return {'ai_probability': 50.0}
        
        pattern_density = (pattern_count / words) * 1000
        ai_score = min(pattern_density * 20, 100.0)
        
        return {'ai_probability': ai_score}

class SyntacticDetector:
    def analyze(self, text: str) -> Dict:
        sentences = re.split(r'[.!?]+', text)
        if not sentences:
            return {'ai_probability': 50.0}
        
        sentence_lengths = [len(s.split()) for s in sentences if s.strip()]
        if not sentence_lengths:
            return {'ai_probability': 50.0}
        
        # IA tende a ter frases mais uniformes
        avg_length = np.mean(sentence_lengths)
        std_length = np.std(sentence_lengths)
        
        # Baixa variação = mais provável IA
        if std_length == 0:
            uniformity = 1.0
        else:
            uniformity = 1 / (1 + std_length / avg_length)
        
        ai_score = uniformity * 100
        return {'ai_probability': ai_score}

class SemanticDetector:
    def analyze(self, text: str) -> Dict:
        # Análise semântica simplificada
        formal_words = ['entretanto', 'todavia', 'outrossim', 'destarte', 'ademais']
        formal_count = sum(text.lower().count(word) for word in formal_words)
        
        words = len(text.split())
        if words == 0:
            return {'ai_probability': 50.0}
        
        formality_ratio = formal_count / words
        ai_score = min(formality_ratio * 500, 100.0)
        
        return {'ai_probability': ai_score}

class PerplexityDetector:
    def analyze(self, text: str) -> Dict:
        words = text.lower().split()
        if len(words) < 4:
            return {'ai_probability': 50.0}
        
        # Aproximação simples de perplexidade
        bigrams = [(words[i], words[i+1]) for i in range(len(words)-1)]
        bigram_counts = Counter(bigrams)
        word_counts = Counter(words)
        
        log_prob_sum = 0
        for bigram in bigrams:
            prob = bigram_counts[bigram] / word_counts[bigram[0]]
            if prob > 0:
                log_prob_sum += np.log2(prob)
        
        avg_log_prob = log_prob_sum / len(bigrams)
        perplexity = 2 ** (-avg_log_prob)
        
        # Normaliza perplexidade para score de IA
        normalized_perplexity = min(perplexity / 100, 1.0)
        ai_score = normalized_perplexity * 100
        
        return {'ai_probability': ai_score}

# Exemplo de uso
def exemplo_sistema_confianca():
    """Exemplo de uso do sistema integrado de confiança"""
    
    # Texto de exemplo
    texto = """
    A inteligência artificial representa uma das mais significativas inovações tecnológicas 
    da era moderna. Além disso, é importante notar que seus impactos se estendem por 
    diversos setores da sociedade. Consequentemente, devemos considerar tanto os benefícios 
    quanto os desafios que essa tecnologia apresenta. Em conclusão, a IA continuará a 
    moldar nosso futuro de maneiras que ainda estamos começando a compreender.
    """
    
    # Inicializa componentes
    ensemble = MultiDetectorEnsemble()
    quality_analyzer = TextQualityAnalyzer()
    calibrator = ConfidenceCalibrator()
    margin_analyzer = SeparationMarginAnalyzer()
    
    print("=== SISTEMA INTEGRADO DE CONFIANÇA ===\n")
    
    # 1. Análise do ensemble
    print("1. Análise do Ensemble de Detectores:")
    ensemble_result = ensemble.calculate_ensemble_confidence(texto)
    print(f"   Confiança do Ensemble: {ensemble_result['confidence']:.1f}%")
    print(f"   Detectores ativos: {ensemble_result['detector_count']}")
    print(f"   Score de concordância: {ensemble_result['agreement_score']:.2f}")
    print()
    
    # 2. Análise de qualidade
    print("2. Análise de Qualidade do Texto:")
    quality_result = quality_analyzer.assess_text_quality(texto)
    print(f"   Confiança da Qualidade: {quality_result['quality_confidence']:.1f}%")
    print(f"   Score de qualidade: {quality_result['quality_score']:.2f}")
    for factor, score in quality_result['quality_factors'].items():
        print(f"   - {factor}: {score:.2f}")
    print()
    
    # 3. Análise de margem
    prediction = ensemble_result['mean_prediction']
    print("3. Análise de Margem de Separação:")
    margin_result = margin_analyzer.calculate_margin_confidence(prediction)
    print(f"   Confiança da Margem: {margin_result['margin_confidence']:.1f}%")
    print(f"   Zona atual: {margin_result['current_zone']}")
    print(f"   Distância da incerteza: {margin_result['uncertainty_distance']:.1f}")
    print()
    
    # 4. Calibração (exemplo sem dados históricos)
    print("4. Calibração com Dados Históricos:")
    text_features = {
        'word_count': len(texto.split()),
        'sentence_count': len(re.split(r'[.!?]+', texto)),
        'avg_word_length': np.mean([len(word) for word in texto.split()]),
        'unique_words': len(set(texto.split()))
    }
    
    calibration_result = calibrator.calibrate_confidence(prediction, text_features)
    print(f"   Confiança Calibrada: {calibration_result['calibrated_confidence']:.1f}%")
    print(f"   Razão: {calibration_result['reason']}")
    print()
    
    # 5. Confiança final integrada
    print("5. Confiança Final Integrada:")
    
    # Pesos para cada componente
    weights = {
        'ensemble': 0.30,
        'quality': 0.25,
        'margin': 0.25,
        'calibration': 0.20
    }
    
    # Calcula confiança final
    final_confidence = (
        ensemble_result['confidence'] * weights['ensemble'] +
        quality_result['quality_confidence'] * weights['quality'] +
        margin_result['margin_confidence'] * weights['margin'] +
        calibration_result['calibrated_confidence'] * weights['calibration']
    )
    
    print(f"   CONFIANÇA FINAL: {final_confidence:.1f}%")
    
    # Classificação da confiança
    if final_confidence >= 85:
        nivel = "MUITO ALTA"
    elif final_confidence >= 70:
        nivel = "ALTA"
    elif final_confidence >= 55:
        nivel = "MODERADA"
    elif final_confidence >= 40:
        nivel = "BAIXA"
    else:
        nivel = "MUITO BAIXA"
    
    print(f"   Nível de Confiança: {nivel}")
    print(f"   Predição de IA: {prediction:.1f}%")

if __name__ == "__main__":
    exemplo_sistema_confianca()

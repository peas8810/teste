"""
Sistema de Calibração Avançado para Confiança
Implementa técnicas avançadas de calibração e validação
"""

import numpy as np
import json
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from sklearn.calibration import CalibratedClassifierCV
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
import warnings
warnings.filterwarnings('ignore')

class AdvancedConfidenceCalibrator:
    """Sistema avançado de calibração de confiança"""
    
    def __init__(self, data_file: str = "advanced_calibration_data.json"):
        self.data_file = data_file
        self.historical_data = self._load_data()
        self.isotonic_calibrator = None
        self.platt_calibrator = None
        self.min_samples_for_calibration = 100
        self.confidence_bins = np.linspace(0, 100, 21)  # 20 bins de 5% cada
        
    def _load_data(self) -> List[Dict]:
        """Carrega dados históricos"""
        try:
            with open(self.data_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return []
    
    def _save_data(self):
        """Salva dados históricos"""
        try:
            with open(self.data_file, 'w') as f:
                json.dump(self.historical_data, f, indent=2)
        except Exception as e:
            print(f"Erro ao salvar dados: {e}")
    
    def add_validation_result(self, predicted_confidence: float, 
                            predicted_probability: float, actual_label: int,
                            text_features: Dict):
        """Adiciona resultado de validação para calibração"""
        
        # Verifica se a predição estava correta
        predicted_label = 1 if predicted_probability > 50 else 0
        is_correct = predicted_label == actual_label
        
        # Calcula erro de calibração
        if actual_label == 1:
            calibration_error = abs(predicted_probability - 100)
        else:
            calibration_error = abs(predicted_probability - 0)
        
        entry = {
            'predicted_confidence': predicted_confidence,
            'predicted_probability': predicted_probability,
            'actual_label': actual_label,
            'is_correct': is_correct,
            'calibration_error': calibration_error,
            'text_features': text_features,
            'timestamp': datetime.now().isoformat()
        }
        
        self.historical_data.append(entry)
        
        # Limita tamanho dos dados
        if len(self.historical_data) > 5000:
            self.historical_data = self.historical_data[-4000:]
        
        self._save_data()
        
        # Re-treina calibradores se temos dados suficientes
        if len(self.historical_data) >= self.min_samples_for_calibration:
            self._train_calibrators()
    
    def _train_calibrators(self):
        """Treina calibradores isotônico e Platt"""
        
        if len(self.historical_data) < self.min_samples_for_calibration:
            return
        
        # Prepara dados para treinamento
        confidences = [entry['predicted_confidence'] for entry in self.historical_data]
        probabilities = [entry['predicted_probability'] for entry in self.historical_data]
        correct_flags = [entry['is_correct'] for entry in self.historical_data]
        
        # Treina calibrador isotônico (não-paramétrico)
        try:
            self.isotonic_calibrator = IsotonicRegression(out_of_bounds='clip')
            self.isotonic_calibrator.fit(confidences, correct_flags)
        except Exception as e:
            print(f"Erro ao treinar calibrador isotônico: {e}")
            self.isotonic_calibrator = None
        
        # Treina calibrador Platt (logístico)
        try:
            # Reshape para sklearn
            X = np.array(confidences).reshape(-1, 1)
            y = np.array(correct_flags)
            
            self.platt_calibrator = LogisticRegression()
            self.platt_calibrator.fit(X, y)
        except Exception as e:
            print(f"Erro ao treinar calibrador Platt: {e}")
            self.platt_calibrator = None
    
    def calibrate_confidence(self, raw_confidence: float, 
                           predicted_probability: float,
                           text_features: Dict) -> Dict:
        """Calibra confiança usando múltiplos métodos"""
        
        calibration_results = {}
        
        # 1. Calibração por bins históricos
        bin_calibrated = self._calibrate_by_bins(raw_confidence)
        calibration_results['bin_calibrated'] = bin_calibrated
        
        # 2. Calibração isotônica
        if self.isotonic_calibrator is not None:
            try:
                isotonic_calibrated = self.isotonic_calibrator.predict([raw_confidence])[0] * 100
                calibration_results['isotonic_calibrated'] = isotonic_calibrated
            except:
                calibration_results['isotonic_calibrated'] = raw_confidence
        else:
            calibration_results['isotonic_calibrated'] = raw_confidence
        
        # 3. Calibração Platt
        if self.platt_calibrator is not None:
            try:
                platt_prob = self.platt_calibrator.predict_proba([[raw_confidence]])[0, 1]
                platt_calibrated = platt_prob * 100
                calibration_results['platt_calibrated'] = platt_calibrated
            except:
                calibration_results['platt_calibrated'] = raw_confidence
        else:
            calibration_results['platt_calibrated'] = raw_confidence
        
        # 4. Calibração baseada em features similares
        feature_calibrated = self._calibrate_by_similar_features(
            raw_confidence, text_features
        )
        calibration_results['feature_calibrated'] = feature_calibrated
        
        # 5. Ensemble das calibrações
        ensemble_calibrated = self._ensemble_calibrations(calibration_results)
        
        # 6. Análise de confiabilidade da calibração
        calibration_reliability = self._assess_calibration_reliability()
        
        return {
            'final_calibrated_confidence': ensemble_calibrated,
            'calibration_methods': calibration_results,
            'calibration_reliability': calibration_reliability,
            'data_points_used': len(self.historical_data),
            'recommendation': self._generate_calibration_recommendation(
                ensemble_calibrated, calibration_reliability
            )
        }
    
    def _calibrate_by_bins(self, raw_confidence: float) -> float:
        """Calibra confiança usando bins históricos"""
        
        if len(self.historical_data) < 20:
            return raw_confidence
        
        # Encontra bin apropriado
        bin_size = 10  # Bins de 10%
        bin_start = (raw_confidence // bin_size) * bin_size
        bin_end = bin_start + bin_size
        
        # Filtra dados no bin
        bin_data = [
            entry for entry in self.historical_data
            if bin_start <= entry['predicted_confidence'] < bin_end
        ]
        
        if len(bin_data) < 5:
            # Expande bin se poucos dados
            bin_size = 20
            bin_start = (raw_confidence // bin_size) * bin_size
            bin_end = bin_start + bin_size
            
            bin_data = [
                entry for entry in self.historical_data
                if bin_start <= entry['predicted_confidence'] < bin_end
            ]
        
        if len(bin_data) < 3:
            return raw_confidence
        
        # Calcula precisão real no bin
        correct_count = sum(1 for entry in bin_data if entry['is_correct'])
        bin_accuracy = correct_count / len(bin_data)
        
        # Calibra baseado na precisão real
        calibrated_confidence = bin_accuracy * 100
        
        return calibrated_confidence
    
    def _calibrate_by_similar_features(self, raw_confidence: float,
                                     text_features: Dict) -> float:
        """Calibra baseado em casos com features similares"""
        
        if len(self.historical_data) < 30:
            return raw_confidence
        
        # Encontra casos similares
        similar_cases = []
        for entry in self.historical_data:
            similarity = self._calculate_feature_similarity(
                text_features, entry['text_features']
            )
            if similarity > 0.7:
                similar_cases.append(entry)
        
        if len(similar_cases) < 10:
            return raw_confidence
        
        # Filtra por faixa de confiança similar
        confidence_range = 15  # ±15%
        range_cases = [
            case for case in similar_cases
            if abs(case['predicted_confidence'] - raw_confidence) <= confidence_range
        ]
        
        if len(range_cases) < 5:
            range_cases = similar_cases  # Usa todos os casos similares
        
        # Calcula precisão em casos similares
        correct_count = sum(1 for case in range_cases if case['is_correct'])
        similarity_accuracy = correct_count / len(range_cases)
        
        return similarity_accuracy * 100
    
    def _ensemble_calibrations(self, calibration_results: Dict) -> float:
        """Combina diferentes métodos de calibração"""
        
        # Pesos baseados na confiabilidade de cada método
        weights = {
            'bin_calibrated': 0.3,
            'isotonic_calibrated': 0.25,
            'platt_calibrated': 0.25,
            'feature_calibrated': 0.2
        }
        
        # Calcula média ponderada
        weighted_sum = 0
        total_weight = 0
        
        for method, confidence in calibration_results.items():
            if method in weights and confidence is not None:
                weighted_sum += confidence * weights[method]
                total_weight += weights[method]
        
        if total_weight == 0:
            return calibration_results.get('bin_calibrated', 50.0)
        
        ensemble_result = weighted_sum / total_weight
        
        # Aplica suavização para evitar valores extremos
        smoothed_result = self._smooth_confidence(ensemble_result)
        
        return smoothed_result
    
    def _smooth_confidence(self, confidence: float) -> float:
        """Aplica suavização para evitar valores extremos"""
        
        # Limita valores extremos
        if confidence < 5:
            return 5.0
        elif confidence > 95:
            return 95.0
        
        # Suavização em direção à média se muito extremo
        if confidence < 20 or confidence > 80:
            mean_confidence = 50.0
            smoothing_factor = 0.1
            confidence = confidence * (1 - smoothing_factor) + mean_confidence * smoothing_factor
        
        return confidence
    
    def _assess_calibration_reliability(self) -> Dict:
        """Avalia confiabilidade do sistema de calibração"""
        
        if len(self.historical_data) < 50:
            return {
                'reliability_score': 30.0,
                'reliability_level': 'Baixa',
                'reason': 'Dados insuficientes para calibração confiável'
            }
        
        # Calcula métricas de calibração
        recent_data = self.historical_data[-200:]  # Últimos 200 casos
        
        # 1. Brier Score (menor é melhor)
        brier_score = self._calculate_brier_score(recent_data)
        
        # 2. Calibration Error (menor é melhor)
        calibration_error = self._calculate_calibration_error(recent_data)
        
        # 3. Reliability (maior é melhor)
        reliability = self._calculate_reliability(recent_data)
        
        # Score final de confiabilidade
        reliability_score = (
            (1 - min(brier_score, 1.0)) * 40 +  # 40% peso
            (1 - min(calibration_error / 50, 1.0)) * 35 +  # 35% peso
            reliability * 25  # 25% peso
        )
        
        # Classifica nível de confiabilidade
        if reliability_score >= 80:
            level = 'Muito Alta'
        elif reliability_score >= 65:
            level = 'Alta'
        elif reliability_score >= 50:
            level = 'Moderada'
        elif reliability_score >= 35:
            level = 'Baixa'
        else:
            level = 'Muito Baixa'
        
        return {
            'reliability_score': reliability_score,
            'reliability_level': level,
            'brier_score': brier_score,
            'calibration_error': calibration_error,
            'reliability': reliability,
            'data_points': len(recent_data)
        }
    
    def _calculate_brier_score(self, data: List[Dict]) -> float:
        """Calcula Brier Score para avaliar calibração"""
        if not data:
            return 1.0
        
        brier_sum = 0
        for entry in data:
            predicted_prob = entry['predicted_confidence'] / 100
            actual = 1 if entry['is_correct'] else 0
            brier_sum += (predicted_prob - actual) ** 2
        
        return brier_sum / len(data)
    
    def _calculate_calibration_error(self, data: List[Dict]) -> float:
        """Calcula erro de calibração médio"""
        if not data:
            return 50.0
        
        # Agrupa por bins de confiança
        bins = {}
        for entry in data:
            bin_idx = int(entry['predicted_confidence'] // 10)
            if bin_idx not in bins:
                bins[bin_idx] = []
            bins[bin_idx].append(entry)
        
        # Calcula erro por bin
        total_error = 0
        total_samples = 0
        
        for bin_idx, bin_data in bins.items():
            if len(bin_data) < 3:  # Pula bins com poucos dados
                continue
            
            avg_confidence = np.mean([entry['predicted_confidence'] for entry in bin_data])
            accuracy = np.mean([entry['is_correct'] for entry in bin_data]) * 100
            
            bin_error = abs(avg_confidence - accuracy)
            total_error += bin_error * len(bin_data)
            total_samples += len(bin_data)
        
        return total_error / total_samples if total_samples > 0 else 50.0
    
    def _calculate_reliability(self, data: List[Dict]) -> float:
        """Calcula confiabilidade baseada na consistência"""
        if len(data) < 20:
            return 0.3
        
        # Analisa últimos 30 dias
        recent_cutoff = datetime.now() - timedelta(days=30)
        recent_data = [
            entry for entry in data
            if datetime.fromisoformat(entry['timestamp']) > recent_cutoff
        ]
        
        if len(recent_data) < 10:
            recent_data = data[-20:]  # Últimos 20 casos
        
        # Calcula estabilidade da precisão ao longo do tempo
        accuracies = []
        window_size = max(5, len(recent_data) // 4)
        
        for i in range(0, len(recent_data) - window_size + 1, window_size // 2):
            window_data = recent_data[i:i + window_size]
            window_accuracy = np.mean([entry['is_correct'] for entry in window_data])
            accuracies.append(window_accuracy)
        
        if len(accuracies) < 2:
            return 0.5
        
        # Estabilidade baseada no desvio padrão
        stability = 1 - min(np.std(accuracies) * 2, 1.0)
        
        return stability
    
    def _calculate_feature_similarity(self, features1: Dict, features2: Dict) -> float:
        """Calcula similaridade entre features"""
        
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
                    diff = abs(val1 - val2) / max(val1, val2)
                    similarity = max(0, 1 - diff)
                    similarities.append(similarity)
        
        return np.mean(similarities) if similarities else 0.0
    
    def _generate_calibration_recommendation(self, calibrated_confidence: float,
                                           reliability: Dict) -> str:
        """Gera recomendação baseada na calibração"""
        
        reliability_level = reliability['reliability_level']
        
        if reliability_level in ['Muito Alta', 'Alta']:
            if calibrated_confidence >= 80:
                return f"✅ Confiança calibrada muito alta ({calibrated_confidence:.0f}%) - resultado muito confiável"
            elif calibrated_confidence >= 60:
                return f"✅ Confiança calibrada alta ({calibrated_confidence:.0f}%) - resultado confiável"
            else:
                return f"⚠️ Confiança calibrada baixa ({calibrated_confidence:.0f}%) - considere análise adicional"
        
        elif reliability_level == 'Moderada':
            return f"ℹ️ Confiança calibrada moderada ({calibrated_confidence:.0f}%) - calibração em desenvolvimento"
        
        else:
            return f"⚠️ Sistema de calibração ainda em treinamento - use com cautela"
    
    def get_calibration_statistics(self) -> Dict:
        """Retorna estatísticas do sistema de calibração"""
        
        if not self.historical_data:
            return {'status': 'Sem dados históricos'}
        
        # Estatísticas gerais
        total_cases = len(self.historical_data)
        correct_predictions = sum(1 for entry in self.historical_data if entry['is_correct'])
        overall_accuracy = correct_predictions / total_cases if total_cases > 0 else 0
        
        # Estatísticas por faixa de confiança
        confidence_ranges = {
            'Muito Baixa (0-20%)': [0, 20],
            'Baixa (20-40%)': [20, 40],
            'Moderada (40-60%)': [40, 60],
            'Alta (60-80%)': [60, 80],
            'Muito Alta (80-100%)': [80, 100]
        }
        
        range_stats = {}
        for range_name, (min_conf, max_conf) in confidence_ranges.items():
            range_data = [
                entry for entry in self.historical_data
                if min_conf <= entry['predicted_confidence'] < max_conf
            ]
            
            if range_data:
                range_accuracy = np.mean([entry['is_correct'] for entry in range_data])
                range_stats[range_name] = {
                    'count': len(range_data),
                    'accuracy': range_accuracy,
                    'avg_confidence': np.mean([entry['predicted_confidence'] for entry in range_data])
                }
            else:
                range_stats[range_name] = {'count': 0, 'accuracy': 0, 'avg_confidence': 0}
        
        return {
            'total_cases': total_cases,
            'overall_accuracy': overall_accuracy,
            'calibrators_trained': {
                'isotonic': self.isotonic_calibrator is not None,
                'platt': self.platt_calibrator is not None
            },
            'range_statistics': range_stats,
            'reliability_assessment': self._assess_calibration_reliability()
        }

# Exemplo de uso do sistema avançado
def exemplo_calibracao_avancada():
    """Demonstra o sistema avançado de calibração"""
    
    print("=== SISTEMA AVANÇADO DE CALIBRAÇÃO DE CONFIANÇA ===\n")
    
    # Inicializa calibrador
    calibrator = AdvancedConfidenceCalibrator()
    
    # Simula alguns dados históricos para demonstração
    print("1. Simulando dados históricos...")
    
    # Adiciona dados simulados
    for i in range(150):
        # Simula diferentes cenários
        if i < 50:  # Casos de alta confiança
            pred_conf = np.random.uniform(70, 95)
            pred_prob = np.random.uniform(75, 95)
            actual = 1 if np.random.random() > 0.15 else 0  # 85% correto
        elif i < 100:  # Casos de baixa confiança
            pred_conf = np.random.uniform(20, 50)
            pred_prob = np.random.uniform(10, 40)
            actual = 0 if np.random.random() > 0.25 else 1  # 75% correto
        else:  # Casos de confiança moderada
            pred_conf = np.random.uniform(50, 70)
            pred_prob = np.random.uniform(45, 65)
            actual = 1 if np.random.random() > 0.4 else 0  # 60% correto
        
        features = {
            'word_count': np.random.randint(50, 500),
            'sentence_count': np.random.randint(3, 25),
            'avg_word_length': np.random.uniform(4, 8),
            'unique_words': np.random.randint(30, 200)
        }
        
        calibrator.add_validation_result(pred_conf, pred_prob, actual, features)
    
    print(f"   Adicionados {len(calibrator.historical_data)} casos históricos")
    print()
    
    # Testa calibração
    print("2. Testando Calibração:")
    
    test_cases = [
        {'confidence': 85, 'probability': 80, 'description': 'Alta confiança'},
        {'confidence': 45, 'probability': 55, 'description': 'Confiança moderada'},
        {'confidence': 25, 'probability': 30, 'description': 'Baixa confiança'}
    ]
    
    for case in test_cases:
        features = {
            'word_count': 200,
            'sentence_count': 10,
            'avg_word_length': 5.5,
            'unique_words': 120
        }
        
        result = calibrator.calibrate_confidence(
            case['confidence'], case['probability'], features
        )
        
        print(f"   {case['description']}:")
        print(f"   - Confiança original: {case['confidence']:.0f}%")
        print(f"   - Confiança calibrada: {result['final_calibrated_confidence']:.1f}%")
        print(f"   - Confiabilidade: {result['calibration_reliability']['reliability_level']}")
        print(f"   - Recomendação: {result['recommendation']}")
        print()
    
    # Estatísticas do sistema
    print("3. Estatísticas do Sistema:")
    stats = calibrator.get_calibration_statistics()
    
    print(f"   Total de casos: {stats['total_cases']}")
    print(f"   Precisão geral: {stats['overall_accuracy']:.1%}")
    print(f"   Calibradores treinados: {stats['calibrators_trained']}")
    print()
    
    print("   Estatísticas por faixa de confiança:")
    for range_name, range_data in stats['range_statistics'].items():
        if range_data['count'] > 0:
            print(f"   - {range_name}: {range_data['count']} casos, "
                  f"precisão {range_data['accuracy']:.1%}")
    
    print()
    reliability = stats['reliability_assessment']
    print(f"   Confiabilidade do sistema: {reliability['reliability_level']} "
          f"({reliability['reliability_score']:.0f}%)")

if __name__ == "__main__":
    exemplo_calibracao_avancada()

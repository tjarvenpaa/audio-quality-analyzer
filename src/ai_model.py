"""
AI-malli äänenlaadun arviointiin ja suositusten generointiin
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, List, Tuple, Optional
import numpy as np


class AudioQualityAssessmentModel(nn.Module):
    """
    Transformer-pohjainen malli äänenlaadun arviointiin
    Ottaa embeddings ja DSP-featuret, tuottaa laatuarvion ja suosituksia
    """
    
    def __init__(self,
                 embedding_dim: int = 512,
                 num_heads: int = 8,
                 num_layers: int = 6,
                 dropout: float = 0.1,
                 num_quality_aspects: int = 7):  # clarity, noise, freq balance, DR, loudness, stereo, production
        super().__init__()
        
        self.embedding_dim = embedding_dim
        self.num_quality_aspects = num_quality_aspects
        
        # Positional encoding (optional, for sequence data)
        self.pos_encoding = PositionalEncoding(embedding_dim, dropout)
        
        # Transformer encoder
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=embedding_dim,
            nhead=num_heads,
            dim_feedforward=embedding_dim * 4,
            dropout=dropout,
            batch_first=True
        )
        self.transformer_encoder = nn.TransformerEncoder(encoder_layer, num_layers)
        
        # Quality score heads (one for each aspect)
        self.quality_heads = nn.ModuleDict({
            'clarity': nn.Linear(embedding_dim, 1),
            'noise': nn.Linear(embedding_dim, 1),
            'frequency_balance': nn.Linear(embedding_dim, 1),
            'dynamic_range': nn.Linear(embedding_dim, 1),
            'loudness': nn.Linear(embedding_dim, 1),
            'stereo': nn.Linear(embedding_dim, 1),
            'production_quality': nn.Linear(embedding_dim, 1)
        })
        
        # Overall quality score
        self.overall_head = nn.Linear(embedding_dim, 1)
        
        # Issue detection head (multi-label classification)
        self.issue_detector = nn.Sequential(
            nn.Linear(embedding_dim, 256),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Linear(128, 20)  # 20 possible issues
        )
        
        # Recommendation generator (maps features to recommendation categories)
        self.recommendation_head = nn.Sequential(
            nn.Linear(embedding_dim, 512),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(512, 256),
            nn.ReLU(),
            nn.Linear(256, 30)  # 30 recommendation categories
        )
        
    def forward(self, embeddings: torch.Tensor) -> Dict[str, torch.Tensor]:
        """
        Forward pass
        
        Args:
            embeddings: (batch, seq_len, embedding_dim) or (batch, embedding_dim)
            
        Returns:
            Dictionary with quality scores, issues, and recommendations
        """
        # Handle different input shapes
        if embeddings.dim() == 2:
            embeddings = embeddings.unsqueeze(1)  # Add sequence dimension
        
        # Apply positional encoding
        x = self.pos_encoding(embeddings)
        
        # Transformer encoding
        encoded = self.transformer_encoder(x)
        
        # Take mean over sequence dimension for final representation
        pooled = torch.mean(encoded, dim=1)
        
        # Quality scores (0-100)
        quality_scores = {}
        for aspect, head in self.quality_heads.items():
            score = torch.sigmoid(head(pooled)) * 100
            quality_scores[aspect] = score
        
        # Overall quality
        quality_scores['overall'] = torch.sigmoid(self.overall_head(pooled)) * 100
        
        # Issue detection (probabilities)
        issues = torch.sigmoid(self.issue_detector(pooled))
        
        # Recommendations (scores for each recommendation type)
        recommendations = torch.sigmoid(self.recommendation_head(pooled))
        
        return {
            'quality_scores': quality_scores,
            'issues': issues,
            'recommendations': recommendations,
            'embeddings': pooled
        }


class PositionalEncoding(nn.Module):
    """Positional encoding for transformer"""
    
    def __init__(self, d_model: int, dropout: float = 0.1, max_len: int = 5000):
        super().__init__()
        self.dropout = nn.Dropout(p=dropout)
        
        position = torch.arange(max_len).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2) * (-np.log(10000.0) / d_model))
        pe = torch.zeros(max_len, 1, d_model)
        pe[:, 0, 0::2] = torch.sin(position * div_term)
        pe[:, 0, 1::2] = torch.cos(position * div_term)
        self.register_buffer('pe', pe)
        
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = x + self.pe[:x.size(1)].transpose(0, 1)
        return self.dropout(x)


class RecommendationEngine:
    """
    Generoi konkreettisia parannusehdotuksia analyysin perusteella
    """
    
    # Issue categories
    ISSUE_CATEGORIES = [
        'clipping', 'excessive_noise', 'low_snr', 'dc_offset', 'phase_issues',
        'over_compression', 'under_compression', 'excessive_bass', 'lacking_bass',
        'harsh_highs', 'muddy_mids', 'narrow_stereo', 'wide_stereo', 
        'low_loudness', 'excessive_loudness', 'poor_mono_compatibility',
        'sudden_level_changes', 'frequency_imbalance', 'high_noise_floor', 'artifacts'
    ]
    
    # Recommendation categories
    RECOMMENDATION_CATEGORIES = [
        'reduce_input_gain', 'add_noise_reduction', 'apply_eq_bass_cut',
        'apply_eq_bass_boost', 'apply_eq_treble_cut', 'apply_eq_treble_boost',
        'apply_compression', 'reduce_compression', 'apply_limiting',
        'normalize_loudness', 'increase_loudness', 'decrease_loudness',
        'widen_stereo', 'narrow_stereo', 'fix_phase', 'add_reverb',
        'reduce_reverb', 'apply_de-esser', 'apply_multiband_compression',
        'improve_room_treatment', 'use_better_microphone', 'adjust_mic_placement',
        'apply_spectral_repair', 'use_noise_gate', 'apply_expansion',
        'improve_recording_conditions', 'apply_harmonic_enhancement',
        'apply_saturation', 'improve_gain_staging', 'check_cables'
    ]
    
    def __init__(self):
        self.issue_threshold = 0.5  # Probability threshold for issue detection
        self.recommendation_threshold = 0.4
        
    def generate_recommendations(self,
                                dsp_results: Dict,
                                ai_predictions: Dict) -> Dict:
        """
        Generoi suositukset DSP-analyysin ja AI-ennusteiden perusteella
        
        Args:
            dsp_results: DSP analyzer results
            ai_predictions: AI model predictions
            
        Returns:
            Structured recommendations with priorities
        """
        recommendations = {
            'issues_detected': [],
            'recommendations': [],
            'priority_actions': [],
            'quality_summary': {},
            'improvement_potential': 0.0
        }
        
        # Parse AI predictions
        if 'issues' in ai_predictions:
            issues_tensor = ai_predictions['issues']
            if isinstance(issues_tensor, torch.Tensor):
                issues_probs = issues_tensor.cpu().numpy().flatten()
            else:
                issues_probs = issues_tensor
            
            # Identify detected issues
            for idx, prob in enumerate(issues_probs[:len(self.ISSUE_CATEGORIES)]):
                if prob > self.issue_threshold:
                    issue_name = self.ISSUE_CATEGORIES[idx]
                    recommendations['issues_detected'].append({
                        'issue': issue_name,
                        'confidence': float(prob),
                        'severity': self._assess_severity(issue_name, prob)
                    })
        
        # Generate recommendations based on DSP analysis
        dsp_recommendations = self._generate_dsp_recommendations(dsp_results)
        recommendations['recommendations'].extend(dsp_recommendations)
        
        # Parse AI recommendations
        if 'recommendations' in ai_predictions:
            rec_tensor = ai_predictions['recommendations']
            if isinstance(rec_tensor, torch.Tensor):
                rec_scores = rec_tensor.cpu().numpy().flatten()
            else:
                rec_scores = rec_tensor
            
            for idx, score in enumerate(rec_scores[:len(self.RECOMMENDATION_CATEGORIES)]):
                if score > self.recommendation_threshold:
                    rec_name = self.RECOMMENDATION_CATEGORIES[idx]
                    recommendations['recommendations'].append({
                        'action': rec_name,
                        'priority': float(score),
                        'description': self._get_recommendation_description(rec_name)
                    })
        
        # Sort recommendations by priority
        recommendations['recommendations'] = sorted(
            recommendations['recommendations'],
            key=lambda x: x['priority'],
            reverse=True
        )
        
        # Extract top 5 priority actions
        recommendations['priority_actions'] = [
            r['action'] for r in recommendations['recommendations'][:5]
        ]
        
        # Quality summary
        if 'quality_scores' in ai_predictions:
            for aspect, score in ai_predictions['quality_scores'].items():
                if isinstance(score, torch.Tensor):
                    score = score.item()
                recommendations['quality_summary'][aspect] = {
                    'score': float(score),
                    'rating': self._score_to_rating(score)
                }
        
        # Calculate improvement potential
        recommendations['improvement_potential'] = self._calculate_improvement_potential(
            recommendations['quality_summary']
        )
        
        return recommendations
    
    def _generate_dsp_recommendations(self, dsp_results: Dict) -> List[Dict]:
        """Generate recommendations from DSP analysis"""
        recommendations = []
        
        # Clarity issues
        if 'clarity' in dsp_results:
            if dsp_results['clarity']['score'] < 60:
                recommendations.append({
                    'action': 'improve_clarity',
                    'priority': 0.8,
                    'description': 'Audio clarity is below optimal. Consider better recording conditions or noise reduction.',
                    'specific': f"Spectral flatness: {dsp_results['clarity'].get('spectral_flatness_mean', 'N/A')}"
                })
        
        # Noise issues
        if 'noise' in dsp_results:
            snr = dsp_results['noise'].get('snr_db', 0)
            if snr < 25:
                recommendations.append({
                    'action': 'add_noise_reduction',
                    'priority': 0.9,
                    'description': f'High noise level detected (SNR: {snr:.1f} dB). Apply noise reduction.',
                    'specific': dsp_results['noise'].get('issues', [])
                })
        
        # Frequency balance
        if 'frequency_balance' in dsp_results:
            freq_recs = dsp_results['frequency_balance'].get('recommendations', [])
            for rec in freq_recs:
                if 'good' not in rec.lower():
                    recommendations.append({
                        'action': 'equalization',
                        'priority': 0.7,
                        'description': rec,
                        'specific': dsp_results['frequency_balance'].get('dominant_range', '')
                    })
        
        # Dynamic range
        if 'dynamic_range' in dsp_results:
            dr = dsp_results['dynamic_range'].get('dynamic_range_db', 0)
            if dr < 6:
                recommendations.append({
                    'action': 'reduce_compression',
                    'priority': 0.85,
                    'description': f'Audio is over-compressed (DR: {dr:.1f} dB). Reduce compression or limiting.'
                })
            elif dr > 20:
                recommendations.append({
                    'action': 'apply_compression',
                    'priority': 0.6,
                    'description': f'Wide dynamic range (DR: {dr:.1f} dB). Consider gentle compression for consistency.'
                })
        
        # Loudness
        if 'loudness' in dsp_results:
            if dsp_results['loudness'].get('needs_adjustment', False):
                deviation = dsp_results['loudness'].get('deviation_from_target', 0)
                target = dsp_results['loudness'].get('target_lufs', -16)
                current = dsp_results['loudness'].get('integrated_loudness_lufs', 0)
                
                if current < target:
                    recommendations.append({
                        'action': 'increase_loudness',
                        'priority': 0.75,
                        'description': f'Increase loudness by ~{abs(deviation):.1f} LU to reach target ({target} LUFS)'
                    })
                else:
                    recommendations.append({
                        'action': 'decrease_loudness',
                        'priority': 0.75,
                        'description': f'Reduce loudness by ~{abs(deviation):.1f} LU to reach target ({target} LUFS)'
                    })
        
        # Stereo issues
        if 'stereo' in dsp_results and dsp_results['stereo'].get('is_stereo', False):
            issues = dsp_results['stereo'].get('issues', [])
            for issue in issues:
                if 'phase' in issue.lower():
                    recommendations.append({
                        'action': 'fix_phase',
                        'priority': 0.95,
                        'description': 'Phase cancellation detected. Check stereo phase relationship.',
                        'specific': issue
                    })
                elif 'imbalance' in issue.lower():
                    recommendations.append({
                        'action': 'balance_channels',
                        'priority': 0.7,
                        'description': issue
                    })
        
        # Production quality issues
        if 'production_quality' in dsp_results:
            issues = dsp_results['production_quality'].get('issues', [])
            for issue in issues:
                if 'clipping' in issue.lower():
                    recommendations.append({
                        'action': 'reduce_input_gain',
                        'priority': 1.0,
                        'description': 'Clipping detected! Reduce input gain or apply limiting.',
                        'specific': issue
                    })
                elif 'dc offset' in issue.lower():
                    recommendations.append({
                        'action': 'remove_dc_offset',
                        'priority': 0.6,
                        'description': 'DC offset present. Apply DC offset removal filter.'
                    })
        
        return recommendations
    
    def _assess_severity(self, issue_name: str, probability: float) -> str:
        """Assess issue severity"""
        if probability > 0.8:
            return 'critical'
        elif probability > 0.6:
            return 'high'
        elif probability > 0.4:
            return 'medium'
        else:
            return 'low'
    
    def _get_recommendation_description(self, rec_name: str) -> str:
        """Get human-readable description for recommendation"""
        descriptions = {
            'reduce_input_gain': 'Lower the input gain to prevent clipping and distortion',
            'add_noise_reduction': 'Apply noise reduction to clean up background noise',
            'apply_eq_bass_cut': 'Reduce low frequencies to clean up muddiness',
            'apply_eq_bass_boost': 'Boost low frequencies for more warmth and body',
            'apply_eq_treble_cut': 'Reduce high frequencies to tame harshness',
            'apply_eq_treble_boost': 'Boost high frequencies for more clarity and air',
            'apply_compression': 'Use compression to control dynamic range',
            'reduce_compression': 'Reduce compression to restore dynamics',
            'normalize_loudness': 'Normalize to broadcast loudness standards (-16 LUFS)',
            'widen_stereo': 'Increase stereo width for more spaciousness',
            'narrow_stereo': 'Reduce stereo width for better mono compatibility',
            'fix_phase': 'Correct phase issues between channels',
            'use_noise_gate': 'Apply a noise gate to reduce ambient noise during silence'
        }
        return descriptions.get(rec_name, f'Apply {rec_name.replace("_", " ")}')
    
    def _score_to_rating(self, score: float) -> str:
        """Convert numeric score to rating"""
        if score >= 90:
            return 'Excellent'
        elif score >= 75:
            return 'Good'
        elif score >= 60:
            return 'Fair'
        elif score >= 40:
            return 'Poor'
        else:
            return 'Very Poor'
    
    def _calculate_improvement_potential(self, quality_summary: Dict) -> float:
        """Calculate how much the audio can be improved"""
        if not quality_summary:
            return 0.0
        
        scores = [v['score'] for v in quality_summary.values() if 'score' in v]
        if not scores:
            return 0.0
        
        avg_score = np.mean(scores)
        # Improvement potential = how far from perfect (100)
        potential = (100 - avg_score) / 100.0
        return float(potential)


def format_analysis_report(dsp_results: Dict, 
                           ai_predictions: Dict,
                           recommendations: Dict,
                           filename: str) -> str:
    """
    Muotoile kattava analysiraportti
    
    Returns:
        Formatted string report
    """
    report = []
    report.append("=" * 80)
    report.append(f"ÄÄNENLAATU-ANALYYSI: {filename}")
    report.append("=" * 80)
    report.append("")
    
    # Quality Summary
    report.append("LAATUARVIOT:")
    report.append("-" * 40)
    if 'quality_summary' in recommendations:
        for aspect, data in recommendations['quality_summary'].items():
            score = data['score']
            rating = data['rating']
            report.append(f"  {aspect.replace('_', ' ').title():.<30} {score:>5.1f}/100 ({rating})")
    report.append("")
    
    # Issues Detected
    if recommendations.get('issues_detected'):
        report.append("HAVAITUT ONGELMAT:")
        report.append("-" * 40)
        for issue in recommendations['issues_detected']:
            report.append(f"  [{issue['severity'].upper()}] {issue['issue'].replace('_', ' ').title()}")
            report.append(f"      Varmuus: {issue['confidence']*100:.0f}%")
        report.append("")
    
    # Recommendations
    if recommendations.get('recommendations'):
        report.append("PARANNUSEHDOTUKSET (tärkeysjärjestyksessä):")
        report.append("-" * 40)
        for i, rec in enumerate(recommendations['recommendations'][:10], 1):
            report.append(f"  {i}. {rec.get('description', rec['action'])}")
            if 'specific' in rec and rec['specific']:
                report.append(f"      Lisätiedot: {rec['specific']}")
        report.append("")
    
    # Detailed DSP Analysis
    report.append("YKSITYISKOHTAINEN TEKNINEN ANALYYSI:")
    report.append("-" * 40)
    
    if 'loudness' in dsp_results:
        l = dsp_results['loudness']
        report.append(f"  Loudness: {l.get('integrated_loudness_lufs', 'N/A'):.1f} LUFS")
        report.append(f"  Peak: {l.get('peak_db', 'N/A'):.1f} dB")
        report.append(f"  Loudness Range: {l.get('loudness_range_lu', 'N/A'):.1f} LU")
        report.append("")
    
    if 'noise' in dsp_results:
        n = dsp_results['noise']
        report.append(f"  Signal-to-Noise Ratio: {n.get('snr_db', 'N/A'):.1f} dB")
        report.append(f"  Noise Floor: {n.get('noise_floor_db', 'N/A'):.1f} dB")
        report.append("")
    
    if 'dynamic_range' in dsp_results:
        dr = dsp_results['dynamic_range']
        report.append(f"  Dynamic Range: {dr.get('dynamic_range_db', 'N/A'):.1f} dB")
        report.append(f"  Crest Factor: {dr.get('crest_factor_db', 'N/A'):.1f} dB")
        report.append("")
    
    if 'stereo' in dsp_results and dsp_results['stereo'].get('is_stereo'):
        s = dsp_results['stereo']
        report.append(f"  Phase Correlation: {s.get('phase_correlation', 'N/A'):.2f}")
        report.append(f"  Stereo Width: {s.get('stereo_width', 'N/A'):.2f}")
        report.append(f"  Mono Compatibility: {s.get('mono_compatibility', 'N/A'):.2f}")
        report.append("")
    
    # Improvement Potential
    if 'improvement_potential' in recommendations:
        potential = recommendations['improvement_potential'] * 100
        report.append(f"PARANNUSPOTENTIAALI: {potential:.0f}%")
        report.append("")
    
    report.append("=" * 80)
    
    return "\n".join(report)


if __name__ == "__main__":
    # Test model
    print("Testing Audio Quality Assessment Model...")
    
    model = AudioQualityAssessmentModel(embedding_dim=512)
    
    # Dummy input
    batch_size = 2
    embeddings = torch.randn(batch_size, 512)
    
    with torch.no_grad():
        predictions = model(embeddings)
    
    print("\nModel predictions:")
    print(f"  Quality scores: {list(predictions['quality_scores'].keys())}")
    print(f"  Issues shape: {predictions['issues'].shape}")
    print(f"  Recommendations shape: {predictions['recommendations'].shape}")
    
    print("\n✓ AI Model test passed!")

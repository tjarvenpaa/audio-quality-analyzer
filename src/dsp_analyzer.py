"""
Laajennetut DSP-analyysit äänenlaadun arviointiin
"""

import numpy as np
import librosa
import pyloudnorm as pyln
from scipy import signal
from typing import Dict, Tuple, Optional
import torch


class DSPAnalyzer:
    """Kattava DSP-analyysi äänensignaaleille"""
    
    def __init__(self, sample_rate: int = 44100, config: Optional[dict] = None):
        self.sr = sample_rate
        self.config = config or {}
        
    def analyze_full(self, audio: np.ndarray, stereo: bool = False) -> Dict:
        """
        Suorittaa täydellinen analyysi äänisignaalille
        
        Args:
            audio: Äänisignaali (mono tai stereo)
            stereo: Onko signaali stereo
            
        Returns:
            Sanakirja joka sisältää kaikki analyysitulokset
        """
        results = {}
        
        # Varmista että audio on oikessa muodossa
        if audio.ndim == 1:
            y_mono = audio
            y_stereo = None
        else:
            y_mono = librosa.to_mono(audio)
            y_stereo = audio if stereo else None
            
        # 1. Clarity Analysis - Selkeysanalyysi
        results['clarity'] = self.analyze_clarity(y_mono)
        
        # 2. Noise Analysis - Kohinaanalyysi
        results['noise'] = self.analyze_noise(y_mono)
        
        # 3. Frequency Balance - Taajuustasapaino
        results['frequency_balance'] = self.analyze_frequency_balance(y_mono)
        
        # 4. Dynamic Range - Dynaaminen alue
        results['dynamic_range'] = self.analyze_dynamic_range(y_mono)
        
        # 5. Loudness - Äänenvoimakkuus
        results['loudness'] = self.analyze_loudness(audio if audio.ndim > 1 else y_mono)
        
        # 6. Stereo Analysis - Stereoanalyysi (jos stereo)
        if y_stereo is not None and y_stereo.shape[0] == 2:
            results['stereo'] = self.analyze_stereo(y_stereo)
        else:
            results['stereo'] = {'is_stereo': False}
            
        # 7. Production Quality - Tuotannon laatu
        results['production_quality'] = self.analyze_production_quality(y_mono)
        
        return results
    
    def analyze_clarity(self, y: np.ndarray) -> Dict:
        """
        Analysoi äänen selkeys
        - Spectral clarity
        - Transient response
        - Harmonic-to-noise ratio
        """
        # Spectral centroid - korkeampi arvo = kirkkaampi ääni
        spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=self.sr)[0]
        
        # Spectral contrast - ero peaks ja valleys välillä
        spectral_contrast = librosa.feature.spectral_contrast(y=y, sr=self.sr)
        
        # Zero crossing rate - nopeat muutokset signaalissa
        zcr = librosa.feature.zero_crossing_rate(y)[0]
        
        # Spectral flatness - mittaa äänen "kohinaisuutta"
        spectral_flatness = librosa.feature.spectral_flatness(y=y)[0]
        
        # THD+N arvio (Total Harmonic Distortion + Noise)
        f0 = librosa.yin(y, fmin=50, fmax=500, sr=self.sr)
        harmonicity = np.nanmean(1.0 / (1.0 + np.abs(f0)))
        
        clarity_score = self._calculate_clarity_score(
            spectral_centroid, spectral_contrast, zcr, spectral_flatness, harmonicity
        )
        
        return {
            'score': float(clarity_score),
            'spectral_centroid_mean': float(np.mean(spectral_centroid)),
            'spectral_centroid_std': float(np.std(spectral_centroid)),
            'spectral_contrast_mean': float(np.mean(spectral_contrast)),
            'zero_crossing_rate_mean': float(np.mean(zcr)),
            'spectral_flatness_mean': float(np.mean(spectral_flatness)),
            'harmonicity': float(harmonicity),
            'rating': self._rate_clarity(clarity_score)
        }
    
    def analyze_noise(self, y: np.ndarray) -> Dict:
        """
        Analysoi taustakohinan taso ja laatu
        - SNR (Signal-to-Noise Ratio)
        - Noise floor
        - Spectral noise profile
        """
        # RMS energia
        rms = librosa.feature.rms(y=y)[0]
        
        # Signal ja noise erottelu (yksinkertaistettu)
        rms_sorted = np.sort(rms)
        noise_threshold_idx = int(len(rms_sorted) * 0.1)  # Alin 10%
        noise_rms = np.mean(rms_sorted[:noise_threshold_idx])
        signal_rms = np.mean(rms_sorted[noise_threshold_idx:])
        
        # SNR laskenta
        snr_db = 20 * np.log10((signal_rms / (noise_rms + 1e-10)))
        
        # Noise floor dB
        noise_floor_db = 20 * np.log10(noise_rms + 1e-10)
        
        # Spectral noise analysis
        stft = librosa.stft(y)
        noise_profile = self._estimate_noise_profile(np.abs(stft))
        
        noise_score = self._calculate_noise_score(snr_db, noise_floor_db)
        
        return {
            'score': float(noise_score),
            'snr_db': float(snr_db),
            'noise_floor_db': float(noise_floor_db),
            'signal_rms': float(signal_rms),
            'noise_rms': float(noise_rms),
            'noise_variability': float(np.std(noise_profile)),
            'rating': self._rate_noise(snr_db),
            'issues': self._identify_noise_issues(snr_db, noise_floor_db)
        }
    
    def analyze_frequency_balance(self, y: np.ndarray) -> Dict:
        """
        Analysoi taajuuksien tasapaino eri kaistalla
        """
        # Määrittele taajuuskaistat
        bands = self.config.get('frequency_bands', {
            'sub_bass': (20, 60),
            'bass': (60, 250),
            'low_mids': (250, 500),
            'mids': (500, 2000),
            'high_mids': (2000, 4000),
            'presence': (4000, 6000),
            'brilliance': (6000, 20000)
        })
        
        # Laske energia per kaista
        stft = librosa.stft(y)
        freqs = librosa.fft_frequencies(sr=self.sr)
        
        band_energies = {}
        for band_name, (f_min, f_max) in bands.items():
            # Löydä indeksit tälle taajuuskaistalle
            band_mask = (freqs >= f_min) & (freqs <= f_max)
            band_energy = np.mean(np.abs(stft[band_mask, :])**2)
            band_energies[band_name] = float(20 * np.log10(band_energy + 1e-10))
        
        # Laske tasapainoindeksi (pienempi varianssi = tasapainoisempi)
        energy_values = list(band_energies.values())
        balance_variance = np.var(energy_values)
        balance_score = self._calculate_balance_score(balance_variance)
        
        # Spectral rolloff - taajuus jossa 85% energiasta on alapuolella
        rolloff = librosa.feature.spectral_rolloff(y=y, sr=self.sr)[0]
        
        return {
            'score': float(balance_score),
            'band_energies_db': band_energies,
            'balance_variance': float(balance_variance),
            'spectral_rolloff_mean': float(np.mean(rolloff)),
            'rating': self._rate_frequency_balance(balance_score),
            'dominant_range': self._identify_dominant_range(band_energies),
            'recommendations': self._frequency_balance_recommendations(band_energies)
        }
    
    def analyze_dynamic_range(self, y: np.ndarray) -> Dict:
        """
        Analysoi dynaaminen alue
        - Peak vs RMS ratio
        - Crest factor
        - Dynamic variation over time
        """
        # Peak level
        peak_level = np.max(np.abs(y))
        peak_db = 20 * np.log10(peak_level + 1e-10)
        
        # RMS level
        rms = np.sqrt(np.mean(y**2))
        rms_db = 20 * np.log10(rms + 1e-10)
        
        # Crest factor (peak-to-RMS ratio)
        crest_factor_db = peak_db - rms_db
        
        # Dynamic range (DR meter standard)
        # Käytä RMS frame-based analysis
        rms_frames = librosa.feature.rms(y=y, frame_length=self.sr//10)[0]
        rms_frames_db = 20 * np.log10(rms_frames + 1e-10)
        
        # DR = (Peak - Mean of top 20% RMS levels)
        sorted_rms = np.sort(rms_frames_db)
        top_20_idx = int(len(sorted_rms) * 0.8)
        avg_top_20 = np.mean(sorted_rms[top_20_idx:])
        
        dynamic_range_db = peak_db - avg_top_20
        
        # PLR (Peak to Loudness Ratio) käyttäen ITU-R BS.1770 loudness
        meter = pyln.Meter(self.sr)
        loudness = meter.integrated_loudness(y.reshape(-1, 1))
        plr = peak_db - loudness
        
        dr_score = self._calculate_dr_score(dynamic_range_db, crest_factor_db)
        
        return {
            'score': float(dr_score),
            'dynamic_range_db': float(dynamic_range_db),
            'crest_factor_db': float(crest_factor_db),
            'peak_db': float(peak_db),
            'rms_db': float(rms_db),
            'plr': float(plr),
            'rating': self._rate_dynamic_range(dynamic_range_db),
            'compression_detected': crest_factor_db < 8.0,
            'issues': self._identify_dr_issues(dynamic_range_db, crest_factor_db)
        }
    
    def analyze_loudness(self, y: np.ndarray) -> Dict:
        """
        ITU-R BS.1770 loudness analyysi
        """
        # Varmista oikea muoto pyloudnormille
        if y.ndim == 1:
            y_input = y.reshape(-1, 1)
        else:
            y_input = y.T
            
        meter = pyln.Meter(self.sr)
        
        # Integrated loudness
        loudness = meter.integrated_loudness(y_input)
        
        # True peak
        peak_db = 20 * np.log10(np.max(np.abs(y)) + 1e-10)
        
        # Loudness range (LRA)
        # Simplified version - voisi käyttää EBU R128 standardia
        rms_frames = librosa.feature.rms(y=y if y.ndim == 1 else librosa.to_mono(y))[0]
        rms_db = 20 * np.log10(rms_frames + 1e-10)
        loudness_range = np.percentile(rms_db, 95) - np.percentile(rms_db, 10)
        
        target_lufs = self.config.get('target_lufs', -16.0)
        loudness_score = self._calculate_loudness_score(loudness, target_lufs)
        
        return {
            'score': float(loudness_score),
            'integrated_loudness_lufs': float(loudness),
            'peak_db': float(peak_db),
            'loudness_range_lu': float(loudness_range),
            'target_lufs': float(target_lufs),
            'deviation_from_target': float(abs(loudness - target_lufs)),
            'rating': self._rate_loudness(loudness, target_lufs),
            'needs_adjustment': abs(loudness - target_lufs) > 2.0
        }
    
    def analyze_stereo(self, y_stereo: np.ndarray) -> Dict:
        """
        Analysoi stereo-ominaisuudet
        - Stereo width
        - Phase correlation
        - Channel balance
        - Mono compatibility
        """
        left = y_stereo[0]
        right = y_stereo[1]
        
        # Phase correlation
        correlation = np.corrcoef(left, right)[0, 1]
        
        # Channel balance (L vs R RMS)
        rms_left = np.sqrt(np.mean(left**2))
        rms_right = np.sqrt(np.mean(right**2))
        balance_db = 20 * np.log10((rms_left / (rms_right + 1e-10)))
        
        # Stereo width estimation (käyttäen Mid/Side analyysiä)
        mid = (left + right) / 2
        side = (left - right) / 2
        
        rms_mid = np.sqrt(np.mean(mid**2))
        rms_side = np.sqrt(np.mean(side**2))
        stereo_width = rms_side / (rms_mid + 1e-10)
        
        # Mono compatibility (tarkista phase issues)
        mono = librosa.to_mono(y_stereo)
        rms_mono = np.sqrt(np.mean(mono**2))
        rms_stereo = np.sqrt(np.mean(y_stereo**2))
        mono_compatibility = rms_mono / (rms_stereo + 1e-10)
        
        stereo_score = self._calculate_stereo_score(correlation, stereo_width, mono_compatibility)
        
        return {
            'is_stereo': True,
            'score': float(stereo_score),
            'phase_correlation': float(correlation),
            'channel_balance_db': float(balance_db),
            'stereo_width': float(stereo_width),
            'mono_compatibility': float(mono_compatibility),
            'rating': self._rate_stereo(correlation),
            'issues': self._identify_stereo_issues(correlation, balance_db, mono_compatibility)
        }
    
    def analyze_production_quality(self, y: np.ndarray) -> Dict:
        """
        Yleiset tuotannon laatuindikaattorit
        - Clipping detection
        - DC offset
        - Silence detection
        - Artifacts detection
        """
        # Clipping detection
        clipping_threshold = 0.99
        clipped_samples = np.sum(np.abs(y) >= clipping_threshold)
        clipping_percentage = (clipped_samples / len(y)) * 100
        
        # DC offset
        dc_offset = np.mean(y)
        
        # Silence detection (alle -60dB)
        silence_threshold_db = -60
        silence_threshold_linear = 10**(silence_threshold_db / 20)
        silent_samples = np.sum(np.abs(y) < silence_threshold_linear)
        silence_percentage = (silent_samples / len(y)) * 100
        
        # Bit depth estimation (effective bits)
        effective_bits = self._estimate_bit_depth(y)
        
        # Detect sudden level changes (possible edits/artifacts)
        rms_frames = librosa.feature.rms(y=y, frame_length=2048)[0]
        rms_diff = np.abs(np.diff(20 * np.log10(rms_frames + 1e-10)))
        sudden_changes = np.sum(rms_diff > 10)  # >10dB muutokset
        
        quality_score = self._calculate_production_quality_score(
            clipping_percentage, dc_offset, effective_bits, sudden_changes
        )
        
        return {
            'score': float(quality_score),
            'clipping_percentage': float(clipping_percentage),
            'dc_offset': float(dc_offset),
            'silence_percentage': float(silence_percentage),
            'effective_bit_depth': float(effective_bits),
            'sudden_changes_count': int(sudden_changes),
            'rating': self._rate_production_quality(quality_score),
            'issues': self._identify_production_issues(
                clipping_percentage, dc_offset, sudden_changes
            )
        }
    
    # Helper methods for scoring
    def _calculate_clarity_score(self, centroid, contrast, zcr, flatness, harmonicity):
        """Laske selkeyspistemäärä 0-100"""
        # Normalisoi ja yhdistä eri metriikat
        score = 50.0  # Base score
        
        # Spectral contrast korkeampi = parempi selkeys
        score += np.clip(np.mean(contrast) * 2, -20, 20)
        
        # Harmonicity
        score += harmonicity * 30
        
        # Spectral flatness matalampi = vähemmän kohinaa
        score -= np.mean(flatness) * 50
        
        return np.clip(score, 0, 100)
    
    def _calculate_noise_score(self, snr_db, noise_floor_db):
        """Laske kohinapistemäärä 0-100"""
        # SNR > 45dB = excellent, 25dB = acceptable, <20dB = poor
        if snr_db >= 45:
            score = 100
        elif snr_db >= 25:
            score = 50 + ((snr_db - 25) / 20) * 50
        else:
            score = (snr_db / 25) * 50
            
        return np.clip(score, 0, 100)
    
    def _calculate_balance_score(self, variance):
        """Laske tasapainopistemäärä 0-100"""
        # Matalampi varianssi = parempi tasapaino
        # Typical variance 50-200, ideal <50
        score = 100 - np.clip(variance / 2, 0, 100)
        return score
    
    def _calculate_dr_score(self, dr_db, crest_factor):
        """Laske dynaamisen alueen pistemäärä 0-100"""
        # Ideal DR 8-20dB, crest factor 10-20dB
        ideal_dr = 12
        dr_deviation = abs(dr_db - ideal_dr)
        
        score = 100 - (dr_deviation * 5)
        return np.clip(score, 0, 100)
    
    def _calculate_loudness_score(self, loudness, target):
        """Laske äänenvoimakkuuspistemäärä 0-100"""
        deviation = abs(loudness - target)
        
        if deviation <= 1.0:
            score = 100
        elif deviation <= 2.0:
            score = 80
        elif deviation <= 3.0:
            score = 60
        else:
            score = max(0, 60 - (deviation - 3) * 10)
            
        return score
    
    def _calculate_stereo_score(self, correlation, width, mono_compat):
        """Laske stereokohtapistemäärä 0-100"""
        score = 50
        
        # Ideal correlation 0.3-0.7
        if 0.3 <= correlation <= 0.7:
            score += 25
        elif correlation < 0:  # Phase issues
            score -= 30
            
        # Stereo width
        if 0.3 <= width <= 1.5:
            score += 15
            
        # Mono compatibility
        if mono_compat > 0.9:
            score += 10
            
        return np.clip(score, 0, 100)
    
    def _calculate_production_quality_score(self, clipping, dc_offset, bits, changes):
        """Laske tuotannon laatupistemäärä 0-100"""
        score = 100
        
        # Clipping penalty
        if clipping > 0:
            score -= min(clipping * 20, 50)
            
        # DC offset penalty
        if abs(dc_offset) > 0.01:
            score -= 10
            
        # Bit depth bonus
        if bits >= 16:
            score += 0
        else:
            score -= (16 - bits) * 5
            
        # Sudden changes penalty
        score -= min(changes * 2, 30)
        
        return np.clip(score, 0, 100)
    
    def _estimate_noise_profile(self, stft_mag):
        """Estimoi kohinaprofiili"""
        # Ota minimum per taajuus aikaikkunasta
        return np.min(stft_mag, axis=1)
    
    def _estimate_bit_depth(self, y):
        """Arvioi efektiivinen bittisyvyys"""
        # Laske uniikkien arvojen määrä (yksinkertaistettu)
        unique_ratio = len(np.unique(y)) / len(y)
        estimated_bits = np.log2(len(np.unique(y))) if len(np.unique(y)) > 1 else 1
        return min(estimated_bits, 24)
    
    # Rating methods
    def _rate_clarity(self, score):
        if score >= 80: return "Excellent"
        elif score >= 60: return "Good"
        elif score >= 40: return "Fair"
        else: return "Poor"
    
    def _rate_noise(self, snr_db):
        if snr_db >= 45: return "Excellent"
        elif snr_db >= 35: return "Good"
        elif snr_db >= 25: return "Fair"
        else: return "Poor"
    
    def _rate_frequency_balance(self, score):
        if score >= 75: return "Well-balanced"
        elif score >= 50: return "Acceptable"
        else: return "Unbalanced"
    
    def _rate_dynamic_range(self, dr_db):
        if 8 <= dr_db <= 18: return "Excellent"
        elif 6 <= dr_db <= 20: return "Good"
        elif dr_db < 6: return "Over-compressed"
        else: return "Excessive"
    
    def _rate_loudness(self, loudness, target):
        deviation = abs(loudness - target)
        if deviation <= 1.0: return "Perfect"
        elif deviation <= 2.0: return "Good"
        elif deviation <= 3.0: return "Acceptable"
        else: return "Needs adjustment"
    
    def _rate_stereo(self, correlation):
        if 0.3 <= correlation <= 0.7: return "Excellent"
        elif 0 <= correlation < 0.3: return "Wide"
        elif 0.7 < correlation <= 1.0: return "Narrow"
        else: return "Phase issues"
    
    def _rate_production_quality(self, score):
        if score >= 90: return "Professional"
        elif score >= 70: return "Good"
        elif score >= 50: return "Acceptable"
        else: return "Poor"
    
    # Issue identification
    def _identify_noise_issues(self, snr_db, noise_floor_db):
        issues = []
        if snr_db < 25:
            issues.append("Low SNR - significant background noise")
        if noise_floor_db > -50:
            issues.append("High noise floor")
        return issues
    
    def _identify_dr_issues(self, dr_db, crest_factor):
        issues = []
        if dr_db < 6:
            issues.append("Over-compressed - limited dynamic range")
        if crest_factor < 8:
            issues.append("Heavy limiting detected")
        if dr_db > 20:
            issues.append("Excessive dynamic range - may need compression")
        return issues
    
    def _identify_stereo_issues(self, correlation, balance_db, mono_compat):
        issues = []
        if correlation < 0:
            issues.append("Phase cancellation detected - mono incompatible")
        if abs(balance_db) > 3:
            issues.append("Significant L/R imbalance")
        if mono_compat < 0.8:
            issues.append("Poor mono compatibility")
        return issues
    
    def _identify_production_issues(self, clipping, dc_offset, changes):
        issues = []
        if clipping > 0:
            issues.append(f"Clipping detected ({clipping:.2f}% of samples)")
        if abs(dc_offset) > 0.01:
            issues.append("DC offset present")
        if changes > 10:
            issues.append("Many sudden level changes detected")
        return issues
    
    def _identify_dominant_range(self, band_energies):
        """Tunnista dominoiva taajuusalue"""
        max_band = max(band_energies, key=band_energies.get)
        return max_band
    
    def _frequency_balance_recommendations(self, band_energies):
        """Anna suositukset taajuustasapainon parantamiseksi"""
        recommendations = []
        
        avg_energy = np.mean(list(band_energies.values()))
        
        for band, energy in band_energies.items():
            deviation = energy - avg_energy
            if deviation > 6:
                recommendations.append(f"Reduce {band} by ~{deviation:.1f} dB")
            elif deviation < -6:
                recommendations.append(f"Boost {band} by ~{abs(deviation):.1f} dB")
                
        return recommendations if recommendations else ["Frequency balance is good"]

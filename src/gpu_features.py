"""
GPU-kiihdytetty feature extraction PyTorchilla
"""

import torch
import torch.nn as nn
import torchaudio
import torchaudio.transforms as T
import numpy as np
from typing import Dict, Optional, Tuple


class GPUFeatureExtractor(nn.Module):
    """
    GPU-kiihdytetty ääniominaisuuksien ekstraktori
    Käyttää PyTorchia ja torchaudiota
    """
    
    def __init__(self, 
                 sample_rate: int = 44100,
                 n_fft: int = 2048,
                 hop_length: int = 512,
                 n_mels: int = 128,
                 n_mfcc: int = 40,
                 device: str = 'cuda'):
        super().__init__()
        
        self.sample_rate = sample_rate
        self.n_fft = n_fft
        self.hop_length = hop_length
        self.n_mels = n_mels
        self.n_mfcc = n_mfcc
        self.device = torch.device(device if torch.cuda.is_available() else 'cpu')
        
        # Määrittele transformaatiot (nämä ajetaan GPU:lla)
        self.mel_spectrogram = T.MelSpectrogram(
            sample_rate=sample_rate,
            n_fft=n_fft,
            hop_length=hop_length,
            n_mels=n_mels,
            power=2.0
        ).to(self.device)
        
        self.mfcc_transform = T.MFCC(
            sample_rate=sample_rate,
            n_mfcc=n_mfcc,
            melkwargs={
                'n_fft': n_fft,
                'hop_length': hop_length,
                'n_mels': n_mels
            }
        ).to(self.device)
        
        self.spectrogram = T.Spectrogram(
            n_fft=n_fft,
            hop_length=hop_length,
            power=2.0
        ).to(self.device)
        
        # AmplitudeToDB muunnos
        self.amplitude_to_db = T.AmplitudeToDB().to(self.device)
        
        print(f"FeatureExtractor initialized on device: {self.device}")
    
    def extract_all_features(self, waveform: torch.Tensor) -> Dict[str, torch.Tensor]:
        """
        Ekstraktoi kaikki ominaisuudet äänisignaalista
        
        Args:
            waveform: Audio tensor, shape (channels, samples) or (samples,)
            
        Returns:
            Dictionary of extracted features
        """
        # Varmista että waveform on GPU:lla ja oikeassa muodossa
        if waveform.dim() == 1:
            waveform = waveform.unsqueeze(0)  # (samples,) -> (1, samples)
            
        waveform = waveform.to(self.device)
        
        features = {}
        
        # 1. Mel-spectrogram
        mel_spec = self.mel_spectrogram(waveform)
        mel_spec_db = self.amplitude_to_db(mel_spec)
        features['mel_spectrogram'] = mel_spec_db
        features['mel_spectrogram_mean'] = torch.mean(mel_spec_db, dim=-1)
        features['mel_spectrogram_std'] = torch.std(mel_spec_db, dim=-1)
        
        # 2. MFCC (Mel-frequency cepstral coefficients)
        mfcc = self.mfcc_transform(waveform)
        features['mfcc'] = mfcc
        features['mfcc_mean'] = torch.mean(mfcc, dim=-1)
        features['mfcc_std'] = torch.std(mfcc, dim=-1)
        
        # 3. Spectrogram
        spec = self.spectrogram(waveform)
        spec_db = self.amplitude_to_db(spec)
        features['spectrogram'] = spec_db
        
        # 4. Spectral Centroid (GPU-accelerated)
        features['spectral_centroid'] = self._compute_spectral_centroid(spec)
        
        # 5. Spectral Bandwidth
        features['spectral_bandwidth'] = self._compute_spectral_bandwidth(spec)
        
        # 6. Spectral Rolloff
        features['spectral_rolloff'] = self._compute_spectral_rolloff(spec)
        
        # 7. Zero Crossing Rate
        features['zero_crossing_rate'] = self._compute_zcr(waveform)
        
        # 8. RMS Energy
        features['rms_energy'] = self._compute_rms(waveform)
        
        # 9. Spectral Contrast
        features['spectral_contrast'] = self._compute_spectral_contrast(mel_spec)
        
        # 10. Chroma features
        features['chroma'] = self._compute_chroma(waveform)
        
        return features
    
    def _compute_spectral_centroid(self, spectrogram: torch.Tensor) -> torch.Tensor:
        """Laske spectral centroid GPU:lla"""
        freqs = torch.linspace(0, self.sample_rate / 2, spectrogram.shape[1], device=self.device)
        freqs = freqs.unsqueeze(0).unsqueeze(-1)  # (1, freq_bins, 1)
        
        # Weighted average of frequencies
        weighted_sum = torch.sum(spectrogram * freqs, dim=1)
        total_energy = torch.sum(spectrogram, dim=1) + 1e-10
        
        centroid = weighted_sum / total_energy
        return centroid
    
    def _compute_spectral_bandwidth(self, spectrogram: torch.Tensor) -> torch.Tensor:
        """Laske spectral bandwidth GPU:lla"""
        freqs = torch.linspace(0, self.sample_rate / 2, spectrogram.shape[1], device=self.device)
        freqs = freqs.unsqueeze(0).unsqueeze(-1)
        
        # Centroid
        centroid = self._compute_spectral_centroid(spectrogram).unsqueeze(1)
        
        # Bandwidth as weighted standard deviation
        deviation_sq = (freqs - centroid) ** 2
        weighted_dev = torch.sum(spectrogram * deviation_sq, dim=1)
        total_energy = torch.sum(spectrogram, dim=1) + 1e-10
        
        bandwidth = torch.sqrt(weighted_dev / total_energy)
        return bandwidth
    
    def _compute_spectral_rolloff(self, spectrogram: torch.Tensor, rolloff_percent: float = 0.85) -> torch.Tensor:
        """Laske spectral rolloff GPU:lla"""
        cumulative_sum = torch.cumsum(spectrogram, dim=1)
        total_energy = cumulative_sum[:, -1:, :]
        
        # Find frequency where cumulative energy reaches rolloff_percent
        threshold = rolloff_percent * total_energy
        rolloff_idx = torch.searchsorted(cumulative_sum.transpose(1, 2).contiguous(), 
                                        threshold.transpose(1, 2).contiguous())
        
        # Convert index to frequency
        freqs = torch.linspace(0, self.sample_rate / 2, spectrogram.shape[1], device=self.device)
        rolloff_freq = freqs[rolloff_idx.clamp(0, len(freqs) - 1)]
        
        return rolloff_freq
    
    def _compute_zcr(self, waveform: torch.Tensor) -> torch.Tensor:
        """Laske zero crossing rate GPU:lla"""
        # Sign changes
        signs = torch.sign(waveform)
        sign_changes = torch.abs(torch.diff(signs, dim=-1))
        
        # Frame-based ZCR
        frame_length = self.hop_length
        num_frames = waveform.shape[-1] // frame_length
        
        if num_frames == 0:
            return torch.zeros(waveform.shape[0], 1, device=self.device)
        
        # Reshape to frames
        trimmed_length = num_frames * frame_length
        sign_changes_trimmed = sign_changes[..., :trimmed_length]
        frames = sign_changes_trimmed.reshape(waveform.shape[0], num_frames, frame_length)
        
        zcr = torch.mean(frames, dim=-1) / 2.0  # Divide by 2 because sign change = 2
        return zcr
    
    def _compute_rms(self, waveform: torch.Tensor) -> torch.Tensor:
        """Laske RMS energy frame-based GPU:lla"""
        frame_length = self.hop_length
        num_frames = waveform.shape[-1] // frame_length
        
        if num_frames == 0:
            return torch.sqrt(torch.mean(waveform ** 2, dim=-1, keepdim=True))
        
        trimmed_length = num_frames * frame_length
        frames = waveform[..., :trimmed_length].reshape(waveform.shape[0], num_frames, frame_length)
        
        rms = torch.sqrt(torch.mean(frames ** 2, dim=-1))
        return rms
    
    def _compute_spectral_contrast(self, mel_spectrogram: torch.Tensor, n_bands: int = 6) -> torch.Tensor:
        """Laske spectral contrast GPU:lla"""
        # Jaa mel-spektrogrammi kaistiin
        n_mels = mel_spectrogram.shape[1]
        band_size = n_mels // n_bands
        
        contrasts = []
        for i in range(n_bands):
            start_idx = i * band_size
            end_idx = start_idx + band_size if i < n_bands - 1 else n_mels
            
            band = mel_spectrogram[:, start_idx:end_idx, :]
            
            # Peak vs valley
            peak = torch.quantile(band, 0.9, dim=1)
            valley = torch.quantile(band, 0.1, dim=1)
            
            contrast = peak - valley
            contrasts.append(contrast)
        
        return torch.stack(contrasts, dim=1)
    
    def _compute_chroma(self, waveform: torch.Tensor, n_chroma: int = 12) -> torch.Tensor:
        """Laske chroma features GPU:lla"""
        # Yksinkertaistettu chroma (käytä CQT constant-Q transform)
        # Tämä on approximaatio, voi käyttää torchaudio.transforms.ChromaScale tulevaisuudessa
        
        spec = self.spectrogram(waveform)
        n_freqs = spec.shape[1]
        
        # Luo chroma filter bank
        freqs = torch.linspace(0, self.sample_rate / 2, n_freqs, device=self.device)
        
        # Map frequencies to chroma bins (simplified)
        # C = 0, C# = 1, ..., B = 11
        chroma_filters = torch.zeros(n_chroma, n_freqs, device=self.device)
        
        for freq_idx, freq in enumerate(freqs):
            if freq < 20:  # Skip very low frequencies
                continue
            # MIDI note number
            midi = 12 * torch.log2(freq / 440.0) + 69
            chroma_bin = int(midi.item()) % n_chroma
            if 0 <= chroma_bin < n_chroma:
                chroma_filters[chroma_bin, freq_idx] = 1.0
        
        # Normalize filters
        chroma_filters = chroma_filters / (torch.sum(chroma_filters, dim=1, keepdim=True) + 1e-10)
        
        # Apply filters
        chroma = torch.matmul(chroma_filters, spec)
        
        return chroma
    
    def compute_embeddings(self, features: Dict[str, torch.Tensor], 
                          embedding_dim: int = 512) -> torch.Tensor:
        """
        Luo kompaktit embeddings feature-setistä
        Tämä on yksinkertaistettu versio - voi korvata neuraalimallilla
        """
        # Kerää kaikki featuret yhteen tensoriin
        feature_list = []
        
        for key, value in features.items():
            if 'mean' in key or 'std' in key:
                # Käytä summary statistiikkoja
                if value.dim() > 1:
                    value = torch.mean(value, dim=-1)
                feature_list.append(value.flatten())
        
        # Concatenate
        combined = torch.cat(feature_list, dim=-1)
        
        # Normalisoi
        combined = (combined - torch.mean(combined)) / (torch.std(combined) + 1e-10)
        
        # Project to embedding_dim (simple linear projection)
        if combined.shape[-1] != embedding_dim:
            # Joko pad tai truncate
            if combined.shape[-1] < embedding_dim:
                padding = torch.zeros(embedding_dim - combined.shape[-1], device=self.device)
                combined = torch.cat([combined, padding])
            else:
                combined = combined[:embedding_dim]
        
        return combined
    
    def batch_extract(self, waveforms: torch.Tensor) -> Tuple[Dict, torch.Tensor]:
        """
        Batch-prosessointi useille äänisignaaleille
        
        Args:
            waveforms: Batch of audio, shape (batch, channels, samples)
            
        Returns:
            Tuple of (features_dict, embeddings)
        """
        batch_size = waveforms.shape[0]
        all_features = []
        all_embeddings = []
        
        for i in range(batch_size):
            features = self.extract_all_features(waveforms[i])
            embeddings = self.compute_embeddings(features)
            
            all_features.append(features)
            all_embeddings.append(embeddings)
        
        # Stack embeddings
        embeddings_tensor = torch.stack(all_embeddings)
        
        return all_features, embeddings_tensor


class AudioQualityEmbeddingNet(nn.Module):
    """
    Neuraalimalli joka luo rikkaita embeddings-vektoreita äänisignaaleista
    Voidaan käyttää quality assessment taskissa
    """
    
    def __init__(self, 
                 input_channels: int = 1,
                 embedding_dim: int = 512,
                 n_mels: int = 128):
        super().__init__()
        
        # Convolutional frontend (2D CNN mel-spektrogrammeille)
        self.conv_layers = nn.Sequential(
            # Block 1
            nn.Conv2d(input_channels, 64, kernel_size=3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(),
            nn.MaxPool2d(2, 2),
            
            # Block 2
            nn.Conv2d(64, 128, kernel_size=3, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(),
            nn.MaxPool2d(2, 2),
            
            # Block 3
            nn.Conv2d(128, 256, kernel_size=3, padding=1),
            nn.BatchNorm2d(256),
            nn.ReLU(),
            nn.MaxPool2d(2, 2),
            
            # Block 4
            nn.Conv2d(256, 512, kernel_size=3, padding=1),
            nn.BatchNorm2d(512),
            nn.ReLU(),
            nn.AdaptiveAvgPool2d((1, 1))
        )
        
        # Fully connected layers
        self.fc_layers = nn.Sequential(
            nn.Linear(512, embedding_dim),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(embedding_dim, embedding_dim)
        )
        
    def forward(self, mel_spectrogram: torch.Tensor) -> torch.Tensor:
        """
        Args:
            mel_spectrogram: (batch, channels, n_mels, time)
            
        Returns:
            embeddings: (batch, embedding_dim)
        """
        x = self.conv_layers(mel_spectrogram)
        x = x.view(x.size(0), -1)  # Flatten
        embeddings = self.fc_layers(x)
        
        return embeddings


def test_gpu_features():
    """Testifunktio GPU feature extractionille"""
    print("Testing GPU Feature Extractor...")
    
    # Luo satunnainen äänisignaali
    sample_rate = 44100
    duration = 3  # seconds
    waveform = torch.randn(1, sample_rate * duration)
    
    # Luo extractor
    extractor = GPUFeatureExtractor(sample_rate=sample_rate, device='cuda')
    
    # Ekstraktoi featuret
    with torch.no_grad():
        features = extractor.extract_all_features(waveform)
    
    print("\nExtracted features:")
    for key, value in features.items():
        print(f"  {key}: shape {value.shape}")
    
    # Luo embeddings
    with torch.no_grad():
        embeddings = extractor.compute_embeddings(features)
    print(f"\nEmbeddings shape: {embeddings.shape}")
    
    print("\n✓ GPU Feature Extraction test passed!")
    

if __name__ == "__main__":
    test_gpu_features()

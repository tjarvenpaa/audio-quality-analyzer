# Modulaariseen rakenteeseen siirtyminen - Vaiheittainen opas

## 🎯 Tavoite

Siirtyä nykyisestä monolitisesta rakenteesta modulaariseen frameworkiin **vaiheittain** ilman että rikotaan toimivaa järjestelmää.

## 📁 Kaksoispistejuoksu - strategia

Säilytetään molemmat rinnakkain:

```
äänityökalu/
├── src/                    # VANHA - toimii edelleen
│   ├── main.py
│   ├── dsp_analyzer.py
│   ├── gpu_features.py
│   ├── ai_model.py
│   └── visualizations.py
│
└── audio_quality_ai/       # UUSI - modulaarinen
    ├── ingest/
    ├── analysis/
    ├── inference/
    ├── explain/
    ├── storage/
    ├── api/
    └── ui/
```

## 🔧 VAIHE 1: Luo pohjarakenne (10 min)

Luo uudet kansiot ja perus__init__.py tiedostot :

```python
# Aja tämä luodaksesi rakenteen:
python create_modular_structure.py
```

Tarkemmat ohjeet alla.

## 📦 VAIHE 2: Siirrä DSP-analyysit (2 tuntia)

### 2.1 Luo DSP-moduulit

Puretaan `dsp_analyzer.py` osiin:

```
analysis/dsp/
├── __init__.py
├── base.py              # BaseAnalyzer luokka
├── loudness.py          # LUFS, loudness range
├── dynamics.py          # DR, crest factor, RMS
├── frequency.py         # Spectral analysis, balance
├── stereo.py            # Phase, correlation, width
├── clarity.py           # Spectral clarity, flatness
├── noise.py             # SNR, noise floor
└── production.py        # Clipping, DC offset
```

### 2.2 Yhteinen interface

Kaikki analyysit implementing saman interfacen:

```python
# ana lysis/dsp/base.py
from abc import ABC, abstractmethod
from typing import Dict
import numpy as np

class BaseAnalyzer(ABC):
    """Base class for all DSP analyzers"""
    
    @abstractmethod
    def analyze(self, audio: np.ndarray, sr: int) -> Dict:
        """
        Analyze audio and return results
        
        Args:
            audit: Audio signal
            sr: Sample rate
            
        Returns:
            Dictionary with analysis results
        """
        pass
    
    @abstractmethod
    def get_metrics(self) -> Dict:
        """Return available metrics"""
        pass
```

### 2.3 Esimerkki: Loudness moduuli

```python
# analysis/dsp/loudness.py
from .base import BaseAnalyzer
import pyloudnorm as pyln
import numpy as np

class LoudnessAnalyzer(BaseAnalyzer):
    """ITU-R BS.1770 Loudness Analysis"""
    
    def __init__(self, target_lufs: float = -16.0):
        self.target_lufs = target_lufs
        
    def analyze(self, audio: np.ndarray, sr: int) -> Dict:
        """Analyze loudness"""
        # Ensure correct shape
        if audio.ndim == 1:
            audio = audio.reshape(-1, 1)
        elif audio.ndim > 1:
            audio = audio.T
            
        meter = pyln.Meter(sr)
        
        # Integrated loudness
        loudness = meter.integrated_loudness(audio)
        
        # True peak
        peak_db = 20 * np.log10(np.max(np.abs(audio)) + 1e-10)
        
        # Loudness range (simplified)
        # Could use EBU R128 standard
        
        return {
            'integrated_loudness_lufs': float(loudness),
            'true_peak_db': float(peak_db),
            'target_lufs': self.target_lufs,
            'deviation_from_target': float(abs(loudness - self.target_lufs)),
            'within_tolerance': abs(loudness - self.target_lufs) <= 2.0
        }
    
    def get_metrics(self) -> Dict:
        return {
            'integrated_loudness_lufs': 'Integrated Loudness (LUFS)',
            'true_peak_db': 'True Peak (dB)',
            'deviation_from_target': 'Deviation from Target (LU)'
        }
```

### 2.4 Registry pattern

```python
# analysis/dsp/__init__.py
from .loudness import LoudnessAnalyzer
from .dynamics import DynamicsAnalyzer
from .frequency import FrequencyAnalyzer
from .stereo import StereoAnalyzer
from .clarity import ClarityAnalyzer
from .noise import NoiseAnalyzer
from .production import ProductionAnalyzer

__all__ = [
    'LoudnessAnalyzer',
    'DynamicsAnalyzer',
    'FrequencyAnalyzer',
    'StereoAnalyzer',
    'ClarityAnalyzer',
    'NoiseAnalyzer',
    'ProductionAnalyzer'
]

# Registry
ANALYZERS = {
    'loudness': LoudnessAnalyzer,
    'dynamics': DynamicsAnalyzer,
    'frequency': FrequencyAnalyzer,
    'stereo': StereoAnalyzer,
    'clarity': ClarityAnalyzer,
    'noise': NoiseAnalyzer,
    'production': ProductionAnalyzer
}
```

## 🧠 VAIHE 3: Refaktoroi ML-osuus (3 tuntia)

### 3.1 Erota encoder ja heads

```
analysis/ml/
├── encoders/
│   ├── base.py          # Base encoder
│   ├── pytorch_cnn.py   # Nykyinen CNN
│   ├── openl3.py        # OpenL3 (tulevaisuus)
│   └── passt.py         # PaSST (tulevaisuus)
│
└── heads/
    ├── base.py
    ├── clarity.py
    ├── noise.py
    ├── dynamics.py
    └── stereo.py
```

### 3.2 Encoder interface

```python
# analysis/ml/encoders/base.py
from abc import ABC, abstractmethod
import torch

class BaseEncoder(ABC):
    """Base class for audio encoders"""
    
    @abstractmethod
    def encode(self, waveform: torch.Tensor) -> torch.Tensor:
        """
        Generate embeddings from waveform
        
        Args:
            waveform: Audio tensor
            
        Returns:
            Embeddings tensor
        """
        pass
```

## ⚙️ VAIHE 4: Inference Engine (2 tuntia)

```python
# inference/quality_engine.py
from typing import Dict, List
from audio_quality_ai.analysis.dsp import ANALYZERS
from audio_quality_ai.analysis.ml import MLAnalyzer

class QualityEngine:
    """Combines DSP and ML results"""
    
    def __init__(self, config: Dict):
        self.config = config
        
        # Initialize DSP analyzers
        self.dsp_analyzers = {
            name: analyzer_class()
            for name, analyzer_class in ANALYZERS.items()
        }
        
        # Initialize ML analyzer
        self.ml_analyzer = MLAnalyzer(config)
        
    def analyze(self, audio, sr: int) -> Dict:
        """Run full analysis"""
        results = {
            'dsp': {},
            'ml': {},
            'combined': {}
        }
        
        # DSP análisis
        for name, analyzer in self.dsp_analyzers.items():
            results['dsp'][name] = analyzer.analyze(audio, sr)
        
        # ML analysis
        results['ml'] = self.ml_analyzer.analyze(audio, sr)
        
        # Combine results
        results['combined'] = self._combine_results(
            results['dsp'], 
            results['ml']
        )
        
        return results
    
    def _combine_results(self, dsp: Dict, ml: Dict) -> Dict:
        """Combine DSP and ML results into final scores"""
        # Implementation...
        pass
```

## 🤖 VAIHE 5: Lisää LLM Explain (4 tuntia)

**TÄMÄ ON SUURIN PUUTE NYKYISESSÄ**

### 5.1 Asenna Ollama

```bash
# Windows/Linux/Mac
curl https://ollama.ai/install.sh | sh

# Lataa malli
ollama pull mistral
# tai
ollama pull phi
```

### 5.2 LLM Explainer

```python
# explain/llm_explainer.py
import requests
import json
from pathlib import Path
from typing import Dict, List

class LLMExplainer:
    """Generate human-readable explanations using local LLM"""
    
    def __init__(self, oll ama_url: str = "http://localhost:11434"):
        self.ollama_url = ollama_url
        self.model = "mistral"  # or "phi"
        
    def explain_results(self, 
                       analysis_results: Dict,
                       user_notes: str = "") -> str:
        """
        Generate explanation from analysis results
        
        Args:
            analysis_results: Complete analysis dict
            user_notes: User's focus areas
            
        Returns:
            Human-readable explanation
        """
        # Build context
        context = self._build_context(analysis_results, user_notes)
        
        # Load prompt template
        prompt = self._load_prompt_template('general', context)
        
        # Query LLM
        response = self._query_ollama(prompt)
        
        return response
    
    def _build_context(self, results: Dict, notes: str) -> Dict:
        """Build context for LLM"""
        context = {
            'overall_score': results.get('combined', {}).get('overall_score', 0),
            'issues': results.get('issues', []),
            'recommendations': results.get('recommendations', []),
            'dsp_metrics': self._extract_key_metrics(results.get('dsp', {})),
            'user_focus': notes
        }
        return context
    
    def _load_prompt_template(self, category: str, context: Dict) -> str:
        """Load and format prompt template"""
        template_path = Path(__file__).parent / 'prompt_templates' / f'{category}.txt'
        
        with open(template_path, 'r', encoding='utf-8') as f:
            template = f.read()
        
        # Format with context
        prompt = template.format(**context)
        return prompt
    
    def _query_ollama(self, prompt: str) -> str:
        """Query Ollama API"""
        response = requests.post(
            f"{self.ollama_url}/api/generate",
            json={
                "model": self.model,
                "prompt": prompt,
                "stream": False
            }
        )
        
        if response.status_code == 200:
            return response.json()['response']
        else:
            return "Error generating explanation"
```

### 5.3 Prompt Template

```text
# explain/prompt_templates/general.txt
You are an audio quality expert analyzing a recording.

Analysis Results:
- Overall Quality Score: {overall_score}/100
- Detected Issues: {issues}
- Key Metrics: {dsp_metrics}

User Focus: {user_focus}

Please provide:
1. Brief overall assessment (2-3 sentences)
2. Explanation of the main issues in plain language
3. Top 3 specific, actionable recommendations
4. What's working well (positive feedback)

Be concise, practical, and educational. Explain technical terms when you use them.
```

## 💾 VAIHE 6: Storage Layer (2 tuntia)

```python
# storage/results_store.py
import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

class ResultsStore:
    """Store and retrieve analysis results"""
    
    def __init__(self, db_path: str = "results.db"):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Initialize database schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS analysis_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                filepath TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                overall_score REAL,
                results_json TEXT NOT NULL,
                notes TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def save(self, filename: str, results: Dict, notes: str = ""):
        """Save analysis results"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO analysis_results 
            (filename, filepath, overall_score, results_json, notes)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            filename,
            results.get('filepath', ''),
            results.get('combined', {}).get('overall_score', 0),
            json.dumps(results),
            notes
        ))
        
        conn.commit()
        conn.close()
    
    def get_history(self, filename: str) -> List[Dict]:
        """Get analysis history for a file"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, timestamp, overall_score, results_json
            FROM analysis_results
            WHERE filename = ?
            ORDER BY timestamp DESC
        ''', (filename,))
        
        results = []
        for row in cursor.fetchall():
            results.append({
                'id': row[0],
                'timestamp': row[1],
                'overall_score': row[2],
                'results': json.loads(row[3])
            })
        
        conn.close()
        return results
    
    def compare(self, id1: int, id2: int) -> Dict:
        """Compare two analyses"""
        # Implementation...
        pass
```

## 🌐 VAIHE 7: REST API (3 tuntia)

```python
# api/fastapi_app.py
from fastapi import FastAPI, UploadFile, File, HTTPException
from audio_quality_ai.inference import QualityEngine
from audio_quality_ai.storage import ResultsStore
import tempfile
import librosa

app = FastAPI(title="Audio Quality AI API")

quality_engine = QualityEngine({})
results_store = ResultsStore()

@app.post("/analyze")
async def analyze_audio(
    file: UploadFile = File(...),
    notes: str = ""
):
    """Analyze uploaded audio file"""
    try:
        # Save to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name
        
        # Load audio
        audio, sr = librosa.load(tmp_path, sr=None)
        
        # Analyze
        results = quality_engine.analyze(audio, sr)
        
        # Save to database
        results_store.save(file.filename, results, notes)
        
        return results
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/history/{filename}")
async def get_history(filename: str):
    """Get analysis history"""
    history = results_store.get_history(filename)
    return {"history": history}
```

## 🖥️ VAIHE 8: Web UI (3 tuntia)

```python
# ui/streamlit_app.py
import streamlit as st
import requests
from audio_quality_ai.inference import QualityEngine
import plotly.graph_objects as go

st.title("🎵 Audio Quality Analyzer")

uploaded_file = st.file_uploader("Upload audio file", type=['wav', 'mp3'])

if uploaded_file:
    st.audio(uploaded_file)
    
    notes = st.text_area("Analysis notes (optional)")
    
    if st.button("Analyze"):
        with st.spinner("Analyzing..."):
            # Run analysis
            # ... 
            
            # Display results
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Overall Score", f"{overall_score}/100")
            
            with col2:
                st.metric("Loudness", f"{loudness:.1f} LUFS")
            
            with col3:
                st.metric("SNR", f"{snr:.1f} dB")
            
            # Radar chart
            fig = go.Figure(data=go.Scatterpolar(
                r=scores,
                theta=categories,
                fill='toself'
            ))
            st.plotly_chart(fig)
```

## ✅ Testausstrategia

Jokaisen vaiheen jälkeen:

1. **Unit testit** - Testaa moduulit erikseen
2. **Integration testit** - Testaa yhdessä
3. **Regression testit** - Varmista että vanha toimii
4 . **Performance testit** - Mittaa suorituskyky

## 📝 TODO-lista

- [ ] Vaihe 1: Luo pohjarakenne
- [ ] Vaihe 2: DSP-moduulit
  - [ ] Loudness
  - [ ] Dynamics
  - [ ] Frequency
  - [ ] Stereo
  - [ ] Clarity
  - [ ] Noise
  - [ ] Production
- [ ] Vaihe 3: ML-refaktorointi
- [ ] Vaihe 4: Inference engine
- [ ] Vaihe 5: LLM explain ⭐ **PRIORITEETTI**
- [ ] Vaihe 6: Storage
- [ ] Vaihe 7: REST API
- [ ] Vaihe 8: Web UI

## 🚀 Seuraavaksi

1. **Päätä**: Aloitetaanko refaktorointi?
2. **Priorisoi**: Mitkä vaiheet ovat tärkeimmät?
3. **Aikatauluta**: Kuinka paljon aikaa on käytettävissä?
4. **Aloita**: Vaihe kerrallaan

**Suositus:** Aloita LLM explain -kerroksesta (Vaihe 5), sillä se on suurin puute nykyisessä ja antaa heti lisäarvoa!

# REFAKTOROINTISUUNNITELMA - Modulaariseen arkkitehtuuriin

## Nykyinen vs. Ehdotettu

### ❌ NYKYINEN (Monolitinen prototyyppi):
```
src/
├── main.py              # 300+ riviä - kaikki yhdessä
├── dsp_analyzer.py      # 600+ riviä - kaikki DSP yhdessä
├── gpu_features.py      # 400+ riviä - feature extraction
├── ai_model.py          # 500+ riviä - AI + recommendations
└── visualizations.py    # 300+ riviä
```

### ✅ TAVOITE (Modulaarinen framework):
```
audio_quality_ai/
├── ingest/
│   ├── __init__.py
│   ├── loader.py           # librosa, torchaudio, ffmpeg
│   ├── normalizer.py       # audio normalization
│   └── segmenter.py        # chunking for long files
│
├── analysis/
│   ├── dsp/
│   │   ├── __init__.py
│   │   ├── loudness.py     # pyloudnorm
│   │   ├── dynamics.py     # RMS, crest, DR
│   │   ├── frequency.py    # spectral analysis
│   │   └── stereo.py       # phase, correlation
│   │
│   ├── ml/
│   │   ├── __init__.py
│   │   ├── encoder.py      # base embedding class
│   │   ├── openl3.py       # OpenL3 encoder
│   │   ├── passt.py        # PaSST encoder
│   │   └── heads/
│   │       ├── clarity.py
│   │       ├── noise.py
│   │       ├── dynamics.py
│   │       └── stereo.py
│   │
│   └── metrics/
│       ├── __init__.py
│       └── quality_metrics.py
│
├── inference/
│   ├── __init__.py
│   ├── quality_engine.py   # combine DSP + ML
│   ├── issue_detector.py   # detect problems
│   └── scoring.py          # calculate scores
│
├── explain/
│   ├── __init__.py
│   ├── llm_explainer.py    # LLM interface
│   ├── prompt_templates/
│   │   ├── clarity.txt
│   │   ├── noise.txt
│   │   └── general.txt
│   └── ollama_backend.py   # local LLM via Ollama
│
├── storage/
│   ├── __init__.py
│   ├── results_store.py    # JSON/SQLite storage
│   ├── history.py          # version tracking
│   └── comparison.py       # before/after analysis
│
├── api/
│   ├── __init__.py
│   ├── fastapi_app.py      # REST API
│   └── routes/
│       ├── analyze.py
│       ├── history.py
│       └── compare.py
│
├── ui/
│   ├── __init__.py
│   ├── streamlit_app.py    # web UI
│   └── cli.py              # enhanced CLI
│
└── core/
    ├── __init__.py
    ├── config.py           # configuration management
    └── utils.py            # shared utilities
```

## VAIHEITTAINEN REFAKTOROINTI

### Vaihe 1: Säilytä nykyinen toimivuus (VALMIS ✅)
- Nykyinen rakenne toimii
- Dokumentaatio kunnossa
- Testattavissa

### Vaihe 2: Pilko DSP-analyysit erillisiksi moduuleiksi (SEURAAVAKSI)
```
Etteistä: dsp_analyzer.py (600 riviä)
→ Jälkeen:
  analysis/dsp/loudness.py    (100 riviä)
  analysis/dsp/dynamics.py    (100 riviä)
  analysis/dsp/frequency.py   (150 riviä)
  analysis/dsp/stereo.py      (100 riviä)
  analysis/dsp/clarity.py     (100 riviä)
```

**Hyödyt:**
- Helpompi testata
- Helpompi ylläpitää
- Voi käyttää erikseen
- Single Responsibility Principle

### Vaihe 3: Erota ML-encoders ja heads
```
Ennen: gpu_features.py (400 riviä)
→ Jälkeen:
  analysis/ml/encoder.py      (base class)
  analysis/ml/pytorch_encoder.py
  analysis/ml/heads/clarity.py
  analysis/ml/heads/noise.py
```

**Hyödyt:**
- Voi vaihtaa encoderia (OpenL3, PaSST, wav2vec)
- Heads uudelleenkäytettäviä
- Helppo lisätä uusia heads

### Vaihe 4: Luo inference-kerros
```
Ennen: ai_model.py (yhdistää kaiken)
→ Jälkeen:
  inference/quality_engine.py  (yhdistää DSP + ML)
  inference/issue_detector.py  (tunnistaa ongelmat)
  inference/scoring.py         (laskee pisteet)
```

**Hyödyt:**
- Selkeä vastuunjako
- DSP ja ML irrotettu toisistaan
- Voi käyttää vain DSP:tä ilman ML:ää

### Vaihe 5: Lisää explain-kerros (LLM)
```
explain/
├── llm_explainer.py
├── ollama_backend.py      # Mistral 7B / Phi-4
└── prompt_templates/
```

**Uusi ominaisuus:**
- Selittää tulokset ihmiskielellä
- Kontekstuaaliset suositukset
- Opettavainen palaute
- **Täysin offline via Ollama**

### Vaihe 6: Lisää storage-kerros
```
storage/
├── results_store.py    # SQLite tai JSON
├── history.py          # version tracking
└── comparison.py       # A/B comparison
```

**Uudet ominaisuudet:**
- Tallennus historiaan
- Versioiden vertailu
- Kehityksen seuranta
- Aikasarja-analyysi

### Vaihe 7: Lisää API
```
api/
├── fastapi_app.py
└── routes/
```

**Uudet käyttötavat:**
- REST API
- Webhook integrations
- Batch processing via API
- Cloud deployment

### Vaihe 8: Lisää Web UI
```
ui/
├── streamlit_app.py
└── cli.py
```

**Parannettu UX:**
- Drag & drop files
- Real-time analysis
- Interactive visualizations
- Audio playback

## YHTEENSOPIVUUS

**Taaksepäin yhteensopiva:**
```python
# Vanha tapa toimii edelleen:
from src.main import AudioQualityAnalyzer
analyzer = AudioQualityAnalyzer()
results = analyzer.analyze_file("audio.wav")

# Uusi modulaarinen tapa:
from audio_quality_ai.analysis.dsp import LoudnessAnalyzer
from audio_quality_ai.analysis.ml import ClarityHead
from audio_quality_ai.inference import QualityEngine

loudness = LoudnessAnalyzer().analyze(audio)
clarity = ClarityHead().predict(embeddings)
quality = QualityEngine().combine(loudness, clarity)
```

## MIGRAATIOSTRATEGIA

1. **Luo uusi audio_quality_ai/ kansio**
2. **Kopioi src/ → audio_quality_ai/legacy/**
3. **Rakenna uudet moduulit vaiheittain**
4. **Testaa jokainen vaihe**
5. **Dokumentoi muutokset**
6. **Säilytä vanha versio toimivana**

## AIKATAULU (Ehdotus)

- **Vaihe 1**: Valmis ✅
- **Vaihe 2**: DSP-moduulit (1-2 päivää)
- **Vaihe 3**: ML-encoders (1-2 päivää)
- **Vaihe 4**: Inference (1 päivä)
- **Vaihe 5**: LLM explain (2-3 päivää)
- **Vaihe 6**: Storage (1 päivä)
- **Vaihe 7**: API (2 päivää)
- **Vaihe 8**: UI (2-3 päivää)

**Yhteensä**: ~2 viikkoa full-time

## PÄÄTÖS

**Ehdotus:** 

1. **Säilytä nykyinen** versio toimivana prototyyppinä
2. **Aloita refaktorointi** uuteen audio_quality_ai/ kansioon
3. **Rakenna vaiheittain** ehdotetun rakenteen mukaan
4. **Testaa jokainen vaihe** ennen seuraavaa
5. **Dokumentoi** muutokset

**Kannattaako refaktoroida nyt?**

**KYLLÄ, jos:**
- Haluat skaalautuvan ratkaisun
- Suunnittelet pitkän aikavälin kehitystä
- Haluat API:n ja web UI:n
- Tarvitset LLM-selityksiä
- Tiimi kasvaa

**EI, jos:**
- Tarvitset vain nopean prototyypin
- Käyttö on kertaluontoista
- Resurssit rajalliset
- Nykyinen versio riittää

## SUOSITUS

**Kaksoispistejuoksu:**

1. **Jatka nykyisellä** välittömiin tarpeisiin
2. **Rakenna modulaarinen** rinnalle pitkälle tähtäimelle
3. **Migroi vaiheittain** kun uusi on testattu

Näin saat:
- ✅ Toimivan version heti
- ✅ Skaalautuvan rakenteen tulevaisuuteen
- ✅ Oppimiskokemuksen molemmista
- ✅ Jaamisen riskin hallintaa

# Muutosloki

## [1.1.0] - 2026-04-19

### Lisätty
- 🆕 **HTML-yhteenveto raportti** (`audio_quality_summary_*.html`)
  - Interaktiivinen, responsiivinen HTML-sivu
  - Vertailutaulukko kaik kien tiedostojen välillä
  - Yhteenvetotilastot (paras, heikoin, keskiarvo)
  - Yksityiskohtaiset analyysit per tiedosto
  - Visualisoinnit embedattuina
  - LLM-selitykset muotoiltuina
  - Moderni, printtausystävällinen design
- Laitteisto- ja järjestelmävaatimukset README:hen
  - Testattu laitteisto
  - Minimispeksit
  - GPU-yhteensopivuus
  - Käyttöjärjestelmätuki

### Korjattu
- Docker-kontti ei enää looppaa loputtomiin
  - Poistettu automaattinen `python3 src/main.py` -komento
  - Manuaalinen ajo docker exec -kautta
- Visualisointien colorbar-virhe korjattu
- Excel-raportin UnboundLocalError korjattu

## [1.0.0] - 2026-04-18

### Lisätty
- Ensimmäinen julkaisu
- GPU-kiihdytetty analyysi (CUDA 11.8)
- 7 laatuaspektia (Clarity, Noise, Frequency, Dynamic Range, Loudness, Stereo, Production)
- LLM-selitykset (Ollama Phi/Mistral)
- Excel, teksti ja visualisointiraportit
- Docker-deployment GPU-tuella
- Batch-käsittely
- Watch-mode

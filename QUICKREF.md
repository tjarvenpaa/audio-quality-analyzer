# Quick Reference - Pikaopas

## 🚀 Yleisimmät komennot

### Docker-kontit

```powershell
# Käynnistä kontit
docker compose -f docker-compose.gpu.yml up -d

# Pysäytä kontit
docker compose -f docker-compose.gpu.yml down

# Tarkista status
docker compose -f docker-compose.gpu.yml ps

# Lokit
docker compose -f docker-compose.gpu.yml logs -f audio-analyzer
```

### Analyysi

```powershell
# Analysoi kaikki tiedostot input_folder/-kansiossa
docker exec audio-quality-analyzer-gpu python3 src/main.py

# Analysoi yksittäinen tiedosto
docker exec audio-quality-analyzer-gpu python3 src/main.py --single --input input_folder/podcast.wav

# Käynnistä watch-mode (jatkuva monitorointi)
docker exec -d audio-quality-analyzer-gpu python3 watch.py

# Pysäytä watch-mode
docker restart audio-quality-analyzer-gpu
```

### LLM (Ollama)

```powershell
# Lataa Phi-malli (3GB, suositeltu)
docker exec audio-quality-ollama-gpu ollama pull phi

# Lataa Mistral-malli (4.4GB, hitaampi)
docker exec audio-quality-ollama-gpu ollama pull mistral

# Listaa ladatut mallit
docker exec audio-quality-ollama-gpu ollama list

# Testaa mallia interaktiivisesti
docker exec -it audio-quality-ollama-gpu ollama run phi
```

### Tulokset

```powershell
# Listaa tulokset
dir output\

# Avaa Excel-raportti
start output\audio_quality_report_*.xlsx

# Katso tekstiraporttia
Get-Content output\reports\podcast_report.txt

# Avaa visualisointi
start output\visualizations\podcast_analysis.png
```

---

## ⚙️ Konfiguraatio (config.yaml)

### LLM-asetukset

```yaml
llm:
  enabled: true          # true = LLM-selitykset käytössä
  model: "phi"           # phi (nopea) tai mistral (tarkempi)
  timeout: 240           # Aikakatkaisu sekunteina
```

### GPU-asetukset

```yaml
gpu:
  enabled: true          # true = GPU-kiihdytys
  device: "cuda:0"       # CUDA-device
  batch_size: 8          # Batch-koko
```

---

## 🐛 Yleisimmät ongelmat

### "CUDA not available"

```powershell
# Tarkista GPU-näkyvyys
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi
```

### "Ollama connection refused"

```powershell
# Tarkista että Ollama-kontti on käynnissä
docker compose -f docker-compose.gpu.yml ps ollama

# Lataa malli uudelleen
docker exec audio-quality-ollama-gpu ollama pull phi
```

### "LLM timeout"

Kasvata timeout-arvoa [config.yaml](config.yaml):ssa:

```yaml
llm:
  timeout: 300  # Kasvatettu 240 → 300 sekuntia
```

### "Empty Excel report"

Tarkista lokeista virheet:

```powershell
docker compose -f docker-compose.gpu.yml logs audio-analyzer | Select-String "Error"
```

### "Infinite loop / Duplicate reports"

Tämä on korjattu! [docker-compose.gpu.yml](docker-compose.gpu.yml) ei enää käynnistä analyysiä automaattisesti.

---

## 📊 Tuetut äänimuodot

✅ WAV, MP3, FLAC, M4A, OGG, AAC

**Suositellut asetukset:**
- Sample rate: 44.1 kHz tai 48 kHz
- Bit depth: 16-bit tai 24-bit
- Stereo tai mono

---

## 🔧 Kehitys

### Lokaali asennus (ilman Dockeria)

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### Testaus

```powershell
# Yksittäinen tiedosto
python src/main.py --single --input input_folder/test.wav

# Batch-analyysi
python src/main.py
```

---

## 📚 Lisätietoa

- [README.md](README.md) - Täysi dokumentaatio
- [GITHUB_SETUP.md](GITHUB_SETUP.md) - GitHub-julkaisun ohjeet
- [CONTRIBUTING.md](CONTRIBUTING.md) - Kontribuutio-ohjeet
- [docs/](docs/) - Vanha dokumentaatio (arkisto)

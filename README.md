# Koko projekti on toteutettu wipe koodina, pienenä iltapuhteena.
Projektia ohjannut ajatus oli luoda podcast edittiä varten työkalu, joka käy läpi äänitiedoston hyvyyttä DSP työkaluilla ja tuottaa tästä llm avulla selityksen ja kommentoinnin. 

# 🎙️ GPU-kiihdytetty Äänenlaatuanalysaattori

![Docker](https://img.shields.io/badge/docker-latest-blue?logo=docker)
![Python](https://img.shields.io/badge/python-3.10+-green?logo=python)
![CUDA](https://img.shields.io/badge/CUDA-11.8-76B900?logo=nvidia)
![PyTorch](https://img.shields.io/badge/PyTorch-CUDA-red?logo=pytorch)
![License](https://img.shields.io/badge/license-MIT-blue)

**Kattava äänenlaatuanalyysi GPU-kiihdytyksellä ja paikallisella LLM-selittäjällä.**

Analysoi podcasteja, äänitallenteitä ja musiikkia käyttäen DSP-analytiikkaa, AI-malleja ja ihmisluettavia LLM-selityksiä. Docker-pohjainen ratkaisu NVIDIA GPU:lle.

---

## ✨ Ominaisuudet

### 📊 Analysoitavat osa-alueet (7 aspektia)

1. **Clarity (Selkeys)** - Kuinka selkeästi ääni toistuu
2. **Noise Analysis (Kohina)** - Taustakohinan taso ja laatu  
3. **Frequency Balance (Taajuustasapaino)** - Taajuuksien jakautuminen
4. **Dynamic Range (Dynamiikka)** - Hiljaisimpien ja äänekkäimpien osien väli
5. **Stereo Image (Stereokuva)** - Stereokentän ominaisuudet
6. **Loudness (Äänenvoimakkuus)** - ITU-R BS.1770 standardi
7. **Production Quality (Tuotantolaatu)** - Teknisen laadun kokonaisarvio

### 🚀 Tekniset ominaisuudet

- ✅ **DSP-analyysi** - 30+ mittaria per tiedosto (librosa, pyloudnorm)
- ✅ **GPU-kiihdytys** - PyTorch CUDA 11.8 (NVIDIA)
- ✅ **AI-arviointi** - Transformer-pohjainen laatumalli
- ✅ **LLM-selitykset** - Ollama Phi (3GB) tuottaa ihmisluettavat suositukset
- ✅ **Automaattiset suositukset** - Ongelmatunnistus + priorisoidut toimenpiteet
- ✅ **Monipuoliset raportit** - Excel, teksti, visualisoinnit (PNG)
- ✅ **Batch-käsittely** - Analysoi useita tiedostoja kerralla
- ✅ **Watch-mode** - Jatkuva monitorointi uusille tiedostoille

---

## 🐳 Pika-aloitus (Docker)

### Vaatimukset

- Docker Desktop + WSL2 (Windows) / Docker (Linux/Mac)
- NVIDIA GPU + [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html)
- 8GB+ RAM, 4GB+ GPU VRAM

---

## 🖥️ Laitteisto- ja järjestelmävaatimukset

### Testattu laitteisto

**Kehitysympäristö:**
- **GPU:** NVIDIA RTX PRO 4000 Blackwell (8GB VRAM)
- **CPU:** AMD Ryzen / Intel Core i7+ (8+ ytimiä suositeltu)
- **RAM:** 32GB DDR4
- **Tallennustila:** 50GB+ vapaata tilaa (Docker-imaget + Ollama-mallit)
- **Käyttöjärjestelmä:** Windows 11 Pro + WSL2 (Ubuntu 22.04)

### Minimirautavaatimukset

**CPU:**
- 4+ ytimiä (DSP-analyysi on CPU-intensiivinen)
- AVX2-tuki suositeltu (numpy/librosa-optimoinnit)

**GPU:**
- NVIDIA GPU CUDA Compute Capability 3.7+ (Kepler tai uudempi)
- 4GB+ VRAM (Phi-malli 3GB + PyTorch overhead)
- CUDA 11.8 tai 12.x yhteensopiva

**RAM:**
- 8GB minimi (batch-analyysi vaatii enemmän)
- 16GB+ suositeltu useiden tiedostojen käsittelyyn

**Tallennustila:**
- 30GB vapaata tilaa minimissään:
  - Docker-imaget: ~10GB
  - Ollama Phi-malli: ~3GB
  - PyTorch + riippuvuudet: ~5GB
  - Työskentely-/output-tila: ~10GB

### Suositellut speksit (tuotantokäyttö)

- **GPU:** NVIDIA RTX 3060+ / A4000+ / T4+ (6-12 GB VRAM)
- **CPU:** 8+ ytimiä, 3.0+ GHz
- **RAM:** 32GB+ (isot batch-käsittelyt)
- **Tallennustila:** 100GB+ SSD/NVMe (nopea I/O)

### GPU-yhteensopivuus

✅ **Testatut ja tuetut:**
- NVIDIA RTX-sarja (20xx, 30xx, 40xx)
- NVIDIA Quadro / RTX Pro -sarja
- NVIDIA Tesla / A-series (datacenter)
- NVIDIA GTX 16xx -sarja (rajallinen suorituskyky)

❌ **Ei tuettu:**
- AMD Radeon GPU:t (ei CUDA-tukea)
- Intel Arc GPU:t (ei CUDA-tukea)
- CPU-only mode (toimii mutta erittäin hidas)

### Käyttöjärjestelmät

**✅ Tuettu (Docker):**
- **Windows 10/11** + WSL2 + Docker Desktop
- **Linux** (Ubuntu 20.04+, Debian 11+, CentOS 8+)
- **macOS** (CPU-only, ei GPU-tuki - Apple Silicon ei yhteensopiva NVIDIA CUDA:n kanssa)

**Lokaali asennus (ilman Dockeria):**
- Python 3.10+ vaaditaan
- CUDA Toolkit 11.8 asennettuna
- NVIDIA GPU-ajurit (535.xx tai uudempi)

### Docker-vaatimukset

- **Docker Desktop:** 4.20+
- **Docker Compose:** 2.17+
- **NVIDIA Container Toolkit:** Asennettuna ja konfiguroitu
- **WSL2** (Windows): Kernel 5.10+

**Testaa GPU-näkyvyys Dockerissa:**
```powershell
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi
```

Jos komento näyttää GPU-tiedot, Docker GPU-tuki on kunnossa!

---

### Käynnistys

```powershell
# 1. Kloonaa repo
git clone https://github.com/your-username/audio-quality-analyzer.git
cd audio-quality-analyzer

# 2. Käynnistä kontit (GPU-tuki)
docker compose -f docker-compose.gpu.yml up -d

# 3. Lataa LLM-malli (ensimmäisellä kerralla)
docker exec audio-quality-ollama-gpu ollama pull phi

# 4. Kopioi äänitiedostoja
Copy-Item podcast.wav input_folder\

# 5. Aja analyysi
docker exec audio-quality-analyzer-gpu python3 src/main.py

# 6. Tarkista tulokset
dir output\
```

Tulokset:
- `output/audio_quality_summary_YYYYMMDD_HHMMSS.html` - **Interaktiivinen HTML-yhteenveto** (UUSI!)
- `output/audio_quality_report_YYYYMMDD_HHMMSS.xlsx` - Excel-raportti
- `output/reports/*.txt` - Yksityiskohtaiset tekstiraportit
- `output/visualizations/*.png` - Spektrogrammit ja kaaviot

**HTML-raportti sisältää:**
- 📊 Vertailutaulukko (kaikki tiedostot yhdessä)
- 📈 Yhteenvetotilastot
- 📁 Yksityiskohtaiset analyysit per tiedosto
- 🖼️ Visualisoinnit embedattuina
- 🤖 LLM-selitykset (jos käytettävissä)
- 🎨 Modernit, responsiiviset graafit

**Avaa HTML-raportti selaimessa:**
```powershell
start output\audio_quality_summary_*.html
```

---

## 📖 Käyttöohjeet

### Manuaalinen analyysi (kerran)

```powershell
# Analysoi kaikki input_folder/ -tiedostot
docker exec audio-quality-analyzer-gpu python3 src/main.py

# Analysoi yksittäinen tiedosto
docker exec audio-quality-analyzer-gpu python3 src/main.py --single --input input_folder/podcast.wav
```

### Jatkuva valvonta (automaattinen)

```powershell
# Käynnistä watch-mode (tarkkailee input_folder/)
docker exec -d audio-quality-analyzer-gpu python3 watch.py

# Pysäytä watch-mode
docker restart audio-quality-analyzer-gpu
```

Watch-mode käsittelee automaattisesti kaikki uudet tiedostot `input_folder/`-kansiossa.

### Konttien hallinta

```powershell
# Pysäytä kontit
docker compose -f docker-compose.gpu.yml down

# Käynnistä uudelleen
docker compose -f docker-compose.gpu.yml up -d

# Tarkista lokit
docker compose -f docker-compose.gpu.yml logs -f audio-analyzer

# Tarkista LLM-status
docker exec audio-quality-ollama-gpu ollama list
```

---

## ⚙️ Konfiguraatio

Muokkaa [config.yaml](config.yaml) tarpeidesi mukaan:

### LLM-asetukset

```yaml
llm:
  enabled: true           # Ota LLM-selitykset käyttöön/pois
  provider: "ollama"
  model: "phi"            # Malli: phi (3GB) tai mistral (4.4GB)
  ollama_url: "http://ollama:11434"
  timeout: 240            # Timeout sekunteina (Phi: 70-185s tyypillinen)
  max_retries: 2
```

**LLM-mallit:**
- `phi` (3GB) - Nopea, suositeltu (70-185s vastausaika)
- `mistral` (4.4GB) - Tarkempi mutta hitaampi

### DSP-asetukset

```yaml
dsp:
  sample_rate: 22050      # Hz
  n_fft: 2048
  hop_length: 512
  n_mels: 128
```

### Tuetut formaatit

WAV, MP3, FLAC, M4A, OGG, AAC

---

## 📁 Projektirakenne

```
audio-quality-analyzer/
├── src/
│   ├── main.py              # Päämoduuli
│   ├── dsp_analyzer.py      # DSP-analyysi (librosa)
│   ├── gpu_features.py      # GPU-ominaisuuksien purku
│   ├── ai_model.py          # AI-laatumalli + suositukset
│   ├── llm_explainer.py     # LLM-selitysgeneraattori
│   ├── visualizations.py    # Kuvaajien luonti
│   └── watch.py             # Jatkuva monitorointi
├── input_folder/            # Syötteet (äänitiedostot)
├── output/                  # Tulokset (raportit, kuvat)
├── config.yaml              # Konfiguraatio
├── docker-compose.gpu.yml   # Docker Compose (GPU)
├── Dockerfile.gpu           # Docker image (CUDA 11.8)
└── requirements.txt         # Python-riippuvuudet
```

---

## 🛠️ Kehitys & kontribuutio

### Lokaali asennus (ilman Dockeria)

```bash
# Python 3.10+ vaaditaan
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Asenna riippuvuudet
pip install -r requirements.txt

# Asenna PyTorch CUDA-tuki
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Käynnistä Ollama erikseen
ollama serve
ollama pull phi

# Aja analyysi
python src/main.py
```

### Debug-lokit

LLM-kyselyissä näkyy yksityiskohtaiset debug-lokit:

```
🤖 LLM query (attempt 1/2)
   Model: phi
   URL: http://ollama:11434
   Timeout: 240s
   Prompt length: 3761 chars
   Response time: 107.9s
   ✓ Success! Response length: 2460 chars
```

---

## 📄 Lisenssi

MIT License - katso [LICENSE](LICENSE)

---

## 🙋 Tuki & palaute

- **Issues:** [GitHub Issues](https://github.com/your-username/audio-quality-analyzer/issues)
- **Dokumentaatio:** [docs/](docs/)

---

**Kehittäjä:** Audio Quality AI Team  
**Päivitetty:** Huhtikuu 2026
- ✅ **Docker-tuki** - Helppokäyttöinen konttipohjainen ajaminen
- ✅ **100% paikallinen** - Ei pilvipalveluita

## Asennus

### 1. Esivaatimukset

- Python 3.8 tai uudempi
- NVIDIA GPU CUDA-tuella (valinnainen, mutta suositeltu)
- CUDA Toolkit 11.8+ (GPU-käyttöä varten)

### 2. Asenna riippuvuudet

```bash
# Luo virtuaaliympäristö (suositeltu)
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Asenna riippuvuudet
pip install -r requirements.txt
```

### 3. GPU-tuki (valinnainen)

Jos sinulla on NVIDIA GPU:

```bash
# Asenna PyTorch CUDA-tuella
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

Jos et käytä GPU:ta, CPU-versio toimii myös (hitaammin).

## Käyttö

### Perusperuskäyttö - Batch-analyysi

Analysoi kaikki äänitiedostot kansiosta:

```bash
python src/main.py
```

Tämä analysoi kaikki tiedostot `input_folder/` kansiosta ja tallentaa tulokset `output/` kansioon.

### Yksittäisen tiedoston analyysi

```bash
python src/main.py --single --input "path/to/audio.wav"
```

### Mukautettu input/output kansio

```bash
python src/main.py --input "C:/my_audio_files" --output "C:/results"
```

### Lisää muistiinpanoja analyysiin

```bash
python src/main.py --single --input "audio.wav" --notes "Focus on noise analysis"
```

## Konfiguraatio

Muokkaa `config.yaml` tiedostoa mukauttaaksesi asetuksia:

```yaml
general:
  use_gpu: true  # Käytä GPU:ta jos saatavilla
  batch_size: 4  # Batch-koko GPU-prosessointiin

dsp:
  sample_rate: 44100  # Näytteenottotaajuus
  
quality_criteria:
  loudness:
    target_lufs: -16.0  # Tavoiteloudness (broadcast standard)
  snr:
    minimum_db: 25.0  # Minimi SNR hyvälle laadulle
```

## Tulosten tulkinta

### Excel-raportti

Excel-tiedosto sisältää yhteenvedon kaikista analysoiduista tiedostoista:
- Laatupisteet (0-100) jokaiselle osa-alueelle
- Tekniset mittarit (LUFS, SNR, Dynamic Range, jne.)
- Tunnistettujen ongelmien määrä
- Tärkeimmät parannusehdotukset

### Yksityiskohtaiset tekstiraportit

Jokainen tiedosto saa oman raportin `output/reports/` kansioon:
- Laatuarviot jokaiselle osa-alueelle
- Havaitut ongelmat ja niiden vakavuus
- Priorisoitu lista parannusehdotuksista
- Yksityiskohtaiset tekniset mittaustulokset

### Visualisoinnit

Kansio `output/visualizations/` sisältää kuvaajat:
1. **Aaltomuoto** - Audiosignaalin visuaalinen esitys
2. **Spektrogrammi** - Taajuussisältö ajan funktiona
3. **Mel-spektrogrammi** - Ihmiskorvan havainnoimaan perustuvat taajuudet
4. **Taajuustasapaino** - Energian jakautuminen eri taajuuskaistoissa
5. **Dynaaminen vaihtelu** - RMS-energian vaihtelu ajassa
6. **Laatupisteet (Radar)** - Kaikki laatuaspektit yhdessä kaaviossa
7. **Stereokenttä** - L/R kanavien välinen suhde (stereo-audiolle)
8. **Yhteenveto** - Ongelmat ja suositukset

## Laatukriteerit

### Pisteytysjärjestelmä (0-100)

- **90-100**: Excellent - Ammattimainen laatu
- **75-89**: Good - Hyvä laatu
- **60-74**: Fair - Hyväksyttävä
- **40-59**: Poor - Vaatii parannuksia
- **0-39**: Very Poor - Vakavia ongelmia

### Tekniset standardit

- **Loudness**: -16 LUFS ± 2 LU (broadcast standard)
- **Peak**: < -1.0 dB
- **SNR**: ≥ 25 dB (minimum), ≥ 45 dB (excellent)
- **Dynamic Range**: 6-20 dB (podcast ~8-12 dB)
- **Phase Correlation**: 0.3-0.7 (stereo)

## Esimerkkisuositukset

Työkalu voi antaa esimerkiksi seuraavia suosituksia:

- "Reduce input gain" - Clippausta havaittu
- "Add noise reduction" - Korkea taustakohinan taso
- "Apply EQ bass cut/boost" - Taajuustasapainon ongelmat
- "Reduce compression" - Ylikompressoitu
- "Fix phase issues" - Stereokuvan ongelmat
- "Normalize loudness" - Loudness ei vastaa standardia

## Tiedostorakenne

```
äänityökalu/
├── config.yaml              # Konfiguraatio
├── requirements.txt         # Python-riippuvuudet
├── README.md               # Tämä tiedosto
├── input_folder/           # Sisääntulo äänitiedostoille
├── output/                 # Analyysitulokset
│   ├── reports/           # Tekstiraportit
│   └── visualizations/    # Kuvaajat
└── src/                    # Lähdekoodi
    ├── __init__.py
    ├── main.py            # Pääohjelma
    ├── dsp_analyzer.py    # DSP-analyysit
    ├── gpu_features.py    # GPU-feature extraction
    ├── ai_model.py        # AI-malli
    └── visualizations.py  # Visualisoinnit
```

## Tekninen stack

- **Python 3.8+**
- **PyTorch** - GPU-kiihdytetty neuroverkkokirjasto
- **Librosa** - Äänianalyysi ja -prosessointi
- **Torchaudio** - GPU-kiihdytetyt äänenkäsittelytransformaatiot
- **Pyloudnorm** - ITU-R BS.1770 loudness-mittaus
- **NumPy & SciPy** - Numeerinen laskenta
- **Matplotlib** - Visualisoinnit
- **Pandas** - Datan käsittely ja Excel-vienti
- **PyYAML** - Konfiguraatiotiedostojen käsittely

## Lisenssi

Tämä projekti käyttää avoimien lähdekoodien komponentteja MIT-lisenssillä.

## Kehitysideoita

Tulevaisuudessa voidaan lisätä:
- [ ] Web-käyttöliittymä (Streamlit/Gradio)
- [ ] Reaaliaikainen analyysi
- [ ] Automaattinen audiokorjaus (denoise, normalize)
- [ ] Ääninäytteiden vertailu
- [ ] Opitun mallin hienosäätö omalla datalla
- [ ] Parempien visualisointien tuki (3D-spektrogrammit)
- [ ] PDF-raportit
- [ ] API REST endpoint
- [ ] Tuki useammille äänimuodoille (AAC, OPUS, jne.)

## Tuki ja ongelmanratkaisu

### GPU ei havaita

Varmista että:
1. NVIDIA GPU on asennettu
2. CUDA Toolkit on asennettu
3. PyTorch on asennettu CUDA-tuella

Testaa GPU:
```python
import torch
print(torch.cuda.is_available())  # Pitäisi tulostaa True
print(torch.cuda.get_device_name(0))  # Näyttää GPU:n nimen
```

### Muistiongelmat (Out of Memory)

Pienennä batch_size arvoa config.yaml tiedostossa tai käytä lyhyempiä äänitiedostoja.

### Dependency-konfliktit

Käytä virtuaaliympäristöä ja asenna riippuvuudet puhtaaseen ympäristöön.

## Yhteystiedot ja palaute

Kehitysehdotuksia ja bugiraportteja otetaan vastaan!

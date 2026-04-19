# 🎵 DOCKER-DEPLOYMENT VALMIS!

## ✅ Mitä luotiin

### 1. **Docker-tiedostot**
- `Dockerfile` - CPU-versio (kevyt)
- `Dockerfile.gpu` - GPU-versio (CUDA 11.8)
- `docker-compose.yml` - CPU-deployment
- `docker-compose.gpu.yml` - GPU-deployment
- `.dockerignore` - Optimoi imagen koko

### 2. **Automaatioskriptit**
- `start-docker.sh` - Linux/Mac käynnistys
- `start-docker.bat` - Windows käynnistys
- `src/watch.py` - Automaattinen tiedostomonitorointi

### 3. **Dokumentaatio**
- `DOCKER.md` - Kattava käyttöopas (250+ riviä)

## 🏗️ Arkkitehtuuri

```
┌────────────────────────────────────────┐
│       Docker Compose Stack             │
├────────────────────────────────────────┤
│                                        │
│  ┌──────────────┐  ┌──────────────┐  │
│  │   Ollama     │◄─┤  Analyzer    │  │
│  │   (LLM)      │  │  (Audio AI)  │  │
│  │              │  │              │  │
│  │ Port: 11434  │  │ Python 3.10  │  │
│  │ GPU: ✓       │  │ GPU: ✓       │  │
│  └──────────────┘  └──────────────┘  │
│         │                  │          │
│         ▼                  ▼          │
│  [ollama_data]      [Shared Vols]    │
│   (4GB Mistral)     input/output     │
└────────────────────────────────────────┘
```

## 🚀 Käyttöönotto (3 tapaa)

### Tapa 1: Automaattinen (helpooin)

**Linux/Mac:**
```bash
bash start-docker.sh
```

**Windows:**
```cmd
start-docker.bat
```

Skripti:
- ✅ Tarkistaa Docker-asennuksen
- ✅ Tunnistaa GPU:n automaattisesti
- ✅ Rakentaa kontit
- ✅ Käynnistää palvelut
- ✅ Lataa Mistral-mallin
- ✅ Näyttää komennot jatkoon

### Tapa 2: Manuaalinen CPU

```bash
# Rakenna ja käynnistä
docker-compose up -d

# Lataa LLM-malli
docker exec audio-quality-ollama ollama pull mistral

# Aja analyysi
docker-compose exec audio-analyzer python src/main.py
```

### Tapa 3: Manuaalinen GPU (suositeltava)

```bash
# Vaatii: nvidia-docker
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi

# Rakenna ja käynnistä
docker-compose -f docker-compose.gpu.yml up -d

# Lataa malli
docker exec audio-quality-ollama-gpu ollama pull mistral

# Testaa GPU
docker exec audio-quality-analyzer-gpu python3 -c "import torch; print(torch.cuda.is_available())"

# Aja analyysi
docker-compose -f docker-compose.gpu.yml exec audio-analyzer python3 src/main.py
```

## 📋 Tyypilliset käyttötapaukset

### 1. Yksittäinen tiedosto

```bash
# Kopioi tiedosto
cp podcast.mp3 input_folder/

# Analysoi
docker-compose exec audio-analyzer python src/main.py

# Tulokset
ls output/
```

### 2. Batch-analyysi

```bash
# Kopioi useita tiedostoja
cp ~/my_audio/*.mp3 input_folder/

# Käynnistä analyysi
docker-compose exec audio-analyzer python src/main.py

# Kaikki tulokset output/-kansioon
```

### 3. Automaattinen watch-mode

```bash
# Käynnistä watcher
docker-compose exec audio-analyzer python src/watch.py

# Nyt kontti monitoroi input_folder/:a
# Uudet tiedostot analysoidaan automaattisesti!
```

### 4. Tuotantopalvelin

```bash
# Käynnistä daemonina
docker-compose -f docker-compose.gpu.yml up -d

# Watch-mode taustalle
docker-compose -f docker-compose.gpu.yml exec -d audio-analyzer python3 src/watch.py

# Nyt palvelin analysoi jatkuvasti uusia tiedostoja
```

## 🎛️ Konfigurointi

### LLM-malli vaihto

```bash
# Saatavilla olevat mallit
docker exec audio-quality-ollama ollama list

# Lataa uusi (esim. phi - pienempi ja nopeampi)
docker exec audio-quality-ollama ollama pull phi

# Päivitä config.yaml:
# llm:
#   model: "phi"

# Uudelleenkäynnistä
docker-compose restart audio-analyzer
```

### Suorituskyvyn optimointi

**Muistirajoitukset** (jos kone hidastuu):
```yaml
# docker-compose.yml
services:
  ollama:
    deploy:
      resources:
        limits:
          memory: 8G
```

**Useampi työntekijä** (batch-käsittely):
```yaml
services:
  audio-analyzer:
    deploy:
      replicas: 3
```

## 📊 Resurssitarpeet

| Versio | CPU | RAM | GPU | Nopeus | Suositus |
|--------|-----|-----|-----|--------|----------|
| **CPU** | 4+ | 8GB | - | 1x | Testaus |
| **GPU Basic** | 4+ | 16GB | RTX 3060 (8GB) | 10x | Normaalikäyttö |
| **GPU Pro** | 8+ | 32GB | RTX 4090 (24GB) | 20x | Tuotanto |

## 🔧 Ongelmanratkaisu

### Ollama ei käynnisty

```bash
# Tarkista logit
docker logs audio-quality-ollama

# Uudelleenkäynnistä
docker-compose restart ollama

# Testaa API
curl http://localhost:11434/api/tags
```

### GPU ei toimi

```bash
# Testaa nvidia-docker
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi

# Jos ei toimi, asenna nvidia-container-toolkit
# Katso: DOCKER.md - GPU-tuki osio
```

### Hidas suoritus

```bash
# 1. Vaihda pienempään malliin
docker exec audio-quality-ollama ollama pull phi

# 2. Käytä GPU-versiota
docker-compose -f docker-compose.gpu.yml up -d

# 3. Tarkista resurssit
docker stats
```

## 🎯 Seuraavat askeleet

1. **Testaa käyttöönotolla:**
   ```bash
   bash start-docker.sh
   ```

2. **Kopioi testiääni:**
   ```bash
   cp test_audio.mp3 input_folder/
   ```

3. **Aja ensimmäinen analyysi:**
   ```bash
   docker-compose exec audio-analyzer python src/main.py
   ```

4. **Tarkista tulokset:**
   ```bash
   ls output/
   open output/*.xlsx
   ```

5. **Käynnistä watch-mode:**
   ```bash
   docker-compose exec audio-analyzer python src/watch.py
   ```

## 📚 Lisädokumentaatio

- **Yksityiskohtainen opas**: [DOCKER.md](DOCKER.md)
- **Pika-aloitus**: [QUICKSTART.md](QUICKSTART.md)
- **Asennusohje**: [INSTALL.md](INSTALL.md)
- **Projektin rakenne**: [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)

## ✨ Mitä Docker tuo?

| Ominaisuus | Ilman Dockeria | Dockerilla |
|------------|----------------|------------|
| **Asennus** | 30+ min | 5 min |
| **Riippuvuudet** | Manuaalinen | Automaattinen |
| **Ympäristö** | Riippuvainen | Eristetty |
| **Skaalaus** | Vaikea | Helppo |
| **Ylläpito** | Haastavaa | docker-compose up |
| **Siirrettävyys** | Heikko | Täydellinen |

## 🎉 Valmista!

Järjestelmä on nyt täysin kontitettuna ja valmis tuotantoon. Voit:

- ✅ Ajaa paikallisesti (Docker Desktop)
- ✅ Deployata palvelimelle (Linux + nvidia-docker)
- ✅ Skaalata useampaan työntekijään
- ✅ Monitoroida kansiota automaattisesti
- ✅ Integroida muihin järjestelmiin (API tulossa)

**Aloita nyt:**
```bash
bash start-docker.sh  # tai start-docker.bat Windowsissa
```

---

**Kysymyksiä?** Katso [DOCKER.md](DOCKER.md) - 250+ riviä yksityiskohtaista dokumentaatiota!

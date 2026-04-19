# DOCKER DEPLOYMENT GUIDE
# GPU-kiihdytetty Äänenlaatuanalysaattori Docker-ympäristössä

## 🎯 Arkkitehtuuri

```
┌─────────────────────────────────────────────────────┐
│                Docker Compose Stack                  │
├─────────────────────────────────────────────────────┤
│                                                       │
│  ┌────────────────────┐      ┌──────────────────┐  │
│  │  Ollama Container  │◄────►│ Analyzer Container│  │
│  │                    │      │                   │  │
│  │  - Mistral 7B     │      │  - Audio Analysis │  │
│  │  - GPU Accelerated│      │  - GPU Features   │  │
│  │  - API: :11434    │      │  - DSP Processing │  │
│  └────────────────────┘      └──────────────────┘  │
│          │                            │              │
│          │    Network: audio-ai       │              │
│          ▼                            ▼              │
│  ┌────────────────────┐      ┌──────────────────┐  │
│  │  ollama_data       │      │ Shared Volumes   │  │
│  │  (models)          │      │ - input_folder   │  │
│  └────────────────────┘      │ - output         │  │
│                               └──────────────────┘  │
└─────────────────────────────────────────────────────┘
         ▲                                  ▲
         │                                  │
    Host GPU                           Host Files
```

## 📦 Kaksi versiota

### 1. **CPU-versio** (docker-compose.yml)
- Toimii ilman GPU:ta
- Hitaampi (CPU PyTorch)
- Ollama CPU-modessa
- Helppo setup

### 2. **GPU-versio** (docker-compose.gpu.yml)
- Vaatii NVIDIA GPU + CUDA
- 10-20x nopeampi
- Ollama GPU-modessa
- Vaatii nvidia-docker

## 🚀 KÄYTTÖÖNOTTO

### Esivalmistelut

#### 1. Asenna Docker

**Windows:**
- Lataa Docker Desktop: https://www.docker.com/products/docker-desktop
- Asenna ja käynnistä
- Varmista WSL2-tuki

**Linux:**
```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
```

#### 2. GPU-tuki (valinnainen, mutta suositeltu)

**NVIDIA GPU + CUDA:**
```bash
# Asenna NVIDIA Container Toolkit
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
  sudo tee /etc/apt/sources.list.d/nvidia-docker.list

sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit
sudo systemctl restart docker

# Testaa
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi
```

**Windows Docker Desktop:**
- Settings → Resources → WSL Integration
- Enabling GPU support (vaatii NVIDIA driver)

### 🏃 Käynnistys

#### CPU-versio (helppo)

```bash
# 1. Siirry projektikansioon
cd äänityökalu

# 2. Rakenna ja käynnistä
docker-compose up -d

# 3. Lataa LLM-malli (ensimmäisellä kerralla)
docker exec audio-quality-ollama ollama pull mistral

# 4. Tarkista tila
docker-compose ps
docker-compose logs -f
```

#### GPU-versio (suositeltava jos GPU)

```bash
# 1. Siirry projektikansioon
cd äänityökalu

# 2. Rakenna ja käynnistä GPU-versio
docker-compose -f docker-compose.gpu.yml up -d

# 3. Lataa LLM-malli
docker exec audio-quality-ollama-gpu ollama pull mistral

# 4. Testaa GPU
docker exec audio-quality-analyzer-gpu python3 -c "import torch; print(f'CUDA: {torch.cuda.is_available()}')"

# 5. Tarkista logit
docker-compose -f docker-compose.gpu.yml logs -f
```

### 📁 Tiedostojen käsittely

```bash
# Kopioi äänitiedostoja input-kansioon
cp ~/my_audio/*.mp3 input_folder/

# Aja analyysi
docker-compose exec audio-analyzer python src/main.py

# Tai GPU-versiolla
docker-compose -f docker-compose.gpu.yml exec audio-analyzer python3 src/main.py

# Tulokset löytyvät
ls output/
```

### 🔄 Automaattinen analyysi (watch mode)

Luo watch-skripti joka analysoi automaattisesti uudet tiedostot:

```bash
# Käynnistä watch-mode
docker-compose exec audio-analyzer python src/watch.py

# Nyt kun kopioit tiedostoja input_folder/:iin, ne analysoidaan automaattisesti
```

## 🎛️ Konfigurointi

### config.yaml muokkaus

```bash
# Muokkaa konfiguraatiota
nano config.yaml

# Uudelleenkäynnistä palvelut
docker-compose restart
```

### LLM-mallin vaihto

```bash
# Lataa eri malli
docker exec audio-quality-ollama ollama pull phi

# Päivitä config.yaml:
llm:
  model: "phi"  # tai "llama2", "codellama", etc.

# Käynnistä uudelleen
docker-compose restart audio-analyzer
```

### Saatavilla olevat Ollama-mallit:

| Malli | Koko | Nopeus | Laatu | Suositus |
|-------|------|--------|-------|----------|
| **mistral** | 4GB | Nopea | Erinomainen | ⭐ Suositeltu |
| **phi** | 3GB | Erittäin nopea | Hyvä | Resurssirajoitettu |
| **llama2** | 4GB | Keskitaso | Hyvä | Vakaa |
| **codellama** | 4GB | Nopea | Hyvä | Tekninen |
| **mixtral** | 26GB | Hidas | Paras | Jos resursseja |

```bash
# Katso kaikki saatavilla olevat mallit
docker exec audio-quality-ollama ollama list

# Lataa uusi malli
docker exec audio-quality-ollama ollama pull <model_name>

# Poista vanha malli (säästä tilaa)
docker exec audio-quality-ollama ollama rm <model_name>
```

## 🐛 Ongelmanratkaisu

### Ollama ei käynnisty

```bash
# Tarkista logit
docker logs audio-quality-ollama

# Uudelleenkäynnistä
docker-compose restart ollama

# Tarkista yhteys
curl http://localhost:11434/api/tags
```

### GPU ei toimi

```bash
# Testaa NVIDIA runtime
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi

# Tarkista että GPU näkyy konttiin
docker exec audio-quality-analyzer-gpu nvidia-smi

# Tarkista PyTorch GPU-tuki
docker exec audio-quality-analyzer-gpu python3 -c "import torch; print(torch.cuda.is_available())"
```

### Muistin loppuminen

```bash
# Rajoita muistia docker-compose.yml:ssä
services:
  ollama:
    deploy:
      resources:
        limits:
          memory: 8G
        reservations:
          memory: 4G
```

### Hidas suoritus

```bash
# Tarkista että GPU on käytössä
docker stats

# Vaihda pienempään LLM-malliin
docker exec audio-quality-ollama ollama pull phi

# Päivitä config.yaml: model: "phi"
```

## 📊 Resurssitarpeet

### Minimi (CPU-versio):
- CPU: 4 core
- RAM: 8 GB
- Disk: 20 GB
- GPU: Ei tarvita

### Suositeltu (GPU-versio):
- CPU: 8 core
- RAM: 16 GB
- GPU: NVIDIA RTX 3060 (8GB VRAM) tai parempi
- Disk: 30 GB
- CUDA: 11.8+

### Optimaalinen (tuotanto):
- CPU: 16 core
- RAM: 32 GB
- GPU: NVIDIA RTX 4090 (24GB VRAM)
- Disk: 100 GB SSD
- CUDA: 12.0+

## 🔧 Ylläpito

### Päivitä järjestelmä

```bash
# Pull uusimmat imaget
docker-compose pull

# Uudelleenrakenna
docker-compose build --no-cache

# Käynnistä uusilla imageilla
docker-compose up -d
```

### Siivoa vanhoja resursseja

```bash
# Poista käyttämättömät imaget
docker image prune -a

# Poista käyttämättömät volumet
docker volume prune

# Poista kaikki (VAROITUS: poistaa myös mallit)
docker system prune -a --volumes
```

### Backup

```bash
# Varmuuskopioi Ollama-mallit
docker run --rm -v äänityökalu_ollama_data:/data -v $(pwd):/backup \
  ubuntu tar czf /backup/ollama_backup.tar.gz /data

# Palauta
docker run --rm -v äänityökalu_ollama_data:/data -v $(pwd):/backup \
  ubuntu tar xzf /backup/ollama_backup.tar.gz -C /
```

## 🌐 Lisää API-palvelin (tulevaisuus)

```bash
# Poista kommentti docker-compose.yml:stä
# Rakenna API
docker-compose up -d api-server

# API on nyt: http://localhost:8000
# Swagger docs: http://localhost:8000/docs
```

## 📈 Skaalaus

### Useampi työntekijä

```yaml
# docker-compose.yml
services:
  audio-analyzer:
    deploy:
      replicas: 3  # 3 rinnakkaista työntekijää
```

### Kubernetes deployment

```bash
# Luo Kubernetes manifestit
kubectl create -f k8s/

# Katso KUBERNETES.md (tuleva)
```

## ✅ Tarkistuslista

Ennen tuotantokäyttöä:

- [ ] Docker ja Docker Compose asennettu
- [ ] NVIDIA drivers ja nvidia-docker (GPU)
- [ ] Ollama malli ladattu (mistral/phi)
- [ ] GPU testaus onnistunut
- [ ] Testanalyysi suoritettu
- [ ] config.yaml mukautettu
- [ ] Backup-strategia paikallaan
- [ ] Monitoring käytössä (tuleva)

## 🎓 Esimerkkejä

### Yksinkertainen batch-analyysi

```bash
# 1. Kopioi tiedostot
cp ~/podcasts/*.mp3 input_folder/

# 2. Aja analyysi
docker-compose exec audio-analyzer python src/main.py

# 3. Katso tulokset
ls output/
open output/audio_quality_report_*.xlsx
```

### Automatisoi cron-jobilla

```bash
# Lisää crontabiin (Linux)
crontab -e

# Aja joka yö klo 2:00
0 2 * * * cd /path/to/äänityökalu && docker-compose exec -T audio-analyzer python src/main.py
```

### CI/CD pipeline

```yaml
# .github/workflows/audio-analysis.yml
name: Audio Quality Analysis
on: [push]
jobs:
  analyze:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run Docker Compose
        run: |
          docker-compose up -d
          docker-compose exec -T audio-analyzer python src/main.py
```

---

## 🆘 Tuki

Ongelmia? Tarkista:
1. Docker logit: `docker-compose logs`
2. Ollama tila: `curl http://localhost:11434/api/tags`
3. GPU-tuki: `nvidia-smi` (host) ja `docker exec ... nvidia-smi` (container)

**Seuraavaksi**: Katso [KUBERNETES.md](KUBERNETES.md) Kubernetes-deploymentille

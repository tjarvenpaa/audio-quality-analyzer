# Asennusohjeet - GPU-kiihdytetty Äänenlaatuanalysaattori

## Vaihe 1: Python asennus

1. Lataa ja asenna Python 3.8 tai uudempi: https://www.python.org/downloads/
2. Varmista asennuksen aikana, että valitset "Add Python to PATH"
3. Testaa asennus komentoriviltä:
   ```
   python --version
   ```

## Vaihe 2: CUDA ja GPU-tuki (VALINNAINEN)

### Windows:

1. **Tarkista GPU yhteensopivuus:**
   - Avaa Device Manager
   - Laajenna "Display adapters"
   - Jos sinulla on NVIDIA GPU, jatka asennusta
   - Jos ei, ohita GPU-asennus ja käytä CPU:ta

2. **Asenna NVIDIA CUDA Toolkit:**
   - Lataa CUDA Toolkit 11.8 tai uudempi: https://developer.nvidia.com/cuda-downloads
   - Asenna oletusasetuksilla
   - Käynnistä kone uudelleen

3. **Asenna NVIDIA cuDNN (valinnainen, mutta suositeltu):**
   - Rekisteröidy NVIDIA Developer -ohjelmaan: https://developer.nvidia.com/
   - Lataa cuDNN CUDA 11.x versioon sopiva
   - Pura zip-tiedosto ja kopioi tiedostot CUDA-kansioon (yleensä C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v11.8)

4. **Testaa CUDA:**
   ```
   nvcc --version
   nvidia-smi
   ```

## Vaihe 3: Projektin asennus

1. **Luo projektin kansio:**
   ```
   mkdir äänityökalu
   cd äänityökalu
   ```

2. **Kopioi projektitiedostot:**
   - Kopioi kaikki tiedostot projektikansioon

3. **Luo virtuaaliympäristö (SUOSITELTU):**
   ```
   python -m venv venv
   ```

4. **Aktivoi virtuaaliympäristö:**
   
   Windows:
   ```
   venv\Scripts\activate
   ```
   
   Linux/Mac:
   ```
   source venv/bin/activate
   ```
   
   Näet että ympäristö on aktiivinen kun komentorivin alussa näkyy `(venv)`

## Vaihe 4: Asenna riippuvuudet

### A) GPU-versio (NVIDIA GPU + CUDA):

1. Asenna PyTorch CUDA-tuella:
   ```
   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
   ```

2. Asenna muut riippuvuudet:
   ```
   pip install -r requirements.txt
   ```

3. Testaa GPU-tuki:
   ```python
   python -c "import torch; print('CUDA available:', torch.cuda.is_available()); print('GPU:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'None')"
   ```

### B) CPU-versio (ei NVIDIA GPU:ta):

1. Asenna kaikki riippuvuudet:
   ```
   pip install -r requirements.txt
   ```

2. Muokkaa `config.yaml`:
   ```yaml
   general:
     use_gpu: false  # Muuta false
   ```

## Vaihe 5: Luo tarvittavat kansiot

```
mkdir input_folder
mkdir output
```

## Vaihe 6: Testaa asennus

1. **Kopioi testitiedosto:**
   Kopioi jokin äänitiedosto (MP3, WAV) `input_folder/` kansioon

2. **Aja analyysi:**
   ```
   python src/main.py
   ```

3. **Tarkista tulokset:**
   - `output/` kansiossa pitäisi olla Excel-raportti
   - `output/reports/` tekstiraportit
   - `output/visualizations/` kuvaajat

## Vaihe 7: Päivitä konfiguraatio (valinnainen)

Muokkaa `config.yaml` sopivaksi:

```yaml
general:
  input_folder: "input_folder"  # Muuta oma kansiopolku
  output_folder: "output"       # Muuta oma kansiopolku
  use_gpu: true                # true jos GPU, false jos CPU
  
quality_criteria:
  loudness:
    target_lufs: -16.0  # Muuta target loudness
```

## Yleisiä ongelmia ja ratkaisuja

### Ongelma: "ModuleNotFoundError: No module named 'xxx'"

**Ratkaisu:**
```
pip install xxx
```
tai
```
pip install -r requirements.txt --force-reinstall
```

### Ongelma: "CUDA out of memory"

**Ratkaisu:**
1. Pienennä batch_size config.yaml tiedostossa:
   ```yaml
   general:
     batch_size: 1  # Pienennä 4 -> 1
   ```
2. Käytä lyhyempiä äänitiedostoja
3. Vaihda CPU-moodiin

### Ongelma: "torch.cuda.is_available() returns False"

**Ratkaisu:**
1. Varmista että CUDA Toolkit on asennettu
2. Asenna PyTorch uudelleen CUDA-tuella:
   ```
   pip uninstall torch torchvision torchaudio
   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
   ```
3. Jos ei toimi, käytä CPU-versiota

### Ongelma: Hidas suoritus

**Ratkaisuja:**
- Käytä GPU:ta jos mahdollista
- Pienennä näytteenottotaajuutta config.yaml:ssa
- Analysoi vain tarvittavat osa-alueet
- Käytä batch-analyysiä suurille määrille

### Ongelma: FFmpeg puuttuu

Jotkut äänimuodot vaativat FFmpeg:n.

**Windows:**
1. Lataa FFmpeg: https://ffmpeg.org/download.html
2. Pura zip ja lisää bin/ kansio PATH-ympäristömuuttujaan
3. Testaa: `ffmpeg -version`

**Linux:**
```
sudo apt-get install ffmpeg
```

**Mac:**
```
brew install ffmpeg
```

## Seuraavat askeleet

1. Lue README.md kokonaan
2. Kokeile analysointia omilla äänitiedostoilla
3. Mukauta config.yaml omiin tarpeisiin
4. Tutki raportointeja ja visualisointeja

## Tuki

Jos törmäät ongelmiin:
1. Tarkista että kaikki riippuvuudet on asennettu
2. Varmista että Python-versio on 3.8+
3. Kokeile puhtaassa virtuaaliympäristössä
4. Tarkista error-viestit ja Google
5. Kysy apua!

Onnea analysointiin! 🎵🎧

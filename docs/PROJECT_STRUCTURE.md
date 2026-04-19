# Projektin tiedostorakenne

```
äänityökalu/
├── README.md                    # Pääohje - lue tämä ensin!
├── QUICKSTART.md               # Pikaopas - pääset alkuun 5 minuutissa
├── INSTALL.md                  # Yksityiskohtaiset asennusohjeet
├── config.yaml                 # Pääkonfiguraatio - muokkaa tätä
├── requirements.txt            # Python-riippuvuudet
├── check_install.py           # Testaa asennus
├── examples.py                # Käyttöesimerkit
├── analyze.py                 # Vanha versio (deprecated)
│
├── src/                       # Lähdekoolikansio
│   ├── __init__.py           
│   ├── main.py               # Pääohjelma - käynnistä tästä
│   ├── dsp_analyzer.py       # DSP-analyysit (clarity, noise, balance, jne.)
│   ├── gpu_features.py       # GPU-kiihdytetty feature extraction
│   ├── ai_model.py           # AI-malli laatuarviointiin
│   └── visualizations.py     # Kuvaajien luonti
│
├── input_folder/             # LUO TÄMÄ - Laita äänitiedostot tänne
│   └── (MP3/WAV tiedostosi)
│
└── output/                   # LUO TÄMÄ - Analyysitulokset tallentuvat tänne
    ├── audio_quality_report_*.xlsx    # Excel-yhteenveto
    ├── reports/                       # Yksityiskohtaiset tekstiraportit
    │   └── *_report.txt
    └── visualizations/                # Kuvaajat
        └── *_analysis.png
```

## Tärkeimmät tiedostot:

### Käyttäjälle:

1. **README.md** - Lue ensin! Kattava dokumentaatio
2. **QUICKSTART.md** - Pikaopas alkuun pääsemiseksi
3. **INSTALL.md** - Asennusohjeet vaihe vaiheelta
4. **config.yaml** - Muokkaa asetuksia tästä
5. **examples.py** - Esimerkkejä käytöstä

### Ohjelmoijalle:

1. **src/main.py** - Pääohjelma, aloita tästä
2. **src/dsp_analyzer.py** - DSP-analyysin ydin
3. **src/gpu_features.py** - GPU-feature extraction PyTorchilla
4. **src/ai_model.py** - AI-mallit ja suositusgeneraattori
5. **src/visualizations.py** - Visualisointifunktiot

## Käytä näin:

```bash
# 1. Tarkista asennus
python check_install.py

# 2. Analysoi tiedostot
python src/main.py

# 3. Katso tulokset
# Avaa output/
```

## Muokkaa konfiguraatiota:

Avaa `config.yaml` tekstieditorilla ja muuta asetuksia:

```yaml
general:
  input_folder: "input_folder"   # Vaihda kansio
  use_gpu: true                  # CPU vs GPU

quality_criteria:
  loudness:
    target_lufs: -16.0           # Broadcast standard
```

## Laajenna toiminnallisuutta:

Halutut lisätä uusia ominaisuuksia?

- Uudet DSP-analyysit → `src/dsp_analyzer.py`
- AI-mallin parannus → `src/ai_model.py`
- Uudet visualisoinnit → `src/visualizations.py`
- Konfiguraatio → `config.yaml`

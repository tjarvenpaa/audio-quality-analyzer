# PIKAOPAS - Pääset alkuun 5 minuutissa

## 1. Tarkista asennus (30 sekuntia)

```bash
python check_install.py
```

Jos kaikki OK, jatka. Jos virheitä, katso INSTALL.md.

## 2. Kopioi äänitiedostoja (1 minuutti)

```bash
# Kopioi MP3/WAV tiedostoja
# Windows:
copy "C:\Omat tiedostot\podcast.mp3" input_folder\

# Linux/Mac:
cp ~/my_audio/podcast.mp3 input_folder/
```

## 3. Aja ensimmäinen analyysi (2 minuuttia)

```bash
python src/main.py
```

Odota että analyysi valmistuu. GPU:lla ~10-30 sekuntia per tiedosto, CPU:lla 1-3 minuuttia.

## 4. Tarkista tulokset (2 minuuttia)

Avaa:
- `output/audio_quality_report_*.xlsx` - Excel-yhteenveto
- `output/reports/` - Yksityiskohtaiset raportit
- `output/visualizations/` - Kuvaajat

## Valmis! 🎉

### Seuraavat askeleet:

**Yksittäisen tiedoston analyysi:**
```bash
python src/main.py --single --input "input_folder/my_audio.wav"
```

**Mukautetut kansiot:**
```bash
python src/main.py --input "C:\MinunAudit" --output "C:\Tulokset"
```

**Katso esimerkkejä:**
```bash
python examples.py
```

## Pikavinkitvalmiina Ohjeita:

### Laatupisteiden tulkinta:

| Pisteet | Arvio | Toimenpide |
|---------|-------|------------|
| 90-100 | Excellent | Julkaisuun valmis |
| 75-89 | Good | Kehuja pieninä parannuksina |
| 60-74 | Fair | Vaatii korjauksia |
| 40-59 | Poor | Vakavia ongelmia |
| 0-39 | Very Poor | Uudelleennauhoitus suositeltava |

### Yleiset ongelmat:

**"Clipping detected"** → Pienenpaa input gain
**"Low SNR"** → Vähennä taustakohinaa, lähemmäs mikrofonia
**"Over-compressed"** → Vähennä kompressiota
**"Loudness too low/high"** → Normalisoi -16 LUFS

### Konfigurointi:

Muokkaa `config.yaml`:

```yaml
general:
  use_gpu: true  # false jos ei GPU:ta

quality_criteria:
  loudness:
    target_lufs: -16.0  # Muuta tarvittaessa
```

## Tuki

Ongelmia? Katso:
1. INSTALL.md - Asennatuspåhjeet
2. README.md - Täydelliset ohjeet
3. examples.py - Käyttöesimerkit

---

**Vinkki:** Käytä batch-analyysia kun sinulla on paljon tiedostoja:
```bash
# Kopioi kaikki tiedostot input_folder/
# Aja:
python src/main.py
# Kaikki analysoidaan automaattisesti!
```

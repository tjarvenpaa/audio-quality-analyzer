# Kontribuutio-ohjeet

Kiitos kiinnostuksestasi osallistua projektiin! 🎉

## Miten voin osallistua?

### 🐛 Ilmoita bugeista

- Avaa [GitHub Issue](https://github.com/your-username/audio-quality-analyzer/issues)
- Kuvaile ongelma selkeästi
- Liitä mukaan:
  - Käyttöympäristö (OS, Docker-versio, GPU-malli)
  - Virheloki
  - Toistettavat vaiheet

### 💡 Ehdota parannuksia

- Avaa Issue ennen suuren muutoksen tekemistä
- Keskustele ideasta muiden kanssa
- Odota palautetta ennen koodin kirjoittamista

### 🔧 Lähetä Pull Request

1. **Fork** projekti
2. Luo feature-branch: `git checkout -b feature/amazing-feature`
3. Tee muutokset ja testaa
4. Commit: `git commit -m "Add amazing feature"`
5. Push: `git push origin feature/amazing-feature`
6. Avaa Pull Request

## Koodaustyyli

- **Python:** Noudata PEP 8 -standardia
- **Kommentit:** Kirjoita selkeät docstringit funktioille
- **Muuttujat:** Käytä kuvaavia nimiä (ei `x`, `temp`, `data`)
- **Testit:** Lisää testit uusille ominaisuuksille

## Testaus

```bash
# Aja testit ennen PR:ää
pytest tests/

# Tarkista koodin laatu
flake8 src/
black src/ --check
```

## Docker-kehitys

```bash
# Rakenna uudelleen muutosten jälkeen
docker compose -f docker-compose.gpu.yml build --no-cache

# Testaa konteissa
docker exec audio-quality-analyzer-gpu python3 src/main.py --single --input input_folder/test.wav
```

## Kehityssuositelmat

- Tee pieniä, atomiittisia committeja
- Yksi PR per ominaisuus/korjaus
- Päivitä dokumentaatio muutosten mukana
- Lisää kommentteja kompleksiseen koodiin

## Kysymykset?

Ota yhteyttä [GitHub Discussions](https://github.com/your-username/audio-quality-analyzer/discussions) -kautta!

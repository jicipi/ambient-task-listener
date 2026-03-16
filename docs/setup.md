# Ambient Task Listener - Setup Mac + Cursor

## 1) Outils recommandes

- Cursor ou VSCodium
- Git
- Homebrew
- Python 3.11+
- ESP-IDF

## 2) Installation de base (macOS)

```bash
brew update
brew install git cmake ninja dfu-util python@3.11 wget
```

## 3) ESP-IDF

Suivre la documentation officielle ESP32-P4.

Etapes generales:

1. Cloner ESP-IDF
2. Lancer le script d'installation
3. Activer l'environnement
4. Tester un projet exemple

Commandes typiques:

```bash
git clone --recursive https://github.com/espressif/esp-idf.git
cd esp-idf
./install.sh esp32p4
. ./export.sh
```

## 4) Cursor / VSCodium

Extensions utiles:

- C/C++
- Python
- Even Better TOML
- Error Lens
- GitLens
- ESP-IDF extension (si supportee dans ton setup)

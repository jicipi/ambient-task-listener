# Setup local ESP-IDF (macOS)

## Activation ESP-IDF a chaque nouveau terminal

Dans chaque nouveau terminal, executer:

```bash
cd ~/DEV/espressif/esp-idf
export PATH="/usr/local/opt/python@3.11/libexec/bin:/usr/local/bin:$PATH"
. ./export.sh
```

## Verification rapide

Une fois l'environnement active:

```bash
idf.py --version
```

Si la commande repond, l'environnement est pret.

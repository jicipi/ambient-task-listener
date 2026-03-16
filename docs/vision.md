# Ambient Task Listener - Vision Produit

## 1) Vision produit

Creer un objet domestique intelligent capable d'ecouter les conversations naturelles dans une piece et d'extraire automatiquement des actions utiles (courses, taches, rendez-vous) pour alimenter une application mobile de type To-Do.

Objectif: supprimer la friction entre "penser a quelque chose" et "l'ajouter a une liste".

Exemples:

- "Il faut acheter du lait" -> ajout automatique dans la liste de courses
- "Il faudra appeler le plombier" -> creation d'une tache
- "Il faudra prendre rendez-vous chez le dentiste" -> suggestion d'evenement

Le systeme apprend progressivement les habitudes du foyer.

## 2) Objectifs du MVP

MVP = prototype fonctionnel minimal.

Fonctions:

1. Capturer l'audio
2. Envoyer l'audio au serveur
3. Transcrire la parole
4. Detecter une phrase d'action
5. Ajouter une tache dans l'application

Pipeline MVP:

Micro -> ESP32 -> WiFi -> Serveur -> Transcription -> Extraction action -> App mobile

## 3) Structure du repository

```text
repo/
  firmware/
  backend/
  mobile/
  hardware/
  3d/
```

## 4) Premiers objectifs techniques

1. Installer ESP-IDF
2. Compiler exemple ESP32
3. Lire micro I2S
4. Enregistrer audio
5. Envoyer audio au serveur

## 5) Future extensions

- Multi-micro beamforming
- Speaker voice feedback
- Detection locuteur
- Assistant domestique complet

## 6) README racine recommande

Sections conseillees:

- Vision du projet
- Architecture generale
- Structure du repo
- Demarrage rapide
- Liens vers `docs/`

Structure repo recommandee:

```text
ambient-task-listener/
├─ README.md
├─ docs/
│  ├─ vision.md
│  ├─ architecture.md
│  ├─ hardware.md
│  └─ roadmap.md
├─ firmware/
├─ backend/
├─ mobile/
├─ hardware/
└─ 3d/
```

# Ambient Task Listener

Ambient Task Listener est un assistant vocal local capable de capturer des actions à partir de la parole et de les transformer automatiquement en tâches organisées dans différentes listes.

Le système fonctionne entièrement en local et combine :

- transcription vocale
- compréhension d’intention
- stockage structuré
- interface mobile/web

L’objectif est de créer un assistant ambiant domestique capable de capturer naturellement :

- courses
- tâches personnelles
- tâches professionnelles
- rendez-vous
- idées

---

# Architecture

Pipeline actuel :

microphone  
→ VAD (détection de parole)  
→ transcription Whisper MLX  
→ extraction d’intention (règles + fallback LLM)  
→ backend FastAPI  
→ stockage JSON  
→ application Flutter  

---

# Fonctionnalités

## Capture vocale

Le système écoute en continu via listen_loop.py.

Exemples :

"il faut acheter du chocolat"  
→ shopping : chocolat  

"je dois préparer la réunion Data4"  
→ todo_pro : réunion data4  

"il faut appeler le plombier"  
→ todo : plombier  

---

## Déduplication intelligente

Les tâches sont comparées avec une forme canonique.

Exemple :

plombier  
appeler le plombier  

Ces deux formes sont considérées comme identiques.

Le système ignore :

- les verbes d’action
- les articles

Cela évite les doublons.

---

# Listes supportées

- shopping
- todo
- todo_pro
- appointments
- ideas

---

# API Backend

API REST via FastAPI.

Endpoints principaux :

GET /health  
GET /lists  
GET /lists/{list_name}  
POST /lists/{list_name}  
DELETE /lists/{list_name}/item/{item_id}  
PATCH /lists/{list_name}/item/{item_id}  
PATCH /lists/{list_name}/item/{item_id}/rename  

Documentation interactive :

http://localhost:8000/docs

---

# Installation

## Backend

Créer l’environnement Python :

python -m venv .venv  
source .venv/bin/activate  
pip install -r requirements.txt  

Lancer le serveur :

uvicorn app.main:app --reload  

---

## Assistant vocal

Lancer l’écoute continue :

python listen_loop.py  

Le système écoutera le micro et ajoutera automatiquement les actions détectées.

---

## Application Flutter

Lancer l’interface web :

cd mobile  
flutter pub get  
flutter run -d chrome  

---

# Structure du projet

Backend :

backend/  
├── app/  
│   ├── main.py  
│   ├── action_extractor.py  
│   ├── storage.py  
│   └── llm_interpreter.py  
├── data/  
│   ├── shopping.json  
│   ├── todo.json  
│   ├── todo_pro.json  
│   ├── appointments.json  
│   └── ideas.json  
├── listen_loop.py  
└── record_and_extract.py  

Application Flutter :

mobile/  
├── lib/  
│   ├── features/  
│   │   ├── home/  
│   │   └── lists/  
│   └── data/  
│       └── services/  
└── main.dart  

---

# Roadmap

Prochaines évolutions :

- bouton micro dans l’application
- communication temps réel (WebSocket)
- capture audio via ESP32
- gestion multi-pièces
- rappels intelligents
- synchronisation mobile

---

# Objectif

Créer un assistant ambiant local qui capture les actions du quotidien sans friction.

L’utilisateur parle naturellement et les tâches apparaissent automatiquement dans l’application.
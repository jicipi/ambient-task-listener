# Ambient Task Listener

Ambient Task Listener est un assistant ambiant local capable de capter la parole naturelle, d’en extraire des actions et de les transformer en éléments organisés dans des listes consultables depuis une application mobile.

Le système repose sur une architecture local-first avec transcription Whisper, extraction d’actions, backend FastAPI et application Flutter.

---

## Vision

Construire un assistant ambiant utilisable au quotidien pour capturer sans friction :

- des courses
- des tâches personnelles
- des tâches pro
- des rendez-vous
- des idées

avec un fonctionnement progressif :

voix → compréhension → décision → stockage → consultation / correction mobile

---

## Démo rapide

### Tu dis
- « acheter 2 litres de lait »
- « il faut appeler le plombier demain »
- « tiens j’ai une idée de jeu »

### Tu obtiens automatiquement
- 2 l de lait dans shopping
- une tâche todo « plombier »
- une idée à confirmer dans pending

---

## Architecture

Microphone / source audio
↓
VAD listener
↓
Transcription locale MLX Whisper
↓
Extraction d’actions (règles + fallback LLM)
↓
Backend FastAPI
↓
Stockage JSON local
↓
Application mobile Flutter
↓
Synchronisation temps réel via WebSocket

---

## Stack technique

### Backend
- Python
- FastAPI
- stockage JSON local
- logique métier dans `storage.py`

### Audio / IA
- VAD local
- MLX Whisper
- règles d’extraction
- fallback LLM pour cas ambigus

### Frontend mobile
- Flutter
- WebSocket temps réel
- édition et validation depuis l’UI

---

## Fonctionnalités actuelles

### 1. Capture et transcription
- écoute semi-continue avec VAD
- transcription locale avec MLX Whisper
- latence fortement réduite avec `whisper-small-mlx`

### 2. Extraction d’actions
- shopping
- todo
- todo pro
- rendez-vous
- idées
- support multi-actions
- décisions :
  - `add`
  - `confirm`
  - `ignore`

### 3. Compréhension des formulations naturelles
Exemples supportés :
- `il faut que j'achète 1 kg d'orange`
- `2 litres de lait`
- `3 pommes`
- `il faut appeler le plombier demain`
- `prends rendez-vous chez le dentiste`
- `j'ai une idée de sortie en forêt`

### 4. Shopping intelligence
- parsing quantité / unité
- catégorisation automatique
- regroupement par catégorie dans l’UI
- apprentissage des catégories utilisateur
- apprentissage des synonymes utilisateur
- fusion intelligente des items

Exemples :
- `10 poires` + `3 poires` → `13 poires`
- `poires` + `10 poires` → `10 poires`
- `2 kg pommes` + `3 pommes` → deux lignes distinctes
- `patates` renommé en `pommes de terre` → apprentissage du synonyme

### 5. Pending / confirmation
- stockage temporaire des actions à confirmer
- validation depuis le mobile
- rejet depuis le mobile
- édition partielle lors de la confirmation

### 6. Mobile app
- dashboard des listes
- compteurs
- affichage des items
- ajout manuel
- suppression
- renommage
- toggle done
- changement de catégorie shopping
- rafraîchissement automatique
- synchronisation temps réel via WebSocket

---

## Types de listes

- `shopping`
- `todo`
- `todo_pro`
- `appointments`
- `ideas`

---

## Apprentissage utilisateur

Le système apprend progressivement des corrections utilisateur.

### Catégories apprises
Exemple :
- `clémentines` → `fruits`

### Synonymes appris
Exemple :
- `patates` → `pommes de terre`

Ces apprentissages sont persistés dans :

    data/user_learning.json

---

## Fichiers de données

Les listes sont stockées localement en JSON :

    data/shopping.json
    data/todo.json
    data/todo_pro.json
    data/appointments.json
    data/ideas.json
    data/pending.json
    data/user_learning.json

---

## API principales

### Listes
- `GET /lists`
- `GET /lists/{list_name}`
- `POST /lists/{list_name}`
- `DELETE /lists/{list_name}/item/{item_id}`
- `PATCH /lists/{list_name}/item/{item_id}`
- `PATCH /lists/{list_name}/item/{item_id}/rename`
- `PATCH /lists/{list_name}/item/{item_id}/category`

### Pending
- `GET /pending`
- `POST /pending/{item_id}/approve`
- `DELETE /pending/{item_id}`

### Temps réel
- `WS /ws`
- `POST /internal/notify`

### Audio / extraction
- `POST /extract`
- `POST /transcribe-file`
- `POST /audio-to-action`

---

## Installation

### Backend

    cd backend
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    uvicorn app.main:app --reload

### Listener vocal

    python listen_loop.py

### Mobile

    cd mobile
    flutter pub get
    flutter run -d chrome

---

## État actuel

Le pipeline complet est fonctionnel :

- parole → transcription
- transcription → action
- action → stockage
- stockage → mobile
- correction utilisateur → apprentissage persistant

Le système est déjà utilisable comme prototype avancé local-first.

---

## Limitations actuelles

- pas de conversion d’unités (`g ↔ kg`, `ml ↔ l`)
- gestion des dates encore simple
- arbitrage règles / LLM encore basique
- édition mobile encore incomplète sur quantité / unité
- stockage encore en JSON local, pas en base de données

---

## Roadmap courte

### Court terme
- édition complète d’un item shopping (texte + quantité + unité + catégorie)
- gestion avancée des dates et échéances
- enrichissement du vocabulaire utilisateur

### Moyen terme
- arbitrage avancé règles vs LLM
- feedback audio (TTS)
- capture audio via ESP32
- gestion multi-pièces

### Long terme
- assistant ambiant distribué
- synchronisation multi-device
- intégration agenda / rappels
- gestion du contexte (personnes, projets, lieux)

---

## Statut

Prototype local avancé en forte consolidation, avec intelligence métier croissante, apprentissage utilisateur persistant et synchronisation temps réel.

---

## Contribution

Projet personnel en cours d’exploration.
Contributions, idées et feedback bienvenus.

---

## Licence

À définir.
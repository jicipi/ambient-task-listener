# Ambient Task Listener — Development Roadmap

## Vision

Construire un assistant ambiant capable de capter la parole naturelle, d’en extraire des actions et de les transformer en éléments organisés dans des listes consultables depuis une application mobile.

Architecture cible :

Microphones (ESP32)
↓
Audio streaming
↓
Python listener (VAD + Whisper)
↓
Extraction d’actions
↓
Backend FastAPI
↓
Stockage JSON / DB
↓
Application mobile Flutter

---

# Phase 1 — Prototype local (Done)

Objectif : démontrer la faisabilité complète du pipeline voix → tâche.

Audio & transcription
- [x] capture micro locale
- [x] écoute semi-continue avec VAD
- [x] transcription locale MLX Whisper

Extraction d’actions
- [x] extraction d’action simple
- [x] support multi-actions dans une phrase

Stockage
- [x] stockage JSON local

Backend
- [x] API FastAPI pour les listes

Application mobile
- [x] application Flutter
- [x] dashboard avec listes
- [x] affichage des items
- [x] ajout d’un item
- [x] suppression d’un item
- [x] renommage d’un item
- [x] toggle done
- [x] tri intelligent
- [x] compteurs sur le dashboard
- [x] rename item
- [x] automatic sorting (done items last)
- [x] dashboard counters
- [x] automatic refresh of lists (5s polling)

Résultat :
pipeline voix → action → mobile fonctionnel

---

# Phase 2 — Robustesse de compréhension

Objectif : améliorer la fiabilité de l’extraction d’actions.

- [ ] correction ASR contextuelle
- [ ] déduplication des actions
- [ ] meilleure gestion des formulations naturelles
- [ ] gestion avancée des dates et échéances
- [ ] apprentissage du vocabulaire utilisateur
- [ ] résolution d’ambiguïtés (pompier / plombier)

---

# Phase 3 — Expérience assistant

Objectif : rendre l’assistant réellement agréable à utiliser.

- [ ] confirmation intelligente des actions
- [ ] meilleure gestion des silences
- [ ] segmentation plus robuste des phrases
- [ ] amélioration de listen_loop.py
- [ ] wake word local

---

# Phase 4 — Interface & interaction

Objectif : améliorer l’expérience utilisateur mobile.

- [ ] rafraîchissement automatique des listes
- [ ] WebSocket temps réel
- [ ] swipe gestures (delete / edit)
- [ ] édition inline
- [ ] animations d’apparition des tâches
- [ ] notifications / rappels

---

# Phase 5 — Hardware

Objectif : transformer le prototype en assistant ambiant physique.

- [ ] intégrer ESP32 comme front-end audio
- [ ] streaming audio vers backend
- [ ] expérimentation multi-micro
- [ ] test INMP441 vs ICS-43434
- [ ] conception d’un boîtier 3D

---

# Phase 6 — Architecture hybride règles + IA

Objectif : combiner règles rapides et compréhension LLM.

- [ ] garder les règles pour les cas évidents
- [ ] ajouter un interpréteur LLM en fallback
- [ ] comparer règles vs LLM
- [ ] arbitrage automatique selon confiance

---

# Phase 7 — Produit final

Objectif : assistant ambiant réellement utilisable au quotidien.

- [ ] gestion multi-pièces
- [ ] synchronisation mobile
- [ ] intégration agenda
- [ ] rappels intelligents

---

# Extensions possibles

Ajouter une catégorie :

ideas

Exemples :

- idée de blague
- idée de projet
- idée de jeu de mots
- note vocale rapide

Objectif :

capturer toute pensée rapide sans friction.

---

# Backlog long terme

- mémos vocaux
- capture audio créative
- détection d’idées musicales
- transcription musicale expérimentale
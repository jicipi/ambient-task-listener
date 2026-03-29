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

## Audio & transcription
- [x] capture micro locale
- [x] écoute semi-continue avec VAD
- [x] transcription locale MLX Whisper

## Extraction d’actions
- [x] extraction d’action simple
- [x] support multi-actions dans une phrase

## Stockage
- [x] stockage JSON local

## Backend
- [x] API FastAPI pour les listes

## Application mobile
- [x] application Flutter
- [x] dashboard avec listes
- [x] affichage des items
- [x] ajout d’un item
- [x] suppression d’un item
- [x] renommage d’un item
- [x] toggle done
- [x] tri intelligent
- [x] compteurs sur le dashboard
- [x] rafraîchissement automatique des listes
- [x] WebSocket temps réel

Résultat :  
pipeline voix → action → mobile fonctionnel

---

# Phase 2 — Robustesse de compréhension

Objectif : améliorer la fiabilité de l’extraction d’actions.

- [x] déduplication sémantique des tâches
- [x] amélioration partielle des formulations shopping
- [x] parsing quantités / unités pour shopping
- [x] catégorisation automatique des courses
- [x] apprentissage des catégories utilisateur (persisté)
- [x] mise à jour dynamique des catégories depuis l’UI
- [x] mise à jour temps réel via WebSocket (backend → mobile)
- [x] normalisation des items (cleaning + parsing centralisé)
- [~] cohérence des opérations CRUD (édition + fusion + apprentissage)
- [~] cohérence backend ↔ mobile (WebSocket, refresh, sync état)
- [~] correction ASR contextuelle (premières règles locales)
- [~] meilleure gestion des formulations naturelles todo / todo pro
- [ ] gestion avancée des dates et échéances
- [~] apprentissage utilisateur (catégories + synonymes OK, vocabulaire à étendre)
- [ ] résolution d’ambiguïtés (pompier / plombier)
- [~] fusion intelligente des quantités (édition + renommage + ajout, hors conversion d’unités)
- [x] fusion à l’ajout alignée avec l’édition
- [ ] conversion d’unités (ex : g ↔ kg, ml ↔ l)
- [ ] synonymes métier (ex : patates → pommes de terre)

---

# Phase 3 — Moteur de décision assistant

Objectif : transformer le système en assistant intelligent capable de décider quoi faire avec une phrase.

## Décision intelligente

- [x] introduction des décisions : add / confirm / ignore
- [x] distinction règles fortes vs faible confiance
- [x] filtrage des phrases non pertinentes
- [x] intégration temps réel dans listen_loop avec feedback utilisateur

## Améliorations à venir

- [ ] ajustement dynamique du seuil de confiance
- [~] confirmation utilisateur simple (UI)
- [ ] confirmation utilisateur avancée (édition + validation)
- [ ] priorisation des actions
- [ ] gestion des actions multiples complexes

---

## Compréhension hybride règles + IA

- [x] règles pour cas simples
- [x] fallback LLM pour cas ambigus
- [ ] arbitrage avancé règles vs IA
- [ ] score de confiance combiné

---

## Préparation interaction utilisateur

- [ ] stockage temporaire des actions à confirmer
- [ ] feedback utilisateur (valider / refuser)
- [ ] apprentissage des corrections

---

Résultat attendu :

Le système devient capable de :

- ignorer le bruit
- détecter les intentions utiles
- décider automatiquement ou demander confirmation

---

# Phase 4 — Interface & interaction

Objectif : améliorer l’expérience utilisateur mobile.

- [x] regroupement des courses par catégorie
- [x] affichage quantité + unité dans les listes
- [ ] tri manuel / bouton de tri
- [ ] ordre de catégories personnalisé
- [ ] swipe gestures (delete / edit)
- [ ] édition inline
- [ ] animations d’apparition des tâches
- [ ] notifications / rappels
- [ ] mode “courses” optimisé pour usage en magasin

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

- [x] garder les règles pour les cas évidents
- [x] ajouter un interpréteur LLM en fallback
- [ ] comparer règles vs LLM
- [ ] arbitrage automatique selon confiance
- [ ] enrichissement du parsing métier par IA
- [ ] capacité à proposer de nouveaux types d’items

---

# Phase 7 — Produit final

Objectif : assistant ambiant réellement utilisable au quotidien.

- [ ] gestion multi-pièces
- [ ] synchronisation mobile
- [ ] intégration agenda
- [ ] rappels intelligents
- [ ] contexte utilisateur (personnes, projets, lieux)
- [ ] interaction vocale contextuelle

---

# Extensions possibles

## Catégorie ideas
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
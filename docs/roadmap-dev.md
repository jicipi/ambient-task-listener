# Ambient Task Listener — Development Roadmap

## Vision

Construire un assistant ambiant capable de capter la parole naturelle, d'en extraire des actions et de les transformer en éléments organisés dans des listes consultables depuis une application mobile.

Architecture cible :

Microphones (ESP32)  
↓  
Audio streaming  
↓  
Python listener (VAD + Whisper)  
↓  
Extraction d'actions  
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

## Extraction d'actions
- [x] extraction d'action simple
- [x] support multi-actions dans une phrase

## Stockage
- [x] stockage JSON local

## Backend
- [x] API FastAPI pour les listes

## Application mobile
- [x] application Flutter
- [x] dashboard avec listes
- [x] affichage des items
- [x] ajout d'un item
- [x] suppression d'un item
- [x] renommage d'un item
- [x] toggle done
- [x] tri intelligent
- [x] compteurs sur le dashboard
- [x] rafraîchissement automatique des listes
- [x] WebSocket temps réel

Résultat :  
pipeline voix → action → mobile fonctionnel

---

# Phase 2 — Robustesse de compréhension (en cours)

Objectif : améliorer la fiabilité de l'extraction d'actions.

## Fait
- [x] déduplication sémantique des tâches
- [x] amélioration partielle des formulations shopping
- [x] parsing quantités / unités pour shopping
- [x] catégorisation automatique des courses
- [x] apprentissage des catégories utilisateur (persisté)
- [x] mise à jour dynamique des catégories depuis l'UI
- [x] mise à jour temps réel via WebSocket (backend → mobile)
- [x] normalisation des items (cleaning + parsing centralisé)
- [x] fusion à l'ajout alignée avec l'édition
- [~] cohérence des opérations CRUD (édition + fusion + apprentissage)
- [~] cohérence backend ↔ mobile (WebSocket, refresh, sync état)
- [~] correction ASR contextuelle (premières règles locales)
- [~] meilleure gestion des formulations naturelles todo / todo pro
- [~] apprentissage utilisateur (catégories + synonymes OK, vocabulaire à étendre)
- [~] fusion intelligente des quantités (édition + renommage + ajout, hors conversion d'unités)

## Résidus à compléter en priorité
- [x] gestion avancée des dates et échéances — parsing français stdlib-only, affichage mobile trié
- [x] résolution d'ambiguïtés phonétiques (pompier / plombier)
- [x] conversion d'unités (g ↔ kg, ml ↔ l, cl) — fusion cross-unité avec sélection unité lisible
- [x] synonymes métier (patates → pommes de terre)

---

# Phase 2.5 — Stabilité & Tests ← NOUVELLE PHASE (prioritaire)

Objectif : poser le socle technique avant d'aller plus loin. Sans cette phase, chaque refacto risque de casser silencieusement ce qui fonctionne.

## Persistance
- [ ] migration JSON → SQLite (thread-safety, intégrité, pas de corruption)
- [x] verrou threading.RLock sur les écritures JSON
- [ ] script de migration des données existantes

## Tests backend
- [x] setup pytest + structure de tests
- [x] tests unitaires : cleaning (parse_shopping_item, normalize, categorize) — 20 tests
- [x] tests storage : add_item, rename_item, delete, update_done, fusion — 22 tests
- [x] tests de régression sur les bugs corrigés (learn_synonym, décimaux, fusion) — 15 tests
- [ ] tests d'intégration : pipeline complet voix → liste

## Résilience
- [x] timeout court sur Ollama (5s) + fallback gracieux
- [x] gestion propre du cas "Ollama indisponible" (WARNING log)
- [ ] logs structurés (niveau INFO/WARNING/ERROR) — partiellement fait

## Configuration
- [x] URL backend configurable dans l'app Flutter
- [x] support des devices physiques iOS/Android
- [x] backend accessible réseau local (--host 0.0.0.0 + CORS étendu)

## Bugs corrigés (session du 2026-03-31)
- [x] dialog édition shopping : champs quantity/unit séparés
- [x] parse_shopping_item : support décimaux français (0,75 virgule)
- [x] rename_item : ne stocke plus de synonymes depuis l'UI (source de corruption)
- [x] rename_item : passe quantity=None à update_shopping_item (laisse le texte faire foi)

---

# Phase 3 — Moteur de décision assistant

Objectif : transformer le système en assistant intelligent capable de décider quoi faire avec une phrase.

## Décision intelligente (fait)
- [x] introduction des décisions : add / confirm / ignore
- [x] distinction règles fortes vs faible confiance
- [x] filtrage des phrases non pertinentes
- [x] intégration temps réel dans listen_loop avec feedback utilisateur

## À compléter
- [ ] ajustement dynamique du seuil de confiance
- [x] confirmation utilisateur simple (UI pending basique)
- [x] confirmation utilisateur avancée (édition complète : texte, liste, qté, unité, catégorie, date)
- [ ] priorisation des actions
- [ ] gestion des actions multiples complexes

## Compréhension hybride règles + IA
- [x] règles pour cas simples
- [x] fallback LLM pour cas ambigus
- [ ] arbitrage avancé règles vs IA
- [ ] score de confiance combiné règles + LLM

---

# Phase 4 — UX fonctionnelle (items à fort impact quotidien)

Objectif : rendre l'app réellement utilisable au quotidien, pas juste démontrable.

## Priorité haute (impact direct sur l'usage)
- [x] mode "courses" optimisé — plein écran, tap = toggle, swipe suppression, effacer faits
- [x] notifications locales iOS/macOS pour appointments (planifiées à 9h, replanifiées à chaque sync)
- [x] édition inline (sans dialog)
- [x] swipe gestures (delete / edit) — toutes les listes, swipe droit = édition, gauche = suppression

## Priorité normale
- [ ] tri manuel / bouton de tri
- [ ] ordre de catégories personnalisé
- [ ] animations d'apparition des tâches

---

# Phase 5 — IA avancée

Objectif : raffiner la compréhension et réduire les erreurs résiduelles.

> Cette phase est placée avant le hardware : améliorer le cerveau avant de construire le corps.

- [ ] comparer règles vs LLM sur corpus de phrases réelles
- [ ] arbitrage automatique selon confiance combinée
- [ ] enrichissement du parsing métier par IA
- [ ] capacité à proposer de nouveaux types d'items
- [ ] apprentissage actif : les corrections utilisateur alimentent les règles

---

# Phase 6 — Hardware ESP32

Objectif : transformer le prototype en assistant ambiant physique.

> Uniquement quand le logiciel est stable et testé — le hardware amplifie ce qui marche, il ne répare pas ce qui est fragile.

- [ ] intégrer ESP32 comme front-end audio
- [ ] streaming audio vers backend
- [ ] expérimentation multi-micro
- [ ] test INMP441 vs ICS-43434
- [ ] conception d'un boîtier 3D

---

# Phase 7 — Produit final

Objectif : assistant ambiant réellement utilisable au quotidien dans un contexte de vie.

- [ ] gestion multi-pièces
- [ ] synchronisation mobile hors réseau local (tunnel, VPN, cloud optionnel)
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
- détection d'idées musicales
- transcription musicale expérimentale

# Ambient Task Listener — Historique du projet

Ce document retrace l’évolution technique du projet **Ambient Task Listener**, depuis le prototype vocal local jusqu’à l’intégration d’une application mobile.

---

# 2026-03 — Prototype vocal local fonctionnel

## Environnement

- setup ESP-IDF validé pour ESP32-P4
- build `hello_world` réussi
- backend Python arm64 configuré sur Mac Apple Silicon
- MLX Whisper opérationnel localement

## Audio local

- capture micro fonctionnelle sur Mac
- enregistrement au sample rate natif du device
- prototype `record_and_extract.py` fonctionnel
- prototype `listen_loop.py` avec WebRTC VAD

## Pipeline vocal

Pipeline complet validé :

micro  
→ capture audio  
→ transcription Whisper MLX  
→ normalisation  
→ extraction d’intention  
→ stockage JSON  

---

# 2026-03 — Compréhension vocale

## Extraction d’intentions

Support des intentions suivantes :

- shopping
- todo
- appointments
- ideas

## Formulations naturelles supportées

Exemples :

- il faut acheter
- il faut que j'achète
- il faut que j'appelle
- prendre rendez-vous

## Capacités supplémentaires

- segmentation multi-actions dans une phrase
- normalisation de transcription  
  exemple : "de main" → "demain"

## Gestion des dates simples

Support des indices temporels :

- demain
- ce soir
- week-end
- jours de semaine

---

# 2026-03 — Architecture hybride règles + IA

Le moteur de compréhension combine deux approches.

## Règles

Pour les cas simples :

- achat
- appel
- prise de rendez-vous
- ajout d’idée

## LLM local

Fallback via :

Ollama + llama3.2

Utilisé pour :

- phrases ambiguës
- formulations complexes

Pipeline :

transcript  
→ extraction par règles  
→ fallback LLM si nécessaire  

---

# 2026-03 — Stockage des données

Stockage persistant local en JSON.

Fichiers :

backend/data/shopping.json  
backend/data/todo.json  
backend/data/appointments.json  
backend/data/ideas.json  

Fonctionnalités :

- stockage persistant
- ajout automatique d’items
- premières règles de déduplication

---

# 2026-03 — Outils CLI

Scripts disponibles :

record_and_extract.py  
listen_loop.py  
show_lists.py  

Fonctions :

- enregistrement audio
- écoute continue avec VAD
- affichage des listes en CLI

---

# 2026-03 — Backend API

Le backend devient un service applicatif complet.

Framework utilisé :

FastAPI

Endpoints disponibles :

GET /health  
GET /lists  
GET /lists/{list_name}  
POST /lists/{list_name}  
DELETE /lists/{list_name}/item/{item_id}  
PATCH /lists/{list_name}/item/{item_id}  
PATCH /lists/{list_name}/item/{item_id}/rename  

Ces endpoints permettent :

- lecture des listes
- ajout manuel d’items
- suppression d’items
- modification d’un item
- marquage d’une tâche comme faite

Documentation automatique via Swagger.

---

# 2026-03 — Nettoyage des données

Nettoyage des listes historiques avant l’introduction de l’application mobile.

Actions réalisées :

- suppression des doublons
- normalisation des items
- correction des anciennes formes bruitées
- conservation d'une base propre pour les tests API et mobile

Résultat :

- shopping nettoyée
- todo simplifiée
- ideas conservée propre

---

# 2026-03 — Application mobile Flutter

Création d’une application Flutter connectée au backend.

Plateformes supportées :

- Web
- Android
- iOS

## Fonctionnalités

- dashboard des listes
- affichage des items
- ajout manuel d’un item
- suppression d’un item
- renommage d’un item
- validation d’une tâche (done / undone)

## Améliorations UX

- tri automatique des items
  - tâches ouvertes en premier
  - tâches terminées en dernier
- tri alphabétique
- compteurs sur le dashboard
- rafraîchissement automatique des listes (polling toutes les 5 secondes)

Architecture :

Flutter app  
↓  
API FastAPI  
↓  
JSON storage  

---

# 2026-03 — Amélioration du pipeline vocal

Plusieurs améliorations importantes ont été ajoutées pour fiabiliser l’assistant.

## Correction fuzzy limitée

La correction automatique est désormais désactivée pour les courses.

Avant :

chocolat → lait

Après :

chocolat → chocolat

---

## Déduplication sémantique des tâches

Ajout d’une forme canonique pour comparer les tâches.

Exemples :

plombier  
appeler le plombier  

sont maintenant considérés comme la même tâche.

Règles appliquées :

suppression des verbes initiaux :

- appeler
- envoyer
- préparer
- organiser
- traiter

suppression des articles :

- le
- la
- les
- un
- une
- du
- des

Exemples :

appeler le plombier → plombier  
préparer la réunion data4 → réunion data4  
organiser le comité projet → comité projet  

---

# État actuel du système

Le projet fonctionne désormais de bout en bout.

Pipeline complet :

microphone  
→ VAD  
→ Whisper MLX  
→ normalisation texte  
→ extraction d’intention  
→ fallback LLM  
→ stockage JSON  
→ API FastAPI  
→ application Flutter  

L’utilisateur peut :

- dicter une tâche
- voir apparaître la tâche dans l’application
- modifier ou supprimer la tâche

Le projet constitue désormais un prototype fonctionnel d’assistant ambiant domestique.

---

# Prochaines étapes envisagées

- bouton micro directement dans l’application mobile
- communication temps réel (WebSocket)
- intégration ESP32 pour capture audio distante
- gestion multi-pièces
- synchronisation mobile
- rappels et agenda
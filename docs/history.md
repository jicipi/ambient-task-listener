# Ambient Task Listener — Historique du projet

Ce document retrace l’évolution technique et produit du projet **Ambient Task Listener**, depuis un prototype vocal local jusqu’à une application mobile connectée.

---

# 2026-03 — Prototype vocal local fonctionnel

## Environnement

- setup ESP-IDF validé pour ESP32-P4
- build `hello_world` réussi
- backend Python arm64 configuré sur Mac Apple Silicon
- MLX Whisper opérationnel en local

## Audio local

- capture micro fonctionnelle sur Mac
- enregistrement au sample rate natif du device
- prototype `record_and_extract.py` fonctionnel
- prototype `listen_loop.py` avec WebRTC VAD

## Pipeline vocal initial

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

- backend/data/shopping.json  
- backend/data/todo.json  
- backend/data/appointments.json  
- backend/data/ideas.json  

Fonctionnalités :

- stockage persistant
- ajout automatique d’items
- premières règles de déduplication

---

# 2026-03 — Outils CLI

Scripts disponibles :

- record_and_extract.py  
- listen_loop.py  
- show_lists.py  

Fonctions :

- enregistrement audio
- écoute continue avec VAD
- affichage des listes en CLI

---

# 2026-03 — Backend API

Le backend devient un service applicatif complet.

Framework utilisé :

FastAPI

## Endpoints disponibles

- GET /health  
- GET /lists  
- GET /lists/{list_name}  
- POST /lists/{list_name}  
- DELETE /lists/{list_name}/item/{item_id}  
- PATCH /lists/{list_name}/item/{item_id}  
- PATCH /lists/{list_name}/item/{item_id}/rename  

## Capacités

- lecture des listes
- ajout manuel d’items
- suppression d’items
- modification d’un item
- marquage d’une tâche comme faite

Documentation automatique via Swagger.

---

# 2026-03 — Nettoyage des données

Nettoyage des listes historiques avant l’introduction de l’application mobile.

## Actions réalisées

- suppression des doublons
- normalisation des items
- correction des formes bruitées
- consolidation des données existantes

## Résultat

- shopping nettoyée
- todo simplifiée
- ideas conservée propre

---

# 2026-03 — Application mobile Flutter

Création d’une application Flutter connectée au backend.

## Plateformes supportées

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
- rafraîchissement automatique des listes (polling)

## Architecture

Flutter app  
↓  
API FastAPI  
↓  
JSON storage  

---

# 2026-03 — Synchronisation temps réel

Ajout d’un mécanisme de mise à jour en temps réel.

## Implémentation

- WebSocket côté backend
- écoute côté application Flutter

## Résultat

- mise à jour instantanée des listes
- suppression du besoin de polling

---

# 2026-03 — Amélioration du pipeline vocal

## Correction fuzzy limitée

La correction automatique est désactivée pour les courses afin d’éviter les erreurs critiques.

Exemple :

chocolat → lait ❌  
chocolat → chocolat ✅  

---

## Déduplication sémantique des tâches

Ajout d’une forme canonique pour comparer les tâches.

### Règles appliquées

- suppression des verbes initiaux :
  - appeler
  - envoyer
  - préparer
  - organiser
  - traiter

- suppression des articles :
  - le
  - la
  - les
  - un
  - une
  - du
  - des

### Exemples

- appeler le plombier → plombier  
- préparer la réunion data4 → réunion data4  
- organiser le comité projet → comité projet  

---

# 2026-03 — Smart shopping parsing (v0.3)

Amélioration majeure de la gestion des listes de courses.

## Parsing intelligent

Extraction automatique de :

- quantité
- unité
- item

Exemples :

- "acheter 2 litres de lait" → 2 l lait  
- "acheter 3 kg de carottes" → 3 kg carottes  

## Nettoyage avancé

- suppression des suffixes inutiles  
  ("à la liste", "sur la liste")
- suppression des démonstratifs  
  ("cette banane" → banane)

## Catégorisation automatique

Classification des items :

- fruits
- légumes
- produits laitiers
- etc.

### Cas particuliers gérés

- gestion des pluriels  
  ("pommes de terre")
- priorisation des expressions longues  
- correction du bug :
  "pomme de terre" → légumes (et non fruits)

## Amélioration UI

Application mobile :

- regroupement des items par catégorie
- affichage structuré type liste de courses réelle

## Résultat

Passage d’un stockage simple à :

→ une liste de courses structurée et exploitable  

→ amélioration significative de l’expérience utilisateur en situation réelle  

→ base solide pour des optimisations futures (fusion d’items, tri magasin, etc.)

---

# État actuel du système

Le projet fonctionne de bout en bout.

## Pipeline complet

microphone  
→ VAD  
→ Whisper MLX  
→ normalisation texte  
→ extraction d’intention  
→ fallback LLM  
→ parsing métier  
→ stockage JSON  
→ API FastAPI  
→ application Flutter  

## Capacités utilisateur

L’utilisateur peut :

- dicter une tâche ou une course
- voir apparaître l’item dans l’application en temps réel
- modifier ou supprimer un item
- valider une tâche

Le système constitue un prototype fonctionnel d’assistant ambiant personnel.

---

# Prochaines étapes envisagées

## Court terme

- fusion intelligente des quantités  
  (ex : 2 l + 1 l → 3 l)
- amélioration du parsing (unités complexes)
- amélioration du tri par catégories

## Moyen terme

- bouton micro intégré dans l’application mobile
- intégration ESP32 pour capture audio distante
- gestion multi-pièces

## Long terme

- assistant ambiant distribué
- synchronisation multi-device
- intégration agenda / rappels
- contextualisation (personnes, projets, lieux)

---

# 2026-03 — Introduction du moteur de décision assistant

Une évolution majeure du système a été introduite : le passage d’un simple extracteur d’actions à un **moteur de décision assistant**.

## Problème initial

Le système ajoutait automatiquement toute action détectée :

transcript → extraction → ajout

Limites :

- ajout de bruit dans les listes
- incapacité à gérer l’ambiguïté
- aucune distinction entre cas sûrs et incertains
- pas de base pour interaction utilisateur

---

## Nouvelle architecture : décision intelligente

Chaque action extraite est désormais associée à une décision :

- `add` → ajout automatique
- `confirm` → nécessite validation utilisateur
- `ignore` → ignoré

---

## Pipeline mis à jour

audio  
→ VAD  
→ transcription (Whisper MLX)  
→ normalisation  
→ extraction (règles)  
→ fallback LLM (si nécessaire)  
→ décision (add / confirm / ignore)  
→ stockage  

---

## Règles de décision

### Cas simples (règles fortes)

Exemple :

- acheter 2 litres de lait

→ `decision = add`

---

### Cas ambigus / faible confiance

Exemple :

- tiens j’ai une idée de jeu
- pense au devis

→ `decision = confirm`

---

### Cas non pertinents

Exemple :

- ok
- merci
- bruit conversationnel

→ `decision = ignore`

---

## Intégration dans le code

Ajouts principaux :

- champ `decision` dans les résultats
- champ `source` (`rule` / `llm`)
- logique de filtrage dans `listen_loop.py`

---

## Impact

Le système devient :

- plus fiable
- moins bruité
- prêt pour interaction utilisateur
- compatible avec une future interface vocale (TTS)

---

## Nouvelle capacité clé

Le système ne fait plus seulement :

→ comprendre une phrase  

Il fait désormais :

→ **interpréter une intention et décider quoi faire**

---

## 2026-03-28 — Shopping intelligence & real-time sync

### Backend
- ajout update_item_category avec apprentissage automatique
- ajout update_shopping_item avec logique de fusion
- fusion intelligente des items (quantité / unité / texte)
- correction des routes FastAPI pour notifier le frontend

### Mobile
- édition d’un item avec changement de catégorie
- regroupement dynamique par catégorie

### Temps réel
- synchronisation WebSocket stabilisée
- notification après ajout / suppression / édition / catégorie

### Qualité produit
- cohérence entre renommage, catégorie et fusion
- comportement métier validé :
  - "10 poires" + "poires" → 10 poires
  - "10 poires" + "3 poires" → 13 poires

### Limitations connues
- pas de conversion d’unités (kg ↔ g)
- pas de gestion avancée des synonymes


## 2026-03-29 — Shopping intelligence, user learning and real-time sync

### Backend
- stabilisation de `action_extractor.py`
- correction des patterns shopping pour supporter les formulations nominales :
  - `2 litres de lait`
  - `1 kg de pommes`
  - `3 pommes`
- ajout du support impératif pour les rendez-vous :
  - `prends rendez-vous chez le dentiste`
  - `prenez rendez-vous avec l'ostéo`

### Shopping intelligence
- parsing robuste des quantités / unités
- catégorisation automatique des courses
- ajout de la mise à jour de catégorie via API
- ajout de l’apprentissage persistant des catégories utilisateur
- ajout de l’apprentissage persistant des synonymes utilisateur
- application des synonymes dans `add_item()`
- fusion intelligente des items shopping :
  - fusion si unités compatibles
  - pas de fusion si unités incompatibles (`kg` vs sans unité)

### Exemples validés
- `10 poires` + `3 poires` → `13 poires`
- `poires` + `10 poires` → `10 poires`
- `2 kg pommes` + `3 pommes` → deux lignes distinctes
- `patates` renommé en `pommes de terre` → apprentissage du synonyme
- ajout ultérieur de `3 patates` → fusion en `pommes de terre`

### Mobile
- édition d’un item shopping
- changement manuel de catégorie depuis l’UI
- synchronisation temps réel stabilisée via WebSocket
- rafraîchissement après opérations CRUD

### Pending / confirmation
- confirmation utilisateur simple opérationnelle
- validation / rejet depuis l’UI
- édition partielle lors de la confirmation

### Performance
- passage à `mlx-community/whisper-small-mlx`
- forte réduction de la latence de transcription
- temps observés ~0.2s à 0.5s après warm-up

### Limitations connues
- pas de conversion d’unités (`g ↔ kg`, `ml ↔ l`)
- pas de gestion avancée des échéances / dates
- pas d’arbitrage avancé règles vs LLM
- pas encore d’édition complète quantité / unité depuis le mobile
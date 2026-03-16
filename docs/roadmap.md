# Ambient Task Listener - Roadmap

## 1) Roadmap de developpement

### Phase 1 - Bring up hardware

Objectif: lire le microphone.

Tests:

- Capture audio
- Sauvegarde WAV sur SD

### Phase 2 - Streaming audio

Envoyer audio vers le Mac via WiFi.

### Phase 3 - Transcription

Utiliser Whisper.

### Phase 4 - Detection d'action

Classifier:

- Action
- Discussion

### Phase 5 - Creation tache

Extraire:

Verbe + objet

Exemple:

Acheter -> lait

### Phase 6 - Application mobile

Flutter app.

### Phase 7 - Ecoute passive

Ajouter VAD.

### Phase 8 - Apprentissage domestique

Le systeme apprend les patterns.

## 2) Twists avances

### Memoire domestique

Le systeme detecte les repetitions.

"On n'a plus de cafe" repete -> suggestion automatique.

### Graph de taches

Les taches deviennent liees.

"Prendre RDV dentiste" -> rappel automatique.

### Contexte

Le systeme comprend le contexte temporel.

"Demain" -> date automatique.

## 3) Roadmap simplifiee

### Phase 1 - Bring-up ESP32

- Flasher un exemple
- Verifier USB / serie
- Afficher des logs

### Phase 2 - Microphone I2S

- Lire le micro
- Enregistrer un WAV
- Stocker sur SD

### Phase 3 - Streaming audio

- Envoyer audio au Mac
- Protocole simple HTTP ou WebSocket

### Phase 4 - Transcription

- Traiter audio avec Whisper local
- Afficher texte brut

### Phase 5 - Extraction d'action

- Classifier action / non action
- Extraire verbe + objet

### Phase 6 - Application mobile

- Listes Courses / Taches / RDV
- Affichage et confirmation

### Phase 7 - Ecoute passive

- Ajouter VAD
- Limiter l'envoi audio aux segments utiles

### Phase 8 - Memoire domestique

- Detecter repetitions
- Proposer automatiquement des ajouts

# Ambient Task Listener - Architecture

## 1) Architecture generale

### Architecture globale

ESP32 Device

- Microphone I2S
- VAD (detection parole)
- Streaming audio
- Speaker (feedback)
- Ecran (UI)

↓

Serveur IA (MacBook / serveur local)

- Transcription Whisper
- Analyse intention
- Extraction action

↓

Application mobile

- Affichage listes
- Confirmation actions
- Historique

## 2) Architecture logicielle

### Firmware ESP32

Modules principaux:

- `AudioInput`: capture micro I2S
- `VAD`: detection activite vocale
- `AudioStreamer`: envoi audio WebSocket
- `DeviceUI`: ecran TFT, LED, bouton mute
- `Speaker`: feedback audio

### Backend IA

Pipeline:

Audio  
↓  
Transcription (Whisper)  
↓  
Extraction intention  
↓  
Extraction objet  
↓  
Creation tache

### Application mobile

Sections:

- Courses
- Taches
- Rendez-vous
- Historique
- Parametres

## Mobile Application

The project now includes a Flutter mobile application.

Architecture:

ESP32 microphones (future)
        ↓
Python listener (Whisper / extraction)
        ↓
FastAPI backend
        ↓
JSON storage
        ↓
Flutter mobile / web app

The Flutter app communicates with the backend through REST endpoints.

Implemented features:

- View lists
- Add item
- Delete item
- Rename item
- Toggle done
- Sorted display
- Dashboard with counters

---

## Mobile Application Layer

The project now includes a Flutter application used to interact with the assistant.

Current features:

- dashboard showing all lists
- view items in each list
- add item manually
- delete item
- rename item
- toggle item done
- automatic sorting (open items first)
- counters on dashboard
- automatic refresh every 5 seconds

The Flutter app communicates with the backend through REST endpoints.

Architecture:

Microphone input  
→ Python listener (VAD + Whisper)  
→ action extraction  
→ FastAPI backend  
→ JSON storage  
→ Flutter mobile/web app

### Shopping parsing pipeline

1. Nettoyage du transcript
2. Extraction item
3. Parsing quantité / unité
4. Normalisation
5. Catégorisation
6. Stockage JSON
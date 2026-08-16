# 🎬 YouTube Downloader (YouPiv)

[![Python CI](https://github.com/fordimalanda/youpiv/actions/workflows/ci.yml/badge.svg)](https://github.com/fordimalanda/youpiv/actions/workflows/ci.yml)
[![Docker Build CI](https://github.com/fordimalanda/youpiv/actions/workflows/docker-ci.yml/badge.svg)](https://github.com/fordimalanda/youpiv/actions/workflows/docker-ci.yml)
[![Security Analysis](https://github.com/fordimalanda/youpiv/actions/workflows/security.yml/badge.svg)](https://github.com/fordimalanda/youpiv/actions/workflows/security.yml)
![Python 3.13](https://img.shields.io/badge/Python-3.13-blue.svg)
![Django 5.1](https://img.shields.io/badge/Django-5.1+-092E20.svg)
![Docker](https://img.shields.io/badge/Docker-Enabled-2496ED.svg)

Application Web moderne et réactive développée avec **Django** et **Docker**, permettant de télécharger des vidéos YouTube avec suivi en temps réel de la progression et transfert direct du fichier dans le dossier de téléchargement du navigateur client.

---

## 🌟 Fonctionnalités

- 🚀 **Téléchargement rapide & haute qualité** : Utilise `yt-dlp` et `ffmpeg` pour extraire et combiner les flux audio/vidéo en format MP4.
- 📊 **Progression en temps réel** : Suivi fluide par polling HTTP (pourcentage, vitesse de téléchargement, taille téléchargée, temps restant ETA).
- 💾 **Téléchargement direct dans le navigateur** : Une fois la vidéo préparée par le serveur, le fichier est automatiquement transmis et enregistré dans le dossier de téléchargement de l'utilisateur (Chrome, Firefox, Safari, Edge, Mobile).
- 🎨 **Interface Dark Mode moderne** : Design sobre, responsive et épuré (Glassmorphism & animations CSS).
- 🐳 **Conteneurisation totale** : Déploiement instantané avec Docker et Docker Compose.
- 🛡️ **Qualité & Sécurité** : Tests automatisés, linting `flake8`, analyse de sécurité `Bandit` et audits de dépendances `pip-audit`.

---

## 🛠️ Stack Technique

- **Backend** : Python 3.13, Django 5.1+
- **Moteur de téléchargement** : `yt-dlp`, `FFmpeg`
- **Frontend** : HTML5 sémantique, Vanilla CSS (Dark Mode), Javascript ES6 Async/Await
- **Conteneurisation** : Docker, Docker Compose
- **CI/CD** : GitHub Actions (`ci.yml`, `docker-ci.yml`, `security.yml`, `dependabot.yml`)

---

## 🚀 Démarrage Rapide

### Prérequis

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) ou Docker Engine.

### 1. Démarrer avec Docker (Recommandé)

Lancez la commande suivante à la racine du projet :

```bash
docker compose up --build
```

L'application est ensuite accessible sur : **`http://localhost:8000`**

### 2. Arrêt et reconstruction

```bash
# Arrêter le conteneur
docker compose down

# Reconstruire et relancer
docker compose up --build
```

---

## 💻 Exécution en Local (Sans Docker)

Si vous préférez exécuter l'application sans Docker :

1. Assurez-vous d'avoir **Python 3.12+** et **FFmpeg** installés sur votre système.
2. Installez les dépendances Python :

```bash
pip install -r requirements.txt
```

3. Lancez le serveur de développement Django :

```bash
python manage.py runserver
```

---

## 📡 Endpoints API

| Méthode | Route | Description |
| :--- | :--- | :--- |
| `GET` | `/` | Page d'accueil de l'application Web. |
| `POST` | `/download/` | Démarre le traitement d'une vidéo YouTube (prend un JSON `{"url": "..."}`). Retourne un `download_id`. |
| `GET` | `/progress/<download_id>/` | Renvoie l'état d'avancement du téléchargement (pourcentage, vitesse, ETA, `download_url`). |
| `GET` | `/file/<download_id>/` | Transmet le fichier vidéo au navigateur avec l'en-tête `Content-Disposition: attachment`. |

---

## 🧪 Exécution des Tests

### Avec Docker

```bash
docker compose exec web python manage.py test
```

### Sans Docker

```bash
python manage.py test
```

---

## ⚙️ Architecture & Téléchargement

```
[ Navigateur Client ] ──( 1. POST /download/ )──> [ Serveur Django ]
         │                                              │
         │<──( 2. Restitue download_id )────────────────┤
         │                                              │ (Lance Worker Thread)
         │──( 3. Poll /progress/<id>/ )────────────────>│   └─> yt-dlp + ffmpeg
         │<──( 4. Statut 100% + download_url )──────────┤        └─> Stocke dans /downloads
         │                                              │
         └──( 5. GET /file/<id>/ )─────────────────────>│
         <──( 6. Flux Vidéo attachment )────────────────┘
         └─> Fichier enregistré dans le dossier Téléchargements du client
```

1. **Isolation des threads** : Le traitement vidéo s'exécute dans un thread arrière-plan dédié afin que Django reste réactif pour répondre aux requêtes de progression.
2. **Persistance locale** : Le volume `./downloads` conserve les fichiers sur le serveur hôte.
3. **Distribution client** : L'endpoint `/file/<download_id>/` transmet le fichier au navigateur de l'utilisateur sous forme de pièce jointe HTTP (`attachment`).

---

## ⚙️ Workflows GitHub Actions (CI/CD)

Le projet intègre une suite de workflows automatisés situés dans `.github/workflows/` :

- **`ci.yml`** : Installe `ffmpeg`, vérifie la syntaxe avec `flake8` et exécute les tests unitaires Django sous Python 3.12 et 3.13.
- **`docker-ci.yml`** : Valide le build de l'image Docker (`Dockerfile`) avec cache de layers GitHub Actions.
- **`security.yml`** : Audit de sécurité du code avec `Bandit` et analyse des vulnérabilités des dépendances avec `pip-audit`.
- **`dependabot.yml`** : Mises à jour automatisées de `pip`, `docker` et des actions GitHub.

---

## 📂 Structure du Projet

```text
youpiv/
├── .github/
│   ├── ISSUE_TEMPLATE/       # Formulaires de bugs et fonctionnalités
│   ├── workflows/            # Workflows GitHub Actions (CI, Docker, Security)
│   ├── dependabot.yml        # Configuration des mises à jour automatiques
│   └── PULL_REQUEST_TEMPLATE.md
├── downloader/
│   ├── __init__.py
│   ├── settings.py           # Configuration Django
│   ├── tests.py              # Suite de tests unitaires
│   ├── urls.py               # Routage des URL API
│   ├── views.py              # Logique métier et endpoints
│   └── wsgi.py
├── static/
│   ├── css/
│   │   └── style.css         # Thème sombre et styles de l'UI
│   └── js/
│       └── app.js            # Polling et déclenchement automatique du téléchargement
├── templates/
│   └── index.html            # Template HTML principal
├── .dockerignore
├── .gitignore
├── docker-compose.yml        # Orchestration Docker Compose
├── Dockerfile                # Image Python 3.13-slim avec FFmpeg
├── manage.py
├── README.md
└── requirements.txt          # Dépendances Python (Django, yt-dlp)
```

---

## ⚖️ Avertissement Légal

Cet outil est destiné exclusivement à un usage personnel et au téléchargement de contenus pour lesquels vous possédez les droits nécessaires ou une autorisation explicite des ayants droit. Respectez les conditions d'utilisation des plateformes et les lois sur le droit d'auteur applicables dans votre juridiction.

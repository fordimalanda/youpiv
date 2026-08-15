# YouTube Downloader

Application Django simple, entièrement exécutée dans un seul conteneur Docker. Elle télécharge les vidéos YouTube individuelles pour lesquelles vous détenez les droits nécessaires, affiche une progression par polling HTTP et écrit les fichiers sur l’hôte.

## Prérequis

La seule dépendance externe est **Docker / Docker Desktop**. Python, Django, FFmpeg et les bibliothèques Python sont installés dans l’image.

## Démarrage

```bash
docker compose up --build
```

Ouvrez ensuite <http://localhost:8000>. Collez une URL de vidéo YouTube (`youtube.com/watch?v=...` ou `youtu.be/...`) puis cliquez sur **Télécharger**. Les playlists sont volontairement refusées dans cette première version.

## Téléchargements

Le volume par défaut est :

```yaml
volumes:
  - ./downloads:/downloads
```

Les fichiers apparaissent donc directement dans `downloads/` à la racine du projet sur la machine hôte.

Pour employer le dossier système **Downloads/Téléchargements**, remplacez le chemin dans `docker-compose.yml`, par exemple :

```yaml
# Windows (adaptez le nom d’utilisateur)
- C:/Users/VotreNom/Downloads:/downloads
# Linux/macOS
- /home/votre-nom/Downloads:/downloads
```

Sous Windows, Docker Desktop peut demander l’autorisation de partager le lecteur. Les noms sont nettoyés pour la compatibilité Windows avant écriture dans `/downloads`.

## Tests

Une fois le service démarré :

```bash
docker compose exec web python manage.py test
```

## Arrêt et reconstruction

```bash
docker compose down
docker compose up --build
```

## Fonctionnement

Le téléchargement s’exécute dans un thread afin que Django puisse continuer à répondre à `GET /progress/<download_id>/`. L’état est volontairement conservé en mémoire : il est adapté à cette petite application monocon­teneur et est réinitialisé lors d’un redémarrage.

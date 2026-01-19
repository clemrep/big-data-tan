# 01 - Ingestion Kafka

## Description

Producer Python qui récupère les données de l'API OpenSky Network et les publie sur Kafka.

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  OpenSky API    │ ──► │  Producer       │ ──► │  Kafka Topic    │
│  (REST)         │     │  (Python)       │     │  opensky-data   │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

## Fonctionnement

### Source de données
- **API** : OpenSky Network (`/api/states/all`)
- **Fréquence** : Appel toutes les 15 secondes (respect du rate limiting)
- **Format** : Vecteurs d'état convertis en objets JSON

### Producer Kafka
- **Exécution** : Thread en arrière-plan (daemon)
- **Sérialisation** : JSON → bytes UTF-8
- **Topic** : `opensky-data`

## Schéma des données

Chaque message Kafka contient :

| Champ | Type | Description |
|-------|------|-------------|
| `time` | long | Timestamp Unix |
| `icao24` | string | Identifiant unique de l'avion |
| `callsign` | string | Indicatif d'appel |
| `origin_country` | string | Pays d'origine |
| `longitude` | float | Longitude |
| `latitude` | float | Latitude |
| `baro_altitude` | float | Altitude barométrique (m) |
| `velocity` | float | Vitesse (m/s) |
| `on_ground` | boolean | Au sol ou en vol |
| `vertical_rate` | float | Taux de montée/descente |
| `category` | integer | Catégorie d'aéronef |

## Comment utiliser

### Démarrer le Producer

1. **Exécuter les cellules de configuration** (variables Kafka)
2. **Exécuter la cellule Producer** - Lance le thread en arrière-plan
3. **Vérifier** : Messages `📡 XX vols envoyés` toutes les 15 secondes

### Arrêter le Producer

Exécuter la cellule d'arrêt : `stop_producer = True`

## Points d'attention

- **Rate limiting** : L'API OpenSky limite à ~400 requêtes/jour sans authentification
- **Thread daemon** : S'arrête automatiquement à la fermeture du notebook
- **Connexion Kafka** : Vérifier que Kafka est accessible sur `kafka1:9092`

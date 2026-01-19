# 03 - Streaming Silver & Silver_ML

## Description

Pipeline de transformation depuis Bronze vers deux destinations :
- **Silver** : Données nettoyées et enrichies
- **Silver_ML** : Données avec features pour le Machine Learning (directement depuis Bronze)

## Architecture

```
                              ┌─────────────────┐
                         ┌──► │  Silver Layer   │
                         │    │  (flights)      │
┌─────────────────┐      │    └─────────────────┘
│  Bronze Layer   │ ─────┤
│  (Delta Lake)   │      │    ┌─────────────────┐
└─────────────────┘      └──► │  Silver_ML      │
                              │  (flights_ml)   │
                              │  + airports.csv │
                              └─────────────────┘
```

## Stream 1 : Bronze → Silver

### Transformations
- **Filtrage** : Suppression des vols sans `icao24` ou sans coordonnées GPS
- **Typage** : Conversion timestamp Unix → `event_timestamp`
- **Enrichissement** : Calcul `velocity_kmh = velocity * 3.6`
- **Projection** : Sélection des colonnes utiles

### Schéma Silver
```
event_timestamp, icao24, callsign, origin_country,
longitude, latitude, velocity_kmh, altitude_meters,
on_ground, category
```

## Stream 2 : Bronze → Silver_ML

### Jointure de données
- **Source 1** : Bronze (données de vol)
- **Source 2** : `airports.csv` (référentiel aéroports)
- **Type** : Cross join + filtre distance minimum (avions au sol)

### Features temporelles (Window Functions)

| Feature | Description |
|---------|-------------|
| `prev_altitude` | Altitude observation précédente |
| `prev_velocity` | Vitesse observation précédente |
| `altitude_change` | Variation d'altitude |
| `velocity_change` | Variation de vitesse |
| `observation_rank` | Rang par avion |

### Features Rolling Window

| Feature | Description |
|---------|-------------|
| `rolling_avg_altitude` | Moyenne altitude (5 obs) |
| `rolling_std_altitude` | Écart-type altitude (5 obs) |
| `rolling_avg_velocity` | Moyenne vitesse (5 obs) |

### Label `flight_phase`

| Phase | Condition |
|-------|-----------|
| `GROUND` | `on_ground = true` |
| `TAKEOFF` | Montée >50m à altitude <3000m |
| `CLIMB` | Variation altitude >20m |
| `CRUISE` | Altitude stable (±20m) à >8000m |
| `DESCENT` | Variation altitude <-20m |
| `TRANSITION` | Autre |

## Comment utiliser

### Démarrer les streams

1. **Configuration** - Charge les chemins et crée SparkSession
2. **Aéroports** - Charge le référentiel `airports.csv`
3. **Stream 1** - Lance Bronze → Silver
4. **Stream 2** - Lance Bronze → Silver_ML (avec `foreachBatch`)

### Monitoring

La cellule de monitoring affiche le statut des deux streams toutes les 30 secondes.

### Arrêter

Exécuter la cellule d'arrêt : `query_silver.stop()` et `query_silver_ml.stop()`

## Points d'attention

- **Ordre** : Exécuter APRÈS le notebook 02 (Bronze doit contenir des données)
- **Checkpoints** : Deux checkpoints séparés (`silver_flights` et `silver_ml_flights`)
- **foreachBatch** : Utilisé pour Silver_ML car les window functions nécessitent un traitement par batch
- **Jointure aéroports** : Utilise `broadcast()` pour optimiser la performance

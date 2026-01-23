# 07 - Streaming Gold

## Description

Agrégations temps réel avec fenêtres temporelles sur les données Silver_ML. Ce notebook implémente la couche Gold en streaming pour compléter l'architecture médaillon full streaming.

## Architecture

```
┌─────────────────┐     ┌─────────────────────────────────┐     ┌─────────────────────────┐
│  Silver_ML      │     │      Streaming Gold             │     │      Gold Layer         │
│  (flights_ml)   │ ──► │  - Tumbling Window (1 min)      │ ──► │  streaming_aggregations/│
│                 │     │  - Sliding Window (5 min)       │     │  ├── flight_phase_counts│
└─────────────────┘     └─────────────────────────────────┘     │  └── anomaly_alerts     │
                                                                 └─────────────────────────┘
```

## Requêtes Streaming

### Stream 1 : Comptage par phase de vol

| Paramètre | Valeur |
|-----------|--------|
| **Type de fenêtre** | Tumbling (non-chevauchante) |
| **Durée** | 1 minute |
| **Watermark** | 2 minutes |
| **Groupement** | `flight_phase` |

#### Agrégations calculées

| Métrique | Description |
|----------|-------------|
| `flight_count` | Nombre de vols par phase |
| `avg_altitude` | Altitude moyenne |
| `avg_velocity` | Vitesse moyenne |

#### Schéma de sortie

```
window_start, window_end, flight_phase, flight_count, avg_altitude, avg_velocity
```

### Stream 2 : Alertes anomalies par pays

| Paramètre | Valeur |
|-----------|--------|
| **Type de fenêtre** | Sliding (chevauchante) |
| **Durée** | 5 minutes |
| **Slide** | 1 minute |
| **Watermark** | 6 minutes |
| **Groupement** | `origin_country` |

#### Seuils d'anomalie

| Type | Min | Max |
|------|-----|-----|
| Altitude | -100 m | 12 000 m |
| Vitesse | 0 km/h | 1 000 km/h |

#### Agrégations calculées

| Métrique | Description |
|----------|-------------|
| `total_observations` | Nombre total d'observations |
| `altitude_anomalies` | Nombre d'anomalies altitude |
| `velocity_anomalies` | Nombre d'anomalies vitesse |
| `anomaly_rate` | Taux d'anomalies (0-1) |
| `max_altitude`, `min_altitude` | Extrema altitude |
| `max_velocity` | Vitesse maximale |
| `avg_altitude`, `avg_velocity` | Moyennes |
| `stddev_altitude`, `stddev_velocity` | Écarts-types |

#### Schéma de sortie

```
window_start, window_end, origin_country, total_observations,
altitude_anomalies, velocity_anomalies, anomaly_rate,
max_altitude, min_altitude, max_velocity,
avg_altitude, avg_velocity, stddev_altitude, stddev_velocity
```

## Fenêtres Temporelles

### Tumbling Window (Stream 1)

```
|----1min----|----1min----|----1min----|
     W1           W2           W3
```

Chaque événement appartient à exactement une fenêtre.

### Sliding Window (Stream 2)

```
|--------5min--------|
     |--------5min--------|
          |--------5min--------|
|--1min--|
```

Les fenêtres se chevauchent, permettant une détection plus réactive des anomalies.

## Comment utiliser

### Exécution

1. **Configuration** - Définit les chemins S3 et crée SparkSession
2. **Lecture** - Initialise le stream depuis Silver_ML
3. **Stream 1** - Démarre le comptage par phase de vol
4. **Stream 2** - Démarre la détection d'anomalies
5. **Monitoring** - Affiche le statut toutes les 30 secondes
6. **Vérification** - Consulte les données Gold produites

### Arrêter les streams

```python
query_aggregations.stop()
query_anomalies.stop()
```

## Sorties Gold

```
gold/
└── streaming_aggregations/
    ├── flight_phase_counts/     # Tumbling window 1 min
    │   ├── _delta_log/
    │   └── *.parquet
    └── anomaly_alerts/          # Sliding window 5 min
        ├── _delta_log/
        └── *.parquet
```

## Points d'attention

- **Ordre** : Exécuter APRÈS le notebook 03 (Silver_ML doit exister et recevoir des données)
- **Watermark** : Configuré pour tolérer les retards de données
- **Checkpoints** : Deux checkpoints séparés pour chaque stream
- **outputMode** : `append` car les agrégations avec watermark ne peuvent pas utiliser `complete`
- **Deux streams distincts** : Nécessaire car chaque stream a besoin de sa propre source

## Cas d'usage

### Tableau de bord temps réel

```python
# Lire les agrégations pour un dashboard
df_live = spark.read.format("delta").load(GOLD_AGGREGATIONS_PATH)
df_live.orderBy(col("window_start").desc()).limit(10).show()
```

### Alertes automatiques

```python
# Détecter les pays avec taux d'anomalie élevé
df_alerts = spark.read.format("delta").load(GOLD_ANOMALIES_PATH)
df_alerts.filter(col("anomaly_rate") > 0.1).show()
```

# 07 - Streaming Gold

## Description

Agrégations temps réel avec fenêtres temporelles sur les données Silver. Ce notebook implémente la couche Gold en streaming pour compléter l'architecture médaillon full streaming.

## Architecture

```
┌─────────────────┐     ┌─────────────────────────────────┐     ┌─────────────────────────┐
│  Silver         │     │      Streaming Gold             │     │      Gold Layer         │
│  (flights)      │ ──► │  - Tumbling Window (1 min)      │ ──► │  gold/                  │
│                 │     │  - Sliding Window (5 min)       │     │  ├── country_stats      │
└─────────────────┘     └─────────────────────────────────┘     │  └── country_anomalies  │
                                                                └─────────────────────────┘
```

## Requêtes Streaming

### Stream 1 : Statistiques par pays

| Paramètre | Valeur |
|-----------|--------|
| **Type de fenêtre** | Tumbling (non-chevauchante) |
| **Durée** | 1 minute |
| **Watermark** | 2 minutes |
| **Groupement** | `origin_country` |

#### Agrégations calculées

| Métrique | Description |
|----------|-------------|
| `flight_count` | Nombre d'observations par pays |
| `avg_altitude` | Altitude moyenne |
| `avg_velocity` | Vitesse moyenne |
| `ground_count` | Nombre d'avions au sol |
| `airborne_count` | Nombre d'avions en vol |

#### Schéma de sortie

```
window_start, window_end, origin_country, flight_count, avg_altitude, avg_velocity, ground_count, airborne_count
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
2. **Lecture** - Initialise le stream depuis Silver
3. **Stream 1** - Démarre les statistiques par pays
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
├── country_stats/               # Tumbling window 1 min (stats par pays)
│   ├── _delta_log/
│   └── *.parquet
└── country_anomalies/           # Sliding window 5 min (anomalies)
    ├── _delta_log/
    └── *.parquet
```

## Points d'attention

- **Ordre** : Exécuter APRÈS le notebook 03 (Silver doit exister et recevoir des données)
- **Watermark** : Configuré pour tolérer les retards de données
- **Checkpoints** : Deux checkpoints séparés pour chaque stream
- **outputMode** : `append` car les agrégations avec watermark ne peuvent pas utiliser `complete`
- **Deux streams distincts** : Nécessaire car chaque stream a besoin de sa propre source

## Cas d'usage

### Tableau de bord temps réel

```python
# Lire les agrégations pour un dashboard
GOLD_COUNTRY_STATS = get_s3_path("gold", "country_stats")
df_live = spark.read.format("delta").load(GOLD_COUNTRY_STATS)
df_live.orderBy(col("window_start").desc()).limit(10).show()
```

### Alertes automatiques

```python
# Détecter les pays avec taux d'anomalie élevé
GOLD_COUNTRY_ANOMALIES = get_s3_path("gold", "country_anomalies")
df_alerts = spark.read.format("delta").load(GOLD_COUNTRY_ANOMALIES)
df_alerts.filter(col("anomaly_rate") > 0.1).show()
```

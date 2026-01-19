# 05 - Feature Engineering (Mode Batch)

## Description

Création des features pour le Machine Learning en mode batch (Silver → Silver_ML).

> **Note** : Ce notebook est une alternative batch au stream Silver_ML du notebook 03. Utiliser l'un ou l'autre selon le besoin (streaming temps réel vs traitement batch).

## Architecture

```
┌─────────────────┐     ┌─────────────────────┐     ┌─────────────────┐
│  Silver Layer   │ ──► │ Feature Engineering │ ──► │  Silver_ML      │
│  (flights)      │     │   (Spark Batch)     │     │  (flights_ml)   │
└─────────────────┘     └─────────────────────┘     └─────────────────┘
                                 │
                        ┌────────┴────────┐
                        │  airports.csv   │
                        │  (Jointure)     │
                        └─────────────────┘
```

## Transformations appliquées

### 1. Nettoyage 🧹

- **Filtrage altitudes** : Entre -500m et 15 000m
- **Filtrage vitesses** : Entre 0 et 1 200 km/h
- **Suppression nulls** : Lignes sans `icao24`

### 2. Features temporelles (Window Functions)

```python
Window.partitionBy("icao24").orderBy("event_timestamp")
```

| Feature | Description |
|---------|-------------|
| `prev_altitude` | Altitude observation précédente |
| `prev_velocity` | Vitesse observation précédente |
| `altitude_change` | Variation d'altitude |
| `velocity_change` | Variation de vitesse |
| `observation_rank` | Rang par avion |

### 3. Jointure aéroports

- **Source** : `airports.csv` (large et medium airports)
- **Logique** : Pour les avions au sol, trouve l'aéroport le plus proche
- **Colonnes ajoutées** : `airport_icao`, `airport_name`, `airport_country`

### 4. Features Rolling Window

```python
Window.partitionBy("icao24").orderBy("event_timestamp").rowsBetween(-5, 0)
```

| Feature | Description |
|---------|-------------|
| `rolling_avg_altitude` | Moyenne altitude (5 obs) |
| `rolling_std_altitude` | Écart-type altitude (5 obs) |
| `rolling_avg_velocity` | Moyenne vitesse (5 obs) |

### 5. Label `flight_phase`

| Phase | Condition |
|-------|-----------|
| `GROUND` | `on_ground = true` |
| `TAKEOFF` | Montée >50m à altitude <3000m |
| `CLIMB` | Variation altitude >20m |
| `CRUISE` | Altitude stable (±20m) à >8000m |
| `DESCENT` | Variation altitude <-20m |
| `TRANSITION` | Autre |

## Comment utiliser

### Exécution

1. **Configuration** - Définit les chemins S3
2. **Lecture Silver** - Charge les données et nettoie
3. **Features temporelles** - Applique les window functions
4. **Jointure aéroports** - Enrichit avec le référentiel
5. **Features rolling** - Calcule les moyennes glissantes
6. **Label** - Crée `flight_phase`
7. **Sauvegarde** - Écrit en Delta Lake (mode overwrite)

### Vérification

La dernière cellule affiche la distribution des phases de vol.

## Schéma final Silver_ML

```
root
 |-- event_timestamp: timestamp
 |-- icao24: string
 |-- callsign: string
 |-- origin_country: string
 |-- longitude: float
 |-- latitude: float
 |-- velocity_kmh: float
 |-- altitude_meters: float
 |-- on_ground: boolean
 |-- category: integer
 |-- prev_altitude: float
 |-- prev_velocity: float
 |-- altitude_change: float
 |-- velocity_change: float
 |-- observation_rank: integer
 |-- airport_icao: string
 |-- airport_name: string
 |-- airport_country: string
 |-- rolling_avg_altitude: float
 |-- rolling_std_altitude: float
 |-- rolling_avg_velocity: float
 |-- flight_phase: string (LABEL)
```

## Points d'attention

- **Ordre** : Exécuter APRÈS les notebooks 02 et 03 (Silver doit contenir des données)
- **Mode overwrite** : Écrase les données Silver_ML existantes
- **Valeurs NULL** : Premières observations par avion ont des `prev_*` et `altitude_change` NULL
- **Alternative streaming** : Le notebook 03 fait le même traitement en mode streaming

# 02 - Streaming Bronze

## Description

Ingestion des données brutes depuis Kafka vers la couche Bronze (Delta Lake).

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Kafka Topic    │ ──► │  Spark          │ ──► │  Bronze Layer   │
│  opensky-data   │     │  Streaming      │     │  (Delta Lake)   │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

## Fonctionnement

### Lecture Kafka
- **Format** : `kafka`
- **Mode** : `readStream` (streaming continu)
- **Offset** : `earliest` (reprend depuis le début)

### Parsing JSON
- Définition d'un schéma strict (`StructType`)
- Extraction des champs depuis la colonne `value` de Kafka
- Conversion JSON → colonnes typées

### Écriture Delta Lake
- **Format** : Delta Lake
- **Mode** : `append`
- **Checkpoints** : Garantie exactly-once

## Schéma des données Bronze

```
root
 |-- time: long
 |-- icao24: string
 |-- callsign: string
 |-- origin_country: string
 |-- time_position: long
 |-- last_contact: long
 |-- longitude: float
 |-- latitude: float
 |-- baro_altitude: float
 |-- on_ground: boolean
 |-- velocity: float
 |-- true_track: float
 |-- vertical_rate: float
 |-- geo_altitude: float
 |-- squawk: string
 |-- spi: boolean
 |-- position_source: integer
 |-- category: integer
```

## Comment utiliser

### Démarrer le streaming

1. **Exécuter la configuration** - Charge les variables et crée la SparkSession
2. **Exécuter le schéma** - Définit la structure des données
3. **Exécuter le streaming** - Lance `readStream` → `writeStream`

### Vérifier

- **Garage WebUI** : Naviguer vers `datalake/bronze/flights`
- Vérifier la présence de `_delta_log/` et fichiers `.parquet`

### Arrêter

Interrompre la cellule (bouton Stop) ou `query.stop()`

## Points d'attention

- **Checkpoints** : Stockés dans `s3a://datalake/checkpoints/bronze_flights`
- **Ordre** : Exécuter APRÈS le notebook 01 (Producer actif)
- **Ressources** : Arrêter avant de lancer d'autres streams

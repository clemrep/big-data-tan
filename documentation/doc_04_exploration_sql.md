# 04 - Exploration SQL

## Description

Analyse exploratoire des données Silver avec SparkSQL. Inclut des requêtes batch avec et sans window functions.

## Requêtes disponibles

### 1. Statistiques par pays (sans fenêtre)

```sql
SELECT origin_country, COUNT(*) AS nb_observations,
       AVG(altitude_meters), AVG(velocity_kmh)
FROM flights
GROUP BY origin_country
ORDER BY nb_observations DESC
```

**Type** : Requête batch sans fenêtre (agrégation simple)

### 2. Avions au sol vs en vol (sans fenêtre)

```sql
SELECT on_ground, COUNT(*), AVG(velocity_kmh)
FROM flights
GROUP BY on_ground
```

**Type** : Requête batch sans fenêtre (agrégation simple)

### 3. Distribution des altitudes (sans fenêtre)

```sql
SELECT
    CASE WHEN altitude_meters < 1000 THEN '0-1000m' ... END AS altitude_range,
    COUNT(*)
FROM flights
GROUP BY 1
```

**Type** : Requête batch sans fenêtre (agrégation avec CASE)

### 4. Requête avec Window Functions (avec fenêtre)

```sql
SELECT
    icao24, callsign, origin_country, event_timestamp, altitude_meters,
    LAG(altitude_meters) OVER (PARTITION BY icao24 ORDER BY event_timestamp) AS prev_altitude,
    altitude_meters - LAG(...) AS altitude_change,
    AVG(altitude_meters) OVER (PARTITION BY icao24 ORDER BY event_timestamp
        ROWS BETWEEN 5 PRECEDING AND CURRENT ROW) AS rolling_avg_altitude,
    RANK() OVER (PARTITION BY origin_country ORDER BY velocity_kmh DESC) AS velocity_rank_in_country
FROM flights
```

**Type** : Requête batch AVEC fenêtre

**Window Functions utilisées** :
- `LAG()` : Valeur de l'observation précédente
- `AVG() OVER (ROWS BETWEEN)` : Moyenne glissante
- `RANK() OVER (PARTITION BY)` : Classement par groupe

## Comment utiliser

### Exécution

1. **Configuration** - Charge les données Silver et crée la vue `flights`
2. **Schéma** - Affiche la structure des données
3. **Requêtes** - Exécuter chaque cellule SQL individuellement

### Résultats

Chaque requête affiche un tableau avec les résultats via `.show()`.

## Couverture des exigences

| Exigence | Statut |
|----------|--------|
| Requête batch sans fenêtre | ✅ Statistiques par pays, distribution altitudes |
| Requête batch avec fenêtre | ✅ Window functions (LAG, AVG OVER, RANK) |
| Requête SparkSQL | ✅ Toutes les requêtes utilisent `spark.sql()` |

## Points d'attention

- **Ordre** : Exécuter APRÈS les notebooks 02 et 03 (Silver doit contenir des données)
- **Performance** : Les requêtes avec window functions peuvent être lentes sur de gros volumes
- **Vue temporaire** : La vue `flights` est créée dans la SparkSession courante uniquement

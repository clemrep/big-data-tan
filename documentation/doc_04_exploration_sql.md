# 04 - Exploration SQL

## Description

Analyse exploratoire des données Silver avec SparkSQL. Inclut des requêtes batch avec et sans window functions, ainsi que des visualisations Seaborn/Pandas.

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

## Visualisations Seaborn/Pandas

Les visualisations utilisent les données de `s3a://datalake/silver/flights_ml` converties en Pandas (échantillon de 10000 lignes pour limiter la mémoire).

### 1. Distribution des altitudes (histogramme)

- **Type** : `sns.histplot` avec KDE
- **Données** : `altitude_meters`
- **Insight** : Montre la répartition des altitudes de vol

### 2. Répartition des phases de vol (pie chart)

- **Type** : `plt.pie`
- **Données** : `flight_phase` (CLIMB, CRUISE, DESCENT, GROUND)
- **Insight** : Proportion de chaque phase de vol dans l'échantillon

### 3. Vitesse moyenne par pays (barplot horizontal)

- **Type** : `sns.barplot` horizontal
- **Données** : Moyenne de `velocity_kmh` groupée par `origin_country` (Top 15)
- **Insight** : Comparaison des vitesses moyennes entre pays

### 4. Heatmap corrélation features ML

- **Type** : `sns.heatmap`
- **Données** : Corrélations entre `altitude_meters`, `velocity_kmh`, `latitude`, `longitude`, `altitude_change`, `velocity_change`, `rolling_avg_altitude`
- **Insight** : Identifie les features corrélées pour le ML

### 5. Évolution temporelle du trafic (lineplot)

- **Type** : `sns.lineplot`
- **Données** : Nombre de vols par minute (`event_timestamp` resamplé)
- **Insight** : Tendances temporelles du trafic aérien

## Comment utiliser

### Exécution

1. **Configuration** - Charge les données Silver et crée la vue `flights`
2. **Schéma** - Affiche la structure des données
3. **Requêtes SQL** - Exécuter chaque cellule SQL individuellement
4. **Visualisations** - Exécuter les cellules Seaborn après les requêtes

### Résultats

- Requêtes SQL : Tableaux affichés via `.show()`
- Visualisations : Graphiques matplotlib/seaborn inline

## Couverture des exigences

| Exigence | Statut |
|----------|--------|
| Requête batch sans fenêtre | Statistiques par pays, distribution altitudes |
| Requête batch avec fenêtre | Window functions (LAG, AVG OVER, RANK) |
| Requête SparkSQL | Toutes les requêtes utilisent `spark.sql()` |
| Visualisations Seaborn | 5 graphiques (histogramme, pie, barplot, heatmap, lineplot) |

## Points d'attention

- **Ordre** : Exécuter APRÈS les notebooks 02 et 03 (Silver doit contenir des données)
- **Performance** : Les requêtes avec window functions peuvent être lentes sur de gros volumes
- **Vue temporaire** : La vue `flights` est créée dans la SparkSession courante uniquement
- **Mémoire** : Les visualisations utilisent un échantillon limité via `.sample().limit(10000).toPandas()`

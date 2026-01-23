# Contexte - Améliorations Pipeline Streaming

## Architecture Actuelle

```
OpenSky API → Kafka → Bronze (streaming) → Silver (streaming) → Gold (BATCH)
```

**Problème identifié:** La couche Gold utilise actuellement du **batch processing** (`06_classification_rf.ipynb`) alors que l'architecture médaillon devrait être **full streaming** de bout en bout.

---

## Tâches à Réaliser

### 1. ~~Convertir Gold en Streaming avec Fenêtres Temporelles~~ FAIT

**Objectif:** Notebook `07_streaming_gold.ipynb` créé avec 2 requêtes streaming.

**Requêtes implémentées:**

| Requête | Description | Fenêtre |
|---------|-------------|---------|
| **Agrégations temps réel** | Comptage vols par phase (CLIMB, CRUISE, DESCENT...) | Tumbling window 1 min |
| **Alertes anomalies** | Détection vitesse/altitude anormales par pays | Sliding window 5 min, slide 1 min |

**Pattern utilisé:**
```python
# Fenêtre tumbling (non-chevauchante)
.groupBy(window("event_timestamp", "1 minute"), "flight_phase")

# Fenêtre sliding (chevauchante)
.groupBy(window("event_timestamp", "5 minutes", "1 minute"), "origin_country")
```

**Output:**
- `s3a://datalake/gold/streaming_aggregations/flight_phase_counts/`
- `s3a://datalake/gold/streaming_aggregations/anomaly_alerts/`

**Documentation:** `doc_07_streaming_gold.md`

**Note:** Le notebook 06 reste dédié au ML batch (training Random Forest).

---

### 2. ~~Visualisations Seaborn/Pandas sur Silver~~ FAIT

**Objectif:** Notebook `04_exploration_sql.ipynb` enrichi avec 5 visualisations Seaborn.

**Graphiques implémentés:**

| Graphique | Type | Données |
|-----------|------|---------|
| Distribution des altitudes | `sns.histplot` + KDE | `altitude_meters` |
| Répartition des phases de vol | `plt.pie` | `flight_phase` |
| Vitesse moyenne par pays | `sns.barplot` horizontal | Top 15 pays |
| Heatmap corrélation features ML | `sns.heatmap` | 7 features numériques |
| Évolution temporelle du trafic | `sns.lineplot` | Resample 1 min |

**Données source:** `s3a://datalake/silver/flights_ml`

**Note:** Conversion Spark → Pandas via `.sample().limit(10000).toPandas()` (limite mémoire).

**Documentation:** `doc_04_exploration_sql.md`

---

### 3. ~~Dashboard Temps Réel~~ FAIT

**Objectif:** Dashboard Streamlit `dashboard/app.py` connecté aux agrégations Gold.

**Fonctionnalités implémentées:**

| Composant | Description | Visualisation |
|-----------|-------------|---------------|
| **KPIs temps réel** | Vols actifs, altitude/vitesse moyenne, taux anomalies | 4 métriques |
| **Distribution phases** | Répartition GROUND/TAKEOFF/CLIMB/CRUISE/DESCENT | Pie + Bar chart |
| **Timeline évolution** | Nombre de vols par phase dans le temps | Area chart empilé |
| **Alertes anomalies** | Top 10 pays + tableau alertes critiques (>10%) | Bar horizontal + Table |
| **Heatmap anomalies** | Matrice pays × heure | Heatmap Plotly |

**Stack technique:**
- Streamlit >= 1.28.0
- Plotly >= 5.18.0
- Boto3 pour accès S3/MinIO

**Flux:**
```
Gold Aggregations (Delta Lake) → Boto3 S3 → Pandas → Plotly → Streamlit
```

**Démarrage:**
```bash
docker compose up -d dashboard
# Accessible sur http://localhost:8501
```

**Documentation:** `doc_08_dashboard.md`

### Dépendances ajoutées (requirements.txt)

```
streamlit>=1.28.0
plotly>=5.18.0
boto3>=1.34.0
pyarrow>=14.0.0
```

---

## Critères de Validation

- [x] Bronze → Silver → Gold = **100% streaming** (sauf ML training)
- [x] 2 requêtes Gold avec `window()` fonctionnelles
- [x] 5+ visualisations Seaborn documentées
- [x] Dashboard affiche données < 30s de latence
- [x] Checkpoints configurés pour chaque stream Gold

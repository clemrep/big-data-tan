# Documentation - Dashboard Temps Réel Streamlit

## Objectif

Ce document décrit le dashboard temps réel Streamlit qui visualise les données agrégées de la couche Gold du pipeline streaming OpenSky.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     PIPELINE STREAMING                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   OpenSky API → Kafka → Bronze → Silver → Gold (streaming)     │
│                                               │                 │
│                                               ▼                 │
│                                    ┌──────────────────┐         │
│                                    │  MinIO/Garage    │         │
│                                    │  (Delta Lake)    │         │
│                                    └────────┬─────────┘         │
│                                             │                   │
│                                             ▼                   │
│                                    ┌──────────────────┐         │
│                                    │    Streamlit     │         │
│                                    │    Dashboard     │         │
│                                    │   (port 8501)    │         │
│                                    └──────────────────┘         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Sources de Données

Le dashboard lit les agrégations Gold depuis MinIO/Garage :

| Source | Chemin S3 | Fenêtre | Description |
|--------|-----------|---------|-------------|
| **Country Stats** | `s3a://datalake/gold/phase_stats/` | Tumbling 1 min | Statistiques par pays |
| **Anomaly Alerts** | `s3a://datalake/gold/country_stats/` | Sliding 5 min | Détection anomalies par pays |

### Schéma Country Stats

```
window_start    : timestamp
window_end      : timestamp
origin_country  : string
flight_count    : long
avg_altitude    : double
avg_velocity    : double
ground_count    : long
airborne_count  : long
```

### Schéma Anomaly Alerts

```
window_start        : timestamp
window_end          : timestamp
origin_country      : string
total_observations  : long
altitude_anomalies  : long
velocity_anomalies  : long
anomaly_rate        : double
max_altitude        : double
min_altitude        : double
max_velocity        : double
avg_altitude        : double
avg_velocity        : double
stddev_altitude     : double
stddev_velocity     : double
```

## Fonctionnalités du Dashboard

### 1. KPIs Temps Réel

Quatre métriques principales affichées en haut du dashboard :

| KPI | Description | Source |
|-----|-------------|--------|
| 🛫 Vols Actifs | Nombre total de vols observés | `SUM(flight_count)` |
| 📏 Altitude Moyenne | Altitude moyenne tous vols | `AVG(avg_altitude)` |
| ⚡ Vitesse Moyenne | Vitesse moyenne tous vols | `AVG(avg_velocity)` |
| ⚠️ Taux Anomalies | Pourcentage d'observations anormales | `AVG(anomaly_rate)` |

### 2. Statistiques par Pays

**Graphiques :**
- **Pie Chart** : Répartition en pourcentage par pays
- **Bar Chart** : Nombre absolu de vols par pays

**Métriques par pays :**
- Nombre d'observations (`flight_count`)
- Avions au sol (`ground_count`)
- Avions en vol (`airborne_count`)
- Altitude et vitesse moyennes

### 3. Évolution Temporelle

**Area Chart** empilé montrant l'évolution du nombre de vols par pays dans le temps.

- Axe X : Timestamps des fenêtres
- Axe Y : Nombre de vols
- Couleurs : Par pays d'origine

### 4. Alertes d'Anomalies

**Visualisations :**
- **Bar Chart horizontal** : Top 10 pays par taux d'anomalies
- **Tableau** : Dernières alertes avec taux > 10%

**Seuils d'anomalies (définis dans Gold) :**
- Altitude : < -100m ou > 12,000m
- Vitesse : < 0 km/h ou > 1,000 km/h

### 5. Heatmap des Anomalies

Matrice pays × heure montrant l'intensité des anomalies :
- Lignes : Top 15 pays
- Colonnes : Heures
- Couleur : Taux d'anomalie (jaune → rouge)

## Configuration

### Variables d'environnement

Le dashboard utilise les variables du fichier `.env` :

```bash
GARAGE_ENDPOINT=http://garage:3900
ACCESS_KEY=<votre_access_key>
SECRET_KEY=<votre_secret_key>
BUCKET_NAME=datalake
```

### Paramètres Streamlit

| Paramètre | Valeur | Description |
|-----------|--------|-------------|
| Port | 8501 | Port d'écoute HTTP |
| Refresh | 30s (configurable) | Intervalle de rafraîchissement auto |
| Layout | Wide | Utilisation pleine largeur |

## Démarrage

### Option 1 : Via Docker Compose (recommandé)

```bash
# Démarrer tous les services incluant le dashboard
docker compose up -d dashboard

# Ou démarrer tout le stack
docker compose up -d
```

Le dashboard sera accessible sur : **http://localhost:8501**

### Option 2 : Exécution locale

```bash
# Installer les dépendances
pip install streamlit plotly boto3 pyarrow pandas python-dotenv

# Lancer le dashboard
streamlit run dashboard/app.py
```

**Note :** En local, modifier `GARAGE_ENDPOINT` pour pointer vers `http://localhost:3900`.

## Structure du Code

```
dashboard/
└── app.py              # Application Streamlit principale
    ├── get_s3_client()           # Connexion MinIO/Garage
    ├── read_parquet_from_s3()    # Lecture fichiers Parquet
    ├── load_flight_phase_data()  # Chargement données phases
    ├── load_anomaly_data()       # Chargement données anomalies
    ├── render_header()           # En-tête dashboard
    ├── render_kpi_cards()        # Métriques KPI
    ├── render_flight_phase_chart()    # Graphiques phases
    ├── render_flight_phase_timeline() # Timeline évolution
    ├── render_anomaly_alerts()   # Section alertes
    ├── render_anomaly_heatmap()  # Heatmap anomalies
    ├── render_sidebar()          # Barre latérale
    └── main()                    # Point d'entrée
```

## Dépendances

```
streamlit>=1.28.0
plotly>=5.18.0
boto3>=1.34.0
pyarrow>=14.0.0
pandas>=2.1.4
python-dotenv>=1.0.0
```

## Latence et Performance

| Métrique | Valeur |
|----------|--------|
| Latence Gold → Dashboard | < 30 secondes |
| Rafraîchissement UI | Configurable (10-120s) |
| Limite fichiers Parquet | 50 derniers fichiers |
| Cache S3 client | Singleton via `@st.cache_resource` |

## Captures d'écran

### Vue principale
```
┌────────────────────────────────────────────────────────────────┐
│  ✈️ OpenSky Flight Dashboard                      🕐 14:32:05  │
├────────────────────────────────────────────────────────────────┤
│  🛫 Vols    📏 Altitude    ⚡ Vitesse    ⚠️ Anomalies          │
│  1,234      8,500 m        650 km/h     2.3%                   │
├────────────────────────────────────────────────────────────────┤
│  📊 Statistiques par Pays                                      │
│  ┌──────────────────┐  ┌──────────────────┐                    │
│  │   [PIE CHART]    │  │   [BAR CHART]    │                    │
│  │   USA: 35%       │  │   █████ USA      │                    │
│  │   Germany: 15%   │  │   ███ Germany    │                    │
│  │   ...            │  │   ...            │                    │
│  └──────────────────┘  └──────────────────┘                    │
├────────────────────────────────────────────────────────────────┤
│  🚨 Alertes d'Anomalies                                        │
│  ┌──────────────────┐  ┌──────────────────┐                    │
│  │ Top 10 Pays      │  │ Alertes Récentes │                    │
│  │ █████ France     │  │ France  12.5%    │                    │
│  │ ████ Germany     │  │ Spain   11.2%    │                    │
│  └──────────────────┘  └──────────────────┘                    │
└────────────────────────────────────────────────────────────────┘
```

## Troubleshooting

### Le dashboard n'affiche pas de données

1. Vérifier que le streaming Gold est actif (notebook `07_streaming_gold.ipynb`)
2. Vérifier la connexion MinIO dans la sidebar (✅ ou ❌)
3. S'assurer que les chemins Gold existent :
   ```bash
   # Via MinIO client ou Garage WebUI
   mc ls minio/datalake/gold/phase_stats/
   mc ls minio/datalake/gold/country_stats/
   ```

### Erreur de connexion S3

1. Vérifier les variables d'environnement dans `.env`
2. S'assurer que Garage est démarré : `docker compose ps garage`
3. Tester la connexion :
   ```python
   import boto3
   s3 = boto3.client('s3', endpoint_url='http://localhost:3900', ...)
   s3.list_buckets()
   ```

### Performance lente

1. Réduire la fréquence de rafraîchissement (sidebar)
2. Le dashboard limite automatiquement aux 50 derniers fichiers Parquet
3. Augmenter les ressources Docker si nécessaire

## Évolutions Futures

- [ ] Carte géographique des vols en temps réel
- [ ] Filtres par pays/phase dans la sidebar
- [ ] Export des données affichées (CSV)
- [ ] Alertes push (email/Slack) sur anomalies critiques
- [ ] Mode sombre

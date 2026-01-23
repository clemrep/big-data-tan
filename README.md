# ✈️ Projet OpenSky Big Data

Ce projet implémente un pipeline de données complet en temps réel pour le suivi et l'analyse du trafic aérien mondial, en utilisant les données de l'API OpenSky Network. 

L'architecture repose sur une approche **Medallion** (Bronze, Silver, Gold) orchestrée avec Spark Streaming et Kafka.

---

## 📋 Table des Matières

1. [Contexte du Projet](#contexte-du-projet)
2. [Architecture Technique](#architecture-technique)
3. [Structure du Repository](#structure-du-repository)
4. [Documentation Détaillée](#documentation-détaillée)
5. [Démarrage Rapide](#démarrage-rapide)
6. [Auteurs](#auteurs)

---

## 🎯 Contexte du Projet

Le but de ce projet est de capturer des flux de données aéronautiques massifs, de les traiter en temps réel pour en extraire des informations exploitables (phases de vol, anomalies) et de les visualiser sur un dashboard interactif.

### Objectifs principaux :
- **Ingestion Haute Fréquence** : Collecte des états des vols depuis OpenSky via Kafka.
- **Traitement Qualitatif** : Nettoyage et typage des données (Bronze vers Silver).
- **Machine Learning** : Classification des phases de vol via un modèle Random Forest.
- **Analyse Streaming** : Agrégation temporelle des données pour détecter des anomalies de vol.
- **Visualisation** : Dashboard temps réel pour le monitoring des métriques clés (KPIs).

---

## 🏗️ Architecture Technique

Le projet utilise les technologies suivantes :
- **Ingestion** : Python, Kafka, Zookeeper.
- **Traitement & Streaming** : Apache Spark, Spark Structured Streaming.
- **Stockage** : Delta Lake (Format Parquet) sur un stockage objet S3 (Garage/MinIO).
- **Machine Learning** : Spark MLlib (Random Forest).
- **Dashboard** : Streamlit, Plotly.
- **Infrastructure** : Docker & Docker Compose.

---

## 📂 Structure du Repository

- `01_ingestion_kafka.ipynb` : Script d'ingestion des données API vers Kafka.
- `02_streaming_bronze.ipynb` : Consommation Kafka vers la couche Bronze (Raw).
- `03_streaming_silver.ipynb` : Nettoyage et enrichissement vers la couche Silver.
- `04_exploration_sql.ipynb` : Analyse exploratoire des données en SQL.
- `05_feature_engineering.ipynb` : Préparation des données pour le Machine Learning.
- `06_classification_rf.ipynb` : Entraînement et évaluation du modèle Random Forest.
- `07_streaming_gold.ipynb` : Agrégations temps réel sur les données Silver pour le dashboard.
- `dashboard/` : Code source de l'application Streamlit.
- `documentation/` : Guides détaillés pour chaque étape du pipeline.

---

## 📖 Documentation Détaillée

Une documentation exhaustive pour chaque composant est disponible dans le dossier [`documentation/`](./documentation) :

- [**01 - Ingestion Kafka**](./documentation/doc_01_ingestion_kafka.md) : Détails sur le producer et l'API OpenSky.
- [**02 - Streaming Bronze**](./documentation/doc_02_streaming_bronze.md) : Stockage des données brutes.
- [**03 - Streaming Silver**](./documentation/doc_03_streaming_silver.md) : Filtrage et gestion des schémas.
- [**04 - Exploration SQL**](./documentation/doc_04_exploration_sql.md) : Analyse métier et statistiques.
- [**05 - Feature Engineering**](./documentation/doc_05_feature_engineering.md) : Création des variables prédictives.
- [**06 - Classification RF**](./documentation/doc_06_classification_rf.md) : Détails du modèle de classification.
- [**07 - Streaming Gold**](./documentation/doc_07_streaming_gold.md) : Pipeline de production final.
- [**08 - Dashboard**](./documentation/doc_08_dashboard.md) : Guide d'utilisation de l'interface visuelle.

---

## 🚀 Démarrage Rapide

1. **Lancer l'infrastructure** :
   ```bash
   docker compose up -d
   ```
2. **Configurer l'environnement** :
   Copier le fichier `.env.example` en `.env` et renseigner les clés d'accès S3.
3. **Exécuter les Notebooks** :
   Suivre l'ordre numérique des fichiers `.ipynb` (de 01 à 07).
4. **Accéder au Dashboard** :
   Rendez-vous sur [http://localhost:8501](http://localhost:8501).

---

## 👥 Auteurs

Projet réalisé par :
- **Clément Repel**
- **Titouan Cocheril**
- **Adam Guillouet**
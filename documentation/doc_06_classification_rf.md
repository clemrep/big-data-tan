# 06 - Classification Random Forest

## Description

Pipeline MLlib complet pour classifier les phases de vol avec un Random Forest.

## Architecture

```
┌─────────────────┐     ┌─────────────────────┐
│  Silver_ML      │ ──► │   MLlib Pipeline    │
│  (flights_ml)   │     │   Random Forest     │
└─────────────────┘     └─────────────────────┘     
```

## Pipeline MLlib

```
┌───────────────┐   ┌─────────────────┐   ┌───────────────┐   ┌──────────────┐   ┌───────────────┐
│ StringIndexer │──►│ VectorAssembler │──►│ StandardScaler│──►│ RandomForest │──►│ IndexToString │
│ (label)       │   │ (features)      │   │ (normalize)   │   │ (classify)   │   │ (decode)      │
└───────────────┘   └─────────────────┘   └───────────────┘   └──────────────┘   └───────────────┘
```

### Stages

| Stage | Input | Output | Description |
|-------|-------|--------|-------------|
| StringIndexer | `flight_phase` | `label` | Encode labels en indices |
| VectorAssembler | 7 features | `features_raw` | Assemble en vecteur |
| StandardScaler | `features_raw` | `features` | Normalise |
| RandomForestClassifier | `features`, `label` | `prediction` | 100 arbres, depth 10 |
| IndexToString | `prediction` | `predicted_label` | Décode en string |

## Features utilisées

| Feature | Description |
|---------|-------------|
| `altitude_meters` | Altitude barométrique |
| `velocity_kmh` | Vitesse en km/h |
| `altitude_change` | Variation d'altitude |
| `velocity_change` | Variation de vitesse |
| `rolling_avg_altitude` | Moyenne altitude (5 obs) |
| `rolling_std_altitude` | Écart-type altitude |
| `rolling_avg_velocity` | Moyenne vitesse (5 obs) |

## Comment utiliser

### Exécution

1. **Configuration** - Définit les chemins S3
2. **Lecture** - Charge Silver_ML, filtre nulls, remplace par 0
3. **Pipeline** - Crée les 5 stages
4. **Train/Test** - Split 80/20 avec seed 42
5. **Entraînement** - `pipeline.fit(train_df)`
6. **Évaluation** - Accuracy, F1, matrice de confusion
7. **Feature importance** - Affiche les features les plus importantes

### Métriques obtenues

| Métrique | Valeur |
|----------|--------|
| Accuracy | 94.22% |
| F1 Score | 0.9414 |

## Points d'attention

- **Ordre** : Exécuter APRÈS le notebook 03 ou 05 (Silver_ML doit exister)
- **Ressources** : Random Forest consomme beaucoup de mémoire
- **Reproductibilité** : `seed=42` pour résultats reproductibles
- **Classes déséquilibrées** : Certaines phases (TAKEOFF) peuvent être rares

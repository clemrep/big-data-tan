"""
Dashboard temps réel pour le pipeline de données OpenSky.

Ce dashboard affiche les agrégations streaming de la couche Gold:
- Distribution des phases de vol (fenêtre tumbling 1 min)
- Alertes d'anomalies par pays (fenêtre sliding 5 min)

Données source: s3a://datalake/gold/
"""

import os
import sys
import time
from datetime import datetime, timedelta

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Configuration MinIO/Garage
MINIO_ENDPOINT = os.getenv("GARAGE_ENDPOINT", "http://garage:3900").replace("http://", "").replace("https://", "")
ACCESS_KEY = os.getenv("ACCESS_KEY")
SECRET_KEY = os.getenv("SECRET_KEY")
BUCKET_NAME = os.getenv("BUCKET_NAME", "datalake")

# Configuration de la page Streamlit
st.set_page_config(
    page_title="OpenSky Flight Dashboard",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Style CSS personnalisé
st.markdown("""
<style>
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    .alert-card {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        padding: 15px;
        border-radius: 10px;
        color: white;
        margin: 5px 0;
    }
    .stMetric {
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 5px;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def get_s3_client():
    """Initialise le client S3 pour MinIO/Garage."""
    import boto3
    from botocore.client import Config

    return boto3.client(
        's3',
        endpoint_url=f"http://{MINIO_ENDPOINT}",
        aws_access_key_id=ACCESS_KEY,
        aws_secret_access_key=SECRET_KEY,
        config=Config(signature_version='s3v4'),
        region_name='garage'
    )


def read_parquet_from_s3(path: str) -> pd.DataFrame:
    """
    Lit les fichiers Parquet depuis S3/MinIO.

    Args:
        path: Chemin S3 (ex: gold/phase_stats)

    Returns:
        DataFrame pandas avec les données
    """
    import io

    s3 = get_s3_client()

    # Lister les fichiers parquet dans le dossier
    try:
        response = s3.list_objects_v2(Bucket=BUCKET_NAME, Prefix=path)

        if 'Contents' not in response:
            return pd.DataFrame()

        # Filtrer les fichiers parquet
        parquet_files = [
            obj['Key'] for obj in response['Contents']
            if obj['Key'].endswith('.parquet')
        ]

        if not parquet_files:
            return pd.DataFrame()

        # Lire et concaténer tous les fichiers parquet
        dfs = []
        for file_key in parquet_files[-50:]:  # Limiter aux 50 derniers fichiers
            try:
                obj = s3.get_object(Bucket=BUCKET_NAME, Key=file_key)
                df = pd.read_parquet(io.BytesIO(obj['Body'].read()))
                dfs.append(df)
            except Exception as e:
                st.warning(f"Erreur lecture {file_key}: {e}")
                continue

        if dfs:
            return pd.concat(dfs, ignore_index=True)
        return pd.DataFrame()

    except Exception as e:
        st.error(f"Erreur accès S3: {e}")
        return pd.DataFrame()


def load_flight_phase_data() -> pd.DataFrame:
    """Charge les données d'agrégation des phases de vol."""
    df = read_parquet_from_s3("gold/phase_stats")

    if not df.empty and 'window' in df.columns:
        # Extraire window_start et window_end si format struct
        if isinstance(df['window'].iloc[0], dict):
            df['window_start'] = pd.to_datetime(df['window'].apply(lambda x: x.get('start')))
            df['window_end'] = pd.to_datetime(df['window'].apply(lambda x: x.get('end')))
        elif 'window_start' not in df.columns:
            df['window_start'] = pd.to_datetime(df['window'])

    return df


def load_anomaly_data() -> pd.DataFrame:
    """Charge les données d'alertes d'anomalies."""
    df = read_parquet_from_s3("gold/country_stats")

    if not df.empty and 'window' in df.columns:
        # Extraire window_start et window_end si format struct
        if isinstance(df['window'].iloc[0], dict):
            df['window_start'] = pd.to_datetime(df['window'].apply(lambda x: x.get('start')))
            df['window_end'] = pd.to_datetime(df['window'].apply(lambda x: x.get('end')))
        elif 'window_start' not in df.columns:
            df['window_start'] = pd.to_datetime(df['window'])

    return df


def render_header():
    """Affiche l'en-tête du dashboard."""
    col1, col2, col3 = st.columns([1, 4, 1])

    with col2:
        st.title("✈️ OpenSky Flight Dashboard")
        st.markdown("**Pipeline Streaming Gold - Données temps réel**")

    with col3:
        st.markdown(f"🕐 Dernière MAJ: `{datetime.now().strftime('%H:%M:%S')}`")


def render_kpi_cards(df_phases: pd.DataFrame, df_anomalies: pd.DataFrame):
    """Affiche les KPIs principaux."""
    col1, col2, col3, col4 = st.columns(4)

    # Total vols actifs
    total_flights = df_phases['flight_count'].sum() if not df_phases.empty else 0
    with col1:
        st.metric(
            label="🛫 Vols Actifs",
            value=f"{total_flights:,}",
            delta=None
        )

    # Altitude moyenne
    avg_altitude = df_phases['avg_altitude'].mean() if not df_phases.empty and 'avg_altitude' in df_phases.columns else 0
    with col2:
        st.metric(
            label="📏 Altitude Moyenne",
            value=f"{avg_altitude:,.0f} m",
            delta=None
        )

    # Vitesse moyenne
    avg_velocity = df_phases['avg_velocity'].mean() if not df_phases.empty and 'avg_velocity' in df_phases.columns else 0
    with col3:
        st.metric(
            label="⚡ Vitesse Moyenne",
            value=f"{avg_velocity:,.0f} km/h",
            delta=None
        )

    # Taux d'anomalies
    if not df_anomalies.empty and 'anomaly_rate' in df_anomalies.columns:
        avg_anomaly_rate = df_anomalies['anomaly_rate'].mean() * 100
        anomaly_color = "inverse" if avg_anomaly_rate > 10 else "normal"
    else:
        avg_anomaly_rate = 0
        anomaly_color = "normal"

    with col4:
        st.metric(
            label="⚠️ Taux Anomalies",
            value=f"{avg_anomaly_rate:.1f}%",
            delta=None
        )


def render_flight_phase_chart(df: pd.DataFrame):
    """Affiche le graphique de distribution des phases de vol."""
    st.subheader("📊 Distribution des Phases de Vol")

    if df.empty:
        st.info("Aucune donnée disponible. Vérifiez que le streaming Gold est actif.")
        return

    # Agréger par phase
    phase_totals = df.groupby('flight_phase').agg({
        'flight_count': 'sum',
        'avg_altitude': 'mean',
        'avg_velocity': 'mean'
    }).reset_index()

    # Couleurs par phase
    phase_colors = {
        'GROUND': '#95a5a6',
        'TAKEOFF': '#3498db',
        'CLIMB': '#2ecc71',
        'CRUISE': '#9b59b6',
        'DESCENT': '#e74c3c',
        'TRANSITION': '#f39c12'
    }

    col1, col2 = st.columns(2)

    with col1:
        # Pie chart
        fig_pie = px.pie(
            phase_totals,
            values='flight_count',
            names='flight_phase',
            title='Répartition par Phase',
            color='flight_phase',
            color_discrete_map=phase_colors
        )
        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_pie, use_container_width=True)

    with col2:
        # Bar chart avec altitude/vitesse moyennes
        fig_bar = go.Figure()

        fig_bar.add_trace(go.Bar(
            name='Nombre de vols',
            x=phase_totals['flight_phase'],
            y=phase_totals['flight_count'],
            marker_color=[phase_colors.get(p, '#7f8c8d') for p in phase_totals['flight_phase']]
        ))

        fig_bar.update_layout(
            title='Nombre de Vols par Phase',
            xaxis_title='Phase de vol',
            yaxis_title='Nombre de vols',
            showlegend=False
        )
        st.plotly_chart(fig_bar, use_container_width=True)


def render_flight_phase_timeline(df: pd.DataFrame):
    """Affiche l'évolution temporelle des phases de vol."""
    st.subheader("📈 Évolution Temporelle des Vols")

    if df.empty or 'window_start' not in df.columns:
        st.info("Données temporelles non disponibles.")
        return

    # Préparer les données pour le graphique temporel
    df_time = df.copy()
    df_time = df_time.sort_values('window_start')

    # Graphique de ligne empilée
    fig = px.area(
        df_time,
        x='window_start',
        y='flight_count',
        color='flight_phase',
        title='Évolution du Nombre de Vols par Phase',
        labels={'window_start': 'Temps', 'flight_count': 'Nombre de vols', 'flight_phase': 'Phase'}
    )

    fig.update_layout(
        xaxis_title='Temps',
        yaxis_title='Nombre de vols',
        legend_title='Phase de vol',
        hovermode='x unified'
    )

    st.plotly_chart(fig, use_container_width=True)


def render_anomaly_alerts(df: pd.DataFrame):
    """Affiche les alertes d'anomalies."""
    st.subheader("🚨 Alertes d'Anomalies par Pays")

    if df.empty:
        st.info("Aucune alerte d'anomalie. Le système fonctionne normalement.")
        return

    col1, col2 = st.columns(2)

    with col1:
        # Top pays avec anomalies
        if 'origin_country' in df.columns and 'anomaly_rate' in df.columns:
            # Dernière fenêtre par pays
            latest = df.sort_values('window_start', ascending=False).drop_duplicates('origin_country')
            top_anomalies = latest.nlargest(10, 'anomaly_rate')

            fig = px.bar(
                top_anomalies,
                x='anomaly_rate',
                y='origin_country',
                orientation='h',
                title='Top 10 Pays - Taux d\'Anomalies',
                color='anomaly_rate',
                color_continuous_scale='Reds'
            )
            fig.update_layout(yaxis={'categoryorder': 'total ascending'})
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Tableau des alertes récentes
        st.markdown("**Dernières Alertes (taux > 10%)**")

        if 'anomaly_rate' in df.columns:
            alerts = df[df['anomaly_rate'] > 0.1].sort_values('window_start', ascending=False).head(10)

            if not alerts.empty:
                display_cols = ['origin_country', 'anomaly_rate', 'altitude_anomalies', 'velocity_anomalies']
                display_cols = [c for c in display_cols if c in alerts.columns]

                alerts_display = alerts[display_cols].copy()
                if 'anomaly_rate' in alerts_display.columns:
                    alerts_display['anomaly_rate'] = (alerts_display['anomaly_rate'] * 100).round(1).astype(str) + '%'

                st.dataframe(alerts_display, use_container_width=True, hide_index=True)
            else:
                st.success("✅ Aucune alerte critique détectée")


def render_anomaly_heatmap(df: pd.DataFrame):
    """Affiche une heatmap temporelle des anomalies."""
    st.subheader("🗺️ Heatmap des Anomalies")

    if df.empty or 'window_start' not in df.columns or 'origin_country' not in df.columns:
        st.info("Données insuffisantes pour la heatmap.")
        return

    # Préparer les données pour la heatmap
    df_hm = df.copy()
    df_hm['hour'] = pd.to_datetime(df_hm['window_start']).dt.strftime('%H:%M')

    # Pivot pour la heatmap
    pivot = df_hm.pivot_table(
        values='anomaly_rate',
        index='origin_country',
        columns='hour',
        aggfunc='mean'
    ).fillna(0)

    # Limiter aux top 15 pays
    top_countries = df_hm.groupby('origin_country')['anomaly_rate'].mean().nlargest(15).index
    pivot = pivot.loc[pivot.index.isin(top_countries)]

    if pivot.empty:
        return

    fig = px.imshow(
        pivot,
        labels=dict(x='Heure', y='Pays', color='Taux anomalie'),
        title='Taux d\'Anomalies par Pays et Heure',
        color_continuous_scale='YlOrRd'
    )

    st.plotly_chart(fig, use_container_width=True)


def render_sidebar():
    """Affiche la barre latérale avec les options."""
    with st.sidebar:
        st.header("⚙️ Configuration")

        # Intervalle de rafraîchissement
        refresh_interval = st.slider(
            "Rafraîchissement (secondes)",
            min_value=10,
            max_value=120,
            value=30,
            step=10
        )

        st.divider()

        # Informations sur le pipeline
        st.header("📋 Infos Pipeline")
        st.markdown("""
        **Architecture:**
        ```
        OpenSky API
            ↓
        Kafka (raw)
            ↓
        Bronze (streaming)
            ↓
        Silver (streaming)
            ↓
        Gold (streaming)
            ↓
        Dashboard
        ```
        """)

        st.divider()

        # Statut des sources
        st.header("📡 Statut Sources")

        # Vérifier la connexion S3
        try:
            s3 = get_s3_client()
            s3.head_bucket(Bucket=BUCKET_NAME)
            st.success("✅ MinIO/Garage connecté")
        except Exception as e:
            st.error(f"❌ MinIO/Garage: {e}")

        st.divider()

        # Légende des phases
        st.header("📖 Légende Phases")
        phases = {
            "GROUND": "Au sol",
            "TAKEOFF": "Décollage",
            "CLIMB": "Montée",
            "CRUISE": "Croisière",
            "DESCENT": "Descente",
            "TRANSITION": "Transition"
        }
        for phase, desc in phases.items():
            st.markdown(f"**{phase}**: {desc}")

        return refresh_interval


def main():
    """Point d'entrée principal du dashboard."""

    # Sidebar
    refresh_interval = render_sidebar()

    # Header
    render_header()

    st.divider()

    # Charger les données
    with st.spinner("Chargement des données..."):
        df_phases = load_flight_phase_data()
        df_anomalies = load_anomaly_data()

    # KPIs
    render_kpi_cards(df_phases, df_anomalies)

    st.divider()

    # Section Phases de vol
    render_flight_phase_chart(df_phases)
    render_flight_phase_timeline(df_phases)

    st.divider()

    # Section Anomalies
    render_anomaly_alerts(df_anomalies)
    render_anomaly_heatmap(df_anomalies)

    # Footer avec refresh automatique
    st.divider()
    st.caption(f"🔄 Rafraîchissement automatique toutes les {refresh_interval}s | Pipeline Big Data TAN - IMT Atlantique")

    # Auto-refresh via rerun
    time.sleep(refresh_interval)
    st.rerun()


if __name__ == "__main__":
    main()

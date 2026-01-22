import streamlit as st
import time
import pandas as pd
import sys
import os

# Ajouter le répertoire courant au path pour importer config
sys.path.insert(0, '/home/jovyan/work')

import plotly.express as px
from pyspark.sql.functions import col

# Importer la configuration centralisée
from config import get_s3_path, create_spark_session

# 1. Configuration Page
st.set_page_config(page_title="OpenSky Live", page_icon="✈️", layout="wide")

# CSS Dark Mode
st.markdown("""
<style>
    .stApp { background-color: #0e1117; }
    div[data-testid="stMetricValue"] { font-size: 2.5rem; color: #ff9900; }
</style>
""", unsafe_allow_html=True)

# 2. Session Spark (Utilise la même config que les notebooks)
@st.cache_resource
def get_spark():
    try:
        return create_spark_session("StreamlitDashboard")
    except Exception as e:
        st.error(f"❌ Erreur Spark : {e}")
        st.stop()

spark = get_spark()

# Chemins S3 (Utilise la même fonction que les notebooks)
GOLD_TRAFFIC = get_s3_path("gold", "traffic_by_country")
GOLD_METRICS = get_s3_path("gold", "metrics_by_category")

st.title("✈️ OpenSky Live Monitoring")
st.caption(f"📊 Trafic: {GOLD_TRAFFIC}")

placeholder = st.empty()

# 3. Boucle de rafraîchissement
iteration = 0
while True:
    iteration += 1
    with placeholder.container():
        try:
            # Lecture Delta (même format que les autres notebooks)
            df_traf = spark.read.format("delta").load(GOLD_TRAFFIC)
            df_met = spark.read.format("delta").load(GOLD_METRICS)

            # Conversion Pandas (limité pour performance)
            pdf_traf = df_traf.orderBy(col("window").desc()).limit(100).toPandas()
            pdf_met = df_met.orderBy(col("window").desc()).limit(100).toPandas()

            if not pdf_traf.empty and not pdf_met.empty:
                # Filtrage dernière fenêtre
                last_win_traf = pdf_traf['window'].max()
                cur_traf = pdf_traf[pdf_traf['window'] == last_win_traf].sort_values('flight_count', ascending=False)

                last_win_met = pdf_met['window'].max()
                cur_met = pdf_met[pdf_met['window'] == last_win_met]

                # KPI
                total = int(cur_traf['flight_count'].sum())
                top_c = cur_traf.iloc[0]['origin_country'] if len(cur_traf) > 0 else "-"
                avg_vel = int(cur_met['avg_velocity_kmh'].mean()) if 'avg_velocity_kmh' in cur_met.columns else 0
                avg_alt = int(cur_met['avg_altitude_m'].mean()) if 'avg_altitude_m' in cur_met.columns else 0

                # Affichage KPI
                k1, k2, k3, k4 = st.columns(4)
                k1.metric("⏰ Heure UTC", time.strftime('%H:%M:%S'))
                k2.metric("✈️ Avions", f"{total:,}")
                k3.metric("🌍 Top Pays", top_c)
                k4.metric("🚀 Vitesse Moy.", f"{avg_vel} km/h")

                st.divider()

                # Graphiques
                c1, c2 = st.columns(2)

                with c1:
                    st.subheader("🌍 Top 10 Pays")
                    fig = px.bar(
                        cur_traf.head(10), 
                        x="flight_count", 
                        y="origin_country", 
                        orientation='h',
                        template="plotly_dark",
                        color="flight_count",
                        color_continuous_scale="Oranges"
                    )
                    fig.update_layout(showlegend=False, height=400)
                    st.plotly_chart(fig, use_container_width=True)

                with c2:
                    st.subheader("🚀 Performance par Catégorie")
                    if 'category' in cur_met.columns and not cur_met.empty:
                        fig2 = px.scatter(
                            cur_met, 
                            x="avg_velocity_kmh", 
                            y="avg_altitude_m",
                            size="aircraft_count",
                            color="category",
                            template="plotly_dark",
                            labels={"avg_velocity_kmh": "Vitesse (km/h)", "avg_altitude_m": "Altitude (m)"}
                        )
                        fig2.update_layout(height=400)
                        st.plotly_chart(fig2, use_container_width=True)
                    else:
                        st.info("Pas de données de catégories")

                # Stats bas de page
                st.caption(f"🔄 Refresh #{iteration} | Fenêtre : {str(last_win_traf)[:19] if last_win_traf else 'N/A'}")

            else:
                st.warning("⏳ En attente de données dans le Data Lake...")
                st.info("💡 Vérifiez que les notebooks 01, 02, 03, 03b sont actifs")

        except Exception as e:
            st.error(f"❌ Erreur : {str(e)[:200]}")
            st.info("Reconnexion dans 5 secondes...")
            time.sleep(5)

    time.sleep(2)

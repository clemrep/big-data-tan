import streamlit as st
import pandas as pd
import plotly.express as px
from deltalake import DeltaTable
import os
import time
from datetime import datetime
from dotenv import load_dotenv

# --- Configuration Page ---
st.set_page_config(page_title="SkyStream Debug", layout="wide", page_icon="🛠️")
load_dotenv()

# --- Config S3 ---
storage_options = {
    "AWS_ENDPOINT_URL": os.getenv("GARAGE_ENDPOINT", "http://garage:3900"),
    "AWS_ACCESS_KEY_ID": os.getenv("ACCESS_KEY", "minioadmin"),
    "AWS_SECRET_ACCESS_KEY": os.getenv("SECRET_KEY", "minioadmin"),
    "AWS_REGION": "garage",
    "AWS_S3_ALLOW_UNSAFE_SSL": "true",
    "AWS_ALLOW_HTTP": "true",
}

BUCKET = os.getenv("BUCKET_NAME", "datalake")
PATH_TRAFFIC = f"s3://{BUCKET}/gold/traffic_by_country"
PATH_METRICS = f"s3://{BUCKET}/gold/metrics_by_category"

# --- Chargement Robuste ---

def clean_timestamp(df, col_name):
    """
    Tente de nettoyer le timestamp de toutes les manières possibles.
    Gère: Struct (Dict), String, Datetime déjà parsé.
    """
    if df.empty or col_name not in df.columns:
        return df

    def parse_flexible(val):
        # Cas 1: C'est un dict/struct Spark {'start':..., 'end':...}
        if isinstance(val, dict) and 'end' in val:
            return val['end']
        # Cas 2: C'est une Row object (si PyArrow convertit mal)
        if hasattr(val, 'asDict'):
            return val.asDict().get('end')
        # Cas 3: C'est déjà une valeur simple
        return val

    try:
        # 1. Extraction
        df['ts_clean'] = df[col_name].apply(parse_flexible)
        # 2. Conversion forcée en datetime UTC
        df['ts_clean'] = pd.to_datetime(df['ts_clean'], utc=True, errors='coerce')
        # 3. On ne garde que les dates valides
        return df.dropna(subset=['ts_clean'])
    except Exception as e:
        st.error(f"Erreur parsing date sur {col_name}: {e}")
        return df

def load_data_safe(path, name, time_col):
    try:
        # Force le rechargement depuis S3
        dt = DeltaTable(path, storage_options=storage_options)
        df = dt.to_pandas()
        
        if df.empty:
            return None, f"⚠️ Table {name} vide sur S3."
            
        # Nettoyage Temporel
        df = clean_timestamp(df, time_col)
        
        if df.empty or 'ts_clean' not in df.columns:
            return None, f"⚠️ Table {name} chargée mais parsing date échoué."
            
        # Tri par temps décroissant
        df = df.sort_values('ts_clean', ascending=True)
        return df, "OK"
        
    except Exception as e:
        return None, f"❌ Erreur connexion {name}: {str(e)}"

# --- Main App ---

def main():
    st.title("🛠️ SkyStream Dashboard (Mode Correction)")
    
    # Sidebar Paramètres
    with st.sidebar:
        refresh = st.slider("Refresh (sec)", 5, 60, 10)
        st.divider()
        st.write("Debug Infos:")
        if st.button("Vider Cache Streamlit"):
            st.cache_data.clear()
            st.rerun()

    # 1. Chargement
    # Note: Dans Notebook 02, Traffic utilise 'time_window', Metrics utilise 'window'
    df_metrics, status_met = load_data_safe(PATH_METRICS, "Metrics", "window")
    df_traffic, status_traf = load_data_safe(PATH_TRAFFIC, "Traffic", "time_window")

    # --- SECTION DEBUG (Indispensable pour voir le problème) ---
    with st.expander("🔍 Inspecter les Données Brutes (Cliquez ici si rien ne s'affiche)", expanded=True):
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            st.write(f"**Metrics:** {status_met}")
            if df_metrics is not None:
                st.dataframe(df_metrics.tail(5), use_container_width=True)
        with col_d2:
            st.write(f"**Traffic:** {status_traf}")
            if df_traffic is not None:
                st.dataframe(df_traffic.tail(5), use_container_width=True)

    # 2. Affichage des KPIs
    if df_metrics is not None and not df_metrics.empty:
        # On prend la toute dernière fenêtre temporelle disponible
        last_ts = df_metrics['ts_clean'].max()
        df_now = df_metrics[df_metrics['ts_clean'] == last_ts]
        
        st.markdown(f"### ⏱️ Données Live : {last_ts.strftime('%H:%M:%S UTC')}")
        
        kpi1, kpi2, kpi3 = st.columns(3)
        
        # Calculs sécurisés
        total_planes = df_now['aircraft_count'].sum() if 'aircraft_count' in df_now.columns else 0
        
        # Gestion moyenne pondérée safe
        avg_alt = 0
        if 'avg_altitude_m' in df_now.columns and total_planes > 0:
            avg_alt = (df_now['avg_altitude_m'] * df_now['aircraft_count']).sum() / total_planes

        kpi1.metric("Avions détectés", int(total_planes))
        kpi2.metric("Altitude Moyenne", f"{int(avg_alt)} m")
        kpi3.metric("Fenêtre active", "5 min")
        
        st.divider()

        # 3. Graphiques
        c1, c2 = st.columns(2)
        
        with c1:
            st.subheader("Phases de Vol")
            if 'flight_phase' in df_now.columns:
                fig = px.pie(df_now, values='aircraft_count', names='flight_phase', hole=0.4)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("Colonne 'flight_phase' manquante")

        with c2:
            st.subheader("Trafic par Pays")
            if df_traffic is not None and not df_traffic.empty:
                last_ts_traf = df_traffic['ts_clean'].max()
                df_traf_now = df_traffic[df_traffic['ts_clean'] == last_ts_traf]
                
                # Tri explicite pour forcer l'actualisation visuelle
                df_traf_view = df_traf_now.groupby('origin_country')['aircraft_count'].sum().reset_index()
                df_traf_view = df_traf_view.sort_values('aircraft_count', ascending=True).tail(10)
                
                fig2 = px.bar(df_traf_view, x='aircraft_count', y='origin_country', orientation='h')
                st.plotly_chart(fig2, use_container_width=True)
            else:
                st.warning("Pas de données Trafic")

        # 4. Timeline
        st.subheader("Historique récent")
        # On prend les 60 dernières minutes max
        df_hist = df_metrics.tail(100) 
        fig_line = px.area(df_hist, x='ts_clean', y='aircraft_count', color='flight_phase')
        st.plotly_chart(fig_line, use_container_width=True)

    else:
        st.warning("En attente de données... Vérifiez la section 'Inspecter les Données Brutes' ci-dessus.")

    time.sleep(refresh)
    st.rerun()

if __name__ == "__main__":
    main()
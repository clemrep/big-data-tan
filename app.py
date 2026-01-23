#!/usr/bin/env python3
"""
Streamlit Dashboard - Zero Spark Edition
Reads Delta tables from S3/MinIO using deltalake library (live updates).
"""

import os
import logging
import time
from datetime import datetime
from typing import Optional, Tuple
import hashlib

import streamlit as st
import pandas as pd
import plotly.express as px
from deltalake import DeltaTable
from dotenv import load_dotenv
import pyarrow  # Explicit import for Snappy codec support

# --- Configuration ---
load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Variables d'environnement
S3_ENDPOINT = os.getenv("GARAGE_ENDPOINT", "http://garage:3900")
BUCKET_NAME = os.getenv("BUCKET_NAME", "datalake")
ACCESS_KEY = os.getenv("ACCESS_KEY", "minioadmin") 
SECRET_KEY = os.getenv("SECRET_KEY", "minioadmin")

GOLD_TRAFFIC_PATH = f"s3a://{BUCKET_NAME}/gold/traffic_by_country"
GOLD_METRICS_PATH = f"s3a://{BUCKET_NAME}/gold/metrics_by_category"

# Configuration pour Deltalake avec Garage
storage_options = {
    "AWS_ENDPOINT_URL": S3_ENDPOINT,
    "AWS_ACCESS_KEY_ID": ACCESS_KEY,
    "AWS_SECRET_ACCESS_KEY": SECRET_KEY,
    "AWS_REGION": "us-east-1",
    "AWS_S3_ALLOW_UNSAFE_SSL": "true",
    "AWS_ALLOW_HTTP": "true",
}

# --- Session State pour détecteur de changement ---
if "last_traffic_hash" not in st.session_state:
    st.session_state.last_traffic_hash = None
if "last_metrics_hash" not in st.session_state:
    st.session_state.last_metrics_hash = None
if "last_update_time" not in st.session_state:
    st.session_state.last_update_time = None

# --- Fonctions de chargement ---

def compute_data_hash(df: Optional[pd.DataFrame]) -> Optional[str]:
    """Compute hash of dataframe to detect changes."""
    if df is None or df.empty:
        return None
    return hashlib.md5(pd.util.hash_pandas_object(df, index=True).values).hexdigest()

def load_delta_table(path: str, timeout: int = 10) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
    """
    Load Delta table from S3/Garage with error handling and hash.
    Returns: (dataframe, hash_value)
    """
    try:
        logger.info(f"Loading Delta table from: {path}")
        dt = DeltaTable(path, storage_options=storage_options)
        
        # Get table metadata
        logger.info(f"Delta table loaded. Version: {dt.version()}, Files: {len(dt.files())}")
        
        # Convert to pandas with pyarrow backend
        df = dt.to_pandas()
        
        logger.info(f"Data loaded: {len(df)} rows, {len(df.columns)} columns")
        logger.info(f"Columns: {df.columns.tolist()}")
        logger.info(f"First row dtypes: {df.dtypes.to_dict()}")
        
        data_hash = compute_data_hash(df)
        return df if not df.empty else None, data_hash
    except FileNotFoundError:
        logger.warning(f"Delta table not found: {path}")
        return None, None
    except Exception as e:
        logger.error(f"Error loading Delta table {path}: {str(e)}", exc_info=True)
        return None, None
        return None, None

# --- Interface Streamlit ---

st.set_page_config(page_title="Flight Dashboard", page_icon="🌐", layout="wide")
st.title("OpenSky Real-time Flight Dashboard")

# CSS Dark Mode
st.markdown("""
<style>
    .stApp { background-color: #0e1117; }
    div[data-testid="stMetricValue"] { font-size: 2.5rem; color: #ff9900; }
</style>
""", unsafe_allow_html=True)

# --- Sidebar Configuration ---
with st.sidebar:
    st.header("Configuration")
    refresh_rate = st.slider("Refresh interval (sec)", 5, 300, 15, step=5)
    
    status_cols = st.columns(3)
    with status_cols[0]:
        st.metric("DataLake", "OK")
    with status_cols[1]:
        st.metric("Mode", "Live")
    with status_cols[2]:
        st.metric("Storage", "Garage")
    
    with st.expander("Debug Info"):
        st.code(f"S3: {S3_ENDPOINT}\nBucket: {BUCKET_NAME}\nAccess: {ACCESS_KEY[:10]}...", language="text")

st.divider()

# --- Chargement des données en direct ---
placeholder_status = st.empty()
placeholder_content = st.container()

with placeholder_status:
    with st.spinner("Loading data..."):
        df_traffic, hash_traffic = load_delta_table(GOLD_TRAFFIC_PATH)
        df_metrics, hash_metrics = load_delta_table(GOLD_METRICS_PATH)
        
        # Detect change
        data_changed = (hash_traffic != st.session_state.last_traffic_hash or 
                       hash_metrics != st.session_state.last_metrics_hash)
        
        if data_changed:
            st.session_state.last_traffic_hash = hash_traffic
            st.session_state.last_metrics_hash = hash_metrics
            st.session_state.last_update_time = datetime.now()

# --- Affichage du contenu ---
with placeholder_content:
    if df_traffic is not None and not df_traffic.empty:
        # Récupération de la dernière fenêtre temporelle (extract start time from struct)
        # Gold tables have 'time_window' struct with 'start' and 'end' fields
        if "time_window" in df_traffic.columns:
            # Extract start timestamp from window struct
            df_traffic["window_start"] = pd.to_datetime(df_traffic["time_window"].apply(lambda x: x['start'] if isinstance(x, dict) else x))
            latest_window = df_traffic["window_start"].max()
            df_latest_traffic = df_traffic[df_traffic["window_start"] == latest_window].copy()
        else:
            # Fallback if column structure is different
            df_latest_traffic = df_traffic.copy()
        
        # KPIs
        total_flights = int(df_latest_traffic["aircraft_count"].sum())
        
        if not df_latest_traffic.empty:
            top_country_row = df_latest_traffic.sort_values("aircraft_count", ascending=False).iloc[0]
            top_country = f"{top_country_row['origin_country']} ({int(top_country_row['aircraft_count'])})"
        else:
            top_country = "-"

        # Vitesse moyenne
        avg_speed = "N/A"
        if df_metrics is not None and not df_metrics.empty:
            # Debug: Show actual columns
            logger.info(f"Metrics columns: {df_metrics.columns.tolist()}")
            logger.info(f"Metrics sample: {df_metrics.head(2).to_dict()}")
            
            # Extract window start for metrics too
            try:
                if "time_window" in df_metrics.columns:
                    df_metrics["window_start"] = df_metrics["time_window"].apply(
                        lambda x: pd.to_datetime(x['start']) if isinstance(x, dict) and 'start' in x else pd.NaT
                    )
                    df_latest_metrics = df_metrics[df_metrics["window_start"] == latest_window]
                elif "window" in df_metrics.columns:
                    df_metrics["window_start"] = df_metrics["window"].apply(
                        lambda x: pd.to_datetime(x['start']) if isinstance(x, dict) and 'start' in x else pd.NaT
                    )
                    df_latest_metrics = df_metrics[df_metrics["window_start"] == latest_window]
                else:
                    logger.warning("No window column in metrics")
                    df_latest_metrics = df_metrics.copy()
            except Exception as e:
                logger.error(f"Error processing metrics window: {e}")
                df_latest_metrics = df_metrics.copy()
                
            if not df_latest_metrics.empty and "avg_velocity_kmh" in df_latest_metrics.columns:
                avg_speed = f"{int(df_latest_metrics['avg_velocity_kmh'].mean())} km/h"

        # KPIs
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            try:
                window_display = pd.Timestamp(latest_window).strftime('%H:%M:%S') if pd.notna(latest_window) else "N/A"
            except:
                window_display = "N/A"
            st.metric("Window", window_display)
        with c2:
            st.metric("Aircraft", f"{total_flights:,}")
        with c3:
            st.metric("Top Country", top_country)
        with c4:
            st.metric("Avg Speed", avg_speed)
        
        st.divider()
        
        # --- Graphiques en Live ---
        col_left, col_right = st.columns(2)
        
        with col_left:
            st.subheader("Top 15 Countries")
            df_top15 = df_latest_traffic.nlargest(15, "aircraft_count")
            
            if not df_top15.empty:
                fig = px.bar(
                    df_top15, x="aircraft_count", y="origin_country", orientation='h',
                    template="plotly_dark", color="aircraft_count", 
                    color_continuous_scale="Oranges", title=""
                )
                fig.update_layout(showlegend=False, height=400, 
                                margin=dict(l=0, r=0, t=10, b=0),
                                xaxis_title="Aircraft Count", yaxis_title="")
                st.plotly_chart(fig, use_container_width=True, key="bar_chart")
        
        with col_right:
            st.subheader("Flight Metrics")
            if df_metrics is not None and not df_metrics.empty:
                # Use already extracted window_start
                if "window_start" in df_metrics.columns:
                    df_m = df_metrics[df_metrics["window_start"] == latest_window]
                else:
                    df_m = df_metrics.copy()
                    
                if not df_m.empty and "avg_velocity_kmh" in df_m.columns and "avg_altitude_m" in df_m.columns:
                    fig2 = px.scatter(
                        df_m, x="avg_velocity_kmh", y="avg_altitude_m",
                        size="aircraft_count", color="category", 
                        template="plotly_dark",
                        labels={"avg_velocity_kmh": "Speed (km/h)", "avg_altitude_m": "Altitude (m)"}
                    )
                    fig2.update_layout(height=400, showlegend=True,
                                    margin=dict(l=0, r=0, t=10, b=0))
                    st.plotly_chart(fig2, use_container_width=True, key="scatter_chart")
                else:
                    st.info("Metrics not available for this window")
            else:
                st.info("Metrics table not yet populated")

        # Status footer
        update_time = st.session_state.last_update_time or datetime.now()
        st.divider()
        col_status1, col_status2, col_status3 = st.columns(3)
        with col_status1:
            st.caption(f"Last update: {update_time.strftime('%H:%M:%S')}")
        with col_status2:
            st.caption(f"{len(df_latest_traffic)} countries tracked")
        with col_status3:
            st.caption(f"Refresh: {refresh_rate}s")

    else:
        # Waiting screen
        st.warning("Waiting for data in Data Lake...")
        st.info(f"""
        **Connection Status:**
        - **Endpoint:** `{S3_ENDPOINT}`
        - **Bucket:** `{BUCKET_NAME}`
        - **Traffic Path:** `{GOLD_TRAFFIC_PATH}`
        - **Metrics Path:** `{GOLD_METRICS_PATH}`
        
        **Troubleshooting:**
        1. Ensure `docker compose up -d --build` is running
        2. Start 02_Unified_Pipeline.ipynb to populate Gold tables
        3. Check that Spark is writing to the S3 paths above
        """)
        
        # Mini debug
        with st.expander("Debug Details"):
            st.code(f"""
Traffic loaded: {df_traffic is not None}
Metrics loaded: {df_metrics is not None}
S3 Endpoint: {S3_ENDPOINT}
Storage working: Check if Garage is responding
            """, language="python")

# --- Auto-refresh loop ---
placeholder_status.empty()
time.sleep(refresh_rate)
st.rerun()
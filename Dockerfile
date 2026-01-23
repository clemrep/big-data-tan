FROM grosinosky/bigdata_fila3_jupyter:python3.12-spark3.5.3

USER root

RUN pip install --no-cache-dir \
    delta-spark==3.2.0 \
    deltalake==0.24.0 \
    streamlit==1.40.2 \
    pandas==2.2.3 \
    plotly==5.24.0 \
    requests==2.32.0 \
    python-dotenv==1.0.1 \
    kafka-python-ng==2.2.2 \
    watchdog \
    boto3==1.34.0

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import streamlit; print('OK')" || exit 1

USER ${NB_UID}
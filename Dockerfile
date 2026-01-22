FROM grosinosky/bigdata_fila3_jupyter:python3.12-spark3.5.3

USER root

# Ajout de 'anywidget' à la liste
RUN pip install --no-cache-dir \
    delta-spark==3.3.2 \
    python-dotenv \
    pandas \
    plotly \
    ipywidgets \
    anywidget \
    streamlit

USER ${NB_UID}
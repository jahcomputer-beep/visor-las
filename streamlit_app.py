import streamlit as st
import lasio
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from io import BytesIO
from fpdf import FPDF
import tempfile
import os

# Configuración de página
st.set_page_config(page_title="PetroPhysics Pro Viewer", layout="wide")

def crear_pdf(las, fig, ntg, vcl_avg, phie_avg):
    pdf = FPDF()
    pdf.add_page()
    # Usamos fuentes estándar para evitar problemas de compatibilidad
    pdf.set_font("helvetica", "B", 16)
    pdf.cell(0, 10, f"REPORTE PETROFISICO: {las.well.WELL.value}", ln=True, align='C')
    
    pdf.set_font("helvetica", "", 10)
    pdf.ln(5)
    pdf.cell(0, 10, "RESUMEN DE RESULTADOS DE INTERVALO:", ln=True)
    pdf.cell(0, 7, f"- Net-to-Gross (NTG): {ntg:.2%}", ln=True)
    pdf.cell(0, 7, f"- Vcl Promedio: {vcl_avg:.2%}", ln=True)
    pdf.cell(0, 7, f"- Porosidad Efectiva Promedio: {phie_avg:.2%}", ln=True)
    
    # Manejo de imagen temporal para el gráfico
    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmpfile:
        # kaleido debe estar instalado para esto
        fig.write_image(tmpfile.name, engine="kaleido")
        pdf.ln(10)
        pdf.image(tmpfile.name, x=10, y=None, w=180)
    
    # Eliminamos el archivo temporal después de usarlo
    if os.path.exists(tmpfile.name):
        os.remove(tmpfile.name)
        
    # Importante: output() en fpdf2 devuelve bytes por defecto
    return pdf.output()

st.title("📊 Visor Petrofisico Profesional")
st.markdown("Analisis interactivo de archivos .las con calculos de $V_{cl}$, $PHIE$ y $NTG$")

archivo = st.file_uploader("Cargar archivo .las", type=["las"])

if archivo:
    # --- MANEJO DE CODIFICACION ---
    raw_data = archivo.read()
    try:
        string_data = raw_data.decode("utf-8")
    except UnicodeDecodeError:
        string_data = raw_data.decode("latin-1")
    
    # Lectura del LAS
    las = lasio.read(string_data)
    df = las.df()
    df.index.name = 'DEPTH'
    
    # Paso de muestreo
    try:
        paso = abs(df.index[1] - df.index[0])
    except:
        paso = 0.5

    # --- SIDEBAR ---
    st.sidebar.header("1. Configuracion")
    gr_col = st.sidebar.selectbox("Curva Gamma Ray (GR)", df.columns, index=0)
    res_col = st.sidebar.selectbox("Curva Resistividad", df.columns, index=min(1, len(df.columns)-1))
    phi_col = st.sidebar.selectbox("Curva Porosidad Total", df.columns, index=min(2, len(df.columns)-1))

    st.sidebar.header("2. Interpretacion")
    cutoff_gr = st.sidebar.slider("Corte GR (Sand/Shale)", 0, 150, 60)
    gr_clean = st.sidebar.number_input("GR Arena Limpia", value=float(df[gr_col].min()))
    gr_shale = st.sidebar.number_input("GR Arcilla Pura", value=float(df[gr_col].max()))

    # --- CALCULOS ---
    df['VCL'] = ((df[gr_col] - gr_clean) / (gr_shale - gr_clean)).clip(0, 1)
    df['PHIE'] = (df[phi_col] * (1 - df['VCL'])).clip(0, 1)

    datos_v = df[gr_col].dropna()
    esp_total = datos_v.index.max() - datos_v.index.min()
    arena_neta = len(datos_v[datos_v < cutoff_gr]) * paso
    ntg_val = arena_neta / esp_total if esp_total > 0 else 0

    # --- GRAFICO ---
    fig = make_subplots(rows=1, cols=3, shared_yaxes=True, horizontal_spacing=0.03,
                        subplot_titles=("Litologia & Vcl", "Resistividad", "Porosidades"))

    # Track 1
    fig.add_trace(go.Scatter(x=df[gr_col], y=df.index, name="GR", line=dict(color="black")), row=1, col=1)
    df_sand = df.copy()
    df_sand.loc[df_sand[gr_col] > cutoff_gr, gr_col] = cutoff_gr
    fig.add_trace(go.Scatter(x=df_sand[gr_col], y=df_sand.index, fill='tozerox', 
                             fillcolor='rgba(255, 255, 0, 0.4)', line=dict(width=0), showlegend=False), row=1, col=1)

    # Track 2
    fig.add_trace(go.Scatter(x=df[res_col], y=df.index, name="Res", line=dict(color="red")), row=1, col=2)
    fig.update_xaxes(type="log", row=1, col=2)

    # Track 3
    fig.add_trace(go.Scatter(x=df[phi_col], y=df.index, name="Phi Tot", line=dict(color="blue", dash='dash')), row=1, col=3)
    fig.add_trace(go.Scatter(x=df['PHIE'], y=df.index, name="Phi Efec", line=dict(color="black")), row=1, col=3)
    fig.add_trace(go.Scatter(x=df['VCL'], y=df.index, name="Vcl", fill='tozerox', 
                             fillcolor='rgba(139, 69, 19, 0.2)', line=dict(color="brown", width=1)), row=1, col=3)

    fig.update_layout(height=900, template="plotly_white", hovermode="y unified")
    fig.update_yaxes(autorange="reversed", showgrid=True, minor=dict(showgrid=True, nticks=10), matches='y')


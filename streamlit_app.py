import streamlit as st
import lasio
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from io import BytesIO
from fpdf import FPDF
import tempfile
import os

# Configuración de página para Streamlit Cloud
st.set_page_config(page_title="PetroPhysics Pro Viewer", layout="wide")

def crear_pdf(las, fig, ntg, vcl_avg, phie_avg):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, f"REPORTE PETROFÍSICO: {las.well.WELL.value}", ln=True, align='C')
    
    pdf.set_font("Arial", "", 10)
    pdf.ln(5)
    pdf.cell(0, 10, "RESUMEN DE RESULTADOS DE INTERVALO:", ln=True)
    pdf.cell(0, 7, f"- Net-to-Gross (NTG): {ntg:.2%}", ln=True)
    pdf.cell(0, 7, f"- Vcl Promedio: {vcl_avg:.2%}", ln=True)
    pdf.cell(0, 7, f"- Porosidad Efectiva Promedio: {phie_avg:.2%}", ln=True)
    
    # Guardar imagen temporal del gráfico para el PDF
    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmpfile:
        fig.write_image(tmpfile.name)
        pdf.ln(10)
        pdf.image(tmpfile.name, x=10, y=None, w=180)
    return pdf.output()

st.title("📊 Visor Petrofísico Profesional")
st.markdown("Análisis interactivo de archivos .las con cálculos de $V_{cl}$, $PHIE$ y $NTG$")

archivo = st.file_uploader("Cargar archivo .las", type=["las"])

if archivo:
    # --- ARREGLO DE CODIFICACIÓN (UTF-8 / LATIN-1) ---
    raw_data = archivo.read()
    try:
        string_data = raw_data.decode("utf-8")
    except UnicodeDecodeError:
        string_data = raw_data.decode("latin-1")
    
    # Lectura del archivo LAS
    las = lasio.read(string_data)
    df = las.df()
    df.index.name = 'DEPTH'
    
    # Detectar paso de muestreo (Step)
    try:
        paso = abs(df.index[1] - df.index[0])
    except:
        paso = 0.5

    # --- SIDEBAR: CONFIGURACIÓN ---
    st.sidebar.header("1. Configuración de Canales")
    gr_col = st.sidebar.selectbox("Curva Gamma Ray (GR)", df.columns, index=0)
    res_col = st.sidebar.selectbox("Curva Resistividad", df.columns, index=min(1, len(df.columns)-1))
    phi_col = st.sidebar.selectbox("Curva Porosidad Total", df.columns, index=min(2, len(df.columns)-1))

    st.sidebar.header("2. Interpretación")
    cutoff_gr = st.sidebar.slider("Corte GR (Sand/Shale)", 0, 150, 60)
    gr_clean = st.sidebar.number_input("GR Arena Limpia (Min)", value=float(df[gr_col].min()))
    gr_shale = st.sidebar.number_input("GR Arcilla Pura (Max)", value=float(df[gr_col].max()))

    # --- CÁLCULOS ---
    # Volumen de Arcilla Lineal
    df['VCL'] = ((df[gr_col] - gr_clean) / (gr_shale - gr_clean)).clip(0, 1)
    # Porosidad Efectiva corregida
    df['PHIE'] = (df[phi_col] * (1 - df['VCL'])).clip(0, 1)

    # Net-to-Gross
    datos_v = df[gr_col].dropna()
    espesor_total = datos_v.index.max() - datos_v.index.min()
    arena_neta = len(datos_v[datos_v < cutoff_gr]) * paso
    ntg_val = arena_neta / espesor_total if espesor_total > 0 else 0

    # --- GRÁFICO MULTI-TRACK ---
    fig = make_subplots(rows=1, cols=3, shared_yaxes=True, horizontal_spacing=0.03,
                        subplot_titles=("Litología & Vcl", "Resistividad", "Porosidades"))

    # Track 1: Gamma Ray y Sombreado de Arena
    fig.add_trace(go.Scatter(x=df[gr_col], y=df.index, name="GR", line=dict(color="black")), row=1, col=1)
    
    # Sombreado corregido con 'tozerox'
    df_sand = df.copy()
    df_sand.loc[df_sand[gr_col] > cutoff_gr, gr_col] = cutoff_gr
    fig.add_trace(go.Scatter(
        x=df_sand[gr_col], y=df_sand.index, 
        fill='tozerox', 
        fillcolor='rgba(255, 255, 0, 0.4)', 
        line=dict(width=0), 
        name="Zona Arena",
        showlegend=False
    ), row=1, col=1)

    # Track 2: Resistividad (Logarítmica)
    fig.add_trace(go.Scatter(x=df[res_col], y=df.index, name="Res", line=dict(color="red")), row=1, col=2)
    fig.update_xaxes(type="log", row=1, col=2)

    # Track 3: Porosidades y Vcl
    fig.add_trace(go.Scatter(x=df[phi_col], y=df.index, name="Phi Total", line=dict(color="blue", dash='dash')), row=1, col=3)
    fig.add_trace(go.Scatter(x=df['PHIE'], y=df.index, name="Phi Efectiva", line=dict(color="black")), row=1, col=3)
    
    # Sombreado de Arcilla en el Track 3
    fig.add_trace(go.Scatter(
        x=df['VCL'], y=df.index, 
        name="Vcl", 
        fill='tozerox', 
        fillcolor='rgba(139, 69, 19, 0.2)', 
        line=dict(color="brown", width=1)
    ), row=1, col=3)

    # Configuración de Ejes y Alta Precisión
    fig.update_layout(height=900, hovermode="y unified", template="plotly_white")
    fig.update_yaxes(
        autorange="reversed", 
        title="PROFUNDIDAD (ft)",
        showgrid=True, 
        gridcolor='LightGrey', 
        minor=dict(showgrid=True, nticks=10), 
        matches='y',
        showspikes=True, spikemode="across", spikethickness=1, spikecolor="black"
    )
    
    st.plotly_chart(fig, use_container_width=True)

    # --- MÉTRICAS Y DESCARGAS ---
    st.sidebar.markdown("---")
    st.sidebar.subheader("Resultados")
    st.sidebar.metric("Net-to-Gross", f"{ntg_val:.2%}")
    st.sidebar.metric("PHIE Promedio", f"{df['PHIE'].mean():.2%}")

    c1, c2 = st.columns(2)
    with c1:
        buf_xl = BytesIO()
        with pd.ExcelWriter(buf_xl, engine='openpyxl') as wr:
            df.to_excel(wr, sheet_name='Resultados_Petrofisicos')
            meta = [{"Mnemo": i.mnemonic, "Valor": i.value, "Unidad": i.unit} for i in las.well]
            pd.DataFrame(meta).to_excel(wr, sheet_name='Encabezado', index=False)
        st.download_button("📥 Descargar Excel", buf_xl.getvalue(), f"{las.well.WELL.value}_Data.xlsx")
    
    with c2:
        pdf_rep = crear_pdf(las, fig, ntg_val, df['VCL'].mean(), df['PHIE'].mean())
        st.download_button("📄 Descargar Reporte PDF", pdf_rep, f"Reporte_{las.well.WELL.value}.pdf")

else:
    st.info("👋 Sube un archivo .las para iniciar el análisis interactivo.")

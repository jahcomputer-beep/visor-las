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
    pdf.set_font("helvetica", "B", 16)
    pdf.cell(0, 10, f"REPORTE PETROFISICO: {las.well.WELL.value}", ln=True, align='C')
    
    pdf.set_font("helvetica", "", 10)
    pdf.ln(5)
    pdf.cell(0, 10, "RESUMEN DE RESULTADOS DE INTERVALO:", ln=True)
    pdf.cell(0, 7, f"- Net-to-Gross (NTG): {ntg:.2%}", ln=True)
    pdf.cell(0, 7, f"- Vcl Promedio: {vcl_avg:.2%}", ln=True)
    pdf.cell(0, 7, f"- Porosidad Efectiva Promedio: {phie_avg:.2%}", ln=True)
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmpfile:
        fig.write_image(tmpfile.name, engine="kaleido")
        pdf.ln(10)
        pdf.image(tmpfile.name, x=10, y=None, w=180)
    
    if os.path.exists(tmpfile.name):
        os.remove(tmpfile.name)
        
    # Convertimos el PDF a bytes puros antes de devolverlo
    return bytes(pdf.output())

st.title("📊 Visor Petrofisico Profesional")

archivo = st.file_uploader("Cargar archivo .las", type=["las"])

if archivo:
    raw_data = archivo.read()
    try:
        string_data = raw_data.decode("utf-8")
    except UnicodeDecodeError:
        string_data = raw_data.decode("latin-1")
    
    las = lasio.read(string_data)
    df = las.df()
    df.index.name = 'DEPTH'
    
    paso = abs(df.index[1] - df.index[0]) if len(df) > 1 else 0.5

    # --- SIDEBAR ---
    st.sidebar.header("Configuracion")
    gr_col = st.sidebar.selectbox("Gamma Ray", df.columns, index=0)
    res_col = st.sidebar.selectbox("Resistividad", df.columns, index=min(1, len(df.columns)-1))
    phi_col = st.sidebar.selectbox("Porosidad", df.columns, index=min(2, len(df.columns)-1))

    cutoff_gr = st.sidebar.slider("Corte GR", 0, 150, 60)
    gr_clean = st.sidebar.number_input("GR Limpio", value=float(df[gr_col].min()))
    gr_shale = st.sidebar.number_input("GR Arcilla", value=float(df[gr_col].max()))

    # --- CALCULOS ---
    df['VCL'] = ((df[gr_col] - gr_clean) / (gr_shale - gr_clean)).clip(0, 1)
    df['PHIE'] = (df[phi_col] * (1 - df['VCL'])).clip(0, 1)

    datos_v = df[gr_col].dropna()
    esp_total = datos_v.index.max() - datos_v.index.min()
    arena_neta = len(datos_v[datos_v < cutoff_gr]) * paso
    ntg_val = arena_neta / esp_total if esp_total > 0 else 0

    # --- GRAFICO ---
    fig = make_subplots(rows=1, cols=3, shared_yaxes=True, horizontal_spacing=0.03,
                        subplot_titles=("GR & Litologia", "Resistividad", "Porosidad"))

    fig.add_trace(go.Scatter(x=df[gr_col], y=df.index, name="GR", line=dict(color="black")), row=1, col=1)
    df_sand = df.copy()
    df_sand.loc[df_sand[gr_col] > cutoff_gr, gr_col] = cutoff_gr
    fig.add_trace(go.Scatter(x=df_sand[gr_col], y=df_sand.index, fill='tozerox', 
                             fillcolor='rgba(255, 255, 0, 0.4)', line=dict(width=0), showlegend=False), row=1, col=1)

    fig.add_trace(go.Scatter(x=df[res_col], y=df.index, name="Res", line=dict(color="red")), row=1, col=2)
    fig.update_xaxes(type="log", row=1, col=2)

    fig.add_trace(go.Scatter(x=df[phi_col], y=df.index, name="Phi T", line=dict(color="blue", dash='dash')), row=1, col=3)
    fig.add_trace(go.Scatter(x=df['PHIE'], y=df.index, name="Phi E", line=dict(color="black")), row=1, col=3)

    fig.update_layout(height=800, template="plotly_white")
    fig.update_yaxes(autorange="reversed", matches='y')
    
    # MOSTRAMOS EL GRAFICO
    st.plotly_chart(fig, use_container_width=True)

    # --- BOTONES DE DESCARGA ---
    st.sidebar.markdown("---")
    
    # Excel con BytesIO
    buffer_excel = BytesIO()
    with pd.ExcelWriter(buffer_excel, engine='openpyxl') as wr:
        df.to_excel(wr, index=True)
    
    st.sidebar.download_button("📥 Descargar Excel", data=buffer_excel.getvalue(), 
                               file_name="datos_procesados.xlsx", mime="application/vnd.ms-excel")
    
    # PDF con manejo de errores
    try:
        pdf_data = crear_pdf(las, fig, ntg_val, df['VCL'].mean(), df['PHIE'].mean())
        st.sidebar.download_button("📄 Descargar PDF", data=pdf_data, 
                                   file_name="reporte.pdf", mime="application/pdf")
    except Exception as e:
        st.sidebar.error(f"Error PDF: {e}")

else:
    st.info("Sube un archivo .las para comenzar.")

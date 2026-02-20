# 📊 PetroPhysics LAS Pro-Viewer
Esta es una solución profesional e interactiva para la visualización y análisis preliminar de registros de pozos en formato **.las (Log ASCII Standard)**. Diseñada para geofísicos y petrofísicos que necesitan rapidez y precisión en el campo o la oficina.

## 🚀 Características Principales

* **Visualización Multi-Track:** Gráficos sincronizados de Litología, Resistividad y Porosidad con escalas ajustables.
* **Interpretación en Tiempo Real:** * Cálculo automático de **Volumen de Arcilla ()**.
* Cálculo de **Porosidad Efectiva ()**.
* Determinación de **Net-to-Gross (NTG)** mediante cortes (cut-offs) dinámicos.
* **Precisión de Escala:** Cuadrícula de profundidad detallada (paso de 1 ft) para una lectura exacta de intervalos.
* **Exportación Profesional:** * Generación de reportes en **PDF** con gráficos de interpretación.
* Conversión de datos procesados a **Excel (.xlsx)** incluyendo las curvas calculadas.
## 🛠️ Tecnologías Utilizadas
* **Python 3.x**
* **Streamlit:** Interfaz de usuario moderna y web-based.
* **Lasio:** Lectura y manipulación de archivos LAS.
* **Pandas:** Procesamiento de datos y cálculos matemáticos.
* **Plotly:** Gráficos interactivos con zoom sincronizado.
* **FPDF2:** Generación de reportes técnicos.
## 📋 Requisitos e Instalación
Si deseas correrlo de forma local:
1. Clonar el repositorio:
```bash
git clone https://github.com/tu-usuario/visor-las.git

```

2. Instalar dependencias:
```bash
pip install -r requirements.txt

```

3. Ejecutar la aplicación:
```bash
streamlit run streamlit_app.py

```
## 📈 Metodología de Cálculo

El sistema utiliza el modelo lineal para el Índice de Rayos Gamma:
Y la porosidad efectiva corregida:
---
### ¿Cómo personalizar el link de la medalla?
En la segunda línea del código de arriba, donde dice `tu-app-url.streamlit.app`, asegúrate de reemplazarlo con la dirección real que te asigne Streamlit Cloud una vez que publiques la app.


from datetime import datetime
import glob
import os
import pandas as pd
import plotly.express as px
import streamlit as st
from PIL import Image

# Configuración de la página
st.set_page_config(
    page_title="Dashboard Competitivo: Mystic vs Competencia", layout="wide"
)


# 1. Carga automática y segura del archivo de Excel
@st.cache_data
def load_data():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    pattern = os.path.join(script_dir, "*.xlsx")
    archivos = glob.glob(pattern)

    if not archivos:
        return None  # Retornamos None para manejarlo visualmente

    df = pd.read_excel(archivos[0])
    df.columns = [c.strip() for c in df.columns]
    return df


# --- CARGA DE LOGO ---
try:
    logo = Image.open("Mystic.jpg")
except FileNotFoundError:
    try:
        logo = Image.open("image_0.png")
    except FileNotFoundError:
        logo = None

# --- TÍTULO Y LOGO EN LA CABECERA (LOGO MÁS GRANDE) ---
header_col1, header_col2 = st.columns([1.2, 10])
with header_col1:
    if logo:
        st.image(logo, width=150)  # Logo ampliado
with header_col2:
    st.title("📊 Dashboard Competitivo: Mystic vs Competencia (Dispersión)")
    st.markdown(
        """
        <div style='color: #555555; font-size: 14px; margin-bottom: 20px;'>
            Dashboard analítico desarrollado por <b>Jorge Abraham</b> para Mystic. Todos los derechos de diseño, lógica de negocio y procesamiento de datos reservados.
        </div>
        """,
        unsafe_allow_html=True,
    )

df = load_data()

if df is None:
    st.error(
        "⚠️ **No se encontró ningún archivo de Excel (.xlsx)** en la misma"
        " carpeta de este script."
    )
    st.info(
        "Por favor, coloca tu archivo de datos Excel en el mismo directorio donde"
        " estás ejecutando Streamlit."
    )
    st.stop()

# Validación de la columna de Categoría
col_cat = "Floor share Venezuela - Categoria"
if col_cat not in df.columns:
    st.error(f"No se encuentra la columna '{col_cat}' en el archivo.")
    st.stop()

# Asegurar que la columna de precio sea numérica
col_precio = "Floor share Venezuela - precio"
if col_precio in df.columns:
    df[col_precio] = pd.to_numeric(
        df[col_precio].astype(str).str.replace(",", "."), errors="coerce"
    )

# 2. Panel de Filtros Globales en la barra lateral
st.sidebar.header("Filtros Globales")

# Filtro por Empleado
col_empleado = "Empleado" if "Empleado" in df.columns else None
if col_empleado:
    empleados = ["Todos"] + sorted(df[col_empleado].dropna().unique().tolist())
    empleado_sel = st.sidebar.selectbox("Seleccione Empleado / Promotor:", empleados)
    if empleado_sel != "Todos":
        df = df[df[col_empleado] == empleado_sel]

# Filtro por Cadena
if "Cadena" in df.columns:
    clientes = ["Todas"] + sorted(df["Cadena"].dropna().unique().tolist())
    cliente_sel = st.sidebar.selectbox("Seleccione Cliente / Cadena:", clientes)
    if cliente_sel != "Todas":
        df = df[df["Cadena"] == cliente_sel]

# Filtro por Semana / Fecha
col_semana = "Fecha y hora de la encuesta"
if col_semana in df.columns:
    df[col_semana] = df[col_semana].astype(str).str.strip()
    semanas_unicas = sorted(df[col_semana].dropna().unique().tolist())
    semanas = ["Todas"] + semanas_unicas
    semana_sel = st.sidebar.selectbox("Seleccione Semana:", semanas)
    if semana_sel != "Todas":
        df = df[df[col_semana] == semana_sel]

# Filtro por Categoría
categorias_disponibles = sorted(df[col_cat].dropna().unique().tolist())
categoria_sel = st.sidebar.selectbox(
    "Seleccione Categoría:", ["Todas"] + categorias_disponibles
)
if categoria_sel != "Todas":
    df = df[df[col_cat] == categoria_sel]

# Filtro por Marca
col_marca = "Floor share Venezuela - Marca"
marcas_disponibles = (
    sorted(df[col_marca].dropna().unique().tolist())
    if col_marca in df.columns
    else []
)
marcas_seleccion = st.sidebar.multiselect(
    "Filtrar Marcas (Dejar vacío para ver todas):", marcas_disponibles
)

if marcas_seleccion:
    df = df[df[col_marca].isin(marcas_seleccion)]

# Filtro por Modelo / Segmento
col_modelo = "Floor share Venezuela - Segmento/Modelo"
modelos_disponibles = (
    sorted(df[col_modelo].dropna().unique().tolist())
    if col_modelo in df.columns
    else []
)
modelos_seleccion = st.sidebar.multiselect(
    "Filtrar Modelos / Segmentos (Dejar vacío para ver todas):",
    modelos_disponibles,
)

if modelos_seleccion:
    df = df[df[col_modelo].isin(modelos_seleccion)]

# Obtener categorías finales a mostrar
categorias_a_mostrar = (
    sorted(df[col_cat].dropna().unique().tolist()) if not df.empty else []
)

if not categorias_a_mostrar:
    st.warning("No hay datos disponibles con los filtros seleccionados.")
    st.stop()

# Pestañas superiores para las categorías activas
pestanas = st.tabs(categorias_a_mostrar)

# Diccionarios de colores y figuras (con valores por defecto para marcas imprevistas)
color_palette = [
    "#66CCFF",
    "#8CC152",
    "#FF9933",
    "#9933FF",
    "#E6194B",
    "#F032E6",
    "#33CCCC",
    "#FFE119",
    "#4363D8",
    "#f58231",
]
symbol_list = [
    "square",
    "circle",
    "diamond",
    "triangle-up",
    "cross",
    "x",
    "pentagon",
    "hexagram",
    "star",
]

# 3. Generación de gráficos interactivos con Plotly por categoría
for i, cat in enumerate(categorias_a_mostrar):
    with pestanas[i]:
        st.subheader(f"Categoría: {cat}")
        df_cat = df[df[col_cat] == cat]

        if df_cat.empty:
            st.info("No hay registros en esta categoría con los filtros actuales.")
            continue

        df_cat_counts = (
            df_cat.groupby([col_cat, col_marca])
            .size()
            .reset_index(name="Cantidad_Categoria")
        )
        df_cat_plot = df_cat.merge(
            df_cat_counts, on=[col_cat, col_marca], how="left"
        )

        df_cat_total_marca = df_cat[col_marca].value_counts().reset_index()
        df_cat_total_marca.columns = [col_marca, "Total_Marca"]
        df_cat_plot = df_cat_plot.merge(
            df_cat_total_marca, on=col_marca, how="left"
        )

        df_cat_plot["Marca Conteo"] = (
            df_cat_plot[col_marca]
            + " (Total: "
            + df_cat_plot["Total_Marca"].astype(str)
            + ")"
        )

        # Asignación automática y segura de colores y figuras por índice de marca
        temp_color_map = {}
        temp_symbol_map = {}

        unique_marcas = sorted(df_cat_total_marca[col_marca].tolist())
        for idx, m_val in enumerate(unique_marcas):
            total_count = df_cat_total_marca.loc[
                df_cat_total_marca[col_marca] == m_val, "Total_Marca"
            ].values[0]
            label_key = f"{m_val} (Total: {total_count})"

            temp_color_map[label_key] = color_palette[idx % len(color_palette)]
            temp_symbol_map[label_key] = symbol_list[idx % len(symbol_list)]

        if col_modelo in df_cat_plot.columns and col_precio in df_cat_plot.columns:
            fig = px.scatter(
                df_cat_plot,
                x=col_precio,
                y=col_modelo,
                color="Marca Conteo",
                symbol="Marca Conteo",
                color_discrete_map=temp_color_map,
                symbol_map=temp_symbol_map,
                hover_data={
                    col_precio: True,
                    col_modelo: True,
                    col_marca: True,
                    "Cantidad_Categoria": True,
                    "Cadena": True if "Cadena" in df_cat_plot.columns else False,
                    col_empleado
                    if col_empleado
                    else "Empleado": True
                    if col_empleado and col_empleado in df_cat_plot.columns
                    else False,
                },
                height=max(500, df_cat_plot[col_modelo].nunique() * 30),
                category_orders={"Marca Conteo": sorted(list(temp_color_map.keys()))},
            )

            fig.update_traces(marker=dict(size=13, line=dict(width=1, color="black")))
            fig.update_layout(
                title=f"Dispersión de Precios por Modelo y Marca - {cat}",
                xaxis_title="Precio PVP ($)",
                yaxis_title="Modelo / Segmento",
                legend_title="Marca (Total Registros)",
                hovermode="closest",
            )

            st.plotly_chart(fig, use_container_width=True)
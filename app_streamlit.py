import streamlit as st
import pandas as pd
import plotly.express as px
import os
import glob

# Configuración de la página
st.set_page_config(page_title="Dashboard Competitivo: Mystic vs Competencia", layout="wide")

# 1. Carga automática y limpieza del archivo de Excel
@st.cache_data
def load_data():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    pattern = os.path.join(script_dir, "precios*.xlsx")
    archivos = glob.glob(pattern)
    if not archivos:
        raise FileNotFoundError("No se encontró ningún archivo de Excel que empiece por 'precios'.")
    df = pd.read_excel(archivos[0])
    df.columns = [c.strip() for c in df.columns]
    
    if "Fecha y hora de la encuesta" in df.columns:
        df["Fecha y hora de la encuesta"] = df["Fecha y hora de la encuesta"].astype(str).str.strip()
        
    return df

st.title("📊 Dashboard Competitivo: Mystic vs Competencia (Dispersión)")

try:
    df = load_data()
except Exception as e:
    st.error(f"Error al cargar el archivo: {e}")
    st.stop()

# Validación inicial de columnas clave
if "Categoria" not in df.columns:
    st.error("El archivo no contiene la columna 'Categoria'.")
    st.stop()

# 2. Panel de Filtros Globales en la barra lateral
st.sidebar.header("Filtros Globales")

# Filtro por Empleado / Encuestador (Soporta múltiples variaciones comunes de nombre de columna)
col_empleado = next((c for c in ["Empleado", "Promotor", "Usuario", "Encuestador"] if c in df.columns), None)
if col_empleado:
    empleados = ["Todos"] + sorted(df[col_empleado].dropna().unique().tolist())
    empleado_sel = st.sidebar.selectbox("Seleccione Empleado / Promotor:", empleados)
    if empleado_sel != "Todos":
        df = df[df[col_empleado] == empleado_sel]

# Filtro por Cliente / Cadena
if "Cadena" in df.columns:
    clientes = ["Todas"] + sorted(df["Cadena"].dropna().unique().tolist())
    cliente_sel = st.sidebar.selectbox("Seleccione Cliente / Cadena:", clientes)
    if cliente_sel != "Todas":
        df = df[df["Cadena"] == cliente_sel]

# Filtro por Semana
if "Fecha y hora de la encuesta" in df.columns:
    semanas_unicas = sorted(df["Fecha y hora de la encuesta"].dropna().unique().tolist())
    semanas = ["Todas"] + semanas_unicas
    semana_sel = st.sidebar.selectbox("Seleccione Semana:", semanas)
    if semana_sel != "Todas":
        df = df[df["Fecha y hora de la encuesta"] == semana_sel]

# Filtro por Categoría
categorias_disponibles = sorted(df["Categoria"].dropna().unique().tolist())
categoria_sel = st.sidebar.selectbox("Seleccione Categoría:", ["Todas"] + categorias_disponibles)
if categoria_sel != "Todas":
    df = df[df["Categoria"] == categoria_sel]

# Filtro para destacar marcas
marcas_disponibles = sorted(df["Marca"].dropna().unique().tolist()) if "Marca" in df.columns else []
marcas_seleccion = st.sidebar.multiselect("Filtrar Marcas (Dejar vacío para ver todas):", marcas_disponibles)

if marcas_seleccion:
    df = df[df["Marca"].isin(marcas_seleccion)]

# Filtro por Modelo / Segmento (Multiselect para permitir filtrar uno o varios modelos específicos)
modelos_disponibles = sorted(df["Segmento/Modelo"].dropna().unique().tolist()) if "Segmento/Modelo" in df.columns else []
modelos_seleccion = st.sidebar.multiselect("Filtrar Modelos / Segmentos (Dejar vacío para ver todas):", modelos_disponibles)

if modelos_seleccion:
    df = df[df["Segmento/Modelo"].isin(modelos_seleccion)]

# Obtener categorías finales a mostrar
categorias_a_mostrar = sorted(df["Categoria"].dropna().unique().tolist()) if not df.empty else []

if not categorias_a_mostrar:
    st.warning("No hay datos disponibles con los filtros seleccionados.")
    st.stop()

# Pestañas superiores para las categorías activas
pestanas = st.tabs(categorias_a_mostrar)

# 3. Diccionario de colores personalizados (Mystic cambiado a azul chillón / eléctrico #00FFFF o #00BFFF)
color_map = {
    "Mystic": "#00FFFF",        # Azul chillón / cian eléctrico
    "Gtronic": "#2ca02c",       # Verde
    "Sj Electronic": "#d62728", # Rojo
    "Aiwa": "#000000",          # Negro
    "Sam": "#e377c2",           # Fucsia claro
    "Gplus": "#d2b48c",         # Marrón claro (Tan)
    "Omega Electronis": "green",# Verde
    "TCL": "red"                # Rojo
}

# 3. Generación de gráficos interactivos con Plotly por categoría
for i, cat in enumerate(categorias_a_mostrar):
    with pestanas[i]:
        st.subheader(f"Categoría: {cat}")
        df_cat = df[df["Categoria"] == cat]
        
        if df_cat.empty:
            st.info("No hay registros en esta categoría con los filtros actuales.")
            continue
        
        if "Segmento/Modelo" in df_cat.columns and "Precio PVP" in df_cat.columns:
            # Crear gráfico de dispersión interactivo con Plotly Express usando formas (symbol)
            fig = px.scatter(
                df_cat,
                x="Precio PVP",
                y="Segmento/Modelo",
                color="Marca",
                symbol="Marca",
                color_discrete_map=color_map,
                symbol_map={
                    "Omega Electronis": "square-open",
                    "TCL": "cross",
                    "Mystic": "circle",
                    "Gtronic": "circle",
                    "Sj Electronic": "circle",
                    "Aiwa": "circle",
                    "Sam": "circle",
                    "Gplus": "circle"
                },
                hover_data={
                    "Precio PVP": True,
                    "Segmento/Modelo": True,
                    "Marca": True,
                    "Cadena": True if "Cadena" in df_cat.columns else False,
                    col_empleado: True if col_empleado and col_empleado in df_cat.columns else False
                },
                height=max(500, df_cat["Segmento/Modelo"].nunique() * 30)
            )
            
            # Mejorar diseño y legibilidad del gráfico
            fig.update_traces(marker=dict(size=12, line=dict(width=1, color='black')))
            fig.update_layout(
                title=f"Dispersión de Precios por Modelo y Marca - {cat}",
                xaxis_title="Precio PVP ($)",
                yaxis_title="Modelo / Segmento",
                legend_title="Marca",
                hovermode="closest"
            )
            
            # Renderizar en Streamlit de forma interactiva
            st.plotly_chart(fig, use_container_width=True)
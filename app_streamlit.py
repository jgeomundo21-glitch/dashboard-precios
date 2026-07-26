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
    pattern = os.path.join(script_dir, "*.xlsx")
    archivos = glob.glob(pattern)
    if not archivos:
        raise FileNotFoundError("No se encontró ningún archivo de Excel (.xlsx) en el repositorio.")
    
    df = pd.read_excel(archivos[0])
    df.columns = [c.strip() for c in df.columns]
    
    return df

st.title("📊 Dashboard Competitivo: Mystic vs Competencia (Dispersión)")

try:
    df = load_data()
except Exception as e:
    st.error(f"Error al cargar el archivo: {e}")
    st.stop()

# Validación de la columna de Categoría
col_cat = "Floor share Venezuela - Categoria"
if col_cat not in df.columns:
    st.error(f"No se encuentra la columna '{col_cat}' en el archivo.")
    st.stop()

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

# Filtro por Semana (Asegúrate de que el nombre entre comillas coincida con tu columna real)
col_semana = "Fecha y hora de la encuesta"  # Cámbialo si tu columna se llama "Semana"

if col_semana in df.columns:
    df[col_semana] = df[col_semana].astype(str).str.strip()
    semanas_unicas = sorted(df[col_semana].dropna().unique().tolist())
    semanas = ["Todas"] + semanas_unicas
    semana_sel = st.sidebar.selectbox("Seleccione Semana:", semanas)
    if semana_sel != "Todas":
        df = df[df[col_semana] == semana_sel]

# Filtro por Categoría
categorias_disponibles = sorted(df[col_cat].dropna().unique().tolist())
categoria_sel = st.sidebar.selectbox("Seleccione Categoría:", ["Todas"] + categorias_disponibles)
if categoria_sel != "Todas":
    df = df[df[col_cat] == categoria_sel]

# Filtro por Marca
col_marca = "Floor share Venezuela - Marca"
marcas_disponibles = sorted(df[col_marca].dropna().unique().tolist()) if col_marca in df.columns else []
marcas_seleccion = st.sidebar.multiselect("Filtrar Marcas (Dejar vacío para ver todas):", marcas_disponibles)

if marcas_seleccion:
    df = df[df[col_marca].isin(marcas_seleccion)]

# Filtro por Modelo / Segmento
col_modelo = "Floor share Venezuela - Segmento/Modelo"
modelos_disponibles = sorted(df[col_modelo].dropna().unique().tolist()) if col_modelo in df.columns else []
modelos_seleccion = st.sidebar.multiselect("Filtrar Modelos / Segmentos (Dejar vacío para ver todas):", modelos_disponibles)

if modelos_seleccion:
    df = df[df[col_modelo].isin(modelos_seleccion)]

# Obtener categorías finales a mostrar
categorias_a_mostrar = sorted(df[col_cat].dropna().unique().tolist()) if not df.empty else []

if not categorias_a_mostrar:
    st.warning("No hay datos disponibles con los filtros seleccionados.")
    st.stop()

# Pestañas superiores para las categorías activas
pestanas = st.tabs(categorias_a_mostrar)

# Diccionario de colores y símbolos personalizados
color_map = {
    "Mystic": "#00FFFF",
    "Gtronic": "#2ca02c",
    "Sj Electronic": "#d62728",
    "Aiwa": "#000000",
    "Sam": "#e377c2",
    "Gplus": "#d2b48c",
    "Omega Electronis": "green",
    "TCL": "red"
}

symbol_map = {
    "Omega Electronis": "square-open",
    "TCL": "cross",
    "Mystic": "circle",
    "Gtronic": "circle",
    "Sj Electronic": "circle",
    "Aiwa": "circle",
    "Sam": "circle",
    "Gplus": "circle"
}

col_precio = "Floor share Venezuela - precio"

# 3. Generación de gráficos interactivos con Plotly por categoría
for i, cat in enumerate(categorias_a_mostrar):
    with pestanas[i]:
        st.subheader(f"Categoría: {cat}")
        df_cat = df[df[col_cat] == cat]
        
        if df_cat.empty:
            st.info("No hay registros en esta categoría con los filtros actuales.")
            continue
            
        df_cat_counts = df_cat.groupby([col_cat, col_marca]).size().reset_index(name='Cantidad_Categoria')
        df_cat_plot = df_cat.merge(df_cat_counts, on=[col_cat, col_marca], how='left')
        
        df_cat_total_marca = df_cat[col_marca].value_counts().reset_index()
        df_cat_total_marca.columns = [col_marca, 'Total_Marca']
        df_cat_plot = df_cat_plot.merge(df_cat_total_marca, on=col_marca, how='left')
        
        df_cat_plot['Marca Conteo'] = df_cat_plot[col_marca] + ' (Total: ' + df_cat_plot['Total_Marca'].astype(str) + ')'
        
        temp_color_map = {marca + ' (Total: ' + str(count) + ')': color_map.get(marca, 'gray') 
                          for marca, count in zip(df_cat_total_marca[col_marca], df_cat_total_marca['Total_Marca'])}
        temp_symbol_map = {marca + ' (Total: ' + str(count) + ')': symbol_map.get(marca, 'circle') 
                           for marca, count in zip(df_cat_total_marca[col_marca], df_cat_total_marca['Total_Marca'])}
        
        if col_modelo in df_cat_plot.columns and col_precio in df_cat_plot.columns:
            fig = px.scatter(
                df_cat_plot,
                x=col_precio,
                y=col_modelo,
                color='Marca Conteo',
                symbol='Marca Conteo',
                color_discrete_map=temp_color_map,
                symbol_map=temp_symbol_map,
                hover_data={
                    col_precio: True,
                    col_modelo: True,
                    col_marca: True,
                    "Cantidad_Categoria": True,
                    "Cadena": True if "Cadena" in df_cat_plot.columns else False,
                    col_empleado: True if col_empleado and col_empleado in df_cat_plot.columns else False
                },
                height=max(500, df_cat_plot[col_modelo].nunique() * 30),
                category_orders={'Marca Conteo': sorted([m + ' (Total: ' + str(c) + ')' for m, c in zip(df_cat_total_marca[col_marca], df_cat_total_marca['Total_Marca'])])}
            )
            
            fig.update_traces(marker=dict(size=12, line=dict(width=1, color='black')))
            fig.update_layout(
                title=f"Dispersión de Precios por Modelo y Marca - {cat}",
                xaxis_title="Precio PVP ($)",
                yaxis_title="Modelo / Segmento",
                legend_title="Marca (Total Registros)",
                hovermode="closest"
            )
            
            st.plotly_chart(fig, use_container_width=True)
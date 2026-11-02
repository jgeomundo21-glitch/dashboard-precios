import os
import pandas as pd
import plotly.express as px
import streamlit as st

# ---------------------------------------------------------
# 1. Configuración de la página
# ---------------------------------------------------------
st.set_page_config(
    page_title="Intelligence Dashboard: Pricing Strategy",
    page_icon="📊",
    layout="wide",
)

# Paleta Corporativa de Azules
CUSTOM_BLUE_SCALE = [
    "#1b3b6f",  # Azul marino profundo dominante (Mystic)
    "#2b5082",  # Azul corporativo medio-oscuro
    "#3f6c9d",  # Azul intermedio
    "#598ab5",  # Azul acero medio
    "#7aa7cb",  # Celeste acero claro
    "#9ec4de",  # Celeste suave
    "#b8d5e8",  # Celeste muy claro
    "#e2edf5",  # Azul pastel casi blanco
]

# ---------------------------------------------------------
# 2. Carga de datos segura
# ---------------------------------------------------------
@st.cache_data
def load_data():
    file_name = "Floorshare (Cantidades en piso y precio) 30 de Septiembre 2026.xlsx"
    if not os.path.exists(file_name):
        return None
    
    df = pd.read_excel(file_name, sheet_name="report")
    
    df["Floor share Venezuela - precio"] = pd.to_numeric(df["Floor share Venezuela - precio"], errors="coerce")
    df["Floor share Venezuela - Cantidad"] = pd.to_numeric(df["Floor share Venezuela - Cantidad"], errors="coerce").fillna(0)
    
    df["Valor_Total_USD"] = (
        df["Floor share Venezuela - Cantidad"] * df["Floor share Venezuela - precio"]
    )
    return df

df = load_data()

if df is None:
    st.error(
        "No se encontró el archivo 'Floorshare (Cantidades en piso y precio) 30 de Septiembre 2026.xlsx' en el directorio."
    )
    st.stop()

# ---------------------------------------------------------
# Encabezado con Logo Corporativo Mystic (Mystic.jpg)
# ---------------------------------------------------------
col_logo, col_title = st.columns([1, 5])

with col_logo:
    if os.path.exists("Mystic.jpg"):
        st.image("Mystic.jpg", width=140)
    else:
        st.warning("No se encontró la imagen Mystic.jpg")

with col_title:
    st.title("Intelligence Dashboard: Pricing Strategy")
    st.markdown(
        "**Análisis de Posicionamiento de Precios | Auditoría de ASP y Competencia por Categoría y Segmento**"
    )

st.markdown("---")

# ---------------------------------------------------------
# 3. Sidebar: Filtros Globales y de Producto
# ---------------------------------------------------------
st.sidebar.header("Filtros Globales")
st.sidebar.markdown("---")

regional_options = ["Todos"] + sorted(df["Regional"].dropna().unique().tolist())
selected_regional = st.sidebar.selectbox("Seleccione Regional", options=regional_options)

cadena_options = ["Todos"] + sorted(df["Cadena"].dropna().unique().tolist())
selected_cadena = st.sidebar.selectbox("Seleccione Red / Cadena", options=cadena_options)

# Filtrado preliminar paso a paso para encadenar las opciones lógicamente
df_temp = df.copy()
if selected_regional != "Todos":
    df_temp = df_temp[df_temp["Regional"] == selected_regional]
if selected_cadena != "Todos":
    df_temp = df_temp[df_temp["Cadena"] == selected_cadena]

st.sidebar.markdown("---")
st.sidebar.header("Filtros de Producto")
st.sidebar.markdown("---")

cats_disponibles = ["Todas"] + sorted(df_temp["Floor share Venezuela - Categoria"].dropna().unique().tolist())
cat_elegida = st.sidebar.selectbox("Filtrar Categoría:", options=cats_disponibles, key="pos_cat_filter")

if cat_elegida != "Todas":
    df_temp = df_temp[df_temp["Floor share Venezuela - Categoria"] == cat_elegida]

marcas_disponibles = ["Todas"] + sorted(df_temp["Floor share Venezuela - Marca"].dropna().unique().tolist())
marca_elegida = st.sidebar.selectbox("Filtrar Marca:", options=marcas_disponibles, key="pos_marca_filter")

if marca_elegida != "Todas":
    df_temp = df_temp[df_temp["Floor share Venezuela - Marca"] == marca_elegida]

# ---------------------------------------------------------
# 4. Cuerpo Principal: Selector de Segmento / Modelo Amplio
# ---------------------------------------------------------
st.markdown("##### Búsqueda y Filtrado de Segmento / Modelo")
segmentos_disponibles = ["Todos"] + sorted(df_temp["Floor share Venezuela - Segmento/Modelo"].dropna().unique().tolist())
segmento_elegido = st.selectbox("", options=segmentos_disponibles, key="pos_seg_filter", label_visibility="collapsed")

st.markdown("---")

# ---------------------------------------------------------
# 5. Filtrado Final de Datos para el Reporte
# ---------------------------------------------------------
df_filtered = df.copy()

if selected_regional != "Todos":
    df_filtered = df_filtered[df_filtered["Regional"] == selected_regional]
if selected_cadena != "Todos":
    df_filtered = df_filtered[df_filtered["Cadena"] == selected_cadena]
if cat_elegida != "Todas":
    df_filtered = df_filtered[df_filtered["Floor share Venezuela - Categoria"] == cat_elegida]
if marca_elegida != "Todas":
    df_filtered = df_filtered[df_filtered["Floor share Venezuela - Marca"] == marca_elegida]
if segmento_elegido != "Todos":
    df_filtered = df_filtered[df_filtered["Floor share Venezuela - Segmento/Modelo"] == segmento_elegido]

# ---------------------------------------------------------
# 6. Visualización: Mapa de Posicionamiento y KPIs
# ---------------------------------------------------------
if not df_filtered.empty and df_filtered["Floor share Venezuela - precio"].notna().any():
    
    pos_summary = (
        df_filtered.groupby("Floor share Venezuela - Marca")["Floor share Venezuela - precio"]
        .mean()
        .reset_index()
    )

    pos_summary.rename(
        columns={
            "Floor share Venezuela - Marca": "Marca",
            "Floor share Venezuela - precio": "Precio_Promedio",
        },
        inplace=True,
    )

    pos_summary = pos_summary.sort_values(by="Precio_Promedio", ascending=True)
    pos_summary["Precio_Texto"] = pos_summary["Precio_Promedio"].apply(lambda x: f"${x:,.2f}")

    asp_general = df_filtered["Floor share Venezuela - precio"].mean()
    marca_min = pos_summary.iloc[0]
    marca_max = pos_summary.iloc[-1]

    kpi1, kpi2, kpi3 = st.columns(3)
    kpi1.metric("ASP Promedio Sector", f"${asp_general:,.2f}")
    kpi2.metric("Entrada de Precio (Menor ASP)", f"{marca_min['Marca']}", f"${marca_min['Precio_Promedio']:,.2f}")
    kpi3.metric("Techo de Precio (Mayor ASP)", f"{marca_max['Marca']}", f"${marca_max['Precio_Promedio']:,.2f}")

    st.markdown("### Posicionamiento de Precio Promedio (ASP) por Marca")

    fig_pos_marca = px.scatter(
        pos_summary,
        x="Precio_Promedio",
        y="Marca",
        color="Marca",
        text="Precio_Texto",
        hover_data={"Marca": True, "Precio_Promedio": ":$.2f", "Precio_Texto": False},
        color_discrete_sequence=CUSTOM_BLUE_SCALE,
        height=max(450, len(pos_summary) * 35),
    )

    fig_pos_marca.update_traces(
        marker=dict(size=14, line=dict(width=1, color="DarkSlateGrey")),
        textposition="middle right",
    )

    fig_pos_marca.update_layout(
        xaxis_title="Precio Promedio (USD - ASP)",
        yaxis_title="",
        showlegend=False,
        xaxis=dict(tickprefix="$", showgrid=True, gridcolor="#EAEAEA"),
        yaxis=dict(categoryorder="total ascending", showgrid=True, gridcolor="#F5F5F5"),
        plot_bgcolor="white",
        margin=dict(l=20, r=80, t=30, b=40),
    )

    st.plotly_chart(fig_pos_marca, use_container_width=True)

else:
    st.info("No hay registros de precios suficientes para la combinación de filtros seleccionados.")

st.markdown("---")

# ---------------------------------------------------------
# 7. Botón de Descarga
# ---------------------------------------------------------
st.markdown("##### Exportar Datos Filtrados")
csv_export = df_filtered.to_csv(index=False).encode("utf-8")

st.download_button(
    label="Descargar Reporte de Precios (CSV)",
    data=csv_export,
    file_name="pricing_strategy_report.csv",
    mime="text/csv",
)
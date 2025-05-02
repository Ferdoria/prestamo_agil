import streamlit as st
import pandas as pd
import re
import requests
import plotly.express as px
from io import StringIO

# Configuración de la página
st.set_page_config(page_title="Dashboard de Préstamos", layout="wide", page_icon="📊")
st.title("📈 Dashboard de Ofertas de Préstamos")

# Estilo CSS personalizado
st.markdown("""
<style>
    .header-style { 
        font-size: 18px; 
        font-weight: bold; 
        margin-bottom: 10px;
        color: #2c3e50;
    }
    .metric-card { 
        background-color: #f8f9fa; 
        padding: 20px; 
        border-radius: 10px; 
        margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        border-left: 4px solid #3498db;
    }
    .metric-value {
        font-size: 28px;
        font-weight: bold;
        color: #2c3e50;
        margin: 10px 0;
    }
    .metric-label {
        font-size: 14px;
        color: #7f8c8d;
    }
    .plot-container { 
        margin-top: 20px; 
        margin-bottom: 30px;
        background-color: white;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .dataframe th {
        background-color: #3498db !important;
        color: white !important;
    }
    .stDataFrame {
        margin-bottom: 30px;
    }
</style>
""", unsafe_allow_html=True)

# URL por defecto
DEFAULT_URL = ""

# Función para procesar el contenido
def procesar_contenido(content):
    try:
        columnas = [
            'Sccta', 'GxInfCuenta', 'Importe1', 'Plazo1', 'Tasa1', 'ImpMinimo1', 'ImpCuota1', 'ImpComision1',
            'Importe2', 'Plazo2', 'Tasa2', 'ImpMinimo2', 'ImpCuota2', 'ImpComision2',
            'Importe3', 'Plazo3', 'Tasa3', 'ImpMinimo3', 'ImpCuota3', 'ImpComision3',
            'Importe4', 'Plazo4', 'Tasa4', 'ImpMinimo4', 'ImpCuota4', 'ImpComision4', 'Cotasa'
        ]
        
        patron = r'Sccta;(\d+);&GxInfCuenta;\s*(\d+);&Importe1;\s*(\d+);&Plazo1;\s*(\d+);&Tasa1;\s*(\d+);&ImpMinimo1;\s*(\d+);&ImpCuota1;\s*(\d+);&ImpComision1;\s*(\d+);&Importe2;\s*(\d+);&Plazo2;\s*(\d+);&Tasa2;\s*(\d+);&ImpMinimo2;\s*(\d+);&ImpCuota2;\s*(\d+);&ImpComision2;\s*(\d+);&Importe3;\s*(\d+);&Plazo2;\s*(\d+);&Tasa3;\s*(\d+);&ImpMinimo3;\s*(\d+);&ImpCuota3;\s*(\d+);&ImpComision3;\s*(\d+);&Importe4;\s*(\d+);&Plazo4;\s*(\d+);&Tasa4;\s*(\d+);&ImpMinimo4;\s*(\d+);&ImpCuota4;\s*(\d+);&ImpComision4;\s*(\d+);&Cotasa;\s*(\d+)'
        
        coincidencias = re.findall(patron, content)
        
        if not coincidencias:
            st.error("No se encontraron datos que coincidan con el patrón esperado.")
            return None
        
        df = pd.DataFrame(coincidencias, columns=columnas)
        
        # Convertir columnas numéricas
        columnas_numericas = columnas[2:]
        df[columnas_numericas] = df[columnas_numericas].apply(pd.to_numeric)
        
        # Calcular si tiene ofertas
        df['Tiene_Ofertas'] = (df['Importe1'] > 0) | (df['Importe2'] > 0) | (df['Importe3'] > 0) | (df['Importe4'] > 0)
        
        return df
    
    except Exception as e:
        st.error(f"Error al procesar el archivo: {str(e)}")
        return None

# Sidebar con opciones de carga
with st.sidebar:
    st.header("⚙️ Opciones de Carga")
    
    metodo_carga = st.radio(
        "Seleccione el método de carga:",
        ("Subir archivo local", "Cargar desde URL"),
        index=0
    )
    
    df = None
    
    if metodo_carga == "Subir archivo local":
        uploaded_file = st.file_uploader(
            "Seleccione el archivo BASE_PRESTAMO_DEMO.txt",
            type=["txt"]
        )
        
        if uploaded_file is not None:
            with st.spinner("Procesando archivo local..."):
                content = uploaded_file.read().decode('utf-8')
                df = procesar_contenido(content)
    
    else:  # Cargar desde URL
        url_archivo = st.text_input(
            "Ingrese la URL del archivo:",
            value=DEFAULT_URL,
            placeholder="https://ejemplo.com/ruta/BASE_PRESTAMO_DEMO.txt"
        )
        
        if st.button("Cargar desde URL") or url_archivo:
            if url_archivo:
                with st.spinner("Descargando y procesando archivo..."):
                    try:
                        response = requests.get(url_archivo)
                        response.raise_for_status()
                        content = response.text
                        df = procesar_contenido(content)
                    except requests.exceptions.RequestException as e:
                        st.error(f"Error al descargar el archivo: {str(e)}")
                    except Exception as e:
                        st.error(f"Error inesperado: {str(e)}")
            else:
                st.warning("Por favor ingrese una URL válida")

# Mostrar resultados si hay datos
if df is not None:
    st.success(f"✅ Datos cargados correctamente. Registros encontrados: {len(df):,}")
    
    # Métricas resumen
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="metric-card">'
                   f'<div class="metric-label">Cuentas con ofertas</div>'
                   f'<div class="metric-value">{df["Tiene_Ofertas"].sum():,}</div>'
                   f'<div class="metric-label">{df["Tiene_Ofertas"].mean()*100:.1f}% del total</div>'
                   '</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="metric-card">'
                   f'<div class="metric-label">Cuentas sin ofertas</div>'
                   f'<div class="metric-value">{(~df["Tiene_Ofertas"]).sum():,}</div>'
                   f'<div class="metric-label">{(1-df["Tiene_Ofertas"].mean())*100:.1f}% del total</div>'
                   '</div>', unsafe_allow_html=True)
    
    # Pestañas para organizar la visualización
    tab1, tab2 = st.tabs(["📋 Datos y Estadísticas", "📊 Análisis Visual"])
    
    with tab1:
        st.subheader("Resumen General de Importes")
        
        # Preparar datos de importes generales
        importes = pd.concat([
            df[['Importe1']].rename(columns={'Importe1': 'Importe'}),
            df[['Importe2']].rename(columns={'Importe2': 'Importe'}),
            df[['Importe3']].rename(columns={'Importe3': 'Importe'}),
            df[['Importe4']].rename(columns={'Importe4': 'Importe'})
        ]).query('Importe > 0')
        
        # Calcular estadísticas
        count = len(importes)
        min_val = importes['Importe'].min()
        mean_val = importes['Importe'].mean()
        max_val = importes['Importe'].max()
        
        # Crear DataFrame de resumen
        resumen_general = pd.DataFrame({
            'Métrica': ['Cantidad', 'Mínimo', 'Promedio', 'Máximo'],
            'Valor': [
                f"{count:,}", 
                f"PYG {min_val:,.0f}", 
                f"PYG {mean_val:,.0f}", 
                f"PYG {max_val:,.0f}"
            ]
        })
        
        # Mostrar tabla de estadísticas generales
        st.dataframe(
            resumen_general,
            column_config={
                "Métrica": st.column_config.TextColumn("Métrica", width="medium"),
                "Valor": st.column_config.TextColumn("Valor", width="large")
            },
            hide_index=True,
            use_container_width=True
        )
        
        st.markdown("---")
        st.subheader("Resumen de Importes por Plazo")
        
        # Crear DataFrame con importes y plazos
        datos_plazos = pd.DataFrame()
        for i in range(1, 5):
            temp_df = df[['Importe'+str(i), 'Plazo'+str(i)]].rename(
                columns={'Importe'+str(i): 'Importe', 'Plazo'+str(i): 'Plazo'})
            datos_plazos = pd.concat([datos_plazos, temp_df])
        
        # Filtrar solo ofertas válidas
        datos_plazos = datos_plazos.query('Importe > 0 and Plazo > 0')
        
        # Agrupar por plazo y calcular estadísticas
        stats_plazos = datos_plazos.groupby('Plazo').agg(
            Cantidad=('Importe', 'count'),
            Mínimo=('Importe', 'min'),
            Promedio=('Importe', 'mean'),
            Máximo=('Importe', 'max')
        ).reset_index()
        
        # Formatear valores
        stats_plazos['Plazo'] = stats_plazos['Plazo'].astype(int)
        stats_plazos['Mínimo'] = stats_plazos['Mínimo'].apply(lambda x: f"PYG {x:,.0f}")
        stats_plazos['Promedio'] = stats_plazos['Promedio'].apply(lambda x: f"PYG {x:,.0f}")
        stats_plazos['Máximo'] = stats_plazos['Máximo'].apply(lambda x: f"PYG {x:,.0f}")
        
        # Mostrar tabla de estadísticas por plazo
        st.dataframe(
            stats_plazos,
            column_config={
                "Plazo": st.column_config.NumberColumn("Plazo (meses)", format="%d"),
                "Cantidad": st.column_config.NumberColumn("Cantidad", format="%d"),
                "Mínimo": st.column_config.TextColumn("Mínimo"),
                "Promedio": st.column_config.TextColumn("Promedio"),
                "Máximo": st.column_config.TextColumn("Máximo")
            },
            hide_index=True,
            use_container_width=True
        )
        
        st.subheader("Datos completos")
        st.dataframe(df)
    
    with tab2:
        st.markdown('<div class="plot-container">', unsafe_allow_html=True)
        
        # Gráfico 1: Cuentas con/sin ofertas
        fig1 = px.pie(
            df, 
            names=df['Tiene_Ofertas'].map({True: 'Con Ofertas', False: 'Sin Ofertas'}),
            title='<b>Distribución de Cuentas con/sin Ofertas</b>',
            color=df['Tiene_Ofertas'].map({True: 'Con Ofertas', False: 'Sin Ofertas'}),
            color_discrete_map={'Con Ofertas': '#3498db', 'Sin Ofertas': '#e74c3c'},
            hole=0.4,
            width=600,
            height=400
        )
        fig1.update_traces(
            textposition='inside', 
            textinfo='percent+label',
            textfont_size=14,
            marker=dict(line=dict(color='#ffffff', width=2))
        )
        fig1.update_layout(
            title_x=0.5,
            title_font_size=18,
            showlegend=False)
        st.plotly_chart(fig1, use_container_width=True)
        
        # Gráfico 2: Distribución de plazos mejorado
        plazos = pd.concat([
            df[['Plazo1']].rename(columns={'Plazo1': 'Plazo'}),
            df[['Plazo2']].rename(columns={'Plazo2': 'Plazo'}),
            df[['Plazo3']].rename(columns={'Plazo3': 'Plazo'}),
            df[['Plazo4']].rename(columns={'Plazo4': 'Plazo'})
        ]).query('Plazo > 0')
        
        # Agrupar plazos similares
        plazos['Plazo_Agrupado'] = pd.cut(
            plazos['Plazo'],
            bins=[0, 3, 6, 12, 24, 36, 48, 100],
            labels=['1-3', '4-6', '7-12', '13-24', '25-36', '37-48', '49+']
        )
        
        plazo_counts = plazos['Plazo_Agrupado'].value_counts().sort_index().reset_index()
        plazo_counts.columns = ['Plazo (meses)', 'Cantidad de Ofertas']
        
        fig2 = px.bar(
            plazo_counts,
            x='Plazo (meses)',
            y='Cantidad de Ofertas',
            title='<b>Distribución de Plazos en Ofertas Activas</b>',
            text='Cantidad de Ofertas',
            color='Cantidad de Ofertas',
            color_continuous_scale='Blues'
        )
        fig2.update_layout(
            xaxis_title="Rango de Plazo (meses)",
            yaxis_title="Cantidad de Ofertas",
            title_x=0.5,
            title_font_size=18,
            coloraxis_showscale=False
        )
        fig2.update_traces(
            textposition='outside',
            textfont_size=12,
            marker_line_color='white',
            marker_line_width=1.5
        )
        st.plotly_chart(fig2, use_container_width=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Exportar datos
    with st.sidebar:
        st.download_button(
            label="📥 Descargar datos como CSV",
            data=df.to_csv(index=False).encode('utf-8'),
            file_name="datos_prestamos.csv",
            mime="text/csv"
        )

elif metodo_carga == "Cargar desde URL" and url_archivo:
    st.info("Haga clic en 'Cargar desde URL' para obtener los datos")
else:
    st.info("Seleccione un método de carga y proporcione los datos para comenzar")

# Notas adicionales
st.sidebar.markdown("""
**📌 Notas:**
- Cada cuenta puede tener hasta 4 opciones de préstamo
- Los importes se muestran en Guaraníes (PYG) excepto la cantidad total
- Filtre los datos para análisis específicos
""")
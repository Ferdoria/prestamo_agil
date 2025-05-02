import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

# Configuración inicial
st.set_page_config(page_title="Dashboard de Préstamos", layout="wide", page_icon="📊")
pd.set_option("styler.render.max_elements", 2**31-1)
hoy = datetime(2025, 4, 8).date()  # Fecha como objeto date

# Estilos CSS mejorados
st.markdown("""
<style>
    .metric-card {background-color: #f8f9fa; padding: 20px; border-radius: 10px; margin-bottom: 20px; 
                 box-shadow: 0 4px 6px rgba(0,0,0,0.1); border-left: 4px solid #3498db;}
    .metric-value {font-size: 28px; font-weight: bold; color: #2c3e50; margin: 10px 0;}
    .metric-label {font-size: 14px; color: #7f8c8d;}
    .sobreutilizada {font-weight: bold !important;}
    .dataframe th {background-color: #3498db !important; color: white !important;}
</style>
""", unsafe_allow_html=True)

def procesar_archivo(uploaded_file):
    try:
        content = uploaded_file.read().decode('utf-8')
        lineas = [linea.strip() for linea in content.split('\n') if linea.strip()]
        
        if not lineas:
            st.error("Archivo vacío")
            return None
           
        encabezado = [col.strip().replace('&', '') for col in lineas[0].split(';') if col.strip()]
        datos = [linea.split(';')[:len(encabezado)] for linea in lineas[1:] if linea.strip()]
        
        df = pd.DataFrame(datos, columns=encabezado)
    
        # Conversión de tipos
        numeric_cols = ['Linea_Concedida', 'Linea_Utilizada', 'Estado_Linea'] + \
                      [f'{pre}{i}' for pre in ['Importe','Plazo','Tasa','ImpMinimo','ImpCuota','ImpComision'] 
                       for i in range(1,5)] + ['CoTasa']
        
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        # Conversión de fechas (eliminada la referencia a Vencimiento_Linea)
        for col in ['AltaValor_Linea', 'AltaContable_Linea']:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], format='%d/%m/%Y', errors='coerce')
        
        df['Tiene_Ofertas'] = False
        for i in range(1, 5):
            if f'Importe{i}' in df.columns:
                df['Tiene_Ofertas'] = df['Tiene_Ofertas'] | (df[f'Importe{i}'] > 0)

        return df
    
    except Exception as e:
        st.error(f"Error al procesar: {str(e)}")
        return None

def main():
    st.title("📈 Dashboard de Ofertas de Préstamos")
    
    uploaded_file = st.file_uploader("Sube tu archivo BASE_PRESTAMO_AGIL_DEMO.txt", type=["txt"])
    df = procesar_archivo(uploaded_file) if uploaded_file else None
    
    if df is None:
        return st.info("Sube un archivo para comenzar")
    
    st.success(f"✅ Datos cargados: {len(df):,} registros")
    
    # Métricas clave (eliminada la métrica de vencidas)
    cols = st.columns(3)  # Cambiado a 3 columnas
    
    con_ofertas = df['Tiene_Ofertas'].sum()
    linea_util_mayor = (df['Linea_Utilizada'] > df['Linea_Concedida']).sum()
    bloqueadas = (df['Estado_Linea'] != 0).sum()
    
    metricas = [
        ('Cuentas con ofertas', con_ofertas, con_ofertas/len(df)),
        ('Línea usada > concedida', linea_util_mayor, linea_util_mayor/len(df)),
        ('Líneas bloqueadas', bloqueadas, bloqueadas/len(df))
    ]
    
    for col, (title, value, pct) in zip(cols, metricas):
        with col:
            st.markdown(f'''<div class="metric-card">
                          <div class="metric-label">{title}</div>
                          <div class="metric-value">{value:,}</div>
                          <div class="metric-label">{pct*100:.1f}%</div></div>''', 
                       unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["📋 Datos", "📊 Gráficos"])
    
    with tab1:
        col1, col2 = st.columns(2)

        with col1:        
            st.subheader("Resumen General de Importes (PYG)")
            if any(f'Importe{i}' in df.columns for i in range(1,5)):
                importes = pd.concat([df[[f'Importe{i}']].rename(columns={f'Importe{i}':'Importe'}) 
                                    for i in range(1,5) if f'Importe{i}' in df.columns]).query('Importe > 0')
                
                if not importes.empty:
                    stats = importes.describe().loc[['count','min','mean','max']].reset_index()
                    stats.columns = ['Métrica', 'Valor']
                    stats['Valor'] = stats['Valor'].apply(lambda x: f"PYG {x:,.0f}" if x > 0 else "PYG 0")
                    
                    st.dataframe(stats, hide_index=True, use_container_width=True,
                                column_config={
                                    "Métrica": st.column_config.TextColumn(width="medium"),
                                    "Valor": st.column_config.TextColumn(width="large")
                                })
                else:
                    st.warning("No hay importes válidos para mostrar")
        
        with col2:  
            st.subheader("Resumen de Importes por Plazo (PYG)")
            if any(f'Plazo{i}' in df.columns and f'Importe{i}' in df.columns for i in range(1,5)):
                datos_plazos = pd.concat([
                    df[[f'Importe{i}', f'Plazo{i}']].rename(columns={
                        f'Importe{i}': 'Importe', 
                        f'Plazo{i}': 'Plazo'
                    }) for i in range(1,5) 
                    if f'Importe{i}' in df.columns and f'Plazo{i}' in df.columns
                ]).query('Importe > 0 and Plazo > 0')
                
                if not datos_plazos.empty:
                    stats_plazos = datos_plazos.groupby('Plazo').agg(
                        Cantidad=('Importe', 'count'),
                        Mínimo=('Importe', 'min'),
                        Promedio=('Importe', 'mean'),
                        Máximo=('Importe', 'max')
                    ).reset_index()
                    
                    stats_plazos['Plazo'] = stats_plazos['Plazo'].astype(int)
                    for col in ['Mínimo', 'Promedio', 'Máximo']:
                        stats_plazos[col] = stats_plazos[col].apply(lambda x: f"PYG {x:,.0f}")
                    
                    st.dataframe(
                        stats_plazos,
                        column_config={
                            "Plazo": st.column_config.NumberColumn("Plazo (meses)", format="%d"),
                            "Cantidad": st.column_config.NumberColumn("Cantidad", format="%d"),
                            "Mínimo": st.column_config.TextColumn("Mínimo (PYG)"),
                            "Promedio": st.column_config.TextColumn("Promedio (PYG)"),
                            "Máximo": st.column_config.TextColumn("Máximo (PYG)")
                        },
                        hide_index=True,
                        use_container_width=True
                    )
                else:
                    st.warning("No hay datos de importes por plazo para mostrar")
        
        st.subheader("Resumen de Cuentas con y sin Ofertas por Producto menor a 1000")
        if 'Producto_Concedido' in df.columns:
            df['Producto_Concedido'] = pd.to_numeric(df['Producto_Concedido'], errors='coerce')
            resumen_ofertas = df[df['Producto_Concedido'].notna() & (df['Producto_Concedido'] < 1000)].groupby('Producto_Concedido').agg(
                Total_Con_Ofertas=('Tiene_Ofertas', lambda x: (x == True).sum()),
                Total_Sin_Ofertas=('Tiene_Ofertas', lambda x: (x == False).sum())
            ).reset_index()

            resumen_ofertas_transpuesta = resumen_ofertas.set_index('Producto_Concedido').transpose()

            st.dataframe(
                resumen_ofertas_transpuesta,
                use_container_width=True
            )
        else:
            st.warning("No hay datos de productos concedidos para mostrar")

        st.subheader("Resumen de Cuentas con y sin Ofertas por Producto mayor a 1000")
        if 'Producto_Concedido' in df.columns:
            resumen_ofertas = df[df['Producto_Concedido'].notna() & (df['Producto_Concedido'] >= 1000)].groupby('Producto_Concedido').agg(
                Total_Con_Ofertas=('Tiene_Ofertas', lambda x: (x == True).sum()),
                Total_Sin_Ofertas=('Tiene_Ofertas', lambda x: (x == False).sum())
            ).reset_index()

            resumen_ofertas_transpuesta = resumen_ofertas.set_index('Producto_Concedido').transpose()

            st.dataframe(
                resumen_ofertas_transpuesta,
                use_container_width=True
            )
        else:
            st.warning("No hay datos de productos concedidos para mostrar")            
        
        # Datos Completos (simplificado sin referencia a vencimientos)
        st.subheader("Datos Completos")
        
        subset = pd.DataFrame()
        if st.checkbox("Mostrar datos completos", value=False):
            batch_size = st.slider("Registros por página", 10, 100, 50)
            page = st.number_input("Página", 1, max(1, (len(df)//batch_size)+1), 1)
            
            subset = df.iloc[(page-1)*batch_size : page*batch_size].copy()
            
            def highlight_rows(row):
                styles = [''] * len(row)
                
                # Solo resaltar líneas sobreutilizadas
                if 'Linea_Utilizada' in subset.columns and 'Linea_Concedida' in subset.columns:
                    if row['Linea_Utilizada'] > row['Linea_Concedida']:
                        styles = ['background-color: #ccc1a4'] * len(row)
                
                return styles
            
            try:
                styled_df = subset.style.apply(highlight_rows, axis=1)
                st.dataframe(
                    styled_df,
                    height=600,
                    use_container_width=True
                )
            except Exception as e:
                st.warning(f"No se pudieron aplicar estilos: {str(e)}")
                st.dataframe(subset, height=600, use_container_width=True)
        else:
            st.info("Selecciona 'Mostrar datos completos' para visualizar la información")
    
    with tab2:
        if 'Tiene_Ofertas' in df.columns:
            fig = px.pie(df, names=df['Tiene_Ofertas'].map({True:'Con Ofertas', False:'Sin Ofertas'}),
                        title='Distribución de Ofertas', hole=0.4,
                        color_discrete_map={'Con Ofertas':'#3498db', 'Sin Ofertas':'#e74c3c'})
            fig.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    main()
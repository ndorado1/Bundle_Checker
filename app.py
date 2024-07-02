import os
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
from dotenv import load_dotenv

# Cargar variables de entorno desde el archivo .env
load_dotenv()

# Configurar la clave secreta (si es necesaria)
SECRET_KEY = os.getenv('SECRET_KEY', 'default_secret_key')

# Título de la aplicación
st.title('License Summary and RA Action ID Analysis')

# Subida de archivo
uploaded_file = st.file_uploader("Choose an Excel or CSV file", type=["xlsx", "csv"])

if uploaded_file is not None:
    # Determinar el tipo de archivo y leerlo
    file_extension = uploaded_file.name.split('.')[-1]
    if file_extension == 'xlsx':
        df = pd.read_excel(uploaded_file, sheet_name='Export')
    else:
        df = pd.read_csv(uploaded_file)


    # Filtrar por país Colombia
    if 'Country' in df.columns:
        df_colombia = df[df['Country'] == 'COLOMBIA']
    else:
        st.error("La columna 'Country' no existe en el DataFrame.")
        df_colombia = pd.DataFrame()


    # Filtrar por estados de acción específicos
    if 'RA Action Status' in df_colombia.columns:
        filtered_df = df_colombia[df_colombia['RA Action Status'].isin(['Execution', 'Planning'])]
    else:
        st.error("La columna 'RA Action Status' no existe en el DataFrame.")
        filtered_df = pd.DataFrame()

    # Crear un resumen por licencia y estado para mostrar en el summary view
    if not filtered_df.empty:
        summary = filtered_df.groupby('License Number').size().reset_index(name='Count of RA Action ID')
    else:
        st.error("No hay datos después de aplicar los filtros.")
        summary = pd.DataFrame()
        

    # Comprobar si 'summary' está vacío
    if not summary.empty and summary['Count of RA Action ID'].dtype in ['int64', 'float64']:
        # Mostrar el resumen en la aplicación
        st.subheader('Resumen de Licencias')
        st.dataframe(summary, width=1000)

        # Generar gráfico de barras apiladas
        fig, ax = plt.subplots(figsize=(15, len(summary) * 0.5))  # Ajustar tamaño del gráfico
        summary.plot(kind='barh', x='License Number', y='Count of RA Action ID', ax=ax)
        plt.xlabel('Count of RA Action ID')
        plt.title('RA Action ID Count per License Number')
        plt.yticks(fontsize=10)  # Ajustar el tamaño de la fuente de las etiquetas del eje Y
        plt.xticks(fontsize=10)  # Ajustar el tamaño de la fuente de las etiquetas del eje X
        st.pyplot(fig)

        # Selección de licencia para detalles
        st.subheader('Details for a Specific License')
        license_number = st.selectbox('Select a License Number', summary['License Number'])

        if license_number:
            details = filtered_df[filtered_df['License Number'] == license_number].copy()
            # Convertir RA Action ID a string para evitar formateo incorrecto
            details['RA Action ID'] = details['RA Action ID'].astype(str)
            # Formatear Submission Due Date
            details['Submission Due Date'] = pd.to_datetime(details['Submission Due Date']).dt.date
            # Mostrar la tabla sin el índice
            st.dataframe(details[['RA Action ID', 'Source', 'RA Action Status', 'Submission Due Date','LOC Contact']].reset_index(drop=True),width=1500)
    else:
        st.write("No numeric data available to plot.")

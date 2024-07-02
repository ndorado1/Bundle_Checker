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
uploaded_file = st.file_uploader("Choose an Excel file", type="xlsx")

if uploaded_file is not None:
    # Leer el archivo Excel
    df = pd.read_excel(uploaded_file, sheet_name='Export')
    
    # Filtrar por país Colombia
    df_colombia = df[df['Country'] == 'Colombia']
    
    # Filtrar por estados de acción específicos
    filtered_df = df_colombia[df_colombia['RA Action Status'].isin(['Execution', 'Planning'])]
    
    # Crear un resumen por licencia y estado para mostrar en el summary view
    summary = filtered_df.groupby(['License Number', 'RA Action Status']).size().unstack(fill_value=0)
    
    # Comprobación de depuración: verificar si 'summary' contiene datos numéricos
    st.write("DataFrame 'summary':")
    st.write(summary)
    
    # Comprobar si 'summary' está vacío
    if not summary.empty and summary.select_dtypes(include=[float, int]).shape[1] > 0:
        # Mostrar el resumen en la aplicación
        st.subheader('Summary of Licenses')
        st.write(summary)
        
        # Generar gráfico de barras apiladas
        fig, ax = plt.subplots(figsize=(20, 8))
        summary.plot(kind='barh', stacked=True, ax=ax)
        plt.xlabel('Count of RA Action ID')
        plt.title('RA Action ID Count per License Number by Status')
        st.pyplot(fig)
        
        # Selección de licencia para detalles
        st.subheader('Details for a Specific License')
        license_number = st.selectbox('Select a License Number', summary.index)
        
        if license_number:
            details = filtered_df[filtered_df['License Number'] == license_number]
            st.write(details[['RA Action ID', 'Source', 'RA Action Status', 'Submission Due Date']])
    else:
        st.write("No numeric data available to plot.")

import os
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
from dotenv import load_dotenv
import openai
from datetime import datetime, timedelta


# Configurar la clave secreta (si es necesaria)
api_key = os.getenv('OPENAI_API_KEY')

# Título de la aplicación
st.markdown(
    """
    <style>
    .main {
        background-color: #f0f0f0;
    }
    .header {
        text-align: center;
        font-size: 36px;
        font-weight: bold;
        color: #333;
    }
    .subheader {
        font-size: 24px;
        color: #666;
    }
    .logo {
        display: block;
        margin-left: auto;
        margin-right: auto;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Insertar logotipo
#st.image("path_to_your_logo.png", use_column_width=True, caption="Your Company Logo")

# Título de la aplicación
st.markdown('<div class="header">RA NC Bundles Checker Tool</div>', unsafe_allow_html=True)

# Subida de archivo
uploaded_file = st.file_uploader("Cargue su Archivo de Excel para Analizar", type=["xlsx", "csv"])

if uploaded_file is not None:
    # Determinar el tipo de archivo y leerlo
    file_extension = uploaded_file.name.split('.')[-1]
    if file_extension == 'xlsx':
        df = pd.read_excel(uploaded_file, sheet_name='Export')
    else:
        df = pd.read_csv(uploaded_file)


    # Filtrar por país Colombia
  #  if 'Country' in df.columns:
  #      df_colombia = df[df['Country'] == 'COLOMBIA']
  #  else:
  #      st.error("La columna 'Country' no existe en el DataFrame.")
  #      df_colombia = pd.DataFrame()
    df_colombia=df


    # Filtrar por estados de acción específicos
    if 'RA Action Status' in df_colombia.columns:
        filtered_df = df_colombia[df_colombia['RA Action Status'].isin(['Execution', 'Planning'])]
    else:
        st.error("La columna 'RA Action Status' no existe en el DataFrame.")
        filtered_df = pd.DataFrame()
        
    # Asegurarse de que la columna 'Submission Due Date' está en formato de fecha
    filtered_df['Submission Due Date'] = pd.to_datetime(filtered_df['Submission Due Date']).dt.date

    # Filtrar acciones con fecha de vencimiento válida (no pasada)
    today = datetime.today().date()
    acciones_validas = filtered_df[filtered_df['Submission Due Date'] > today]

    # Agrupar por licencia y verificar si la diferencia entre las fechas es mayor a 3 meses
    def es_valido_para_bundle(grupo):
        fechas = sorted(grupo['Submission Due Date'])
        if (fechas[-1] - fechas[0]).days <= 90:  # 3 meses = 90 días
            return True
        return False

    acciones_agrupadas = acciones_validas.groupby('License Number').filter(es_valido_para_bundle)    

    # Crear un resumen por licencia y estado para mostrar en el summary view
    if not filtered_df.empty:
        summary = filtered_df.groupby(['License Number','Country']).size().reset_index(name='Count of RA Action ID')
    else:
        st.error("No hay datos después de aplicar los filtros.")
        summary = pd.DataFrame()
        

    # Comprobar si 'summary' está vacío
    if not summary.empty and summary['Count of RA Action ID'].dtype in ['int64', 'float64']:
        # Mostrar el resumen en la aplicación
        st.subheader('Resumen de Licencias')
        st.dataframe(summary,width=600,hide_index=True)        
            

        # Selección de licencia para detalles
        st.subheader('Detalles Especificos por Licencia')
        license_number = st.selectbox('Seleccione una Licencia', summary['License Number'])

        if license_number:
            details = filtered_df[filtered_df['License Number'] == license_number].copy()
            # Convertir RA Action ID a string para evitar formateo incorrecto
            details['RA Action ID'] = details['RA Action ID'].astype(str)
            # Formatear Submission Due Date
            details['Submission Due Date'] = pd.to_datetime(details['Submission Due Date']).dt.date
            # Mostrar la tabla sin el índice
            st.dataframe(details[['RA Action ID', 'Source', 'RA Action Status', 'Submission Due Date','LOC Contact']].style.hide(axis="index"),width=1500)
    else:
        st.write("No numeric data available to plot.")
        
# Función para construir el prompt desde el DataFrame 'details'
def construir_prompt_desde_detalles(acciones_agrupadas):
    prompt = "Analiza las siguientes licencias sanitarias con múltiples trámites asociados y sugiere cuáles tienenmayor oportunidad de unificar trámites (bundle). Las acciones con fechas de vencimiento pasadas no son válidas, y la diferencia entre las fechas de vencimiento no debe ser mayor a 3 meses. Solo se consideran acciones cuyos estados sean Planning o Execution\n\n"

    for _, row in acciones_agrupadas.iterrows():
        prompt += (
           f"Licencia {row['License Number']} tiene la acción {row['RA Action ID']} con estado '{row['RA Action Status']}' y fecha de vencimiento {row['Submission Due Date']}.\n"
        )

    prompt += "\n¿Cuáles de estas licencias tienen mayor oportunidad de unificación en un solo trámite (bundle) y por qué?"
    return prompt

st.write(prompt)

# Construir el prompt desde los detalles
prompt = construir_prompt_desde_detalles(acciones_agrupadas)

# Función para generar el diagnóstico con GPT4o-mini
# Configura tu clave API
openai.api_key = api_key

# Función para enviar el prompt y obtener la respuesta
def generar_diagnostico(prompt):
    response = openai.chat.completions.create(
        model="gpt-4o-mini",  # Usar el modelo correcto, puedes cambiar por "gpt-4o-mini" si aplica
        messages=[
            {"role": "system", "content": "Eres un asistente que analiza datos para identificar oportunidades de bundle."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=200,
        temperature=0.7
    )
    return response.choices[0].message.content


# Obtener el diagnóstico
diagnostico = generar_diagnostico(prompt)

# Mostrar el diagnóstico en la app de Streamlit
st.write(f"Diagnóstico generado por la IA:\n{diagnostico}")
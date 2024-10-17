import os
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
from dotenv import load_dotenv
import openai

# Cargar variables de entorno desde el archivo .env
load_dotenv()

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
def construir_prompt_desde_detalles(details):
    prompt = "Analiza las siguientes acciones regulatorias para la licencia y sugiere si hay oportunidad de unificar trámites (bundle):\n\n"

    for _, row in details.iterrows():
        prompt += (
            f"Acción {row['RA Action ID']} desde {row['Source']} tiene el estatus '{row['RA Action Status']}' y la fecha de vencimiento de presentación es {row['Submission Due Date']}. "
            f"El contacto es {row['LOC Contact']}.\n"
        )

    prompt += "\n¿Cuáles de estas acciones pueden ser unificadas en un solo trámite y por qué?"
    return prompt

# Construir el prompt desde los detalles
prompt = construir_prompt_desde_detalles(details)

# Función para generar el diagnóstico con GPT4o-mini
# Configura tu clave API
openai.api_key = api_key

# Función para enviar el prompt y obtener la respuesta
def generar_diagnostico(prompt):
    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",  # Usar el modelo correcto, puedes cambiar por "gpt-4o-mini" si aplica
        messages=[
            {"role": "system", "content": "Eres un asistente que analiza datos para identificar oportunidades de bundle."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=200,
        temperature=0.7
    )
    return response['choices'][0]['message']['content'].strip()


# Obtener el diagnóstico
diagnostico = generar_diagnostico(prompt)

# Mostrar el diagnóstico en la app de Streamlit
st.write(f"Diagnóstico generado por la IA:\n{diagnostico}")
import cohere
import os
import pandas as pd
import pymysql
import requests
import uvicorn

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel


# Cargo variables de entorno desde mi .env
load_dotenv()

# Configuro variables de entorno.
USERNAME = os.getenv("DB_USERNAME")
PASSWORD = os.getenv("DB_PASSWORD")
HOST = os.getenv("DB_HOST")
PORT = int(os.getenv("DB_PORT"))
COHERE_API_KEY = os.getenv("COHERE_API_KEY")

# Inicio FastAPI
app = FastAPI(title="KuH")

# Modelo de datos para la solicitud.
class ConsultaRequest(BaseModel):
    consulta: str

# Cargo el catálogo almacenado en local.
df = pd.read_csv('./data/kuh_ene26.csv')

# Convierto el catálogo en texto para el prompt.
catalogo = df.to_string()

# System prompt. 
system_prompt = f'''Eres un educado experto en telefonía móvil y trabajas para Falúa Móvil, te gusta conversar y das respuestas breves con la información esencial.

                    CATÁLOGO EXCLUSIVO DE VENTA: {catalogo}

                    REGLAS: 
                    1. Atiendes en español de España y en inglés británico.
                    2. Si no está en la lista, di: "No disponible actualmente, contacte con la tienda física para más información"
                    3. Si te preguntan por conectividad 5G, la respuesta es afirmativa si viene incluido en el nombre del modelo. Si no fuera así, propón al usuario buscar la ficha del producto en www.faluamovil.es
                    4. En tu respuesta inicial si no te indican ninguna característica, modelo o presupuesto disponible tú mismo preguntas por ello.
                    5. Más avanzada la conversación puedes hacer un máximo de tres propuestas.
                    6. Debes preguntar al usuario para afinar tu respuesta final.
                    7. En todo momento puedes sugerir otras opciones atendiendo a las características o fabricante que priorice el usuario.
                    8. No sugieras visitar la web www.faluamovil.es salvo extrema necesidad, recuerda que estás implementado en ella.''' 

# Endpoint de bienvenida.
@app.get("/hola")
async def home():
    return {"message": "¡Bienvenido a KuH, tu asistente virtual de telefonía móvil!"}

# Endpoint de recomendación.
@app.post("/recomendacion")
async def consulta(pregunta: ConsultaRequest):
    #Conexión con el cliente Cohere.
    try:
        co = cohere.ClientV2(COHERE_API_KEY)
        response = co.chat(
    model="command-r-08-2024",
    messages=[{"role": "system", "content": system_prompt},
              {"role": "user", "content": pregunta.consulta}]
)
        recomendacion = response.message.content[0].text

    except Exception as e:
        raise HTTPException(status_code=400, detail=f'Error con Cohere: {str(e)}')

    # Conectar y guardar en la base de datos.
    try:
        db = pymysql.connect(host = HOST,
                    user = USERNAME,
                    password = PASSWORD,
                    port = PORT,
                    cursorclass = pymysql.cursors.DictCursor
                    
)
    
        cursor = db.cursor()
        use_db = '''USE kuh_db'''
        cursor.execute(use_db)
        query = '''INSERT INTO consultas (consulta, respuesta)
        VALUES (%s, %s)'''
        cursor.execute(query, (pregunta.consulta, recomendacion))
        db.commit()
        cursor.close()
        db.close()
    except pymysql.MySQLError as e:
        raise HTTPException(status_code=500, detail=f'Error de conexión a la base de datos: {str(e)}')
    
    return recomendacion

# Ejecuto la aplicación.
if __name__== "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
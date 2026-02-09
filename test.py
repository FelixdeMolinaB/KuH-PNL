import os
import pytest

# Mockeo env (variables de entorno) antes de importar main.
os.environ["DB_USERNAME"] = "test"
os.environ["DB_PASSWORD"] = "test"
os.environ["DB_HOST"] = "localhost"
os.environ["DB_PORT"] = "3306"
os.environ["COHERE_API_KEY"] = "fake-key"

from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from main import app

client = TestClient(app)

# Test endpoint de bienvenida.
def test_hola_endpoint():
    response = client.get("/hola")
    assert response.status_code == 200
    assert response.json() == {"message": "¡Bienvenido a KuH, tu asistente virtual de telefonía móvil!"}

# Test endpoint de recomendación. 
@patch("main.pymysql.connect")
@patch("main.cohere.ClientV2")
@patch("main.pd.read_csv") # El decorador más cercano a la función entre primero como primer argumento, por eso este mock va el último de los tres. 
def test_recomendacion_endpoint(mock_read_csv, mock_cohere, mock_db):
    # Mock del DataFrame catálogo
    mock_df = MagicMock()
    mock_df.to_string.return_value = "Catálogo mockeado de teléfonos."
    mock_read_csv.return_value = mock_df
    # Mock de Cohere LLM.
    mock_co = MagicMock()
    mock_response = MagicMock()
    mock_response.message.content = [MagicMock(text="Hola, ¿cómo estás? Esto es una prueba, no estás hablando con un LLM. Sí que te diré que no siempre el móvil más caro es la mejor opción, piensa en lo que realmente precisas, al no ser que persigas un status a través de lo material.")]
    mock_co.chat.return_value = mock_response
    mock_cohere.return_value = mock_co
    # Mock de la base de datos SQL. 
    mock_connection = MagicMock()
    mock_cursor = MagicMock()
    mock_connection.cursor.return_value = mock_cursor
    mock_db.return_value = mock_connection

    payload = {"consulta": "Hola, estoy pensando en comprarme un móvil y no sé por dónde empezar."}
    response = client.post("/recomendacion", json=payload)

    assert response.status_code == 200
    assert response.text != ""
    assert "prueba" in response.text.lower()

    # Verifico que se intenta guardar en la base de datos.
    mock_cursor.execute.assert_called()
    mock_connection.commit.assert_called()
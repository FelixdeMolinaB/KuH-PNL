import streamlit as st
import requests
from datetime import datetime
import re

# Configuración de la API
API_URL = "http://localhost:8000"  # Cambia según tu FastAPI

# Estilos CSS personalizados para el chat
st.markdown("""
<style>
.chat-bubble {
    padding: 1rem;
    border-radius: 1rem;
    margin: 0.5rem 0;
    max-width: 80%;
    word-wrap: break-word;
    white-space: pre-wrap;
}
.user-bubble {
    background-color: #e3f2fd;
    margin-left: auto;
    line-height: 1.4;
}
.assistant-bubble {
    background-color: #f5f5f5;
    line-height: 1.4;
}
ol {
    padding-left: 1.5rem;
    margin: 0.5rem 0;
}
li {
    margin-bottom: 0.3rem;
}
</style>
""", unsafe_allow_html=True)


def formatear_texto(texto: str) -> str:
    """Formatea saltos de línea, listas, negritas y URLs a HTML"""
    
    # Normalizar saltos de línea reales y literales
    texto = texto.replace("\\n", "\n")  # \n literal → salto real
    texto = texto.replace("\r\n", "\n")  # Windows
    texto = texto.replace("\r", "\n")    # Mac antiguo

    # Dobles saltos de línea → <br>
    texto = re.sub(r'\n\s*\n', '<br>', texto)
    # Saltos simples → <br>
    texto = re.sub(r'(?<!<br>)\n', '<br>', texto)

    # Listas numeradas (1., 2., 3.) → <ol><li>
    texto = re.sub(r'(\d+)\.\s+(.*?)(?=<br>|$)', r'<li>\2</li>', texto)
    if "<li>" in texto:
        texto = f"<ol>{texto}</ol>"

    # Listas con guion "- " → <ul><li>
    lines = texto.split("<br>")
    in_list = False
    formatted_lines = []
    for line in lines:
        if line.strip().startswith("- "):
            if not in_list:
                formatted_lines.append("<ul>")
                in_list = True
            formatted_lines.append(f"<li>{line.strip()[2:]}</li>")
        else:
            if in_list:
                formatted_lines.append("</ul>")
                in_list = False
            formatted_lines.append(line)
    if in_list:
        formatted_lines.append("</ul>")

    texto = "<br>".join(formatted_lines)

    # Negritas **texto** → <b>texto</b>
    texto = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', texto)

    # URLs → <a href="url" target="_blank">url</a>
    texto = re.sub(r'(https?://[^\s<]+)', r'<a href="\1" target="_blank">\1</a>', texto)

    return texto


def mostrar_historial():
    """Muestra el historial de conversación con formato HTML"""
    if 'historial' in st.session_state:
        for mensaje in st.session_state.historial:
            clase = "user-bubble" if mensaje['rol'] == 'usuario' else "assistant-bubble"
            contenido_html = formatear_texto(mensaje["contenido"])
            st.markdown(f'<div class="chat-bubble {clase}">{contenido_html}</div>', unsafe_allow_html=True)


def obtener_recomendacion(pregunta: str):
    """Obtiene recomendación de la API"""
    try:
        response = requests.post(
            f"{API_URL}/recomendacion",
            json={"consulta": pregunta}
        )
        if response.status_code == 200:
            return response.text
        return "❌ Error al obtener la recomendación"
    
    except requests.exceptions.RequestException:
        return "🔌 Error de conexión con el servidor"


def main():
    st.title("📲 KuH")
    st.markdown("¡Hola! Soy el asistente virtual de Falúa Móvil, todo un experto en nuestro catálogo 🙂")
    
    # Inicializar historial de chat
    if 'historial' not in st.session_state:
        st.session_state.historial = []
    
    # Entrada de usuario
    with st.form("chat_form"):
        pregunta = st.text_input("Para ser más preciso necesito un poco de contexto entre interacciones, ¿en qué te puedo ayudar?")
        enviado = st.form_submit_button("Enviar")
        
        if enviado and pregunta:
            # Añadir pregunta al historial
            st.session_state.historial.append({
                "rol": "usuario",
                "contenido": f"👤 Usuario: {pregunta}",
                "timestamp": datetime.now().isoformat()
            })
            
            # Obtener respuesta de la API
            respuesta = obtener_recomendacion(pregunta)
            
            # Añadir respuesta al historial
            st.session_state.historial.append({
                "rol": "asistente",
                "contenido": f"🤖 KuH: {respuesta}",
                "timestamp": datetime.now().isoformat()
            })
    
    # Mostrar historial de chat
    mostrar_historial()


if __name__ == "__main__":
    main()
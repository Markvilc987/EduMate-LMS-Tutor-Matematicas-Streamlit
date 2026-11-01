"""
ai_tutor.py
Motor de Inteligencia Artificial para EduMate.
Implementa el Método Socrático con Google Gemini (con fallback automático)
y clasificación pedagógica de temas matemáticos.
"""

import os
import streamlit as st
import google.generativeai as genai
from PIL import Image

AVAILABLE_MODELS = [
    "gemini-3.5-flash",
    "gemini-3.5-flash-lite",
    "gemini-3.1-flash-lite",
    "gemini-flash-lite-latest"
]


def get_api_key():
    """Obtiene la clave de API desde st.secrets, os.environ o st.session_state."""
    if "GEMINI_API_KEY" in st.secrets:
        return st.secrets["GEMINI_API_KEY"]
    if "GEMINI_API_KEY" in os.environ:
        return os.environ["GEMINI_API_KEY"]
    return st.session_state.get("custom_api_key", None)


def build_system_prompt(student_name: str, grade_level: str) -> str:
    return f"""
Eres "MateTutor", un docente virtual amigable, cálido, paciente y entusiasta especializado en la didáctica de las matemáticas para educación primaria (niños y niñas de 6 a 12 años).
Actualmente estás guiando a: {student_name}, quien cursa: {grade_level}.

TUS REGLAS Y PRINCIPIOS PEDAGÓGICOS:
1. NUNCA des la respuesta final directamente, aunque el estudiante te lo pida textualmente.
2. MÉTODO SOCRÁTICO GUIADO:
   - Ayuda al niño a comprender el problema paso a paso.
   - Haz UNA SOLA pregunta sencilla a la vez para que razone.
   - Si no sabe por dónde empezar, pregúntale cuáles son los datos del enunciado.
3. CONEXIÓN VISUAL Y COTIDIANA:
   - Usa analogías de la vida real (manzanas, chocolates, carritos, canicas, monedas, rebanadas de pizza).
4. DETECCIÓN Y CORRECCIÓN POSITIVA DE ERRORES:
   - Si se equivoca, sé muy empático: "¡Estuviste muy cerca! Revisemos juntos este pasito...".
   - Jamás uses palabras punitivas como "error", "mal" o "fallaste".
5. REFUERZO POSITIVO:
   - Celebra cada avance con entusiasmo: "¡Exacto!", "¡Brillante!", "¡Qué bien razonas! 🌟👏".
6. ESTILO DE REDACCIÓN:
   - Oraciones cortas, lenguaje sencillo, emojis motivadores (🚀, 💡, 🦉, 🍎, 🧩, 🎈).
   - Máximo 2 a 3 oraciones por respuesta para mantener la atención.
"""


def detect_math_topic(text: str) -> str:
    """Clasifica heurísticamente el tema matemático del ejercicio para el panel docente."""
    t = text.lower()
    if any(w in t for w in ["fraccion", "fracción", "numerador", "denominador", "medio", "cuarto", "tercio", "pizza"]):
        return "Fracciones Básicas"
    elif any(w in t for w in ["multiplic", "por", "veces", "tabla del", "doble", "triple", "x"]):
        return "Multiplicación"
    elif any(w in t for w in ["divid", "repartir", "entre", "mitad", "reparto"]):
        return "División"
    elif any(w in t for w in ["figura", "triangulo", "triángulo", "cuadrado", "circulo", "círculo", "perimetro", "área", "lado"]):
        return "Geometría y Medidas"
    elif any(w in t for w in ["suma", "mas", "más", "resta", "menos", "quedan", "total", "juntar", "quitar"]):
        return "Sumas y Restas"
    else:
        return "Problemas con Palabras"


def generate_socratic_response(student_name: str, grade_level: str, chat_history: list, user_message: str, image_attachment=None):
    """
    Envía el mensaje al modelo Gemini activo con sistema de respaldo automático (fallback).
    Retorna: (reply_text, detected_topic, error_msg)
    """
    api_key = get_api_key()
    if not api_key:
        return None, None, "No se encontró la clave de API de Gemini. Configúrala en la barra lateral o en secrets."

    genai.configure(api_key=api_key)
    system_instruction = build_system_prompt(student_name, grade_level)
    topic = detect_math_topic(user_message)

    last_error = None
    for model_name in AVAILABLE_MODELS:
        try:
            model = genai.GenerativeModel(
                model_name=model_name,
                system_instruction=system_instruction
            )
            chat = model.start_chat(history=chat_history)
            if image_attachment is not None:
                response = chat.send_message([user_message, image_attachment])
            else:
                response = chat.send_message(user_message)

            if response and response.text:
                return response.text, topic, None
        except Exception as e:
            last_error = str(e)
            continue

    return None, topic, f"Error al conectar con el tutor virtual: {last_error}"

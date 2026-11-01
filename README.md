# 🦉 EduMate LMS: Plataforma Escolar de Tutoría Socrática con IA (Docente - Estudiante)

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://streamlit.io)
[![Python 3.9+](https://img.shields.io/badge/Python-3.9+-3776AB.svg?logo=python&logoColor=white)](https://python.org)
[![Google Gemini](https://img.shields.io/badge/Google%20Gemini-3.5%20Flash-4285F4.svg?logo=google&logoColor=white)](https://aistudio.google.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Plataforma educativa integral tipo LMS (Learning Management System) diseñada para **colegios y educación primaria**, que conecta a **docentes** con el seguimiento en tiempo real del razonamiento matemático de sus **estudiantes**, potenciada por **Google Gemini 3.5 Flash** bajo el **Método Socrático**.

---

## 🌟 Funcionalidades Principales

### 👨‍🏫 1. Para Docentes (Profesores y Administradores de Grupo)
* 🏫 **Creación y Gestión de Aulas:** Crea grupos escolares con códigos de invitación únicos (ejemplo: `PRIM-3A`, `MAT-5B`).
* 📊 **Panel de Analítica de Aprendizaje (Learning Analytics):**
  * Gráficos interactivos en **Plotly** con distribución de temas practicados (Fracciones, Multiplicación, Geometría, Sumas y Restas).
  * Monitoreo de actividad cronológica (ejercicios intentados vs. resueltos en los últimos 7 días).
  * Indicador de autonomía: promedio de pistas socráticas requeridas por ejercicio.
* 👥 **Ficha Individual del Estudiante:** Tasa de resolución, temas dominados y áreas que requieren refuerzo pedagógico.
* 📜 **Auditoría de Diálogos Socráticos:** El profesor puede leer las transcripciones reales de las conversaciones de cada alumno con la IA para evaluar su proceso de pensamiento y razonamiento.

### 🧒 2. Para Estudiantes (Alumnos de Primaria)
* 💬 **MateTutor Socrático:** Chat guiado con IA que **nunca da la respuesta directa**. Plantea preguntas guía paso a paso y desglosa problemas complejos.
* 📸 **Soporte Multimodal:** Permite subir fotos del cuaderno o libro escolar con el celular o tablet.
* 🏆 **Gamificación y Medallas:** Sistema de insignias y recompensas que motivan la perseverancia y la resolución de problemas.
* 🏫 **Inscripción Fácil:** Los alumnos se unen al salón de su profesor simplemente ingresando el código del aula.

---

## 🔑 Cuentas Demostrativas Pre-cargadas

Para probar la plataforma de inmediato sin necesidad de crear cuentas nuevas:
* **Docente (Profesor):** Usuario: `profesor` | Contraseña: `clave123`
* **Alumna:** Usuario: `sofia` | Contraseña: `clave123`
* **Alumno:** Usuario: `lucas` | Contraseña: `clave123`

---

## 🚀 Despliegue 100% Gratuito en la Nube (Streamlit Cloud)

1. Sube este repositorio a tu cuenta de GitHub.
2. Ingresa a [share.streamlit.io](https://share.streamlit.io/) e inicia sesión con GitHub.
3. Haz clic en **"New app"**, selecciona este repositorio, rama `main` y archivo `app.py`.
4. En **Advanced settings -> Secrets**, agrega:
   ```toml
   GEMINI_API_KEY = "tu_clave_de_google_ai_studio"
   ```
5. Haz clic en **Deploy!** y obtendrás tu URL pública permanente y segura.

---

## 💻 Ejecución Local

```bash
cd 08_EduMate_Plataforma_Tutor_Docente_Estudiante_Streamlit
pip install -r requirements.txt
streamlit run app.py --server.port 8502
```

---

## 📜 Licencia
Distribuido bajo la Licencia **MIT**. Abierto para colegios, escuelas, docentes e investigadores en tecnología educativa.

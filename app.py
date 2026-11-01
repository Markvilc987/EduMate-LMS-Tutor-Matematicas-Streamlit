import os
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from PIL import Image

from database import (
    init_db,
    authenticate_user,
    register_user,
    get_teacher_classrooms,
    create_classroom,
    get_student_classrooms,
    enroll_student_in_class,
    get_or_create_chat_session,
    save_chat_message,
    get_session_messages,
    record_learning_progress,
    get_classroom_analytics,
    get_student_chat_history_for_teacher,
    get_connection
)
from ai_tutor import generate_socratic_response, get_api_key

# Configuración de página
st.set_page_config(
    page_title="EduMate LMS | Tutor Matemático Socrático para Primaria",
    page_icon="🦉",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inicializar Base de Datos SQLite
init_db()

# Inicializar Estado de Sesión
if "user" not in st.session_state:
    st.session_state.user = None


# Estilos CSS personalizados
st.markdown("""
<style>
    .brand-title {
        color: #2E5BFF;
        font-weight: 800;
        font-size: 2.1rem;
        margin-bottom: 0px;
    }
    .kpi-card {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 18px;
        text-align: center;
        box-shadow: 0 2px 6px rgba(0,0,0,0.03);
    }
    .kpi-val {
        font-size: 2rem;
        font-weight: 800;
        color: #2E5BFF;
    }
    .kpi-label {
        color: #64748B;
        font-size: 0.9rem;
        font-weight: 600;
        text-transform: uppercase;
    }
    .badge-docente {
        background-color: #EEF2FF;
        color: #4F46E5;
        padding: 4px 10px;
        border-radius: 8px;
        font-size: 0.85rem;
        font-weight: 700;
    }
    .badge-alumno {
        background-color: #ECFDF5;
        color: #059669;
        padding: 4px 10px;
        border-radius: 8px;
        font-size: 0.85rem;
        font-weight: 700;
    }
</style>
""", unsafe_allow_html=True)


# ==========================================
# GESTIÓN DE AUTENTICACIÓN Y BARRA LATERAL
# ==========================================

with st.sidebar:
    st.markdown("<div class='brand-title'>🦉 EduMate LMS</div>", unsafe_allow_html=True)
    st.caption("Plataforma Escolar de Tutoría Socrática en Matemáticas")
    st.divider()

    user = st.session_state.user
    if user:
        role_badge = "badge-docente" if user["role"] == "docente" else "badge-alumno"
        st.markdown(f"**Usuario:** {user['avatar']} {user['full_name']}")
        st.markdown(f"<span class='{role_badge}'>{user['role'].upper()}</span>", unsafe_allow_html=True)
        st.caption(f"Nivel: {user.get('grade_level', 'Primaria')}")
        st.divider()

        # Gestión de API Key si no está en secrets
        api_key = get_api_key()
        if not api_key:
            custom_key = st.text_input("🔑 Clave Gemini API:", type="password", key="custom_api_key_input")
            if custom_key:
                st.session_state.custom_api_key = custom_key
                st.success("¡API Key configurada!")

        if st.button("🚪 Cerrar Sesión", use_container_width=True):
            st.session_state.user = None
            st.rerun()
    else:
        st.info("👋 Por favor inicia sesión o crea una cuenta para acceder.")
        st.markdown("💡 **Cuentas Demo Disponibles:**")
        st.markdown("* **Docente:** `profesor` / `clave123`")
        st.markdown("* **Alumna:** `sofia` / `clave123`")


# ==========================================
# PANTALLA DE LOGIN Y REGISTRO (SI NO HAY USUARIO)
# ==========================================

if not st.session_state.user:
    st.markdown("## 🎓 Bienvenido a EduMate")
    st.write("El ecosistema educativo que conecta a **docentes de primaria** con el seguimiento en tiempo real del razonamiento matemático de sus **estudiantes**, guiados por Inteligencia Artificial Socrática.")

    tab_login, tab_register, tab_demos = st.tabs(["🔑 Iniciar Sesión", "📝 Registro Nuevo", "⚡ Acceso Rápido Demo"])

    # 1. Login
    with tab_login:
        col_l1, col_l2 = st.columns([1, 1])
        with col_l1:
            login_user = st.text_input("Nombre de Usuario:", key="login_u")
            login_pass = st.text_input("Contraseña:", type="password", key="login_p")
            if st.button("Ingresar", type="primary", use_container_width=True):
                auth = authenticate_user(login_user.strip(), login_pass.strip())
                if auth:
                    st.session_state.user = auth
                    st.success(f"¡Bienvenido, {auth['full_name']}!")
                    st.rerun()
                else:
                    st.error("Usuario o contraseña incorrectos.")

    # 2. Registro
    with tab_register:
        col_r1, col_r2 = st.columns([1, 1])
        with col_r1:
            reg_name = st.text_input("Nombre Completo:")
            reg_user = st.text_input("Nombre de Usuario (para ingresar):")
            reg_pass = st.text_input("Contraseña:", type="password")
            reg_role = st.selectbox("Tipo de Usuario:", ["alumno", "docente"], format_func=lambda x: "Estudiante (Alumno)" if x == "alumno" else "Profesor (Docente)")
            reg_grade = st.selectbox("Grado Escolar:", ["1° y 2° Primaria", "3° y 4° Primaria", "5° y 6° Primaria"])
            
            reg_code = None
            if reg_role == "alumno":
                reg_code = st.text_input("Código de Aula del Profesor (Opcional, ej: PRIM-3A):")

            if st.button("Registrarme en EduMate", type="primary", use_container_width=True):
                if not reg_name or not reg_user or not reg_pass:
                    st.error("Por favor completa todos los campos obligatorios.")
                else:
                    ok, res = register_user(reg_user.strip(), reg_pass.strip(), reg_name.strip(), reg_role, reg_grade, reg_code)
                    if ok:
                        st.success("¡Registro exitoso! Ya puedes iniciar sesión con tu usuario.")
                    else:
                        st.error(res)

    # 3. Acceso Rápido Demo
    with tab_demos:
        st.write("Haz clic en cualquiera de estos perfiles para explorar el sistema de inmediato sin escribir contraseñas:")
        c_d1, c_d2 = st.columns(2)
        with c_d1:
            if st.button("👨‍🏫 Entrar como Profesor (Prof. Carlos Mendoza)", use_container_width=True):
                st.session_state.user = authenticate_user("profesor", "clave123")
                st.rerun()
        with c_d2:
            if st.button("👧 Entrar como Alumna (Sofía Gómez - 3° Primaria)", use_container_width=True):
                st.session_state.user = authenticate_user("sofia", "clave123")
                st.rerun()

    st.stop()


# ==========================================
# ROL 1: PANEL DEL DOCENTE
# ==========================================

if user["role"] == "docente":
    teacher_id = user["id"]
    classrooms = get_teacher_classrooms(teacher_id)

    st.markdown(f"## 👨‍🏫 Panel Docente | {user['full_name']}")
    st.write("Gestiona tus grupos de estudiantes, monitorea su progreso pedagógico y supervisa sus interacciones socráticas en matemáticas.")

    if not classrooms:
        st.warning("Aún no tienes ningún aula creada. Crea tu primer grupo en la pestaña '🏫 Crear Aula'.")
        selected_class = None
    else:
        # Selector de aula activa
        class_options = {c["id"]: f"{c['name']} (Código: {c['code']}) - {c['student_count']} alumnos" for c in classrooms}
        selected_class_id = st.selectbox("Selecciona el Aula a Supervisar:", options=list(class_options.keys()), format_func=lambda x: class_options[x])
        selected_class = next((c for c in classrooms if c["id"] == selected_class_id), None)

    tab_overview, tab_students, tab_dialogues, tab_manage_class = st.tabs([
        "📊 Panel General y Analítica",
        "👥 Seguimiento de Alumnos",
        "📜 Auditoría de Diálogos Socráticos",
        "🏫 Gestión y Creación de Aulas"
    ])

    # 1. Analítica Grupal
    with tab_overview:
        if selected_class:
            analytics = get_classroom_analytics(selected_class["id"])

            # Tarjetas KPI
            k1, k2, k3, k4 = st.columns(4)
            with k1:
                st.markdown(f"<div class='kpi-card'><div class='kpi-val'>{analytics['total_students']}</div><div class='kpi-label'>Alumnos Inscritos</div></div>", unsafe_allow_html=True)
            with k2:
                st.markdown(f"<div class='kpi-card'><div class='kpi-val'>{analytics['total_exercises']}</div><div class='kpi-label'>Ejercicios Intentados</div></div>", unsafe_allow_html=True)
            with k3:
                st.markdown(f"<div class='kpi-card'><div class='kpi-val'>{analytics['total_solved']}</div><div class='kpi-label'>Ejercicios Resueltos</div></div>", unsafe_allow_html=True)
            with k4:
                st.markdown(f"<div class='kpi-card'><div class='kpi-val'>{analytics['avg_hints']}</div><div class='kpi-label'>Pistas Promedio / Ejercicio</div></div>", unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            col_chart1, col_chart2 = st.columns([1, 1])

            # Gráfico de distribución de temas
            with col_chart1:
                st.subheader("📚 Distribución de Temas Practicados")
                if analytics["topics_distribution"]:
                    df_topics = pd.DataFrame(analytics["topics_distribution"])
                    fig_topics = px.pie(
                        df_topics,
                        names="math_topic",
                        values="count",
                        hole=0.4,
                        color_discrete_sequence=px.colors.qualitative.Pastel
                    )
                    fig_topics.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=300)
                    st.plotly_chart(fig_topics, use_container_width=True)
                else:
                    st.info("Aún no hay actividad registrada en este grupo.")

            # Gráfico de actividad temporal
            with col_chart2:
                st.subheader("📈 Actividad en los Últimos 7 Días")
                if analytics["timeline"]:
                    df_time = pd.DataFrame(analytics["timeline"])
                    fig_time = px.bar(
                        df_time,
                        x="date",
                        y=["solved", "count"],
                        barmode="group",
                        labels={"value": "Ejercicios", "date": "Fecha", "variable": "Estado"},
                        color_discrete_map={"count": "#CBD5E1", "solved": "#2E5BFF"}
                    )
                    fig_time.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=300)
                    st.plotly_chart(fig_time, use_container_width=True)
                else:
                    st.info("No se registra actividad en los últimos 7 días.")

            # Tabla resumen de estudiantes
            st.subheader("📋 Resumen de Desempeño por Alumno")
            if analytics["students_summary"]:
                df_summary = pd.DataFrame(analytics["students_summary"])
                df_display = df_summary[["avatar", "full_name", "total_attempts", "solved", "avg_hints", "last_activity"]].copy()
                df_display.columns = ["Icono", "Nombre del Alumno", "Intentos", "Resueltos", "Pistas Promedio", "Última Actividad"]
                st.dataframe(df_display, use_container_width=True, hide_index=True)
            else:
                st.info("No hay alumnos matriculados en esta aula.")

    # 2. Seguimiento Individual de Alumnos
    with tab_students:
        if selected_class:
            analytics = get_classroom_analytics(selected_class["id"])
            student_list = analytics["students_summary"]

            if not student_list:
                st.info("No hay estudiantes matriculados en este grupo.")
            else:
                student_map = {s["student_id"]: f"{s['avatar']} {s['full_name']} (@{s['username']})" for s in student_list}
                st_id = st.selectbox("Selecciona un Alumno para ver su ficha:", options=list(student_map.keys()), format_func=lambda x: student_map[x])
                target_student = next((s for s in student_list if s["student_id"] == st_id), None)

                if target_student:
                    sc1, sc2, sc3 = st.columns([1, 1, 1])
                    with sc1:
                        st.metric("Total Ejercicios", target_student["total_attempts"])
                    with sc2:
                        st.metric("Ejercicios Resueltos", target_student["solved"])
                    with sc3:
                        st.metric("Pistas Requeridas (Prom.)", round(target_student["avg_hints"] or 0, 1))

                    # Medallas del alumno
                    st.markdown("#### 🏅 Insignias de Aprendizaje Alcanzadas")
                    m_col1, m_col2, m_col3 = st.columns(3)
                    with m_col1:
                        if target_student["solved"] >= 1:
                            st.success("🌟 **Iniciador Matemático** (Completó 1 ejercicio)")
                        else:
                            st.caption("🔒 Iniciador Matemático (Pendiente)")
                    with m_col2:
                        if target_student["solved"] >= 5:
                            st.success("🚀 **Pensador Curioso** (Completó 5 ejercicios)")
                        else:
                            st.caption("🔒 Pensador Curioso (Requiere 5 resueltos)")
                    with m_col3:
                        if (target_student["avg_hints"] or 0) <= 2 and target_student["solved"] >= 3:
                            st.success("🧠 **Alta Autonomía** (Pocas pistas necesarias)")
                        else:
                            st.caption("🔒 Alta Autonomía (Requiere resolver con <= 2 pistas)")

    # 3. Auditoría de Conversaciones con IA
    with tab_dialogues:
        if selected_class:
            analytics = get_classroom_analytics(selected_class["id"])
            student_list = analytics["students_summary"]
            if not student_list:
                st.info("No hay estudiantes en esta clase.")
            else:
                student_map = {s["student_id"]: f"{s['avatar']} {s['full_name']}" for s in student_list}
                sel_st_id = st.selectbox("Ver diálogos de:", options=list(student_map.keys()), format_func=lambda x: student_map[x], key="audit_student_sel")

                history = get_student_chat_history_for_teacher(sel_st_id, selected_class["id"])
                if not history:
                    st.info("Este estudiante aún no ha iniciado sesiones de chat.")
                else:
                    for s_idx, sess in enumerate(history):
                        with st.expander(f"📝 {sess['title']} | Tema: {sess['math_topic']} ({sess['created_at']})", expanded=(s_idx == 0)):
                            for msg in sess["messages"]:
                                role_label = "🧒 Alumno" if msg["role"] == "user" else "🦉 MateTutor"
                                bg_color = "#F1F5F9" if msg["role"] == "user" else "#EFF6FF"
                                st.markdown(f"""
                                <div style='background-color:{bg_color}; padding:10px 14px; border-radius:10px; margin-bottom:8px;'>
                                    <strong>{role_label}:</strong><br>{msg['content']}
                                </div>
                                """, unsafe_allow_html=True)

    # 4. Gestión y Creación de Aulas
    with tab_manage_class:
        st.subheader("➕ Crear Nueva Aula Escolar")
        with st.form("form_create_class"):
            new_c_name = st.text_input("Nombre del Aula (ej: 4° Grado B - Matemáticas):")
            new_c_grade = st.selectbox("Nivel / Grado:", ["1° y 2° Primaria", "3° y 4° Primaria", "5° y 6° Primaria"])
            new_c_code = st.text_input("Código de Aula Personalizado (Opcional, déjalo vacío para generar uno aleatorio):")
            new_c_desc = st.text_area("Descripción para los alumnos:")
            btn_create = st.form_submit_button("Crear Grupo", type="primary")

            if btn_create:
                if not new_c_name:
                    st.error("El nombre del aula es obligatorio.")
                else:
                    ok, code_or_err = create_classroom(teacher_id, new_c_name.strip(), new_c_grade, new_c_code, new_c_desc)
                    if ok:
                        st.success(f"¡Aula creada con éxito! El código de invitación para tus alumnos es: **{code_or_err}**")
                        st.rerun()
                    else:
                        st.error(code_or_err)

        st.divider()
        st.subheader("📚 Tus Aulas Activas")
        for c in classrooms:
            st.markdown(f"**{c['name']}** | Código de Invitación: `{c['code']}` | Alumnos matriculados: `{c['student_count']}`")


# ==========================================
# ROL 2: PANEL DEL ALUMNO (ESTUDIANTE)
# ==========================================

elif user["role"] == "alumno":
    student_id = user["id"]
    classrooms = get_student_classrooms(student_id)
    active_class = classrooms[0] if classrooms else None
    active_class_id = active_class["id"] if active_class else None

    # Header Alumno
    st.markdown(f"## {user['avatar']} ¡Hola, {user['full_name']}! ✨")
    if active_class:
        st.caption(f"🏫 Estás en el aula: **{active_class['name']}** (Código: `{active_class['code']}`) con tu profesor **{active_class['teacher_name']}**")
    else:
        st.warning("Aún no estás inscrito en el aula de tu profesor. Ve a la pestaña '🏫 Mi Salón' para unirte con un código.")

    tab_chat, tab_achievements, tab_my_class = st.tabs([
        "💬 MateTutor (Tutoría IA)",
        "🏆 Mis Logros y Medallas",
        "🏫 Mi Salón de Clase"
    ])

    # 1. Chat de Práctica Socrática
    with tab_chat:
        col_c1, col_c2 = st.columns([3, 1])

        with col_c2:
            st.markdown("#### ⚙️ Opciones")
            grade_level = st.selectbox(
                "Nivel:",
                ["1° y 2° Primaria", "3° y 4° Primaria", "5° y 6° Primaria"],
                index=1
            )
            uploaded_image = st.file_uploader("📸 Foto de tu cuaderno:", type=["jpg", "jpeg", "png"])
            img_to_send = None
            if uploaded_image:
                img_to_send = Image.open(uploaded_image)
                st.image(img_to_send, caption="Vista previa", use_container_width=True)

            st.divider()
            if st.button("🎉 ¡Logré resolverlo!", type="primary", use_container_width=True):
                # Registrar progreso exitoso
                record_learning_progress(student_id, active_class_id, "Resolución de Problemas", status="resuelto", hints=st.session_state.get("hints_used", 1))
                st.balloons()
                st.success("¡Excelente trabajo! Tu profesor verá que resolviste este ejercicio. 🌟")

        with col_c1:
            session_id = get_or_create_chat_session(student_id, active_class_id, grade_level)
            messages = get_session_messages(session_id)

            if not messages:
                # Mensaje de bienvenida inicial
                init_msg = f"¡Hola {user['full_name'].split()[0]}! 🦉 Soy tu MateTutor. ¿Qué ejercicio de matemáticas quieres resolver hoy? ¡Escríbemelo o sube una foto de tu cuaderno y lo resolveremos paso a paso!"
                save_chat_message(session_id, "assistant", init_msg)
                messages = [{"role": "assistant", "content": init_msg}]

            # Renderizar mensajes
            for m in messages:
                role = m["role"]
                avatar = "🦉" if role == "assistant" else user["avatar"]
                with st.chat_message(role, avatar=avatar):
                    st.markdown(m["content"])

            # Input del alumno
            if user_input := st.chat_input("Escribe tu pregunta o respuesta aquí..."):
                # Mostrar y guardar mensaje del alumno
                save_chat_message(session_id, "user", user_input)
                with st.chat_message("user", avatar=user["avatar"]):
                    st.markdown(user_input)
                    if img_to_send:
                        st.image(img_to_send, width=280)

                # Formatear historial para Gemini
                history_for_gemini = []
                for m in messages:
                    history_for_gemini.append({
                        "role": "user" if m["role"] == "user" else "model",
                        "parts": [m["content"]]
                    })

                # Generar respuesta con spinner
                with st.chat_message("assistant", avatar="🦉"):
                    with st.spinner("MateTutor está pensando una pista para ti... 💡"):
                        reply, topic, err = generate_socratic_response(
                            user["full_name"],
                            grade_level,
                            history_for_gemini,
                            user_input,
                            img_to_send
                        )

                        if reply:
                            st.markdown(reply)
                            save_chat_message(session_id, "assistant", reply)
                            # Registrar actividad en progreso
                            record_learning_progress(student_id, active_class_id, topic, status="en_progreso", hints=1)
                        else:
                            st.error(err)

    # 2. Mis Logros y Medallas
    with tab_achievements:
        st.subheader("🏅 Mis Medallas de Matemáticas")
        conn = get_connection()
        c = conn.cursor()
        c.execute("""
        SELECT COUNT(*) as attempts, SUM(CASE WHEN status = 'resuelto' THEN 1 ELSE 0 END) as solved
        FROM learning_logs WHERE student_id = ?;
        """, (student_id,))
        my_stats = dict(c.fetchone())
        conn.close()

        solved_count = my_stats.get("solved", 0) or 0
        attempts_count = my_stats.get("attempts", 0) or 0

        a1, a2 = st.columns(2)
        with a1:
            st.metric("Total Ejercicios Intentados", attempts_count)
        with a2:
            st.metric("Total Ejercicios Resueltos", solved_count)

        st.divider()
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            if solved_count >= 1:
                st.success("🌟 **Primer Paso**\n\nResuelve tu 1er ejercicio")
            else:
                st.caption("🔒 Primer Paso\n\n(Resuelve 1 ejercicio)")
        with m2:
            if solved_count >= 3:
                st.success("🚀 **Explorador**\n\nResuelve 3 ejercicios")
            else:
                st.caption("🔒 Explorador\n\n(Faltan ejercicios)")
        with m3:
            if solved_count >= 5:
                st.success("🧠 **Genio Matemático**\n\nResuelve 5 ejercicios")
            else:
                st.caption("🔒 Genio Matemático\n\n(Faltan ejercicios)")
        with m4:
            if solved_count >= 10:
                st.success("🏆 **Maestro EduMate**\n\nResuelve 10 ejercicios")
            else:
                st.caption("🔒 Maestro EduMate\n\n(Faltan ejercicios)")

    # 3. Mi Salón de Clase
    with tab_my_class:
        st.subheader("🏫 Mis Aulas Registradas")
        if classrooms:
            for c in classrooms:
                st.info(f"Aula: **{c['name']}** | Código: `{c['code']}` | Profesor: **{c['teacher_name']}**")
        else:
            st.write("Aún no estás unido a ningún aula.")

        st.divider()
        st.subheader("➕ Unirme a otra Aula")
        join_code = st.text_input("Ingresa el código que te dio tu profesor (ej: PRIM-3A):")
        if st.button("Unirme al Aula", type="primary"):
            if not join_code:
                st.error("Por favor escribe el código.")
            else:
                ok, msg = enroll_student_in_class(student_id, join_code)
                if ok:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)

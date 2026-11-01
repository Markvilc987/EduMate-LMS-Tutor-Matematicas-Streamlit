"""
database.py
Manejo completo de base de datos SQLite para la plataforma EduMate.
Soporta gestión de usuarios (docentes y alumnos), aulas, matrículas,
sesiones de chat socrático y métricas de aprendizaje/analítica pedagógica.
"""

import sqlite3
import hashlib
import os
from datetime import datetime, timedelta
import random

DB_PATH = os.path.join(os.path.dirname(__file__), "edumate.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def hash_password(password: str) -> str:
    """Genera hash SHA-256 seguro con sal estática para contraseñas."""
    salt = "EduMate_Salt_2026_Secure"
    return hashlib.sha256((salt + password).encode("utf-8")).hexdigest()


def init_db():
    """Crea las tablas de la base de datos si no existen y puebla datos demo."""
    conn = get_connection()
    c = conn.cursor()

    # 1. Tabla de Usuarios (Docentes y Alumnos)
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        full_name TEXT NOT NULL,
        role TEXT NOT NULL CHECK(role IN ('docente', 'alumno')),
        grade_level TEXT DEFAULT '3° y 4° Primaria',
        avatar TEXT DEFAULT '🦉',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 2. Tabla de Aulas / Clases creadas por Docentes
    c.execute("""
    CREATE TABLE IF NOT EXISTS classrooms (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        teacher_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        grade_level TEXT NOT NULL,
        description TEXT DEFAULT '',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 3. Tabla de Matrícula (Alumnos inscritos en Aulas)
    c.execute("""
    CREATE TABLE IF NOT EXISTS enrollments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        classroom_id INTEGER NOT NULL REFERENCES classrooms(id) ON DELETE CASCADE,
        student_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(classroom_id, student_id)
    );
    """)

    # 4. Tabla de Sesiones de Chat Socrático
    c.execute("""
    CREATE TABLE IF NOT EXISTS chat_sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        classroom_id INTEGER REFERENCES classrooms(id) ON DELETE SET NULL,
        title TEXT NOT NULL,
        math_topic TEXT DEFAULT 'General',
        grade_level TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 5. Tabla de Mensajes individuales
    c.execute("""
    CREATE TABLE IF NOT EXISTS chat_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id INTEGER NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
        role TEXT NOT NULL CHECK(role IN ('user', 'assistant')),
        content TEXT NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 6. Tabla de Registros de Aprendizaje (Learning Analytics)
    c.execute("""
    CREATE TABLE IF NOT EXISTS learning_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        classroom_id INTEGER REFERENCES classrooms(id) ON DELETE SET NULL,
        math_topic TEXT NOT NULL,
        status TEXT NOT NULL CHECK(status IN ('resuelto', 'en_progreso')),
        hints_count INTEGER DEFAULT 0,
        exercises_count INTEGER DEFAULT 1,
        difficulty TEXT DEFAULT 'Medio',
        date DATE DEFAULT (DATE('now')),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    conn.commit()

    # Verificar si ya existen usuarios; si no, poblar datos demostrativos
    c.execute("SELECT COUNT(*) as cnt FROM users")
    if c.fetchone()["cnt"] == 0:
        seed_demo_data(conn)

    conn.close()


def seed_demo_data(conn):
    """Puebla datos iniciales realistas para que el docente vea analíticas de inmediato."""
    c = conn.cursor()
    pwd = hash_password("clave123")

    # 1. Crear Docente
    c.execute("""
    INSERT INTO users (username, password_hash, full_name, role, grade_level, avatar)
    VALUES ('profesor', ?, 'Prof. Carlos Mendoza', 'docente', '3° y 4° Primaria', '👨‍🏫');
    """, (pwd,))
    teacher_id = c.lastrowid

    # 2. Crear Aula del Docente
    c.execute("""
    INSERT INTO classrooms (code, name, teacher_id, grade_level, description)
    VALUES ('PRIM-3A', '3° Grado A - Matemáticas Divertidas', ?, '3° y 4° Primaria', 'Aula virtual de práctica guiada con MateTutor');
    """, (teacher_id,))
    class_id = c.lastrowid

    # 3. Crear Alumnos
    students = [
        ("sofia", "Sofía Gómez", "3° y 4° Primaria", "👧"),
        ("lucas", "Lucas Ramírez", "3° y 4° Primaria", "🧒"),
        ("mateo", "Mateo Torres", "3° y 4° Primaria", "👦"),
        ("valentina", "Valentina Morales", "3° y 4° Primaria", "👧")
    ]

    student_ids = []
    for uname, fname, grade, avt in students:
        c.execute("""
        INSERT INTO users (username, password_hash, full_name, role, grade_level, avatar)
        VALUES (?, ?, ?, 'alumno', ?, ?);
        """, (uname, pwd, fname, grade, avt))
        s_id = c.lastrowid
        student_ids.append(s_id)
        # Matricular en el aula
        c.execute("""
        INSERT INTO enrollments (classroom_id, student_id)
        VALUES (?, ?);
        """, (class_id, s_id))

    # 4. Crear Registros de Aprendizaje para los Alumnos (últimos 7 días)
    topics = ["Sumas y Restas", "Multiplicación", "División", "Fracciones Básicas", "Problemas de Conteo"]
    today = datetime.now()

    for s_id in student_ids:
        # Cada alumno tiene entre 4 y 8 actividades registradas
        for _ in range(random.randint(5, 9)):
            topic = random.choice(topics)
            days_ago = random.randint(0, 6)
            log_date = (today - timedelta(days=days_ago)).strftime("%Y-%m-%d")
            hints = random.randint(1, 4)
            status = random.choice(["resuelto", "resuelto", "resuelto", "en_progreso"])

            c.execute("""
            INSERT INTO learning_logs (student_id, classroom_id, math_topic, status, hints_count, exercises_count, date)
            VALUES (?, ?, ?, ?, ?, 1, ?);
            """, (s_id, class_id, topic, status, hints, log_date))

    # 5. Crear una conversación real de ejemplo para Sofía
    sofia_id = student_ids[0]
    c.execute("""
    INSERT INTO chat_sessions (student_id, classroom_id, title, math_topic, grade_level)
    VALUES (?, ?, 'Práctica de Fracciones con Pizzas', 'Fracciones Básicas', '3° y 4° Primaria');
    """, (sofia_id, class_id))
    sess_id = c.lastrowid

    sample_dialogue = [
        ("user", "Hola MateTutor, tengo un problema: si divido una pizza en 4 partes iguales y como 1 parte, ¿qué fracción me comí?"),
        ("assistant", "¡Hola Sofía! 🍕 ¡Qué rico problema! Imagina que tenemos las 4 rebanadas en la mesa. Si tomaste 1 rebanada de las 4 que había en total, ¿cuántas rebanadas tomaste arriba (numerador) y cuántas eran en total abajo (denominador)?"),
        ("user", "Tomé 1 arriba y en total eran 4 abajo... ¿entonces es 1/4?"),
        ("assistant", "¡Brillante, Sofía! 🌟 ¡Exactamente! Te comiste **1/4 (un cuarto)** de la pizza. Ahora dime: ¿cuántas rebanadas quedaron en la mesa?")
    ]

    for role, content in sample_dialogue:
        c.execute("""
        INSERT INTO chat_messages (session_id, role, content)
        VALUES (?, ?, ?);
        """, (sess_id, role, content))

    conn.commit()


# ==========================================
# FUNCIONES DE USUARIOS Y AUTENTICACIÓN
# ==========================================

def authenticate_user(username, password):
    conn = get_connection()
    c = conn.cursor()
    pwd_hash = hash_password(password)
    c.execute("SELECT * FROM users WHERE username = ? AND password_hash = ?", (username, pwd_hash))
    user = c.fetchone()
    conn.close()
    return dict(user) if user else None


def register_user(username, password, full_name, role, grade_level="3° y 4° Primaria", classroom_code=None):
    conn = get_connection()
    c = conn.cursor()
    pwd_hash = hash_password(password)
    avatar = "👨‍🏫" if role == "docente" else "🧒"

    try:
        c.execute("""
        INSERT INTO users (username, password_hash, full_name, role, grade_level, avatar)
        VALUES (?, ?, ?, ?, ?, ?);
        """, (username, pwd_hash, full_name, role, grade_level, avatar))
        user_id = c.lastrowid

        # Si es alumno y brindó código de aula, inscribirlo
        if role == "alumno" and classroom_code:
            c.execute("SELECT id FROM classrooms WHERE code = ?", (classroom_code.strip().upper(),))
            cls = c.fetchone()
            if cls:
                c.execute("""
                INSERT INTO enrollments (classroom_id, student_id)
                VALUES (?, ?);
                """, (cls["id"], user_id))

        conn.commit()
        conn.close()
        return True, user_id
    except sqlite3.IntegrityError:
        conn.close()
        return False, "El nombre de usuario ya está registrado."


# ==========================================
# FUNCIONES DE AULAS Y GRUPOS
# ==========================================

def create_classroom(teacher_id, name, grade_level, code=None, description=""):
    conn = get_connection()
    c = conn.cursor()
    if not code:
        code = f"MAT-{random.randint(100, 999)}"
    try:
        c.execute("""
        INSERT INTO classrooms (code, name, teacher_id, grade_level, description)
        VALUES (?, ?, ?, ?, ?);
        """, (code.upper().strip(), name, teacher_id, grade_level, description))
        conn.commit()
        cls_id = c.lastrowid
        conn.close()
        return True, code
    except sqlite3.IntegrityError:
        conn.close()
        return False, "El código de aula ya existe. Intenta con otro."


def get_teacher_classrooms(teacher_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
    SELECT c.*, COUNT(e.id) as student_count
    FROM classrooms c
    LEFT JOIN enrollments e ON c.id = e.classroom_id
    WHERE c.teacher_id = ?
    GROUP BY c.id
    ORDER BY c.created_at DESC;
    """, (teacher_id,))
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows


def get_student_classrooms(student_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
    SELECT c.*, u.full_name as teacher_name
    FROM classrooms c
    JOIN enrollments e ON c.id = e.classroom_id
    JOIN users u ON c.teacher_id = u.id
    WHERE e.student_id = ?;
    """, (student_id,))
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows


def enroll_student_in_class(student_id, class_code):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id FROM classrooms WHERE code = ?", (class_code.strip().upper(),))
    cls = c.fetchone()
    if not cls:
        conn.close()
        return False, "Código de aula no encontrado."
    try:
        c.execute("""
        INSERT INTO enrollments (classroom_id, student_id)
        VALUES (?, ?);
        """, (cls["id"], student_id))
        conn.commit()
        conn.close()
        return True, "¡Te has unido exitosamente al aula!"
    except sqlite3.IntegrityError:
        conn.close()
        return False, "Ya estás matriculado en esta aula."


# ==========================================
# FUNCIONES DE CHAT Y REGISTRO DE APRENDIZAJE
# ==========================================

def get_or_create_chat_session(student_id, classroom_id=None, grade_level="3° y 4° Primaria"):
    conn = get_connection()
    c = conn.cursor()
    # Buscar última sesión activa del estudiante
    c.execute("""
    SELECT * FROM chat_sessions
    WHERE student_id = ?
    ORDER BY updated_at DESC LIMIT 1;
    """, (student_id,))
    sess = c.fetchone()

    if sess:
        sess_dict = dict(sess)
        conn.close()
        return sess_dict["id"]
    else:
        c.execute("""
        INSERT INTO chat_sessions (student_id, classroom_id, title, grade_level)
        VALUES (?, ?, 'Sesión de Aprendizaje Guiado', ?);
        """, (student_id, classroom_id, grade_level))
        conn.commit()
        s_id = c.lastrowid
        conn.close()
        return s_id


def save_chat_message(session_id, role, content):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
    INSERT INTO chat_messages (session_id, role, content)
    VALUES (?, ?, ?);
    """, (session_id, role, content))
    c.execute("UPDATE chat_sessions SET updated_at = CURRENT_TIMESTAMP WHERE id = ?", (session_id,))
    conn.commit()
    conn.close()


def get_session_messages(session_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
    SELECT role, content, timestamp
    FROM chat_messages
    WHERE session_id = ?
    ORDER BY id ASC;
    """, (session_id,))
    msgs = [dict(r) for r in c.fetchall()]
    conn.close()
    return msgs


def record_learning_progress(student_id, classroom_id, math_topic, status="resuelto", hints=1):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
    INSERT INTO learning_logs (student_id, classroom_id, math_topic, status, hints_count, exercises_count)
    VALUES (?, ?, ?, ?, ?, 1);
    """, (student_id, classroom_id, math_topic, status, hints))
    conn.commit()
    conn.close()


# ==========================================
# ANALÍTICA Y REPORTES PARA EL DOCENTE
# ==========================================

def get_classroom_analytics(classroom_id):
    conn = get_connection()
    c = conn.cursor()

    # 1. Total de estudiantes
    c.execute("SELECT COUNT(*) as total_students FROM enrollments WHERE classroom_id = ?", (classroom_id,))
    total_students = c.fetchone()["total_students"]

    # 2. Total de ejercicios resueltos y en progreso
    c.execute("""
    SELECT 
        COUNT(*) as total_logs,
        SUM(CASE WHEN status = 'resuelto' THEN 1 ELSE 0 END) as total_solved,
        AVG(hints_count) as avg_hints
    FROM learning_logs
    WHERE classroom_id = ?;
    """, (classroom_id,))
    stats = dict(c.fetchone())

    # 3. Distribución por temas matemáticos
    c.execute("""
    SELECT math_topic, COUNT(*) as count, SUM(CASE WHEN status = 'resuelto' THEN 1 ELSE 0 END) as solved_count
    FROM learning_logs
    WHERE classroom_id = ?
    GROUP BY math_topic
    ORDER BY count DESC;
    """, (classroom_id,))
    topics_dist = [dict(r) for r in c.fetchall()]

    # 4. Desempeño por estudiante individual
    c.execute("""
    SELECT 
        u.id as student_id,
        u.full_name,
        u.username,
        u.avatar,
        COUNT(l.id) as total_attempts,
        SUM(CASE WHEN l.status = 'resuelto' THEN 1 ELSE 0 END) as solved,
        AVG(l.hints_count) as avg_hints,
        MAX(l.created_at) as last_activity
    FROM users u
    JOIN enrollments e ON u.id = e.student_id
    LEFT JOIN learning_logs l ON u.id = l.student_id AND l.classroom_id = e.classroom_id
    WHERE e.classroom_id = ?
    GROUP BY u.id
    ORDER BY solved DESC, u.full_name ASC;
    """, (classroom_id,))
    students_summary = [dict(r) for r in c.fetchall()]

    # 5. Actividad en los últimos 7 días
    c.execute("""
    SELECT date, COUNT(*) as count, SUM(CASE WHEN status = 'resuelto' THEN 1 ELSE 0 END) as solved
    FROM learning_logs
    WHERE classroom_id = ? AND date >= DATE('now', '-7 days')
    GROUP BY date
    ORDER BY date ASC;
    """, (classroom_id,))
    timeline = [dict(r) for r in c.fetchall()]

    conn.close()

    return {
        "total_students": total_students,
        "total_exercises": stats.get("total_logs", 0) or 0,
        "total_solved": stats.get("total_solved", 0) or 0,
        "avg_hints": round(stats.get("avg_hints", 0.0) or 0.0, 1),
        "topics_distribution": topics_dist,
        "students_summary": students_summary,
        "timeline": timeline
    }


def get_student_chat_history_for_teacher(student_id, classroom_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
    SELECT s.id as session_id, s.title, s.math_topic, s.created_at, s.updated_at
    FROM chat_sessions s
    WHERE s.student_id = ? AND (s.classroom_id = ? OR s.classroom_id IS NULL)
    ORDER BY s.updated_at DESC;
    """, (student_id, classroom_id))
    sessions = [dict(r) for r in c.fetchall()]

    full_history = []
    for sess in sessions:
        msgs = get_session_messages(sess["session_id"])
        sess["messages"] = msgs
        full_history.append(sess)

    conn.close()
    return full_history

from flask import Flask, render_template, request, redirect, url_for, session, send_file
import random
import sqlite3
import pandas as pd
from io import BytesIO
from fpdf import FPDF

app = Flask(__name__)
app.secret_key = 'clave_secreta_segura'

# Credenciales del administrador
ADMIN_USER = 'Ali-Chan1703'
ADMIN_PASS = 'Ali-Chan1703'

# Variantes por grado
VARIANTES_POR_GRADO = {
    '4to_Bachillerato_CCLL': ['A', 'B', 'C'],
    '4to_Perito':           ['A', 'B', 'C'],
    '5to_Perito':           ['A', 'B', 'C']
}

# Enlaces de Google Forms por grado y variante
GOOGLE_FORMS = {
    '4to_Bachillerato_CCLL': {
        'A': 'https://docs.google.com/forms/d/FORM_4TO_BACH_A/viewform',
        'B': 'https://docs.google.com/forms/d/FORM_4TO_BACH_B/viewform',
        'C': 'https://docs.google.com/forms/d/FORM_4TO_BACH_C/viewform',
    },
    '4to_Perito': {
        'A': 'https://docs.google.com/forms/d/FORM_4TO_PERITO_A/viewform',
        'B': 'https://docs.google.com/forms/d/FORM_4TO_PERITO_B/viewform',
        'C': 'https://docs.google.com/forms/d/FORM_4TO_PERITO_C/viewform',
    },
    '5to_Perito': {
        'A': 'https://docs.google.com/forms/d/FORM_5TO_PERITO_A/viewform',
        'B': 'https://docs.google.com/forms/d/FORM_5TO_PERITO_B/viewform',
        'C': 'https://docs.google.com/forms/d/FORM_5TO_PERITO_C/viewform',
    }
}

# Crear tabla si no existe
def crear_base():
    with sqlite3.connect("examenes.db") as con:
        con.execute('''
            CREATE TABLE IF NOT EXISTS examenes (
                id INTEGER PRIMARY KEY,
                nombre TEXT, apellido TEXT, correo TEXT,
                grado TEXT, seccion TEXT, variante TEXT
            )
        ''')

crear_base()

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        nombre  = request.form.get('nombre')
        apellido= request.form.get('apellido')
        correo  = request.form.get('correo')
        grado   = request.form.get('grado')
        seccion = request.form.get('seccion')

        # Validación de grado
        if grado not in VARIANTES_POR_GRADO:
            return "Grado inválido", 400

        # Asignar variante sólo de ese grado
        variante = random.choice(VARIANTES_POR_GRADO[grado])
        # Obtener enlace correspondiente
        enlace = GOOGLE_FORMS[grado][variante]

        # Guardar en DB
        with sqlite3.connect("examenes.db") as con:
            con.execute('''
                INSERT INTO examenes (nombre, apellido, correo, grado, seccion, variante)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (nombre, apellido, correo, grado, seccion, variante))

        # Mostrar pantalla de variante y enlace
        return render_template("variante.html",
                               nombre=nombre,
                               grado=grado,
                               variante=variante,
                               enlace=enlace)

    return render_template("index.html")


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        usuario   = request.form.get('usuario')
        contrasena= request.form.get('contrasena')
        if usuario == ADMIN_USER and contrasena == ADMIN_PASS:
            session['admin'] = True
            return redirect(url_for('admin'))
        error = 'Credenciales incorrectas'
    return render_template("login.html", error=error)


@app.route('/admin')
def admin():
    if not session.get('admin'):
        return redirect(url_for('login'))

    with sqlite3.connect("examenes.db") as con:
        datos = con.execute(
            "SELECT nombre, apellido, correo, grado, seccion, variante FROM examenes"
        ).fetchall()

    return render_template("admin.html", datos=datos)


@app.route('/exportar_excel')
def exportar_excel():
    if not session.get('admin'):
        return redirect(url_for('login'))
    df = pd.read_sql("SELECT * FROM examenes", sqlite3.connect("examenes.db"))
    salida = BytesIO()
    with pd.ExcelWriter(salida, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Examenes')
    salida.seek(0)
    return send_file(salida,
                     attachment_filename="examenes.xlsx",
                     as_attachment=True,
                     mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


@app.route('/exportar_pdf')
def exportar_pdf():
    if not session.get('admin'):
        return redirect(url_for('login'))

    rows = sqlite3.connect("examenes.db").execute(
        "SELECT nombre, apellido, correo, grado, seccion, variante FROM examenes"
    ).fetchall()

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Asignaciones de Examen", ln=True, align='C')
    pdf.ln(5)

    for r in rows:
        linea = f"{r[0]} {r[1]} | {r[2]} | {r[3]} {r[4]} | Variante: {r[5]}"
        pdf.multi_cell(0, 8, linea)

    salida = BytesIO()
    pdf.output(salida)
    salida.seek(0)
    return send_file(salida,
                     attachment_filename="examenes.pdf",
                     as_attachment=True,
                     mimetype="application/pdf")


@app.route('/logout')
def logout():
    session.pop('admin', None)
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)

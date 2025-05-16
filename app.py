from flask import Flask, render_template, request, redirect, url_for, session, send_file, jsonify
import sqlite3
import pandas as pd
from fpdf import FPDF
from io import BytesIO
from functools import wraps

app = Flask(__name__, static_folder='static')
app.secret_key = 'clave_secreta'

# Decorador login_required funcional
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Base de datos
def obtener_conexion():
    return sqlite3.connect('estudiantes.db')

def crear_tabla():
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS estudiantes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT,
            apellido TEXT,
            correo TEXT,
            grado TEXT,
            seccion TEXT,
            variante TEXT
        )
    ''')
    conexion.commit()
    conexion.close()

crear_tabla()

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        nombre = request.form['nombre']
        apellido = request.form['apellido']
        correo = request.form['correo']
        grado = request.form['grado']
        seccion = request.form['seccion']

        # ← ← ← NO SE TOCA LA LÓGICA DE ASIGNACIÓN AQUÍ →
        variante, formulario = asignar_variante(grado)

        conexion = obtener_conexion()
        cursor = conexion.cursor()
        cursor.execute("INSERT INTO estudiantes (nombre, apellido, correo, grado, seccion, variante) VALUES (?, ?, ?, ?, ?, ?)",
                       (nombre, apellido, correo, grado, seccion, variante))
        conexion.commit()
        conexion.close()

        return render_template('variante.html', variante=variante, formulario=formulario)

    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form['usuario']
        contraseña = request.form['contraseña']
        if usuario == 'admin' and contraseña == 'admin123':
            session['admin'] = True
            return redirect(url_for('admin'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('admin', None)
    return redirect(url_for('index'))

@app.route('/admin')
@login_required
def admin():
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM estudiantes")
    datos = cursor.fetchall()
    cursor.execute("SELECT DISTINCT grado FROM estudiantes")
    grados = [row[0] for row in cursor.fetchall()]
    conexion.close()
    return render_template('admin.html', datos=datos, grados=grados, secciones=[], filtro_grado='', filtro_seccion='')

@app.route('/get_secciones/<grado>')
@login_required
def get_secciones(grado):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT DISTINCT seccion FROM estudiantes WHERE grado = ?", (grado,))
    secciones = [row[0] for row in cursor.fetchall()]
    conexion.close()
    return jsonify(secciones)

@app.route('/filtrar_datos', methods=['POST'])
@login_required
def filtrar_datos():
    grado = request.form['grado']
    seccion = request.form['seccion']

    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM estudiantes WHERE grado = ? AND seccion = ?", (grado, seccion))
    datos_filtrados = cursor.fetchall()
    cursor.execute("SELECT DISTINCT grado FROM estudiantes")
    grados = [row[0] for row in cursor.fetchall()]
    cursor.execute("SELECT DISTINCT seccion FROM estudiantes WHERE grado = ?", (grado,))
    secciones = [row[0] for row in cursor.fetchall()]
    conexion.close()
    return render_template('admin.html', datos=datos_filtrados, grados=grados, secciones=secciones,
                           filtro_grado=grado, filtro_seccion=seccion)

@app.route('/exportar_excel')
@login_required
def exportar_excel():
    conexion = obtener_conexion()
    df = pd.read_sql_query("SELECT * FROM estudiantes", conexion)
    conexion.close()

    output = BytesIO()
    df.to_excel(output, index=False)
    output.seek(0)
    return send_file(output, download_name="estudiantes.xlsx", as_attachment=True)

@app.route('/exportar_pdf')
@login_required
def exportar_pdf():
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM estudiantes")
    datos = cursor.fetchall()
    conexion.close()

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    for fila in datos:
        pdf.cell(200, 10, txt=", ".join(str(x) for x in fila), ln=True)

    output = BytesIO()
    pdf.output(output)
    output.seek(0)
    return send_file(output, download_name="estudiantes.pdf", as_attachment=True)

# ← ← ← LÓGICA DE ASIGNACIÓN NO MODIFICADA
def asignar_variante(grado):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT COUNT(*) FROM estudiantes WHERE grado = ?", (grado,))
    cantidad = cursor.fetchone()[0]
    conexion.close()

    opciones = ['A', 'B', 'C']
    variante = opciones[cantidad % 3]

    formularios = {
        "4to Bachillerato CCLL": {
            "A": "https://docs.google.com/forms/d/e/1FAIpQLSeRBUArBPcE59Yq9urltrrbxAUFKsp5tfq-NqLAKIDV6lt8Mg/viewform?usp=header",
            "B": "https://docs.google.com/forms/d/e/1FAIpQLSchLJXKeEMkrE-L8tLP_rAoLy5RvdC9G4p44sY7pwktN5dIqQ/viewform?usp=dialog",
            "C": "https://docs.google.com/forms/d/e/1FAIpQLSe6uLhQ9MEG_C0hXOqw8HUMuz-kn1mObpJUGlaNEFMEzo4nUg/viewform?usp=header"
        },
        "4to Perito": {
            "A": "https://docs.google.com/forms/d/e/1FAIpQLScWxawlIGTSALdJD9oGz0G1j5pfMZlisQlkKzzbOGEyuiCzlA/viewform?usp=header",
            "B": "https://docs.google.com/forms/d/e/1FAIpQLScrA4cyTR-gMnXlYz3u_InK6k8fo9dhrQ-uzLSkwGZrtHb54g/viewform?usp=dialog",
            "C": "https://docs.google.com/forms/d/e/1FAIpQLSdM8Yiiy9iT2DViqMNnu5dZ5rTIsaVeU3V8UjwUCdk73a5_6Q/viewform?usp=header"
        },
        "5to Perito": {
            "A": "https://docs.google.com/forms/d/e/1FAIpQLSfLgUDVPvos0fXMu2i55nKMn-TZkH-lZ4HABBgWXsGgFGrIXQ/viewform?usp=header",
            "B": "https://docs.google.com/forms/d/e/1FAIpQLScinHn-OXs1vfiUrQj2P5l1JsnKoXkgSKqvJ2cvyve4uTrRPA/viewform?usp=dialog",
            "C": "https://docs.google.com/forms/d/e/1FAIpQLSfQnWAj2cT5tt5g-apHraRXsnzAIgNU0b52zuV0L2OgOfAmHA/viewform?usp=header"
        }
    }

    formulario = formularios.get(grado, {}).get(variante, "#")
    return variante, formulario

if __name__ == '__main__':
    app.run(debug=True)

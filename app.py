from flask import Flask, render_template, request, redirect, url_for, session, send_file
import sqlite3
import random
import os
from io import BytesIO
import pandas as pd
from fpdf import FPDF

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'clave_dev_segura')
app.config['SESSION_COOKIE_SECURE'] = True  # Importante en Render HTTPS

DATABASE = 'estudiantes.db'

def get_connection():
    return sqlite3.connect(DATABASE)

def create_table():
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS estudiantes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            apellido TEXT NOT NULL,
            correo TEXT NOT NULL,
            grado TEXT NOT NULL,
            seccion TEXT NOT NULL,
            variante TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

create_table()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/asignar', methods=['POST'])
def asignar():
    nombre = request.form['nombre']
    apellido = request.form['apellido']
    correo = request.form['correo']
    grado = request.form['grado']
    seccion = request.form['seccion']

    variantes_por_grado = {
        '4to Bachillerato CCLL': ['A', 'B', 'C'],
        '4to Perito': ['A', 'B', 'C'],
        '5to Perito': ['A', 'B', 'C']
    }

    if grado not in variantes_por_grado:
        return 'Grado no válido', 400

    variante = random.choice(variantes_por_grado[grado])

    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        INSERT INTO estudiantes (nombre, apellido, correo, grado, seccion, variante)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (nombre, apellido, correo, grado, seccion, variante))
    conn.commit()
    conn.close()

    formularios_google = {
        '4to Bachillerato CCLL': {
            'A': 'https://docs.google.com/forms/d/e/1FAIpQLSeRBUArBPcE59Yq9urltrrbxAUFKsp5tfq-NqLAKIDV6lt8Mg/viewform?usp=header',
            'B': 'https://docs.google.com/forms/d/e/1FAIpQLSchLJXKeEMkrE-L8tLP_rAoLy5RvdC9G4p44sY7pwktN5dIqQ/viewform?usp=dialog',
            'C': 'https://docs.google.com/forms/d/e/1FAIpQLSe6uLhQ9MEG_C0hXOqw8HUMuz-kn1mObpJUGlaNEFMEzo4nUg/viewform?usp=header'
        },
        '4to Perito': {
            'A': 'https://docs.google.com/forms/d/e/1FAIpQLScWxawlIGTSALdJD9oGz0G1j5pfMZlisQlkKzzbOGEyuiCzlA/viewform?usp=header',
            'B': 'https://docs.google.com/forms/d/e/1FAIpQLScrA4cyTR-gMnXlYz3u_InK6k8fo9dhrQ-uzLSkwGZrtHb54g/viewform?usp=dialog',
            'C': 'https://docs.google.com/forms/d/e/1FAIpQLSdM8Yiiy9iT2DViqMNnu5dZ5rTIsaVeU3V8UjwUCdk73a5_6Q/viewform?usp=header'
        },
        '5to Perito': {
            'A': 'https://docs.google.com/forms/d/e/1FAIpQLSfLgUDVPvos0fXMu2i55nKMn-TZkH-lZ4HABBgWXsGgFGrIXQ/viewform?usp=header',
            'B': 'https://docs.google.com/forms/d/e/1FAIpQLScinHn-OXs1vfiUrQj2P5l1JsnKoXkgSKqvJ2cvyve4uTrRPA/viewform?usp=dialog',
            'C': 'https://docs.google.com/forms/d/e/1FAIpQLSfQnWAj2cT5tt5g-apHraRXsnzAIgNU0b52zuV0L2OgOfAmHA/viewform?usp=header'
        }
    }

    return redirect(formularios_google[grado][variante])

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form['usuario']
        contrasena = request.form['contrasena']
        if usuario == 'Ali-Chan1703' and contrasena == 'Ali-Chan1703':
            session['usuario'] = usuario
            return redirect(url_for('admin'))
        else:
            return render_template('login.html', error='Credenciales incorrectas')
    return render_template('login.html')

@app.route('/admin')
def admin():
    if 'usuario' not in session:
        return redirect(url_for('login'))

    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM estudiantes')
    datos = c.fetchall()
    conn.close()
    return render_template('admin.html', datos=datos)

@app.route('/logout')
def logout():
    session.pop('usuario', None)
    return redirect(url_for('index'))

@app.route('/exportar_excel')
def exportar_excel():
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM estudiantes", conn)
    conn.close()

    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Estudiantes')

    output.seek(0)
    return send_file(output, download_name="estudiantes.xlsx", as_attachment=True)

@app.route('/exportar_pdf')
def exportar_pdf():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM estudiantes")
    datos = c.fetchall()
    conn.close()

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=10)
    pdf.cell(200, 10, txt="Listado de Estudiantes", ln=True, align='C')
    pdf.ln(10)

    for fila in datos:
        fila_texto = ' | '.join(str(campo) for campo in fila)
        pdf.cell(200, 10, txt=fila_texto, ln=True)

    output = BytesIO()
    pdf.output(output)
    output.seek(0)
    return send_file(output, download_name="estudiantes.pdf", as_attachment=True)

if __name__ == '__main__':
    app.run(debug=False)

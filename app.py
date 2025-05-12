from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import random

app = Flask(__name__)

def crear_bd():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS examen (
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

crear_bd()

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        nombre = request.form['nombre']
        apellido = request.form['apellido']
        correo = request.form['correo']
        grado = request.form['grado']
        seccion = request.form['seccion']

        variantes_por_grado = {
            '4to_Bachillerato_CCLL': ['A', 'B', 'C'],
            '4to_Perito': ['A', 'B', 'C'],
            '5to_Perito': ['A', 'B', 'C']
        }

        variante = random.choice(variantes_por_grado.get(grado, ['A']))  # Por defecto A

        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO examen (nombre, apellido, correo, grado, seccion, variante) VALUES (?, ?, ?, ?, ?, ?)",
                       (nombre, apellido, correo, grado, seccion, variante))
        conn.commit()
        conn.close()

        return f'<h2>Gracias, {nombre}. Tu variante de examen es: {variante}</h2>'

    return render_template('index.html')

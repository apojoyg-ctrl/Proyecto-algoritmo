from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'clave_secreta_super_segura_tienda'

UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

USUARIO_CORRECTO = "callejon22"
PASSWORD_CORRECTO = "urbano2121"

def init_db():
    conn = sqlite3.connect('inventario.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS productos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            categoria TEXT NOT NULL,
            talla TEXT NOT NULL,
            color TEXT NOT NULL,
            precio REAL NOT NULL,
            stock INTEGER NOT NULL,
            imagen TEXT
        )
    ''')
    conn.commit()
    conn.close()

# Algoritmo de Ordenamiento de Burbuja (Bubble Sort)
def ordenamiento_burbuja(lista, criterio='id'):
    n = len(lista)
    lista = [list(elem) for elem in lista]
    indices = {'id': 0, 'nombre': 1, 'precio': 5, 'stock': 6}
    idx = indices.get(criterio, 0)

    for i in range(n):
        for j in range(0, n - i - 1):
            if criterio == 'nombre':
                if lista[j][idx].lower() > lista[j + 1][idx].lower():
                    lista[j], lista[j + 1] = lista[j + 1], lista[j]
            else:
                if lista[j][idx] > lista[j + 1][idx]:
                    lista[j], lista[j + 1] = lista[j + 1], lista[j]
    return lista

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        usuario = request.form['usuario']
        password = request.form['password']
        if usuario == USUARIO_CORRECTO and password == PASSWORD_CORRECTO:
            session['logged_in'] = True
            return redirect(url_for('index'))
        else:
            error = "Usuario o contraseña incorrectos"
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route('/')
def index():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    busqueda = request.args.get('busqueda', '').strip()
    orden = request.args.get('orden', 'id')

    conn = sqlite3.connect('inventario.db')
    cursor = conn.cursor()
    
    if busqueda:
        cursor.execute('''
            SELECT * FROM productos 
            WHERE nombre LIKE ? OR categoria LIKE ? OR color LIKE ? OR talla LIKE ?
        ''', (f'%{busqueda}%', f'%{busqueda}%', f'%{busqueda}%', f'%{busqueda}%'))
    else:
        cursor.execute('SELECT * FROM productos')
        
    productos = cursor.fetchall()
    conn.close()

    productos_ordenados = ordenamiento_burbuja(productos, orden)

    total_prendas = sum(p[6] for p in productos_ordenados)
    total_variedad = len(productos_ordenados)
    
    if total_variedad > 0:
        precio_promedio = sum(p[5] for p in productos_ordenados) / total_variedad
        prenda_mas_cara = max(productos_ordenados, key=lambda x: x[5])
        prenda_mas_barata = min(productos_ordenados, key=lambda x: x[5])
    else:
        precio_promedio = 0
        prenda_mas_cara = None
        prenda_mas_barata = None

    calculos = {
        'total_prendas': total_prendas,
        'total_variedad': total_variedad,
        'precio_promedio': precio_promedio,
        'prenda_mas_cara': prenda_mas_cara,
        'prenda_mas_barata': prenda_mas_barata
    }

    return render_template('index.html', productos=productos_ordenados, calculos=calculos, busqueda=busqueda, orden=orden)

@app.route('/agregar', methods=['POST'])
def agregar():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    try:
        nombre = request.form['nombre'].strip()
        categoria = request.form['categoria'].strip()
        talla = request.form['talla'].strip()
        color = request.form['color'].strip()
        precio = float(request.form['precio'])
        stock = int(request.form['stock'])

        if precio < 0 or stock < 0:
            return redirect(url_for('index'))

        imagen_file = request.files['imagen']
        imagen_nombre = ''
        if imagen_file and imagen_file.filename != '':
            imagen_nombre = imagen_file.filename
            imagen_file.save(os.path.join(app.config['UPLOAD_FOLDER'], imagen_nombre))

        conn = sqlite3.connect('inventario.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO productos (nombre, categoria, talla, color, precio, stock, imagen)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (nombre, categoria, talla, color, precio, stock, imagen_nombre))
        conn.commit()
        conn.close()
    except (ValueError, KeyError):
        pass

    return redirect(url_for('index'))

@app.route('/eliminar/<int:id>')
def eliminar(id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    conn = sqlite3.connect('inventario.db')
    cursor = conn.cursor()
    cursor.execute('SELECT imagen FROM productos WHERE id = ?', (id,))
    resultado = cursor.fetchone()
    if resultado and resultado[0]:
        img_path = os.path.join(app.config['UPLOAD_FOLDER'], resultado[0])
        if os.path.exists(img_path):
            os.remove(img_path)

    cursor.execute('DELETE FROM productos WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
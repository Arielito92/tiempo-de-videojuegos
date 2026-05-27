from flask import Flask, render_template, request, session, redirect, send_from_directory
import requests
import sqlite3
import psycopg2
import os
import random
from datetime import timedelta
from werkzeug.utils import secure_filename
from googletrans import Translator
from requests.exceptions import ConnectionError
from flask import jsonify

app = Flask(__name__)

conexion = psycopg2.connect(
    os.getenv("DATABASE_URL")
)

cursor = conexion.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS usuarios (

    id SERIAL PRIMARY KEY,
    nombre TEXT,
    contraseña TEXT,
    foto TEXT

)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS reseñas (

    id SERIAL PRIMARY KEY,
    juego_id TEXT,
    usuario TEXT,
    nota REAL,
    comentario TEXT,
    likes INTEGER DEFAULT 0

)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS favoritos (

    id SERIAL PRIMARY KEY,
    usuario TEXT,
    juego_id TEXT

)
""")

conexion.commit()

conexion.close()

app.config["SESSION_PERMANENT"] = True

app.secret_key = "videojuegos_secret"

app.permanent_session_lifetime = timedelta(days=30)

API_KEY = "00276b692ecb452f99138a74a2fcc579"

@app.route("/")
def inicio():

    usuario = session.get("usuario")

    url_populares = f"https://api.rawg.io/api/games?key={API_KEY}&ordering=-added&page_size=16"

    pagina_random_1 = random.randint(1, 5)

    pagina_random_2 = random.randint(6, 10)

    url_sugeridos_1 = f"https://api.rawg.io/api/games?key={API_KEY}&page={pagina_random_1}&page_size=40"

    url_sugeridos_2 = f"https://api.rawg.io/api/games?key={API_KEY}&page={pagina_random_2}&page_size=40"

    try:

        respuesta_populares = requests.get(url_populares)

    except ConnectionError:

        return render_template("offline.html")

    datos_populares = respuesta_populares.json()

    juegos_populares = datos_populares["results"]

    respuesta_sugeridos_1 = requests.get(url_sugeridos_1)

    respuesta_sugeridos_2 = requests.get(url_sugeridos_2)

    datos_sugeridos_1 = respuesta_sugeridos_1.json()

    datos_sugeridos_2 = respuesta_sugeridos_2.json()

    juegos_sugeridos = (
    datos_sugeridos_1["results"]
    +
    datos_sugeridos_2["results"]
)

    random.shuffle(juegos_sugeridos)

    url_accion = f"https://api.rawg.io/api/games?key={API_KEY}&genres=action&page_size=8"

    accion = requests.get(url_accion).json()["results"]


    url_rpg = f"https://api.rawg.io/api/games?key={API_KEY}&genres=role-playing-games-rpg&page_size=8"

    rpg = requests.get(url_rpg).json()["results"]


    url_indie = f"https://api.rawg.io/api/games?key={API_KEY}&genres=indie&page_size=8"

    indie = requests.get(url_indie).json()["results"]

    foto_usuario = None

    if "usuario" in session:

     conexion = psycopg2.connect(
     os.getenv("DATABASE_URL")
     )

     cursor = conexion.cursor()

     cursor.execute(
        """
        SELECT foto
        FROM usuarios
        WHERE nombre = ?
        """,
        (session["usuario"],)
    )

     resultado = cursor.fetchone()

     conexion.close()

     if resultado:

        foto_usuario = resultado[0]

    return render_template(
        "index.html", 
        juegos_populares=juegos_populares,
        juegos_sugeridos=juegos_sugeridos,
        usuario=usuario,
        accion=accion,
        rpg=rpg,
        indie=indie,
        foto_usuario=foto_usuario
    )

@app.route("/categoria/<genero>")
def categoria(genero):

    usuario = session.get("usuario")

    foto_usuario = None


    if usuario:

        conexion = psycopg2.connect(
        os.getenv("DATABASE_URL")
        )

        cursor = conexion.cursor()

        cursor.execute(
            """
            SELECT foto
            FROM usuarios
            WHERE nombre = ?
            """,
            (usuario,)
        )

        resultado = cursor.fetchone()

        conexion.close()

        if resultado:

            foto_usuario = resultado[0]


    if genero == "populares":

     url = f"https://api.rawg.io/api/games?key={API_KEY}&ordering=-added&page_size=50"


    elif genero == "horror":

     url = f"https://api.rawg.io/api/games?key={API_KEY}&tags=horror&page_size=50"


    else:

     url = f"https://api.rawg.io/api/games?key={API_KEY}&genres={genero}&page_size=50"


    respuesta = requests.get(url)

    datos = respuesta.json()

    juegos = datos["results"]

    nombres = {

    "populares": "🔥 Juegos populares",

    "action": "⚔ Juegos de Acción",

    "role-playing-games-rpg": "🧙 Juegos RPG",

    "shooter": "🔫 Shooters",

    "adventure": "🌍 Aventuras",

    "indie": "💎 Indies",

    "horror-survival": "👻 Terror",

    "sports": "⚽ Deportes"
}

    titulo_categoria = nombres.get(genero, genero)


    return render_template(
        "categoria.html",
        juegos=juegos,
        genero=titulo_categoria,
        usuario=usuario,
        foto_usuario=foto_usuario
    )

@app.route("/buscar")
def buscar():

    usuario = session.get("usuario")

    foto_usuario = None


    if usuario:

        conexion = psycopg2.connect(
        os.getenv("DATABASE_URL")
     )

        cursor = conexion.cursor()

        cursor.execute(
            """
            SELECT foto
            FROM usuarios
            WHERE nombre = ?
            """,
            (usuario,)
        )

        resultado = cursor.fetchone()

        conexion.close()

        if resultado:

            foto_usuario = resultado[0]


    busqueda = request.args.get("q")

    url = f"https://api.rawg.io/api/games?key={API_KEY}&search={busqueda}"

    respuesta = requests.get(url)

    datos = respuesta.json()

    juegos = datos["results"]


    return render_template(
        "index.html",
        juegos=juegos,
        usuario=usuario,
        foto_usuario=foto_usuario
    )

@app.route("/juego/<id_juego>")
def juego(id_juego):

   url = f"https://api.rawg.io/api/games/{id_juego}?key={API_KEY}&languages=es"

   respuesta = requests.get(url)

   juego = respuesta.json()

   try:

    translator = Translator()

    descripcion_ingles = juego["description_raw"]

    descripcion_español = translator.translate(
        descripcion_ingles,
        dest="es"
    ).text

    juego["description_raw"] = descripcion_español

   except:

    pass

   trailer = None

   if "clip" in juego and juego["clip"]:

    trailer = juego["clip"]["clip"]

   url_screenshots = f"https://api.rawg.io/api/games/{id_juego}/screenshots?key={API_KEY}"

   respuesta_screenshots = requests.get(url_screenshots)

   datos_screenshots = respuesta_screenshots.json()

   screenshots = datos_screenshots["results"]

   conexion: sqlite3.Connection = psycopg2.connect(
    os.getenv("DATABASE_URL")
   )

   cursor = conexion.cursor()

   cursor.execute(
    """
    SELECT reseñas.id,
           reseñas.usuario,
           reseñas.nota,
           reseñas.comentario,
           usuarios.foto,

           COUNT(likes.id)

    FROM reseñas

    LEFT JOIN usuarios
    ON reseñas.usuario = usuarios.nombre

    LEFT JOIN likes
    ON reseñas.id = likes.reseña_id

    WHERE juego_id = ?

    GROUP BY reseñas.id
    """,
    (id_juego,)
)
   reseñas = cursor.fetchall()

   cursor.execute(
    """
    SELECT AVG(nota), COUNT(*)

    FROM reseñas

    WHERE juego_id = ?
    """,
    (id_juego,)
)

   promedio = cursor.fetchone()

   conexion.close()

   

   return render_template(
    "juego.html",
    juego=juego,
    reseñas=reseñas,
    screenshots=screenshots,
    trailer=trailer,
    promedio=promedio,
    descripcion=juego["description_raw"]
)

@app.route("/registro")
def registro():

    return render_template("registro.html")
@app.route("/registro", methods=["POST"])
def guardar_usuario():

    nombre = request.form.get("nombre")

    contraseña = request.form.get("contraseña")

    conexion = psycopg2.connect(
    os.getenv("DATABASE_URL")
    )

    cursor = conexion.cursor()

    cursor.execute(
    "SELECT * FROM usuarios WHERE nombre = ?",
    (nombre,)
)

    usuario_existente = cursor.fetchone()

    if usuario_existente:

     conexion.close()

     return render_template(
     "registro.html",
     error="Ese usuario ya existe"
     )

    cursor.execute(
    """
    INSERT INTO usuarios
    (nombre, contraseña, foto)

    VALUES (?, ?, ?)
    """,
    (nombre, contraseña, None)
)

    conexion.commit()

    conexion.close()

    return redirect("/")

@app.route("/login")
def login():

    return render_template("login.html")

@app.route("/login", methods=["POST"])
def verificar_login():

    nombre = request.form.get("nombre")

    contraseña = request.form.get("contraseña")

    conexion = psycopg2.connect(
    os.getenv("DATABASE_URL")
    )

    cursor = conexion.cursor()

    cursor.execute(
        "SELECT * FROM usuarios WHERE nombre = ? AND contraseña = ?",
        (nombre, contraseña)
    )

    usuario = cursor.fetchone()

    conexion.close()

    if usuario:

        session.permanent = True

        session["usuario"] = nombre

        return redirect("/")

    else:

        return render_template(
            "login.html",
            error="Usuario o contraseña incorrectos"
        )
    
@app.route("/cambiar_nombre", methods=["POST"])
def cambiar_nombre():

    if "usuario" not in session:

        return redirect("/login")

    nombre_nuevo = request.form.get("nombre_nuevo")

    nombre_actual = session["usuario"]

    conexion = psycopg2.connect(
    os.getenv("DATABASE_URL")
    )

    cursor = conexion.cursor()

    cursor.execute(
        """
        SELECT *
        FROM usuarios
        WHERE nombre = ?
        """,
        (nombre_nuevo,)
    )

    usuario_existente = cursor.fetchone()

    if usuario_existente:

        conexion.close()

        return redirect(f"/usuario/{nombre_actual}")

    cursor.execute(
        """
        UPDATE usuarios
        SET nombre = ?
        WHERE nombre = ?
        """,
        (nombre_nuevo, nombre_actual)
    )

    cursor.execute(
        """
        UPDATE reseñas
        SET usuario = ?
        WHERE usuario = ?
        """,
        (nombre_nuevo, nombre_actual)
    )

    cursor.execute(
        """
        UPDATE favoritos
        SET usuario = ?
        WHERE usuario = ?
        """,
        (nombre_nuevo, nombre_actual)
    )

    cursor.execute(
        """
        UPDATE likes
        SET usuario = ?
        WHERE usuario = ?
        """,
        (nombre_nuevo, nombre_actual)
    )

    conexion.commit()

    conexion.close()

    session["usuario"] = nombre_nuevo

    return redirect(f"/usuario/{nombre_nuevo}")

@app.route("/guardar_reseña", methods=["POST"])
def guardar_reseña():

    if "usuario" not in session:

        return render_template(
            "mensaje.html",
            titulo="Debes iniciar sesión",
            mensaje="Necesitas iniciar sesión para publicar una reseña."
        )

    juego_id = request.form.get("juego_id")

    nota = request.form.get("nota")

    comentario = request.form.get("comentario")

    usuario = session["usuario"]

    conexion = psycopg2.connect(
    os.getenv("DATABASE_URL")
    )

    cursor = conexion.cursor()

    cursor.execute(
        """
        SELECT *
        FROM reseñas

        WHERE usuario = ?
        AND juego_id = ?
        """,
        (usuario, juego_id)
    )

    reseña_existente = cursor.fetchone()

    if reseña_existente:

        conexion.close()

        return redirect(f"/juego/{juego_id}")

    cursor.execute(
        """
        INSERT INTO reseñas
        (juego_id, usuario, nota, comentario)

        VALUES (?, ?, ?, ?)
        """,
        (juego_id, usuario, nota, comentario)
    )

    conexion.commit()

    conexion.close()

    return redirect(f"/juego/{juego_id}")

@app.route("/like/<int:resena_id>")
def like_resena(resena_id):

    if "usuario" not in session:

        return render_template(
            "mensaje.html",
            titulo="Debes iniciar sesión",
            mensaje="Necesitas una cuenta para dar likes."
        )

    usuario = session["usuario"]

    conexion = psycopg2.connect(
    os.getenv("DATABASE_URL")
    )

    cursor = conexion.cursor()


    cursor.execute(
        """
        SELECT *
        FROM likes

        WHERE usuario = ?
        AND reseña_id = ?
        """,
        (usuario, resena_id)
    )

    like_existente = cursor.fetchone()


    if like_existente:

        cursor.execute(
            """
            DELETE FROM likes

            WHERE usuario = ?
            AND reseña_id = ?
            """,
            (usuario, resena_id)
        )

    else:

        cursor.execute(
            """
            INSERT INTO likes
            (usuario, reseña_id)

            VALUES (?, ?)
            """,
            (usuario, resena_id)
        )


    conexion.commit()

    conexion.close()

    return redirect(request.referrer)

@app.route("/api/like/<int:resena_id>")
def api_like(resena_id):

    if "usuario" not in session:

        return jsonify({
            "error": True
        })

    conexion = psycopg2.connect(
    os.getenv("DATABASE_URL")
    )

    cursor = conexion.cursor()

    cursor.execute(
        """
        UPDATE reseñas
        SET likes = likes + 1
        WHERE id = ?
        """,
        (resena_id,)
    )

    conexion.commit()

    cursor.execute(
        """
        SELECT likes
        FROM reseñas
        WHERE id = ?
        """,
        (resena_id,)
    )

    likes = cursor.fetchone()[0]

    conexion.close()

    return jsonify({
        "likes": likes
    })

@app.route("/borrar_resena/<int:id_resena>")
def borrar_resena(id_resena):

    conexion = psycopg2.connect(
    os.getenv("DATABASE_URL")
    )

    cursor = conexion.cursor()

    cursor.execute(
        "DELETE FROM reseñas WHERE id = ?",
        (id_resena,)
    )

    conexion.commit()

    conexion.close()

    return redirect("/")

@app.route("/logout")
def logout():

    session.pop("usuario", None)

    return redirect("/")

@app.route("/usuario/<nombre>")
def perfil_usuario(nombre):

    if "usuario" not in session:

        return redirect("/login")

    usuario = nombre

    conexion = psycopg2.connect(
    os.getenv("DATABASE_URL")
    )

    cursor = conexion.cursor()

    cursor.execute(
    """
    SELECT foto
    FROM usuarios
    WHERE nombre = ?
    """,
    (usuario,)
)

    foto = cursor.fetchone()

    foto_usuario = foto[0]

    conexion = sqlite3.connect("videojuegos.db")

    cursor = conexion.cursor()

    cursor.execute(
        """
        SELECT reseñas.juego_id,
               reseñas.nota,
               reseñas.comentario,
               COUNT(likes.id)

        FROM reseñas

        LEFT JOIN likes
        ON reseñas.id = likes.reseña_id

        WHERE reseñas.usuario = ?

        GROUP BY reseñas.id
        """,
        (usuario,)
    )

    reseñas_db = cursor.fetchall()

    reseñas = []

    for reseña in reseñas_db:

        id_juego = reseña[0]

        url = f"https://api.rawg.io/api/games/{id_juego}?key={API_KEY}"

        respuesta = requests.get(url)

        juego = respuesta.json()

        nombre_juego = juego["name"]

        reseñas.append(
            (
                nombre_juego,
                reseña[1],
                reseña[2],
                reseña[3]
            )
        )

    cursor.execute(
    """
    SELECT juego_id
    FROM favoritos
    WHERE usuario = ?
    """,
    (usuario,)
)

    favoritos_db = cursor.fetchall()

    favoritos = []

    for favorito in favoritos_db:

     id_juego = favorito[0]

     url = f"https://api.rawg.io/api/games/{id_juego}?key={API_KEY}"

     respuesta = requests.get(url)

     juego = respuesta.json()

     favoritos.append(juego)

    conexion.close()

    return render_template(
        "perfil.html",
        usuario=usuario,
        reseñas=reseñas,
        favoritos=favoritos,
        foto_usuario=foto_usuario
    )

@app.route("/agregar_favorito/<id_juego>")
def agregar_favorito(id_juego):

    if "usuario" not in session:

     return redirect("/login")

    usuario = session["usuario"]

    conexion = psycopg2.connect(
    os.getenv("DATABASE_URL")
    )

    cursor = conexion.cursor()


    cursor.execute(
    """
    SELECT * FROM favoritos

    WHERE usuario = ?
    AND juego_id = ?
    """,
    (usuario, id_juego)
)

    favorito_existente = cursor.fetchone()


    if favorito_existente:

     cursor.execute(
        """
        DELETE FROM favoritos

        WHERE usuario = ?
        AND juego_id = ?
        """,
        (usuario, id_juego)
    )

    else:

     cursor.execute(
        """
        INSERT INTO favoritos
        (usuario, juego_id)

        VALUES (?, ?)
        """,
        (usuario, id_juego)
    )


    conexion.commit()

    conexion.close()

    return redirect(f"/juego/{id_juego}")

@app.route("/subir_foto", methods=["POST"])
def subir_foto():

    if "usuario" not in session:

        return redirect("/login")

    archivo = request.files["foto"]

    if archivo:

        nombre_archivo = secure_filename(archivo.filename)

        ruta = os.path.join(
            "static/uploads",
            nombre_archivo
        )

        archivo.save(ruta)

        conexion = psycopg2.connect(
        os.getenv("DATABASE_URL")
        )

        cursor = conexion.cursor()

        cursor.execute(
            """
            UPDATE usuarios
            SET foto = ?
            WHERE nombre = ?
            """,
            (
                nombre_archivo,
                session["usuario"]
            )
        )

        conexion.commit()

        conexion.close()

    return redirect(f"/usuario/{session['usuario']}")

@app.route("/offline")
def offline():

 return render_template("offline.html")

@app.route("/service-worker.js")
def service_worker():

    return send_from_directory(
        ".",
        "service-worker.js"
    )

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )
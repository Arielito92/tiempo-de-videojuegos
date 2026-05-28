import sqlite3

conexion = sqlite3.connect("videojuegos.db")

cursor = conexion.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS usuarios (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    nombre TEXT UNIQUE,

    contraseña TEXT,
               
    foto TEXT           

)
""")

conexion.commit()

cursor.execute("""
CREATE TABLE IF NOT EXISTS resenas (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    juego_id INTEGER,

    usuario TEXT,

    nota REAL,

    comentario TEXT,
               
    likes INTEGER DEFAULT 0          
               

)
""")

conexion.commit()

cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS favoritos (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        usuario TEXT,

        juego_id TEXT
    )
    """
)

conexion.commit()

cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS likes (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        usuario TEXT,

        resena_id INTEGER
    )
    """
)

conexion.commit()

conexion.close()

print("Base de datos creada")
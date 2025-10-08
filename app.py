


from flask import Flask, render_template, request, redirect, session, url_for, jsonify
from functools import wraps
from random import sample
from werkzeug.utils import secure_filename
import os
from Coneccion import connection, query_all, query_one, execute  # <-- usamos helpers


import os
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())


app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret")

# (Opcional) Ruta de diagnóstico de DB
@app.route("/dbcheck")
def dbcheck():
    try:
        conn = connection()
        with conn.cursor() as cur:
            cur.execute("SELECT VERSION();")
            version = cur.fetchone()[0]
        conn.close()
        return f"✅ Conectado a MySQL. Versión: {version}"
    except Exception as e:
        return f"❌ Error MySQL: {e}", 500

# Manejo de errores
@app.errorhandler(404)
def not_found(error):
    return "Ruta no encontrada"

# Decorador de login
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


# Página principal
@app.route('/')
def mostrar_inicio():
    habilidades = query_all("SELECT * FROM habilidades")
    return render_template('index.html', index=True, habilidades=habilidades)

# Formulario de contacto
@app.route("/Formulario", methods=["GET", "POST"])
def contacto():
    if request.method == "POST":
        Nombre = request.form["name"]
        Correo = request.form["email"]
        Telefono = request.form["phone"]
        Mensaje = request.form["mensaje"]

        insertar = "INSERT INTO contacto (Nombre, Correo, Telefono, Mensaje) VALUES (%s, %s, %s, %s)"
        execute(insertar, (Nombre, Correo, Telefono, Mensaje))
        return render_template("Formulario.html", msg="Mensaje enviado correctamente", Formulario=True)

    return render_template("Formulario.html", msg="", Formulario=True)

# Acerca de mí
@app.route("/acercademi")
def acercademi():
    info= query_one("SELECT id, Perfil, PerfilPro, XP, fecha_nacimiento, TIMESTAMPDIFF(YEAR, fecha_nacimiento, CURDATE()) AS edad FROM informacion WHERE id=1")
    return render_template("Acerca-de-mi.html", Acerca_de_mi=True, info=info)

# Proyectos
@app.route("/Proyectos")
def proyectos():
    Mproyectos = query_all("SELECT * FROM proyectos")
    return render_template("Proyectos.html", Proyectos=True, Mproyectos=Mproyectos)

# Comentarios (protegido)
@app.route('/comentarios', methods=['GET', 'POST'])
@login_required
def comentarios():
    mensajes = query_all("SELECT * FROM contacto")
    return render_template('admin/comentarios.html', mensajes=mensajes, comentarios=True)

# Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    mensaje = ''
    if request.method == 'POST':
        usuario = request.form['usuario']
        password = request.form['password']

        row = query_one("SELECT * FROM usuarios WHERE usuario = %s AND password = %s", (usuario, password))
        if row:
            session["usuario"] = row["usuario"]
            return redirect('/admin')
        else:
            mensaje = "Usuario o contraseña incorrecta"

    return render_template('login.html', mensaje=mensaje)

# Logout
@app.route('/logout')
def logout():
    session.pop("usuario", None)
    return redirect('/login')

# Panel admin (protegido)
@app.route("/admin")
@login_required
def admin():
    return render_template("admin/admin.html", admin=True)

# Gestión de habilidades (protegido)
@app.route("/skills", methods=["GET", "POST"])
@login_required
def skills():
    if request.method == "POST":
        Nombre = request.form["habilidad"]
        Descripcion = request.form["descripcion"]
        Svg = request.form["svg"]
        insertar = "INSERT INTO habilidades (Nombre, Descripcion, Svg) VALUES (%s, %s, %s)"
        execute(insertar, (Nombre, Descripcion, Svg))
        return redirect(url_for('skills'))

    habilidades = query_all("SELECT * FROM habilidades")
    return render_template("admin/habilidades.html", msg="", skills=True, habilidades=habilidades)

# Eliminar habilidad (protegido)
@app.route("/eliminar_habilidad", methods=["POST"])
@login_required
def eliminar_habilidad():
    id_ = request.form["id"]
    try:
        execute("DELETE FROM habilidades WHERE id = %s", (id_,))
        print("Habilidad eliminada con ID:", id_)
    except Exception as e:
        print("Error al eliminar:", e)
    return redirect("/skills")

# Admin proyectos (protegido)
@app.route("/Admin_proyectos", methods=["GET", "POST"])
@login_required
def IntroducirProyectos():
    if request.method == "POST":
        Nombre = request.form["titulo"]
        Descripcion = request.form["descripcionproyecto"]
        Svg = request.form["svgproyecto"]
        link = request.form["link"]
        insertar = "INSERT INTO proyectos (Nombre, Descripcion, Svg, link) VALUES (%s, %s, %s, %s)"
        execute(insertar, (Nombre, Descripcion, Svg, link))
        return redirect("/Admin_proyectos")

    proyectos = query_all("SELECT * FROM proyectos")
    return render_template("admin/Adminproyectos.html", msg="", adminproyectos=True, proyectos=proyectos)

# Eliminar proyecto (protegido)
@app.route("/eliminar_proyecto", methods=["POST"])
@login_required
def eliminar_proyecto():
    id_ = request.form["id"]
    try:
        execute("DELETE FROM proyectos WHERE id = %s", (id_,))
        print("Proyecto eliminado con ID:", id_)
    except Exception as e:
        print("Error al eliminar:", e)
    return redirect("/Admin_proyectos")


@app.route("/eliminar_comentario", methods=["POST"])
@login_required
def eliminar_comentario():
    id_ = request.form["id"]
    try:
        execute("DELETE FROM contacto WHERE id = %s", (id_,))
        print("Contacto eliminado con ID:", id_)
    except Exception as e:
        print("Error al eliminar:", e)
    return redirect("/comentarios")


@app.route("/modificar", methods=["GET", "POST"])
@login_required
def modificarh():
    if request.method == "POST":
        id_ = int(request.form["id"])
        nombre = request.form.get("nombreeditar") or request.form.get("habilidad")
        descripcion = request.form.get("descripcion", "")
        svg = request.form.get("svg", "")

        execute(
            "UPDATE habilidades SET Nombre=%s, Descripcion=%s, Svg=%s WHERE id=%s",
            (nombre, descripcion, svg, id_)
        )
        return redirect(url_for("skills"))

    id_ = request.args.get("id", type=int)
    if id_ is None:
        return redirect(url_for("skills"))

    h = query_one("SELECT id, Nombre, Descripcion, Svg FROM habilidades WHERE id=%s", (id_,))
    if not h:
        return "Habilidad no encontrada", 404

    return render_template("admin/modificarhabilidad.html", h=h)

@app.route("/modificarp", methods=["GET", "POST"])
@login_required
def modificarp():
    if request.method == "POST":
        id_ = int(request.form["id"])
        nombre = request.form.get("nombreeditar") or request.form.get("habilidad")
        descripcion = request.form.get("descripcion", "")
        svg = request.form.get("svg", "")
        link = request.form.get("link", "")

        execute(
            "UPDATE proyectos SET Nombre=%s, Descripcion=%s, Svg=%s, Link=%s WHERE id=%s",
            (nombre, descripcion, svg, link, id_)
        )
        return redirect("Admin_proyectos")

    id_ = request.args.get("id", type=int)
    if id_ is None:
        return redirect("Admin_proyectos")

    h = query_one("SELECT id, Nombre, Descripcion, Svg, link FROM proyectos WHERE id=%s", (id_,))
    if not h:
        return "proyecto no encontrada", 404

    return render_template("admin/modificarproyectos.html", h=h)


@app.route("/Informacion_personal", methods=["GET", "POST"])
@login_required
def Informacion():
    if request.method == "POST":
        Perfil = request.form.get("Perfil") or request.form.get("Perfil")
        PerfilPro = request.form.get("PerfilPro", "")
        Xp = request.form.get("XP", "")
        fechaNac = request.form.get("fechaNac", "")

        execute("UPDATE informacion SET Perfil=%s, PerfilPro=%s, XP=%s, fecha_nacimiento=%s WHERE id=1", (Perfil, PerfilPro, Xp, fechaNac))
        return redirect("Informacion_personal")


    h = query_one("SELECT id, Perfil, PerfilPro, XP, fecha_nacimiento, TIMESTAMPDIFF(YEAR, fecha_nacimiento, CURDATE()) AS edad FROM informacion WHERE id=1")
    if not h:
        return "proyecto no encontrada", 404

    return render_template("admin/InformacionPersonal.html", h=h, modip=True)




# Ejecutar la app
if __name__ == '__main__':
    app.run(host="127.0.0.1", port=7777, debug=True)

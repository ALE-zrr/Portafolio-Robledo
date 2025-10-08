# -*- coding: utf-8 -*-
# Conexión a base de datos MySQL con pool de conexiones
import os
import mysql.connector
from mysql.connector.pooling import MySQLConnectionPool
from pathlib import Path
from dotenv import load_dotenv, find_dotenv, dotenv_values

paths = [
    Path(__file__).resolve().parent / ".env",
    Path(__file__).resolve().parent.parent / ".env",
    Path.cwd() / ".env",
]
dotenv_path = next((p for p in paths if p.exists()), None) or find_dotenv()
if dotenv_path:
    load_dotenv(dotenv_path, override=True, encoding="utf-8-sig")
    print("Cargando .env desde:", dotenv_path)
    print("ENV leídas:", {k: "✓" for k in dotenv_values(dotenv_path, encoding="utf-8-sig").keys()})
else:
    print("No se encontró .env")

def _getenv(name, default=None):
    v = os.getenv(name)
    return v if v not in (None, "", "None") else default

def _require(name: str) -> str:
    v = os.getenv(name)
    if v is None or str(v).strip() == "":
        raise RuntimeError(f"Falta la variable de entorno {name} en tu .env")
    return v

# No calcular DB_CONFIG ni crear el pool en el import; haremos la inicialización perezosa
_pool = None

def _ensure_pool():
    """Crea el pool si no existe. Lanza RuntimeError si faltan variables obligatorias."""
    global _pool
    if _pool is not None:
        return

    # Recalcular DB_CONFIG en tiempo de ejecución por si cambió .env
    cfg = {
        "host": _require("DB_HOST"),
        "port": int(_require("DB_PORT")),
        "user": _require("DB_USER"),
        "password": _require("DB_PASSWORD"),
        "database": _require("DB_NAME"),
        "auth_plugin": _getenv("DB_AUTH_PLUGIN", "caching_sha2_password"),
        "charset": _getenv("DB_CHARSET", "utf8mb4"),
        "use_pure": True,
        "connection_timeout": int(_getenv("DB_TIMEOUT", "10")),
    }

    try:
        _pool = MySQLConnectionPool(pool_name="main_pool", pool_size=5, **cfg)
    except Exception as e:
        # Hacer explícito el error para que la aplicación lo pueda mostrar
        raise RuntimeError(f"No se pudo crear el pool de conexiones: {e}")


def connection():
    """Obtiene una conexión del pool (debes cerrarla tras usarla)."""
    _ensure_pool()
    conn = _pool.get_connection()
    conn.autocommit = True
    from os import getenv
    collation = getenv("DB_COLLATION", "utf8mb4_spanish_ci")
    # Leer el charset actual de las variables de entorno
    from os import getenv as _getenv_local
    charset = _getenv_local("DB_CHARSET") or "utf8mb4"
    with conn.cursor() as cur:
        cur.execute(f"SET NAMES {charset} COLLATE {collation};")
    return conn

def execute(sql, params=None):
    """INSERT/UPDATE/DELETE -> filas afectadas"""
    conn = connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params or ())
            affected = cur.rowcount
            # Aseguramos commit explícito para evitar que los cambios se pierdan
            try:
                conn.commit()
            except Exception:
                # Si la conexión está en autocommit True, commit puede fallar; ignoramos
                pass
        return affected
    except Exception as e:
        print("SQL ERROR:", e, "| SQL:", sql, "| params:", params)
        raise
    finally:
        conn.close()


def query_all(sql, params=None, dict_cursor=True):
    """SELECT * -> lista de filas"""
    conn = connection()
    try:
        with conn.cursor(dictionary=dict_cursor) as cur:
            cur.execute(sql, params or ())
            rows = cur.fetchall()
        conn.commit()
        return rows
    finally:
        conn.close()

def query_one(sql, params=None, dict_cursor=True):
    """SELECT una fila"""
    conn = connection()
    try:
        with conn.cursor(dictionary=dict_cursor) as cur:
            cur.execute(sql, params or ())
            row = cur.fetchone()
        conn.commit()
        return row
    finally:
        conn.close()
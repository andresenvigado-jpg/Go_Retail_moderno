import psycopg2
from psycopg2 import sql
import os
from dotenv import load_dotenv

# ─────────────────────────────────────────
# Carga variables de entorno desde .env
# ─────────────────────────────────────────
load_dotenv()

DB_HOST     = os.getenv("DB_HOST")
DB_NAME     = os.getenv("DB_NAME")
DB_USER     = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_PORT     = os.getenv("DB_PORT", "5432")

# ─────────────────────────────────────────
# Conexión a Go_BD en Neon
# ─────────────────────────────────────────
def conectar():
    return psycopg2.connect(
        host=DB_HOST,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        port=DB_PORT,
        sslmode="require"
    )

# ─────────────────────────────────────────
# Definición de tablas
# ─────────────────────────────────────────
TABLAS = {

    "catalogos": """
        CREATE TABLE IF NOT EXISTS catalogos (
            id                      SERIAL PRIMARY KEY,
            name                    VARCHAR(255),
            description             TEXT,
            product_id              VARCHAR(100),
            product_name            VARCHAR(255),
            product_description     TEXT,
            categories              VARCHAR(255),
            brands                  VARCHAR(255),
            pack_constraint         INTEGER,
            wh_pack_constraint      INTEGER,
            pictures                TEXT,
            price                   NUMERIC(12, 2),
            price_currency          VARCHAR(10),
            cost                    NUMERIC(12, 2),
            cost_currency           VARCHAR(10),
            colors                  VARCHAR(255),
            markets                 VARCHAR(255),
            seasons                 VARCHAR(100),
            styles                  VARCHAR(255),
            size                    VARCHAR(50),
            department_name         VARCHAR(255),
            department_id           VARCHAR(100),
            avoid_replenishment     BOOLEAN DEFAULT FALSE,
            custom_tipolinea        VARCHAR(100),
            custom_bota             VARCHAR(100),
            custom_tiro             VARCHAR(100),
            custom_año              INTEGER,
            custom_mes              INTEGER,
            transaction_date_process TIMESTAMP
        );
    """,

    "inventarios": """
        CREATE TABLE IF NOT EXISTS inventarios (
            id                      SERIAL PRIMARY KEY,
            location_id             VARCHAR(100),
            sku_id                  VARCHAR(100),
            source_location_id      VARCHAR(100),
            transit_qty             NUMERIC(12, 2) DEFAULT 0,
            site_qty                NUMERIC(12, 2) DEFAULT 0,
            reserved_qty            NUMERIC(12, 2) DEFAULT 0,
            min_stock               NUMERIC(12, 2),
            max_stock               NUMERIC(12, 2),
            replenishment_lead_time INTEGER,
            status_date             DATE,
            avoid_replenishment     BOOLEAN DEFAULT FALSE,
            transaction_date_process TIMESTAMP
        );
    """,

    "transacciones": """
        CREATE TABLE IF NOT EXISTS transacciones (
            id                      SERIAL PRIMARY KEY,
            receipt_id              VARCHAR(100),
            sku_id                  VARCHAR(100),
            source_location_id      VARCHAR(100),
            target_location_id      VARCHAR(100),
            quantity                NUMERIC(12, 2),
            sale_price              NUMERIC(12, 2),
            currency                VARCHAR(10),
            type                    VARCHAR(50),
            transaction_date        TIMESTAMP,
            transaction_date_process TIMESTAMP
        );
    """,

    "tiendas": """
        CREATE TABLE IF NOT EXISTS tiendas (
            id                              SERIAL PRIMARY KEY,
            name                            VARCHAR(255),
            description                     TEXT,
            city                            VARCHAR(100),
            region                          VARCHAR(100),
            brands                          VARCHAR(255),
            type                            VARCHAR(100),
            classifications                 VARCHAR(255),
            default_replenishment_lead_time INTEGER,
            avoid_replenishment             BOOLEAN DEFAULT FALSE,
            custom_formato                  VARCHAR(100),
            custom_clima                    VARCHAR(100),
            custom_zona                     VARCHAR(100),
            custom_colortienda              VARCHAR(50),
            transaction_date_process        TIMESTAMP
        );
    """
}

# ─────────────────────────────────────────
# Crear tablas
# ─────────────────────────────────────────
def crear_tablas():
    conn = None
    try:
        print("Conectando a Go_BD en Neon...")
        conn = conectar()
        cursor = conn.cursor()

        for nombre, ddl in TABLAS.items():
            print(f"  Creando tabla: {nombre}...")
            cursor.execute(ddl)

        conn.commit()
        print("\n✅ Todas las tablas fueron creadas exitosamente en Go_BD.")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            cursor.close()
            conn.close()
            print("Conexión cerrada.")

# ─────────────────────────────────────────
# Ejecutar
# ─────────────────────────────────────────
if __name__ == "__main__":
    crear_tablas()

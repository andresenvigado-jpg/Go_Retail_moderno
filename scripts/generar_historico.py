import psycopg2
import os
import random
from datetime import datetime, timedelta
from dotenv import load_dotenv

# ─────────────────────────────────────────
# Conexión
# ─────────────────────────────────────────
load_dotenv()

def conectar():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        port=os.getenv("DB_PORT", "5432"),
        sslmode="require"
    )

# ─────────────────────────────────────────
# Datos base para generación sintética
# ─────────────────────────────────────────

CIUDADES = ["Bogotá", "Medellín", "Cali", "Barranquilla", "Bucaramanga",
            "Pereira", "Manizales", "Cartagena", "Santa Marta", "Cúcuta"]

CLIMAS   = ["frío", "templado", "cálido", "tropical"]
ZONAS    = ["norte", "sur", "centro", "oriente", "occidente"]
FORMATOS = ["grande", "mediano", "pequeño", "express"]

CATEGORIAS   = ["Pantalones", "Camisas", "Zapatos", "Botas", "Accesorios", "Ropa Interior", "Deportivo"]
MARCAS       = ["MarcaA", "MarcaB", "MarcaC", "MarcaD"]
TEMPORADAS   = ["verano", "invierno", "primavera", "otoño"]
TALLAS       = ["XS", "S", "M", "L", "XL", "XXL"]
TIPOS_LINEA  = ["básica", "premium", "outlet"]
TIPOS_BOTA   = ["alta", "media", "baja", "ninguna"]
TIPOS_TIRO   = ["alto", "medio", "bajo", "ninguno"]
TIPO_TRANSAC = ["venta", "reposicion", "devolucion", "traslado"]

# ─────────────────────────────────────────
# 1. Generar Tiendas
# ─────────────────────────────────────────
def generar_tiendas(cursor, n=20):
    print(f"  Generando {n} tiendas...")
    tiendas = []
    for i in range(1, n + 1):
        ciudad  = random.choice(CIUDADES)
        clima   = random.choice(CLIMAS)
        zona    = random.choice(ZONAS)
        formato = random.choice(FORMATOS)
        lead    = random.randint(1, 7)

        cursor.execute("""
            INSERT INTO tiendas (
                name, description, city, region, brands, type,
                classifications, default_replenishment_lead_time,
                avoid_replenishment, custom_formato, custom_clima,
                custom_zona, custom_colortienda, transaction_date_process
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            RETURNING id
        """, (
            f"Tienda_{i:03d}",
            f"Punto de venta {i} en {ciudad}",
            ciudad,
            zona,
            random.choice(MARCAS),
            formato,
            random.choice(["A", "B", "C"]),
            lead,
            False,
            formato,
            clima,
            zona,
            f"color_{random.randint(1,5)}",
            datetime.now()
        ))
        tienda_id = cursor.fetchone()[0]
        tiendas.append({"id": tienda_id, "clima": clima, "zona": zona})

    print(f"  ✅ {n} tiendas creadas.")
    return tiendas

# ─────────────────────────────────────────
# 2. Generar Catálogo
# ─────────────────────────────────────────
def generar_catalogos(cursor, n=200):
    print(f"  Generando {n} productos en catálogo...")
    skus = []
    for i in range(1, n + 1):
        categoria = random.choice(CATEGORIAS)
        precio    = round(random.uniform(30000, 350000), 2)
        costo     = round(precio * random.uniform(0.4, 0.65), 2)
        año       = random.randint(2023, 2024)
        mes       = random.randint(1, 12)

        cursor.execute("""
            INSERT INTO catalogos (
                name, description, product_id, product_name, product_description,
                categories, brands, pack_constraint, wh_pack_constraint,
                price, price_currency, cost, cost_currency,
                colors, markets, seasons, styles, size,
                department_name, department_id, avoid_replenishment,
                custom_tipolinea, custom_bota, custom_tiro,
                custom_año, custom_mes, transaction_date_process
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            RETURNING id
        """, (
            f"SKU_{i:04d}",
            f"Producto {categoria} referencia {i}",
            f"PROD_{i:04d}",
            f"{categoria} Ref{i}",
            f"Descripción detallada del producto {i}",
            categoria,
            random.choice(MARCAS),
            random.randint(1, 6),
            random.randint(6, 24),
            precio,
            "COP",
            costo,
            "COP",
            random.choice(["negro", "blanco", "azul", "rojo", "gris"]),
            "Colombia",
            random.choice(TEMPORADAS),
            random.choice(["casual", "formal", "sport"]),
            random.choice(TALLAS),
            categoria,
            f"DEPT_{random.randint(1,7):02d}",
            False,
            random.choice(TIPOS_LINEA),
            random.choice(TIPOS_BOTA),
            random.choice(TIPOS_TIRO),
            año,
            mes,
            datetime.now()
        ))
        sku_id = cursor.fetchone()[0]
        skus.append(sku_id)

    print(f"  ✅ {n} productos creados.")
    return skus

# ─────────────────────────────────────────
# 3. Generar Inventarios
# ─────────────────────────────────────────
def generar_inventarios(cursor, tiendas, skus):
    print(f"  Generando inventarios ({len(tiendas)} tiendas x {len(skus)} SKUs)...")
    count = 0
    for tienda in tiendas:
        # Cada tienda maneja entre 50 y 100 SKUs del catálogo
        skus_tienda = random.sample(skus, k=random.randint(50, min(100, len(skus))))
        for sku_id in skus_tienda:
            min_stock = random.randint(2, 10)
            max_stock = min_stock * random.randint(3, 8)
            site_qty  = random.randint(0, max_stock)

            cursor.execute("""
                INSERT INTO inventarios (
                    location_id, sku_id, source_location_id,
                    transit_qty, site_qty, reserved_qty,
                    min_stock, max_stock, replenishment_lead_time,
                    status_date, avoid_replenishment, transaction_date_process
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (
                str(tienda["id"]),
                str(sku_id),
                "BODEGA_CENTRAL",
                random.randint(0, 5),
                site_qty,
                random.randint(0, 2),
                min_stock,
                max_stock,
                random.randint(1, 7),
                datetime.now().date(),
                False,
                datetime.now()
            ))
            count += 1

    print(f"  ✅ {count} registros de inventario creados.")

# ─────────────────────────────────────────
# 4. Generar Transacciones (Histórico 12 meses)
# ─────────────────────────────────────────
def generar_transacciones(cursor, tiendas, skus, meses=12):
    print(f"  Generando historial de transacciones ({meses} meses)...")

    fecha_inicio = datetime.now() - timedelta(days=30 * meses)
    fecha_actual = datetime.now()
    total        = 0
    fecha        = fecha_inicio

    # Meses con temporada alta (mayor volumen de ventas)
    temporada_alta = [1, 2, 6, 7, 10, 11, 12]

    while fecha <= fecha_actual:
        mes_actual = fecha.month

        # Más transacciones en temporada alta
        ventas_dia = random.randint(15, 30) if mes_actual in temporada_alta else random.randint(5, 15)

        for _ in range(ventas_dia):
            tienda = random.choice(tiendas)
            sku_id = random.choice(skus)
            tipo   = random.choices(
                TIPO_TRANSAC,
                weights=[70, 15, 10, 5]  # ventas son el 70%
            )[0]

            precio_venta = round(random.uniform(30000, 350000), 2)
            cantidad     = random.randint(1, 5) if tipo == "venta" else random.randint(5, 30)

            cursor.execute("""
                INSERT INTO transacciones (
                    receipt_id, sku_id, source_location_id, target_location_id,
                    quantity, sale_price, currency, type,
                    transaction_date, transaction_date_process
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (
                f"REC_{total:08d}",
                str(sku_id),
                "BODEGA_CENTRAL",
                str(tienda["id"]),
                cantidad,
                precio_venta if tipo == "venta" else 0,
                "COP",
                tipo,
                fecha,
                datetime.now()
            ))
            total += 1

        fecha += timedelta(days=1)

    print(f"  ✅ {total:,} transacciones históricas creadas.")

# ─────────────────────────────────────────
# Ejecutar todo
# ─────────────────────────────────────────
def main():
    conn = None
    try:
        print("\n🔌 Conectando a Go_BD en Neon...")
        conn = conectar()
        cursor = conn.cursor()
        print("✅ Conexión exitosa.\n")

        print("📦 Iniciando generación de data sintética...\n")

        tiendas = generar_tiendas(cursor, n=20)
        conn.commit()

        skus = generar_catalogos(cursor, n=200)
        conn.commit()

        generar_inventarios(cursor, tiendas, skus)
        conn.commit()

        generar_transacciones(cursor, tiendas, skus, meses=12)
        conn.commit()

        print("\n🎉 Data sintética generada exitosamente en Go_BD.")
        print("   Tablas pobladas: tiendas, catalogos, inventarios, transacciones")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            cursor.close()
            conn.close()
            print("🔒 Conexión cerrada.")

if __name__ == "__main__":
    main()

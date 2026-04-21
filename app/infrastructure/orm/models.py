from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Boolean, Column, DateTime, Float, Integer,
    String, Text, ForeignKey, Date, func,
)
from app.config.database import Base


# ─────────────────────────────────────────────────────────────────
# AUTENTICACIÓN
# ─────────────────────────────────────────────────────────────────

class UsuarioORM(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    rol = Column(String(20), default="viewer")        # admin | analyst | viewer
    activo = Column(Boolean, default=True)
    creado_en = Column(DateTime(timezone=True), server_default=func.now())
    ultimo_acceso = Column(DateTime(timezone=True), nullable=True)


# ─────────────────────────────────────────────────────────────────
# TABLAS BASE
# ─────────────────────────────────────────────────────────────────

class CatalogoORM(Base):
    """Esquema real: sku_id = id::VARCHAR (no existe columna sku_id en la tabla)."""
    __tablename__ = "catalogos"

    id = Column(Integer, primary_key=True)          # usado como sku_id en los modelos ML
    name = Column(String, nullable=True)
    product_id = Column(String, nullable=True)
    categories = Column(String, nullable=True)       # categoria
    brands = Column(String, nullable=True)           # marca
    price = Column(Float, nullable=True)
    cost = Column(Float, nullable=True)
    seasons = Column(String, nullable=True)
    size = Column(String, nullable=True)
    department_name = Column(String, nullable=True)
    custom_tipolinea = Column(String, nullable=True)
    avoid_replenishment = Column(Boolean, default=False)


class TiendaORM(Base):
    """Esquema real: tienda_id = id::VARCHAR."""
    __tablename__ = "tiendas"

    id = Column(Integer, primary_key=True)          # usado como tienda_id en los modelos ML
    name = Column(String, nullable=True)
    city = Column(String, nullable=True)
    region = Column(String, nullable=True)
    brands = Column(String, nullable=True)
    custom_formato = Column(String, nullable=True)
    custom_clima = Column(String, nullable=True)
    custom_zona = Column(String, nullable=True)
    default_replenishment_lead_time = Column(Integer, nullable=True)


class InventarioORM(Base):
    __tablename__ = "inventarios"

    id = Column(Integer, primary_key=True)
    location_id = Column(String, index=True)
    sku_id = Column(String, index=True)
    site_qty = Column(Float, default=0)
    transit_qty = Column(Float, default=0)
    reserved_qty = Column(Float, default=0)
    min_stock = Column(Float, nullable=True)
    max_stock = Column(Float, nullable=True)
    replenishment_lead_time = Column(Integer, nullable=True)
    avoid_replenishment = Column(Boolean, default=False)


class TransaccionORM(Base):
    __tablename__ = "transacciones"

    id = Column(Integer, primary_key=True)
    receipt_id = Column(String, index=True)
    sku_id = Column(String, index=True)
    type = Column(String)                        # venta, reposicion, devolucion, traslado
    source_location_id = Column(String, nullable=True)
    target_location_id = Column(String, nullable=True)
    quantity = Column(Float)
    sale_price = Column(Float, nullable=True)
    transaction_date = Column(Date, index=True)


# ─────────────────────────────────────────────────────────────────
# TABLAS DE RESULTADOS ML
# ─────────────────────────────────────────────────────────────────

class PronosticoORM(Base):
    __tablename__ = "pronosticos"

    # PK compuesta — creada por pandas to_sql sin id serial
    sku_id = Column(String, primary_key=True)
    fecha  = Column(Date,   primary_key=True)
    demanda_estimada = Column(Float)
    demanda_minima = Column(Float)
    demanda_maxima = Column(Float)


class PrediccionLGBMORM(Base):
    __tablename__ = "predicciones_lgbm"

    # PK compuesta — creada por pandas to_sql sin id serial
    sku_id    = Column(String, primary_key=True)
    tienda_id = Column(String, primary_key=True)
    cantidad_real = Column(Float, nullable=True)
    cantidad_predicha = Column(Float)


class SegmentacionSKUORM(Base):
    __tablename__ = "segmentacion_skus"

    # PK simple — creada por pandas to_sql sin id serial
    sku_id = Column(String, primary_key=True)
    participacion = Column(Float)
    acumulado = Column(Float)
    segmento_abc = Column(String)


class SegmentacionTiendaORM(Base):
    __tablename__ = "segmentacion_tiendas"

    # PK simple — creada por pandas to_sql sin id serial
    tienda_id = Column(String, primary_key=True)
    ventas_totales = Column(Float)
    venta_promedio = Column(Float)
    num_skus = Column(Integer)
    segmento_tienda = Column(String)


class AnomaliaORM(Base):
    __tablename__ = "anomalias_inventario"

    # PK compuesta — la tabla fue creada por pandas to_sql sin columna id serial
    sku_id    = Column(String, primary_key=True)
    tienda_id = Column(String, primary_key=True)
    tipo_anomalia = Column(String)
    es_anomalia = Column(Boolean)
    score_anomalia = Column(Float)
    # La tabla en BD tiene la columna "site_qty"; se expone como "stock_actual" en Python
    stock_actual = Column("site_qty", Float, nullable=True)
    cobertura_dias = Column(Float, nullable=True)


class EOQResultadoORM(Base):
    __tablename__ = "eoq_resultados"

    # PK compuesta — la tabla fue creada por pandas to_sql sin columna id serial
    sku_id    = Column(String, primary_key=True)
    tienda_id = Column(String, primary_key=True)
    eoq = Column(Float)
    punto_reorden = Column(Float)
    stock_seguridad = Column(Float)
    estado_reposicion = Column(String)
    dias_entre_pedidos = Column(Float, nullable=True)
    # La tabla en BD tiene la columna "costo_total_optimizado"; se expone como "costo_total_anual"
    costo_total_anual = Column("costo_total_optimizado", Float, nullable=True)


class MarketBasketORM(Base):
    __tablename__ = "market_basket"

    # PK compuesta — creada por pandas to_sql sin id serial
    sku_origen = Column(String, primary_key=True)
    sku_destino = Column(String, primary_key=True)
    soporte = Column(Float)
    confianza = Column(Float)
    lift = Column(Float)
    conviction = Column(Float, nullable=True)


class MonteCarloORM(Base):
    __tablename__ = "monte_carlo"

    # PK compuesta — creada por pandas to_sql sin id serial
    sku_id    = Column(String, primary_key=True)
    tienda_id = Column(String, primary_key=True)
    demanda_p50 = Column(Float)
    demanda_p90 = Column(Float)
    demanda_p95 = Column(Float)
    demanda_p99 = Column(Float)
    prob_quiebre = Column(Float)
    stock_recomendado = Column(Float)
    nivel_riesgo = Column(String)


class RentabilidadSKUORM(Base):
    __tablename__ = "rentabilidad_sku"

    # PK compuesta — tabla tiene una fila por SKU+tienda
    sku_id    = Column(String, primary_key=True)
    tienda_id = Column(String, primary_key=True)
    margen_porcentual = Column(Float)
    rentabilidad_total = Column(Float)
    indice_rentabilidad = Column(Float)
    clasificacion = Column(String)


class RotacionSKUORM(Base):
    __tablename__ = "rotacion_sku"

    # PK compuesta — tabla tiene una fila por SKU+tienda
    sku_id    = Column(String, primary_key=True)
    tienda_id = Column(String, primary_key=True)
    tasa_rotacion_anual = Column(Float)
    dsi = Column(Float)
    frecuencia_venta = Column(Float)
    indice_velocidad = Column(Float)
    # BD usa "clasificacion_rotacion"; Python lo expone como "clasificacion"
    clasificacion = Column("clasificacion_rotacion", String)


class EficienciaReposicionORM(Base):
    __tablename__ = "eficiencia_reposicion"

    # PK simple — una fila por tienda
    tienda_id = Column(String, primary_key=True)
    cobertura_reposicion = Column(Float)
    tasa_devolucion = Column(Float)
    eficiencia_skus = Column(Float, nullable=True)
    indice_eficiencia = Column(Float)
    # BD usa "clasificacion_eficiencia"; Python lo expone como "clasificacion"
    clasificacion = Column("clasificacion_eficiencia", String)


class LogCargaORM(Base):
    __tablename__ = "log_cargas"

    id = Column(Integer, primary_key=True)
    fecha_ejecucion = Column(DateTime(timezone=True), server_default=func.now())
    tipo = Column(String)
    registros_nuevos = Column(Integer)
    detalle = Column(Text, nullable=True)

# 📦 Go Retail — Tablero de Abastecimiento

> Sistema de inteligencia para el abastecimiento de puntos de venta en el sector retail colombiano.
> Combina modelos de machine learning con una base de datos en la nube para generar pronósticos de demanda, detectar anomalías, optimizar pedidos y simular escenarios de riesgo.

**Versión:** 2.0 | **Fecha:** Abril 2026

---

## Tabla de contenido

1. [Descripción general](#1-descripción-general)
2. [Arquitectura del sistema](#2-arquitectura-del-sistema)
3. [Base de datos — Go_BD](#3-base-de-datos--go_bd)
4. [Modelos de Machine Learning](#4-modelos-de-machine-learning)
5. [Gestión de data](#5-gestión-de-data)
6. [Estructura del proyecto](#6-estructura-del-proyecto)
7. [Cómo interpretar el tablero](#7-cómo-interpretar-el-tablero)
8. [Instalación y ejecución local](#8-instalación-y-ejecución-local)
9. [Publicación en Streamlit Cloud](#9-publicación-en-streamlit-cloud)
10. [Librerías utilizadas](#10-librerías-utilizadas)

---

## 1. Descripción general

Go Retail es un sistema de inteligencia para el abastecimiento de puntos de venta en el sector retail colombiano. El sistema se actualiza dos veces por semana de forma automática y presenta los resultados en un tablero interactivo accesible desde cualquier navegador.

El proyecto está diseñado para:

- Pronosticar la demanda por producto y tienda
- Detectar quiebres de stock y riesgos de reposición
- Segmentar productos y tiendas por comportamiento de ventas
- Calcular la cantidad óptima de pedido por SKU (EOQ)
- Detectar productos que se compran juntos (Market Basket)
- Simular miles de escenarios de riesgo de quiebre (Monte Carlo)
- Actualizar la información de forma incremental sin intervención manual

---

## 2. Arquitectura del sistema

### 2.1 Componentes principales

| Componente | Tecnología | Función |
|---|---|---|
| Base de datos | PostgreSQL en Neon | Almacenamiento de toda la data |
| Modelos ML | Python (Prophet, LightGBM, Scikit-learn, mlxtend) | Pronósticos, segmentación y optimización |
| Tablero | Streamlit + Plotly | Visualización de indicadores |
| Publicación | Streamlit Community Cloud | Acceso web sin servidor propio |
| Control de versiones | GitHub | Repositorio del código fuente |

### 2.2 Flujo de datos

```
Carga histórica inicial (12 meses)
        ↓
Go_BD en Neon PostgreSQL
        ↓
Modelos ML
  ├── Prophet          → pronósticos de demanda
  ├── LightGBM         → predicción por tienda
  ├── K-Means / ABC    → segmentación
  ├── Isolation Forest → anomalías
  ├── EOQ              → cantidad óptima de pedido
  ├── Market Basket    → productos que se compran juntos
  └── Monte Carlo      → simulación de riesgo
        ↓
Tablas de resultados en Go_BD
        ↓
Tablero Streamlit (lectura y visualización)
        ↓
Carga incremental automática 2x semana
```

---

## 3. Base de datos — Go_BD

### 3.1 Motor y plataforma

- **Motor:** PostgreSQL
- **Proveedor:** Neon (https://neon.tech)
- **Plan:** Gratuito — 512 MB de almacenamiento
- **Región:** us-east-1 (AWS)
- **Conexión:** SSL requerido (`sslmode=require`)

### 3.2 Cadena de conexión

```
postgresql://usuario:contraseña@host/neondb?sslmode=require
```

Las credenciales se almacenan en el archivo `.env` localmente y como secrets en Streamlit Cloud.

---

### 3.3 Tablas base

#### Tabla: `catalogos`

| Campo | Tipo | Descripción |
|---|---|---|
| id | SERIAL PK | Identificador único del producto |
| name | VARCHAR(255) | Nombre del SKU |
| product_id | VARCHAR(100) | Código de producto |
| categories | VARCHAR(255) | Categoría del producto |
| brands | VARCHAR(255) | Marca |
| price | NUMERIC(12,2) | Precio de venta |
| cost | NUMERIC(12,2) | Costo del producto |
| seasons | VARCHAR(100) | Temporada |
| size | VARCHAR(50) | Talla |
| department_name | VARCHAR(255) | Departamento o línea |
| avoid_replenishment | BOOLEAN | Excluir de reposición automática |
| custom_tipolinea | VARCHAR(100) | Tipo de línea (básica, premium, outlet) |
| custom_año | INTEGER | Año de la colección |
| custom_mes | INTEGER | Mes de la colección |
| transaction_date_process | TIMESTAMP | Fecha de procesamiento |

#### Tabla: `inventarios`

| Campo | Tipo | Descripción |
|---|---|---|
| id | SERIAL PK | Identificador único |
| location_id | VARCHAR(100) | ID de la tienda |
| sku_id | VARCHAR(100) | ID del producto |
| site_qty | NUMERIC(12,2) | Stock disponible en tienda |
| transit_qty | NUMERIC(12,2) | Unidades en tránsito |
| reserved_qty | NUMERIC(12,2) | Unidades reservadas |
| min_stock | NUMERIC(12,2) | Stock mínimo permitido |
| max_stock | NUMERIC(12,2) | Stock máximo permitido |
| replenishment_lead_time | INTEGER | Días de tiempo de reposición |
| status_date | DATE | Fecha del estado del inventario |
| avoid_replenishment | BOOLEAN | Excluir de reposición |

#### Tabla: `transacciones`

| Campo | Tipo | Descripción |
|---|---|---|
| id | SERIAL PK | Identificador único |
| receipt_id | VARCHAR(100) | Número de recibo o documento |
| sku_id | VARCHAR(100) | ID del producto |
| source_location_id | VARCHAR(100) | Origen (bodega central) |
| target_location_id | VARCHAR(100) | Destino (tienda) |
| quantity | NUMERIC(12,2) | Cantidad de unidades |
| sale_price | NUMERIC(12,2) | Precio de venta aplicado |
| currency | VARCHAR(10) | Moneda (COP) |
| type | VARCHAR(50) | Tipo: venta, reposicion, devolucion, traslado |
| transaction_date | TIMESTAMP | Fecha real de la transacción |
| transaction_date_process | TIMESTAMP | Fecha de procesamiento |

#### Tabla: `tiendas`

| Campo | Tipo | Descripción |
|---|---|---|
| id | SERIAL PK | Identificador único |
| name | VARCHAR(255) | Nombre de la tienda |
| city | VARCHAR(100) | Ciudad |
| region | VARCHAR(100) | Región o zona |
| brands | VARCHAR(255) | Marcas que maneja |
| type | VARCHAR(100) | Tipo de formato |
| default_replenishment_lead_time | INTEGER | Lead time por defecto |
| avoid_replenishment | BOOLEAN | Excluir de reposición |
| custom_formato | VARCHAR(100) | Formato: grande, mediano, pequeño, express |
| custom_clima | VARCHAR(100) | Clima: frío, templado, cálido, tropical |
| custom_zona | VARCHAR(100) | Zona geográfica |

---

### 3.4 Tablas generadas por modelos ML

| Tabla | Modelo | Contenido |
|---|---|---|
| pronosticos | Prophet | Demanda estimada por SKU para los próximos 30 días |
| predicciones_lgbm | LightGBM | Predicciones por SKU y tienda con variables contextuales |
| segmentacion_skus | K-Means / ABC | Clasificación de productos por volumen de ventas |
| segmentacion_tiendas | K-Means | Agrupación de tiendas por comportamiento de demanda |
| anomalias_inventario | Isolation Forest | Detección de quiebres, sobrestock y anomalías |
| eoq_resultados | EOQ | Cantidad óptima de pedido, punto de reorden y stock de seguridad |
| market_basket | Apriori | Reglas de asociación entre productos que se compran juntos |
| monte_carlo | Monte Carlo | Simulación de riesgo de quiebre por SKU y tienda |
| log_cargas | Sistema | Historial de ejecuciones de carga incremental |

---

## 4. Modelos de Machine Learning

### 4.1 Prophet — Pronóstico de demanda

Librería de Meta para series de tiempo con estacionalidad.

| Parámetro | Valor |
|---|---|
| SKUs analizados | Top 10 por volumen de ventas |
| Horizonte de pronóstico | 30 días |
| Estacionalidad | Anual y semanal |
| Intervalo de confianza | 95% |

---

### 4.2 LightGBM — Predicción por tienda

Modelo de gradient boosting que incorpora variables contextuales de tienda y producto.

**Precisión del modelo (prototipo):** MAE = 1.23 unidades por predicción.

| Variable influyente | Descripción |
|---|---|
| Costo / Precio | Principal predictor de demanda |
| Lead time | Afecta el comportamiento de pedidos |
| Ciudad | Diferencia el comportamiento por ubicación |
| Talla | Ciertos talles rotan más |
| Clima | Influye en las ventas por temporada |

---

### 4.3 K-Means — Segmentación

- **ABC de SKUs:** alta (A=70%), media (B=20%) y baja (C=10%) rotación.
- **Tiendas:** agrupa por demanda, stock y SKUs activos. Número óptimo de clusters determinado por coeficiente de silhouette.

---

### 4.4 Isolation Forest — Detección de anomalías

Detecta el 10% de registros con comportamiento inusual.

| Tipo | Condición | Acción |
|---|---|---|
| 🔴 Quiebre de stock | Stock < mínimo | Reposición inmediata |
| 🟠 Riesgo de quiebre | Cobertura < lead time | Reposición urgente |
| 🟡 Sobrestock | Stock > 150% del máximo | Revisar pedidos |
| 🔵 Sin movimiento | Stock sin ventas | Evaluar discontinuar |

---

### 4.5 EOQ — Cantidad óptima de pedido

```
EOQ = √(2 × Demanda anual × Costo por pedido / Costo de almacenamiento)
```

| Indicador | Descripción |
|---|---|
| EOQ | Cantidad óptima de unidades por pedido |
| Stock de seguridad | Colchón ante variaciones (Z=1.65, nivel servicio 95%) |
| Punto de reorden | Momento exacto para hacer el pedido |
| Costo total optimizado | Costo mínimo posible de inventario |
| Estado | 🔴 Pedir ahora / 🟡 Pedir pronto / 🟢 Stock OK |

---

### 4.6 Market Basket Analysis — Productos que se compran juntos

Algoritmo Apriori aplicado sobre los top 50 SKUs más frecuentes.

| Métrica | Descripción |
|---|---|
| Soporte | % de transacciones donde aparecen juntos |
| Confianza | Si compra A, % de probabilidad de comprar B |
| Lift > 1 | Relación real y no casual |
| Lift > 2 | Relación fuerte — abastecer juntos |
| Lift > 3 | Relación muy fuerte — considerar como combo |

---

### 4.7 Monte Carlo — Simulación de riesgo

Simula 1,000 escenarios de demanda por SKU y tienda para los próximos 30 días.

| Indicador | Descripción |
|---|---|
| Demanda P50 | Escenario normal |
| Demanda P90 | Escenario alto |
| Demanda P95 | Escenario crítico para dimensionar stock |
| Prob. quiebre | % de simulaciones donde el stock se agota |
| Stock recomendado | Cantidad para cubrir el 95% de los escenarios |
| Nivel riesgo | 🔴 Alto ≥70% / 🟡 Medio ≥40% / 🟢 Bajo <15% |

---

## 5. Gestión de data

### 5.1 Carga histórica inicial

```bash
python generar_historico.py
```

| Tabla | Registros |
|---|---|
| tiendas | 20 |
| catalogos | 200 productos |
| inventarios | ~1,462 |
| transacciones | ~6,216 |

Temporada alta simulada: enero, febrero, junio, julio, octubre, noviembre y diciembre.

### 5.2 Carga incremental automática

Se ejecuta automáticamente al abrir el tablero. Verifica si ya existe data del día actual y solo carga los días pendientes. También puede ejecutarse manualmente:

```bash
python carga_incremental.py
```

---

## 6. Estructura del proyecto

```
Go_Retail/
├── .env                        # Credenciales de conexión (no se sube a GitHub)
├── .gitignore                  # Archivos excluidos del repositorio
├── requirements.txt            # Librerías Python necesarias
├── README.md                   # Documentación técnica
├── crear_tablas_Go_BD.py       # Crea las 4 tablas base en Go_BD
├── generar_historico.py        # Genera la data sintética histórica
├── carga_incremental.py        # Script de carga incremental manual
├── modelo_pronostico.py        # Modelo Prophet
├── modelo_lightgbm.py          # Modelo LightGBM
├── modelo_segmentacion.py      # Segmentación ABC y K-Means
├── modelo_anomalias.py         # Detección de anomalías Isolation Forest
├── modelo_eoq.py               # Cantidad óptima de pedido EOQ
├── modelo_market_basket.py     # Productos que se compran juntos
├── modelo_monte_carlo.py       # Simulación de riesgo de quiebre
└── tablero.py                  # Tablero Streamlit con carga automática
```

---

## 7. Cómo interpretar el tablero

### 7.1 Barra de estado
- ✅ **Verde:** carga incremental ejecutada. Data actualizada.
- ℹ️ **Azul:** data del día ya cargada. Sin acción necesaria.

### 7.2 Métricas principales
| Indicador | Cuándo actuar |
|---|---|
| Quiebres de stock | Acción inmediata |
| Riesgo de quiebre | Acción urgente |
| Sin movimiento | Revisar viabilidad |

### 7.3 Ventas históricas
Evolución diaria de ventas. Picos altos indican temporada alta.

### 7.4 Pronóstico 30 días
Top 5 SKUs con mayor demanda estimada. Líneas más altas = mayor prioridad de reposición.

### 7.5 Alertas de inventario
- 🔴 Quiebres activos
- 🟠 Riesgos de quiebre
- 🔵 SKUs sin movimiento

### 7.6 Segmentación ABC
- **A:** 70% de ventas — máxima prioridad
- **B:** 20% de ventas — seguimiento regular
- **C:** 10% de ventas — evaluar continuidad

### 7.7 Tiendas por segmento
Alta demanda = prioridad máxima en reposición.

### 7.8 Quiebres de stock
Cobertura en días cercana a cero = emergencia inmediata.

### 7.9 Top SKUs demanda estimada
Color más oscuro = mayor urgencia de abastecimiento.

### 7.10 EOQ
| Estado | Acción |
|---|---|
| 🔴 Pedir ahora | Hacer pedido inmediato |
| 🟡 Pedir pronto | Planificar pedido |
| 🟢 Stock OK | Sin acción requerida |

### 7.11 Market Basket
Lift > 2 = abastecer productos juntos. Lift > 3 = considerar como combo.

### 7.12 Monte Carlo
| Nivel | Probabilidad | Acción |
|---|---|---|
| 🔴 Alto | ≥ 70% | Acción inmediata |
| 🟡 Medio | 40–70% | Monitorear |
| 🟢 Bajo | < 15% | Estable |

Stock recomendado = cantidad para cubrir el 95% de los escenarios simulados.

---

## 8. Instalación y ejecución local

### Requisitos previos
- Python 3.10 o superior
- Git instalado
- Cuenta en Neon (https://neon.tech)
- Visual Studio Code (recomendado)

### Pasos

```bash
git clone https://github.com/andresenvigado-jpg/Go_Retail.git
cd Go_Retail
python -m venv venv
venv\Scripts\activate
python -m pip install -r requirements.txt

# Configurar .env con credenciales de Neon

python crear_tablas_Go_BD.py
python generar_historico.py
python modelo_pronostico.py
python modelo_lightgbm.py
python modelo_segmentacion.py
python modelo_anomalias.py
python modelo_eoq.py
python modelo_market_basket.py
python modelo_monte_carlo.py

python -m streamlit run tablero.py
```

---

## 9. Publicación en Streamlit Cloud

- **Repositorio:** https://github.com/andresenvigado-jpg/Go_Retail
- **Archivo principal:** `tablero.py`
- **Actualización:** automática al hacer `git push`

### Secrets (formato TOML)

```toml
DB_HOST = "ep-tu-host.neon.tech"
DB_NAME = "neondb"
DB_USER = "neondb_owner"
DB_PASSWORD = "tu_contraseña"
DB_PORT = "5432"
```

---

## 10. Librerías utilizadas

| Librería | Versión | Uso |
|---|---|---|
| streamlit | 1.56.0 | Tablero web |
| plotly | 6.7.0 | Gráficos interactivos |
| pandas | 3.0.2 | Manipulación de datos |
| prophet | 1.3.0 | Pronóstico de demanda |
| lightgbm | 4.6.0 | Predicción por tienda |
| scikit-learn | 1.8.0 | Clustering y anomalías |
| mlxtend | 0.24.0 | Market Basket Analysis |
| numpy | 2.4.4 | Simulación Monte Carlo |
| psycopg2-binary | latest | Conexión PostgreSQL |
| sqlalchemy | latest | ORM SQL |
| python-dotenv | latest | Variables de entorno |

---

*Go Retail — Documentación técnica v2.0 — Abril 2026*

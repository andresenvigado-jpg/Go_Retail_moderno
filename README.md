# 📦 Go Retail — Tablero de Abastecimiento

> Sistema de inteligencia para el abastecimiento de puntos de venta en el sector retail.
> Combina modelos de machine learning con una base de datos en la nube para generar pronósticos de demanda, detectar anomalías en inventario y segmentar productos y tiendas.

**Versión:** 1.0 | **Fecha:** Abril 2026

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

Go Retail es un sistema de inteligencia para el abastecimiento de puntos de venta en el sector retail. El sistema se actualiza dos veces por semana de forma automática y presenta los resultados en un tablero interactivo accesible desde cualquier navegador.

El proyecto está diseñado para:

- Pronosticar la demanda por producto y tienda
- Detectar quiebres de stock y riesgos de reposición
- Segmentar productos y tiendas por comportamiento de ventas
- Actualizar la información de forma incremental sin intervención manual

---

## 2. Arquitectura del sistema

### 2.1 Componentes principales

| Componente | Tecnología | Función |
|---|---|---|
| Base de datos | PostgreSQL en Neon | Almacenamiento de toda la data |
| Modelos ML | Python (Prophet, LightGBM, Scikit-learn) | Pronósticos y segmentación |
| Tablero | Streamlit + Plotly | Visualización de indicadores |
| Publicación | Streamlit Community Cloud | Acceso web sin servidor propio |
| Control de versiones | GitHub | Repositorio del código fuente |

### 2.2 Flujo de datos

```
Carga histórica inicial (12 meses)
        ↓
Go_BD en Neon PostgreSQL
        ↓
Modelos ML (Prophet · LightGBM · K-Means · Isolation Forest)
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

### 3.3 Estructura de tablas

#### Tabla: `catalogos`

Almacena el catálogo completo de productos con sus atributos comerciales y logísticos.

| Campo | Tipo | Descripción |
|---|---|---|
| id | SERIAL PK | Identificador único del producto |
| name | VARCHAR(255) | Nombre del SKU |
| product_id | VARCHAR(100) | Código de producto |
| categories | VARCHAR(255) | Categoría del producto |
| brands | VARCHAR(255) | Marca |
| price | NUMERIC(12,2) | Precio de venta |
| cost | NUMERIC(12,2) | Costo del producto |
| seasons | VARCHAR(100) | Temporada (verano, invierno, etc.) |
| size | VARCHAR(50) | Talla |
| department_name | VARCHAR(255) | Departamento o línea |
| avoid_replenishment | BOOLEAN | Excluir de reposición automática |
| custom_tipolinea | VARCHAR(100) | Tipo de línea (básica, premium, outlet) |
| custom_año | INTEGER | Año de la colección |
| custom_mes | INTEGER | Mes de la colección |
| transaction_date_process | TIMESTAMP | Fecha de procesamiento |

---

#### Tabla: `inventarios`

Registra el estado actual del inventario por SKU y punto de venta.

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

---

#### Tabla: `transacciones`

Registra todos los movimientos de productos: ventas, reposiciones, devoluciones y traslados.

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

---

#### Tabla: `tiendas`

Contiene la información de cada punto de venta con sus características geográficas y comerciales.

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

#### Tablas generadas por los modelos ML

| Tabla | Modelo | Contenido |
|---|---|---|
| pronosticos | Prophet | Demanda estimada por SKU para los próximos 30 días |
| predicciones_lgbm | LightGBM | Predicciones por SKU y tienda con variables contextuales |
| segmentacion_skus | K-Means / ABC | Clasificación de productos por volumen de ventas |
| segmentacion_tiendas | K-Means | Agrupación de tiendas por comportamiento de demanda |
| anomalias_inventario | Isolation Forest | Detección de quiebres, sobrestock y anomalías |
| log_cargas | Sistema | Historial de ejecuciones de carga incremental |

---

## 4. Modelos de Machine Learning

### 4.1 Prophet — Pronóstico de demanda

Librería de Meta para series de tiempo con estacionalidad. Entrena un modelo por SKU usando el historial de ventas y genera una proyección para los próximos 30 días.

| Parámetro | Valor |
|---|---|
| SKUs analizados | Top 10 por volumen de ventas |
| Horizonte de pronóstico | 30 días |
| Estacionalidad | Anual y semanal |
| Intervalo de confianza | 95% |
| Output | Tabla `pronosticos` en Go_BD |

---

### 4.2 LightGBM — Predicción por tienda

Modelo de gradient boosting de Microsoft. Enriquece el pronóstico incorporando variables contextuales de tienda y producto para predecir la demanda a nivel SKU-tienda.

| Variable influyente | Descripción |
|---|---|
| Costo / Precio | El valor del producto es el principal predictor |
| Lead time | El tiempo de reposición afecta la demanda |
| Ciudad | La ubicación geográfica diferencia el comportamiento |
| Talla | Ciertos talles rotan más que otros |
| Clima | El clima de la tienda influye en las ventas |
| Temporada | Las épocas del año definen patrones de compra |

**Precisión del modelo (prototipo):** MAE = 1.23 unidades por predicción.

---

### 4.3 K-Means — Segmentación

Algoritmo de clustering de Scikit-learn. Realiza dos segmentaciones independientes:

- **Análisis ABC de SKUs:** clasifica productos en alta (A), media (B) y baja (C) rotación según su participación en las ventas totales.
- **Segmentación de tiendas:** agrupa los puntos de venta por comportamiento de demanda, stock y número de SKUs activos. El número óptimo de clusters se determina automáticamente usando el coeficiente de silhouette.

---

### 4.4 Isolation Forest — Detección de anomalías

Modelo de Scikit-learn para detección de anomalías en inventario. Analiza el 10% de registros con comportamiento inusual y los clasifica en cuatro tipos:

| Tipo de anomalía | Condición | Acción recomendada |
|---|---|---|
| 🔴 Quiebre de stock | Stock por debajo del mínimo | Reposición inmediata |
| 🟠 Riesgo de quiebre | Cobertura menor al lead time | Reposición urgente |
| 🟡 Sobrestock | Stock mayor al 150% del máximo | Revisión de pedidos |
| 🔵 Sin movimiento | Tiene stock pero no registra ventas | Evaluar discontinuar |

---

## 5. Gestión de data

### 5.1 Carga histórica inicial

Se ejecuta una única vez al iniciar el proyecto. Genera 12 meses de data sintética que incluye tiendas, catálogo, inventarios y transacciones históricas.

```bash
python generar_historico.py
```

Simula temporada alta en: enero, febrero, junio, julio, octubre, noviembre y diciembre.

| Tabla | Registros generados |
|---|---|
| tiendas | 20 |
| catalogos | 200 productos |
| inventarios | ~1,462 |
| transacciones | ~6,216 históricas |

---

### 5.2 Carga incremental automática

Se ejecuta automáticamente cada vez que se abre el tablero:

1. Verifica si ya existe data del día actual en `transacciones`
2. Si no existe, calcula los días pendientes desde la última carga
3. Genera y carga los registros correspondientes
4. Actualiza niveles de stock en tiendas seleccionadas
5. Registra el resultado en la tabla `log_cargas`

También puede ejecutarse manualmente:

```bash
python carga_incremental.py
```

---

## 6. Estructura del proyecto

```
Go_Retail/
├── .env                      # Credenciales de conexión (no se sube a GitHub)
├── .gitignore                # Archivos excluidos del repositorio
├── requirements.txt          # Librerías Python necesarias
├── crear_tablas_Go_BD.py     # Crea las 4 tablas base en Go_BD
├── generar_historico.py      # Genera la data sintética histórica
├── modelo_pronostico.py      # Modelo Prophet
├── modelo_lightgbm.py        # Modelo LightGBM
├── modelo_segmentacion.py    # Segmentación ABC y K-Means
├── modelo_anomalias.py       # Detección de anomalías Isolation Forest
├── carga_incremental.py      # Script de carga incremental manual
└── tablero.py                # Tablero Streamlit con carga automática
```

---

## 7. Cómo interpretar el tablero

### 7.1 Barra de estado superior

Al cargar el tablero aparece uno de dos mensajes:

- ✅ **Verde:** se ejecutó la carga incremental. La data fue actualizada en esta sesión.
- ℹ️ **Azul:** ya existía data del día actual. No se realizó ninguna carga adicional.

---

### 7.2 Métricas principales

| Indicador | Qué significa | Cuándo actuar |
|---|---|---|
| Total SKUs | Productos activos en el catálogo | Referencial |
| Tiendas activas | Puntos de venta con movimiento | Referencial |
| Quiebres de stock | SKUs con stock por debajo del mínimo | Acción inmediata |
| Riesgo de quiebre | SKUs cuya cobertura es menor al lead time | Acción urgente |
| Sin movimiento | SKUs con stock pero sin ventas | Revisar viabilidad |

---

### 7.3 Ventas históricas

Gráfico de área con la evolución diaria de ventas en todas las tiendas. Permite identificar tendencias, picos de temporada y caídas inesperadas. Picos altos en ciertos meses indican temporada alta.

---

### 7.4 Pronóstico 30 días (Prophet)

Gráfico de líneas con la demanda estimada para los próximos 30 días de los 5 SKUs más vendidos. Las líneas más altas indican mayor demanda esperada y mayor prioridad de reposición.

---

### 7.5 Alertas de inventario

Gráfico de barras que resume las anomalías detectadas:

- **Barra roja:** quiebres de stock activos que requieren reposición inmediata.
- **Barra naranja:** riesgos de quiebre, la cobertura es menor al tiempo de reposición.
- **Barra azul:** SKUs sin movimiento con stock inmovilizado.

---

### 7.6 Segmentación ABC de SKUs

Gráfico de torta con la distribución de productos por rotación:

- **A (verde):** 120 SKUs que representan el 70% de las ventas. Máxima prioridad de abastecimiento.
- **B (amarillo):** 47 SKUs que representan el 20% de las ventas. Seguimiento regular.
- **C (rojo):** 33 SKUs que representan el 10% de las ventas. Evaluar si se justifica mantenerlos.

---

### 7.7 Ventas por segmento de tienda

Gráfico de barras horizontales con el volumen de ventas por tienda, coloreado según el segmento K-Means. Las tiendas de alta demanda tienen prioridad en la reposición.

---

### 7.8 Detalle de quiebres de stock

Tabla con los 15 casos más críticos. Columnas clave:

- **Stock actual:** unidades disponibles en la tienda.
- **Stock mínimo:** umbral por debajo del cual se considera quiebre.
- **Cobertura en días:** cuántos días puede operar la tienda con el stock actual. Valores cercanos a cero son emergencias.

---

### 7.9 Top SKUs — Demanda estimada

Gráfico de barras con los 10 SKUs de mayor demanda estimada para los próximos 30 días. El color más oscuro indica mayor urgencia de abastecimiento. Esta vista es la base para generar órdenes de compra o traslados entre bodegas.

---

## 8. Instalación y ejecución local

### 8.1 Requisitos previos

- Python 3.10 o superior
- Git instalado
- Cuenta en Neon (https://neon.tech)
- Visual Studio Code (recomendado)

### 8.2 Pasos de instalación

```bash
# 1. Clonar el repositorio
git clone https://github.com/andresenvigado-jpg/Go_Retail.git

# 2. Crear entorno virtual
python -m venv venv

# 3. Activar entorno virtual (Windows)
venv\Scripts\activate

# 4. Instalar dependencias
python -m pip install -r requirements.txt

# 5. Configurar credenciales
# Editar el archivo .env con los datos de Neon

# 6. Crear tablas en Go_BD
python crear_tablas_Go_BD.py

# 7. Generar data histórica
python generar_historico.py

# 8. Ejecutar modelos ML
python modelo_pronostico.py
python modelo_lightgbm.py
python modelo_segmentacion.py
python modelo_anomalias.py

# 9. Lanzar el tablero
python -m streamlit run tablero.py
```

---

## 9. Publicación en Streamlit Cloud

- **Repositorio GitHub:** https://github.com/andresenvigado-jpg/Go_Retail
- **Plataforma:** Streamlit Community Cloud (share.streamlit.io)
- **Archivo principal:** `tablero.py`
- **Variables de entorno:** configuradas como secrets en formato TOML en Streamlit Cloud
- **Actualización:** automática al hacer `git push` al repositorio

### Secrets en Streamlit Cloud (formato TOML)

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
| streamlit | 1.56.0 | Interfaz del tablero web |
| plotly | 6.7.0 | Gráficos interactivos |
| pandas | 3.0.2 | Manipulación de datos |
| prophet | 1.3.0 | Pronóstico de series de tiempo |
| lightgbm | 4.6.0 | Predicción con gradient boosting |
| scikit-learn | 1.8.0 | Clustering y detección de anomalías |
| psycopg2-binary | latest | Conexión a PostgreSQL |
| sqlalchemy | latest | ORM para consultas SQL |
| python-dotenv | latest | Gestión de variables de entorno |

---

*Go Retail — Documentación técnica v1.0 — Abril 2026*

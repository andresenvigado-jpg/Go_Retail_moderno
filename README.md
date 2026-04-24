# 🛒 Go Retail — Plataforma de Inteligencia de Supply Chain

> Sistema de análisis inteligente para retail que combina modelos de Machine Learning, pronósticos de demanda, optimización de inventario y seguimiento de cumplimiento de metas por tienda. Construido con arquitectura limpia (Clean Architecture) sobre FastAPI + React.

---

## 📋 Tabla de Contenido

- [Descripción General](#-descripción-general)
- [Stack Tecnológico](#-stack-tecnológico)
- [Arquitectura del Proyecto](#-arquitectura-del-proyecto)
- [Estructura de Directorios](#-estructura-de-directorios)
- [Modelos de Datos](#-modelos-de-datos)
- [Modelos de Machine Learning](#-modelos-de-machine-learning)
- [API REST](#-api-rest)
- [Frontend](#-frontend)
- [Explicación de Gráficas e Imágenes](#-explicación-de-gráficas-e-imágenes)
- [Instalación y Ejecución](#-instalación-y-ejecución)
- [Variables de Entorno](#-variables-de-entorno)
- [Despliegue en Producción](#-despliegue-en-producción)

---

## 📌 Descripción General

Go Retail es una plataforma de inteligencia operativa para cadenas de tiendas de retail. Permite:

- **Pronosticar la demanda** de productos con modelos Prophet y LightGBM
- **Detectar anomalías** en el inventario con Isolation Forest
- **Optimizar pedidos** mediante el modelo EOQ y simulaciones Monte Carlo
- **Segmentar productos y tiendas** con análisis ABC y K-Means
- **Descubrir patrones de compra** con Market Basket Analysis (Apriori)
- **Analizar rentabilidad y rotación** de SKUs por tienda
- **Gestionar el cumplimiento de metas de ventas** con KMeans, Regresión Lineal e IsolationForest
- **Gestionar usuarios** con roles (admin, analyst, viewer) y autenticación JWT
- **Generar datos sintéticos automáticamente** al iniciar sesión si no hay transacciones del día

---

## 🛠 Stack Tecnológico

### Backend

| Capa | Tecnología | Versión |
|------|-----------|---------|
| Framework web | FastAPI | ≥ 0.115 |
| Servidor ASGI | Uvicorn | ≥ 0.30 |
| ORM | SQLAlchemy | ≥ 2.0 |
| Base de datos | PostgreSQL (Neon) | — |
| Driver DB | psycopg2-binary | ≥ 2.9 |
| Validación | Pydantic v2 | ≥ 2.9 |
| Autenticación | python-jose + bcrypt | JWT HS256 |
| ML — Pronósticos | Prophet | — |
| ML — Gradient Boosting | LightGBM | ≥ 4.5 |
| ML — Clustering | scikit-learn (KMeans) | ≥ 1.5 |
| ML — Anomalías | scikit-learn (IsolationForest) | ≥ 1.5 |
| ML — Regresión | scikit-learn (LinearRegression) | ≥ 1.5 |
| ML — Asociación | mlxtend (Apriori) | ≥ 0.23 |
| Manipulación de datos | pandas / numpy | ≥ 2.x |
| Configuración | python-dotenv | ≥ 1.0 |

### Frontend

| Tecnología | Versión |
|-----------|---------|
| React | 18.3.1 |
| React Router | 6.27 |
| Recharts | 2.13 |
| Axios | 1.7 |
| Vite | 5.4 |

---

## 🏛 Arquitectura del Proyecto

El backend sigue **Clean Architecture** con cuatro capas claramente separadas:

```
┌─────────────────────────────────────────────────────────┐
│                      API (FastAPI)                      │  ← Capa de presentación
│          Endpoints · Middleware · Routers               │
├─────────────────────────────────────────────────────────┤
│                 Application (Use Cases)                 │  ← Lógica de aplicación
│        DTOs · Use Cases · Orquestación ML              │
├─────────────────────────────────────────────────────────┤
│                      Domain                             │  ← Reglas de negocio puras
│            Entities · Interfaces (contratos)           │
├─────────────────────────────────────────────────────────┤
│                   Infrastructure                        │  ← Detalles externos
│      ORM Models · Repositories · ML Models            │
└─────────────────────────────────────────────────────────┘
                           ↕
                    PostgreSQL (Neon)
```

**Flujo de una petición:**
```
HTTP Request
    → FastAPI Router
        → Use Case (orquesta)
            → Repository (accede a datos via ORM)
                → PostgreSQL
            ← DataFrame / Entity
        ← DTO (validado por Pydantic)
    ← JSON Response
```

---

## 📁 Estructura de Directorios

```
Go_Retail/
│
├── app/                          # Backend FastAPI
│   ├── main.py                   # Punto de entrada, CORS, exception handlers
│   ├── api/
│   │   ├── middleware/
│   │   │   └── error_handler.py
│   │   └── v1/
│   │       ├── router.py         # Agrupador de todos los routers
│   │       └── endpoints/
│   │           ├── auth.py       # Login / tokens JWT
│   │           ├── admin.py      # Carga de datos sintéticos automática
│   │           ├── products.py   # Catálogo, ABC, Market Basket
│   │           ├── inventory.py  # Anomalías, EOQ, Monte Carlo
│   │           ├── analytics.py  # Rentabilidad, Rotación, Eficiencia
│   │           ├── demand.py     # Prophet, LightGBM
│   │           ├── stores.py     # Catálogo de tiendas
│   │           └── compliance.py # Cumplimiento de metas por tienda ✨
│   │
│   ├── application/
│   │   ├── dtos/                 # Schemas Pydantic (request / response)
│   │   └── use_cases/            # Lógica de aplicación
│   │
│   ├── domain/
│   │   ├── entities/             # Entidades de negocio puras
│   │   └── interfaces/           # Contratos de repositorios
│   │
│   ├── infrastructure/
│   │   ├── orm/
│   │   │   └── models.py         # Todos los modelos SQLAlchemy (incluye MetaVentasORM) ✨
│   │   ├── repositories/         # Implementaciones concretas
│   │   └── ml/                   # Modelos de Machine Learning
│   │       ├── modelo_pronostico.py
│   │       ├── modelo_lightgbm.py
│   │       ├── modelo_anomalias.py
│   │       ├── modelo_eoq.py
│   │       ├── modelo_monte_carlo.py
│   │       ├── modelo_rentabilidad.py
│   │       ├── modelo_rotacion.py
│   │       ├── modelo_eficiencia_reposicion.py
│   │       ├── modelo_segmentacion.py
│   │       ├── modelo_market_basket.py
│   │       └── modelo_cumplimiento.py  # KMeans + LR + IsolationForest ✨
│   │
│   └── config/
│       ├── database.py           # Engine SQLAlchemy + SessionLocal
│       └── settings.py           # Variables de entorno (Pydantic Settings)
│
├── frontend/                     # React + Vite
│   ├── src/
│   │   ├── api/
│   │   │   ├── client.js         # Axios con interceptores JWT
│   │   │   └── endpoints.js      # Todas las rutas de la API
│   │   ├── components/
│   │   │   ├── Layout.jsx        # Sidebar + Header con usuario y logout
│   │   │   ├── SoftlineLogo.jsx  # Logo corporativo en CSS
│   │   │   ├── KPICard.jsx       # Tarjeta de métrica reutilizable
│   │   │   ├── RunModelBtn.jsx   # Botón ejecutar modelo ML
│   │   │   └── Spinner.jsx       # Indicador de carga
│   │   ├── context/
│   │   │   └── AuthContext.jsx   # Estado global JWT + auto-carga de datos
│   │   └── pages/
│   │       ├── LoginPage.jsx
│   │       ├── DashboardPage.jsx
│   │       ├── DemandPage.jsx
│   │       ├── InventoryPage.jsx
│   │       ├── AnalyticsPage.jsx
│   │       ├── ProductsPage.jsx
│   │       ├── StoresPage.jsx
│   │       └── CompliancePage.jsx  # Informe de cumplimiento ✨
│   └── vite.config.js
│
├── scripts/                      # Utilidades de carga y setup
│   ├── crear_tablas_Go_BD.py     # Crea todas las tablas base
│   ├── generar_historico.py      # Genera historial de transacciones
│   ├── carga_incremental.py      # Carga incremental diaria
│   ├── create_admin.py           # Crea usuario administrador inicial
│   └── crear_metas_ventas.py     # Crea y carga tabla de metas 2025-2026 ✨
│
├── .python-version               # Fuerza Python 3.11 en Render
├── render.yaml                   # Configuración de despliegue en Render
├── requirements.txt
├── .env
└── README.md
```

> ✨ = Archivo nuevo añadido en la última versión

---

## 🗄 Modelos de Datos

### Tablas Base (fuente de datos)

#### `catalogos` — Catálogo de Productos (SKUs)
| Columna | Tipo | Descripción |
|---------|------|-------------|
| `id` | INTEGER (PK) | SKU ID único |
| `name` | VARCHAR | Nombre del producto |
| `product_id` | VARCHAR | Código de producto |
| `categories` | VARCHAR | Categoría |
| `brands` | VARCHAR | Marca |
| `price` | NUMERIC | Precio de venta |
| `cost` | NUMERIC | Costo del producto |
| `seasons` | VARCHAR | Temporada |
| `department_name` | VARCHAR | Departamento |
| `custom_tipolinea` | VARCHAR | Tipo de línea |
| `avoid_replenishment` | BOOLEAN | Excluir de reposición automática |

#### `tiendas` — Red de Tiendas
| Columna | Tipo | Descripción |
|---------|------|-------------|
| `id` | INTEGER (PK) | ID de tienda |
| `name` | VARCHAR | Nombre de la tienda |
| `city` | VARCHAR | Ciudad |
| `region` | VARCHAR | Región |
| `custom_formato` | VARCHAR | Formato: grande / mediano / pequeño / express |
| `custom_clima` | VARCHAR | Clima de la zona |
| `custom_zona` | VARCHAR | Zona geográfica |
| `default_replenishment_lead_time` | INTEGER | Lead time de reposición (días) |

#### `inventarios` — Stock por SKU-Tienda
| Columna | Tipo | Descripción |
|---------|------|-------------|
| `id` | INTEGER (PK) | ID registro |
| `location_id` | VARCHAR | ID tienda |
| `sku_id` | VARCHAR | ID producto |
| `site_qty` | NUMERIC | Stock actual en tienda |
| `transit_qty` | NUMERIC | Cantidad en tránsito |
| `reserved_qty` | NUMERIC | Cantidad reservada |
| `min_stock` | NUMERIC | Stock mínimo permitido |
| `max_stock` | NUMERIC | Stock máximo permitido |
| `replenishment_lead_time` | INTEGER | Días de reposición |

#### `transacciones` — Historial de Movimientos
| Columna | Tipo | Descripción |
|---------|------|-------------|
| `id` | INTEGER (PK) | ID transacción |
| `receipt_id` | VARCHAR | ID recibo |
| `sku_id` | VARCHAR | Producto involucrado |
| `type` | VARCHAR | Tipo: `venta`, `devolución`, `ajuste` |
| `source_location_id` | VARCHAR | Tienda origen |
| `target_location_id` | VARCHAR | Tienda destino |
| `quantity` | NUMERIC | Cantidad |
| `sale_price` | NUMERIC | Precio de venta aplicado |
| `transaction_date` | DATE | Fecha del movimiento |

---

### Tabla de Metas de Ventas ✨

#### `metas_ventas` — Topes de Ventas por Tienda y Día
Tabla central del módulo de cumplimiento. Contiene una fila por cada combinación **tienda × día calendario** para los años 2025 y 2026 (≈ 14,620 registros con 20 tiendas × 731 días).

| Columna | Tipo | Descripción |
|---------|------|-------------|
| `id` | SERIAL (PK) | ID autoincremental |
| `tienda_id` | INTEGER (FK → tiendas) | Tienda a la que aplica la meta |
| `fecha` | DATE | Día al que corresponde la meta |
| `anio` | SMALLINT | Año (2025 / 2026) |
| `mes` | SMALLINT | Mes del año (1-12) |
| `semana_iso` | SMALLINT | Semana ISO (1-53) |
| `dia_semana` | SMALLINT | Día de la semana (1=Lun, 7=Dom) |
| `trimestre` | SMALLINT | Trimestre (1-4) |
| `es_temporada_alta` | BOOLEAN | `true` en ene, feb, jun, jul, oct, nov, dic |
| `meta_diaria_cop` | NUMERIC(15,2) | Meta de ventas del día en pesos COP |
| `meta_semanal_cop` | NUMERIC(15,2) | Meta de ventas de la semana en COP |
| `meta_mensual_cop` | NUMERIC(15,2) | Meta de ventas del mes en COP |
| `meta_diaria_und` | INTEGER | Meta de unidades vendidas por día |
| `meta_semanal_und` | INTEGER | Meta de unidades vendidas por semana |
| `meta_mensual_und` | INTEGER | Meta de unidades vendidas por mes |
| `created_at` | TIMESTAMP | Fecha de creación del registro |
| `updated_at` | TIMESTAMP | Última actualización |

**Criterios de generación de metas sintéticas:**

| Formato de tienda | Rango meta diaria COP | Rango unidades/día |
|------------------|----------------------|-------------------|
| GRANDE | $4.5M – $7.0M | 80 – 150 und |
| MEDIANO | $2.5M – $4.5M | 45 – 90 und |
| PEQUEÑO | $1.2M – $2.5M | 20 – 50 und |
| EXPRESS | $800K – $1.8M | 15 – 40 und |

**Factores estacionales aplicados:**

| Mes | Factor | Temporada |
|-----|--------|-----------|
| Diciembre | ×1.50 | Máxima — Navidad |
| Noviembre | ×1.30 | Pre-navidad |
| Enero, Julio | ×1.25 | Temporada alta |
| Febrero, Junio, Octubre | ×1.20 | Media-alta |
| Marzo, Septiembre | ×1.00 | Normal |
| Abril, Mayo, Agosto | ×0.95 | Baja |

Los domingos aplican un factor adicional de **×0.70** (menor flujo de clientes).

---

### Tablas de Resultados ML

| Tabla | Clave Primaria | Descripción |
|-------|---------------|-------------|
| `pronosticos` | `sku_id + fecha` | Pronósticos Prophet por SKU y día |
| `predicciones_lgbm` | `sku_id + tienda_id` | Predicciones LightGBM por SKU-tienda |
| `anomalias_inventario` | `sku_id + tienda_id` | Anomalías detectadas por Isolation Forest |
| `eoq_resultados` | `sku_id + tienda_id` | Cantidades óptimas de pedido |
| `monte_carlo` | `sku_id + tienda_id` | Niveles de riesgo simulados |
| `rentabilidad_sku` | `sku_id + tienda_id` | Índice de rentabilidad por SKU-tienda |
| `rotacion_sku` | `sku_id + tienda_id` | Velocidad de rotación de inventario |
| `eficiencia_reposicion` | `tienda_id` | Eficiencia logística por tienda |
| `segmentacion_skus` | `sku_id` | Segmento ABC de cada producto |
| `segmentacion_tiendas` | `tienda_id` | Cluster KMeans de cada tienda |
| `market_basket` | `sku_origen + sku_destino` | Reglas de asociación Apriori |

> **Nota técnica:** Las tablas de resultados ML usan claves primarias naturales o compuestas (sin columna `id` serial), ya que son creadas/reemplazadas por `pandas.to_sql()` en cada ejecución del modelo.

---

### Gestión de Usuarios

#### `usuarios`
| Columna | Tipo | Descripción |
|---------|------|-------------|
| `id` | SERIAL (PK) | ID usuario |
| `username` | VARCHAR | Nombre de usuario único |
| `email` | VARCHAR | Email único |
| `hashed_password` | VARCHAR | Contraseña hasheada con bcrypt |
| `rol` | VARCHAR | `admin` / `analyst` / `viewer` |
| `activo` | BOOLEAN | Estado de la cuenta |
| `creado_en` | TIMESTAMP | Fecha de creación |
| `ultimo_acceso` | TIMESTAMP | Último login registrado |

**Roles y permisos:**

| Rol | Puede ver datos | Puede ejecutar modelos | Gestiona usuarios |
|-----|:-:|:-:|:-:|
| `viewer` | ✅ | ❌ | ❌ |
| `analyst` | ✅ | ✅ | ❌ |
| `admin` | ✅ | ✅ | ✅ |

---

## 🤖 Modelos de Machine Learning

### 1. Prophet — Pronóstico de Demanda
- **Archivo:** `modelo_pronostico.py`
- **Algoritmo:** Facebook Prophet (series de tiempo aditivas)
- **Entrada:** historial de ventas por SKU agrupado por día
- **Salida:** predicción diaria de demanda para los próximos 30 días
- **Tabla resultado:** `pronosticos`

### 2. LightGBM — Predicción por Tienda-SKU
- **Archivo:** `modelo_lightgbm.py`
- **Algoritmo:** Gradient Boosting optimizado (LightGBM)
- **Features:** día semana, mes, tienda, stock actual, precio, lags de ventas
- **Salida:** cantidad predicha de ventas por combinación tienda-SKU
- **Tabla resultado:** `predicciones_lgbm`

### 3. Isolation Forest — Detección de Anomalías de Inventario
- **Archivo:** `modelo_anomalias.py`
- **Algoritmo:** Isolation Forest (detección no supervisada de outliers)
- **Detecta:** sobrestock, quiebre de stock, stock congelado (sin rotación)
- **Salida:** etiqueta de anomalía + score de aislamiento por SKU-tienda
- **Tabla resultado:** `anomalias_inventario`

### 4. EOQ — Cantidad Económica de Pedido
- **Archivo:** `modelo_eoq.py`
- **Algoritmo:** Fórmula clásica EOQ `Q* = √(2DS/H)`
- **Calcula:** cantidad óptima de reorden, punto de reorden, stock de seguridad, estado de reposición
- **Tabla resultado:** `eoq_resultados`

### 5. Monte Carlo — Simulación de Riesgo de Quiebre
- **Archivo:** `modelo_monte_carlo.py`
- **Algoritmo:** Simulación estocástica (10,000 iteraciones por SKU-tienda)
- **Calcula:** probabilidad de quiebre de stock, nivel de riesgo: BAJO / MEDIO / ALTO
- **Tabla resultado:** `monte_carlo`

### 6. Rentabilidad — Análisis Financiero por SKU
- **Archivo:** `modelo_rentabilidad.py`
- **Calcula:** margen porcentual `(precio - costo) / precio`, rentabilidad total, índice combinado
- **Clasificación:** Alta / Media / Baja rentabilidad
- **Tabla resultado:** `rentabilidad_sku`

### 7. Rotación — Velocidad de Venta de Inventario
- **Archivo:** `modelo_rotacion.py`
- **Calcula:** tasa de rotación anual, DSI (días de inventario en stock), frecuencia de venta
- **Clasificación:** Alta / Media / Baja rotación
- **Tabla resultado:** `rotacion_sku`

### 8. Eficiencia de Reposición
- **Archivo:** `modelo_eficiencia_reposicion.py`
- **Calcula:** cobertura de reposición, tasa de devolución, eficiencia de SKUs activos, índice global
- **Tabla resultado:** `eficiencia_reposicion`

### 9. Segmentación ABC + KMeans
- **Archivo:** `modelo_segmentacion.py`
- **SKUs — Análisis ABC:** A = 70% de ventas acumuladas, B = siguiente 20%, C = 10% restante
- **Tiendas — K-Means:** agrupa tiendas por métricas de ventas/stock; k óptimo por silhouette score
- **Tablas resultado:** `segmentacion_skus`, `segmentacion_tiendas`

### 10. Market Basket — Análisis de Asociación
- **Archivo:** `modelo_market_basket.py`
- **Algoritmo:** Apriori + reglas de asociación (mlxtend)
- **Métricas generadas:** soporte, confianza, lift, convicción
- **Tabla resultado:** `market_basket`

### 11. Cumplimiento de Metas — Modelo Compuesto ✨
- **Archivo:** `modelo_cumplimiento.py`
- **Tres algoritmos integrados en un único pipeline:**

| Algoritmo | Función | Salida |
|-----------|---------|--------|
| **KMeans** (k=4) | Segmenta las tiendas por comportamiento de cumplimiento | Tier: Excelente 🏆 / Bueno ✅ / Regular ⚠️ / Crítico 🚨 |
| **LinearRegression** | Calcula la pendiente de cumplimiento diario por tienda | Tendencia: Mejorando ↑ / Estable → / Bajando ↓ |
| **IsolationForest** | Identifica tiendas con comportamiento estadísticamente anómalo | `es_anomalia: true/false` |

- **Entrada:** tabla `metas_ventas` cruzada con `transacciones` del período solicitado
- **Proyección fin de mes:** extrapola las ventas acumuladas al ritmo actual para estimar el cumplimiento total del mes
- **Salida JSON:**
  - `resumen_ejecutivo` — métricas globales de la cadena
  - `tiendas` — ranking completo con tier, tendencia, anomalía y proyección
  - `top3` / `bottom3` — las mejores y peores 3 tiendas
  - `alertas` — tiendas con proyección mensual por debajo del 80%

---

## 🌐 API REST

**Base URL producción:** `https://go-retail-moderno.onrender.com/api/v1`  
**Base URL local:** `http://localhost:8000/api/v1`  
**Documentación interactiva:** `https://go-retail-moderno.onrender.com/api/docs`

### Autenticación
| Método | Endpoint | Descripción | Auth |
|--------|---------|-------------|------|
| `POST` | `/auth/login` | Obtener token JWT | ❌ |
| `GET` | `/auth/me` | Perfil del usuario actual | ✅ |

### Administración
| Método | Endpoint | Descripción | Auth |
|--------|---------|-------------|------|
| `POST` | `/admin/check-and-load` | Valida datos del día y genera sintéticos si faltan | ✅ |

### Productos y Segmentación
| Método | Endpoint | Descripción | Rol mínimo |
|--------|---------|-------------|-----------|
| `GET` | `/products` | Catálogo completo de SKUs | viewer |
| `GET` | `/products/segmentation/abc` | Segmentación ABC | viewer |
| `GET` | `/products/market-basket/rules` | Reglas de asociación | viewer |
| `POST` | `/products/run/segmentation` | ▶ Ejecutar modelo ABC + KMeans | analyst |
| `POST` | `/products/run/market-basket` | ▶ Ejecutar Market Basket | analyst |

### Inventario
| Método | Endpoint | Descripción | Rol mínimo |
|--------|---------|-------------|-----------|
| `GET` | `/inventory/anomalies` | Anomalías detectadas | viewer |
| `GET` | `/inventory/eoq` | Resultados EOQ | viewer |
| `GET` | `/inventory/monte-carlo` | Simulaciones Monte Carlo | viewer |
| `POST` | `/inventory/run/anomalies` | ▶ Ejecutar Isolation Forest | analyst |
| `POST` | `/inventory/run/eoq` | ▶ Ejecutar modelo EOQ | analyst |
| `POST` | `/inventory/run/monte-carlo` | ▶ Ejecutar Monte Carlo | analyst |

### Analítica
| Método | Endpoint | Descripción | Rol mínimo |
|--------|---------|-------------|-----------|
| `GET` | `/analytics/rentability` | Rentabilidad por SKU-Tienda | viewer |
| `GET` | `/analytics/rotation` | Rotación por SKU-Tienda | viewer |
| `GET` | `/analytics/efficiency` | Eficiencia por tienda | viewer |
| `POST` | `/analytics/run/rentability` | ▶ Ejecutar modelo rentabilidad | analyst |
| `POST` | `/analytics/run/rotation` | ▶ Ejecutar modelo rotación | analyst |
| `POST` | `/analytics/run/efficiency` | ▶ Ejecutar modelo eficiencia | analyst |

### Demanda
| Método | Endpoint | Descripción | Rol mínimo |
|--------|---------|-------------|-----------|
| `GET` | `/demand/forecasts` | Pronósticos Prophet | viewer |
| `GET` | `/demand/predictions` | Predicciones LightGBM | viewer |
| `POST` | `/demand/run/forecast` | ▶ Ejecutar Prophet | analyst |
| `POST` | `/demand/run/lgbm` | ▶ Ejecutar LightGBM | analyst |

### Cumplimiento de Metas ✨
| Método | Endpoint | Descripción | Auth |
|--------|---------|-------------|------|
| `GET` | `/compliance/report` | Informe completo de cumplimiento por tienda | ✅ |

**Parámetros opcionales de `/compliance/report`:**

| Parámetro | Tipo | Descripción | Ejemplo |
|-----------|------|-------------|---------|
| `fecha_desde` | date | Inicio del período (YYYY-MM-DD) | `2026-04-01` |
| `fecha_hasta` | date | Fin del período (YYYY-MM-DD) | `2026-04-24` |

Si no se envían fechas, el informe analiza el **mes en curso** por defecto.

---

## 💻 Frontend

Aplicación SPA construida con **React 18 + Vite**, que consume la API REST y visualiza los resultados con **Recharts**. Protegida con JWT: rutas privadas redirigen al login si no hay sesión activa.

### Páginas

| Ruta | Página | Descripción |
|------|--------|-------------|
| `/login` | Login | Formulario de autenticación JWT con logo corporativo |
| `/` | Dashboard | KPIs globales + gráfica de demanda top SKUs |
| `/demand` | Demanda | Pronósticos Prophet + Predicciones LightGBM |
| `/inventory` | Inventario | Anomalías + Monte Carlo + Tabla EOQ |
| `/analytics` | Analítica | Rentabilidad + Rotación + Eficiencia de reposición |
| `/products` | Productos | Segmentación ABC + Market Basket Analysis |
| `/stores` | Tiendas | Catálogo con formato y segmento KMeans por tienda |
| `/compliance` | Cumplimiento ✨ | KPIs + Ranking + Alertas + Top/Bottom 3 tiendas |

### Flujo post-login automático

Al iniciar sesión, el sistema ejecuta en segundo plano `POST /admin/check-and-load`, que verifica si existen transacciones del día actual. Si no las hay, genera automáticamente datos sintéticos de ventas para todas las tiendas. Esto garantiza que los modelos ML siempre tengan datos del día vigente sin intervención manual.

### Componentes clave

| Componente | Descripción |
|-----------|-------------|
| `Layout.jsx` | Barra lateral con navegación, secciones agrupadas, usuario activo y botón de logout |
| `SoftlineLogo.jsx` | Logo corporativo Softline implementado en CSS puro |
| `RunModelBtn.jsx` | Botón que ejecuta un modelo ML, muestra estado de carga y refresca datos automáticamente |
| `KPICard.jsx` | Tarjeta de métrica con ícono, valor principal y etiqueta descriptiva |
| `AuthContext.jsx` | Contexto React global con token JWT, datos de usuario, logout y trigger de carga automática |
| `client.js` | Instancia de Axios con interceptor que inyecta el header `Authorization: Bearer <token>` |

---

## 📊 Explicación de Gráficas e Imágenes

### 🔐 Login

#### Formulario de autenticación
La pantalla de ingreso muestra el formulario de usuario y contraseña sobre un fondo oscuro. En la parte superior aparece el logotipo **Go Retail** con el nombre del sistema y la marca corporativa **Softline s.a.** en la esquina. Una vez ingresadas las credenciales y presionado el botón *Ingresar*, el sistema valida el token JWT, carga el perfil del usuario y redirige automáticamente al Dashboard. Si las credenciales son incorrectas, aparece un mensaje de error en rojo sin redirigir.

---

### 🏠 Dashboard

#### Tarjetas KPI — Resumen Ejecutivo
En la parte superior de la pantalla se muestran tarjetas de indicadores clave extraídos de las tablas de resultados ML. Cada tarjeta tiene un ícono representativo, el valor numérico principal en grande y una etiqueta descriptiva. Permiten leer el estado del negocio de un solo vistazo: total de SKUs catalogados, tiendas activas, registros de inventario y transacciones del período.

#### Barras — Demanda Estimada: Top 8 SKUs
Muestra los 8 productos con mayor demanda estimada según el modelo Prophet. El eje horizontal lista los identificadores de SKU y el eje vertical indica las unidades proyectadas. Una barra alta señala un producto de alta presión de venta que requiere prioridad en abastecimiento. Esta gráfica es el primer filtro para que el equipo de compras sepa dónde concentrar su atención.

---

### 📈 Demanda

#### Líneas — Pronóstico Prophet: Top 5 SKUs (30 días)
Proyección de ventas para los próximos 30 días calendario. Cada línea de color diferente corresponde a un SKU del top de demanda. El eje horizontal es la fecha y el eje vertical son las unidades estimadas. Una línea con pendiente ascendente indica crecimiento de demanda y requiere incrementar el stock; una línea descendente sugiere reducir órdenes de compra o activar promociones. Esta gráfica alimenta directamente la planificación de compras y transferencias entre tiendas.

#### Dispersión (Scatter) — LightGBM: Real vs Predicho
El eje X representa las ventas reales históricas por SKU-tienda y el eje Y las ventas predichas por el modelo LightGBM para esa misma combinación. En un modelo perfecto todos los puntos caerían sobre la diagonal `y = x`. Cuanto más concentrados estén los puntos alrededor de esa diagonal, mayor es la precisión del modelo. Puntos muy dispersos o alejados de la diagonal indican pares SKU-tienda donde el modelo tiene baja confiabilidad y conviene complementar con criterio experto del equipo comercial.

---

### 📦 Inventario

#### Pastel — Tipos de Anomalías (Isolation Forest)
Clasifica las anomalías detectadas por IsolationForest en tres categorías:
- **Sobrestock** — inventario muy por encima del máximo esperado, capital inmovilizado
- **Quiebre de stock** — inventario por debajo del mínimo, riesgo de venta perdida
- **Stock congelado** — sin movimiento en un período prolongado, posible producto obsoleto

Cada segmento del pastel representa la proporción de cada tipo sobre el total de anomalías detectadas. Un segmento grande de sobrestock indica exceso de compras; uno grande de quiebre indica problemas en la cadena de abastecimiento.

#### Barras — Monte Carlo: Nivel de Riesgo de Quiebre
Resultado de 10,000 simulaciones estocásticas que evalúan la probabilidad de que cada SKU-tienda se agote antes del próximo reabastecimiento. Agrupa los resultados en tres niveles de riesgo:
- **BAJO** (verde) — el stock cubre la demanda simulada con alta probabilidad; sin acción urgente
- **MEDIO** (amarillo) — existe riesgo moderado de quiebre; monitorear y preparar reposición
- **ALTO** (rojo) — alta probabilidad de agotamiento; reposición inmediata requerida

Las barras más altas en la categoría ALTO representan la alerta más crítica para el equipo de operaciones.

#### Tabla — EOQ: Cantidad Óptima de Pedido por SKU-Tienda
Guía operativa directa para el equipo de compras. Por cada combinación producto-tienda muestra:
- **EOQ** — cantidad exacta a pedir calculada con la fórmula `Q* = √(2DS/H)` para minimizar el costo total de inventario
- **Punto de reorden** — nivel de stock en el que se debe lanzar la orden de compra
- **Stock de seguridad** — colchón recomendado contra variabilidad de demanda y lead time
- **Estado actual** — semáforo: OK / Reponer / Crítico según el inventario real vs los umbrales calculados

---

### 💰 Analítica

#### Barras — Índice de Rentabilidad: Top SKUs
Ranking de los productos más rentables según un índice que combina el margen porcentual `(precio - costo) / precio` con el volumen de ventas. Las barras más altas identifican los SKUs que generan mayor valor económico para la operación. Esta gráfica orienta decisiones de pricing, negociación con proveedores y enfoque del equipo comercial hacia los productos que más contribuyen al resultado financiero.

#### Pastel — Clasificación de Rotación de SKUs
Distribuye el catálogo en tres categorías de velocidad de venta calculadas con la tasa de rotación anual y el DSI (Days Sales of Inventory):
- **Alta rotación** (verde) — productos que se venden rápido; mantener stock suficiente para no quedar desabastecido
- **Media rotación** (amarillo) — productos de demanda regular; monitorear y ajustar según temporada
- **Baja rotación** (rojo) — capital inmovilizado en inventario; evaluar descuentos, liquidaciones o retiro del surtido

Un segmento grande en baja rotación es una señal directa de que hay dinero atrapado en el anaquel.

#### Barras Horizontales — Eficiencia de Reposición por Tienda
Compara el desempeño logístico de cada tienda combinando tres indicadores en un único índice:
- **Cobertura de reposición** — qué tan bien se reponen los productos antes de llegar al mínimo
- **Tasa de devolución** — proporción de unidades devueltas sobre las recibidas (alta devolución = mala calidad de pedido)
- **Eficiencia de SKUs activos** — proporción de SKUs con movimiento real vs SKUs catalogados

Las tiendas con barra corta tienen procesos logísticos deficientes y requieren revisión operativa, capacitación del equipo o soporte adicional de la cadena de suministro.

---

### 🛒 Productos

#### Pastel — Segmentación ABC de SKUs
Clasifica el catálogo aplicando el principio de Pareto a las ventas acumuladas:
- **Segmento A** — pocos SKUs que generan el **70% de las ventas totales** → máxima prioridad, nunca deben faltar en el anaquel, nivel de servicio ≥ 99%
- **Segmento B** — SKUs de rotación media que aportan el **20% de ventas** → mantener con buffer moderado, revisar mensualmente
- **Segmento C** — mayoría del catálogo con solo el **10% de ventas** → evaluar si justifican espacio en anaquel, bodega y gestión

Esta clasificación determina el nivel de atención y los parámetros de reposición que se aplican en los modelos EOQ y Monte Carlo.

#### Barras Horizontales — Market Basket: Productos Más Comprados Juntos (Lift)
Visualiza las reglas de asociación más fuertes entre pares de productos descubiertas con el algoritmo Apriori. El **Lift** mide la intensidad real de la relación entre dos SKUs, eliminando el efecto de la popularidad individual de cada uno:
- `Lift = 1` → la compra conjunta es casual, sin relación real
- `Lift > 1` → los productos se compran juntos más de lo esperado por azar
- `Lift > 2` → relación fuerte → ubicar juntos en la tienda o en la misma zona de anaquel
- `Lift > 3` → relación muy fuerte → crear bundle, promoción cruzada o descuento combinado

Las barras más largas indican los pares de productos con mayor potencial para estrategias de cross-selling y merchandising.

---

### 🏪 Tiendas

#### Tabla — Catálogo de Tiendas con Segmentación KMeans
Lista todas las tiendas de la cadena con sus atributos: nombre, ciudad, región, formato comercial (grande / mediano / pequeño / express) y el segmento KMeans asignado. El segmento agrupa tiendas con comportamiento de ventas e inventario similar, permitiendo comparar pares equivalentes y aplicar estrategias diferenciadas por clúster en lugar de tratar todas las tiendas igual.

---

### 🎯 Cumplimiento de Metas ✨

Esta es la página más completa del sistema, construida con tres algoritmos de ML integrados en un único pipeline.

#### Filtros de Período
En la parte superior aparecen dos campos de fecha (**Desde** / **Hasta**) y un botón *Actualizar*. Por defecto el informe analiza el mes en curso. Al cambiar las fechas y actualizar, todos los indicadores, gráficas y tablas de la página se recalculan para el nuevo período. Esto permite comparar el cumplimiento entre meses, trimestres o cualquier rango arbitrario.

#### Tarjetas KPI — Resumen Ejecutivo de la Cadena
Siete tarjetas en la parte superior presentan el estado global de la cadena:

| Tarjeta | Qué indica |
|---------|-----------|
| 🏪 **Total tiendas** | Número de tiendas con metas y ventas en el período analizado |
| 🎯 **Cumplimiento global** | Promedio del porcentaje de cumplimiento de todas las tiendas; verde ≥ 100%, amarillo ≥ 80%, rojo < 80% |
| ✅ **Sobre meta** | Cantidad de tiendas que superaron o igualaron el 100% de cumplimiento en el período |
| ⚠️ **En riesgo** | Tiendas cuya proyección de fin de mes es inferior al 80%; requieren acción inmediata |
| 🔍 **Tiendas anómalas** | Tiendas detectadas por IsolationForest con comportamiento estadísticamente atípico respecto al grupo |
| 💰 **Ventas totales** | Suma de ventas COP de todas las tiendas en el período, expresada en millones |
| 📊 **Ventas vs Meta** | Porcentaje global: ventas reales totales / metas totales × 100; indica si la cadena como un todo cumple |

#### Distribución por Tier (KMeans)
Cuatro bloques de color muestran cuántas tiendas cayeron en cada segmento según el algoritmo KMeans con k=4:

| Tier | Color | Criterio |
|------|-------|---------|
| 🏆 Excelente | Verde | Tiendas con mayor cumplimiento promedio, más días sobre meta y mejor consistencia |
| ✅ Bueno | Azul | Buen desempeño, cercanos o sobre la meta con regularidad |
| ⚠️ Regular | Amarillo | Cumplimiento intermitente, por debajo de la meta varios días |
| 🚨 Crítico | Rojo | Bajo cumplimiento consistente, requieren intervención directa de gerencia |

El algoritmo KMeans agrupa las tiendas usando tres dimensiones: porcentaje de cumplimiento COP acumulado, porcentaje de días sobre meta y cumplimiento promedio diario. El clúster con mayor valor promedio en esas tres métricas recibe la etiqueta *Excelente*, y así en orden descendente.

#### Barras — Top 15 Tiendas: Cumplimiento COP (%)
Gráfica de barras verticales que ordena las 15 tiendas con mejor cumplimiento de mayor a menor. El color de cada barra corresponde al tier KMeans asignado (verde = Excelente, azul = Bueno, amarillo = Regular, rojo = Crítico). La línea punteada verde horizontal marca el **100%** (meta cumplida). Al pasar el cursor sobre cada barra aparece un tooltip con el nombre de la tienda, el porcentaje exacto de cumplimiento, las ventas reales, la meta y el tier. Esta gráfica permite comparar visualmente de un vistazo cuáles tiendas están por encima y por debajo de la meta.

#### Tab: Ranking Completo
Tabla interactiva con todas las tiendas ordenadas de mayor a menor cumplimiento. Incluye dos filtros en la parte superior:
- **Búsqueda de texto** — filtra por nombre de tienda o ciudad
- **Filtro de tier** — muestra solo las tiendas del segmento seleccionado

Columnas de la tabla:

| Columna | Descripción |
|---------|-------------|
| **#** | Posición en el ranking general |
| **Tienda** | Nombre de la tienda |
| **Ciudad** | Ciudad donde opera |
| **Tier** | Segmento KMeans con badge de color |
| **Tendencia** | Resultado de LinearRegression: Mejorando ↑ / Estable → / Bajando ↓ |
| **Cump. %** | Porcentaje de cumplimiento acumulado en el período (ventas reales / meta) |
| **Sem. %** | Cumplimiento de la semana ISO en curso |
| **Mes %** | Cumplimiento del mes en curso |
| **Proyec. %** | Proyección de cumplimiento al cierre del mes basada en el ritmo actual |
| **Anómala** | ⚠️ si IsolationForest identificó comportamiento estadísticamente atípico |

Los valores de cumplimiento se colorean automáticamente: verde ≥ 100%, amarillo ≥ 80%, rojo < 80%.

#### Tab: Alertas
Lista de tiendas cuya **proyección de cumplimiento mensual es menor al 80%**. Para cada tienda en alerta se muestra:
- Nombre, ciudad, región y tier con badge de color
- Porcentaje de proyección en grande y en rojo
- Cumplimiento acumulado del período
- Tendencia (LinearRegression) — si dice *Bajando ↓* la situación es crítica porque además empeora
- Indicador morado si además es detectada como anómala por IsolationForest

Si todas las tiendas tienen proyección ≥ 80%, el tab muestra un mensaje verde de confirmación indicando que no hay alertas activas.

#### Tab: Top & Bottom 3
Dos columnas paralelas que muestran las tres mejores y las tres peores tiendas de la cadena en el período:

**Top 3 — Mejores tiendas (borde verde):**
Cada tarjeta muestra el ranking, nombre, ciudad, formato y tier. El porcentaje de cumplimiento aparece en grande en verde. Debajo se presenta la proyección de fin de mes, los días en que la tienda superó la meta diaria y la tendencia de LinearRegression.

**Bottom 3 — Tiendas rezagadas (borde rojo):**
Misma estructura que el Top 3 pero con acento rojo. Estas tiendas requieren revisión de causas raíz: fuerza de ventas, surtido, operación logística o condiciones del mercado local.

---

## ⚙️ Instalación y Ejecución

### Requisitos previos

- Python 3.11+
- Node.js 18+
- PostgreSQL (o cuenta en [Neon](https://neon.tech) para hosting gratuito)

### Backend

```bash
# 1. Clonar el repositorio
git clone https://github.com/andresenvigado-jpg/Go_Retail_moderno.git
cd Go_Retail_moderno

# 2. Crear entorno virtual
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux / Mac

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar variables de entorno
# Crear .env con las variables indicadas en la sección siguiente

# 5. Crear tablas base en la base de datos
python scripts/crear_tablas_Go_BD.py

# 6. Generar historial de transacciones sintéticas
python scripts/generar_historico.py

# 7. Cargar metas de ventas 2025-2026
python scripts/crear_metas_ventas.py

# 8. Crear usuario administrador inicial
python scripts/create_admin.py

# 9. Iniciar el servidor
uvicorn app.main:app --reload --port 8000
```

La API queda disponible en `http://localhost:8000`  
Documentación Swagger en `http://localhost:8000/api/docs`

### Frontend

```bash
cd frontend
npm install
npm run dev
```

La app queda disponible en `http://localhost:5173`

---

## 🔐 Variables de Entorno

Crear un archivo `.env` en la raíz del proyecto:

```env
# ─── Base de datos PostgreSQL ───────────────────────────
DB_HOST=your-host.neon.tech
DB_NAME=your_database_name
DB_USER=your_user
DB_PASSWORD=your_password
DB_PORT=5432

# ─── Seguridad JWT ──────────────────────────────────────
SECRET_KEY=clave_secreta_larga_y_aleatoria_minimo_32_chars
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=480
```

---

## 🚀 Despliegue en Producción

### Backend — Render

El archivo `render.yaml` en la raíz del proyecto configura el servicio automáticamente:

```yaml
services:
  - type: web
    name: go-retail-api
    runtime: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

El archivo `.python-version` fuerza **Python 3.11** para garantizar compatibilidad con todas las dependencias ML.

**Variables de entorno:** configurar en el panel de Render → Environment → las mismas variables del `.env`.

**Auto-deploy:** Render detecta cada push a la rama `main` de GitHub y redespliega automáticamente en 3-5 minutos.

### Frontend — Vercel

El archivo `vercel.json` configura el enrutamiento SPA:

```json
{
  "routes": [
    { "src": "/assets/(.*)", "dest": "/assets/$1" },
    { "src": "/(.+\\.(png|jpg|jpeg|svg|ico|webp|gif|woff|woff2|ttf|eot))", "dest": "/$1" },
    { "src": "/(.*)", "dest": "/index.html" }
  ]
}
```

**Auto-deploy:** Vercel detecta cada push a la rama `main` y redespliega en 2-4 minutos.

**URL de producción:** `https://go-retail-moderno.vercel.app` (o dominio asignado por Vercel)

---

## 📄 Licencia

Proyecto desarrollado para **Go Retail** por **Softline s.a.** — 2026.  
Todos los derechos reservados.

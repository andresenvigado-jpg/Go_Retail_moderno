# 🛒 Go Retail — Plataforma de Inteligencia de Supply Chain

> Sistema de análisis inteligente para retail que combina modelos de Machine Learning, pronósticos de demanda y optimización de inventario, construido con arquitectura limpia (Clean Architecture) sobre FastAPI + React.

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
- [Explicación de Gráficas](#-explicación-de-gráficas)
- [Instalación y Ejecución](#-instalación-y-ejecución)
- [Variables de Entorno](#-variables-de-entorno)

---

## 📌 Descripción General

Go Retail es una plataforma de inteligencia operativa para cadenas de tiendas. Permite:

- **Pronosticar la demanda** de productos con modelos Prophet y LightGBM
- **Detectar anomalías** en el inventario con Isolation Forest
- **Optimizar pedidos** mediante el modelo EOQ y simulaciones Monte Carlo
- **Segmentar productos y tiendas** con análisis ABC y K-Means
- **Descubrir patrones de compra** con Market Basket Analysis (Apriori)
- **Analizar rentabilidad y rotación** de SKUs por tienda
- **Gestionar usuarios** con roles (admin, analyst, viewer) y autenticación JWT

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
│   │           ├── admin.py      # Gestión de usuarios
│   │           ├── products.py   # Catálogo, ABC, Market Basket
│   │           ├── inventory.py  # Anomalías, EOQ, Monte Carlo
│   │           ├── analytics.py  # Rentabilidad, Rotación, Eficiencia
│   │           ├── demand.py     # Prophet, LightGBM
│   │           └── stores.py     # Catálogo de tiendas
│   │
│   ├── application/
│   │   ├── dtos/                 # Schemas Pydantic (request / response)
│   │   │   ├── auth_dto.py
│   │   │   ├── product_dto.py
│   │   │   ├── inventory_dto.py
│   │   │   ├── analytics_dto.py
│   │   │   └── demand_dto.py
│   │   └── use_cases/            # Lógica de aplicación
│   │       ├── auth_use_cases.py
│   │       ├── product_use_cases.py
│   │       ├── inventory_use_cases.py
│   │       ├── analytics_use_cases.py
│   │       └── demand_use_cases.py
│   │
│   ├── domain/
│   │   ├── entities/             # Entidades de negocio puras
│   │   │   ├── product.py
│   │   │   ├── store.py
│   │   │   ├── inventory.py
│   │   │   └── user.py
│   │   └── interfaces/           # Contratos de repositorios
│   │       ├── i_product_repository.py
│   │       ├── i_inventory_repository.py
│   │       ├── i_analytics_repository.py
│   │       ├── i_demand_repository.py
│   │       └── i_auth_repository.py
│   │
│   ├── infrastructure/
│   │   ├── orm/
│   │   │   └── models.py         # Todos los modelos SQLAlchemy
│   │   ├── repositories/         # Implementaciones concretas
│   │   │   ├── inventory_repository.py
│   │   │   ├── product_repository.py
│   │   │   ├── analytics_repository.py
│   │   │   ├── demand_repository.py
│   │   │   └── auth_repository.py
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
│   │       └── modelo_market_basket.py
│   │
│   └── config/
│       ├── database.py           # Engine SQLAlchemy + SessionLocal
│       └── settings.py           # Variables de entorno (Pydantic Settings)
│
├── frontend/                     # React + Vite
│   ├── src/
│   │   ├── api/
│   │   │   ├── client.js         # Axios con interceptores JWT
│   │   │   └── endpoints.js      # Constantes de rutas API
│   │   ├── components/
│   │   │   ├── Layout.jsx        # Navbar + Sidebar
│   │   │   ├── KPICard.jsx       # Tarjeta de métrica
│   │   │   ├── RunModelBtn.jsx   # Botón ejecutar modelo ML
│   │   │   └── Spinner.jsx
│   │   ├── context/
│   │   │   └── AuthContext.jsx   # Estado global de autenticación
│   │   └── pages/
│   │       ├── LoginPage.jsx
│   │       ├── DashboardPage.jsx
│   │       ├── DemandPage.jsx
│   │       ├── InventoryPage.jsx
│   │       ├── AnalyticsPage.jsx
│   │       ├── ProductsPage.jsx
│   │       └── StoresPage.jsx
│   └── vite.config.js
│
├── scripts/                      # Utilidades de carga y setup
│   ├── crear_tablas_Go_BD.py
│   ├── generar_historico.py
│   ├── carga_incremental.py
│   └── create_admin.py
│
├── requirements.txt
├── .env
└── README.md
```

---

## 🗄 Modelos de Datos

### Tablas Base (fuente de datos)

#### `catalogos` — Catálogo de Productos (SKUs)
| Columna | Tipo | Descripción |
|---------|------|-------------|
| `id` | VARCHAR (PK) | SKU ID único |
| `name` | VARCHAR | Nombre del producto |
| `product_id` | VARCHAR | Código de producto |
| `categories` | VARCHAR | Categoría |
| `brands` | VARCHAR | Marca |
| `price` | NUMERIC | Precio de venta |
| `cost` | NUMERIC | Costo del producto |
| `seasons` | VARCHAR | Temporada |
| `department_name` | VARCHAR | Departamento |
| `custom_tipolinea` | VARCHAR | Tipo de línea |
| `avoid_replenishment` | BOOLEAN | Excluir de reposición |

#### `tiendas` — Red de Tiendas
| Columna | Tipo | Descripción |
|---------|------|-------------|
| `id` | INTEGER (PK) | ID de tienda |
| `name` | VARCHAR | Nombre de la tienda |
| `city` | VARCHAR | Ciudad |
| `region` | VARCHAR | Región |
| `custom_formato` | VARCHAR | Formato (express, supermercado…) |
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
| `transaction_date` | TIMESTAMP | Fecha y hora del movimiento |

---

### Tablas de Resultados ML

| Tabla | Clave Primaria | Descripción |
|-------|---------------|-------------|
| `pronosticos` | `sku_id + fecha` | Pronósticos Prophet por SKU y día |
| `predicciones_lgbm` | `sku_id + tienda_id` | Predicciones LightGBM por SKU-tienda |
| `anomalias_inventario` | `sku_id + tienda_id` | Anomalías detectadas por Isolation Forest |
| `eoq_resultados` | `sku_id + tienda_id` | Cantidades óptimas de pedido |
| `montecarlo_riesgo` | `sku_id + tienda_id` | Niveles de riesgo simulados |
| `rentabilidad_sku` | `sku_id + tienda_id` | Índice de rentabilidad por SKU-tienda |
| `rotacion_sku` | `sku_id + tienda_id` | Velocidad de rotación de inventario |
| `eficiencia_reposicion` | `tienda_id` | Eficiencia logística por tienda |
| `segmentacion_skus` | `sku_id` | Segmento ABC de cada producto |
| `segmentacion_tiendas` | `tienda_id` | Cluster KMeans de cada tienda |
| `market_basket` | `sku_origen + sku_destino` | Reglas de asociación Apriori |

> **Nota técnica:** Todas las tablas de resultados ML usan **claves primarias naturales o compuestas** (sin columna `id` serial), ya que son creadas/reemplazadas por `pandas.to_sql()` en cada ejecución del modelo.

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

### 3. Isolation Forest — Detección de Anomalías
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
- **Calcula:** probabilidad de quiebre de stock, nivel de riesgo clasificado en BAJO / MEDIO / ALTO
- **Tabla resultado:** `montecarlo_riesgo`

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

---

## 🌐 API REST

**Base URL:** `http://localhost:8000/api/v1`  
**Documentación interactiva:** `http://localhost:8000/api/docs`

### Autenticación
| Método | Endpoint | Descripción | Auth |
|--------|---------|-------------|------|
| `POST` | `/auth/login` | Obtener token JWT | ❌ |
| `GET` | `/auth/me` | Perfil del usuario actual | ✅ |

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
| `GET` | `/inventory/montecarlo` | Simulaciones Monte Carlo | viewer |
| `POST` | `/inventory/run/anomalies` | ▶ Ejecutar Isolation Forest | analyst |
| `POST` | `/inventory/run/eoq` | ▶ Ejecutar modelo EOQ | analyst |
| `POST` | `/inventory/run/montecarlo` | ▶ Ejecutar Monte Carlo | analyst |

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

---

## 💻 Frontend

Aplicación SPA construida con **React 18 + Vite**, que consume la API REST y visualiza los resultados con **Recharts**.

### Páginas

| Ruta | Página | Visualizaciones |
|------|--------|----------------|
| `/` | Dashboard | KPIs globales + barras de demanda top SKUs |
| `/demand` | Demanda | Líneas Prophet + scatter LightGBM |
| `/inventory` | Inventario | Pastel anomalías + barras Monte Carlo + tabla EOQ |
| `/analytics` | Analítica | Barras rentabilidad + pastel rotación + barras eficiencia |
| `/products` | Productos | Pastel ABC + barras Market Basket + tablas detalle |
| `/stores` | Tiendas | Catálogo de tiendas con segmento KMeans |
| `/login` | Login | Formulario de autenticación JWT |

### Componentes Clave

| Componente | Descripción |
|-----------|-------------|
| `Layout.jsx` | Barra lateral de navegación + header con usuario y botón logout |
| `RunModelBtn.jsx` | Botón que ejecuta un modelo ML, muestra estado y refresca datos con `onSuccess` callback |
| `KPICard.jsx` | Tarjeta de métrica con ícono, valor principal y etiqueta descriptiva |
| `AuthContext.jsx` | Contexto React global con token JWT, datos de usuario y función de logout |
| `client.js` | Instancia de Axios con interceptor que inyecta el header `Authorization: Bearer <token>` |

---

## 📊 Explicación de Gráficas

### 🏠 Dashboard

#### Barras — Demanda Estimada: Top 8 SKUs
Muestra los 8 productos con mayor demanda estimada. Cada barra representa un SKU y su altura indica las unidades proyectadas. De un vistazo permite identificar qué productos necesitan prioridad en el abastecimiento y cuáles tienen mayor presión de venta.

---

### 📈 Demanda

#### Líneas — Pronóstico Prophet: Top 5 SKUs (30 días)
Proyección de ventas para los próximos 30 días. Cada línea de color corresponde a un SKU diferente. Una línea ascendente indica crecimiento de demanda; descendente, reducción. Se usa para planificar compras, transferencias entre tiendas y negociaciones con proveedores con anticipación.

#### Dispersión (Scatter) — LightGBM: Real vs Predicho
Compara el valor real de ventas (eje Y) contra el valor predicho por el modelo (eje X). Cuando los puntos se concentran sobre la diagonal perfecta `y = x`, el modelo predice con alta precisión. Puntos muy dispersos indican oportunidad de mejorar el modelo con más datos o mejores features.

---

### 📦 Inventario

#### Pastel — Tipos de Anomalías (Isolation Forest)
Clasifica las anomalías detectadas por tipo: **sobrestock** (exceso acumulado), **quiebre de stock** (agotamiento) y **stock congelado** (sin movimiento). Cada segmento representa la proporción de cada tipo sobre el total de anomalías, permitiendo priorizar el tipo de problema a resolver primero.

#### Barras — Monte Carlo: Nivel de Riesgo de Quiebre
Resultado de 10,000 simulaciones que evalúan la probabilidad de agotarse antes del próximo reabastecimiento. Agrupa los SKUs por nivel: **BAJO** (sin urgencia), **MEDIO** (monitorear) y **ALTO** (reposición inmediata). Las barras más altas en riesgo ALTO representan la alerta más crítica para operaciones.

#### Tabla — EOQ: Cantidad Óptima de Pedido por SKU-Tienda
Guía operativa para el equipo de compras. Muestra por cada combinación producto-tienda: la cantidad exacta a pedir (EOQ), el punto de reorden en unidades, el stock de seguridad recomendado y el estado actual (OK / Reponer / Crítico).

---

### 💰 Analítica

#### Barras — Índice de Rentabilidad: Top SKUs
Ranking de los productos más rentables según el índice que combina margen porcentual y volumen de ventas. Las barras más altas son los SKUs que generan mayor valor económico para la empresa. Guía decisiones de pricing, negociación con proveedores y foco comercial.

#### Pastel — Clasificación de Rotación de SKUs
Distribuye el catálogo en tres categorías de velocidad de venta: **Alta rotación** (se venden rápido, mantener stock), **Media rotación** (monitorear) y **Baja rotación** (capital inmovilizado, evaluar descuento o liquidación). Un segmento grande en baja rotación es una señal de alerta financiera.

#### Barras Horizontales — Eficiencia de Reposición por Tienda
Compara el desempeño logístico de cada tienda combinando cobertura de reposición, tasa de devolución y eficiencia de SKUs activos. Las tiendas con barra corta tienen procesos logísticos deficientes y requieren revisión operativa o apoyo adicional.

---

### 🛒 Productos

#### Pastel — Segmentación ABC de SKUs
Clasifica el catálogo según el principio de Pareto:
- **Segmento A** — pocos SKUs que generan el **70% de las ventas** → máxima prioridad, nunca deben faltar
- **Segmento B** — SKUs de rotación media que aportan el **20% de ventas** → mantener con buffer moderado
- **Segmento C** — mayoría de SKUs con solo el **10% de ventas** → revisar si justifican espacio en anaquel

#### Barras Horizontales — Market Basket: Productos Más Comprados Juntos (Lift)
Visualiza las reglas de asociación más fuertes entre productos. El **Lift** mide la intensidad de la relación entre dos SKUs:
- `Lift > 1` → la relación es real, no casualidad
- `Lift > 2` → relación fuerte → ubicar juntos en la tienda
- `Lift > 3` → relación muy fuerte → crear bundle o promoción cruzada

Las barras más largas indican los pares de productos con mayor potencial para estrategias de cross-selling.

---

## ⚙️ Instalación y Ejecución

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

# 5. Crear usuario administrador inicial
python scripts/create_admin.py

# 6. Iniciar el servidor
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

## 📄 Licencia

Proyecto desarrollado para **Go Retail** — 2026.  
Todos los derechos reservados.

# SocialGenOpt

**Sistema Inteligente de Optimización de Estrategias de Publicación en Redes Sociales mediante Algoritmos Genéticos Multiobjetivo (NSGA-II)**

---

## Descripción

SocialGenOpt es un sistema basado en algoritmos genéticos multiobjetivo (NSGA-II) que optimiza la planificación semanal de publicaciones en redes sociales para creadores de contenido, pequeñas empresas y emprendedores.

El sistema evalúa múltiples configuraciones de calendario de contenido considerando datos históricos de interacción y restricciones operativas, con el objetivo de:

- **Maximizar** el engagement total semanal, el alcance estimado y la retención promedio por publicación.
- **Minimizar** la saturación de audiencia y el tiempo total de producción requerido.

Las salidas del sistema incluyen la frontera de Pareto, gráfica de evolución por generación, tabla comparativa de los mejores individuos y un calendario visual semanal optimizado.

---

## Estructura del Proyecto

El proyecto está diseñado como un **monolito**, donde cada carpeta cumple una responsabilidad clara:

```
NSGA-II/
├── data/
│   └── knowledge_base.csv      # Base de conocimiento 
├── src/
│   ├── algorithm/               # Núcleo del algoritmo genético multiobjetivo (NSGA-II)
│   ├── domain/                  # Modelos de dominio y entidades del problema
│   ├── knowledge/               # Lógica de acceso y procesamiento de la base de conocimiento
│   ├── output/                  #Funciones para imprimir resultados en consola.
│   └── utils/                   # Utilidades compartidas
├── static/
│   ├── index.html               # Interfaz visual (Vanilla JS)
│   ├── script.js
│   └── styles.css
├── api.py                       # Definición de rutas HTTP y configuración de CORS (solo enrutamiento)
├── main.py                      # Punto de entrada; carga parámetros desde .env o usa valores por defecto
├── .env                         # Variables de entorno (opcional)
├── pyproject.toml
├── poetry.lock
└── Dockerfile
```

> `api.py` actúa exclusivamente como capa de enrutamiento y gestión de CORS. Toda la lógica reside en `src/`.

---

##  Instalación con Poetry

Este proyecto utiliza **Poetry 2.3.3** como gestor de dependencias.

### 1. Instalar Poetry

####  macOS
```bash
curl -sSL https://install.python-poetry.org | python3 -
```

####  Linux
```bash
curl -sSL https://install.python-poetry.org | python3 -
```
Agrega Poetry al PATH si no se detecta automáticamente:
```bash
export PATH="$HOME/.local/bin:$PATH"
```

####  Windows (PowerShell)
```powershell
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -
```
Luego agrega `%APPDATA%\Python\Scripts` al PATH del sistema si es necesario.

---

### 2. Instalar dependencias del proyecto

Desde la **carpeta raíz** del proyecto:

```bash
poetry install
```

Esto creará el entorno virtual e instalará todas las dependencias declaradas en `pyproject.toml`.

---

## 🚀 Ejecución con Poetry

```bash
poetry run python main.py
```

El programa tomará los parámetros definidos en el archivo `.env` si este existe en la raíz del proyecto. En caso de que **no haya un `.env`**, se utilizarán los **valores por defecto definidos en `main.py`**.

### Ejemplo de `.env`
```env
# Parámetros del algoritmo evolutivo
POPULATION_SIZE=100
GENERATIONS=200
CROSSOVER_PROB=0.6
MUTATION_RATE=0.8

# Parámetros del problema
MAX_POSTS=15
HOURS_AVAILABLE=10

# Configuración general
SEED=42
OUTPUT_DIR=./output_nsga2  #Generación de resultados: Pareto, tablas, calendarios
PLATFORM=instagram

```

---

## 🐳 Ejecución con Docker

### 1. Construir la imagen

Desde la carpeta raíz del proyecto (donde se encuentra el `Dockerfile`):

```bash
docker build -t socialgenopt .
```

### 2. Inicializar el contenedor

```bash
docker run -d -p 8000:8000 socialgenopt
```

> Si deseas pasar variables de entorno personalizadas, puedes usar `--env-file`:
> ```bash
> docker run -d -p 8000:8000 --env-file .env socialgenopt
> ```

### 3. Acceder a la interfaz web

Una vez levantado el contenedor, abre tu navegador en:

```
http://localhost:8000
```

---

## 📊 Entradas y Salidas del Sistema

### Entradas
| Parámetro | Descripción |
|---|---|
| `MAX_POSTS` | Número máximo de publicaciones semanales |
| `AVAILABLE_HOURS` | Horas disponibles para creación de contenido |
| `PLATFORM` | Plataforma objetivo (instagram, tiktok, youtube) |
| `TAMAÑO DE POBLACIÓN` | Cantidad de soluciones (individuos) que existen en cada generación|
| `TASA DE MUTACIÓN` | Probabilidad de que un individuo cambie aleatoriamente|
| `NÚMERO DE GENERACIONES` | Cuántas veces repites el ciclo evolutivo|

### Salidas
- Gráfica de evolución de aptitud por generación
- Frontera de Pareto interactiva
- Tabla comparativa de los 3 mejores individuos (día, hora, tipo de contenido, engagement, alcance, saturación)
- Calendario visual semanal optimizado
- Comparación entre estrategia aleatoria inicial vs. estrategia optimizada

---

##  Requisitos

- Python 3.10+
- Poetry 2.3.3
- Docker 29.2.1

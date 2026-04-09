# Unexum - Gestor Académico Inteligente

**Unexum** es una herramienta integral diseñada para estudiantes de ingeniería (específicamente UNEXPO-VRB), desarrollada como un **sistema de soporte a la decisión académica**. La aplicación trasciende la función de una calculadora de notas tradicional para ofrecer planificación semestral, visualización del progreso curricular y solución automática de horarios sin conflictos.

---

## 🌟 Funcionalidades Principales

El sistema actúa como un asistente que valida las normativas universitarias para facilitar la gestión estudiantil:

* **Planificación Curricular:** Visualización interactiva del "Pensum" (plan de estudios). El sistema determina qué asignaturas son inscribibles basándose en el historial académico, verificando automáticamente prelaciones, correquisitos y unidades de crédito acumuladas.
* **Proyección de Índice:** Cálculo preciso del índice académico mediante el ingreso de calificaciones (escala 1-9 o 0-100), permitiendo proyectar el cumplimiento de requisitos para menciones honoríficas (Cum Laude / Summa Cum Laude).
* **Generador Automático de Horarios:** Módulo que automatiza la creación de horarios. A partir de las materias deseadas, el algoritmo genera matemáticamente todas las combinaciones posibles, filtrando cruces de horario y presentando opciones viables.
* **Control de Evaluaciones:** Seguimiento detallado de evaluaciones parciales. La herramienta calcula la calificación necesaria en evaluaciones restantes para aprobar o repetir una asignatura.

---

## 🚀 Fundamentos de Ingeniería

Este proyecto demuestra la aplicación de principios de **Ingeniería Industrial** e **Investigación de Operaciones** en el desarrollo de software, enfocándose en la lógica algorítmica y la optimización de recursos.

### 1. Algoritmo de Optimización Combinatoria

La generación de horarios se aborda como un problema combinatorio complejo.

* **El Problema:** La combinación de múltiples materias con diversas secciones genera un espacio de búsqueda exponencial, resultando en cientos de permutaciones, muchas de ellas inválidas.
* **La Solución:** Se implementó un algoritmo basado en el **Producto Cartesiano** (utilizando `itertools`). El sistema evalúa todas las permutaciones, aplica restricciones lógicas (choques de tiempo) y optimiza la presentación de resultados para la toma de decisiones.

### 2. Modelado de Dependencias (Grafos)

El plan de estudios se modela como un sistema de dependencias o grafo dirigido.

* Cada asignatura funciona como un nodo con requisitos de entrada (prelaciones).
* El sistema recorre la estructura en tiempo real: al cambiar el estado de una asignatura (ej. "Aprobada"), se recalcula la disponibilidad de los nodos subsiguientes, garantizando la integridad de la ruta académica.

### 3. Persistencia y Seguridad de Datos

* **Almacenamiento Local:** Uso de estructuras JSON para la persistencia de datos, eliminando la dependencia de conexión continua a internet.
* **Portabilidad:** Sistema de copias de seguridad (Backup) con compresión ZIP, permitiendo la migración segura de datos entre dispositivos.

---

## 🛠️ Tecnologías Utilizadas

* **Lenguaje:** [Python](https://www.python.org/) (Lógica y algoritmos).
* **Framework UI:** [Kivy](https://kivy.org/) & [KivyMD](https://kivymd.readthedocs.io/) (Interfaz táctil adaptativa basada en Material Design).
* **Análisis de Datos:** `Matplotlib` (Generación de gráficos estadísticos de rendimiento).
* **Gestión de Datos:** `json`, `shutil`, `zipfile` (Manipulación de archivos y backups).
* **Reportes:** `FPDF` (Exportación de horarios generados a formato PDF).
* **Integración Móvil:** `pyjnius`, `androidstorage4kivy` (Interacción con el sistema de archivos y permisos de Android).

---

## 📂 Estructura del Proyecto

El código fuente sigue una arquitectura modular para asegurar la escalabilidad y el mantenimiento:

```text
unexum/
│
├── assets/                  # Recursos estáticos (Imágenes, fuentes, iconos).
├── src/                     # Código Fuente
│   ├── main.py              # Punto de entrada y orquestador de la aplicación.
│   ├── data_manager.py      # Módulo de persistencia de datos.
│   ├── android_permissions.py # Gestión de permisos del sistema operativo.
│   │
│   ├── models/              # Definición de Estructuras de Datos
│   │   └── models.py        # Clases principales: Materia, Evaluación.
│   │
│   ├── views/               # Capa de Presentación
│   │   ├── screens.py       # Lógica de pantallas (Login, Horario).
│   │   └── custom_widgets.py # Componentes gráficos reutilizables.
│   │
│   └── utils/               # Utilidades y Lógica Auxiliar
│       ├── calculations.py  # Motores de cálculo (Interpolación).
│       └── constants.py     # Variables globales de configuración.
│
└── README.md                # Documentación del proyecto.

```

---

## 🔧 Instalación y Ejecución

### Usuario Final (Android)

1. Encuentra la ficha de la playstore en: [UNEXUM](https://play.google.com/store/apps/details?id=org.unexum.unexum)
2. Instalar en el dispositivo Android.
3. Ejecutar la aplicación (no requiere conexión permanente).

## 📄 Licencia

Este proyecto se distribuye bajo la licencia **MIT**, permitiendo su uso, modificación y distribución libre con la debida atribución. Consulte el archivo `LICENSE` para más detalles.

---

**Desarrollado por Salomón Barrera**
*Ingeniería Industrial y Desarrollo de Software*

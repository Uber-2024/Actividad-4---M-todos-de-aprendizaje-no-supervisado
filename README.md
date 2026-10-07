# Sistema de aprendizaje no supervisado

¿Cómo funciona?

Este proyecto es un prototipo de análisis exploratorio de datos en un sistema de transporte. Su objetivo no es predecir una etiqueta conocida, sino descubrir patrones ocultos en los viajes usando técnicas de agrupamiento no supervisado (clustering).

La idea principal es generar un dataset sintético a partir de una red de estaciones, aplicar varios algoritmos sin usar etiquetas previas y evaluar cuál método forma grupos más claros usando métricas como silueta, Calinski-Harabasz y Davies-Bouldin.

En otras palabras, el sistema no clasifica viajes con un modelo entrenado sobre etiquetas; lo que hace es encontrar perfiles naturales de viaje (por ejemplo, hora punta, trayectos tranquilos o viajes con incidencia) a partir de las características operativas del dataset.

## 1. Objetivo del proyecto

El sistema busca responder a una pregunta concreta:

> ¿Qué perfiles de viaje se pueden descubrir automáticamente a partir de las condiciones operativas, sin conocer de antemano las categorías?

Para resolverlo, se trabaja con variables como:

- tiempo planificado del viaje
- hora de salida
- día de la semana
- si es fin de semana
- lluvia
- nivel de ocupación
- si hay incidencia
- número de transbordos
- duración real observada del viaje

El dataset también incluye una columna oculta `trip_profile` (hora punta, viaje tranquilo o viaje con incidencia). Esa etiqueta **no se usa** para agrupar: solo sirve para entender que el dataset tiene estructura recuperable. Los algoritmos trabajan sin verla.

La solución compara tres métodos:

- K-Means
- clustering aglomerativo
- DBSCAN

## 2. Cómo está organizado el proyecto

- [app.py](app.py): contiene la lógica del planificador de rutas y el modelo de red de transporte.
- [network.json](network.json): define la red de estaciones y conexiones que se usa para generar viajes sintéticos.
- [aprendizaje_no_supervisado/generate_dataset.py](aprendizaje_no_supervisado/generate_dataset.py): crea viajes sintéticos reproducibles a partir de la red, con perfiles latentes.
- [aprendizaje_no_supervisado/cluster_model.py](aprendizaje_no_supervisado/cluster_model.py): prepara los datos, compara los algoritmos y guarda las métricas de calidad.
- [aprendizaje_no_supervisado/test_unsupervised_learning.py](aprendizaje_no_supervisado/test_unsupervised_learning.py): valida la integridad del dataset y el flujo principal del proyecto.
- [aprendizaje_no_supervisado/data/trips.csv](aprendizaje_no_supervisado/data/trips.csv): archivo generado con los viajes sintéticos.
- [aprendizaje_no_supervisado/artifacts/metrics.json](aprendizaje_no_supervisado/artifacts/metrics.json): resultados finales de evaluación por algoritmo.
- [aprendizaje_no_supervisado/artifacts/trips_clustered.csv](aprendizaje_no_supervisado/artifacts/trips_clustered.csv): viajes con la etiqueta de cluster de K-Means.
- [aprendizaje_no_supervisado/artifacts/kmeans.joblib](aprendizaje_no_supervisado/artifacts/kmeans.joblib): modelo serializado de K-Means para reutilización posterior.
- [web_app.py](web_app.py): servidor web que sirve la interfaz y atiende las operaciones de generación, clustering y exportación.
- [web/index.html](web/index.html): interfaz principal del dashboard.
- [web/styles.css](web/styles.css): estilos visuales de la aplicación web.
- [web/app.js](web/app.js): valida entradas del usuario, coordina llamadas al backend y presenta resultados en lenguaje sencillo.

## 3. Flujo completo del proyecto

El proyecto sigue este flujo lógico:

1. Se define la red de transporte en [network.json](network.json), con estaciones y conexiones entre ellas.
2. El archivo [aprendizaje_no_supervisado/generate_dataset.py](aprendizaje_no_supervisado/generate_dataset.py) calcula rutas válidas entre estaciones usando el planificador de rutas de [app.py](app.py).
3. Se genera un dataset sintético de viajes con variables operativas simuladas y tres perfiles latentes ocultos: hora punta, viaje tranquilo y viaje con incidencia.
4. El script [aprendizaje_no_supervisado/cluster_model.py](aprendizaje_no_supervisado/cluster_model.py) selecciona las características numéricas relevantes, imputa valores faltantes y normaliza los datos.
5. Se aplican tres algoritmos de clustering (K-Means, aglomerativo y DBSCAN) y se comparan sus métricas de calidad.
6. Se guarda el reporte de resultados en [aprendizaje_no_supervisado/artifacts/metrics.json](aprendizaje_no_supervisado/artifacts/metrics.json), junto con una versión etiquetada en CSV y el modelo serializado de K-Means.
7. La interfaz web en [web/index.html](web/index.html) permite ejecutar estos pasos desde el navegador y explicar el resultado en lenguaje sencillo.

## 4. Requisitos previos

Necesitas tener Python 3 instalado y las dependencias del proyecto.

Primero, desde la carpeta raíz del proyecto, instala las librerías:

```powershell
python -m pip install -r .\aprendizaje_no_supervisado\requirements.txt
```

Si prefieres trabajar en un entorno virtual, puedes crear uno antes de instalar:

```powershell
py -3 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r .\aprendizaje_no_supervisado\requirements.txt
```

Las dependencias principales son:

- `pandas`: lectura y manejo tabular del dataset.
- `scikit-learn`: preprocesamiento, clustering y evaluación de los grupos.
- `joblib`: guardado del modelo de K-Means.
- `openpyxl`: creación del archivo de comparación en formato Excel (`.xlsx`).

También necesitas tener acceso a la carpeta raíz para ejecutar correctamente los scripts del proyecto.

## 5. Paso a paso: ejecutar el proyecto sin la interfaz web

### Paso 1: crear un entorno virtual (opcional, recomendado)

```powershell
py -3 -m venv .venv
.venv\Scripts\Activate.ps1
```

### Paso 2: instalar dependencias

```powershell
python -m pip install -r .\aprendizaje_no_supervisado\requirements.txt
```

### Paso 3: generar el dataset sintético

```powershell
python .\aprendizaje_no_supervisado\generate_dataset.py
```

Esto crea o actualiza el archivo:

- [aprendizaje_no_supervisado/data/trips.csv](aprendizaje_no_supervisado/data/trips.csv)

Este script:

- lee la red desde [network.json](network.json)
- calcula rutas entre estaciones
- genera registros aleatorios con semilla fija
- crea tres perfiles latentes de viaje (hora punta, viaje tranquilo, viaje con incidencia)
- agrega columnas como hora, lluvia, ocupación, incidencias y duración real simulada

### Paso 4: comparar los métodos de clustering

```powershell
python .\aprendizaje_no_supervisado\cluster_model.py
```

Esto:

- carga el CSV generado
- normaliza las variables numéricas
- aplica K-Means, clustering aglomerativo y DBSCAN
- calcula silueta, Calinski-Harabasz y Davies-Bouldin
- guarda resultados en [aprendizaje_no_supervisado/artifacts/metrics.json](aprendizaje_no_supervisado/artifacts/metrics.json)
- serializa el modelo de K-Means en [aprendizaje_no_supervisado/artifacts/kmeans.joblib](aprendizaje_no_supervisado/artifacts/kmeans.joblib)
- escribe una copia etiquetada en [aprendizaje_no_supervisado/artifacts/trips_clustered.csv](aprendizaje_no_supervisado/artifacts/trips_clustered.csv)

### Paso 5: validar el flujo con pruebas automáticas

```powershell
python -m unittest discover -s aprendizaje_no_supervisado -v
```

Las pruebas comprueban que:

- el dataset tiene la estructura esperada
- existen los tres perfiles latentes
- el clustering no usa la etiqueta oculta `trip_profile`
- el flujo principal produce métricas válidas para los tres métodos

## 6. Paso a paso: usar la interfaz web

La interfaz permite probar el proyecto sin escribir comandos manuales. Las operaciones se realizan en orden: crear ejemplos, agrupar y comparar y, si se desea, descargar la comparación. Los resultados se explican con palabras sencillas pensadas para principiantes.

### Paso 1: arrancar el servidor

Desde la raíz del proyecto:

```powershell
python .\web_app.py
```

Si todo está bien, verás un mensaje similar a:

```text
Servidor web activo en http://127.0.0.1:8002
```

### Paso 2: abrir la aplicación

En el navegador accede a:

```text
http://127.0.0.1:8002
```

### Paso 3: elegir las opciones

La pantalla permite configurar:

- Cantidad de viajes: cuántos ejemplos sintéticos se crearán, entre 50 y 10 000.
- Número para repetir la prueba: si se mantiene el mismo número, se generan los mismos ejemplos.

### Paso 4: generar el dataset

Haz clic en **1. Crear viajes de ejemplo**. La aplicación confirma cuántos viajes creó y te indica que continúes con la comparación.

### Paso 5: agrupar y comparar

Haz clic en **2. Agrupar y comparar**. El programa prepara y compara tres métodos:

- cortar en k montones (K-Means)
- unir de abajo hacia arriba (aglomerativo)
- buscar densidades (DBSCAN)

Para comparar, utiliza el conjunto de ejemplos creado. Los ejemplos son sintéticos, no registros reales de viajes. Los algoritmos no ven la etiqueta oculta de perfil.

### Paso 6: entender los resultados

La pantalla explica el resultado en lenguaje sencillo y marca el método con grupos más claros:

- **Claridad de los grupos:** se traduce a Débil, Regular, Bueno o Muy claro. Detrás usa la silueta. Más alto es mejor.
- **Montones:** cuántos grupos distintos encontró el método.
- **Viajes sin grupo:** cuántos viajes quedaron fuera (sobre todo en DBSCAN). Cero significa que todos entraron en algún montón.

El resumen principal corresponde al método con mayor silueta. Las tarjetas y la tabla permiten comparar cada método. Los números técnicos están disponibles en **Ver números técnicos (opcional)**.

### Paso 7: empezar otra prueba o exportar

Usa **Borrar resultados** para limpiar la comparación visible. Crear nuevos viajes también quita los resultados anteriores para evitar confusiones. **Descargar Excel** guarda un archivo `.xlsx`; la fila de mayor silueta queda resaltada.

La interfaz envía las métricas al endpoint `POST /api/export-comparison`. El servidor crea el libro en memoria y lo descarga sin guardar una copia adicional dentro del proyecto. Si aún no hay resultados, la interfaz indica que primero debes crear los ejemplos y agruparlos.

## 7. Qué significa cada métrica

### Claridad / Silueta (Silhouette)

Mide qué tan bien pertenece cada viaje a su grupo frente a los demás.

- Cuanto más cerca de 1, mejor.
- Valores cercanos a 0 indican solapamiento entre grupos.
- Valores negativos sugieren asignaciones dudosas.

En la interfaz se muestra primero como palabra fácil:

- **Muy claro:** los grupos se distinguen bastante bien.
- **Bueno:** se notan grupos útiles, con algo de mezcla.
- **Regular:** hay grupos, pero se solapan bastante.
- **Débil:** cuesta ver una separación clara.

### Compactación / Calinski-Harabasz (CH)

Compara la dispersión entre grupos con la dispersión dentro de cada grupo.

- Cuanto más alto, mejor.
- Indica montones más compactos y mejor separados.

### Solapamiento / Davies-Bouldin (DB)

Estima el promedio de similitud entre cada grupo y su vecino más parecido.

- Cuanto más bajo, mejor.
- Indica menos confusión o mezcla entre montones.

## 8. Cómo interpretar un resultado exitoso

Un resultado bueno suele presentar:

- silueta alta (claridad Buena o Muy clara)
- Calinski-Harabasz alto
- Davies-Bouldin bajo
- un número de clusters cercano a los 3 perfiles latentes del dataset

Por ejemplo, si K-Means obtiene una silueta cercana a 0.30 y Davies-Bouldin cercano a 1.4, eso indica que se formaron grupos útiles, aunque todavía con algo de mezcla. Si otro método supera esa silueta, la interfaz lo marcará como ganador.

## 9. Dependencias y archivos de salida

### Dataset generado

- [aprendizaje_no_supervisado/data/trips.csv](aprendizaje_no_supervisado/data/trips.csv)

### Resultados del clustering

- [aprendizaje_no_supervisado/artifacts/metrics.json](aprendizaje_no_supervisado/artifacts/metrics.json)
- [aprendizaje_no_supervisado/artifacts/trips_clustered.csv](aprendizaje_no_supervisado/artifacts/trips_clustered.csv)

### Modelo serializado

- [aprendizaje_no_supervisado/artifacts/kmeans.joblib](aprendizaje_no_supervisado/artifacts/kmeans.joblib)

## 10. Solución de problemas comunes

### El comando de instalación falla

Verifica que tengas Python 3 y que estés ejecutando el comando desde la raíz del proyecto.

```powershell
python --version
```

### No existe el archivo CSV

Primero genera el dataset:

```powershell
python .\aprendizaje_no_supervisado\generate_dataset.py
```

### El clustering no encuentra el dataset

Asegúrate de que la carpeta [aprendizaje_no_supervisado/data](aprendizaje_no_supervisado/data) exista y que se haya generado el archivo `trips.csv`.

### La interfaz web no abre

Comprueba que el servidor está ejecutándose:

```powershell
python .\web_app.py
```

Y luego entra a:

```text
http://127.0.0.1:8002
```

Si ves `ERR_CONNECTION_REFUSED`, lo más probable es que el servidor no esté arrancado.

### El proyecto no carga funciones del backend

Asegúrate de que estás ejecutando el servidor desde la raíz correcta y que la estructura del proyecto no ha sido modificada.

## 11. Resumen práctico

El proyecto sigue una lógica clara:

1. crear red de transporte
2. generar viajes sintéticos con perfiles latentes
3. aplicar métodos de clustering
4. comparar métricas de calidad
5. validar resultados
6. probar desde la interfaz web

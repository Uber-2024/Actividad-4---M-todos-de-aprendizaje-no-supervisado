// Se definen los elementos del DOM que se van a manipular para controlar la interfaz.
const sampleSizeInput = document.getElementById('sampleSize');
const seedInput = document.getElementById('seed');
const generateBtn = document.getElementById('generateBtn');
const clusterBtn = document.getElementById('clusterBtn');
const clearBtn = document.getElementById('clearBtn');
const exportBtn = document.getElementById('exportBtn');
const statusBox = document.getElementById('status');
const resultBox = document.getElementById('resultBox');
const chartBox = document.getElementById('chart');
const emptyState = document.getElementById('emptyState');
const methodCards = document.getElementById('methodCards');
const claritySummary = document.getElementById('claritySummary');
const clustersSummary = document.getElementById('clustersSummary');
const noiseSummary = document.getElementById('noiseSummary');
const winnerTitle = document.getElementById('winnerTitle');
const winnerExplain = document.getElementById('winnerExplain');
const winnerCard = document.getElementById('winnerCard');
const comparisonTable = document.getElementById('comparisonTable');

// Últimas métricas recibidas del backend; se usan al exportar el Excel.
let lastMetrics = null;

// Orden fijo de los tres métodos de clustering en la interfaz.
const MODEL_ORDER = ['kmeans', 'agglomerative', 'dbscan'];

// Nombres largos pensados para principiantes.
const NAMES_MAP = {
  kmeans: 'Cortar en k montones (K-Means)',
  agglomerative: 'Unir de abajo hacia arriba (Aglomerativo)',
  dbscan: 'Buscar densidades (DBSCAN)',
};

// Nombres cortos para badges, gráficos y mensajes de estado.
const SHORT_NAMES = {
  kmeans: 'K-Means',
  agglomerative: 'Aglomerativo',
  dbscan: 'DBSCAN',
};

// Explicación breve de qué hace cada método.
const METHOD_BLURBS = {
  kmeans: 'Parte los viajes en un número fijo de carpetas y busca el centro de cada una.',
  agglomerative: 'Empieza con viajes sueltos y va uniendo los más parecidos.',
  dbscan: 'Busca zonas densas de viajes parecidos y puede dejar fuera los raros.',
};

/**
 * Unifica las métricas que llegan del clustering y las cargadas desde el archivo guardado.
 * @param {object} data Respuesta del backend o reporte persistido.
 * @returns {object} Diccionario de métricas por método.
 */
function readMetricsSource(data) {
  return data && (data.results || data.models) ? (data.results || data.models) : {};
}

/**
 * Actualiza el estado visual del panel de mensajes para informar éxito o error.
 * @param {string} message Texto a mostrar al usuario.
 * @param {boolean} [isError=false] Si es true, usa el estilo de error.
 */
function setStatus(message, isError = false) {
  statusBox.textContent = message;
  statusBox.style.background = isError ? 'rgba(239, 68, 68, 0.14)' : 'rgba(59, 130, 246, 0.15)';
  statusBox.style.borderColor = isError ? 'rgba(248, 113, 113, 0.3)' : 'rgba(96, 165, 250, 0.3)';
}

/**
 * Muestra el JSON recibido en el panel técnico para facilitar la depuración.
 * @param {object} data Objeto que se convertirá a texto JSON indentado.
 */
function renderJson(data) {
  resultBox.textContent = JSON.stringify(data, null, 2);
}

/**
 * Traduce el valor de silueta a una etiqueta sencilla para principiantes.
 * @param {number} silhouette Coeficiente de silueta del método.
 * @returns {{text: string, level: string, tip: string}} Etiqueta, nivel CSS y consejo.
 */
function clarityLabel(silhouette) {
  if (typeof silhouette !== 'number') {
    return { text: 'Sin dato', level: 'unknown', tip: 'Todavía no hay medida.' };
  }
  if (silhouette >= 0.5) {
    return {
      text: 'Muy claro',
      level: 'great',
      tip: 'Los grupos se distinguen bastante bien.',
    };
  }
  if (silhouette >= 0.35) {
    return {
      text: 'Bueno',
      level: 'good',
      tip: 'Se notan grupos útiles, con algo de mezcla.',
    };
  }
  if (silhouette >= 0.2) {
    return {
      text: 'Regular',
      level: 'ok',
      tip: 'Hay grupos, pero se solapan bastante.',
    };
  }
  return {
    text: 'Débil',
    level: 'weak',
    tip: 'Cuesta ver una separación clara.',
  };
}

/**
 * Devuelve el método con la mayor silueta y sus métricas asociadas.
 * @param {object} data Respuesta con resultados de clustering.
 * @returns {object|null} Mejor método o null si aún no hay datos.
 */
function findBestModel(data) {
  const metricsSource = readMetricsSource(data);
  const models = MODEL_ORDER.map((key) => ({
    key,
    name: NAMES_MAP[key],
    shortName: SHORT_NAMES[key],
    metrics: metricsSource[key],
  })).filter((model) => typeof model.metrics?.silhouette === 'number');

  // Gana quien tenga la silueta más alta (grupos más claros).
  return models.reduce((best, current) =>
    !best || current.metrics.silhouette > best.metrics.silhouette ? current : best, null);
}

/**
 * Presenta el resumen fácil del método ganador en la tarjeta principal.
 * @param {object|null} metrics Datos de comparación o null para estado vacío.
 */
function updateSummary(metrics) {
  const bestModel = findBestModel(metrics);
  if (!bestModel) {
    // Estado inicial: sin comparación todavía.
    claritySummary.textContent = '-';
    clustersSummary.textContent = '-';
    noiseSummary.textContent = '-';
    winnerTitle.textContent = 'Todavía no hay comparación';
    winnerExplain.textContent =
      'Cuando pulses “Agrupar y comparar”, aquí te diremos en lenguaje sencillo qué método formó los grupos más claros.';
    winnerCard.classList.remove('has-winner');
    return;
  }

  // Traduce la silueta a una palabra fácil y completa la explicación.
  const clarity = clarityLabel(bestModel.metrics.silhouette);
  claritySummary.textContent = clarity.text;
  clustersSummary.textContent = String(bestModel.metrics.n_clusters);
  noiseSummary.textContent = bestModel.metrics.n_noise === 0
    ? 'Ninguno'
    : `${bestModel.metrics.n_noise} viajes`;

  winnerCard.classList.add('has-winner');
  winnerTitle.textContent = `Ganó: ${bestModel.shortName}`;
  winnerExplain.textContent =
    `${bestModel.name} formó los grupos más claros (${clarity.text.toLowerCase()}). ` +
    `Encontró ${bestModel.metrics.n_clusters} montones` +
    (bestModel.metrics.n_noise
      ? ` y dejó ${bestModel.metrics.n_noise} viajes sin grupo por ser muy distintos.`
      : ' y no dejó viajes raros fuera.') +
    ` ${clarity.tip}`;
}

/**
 * Construye las tarjetas visuales de cada método con veredicto sencillo.
 * @param {object|null} metrics Datos de comparación.
 */
function buildMethodCards(metrics) {
  const metricsSource = readMetricsSource(metrics);
  const best = findBestModel(metrics);

  if (!best) {
    methodCards.innerHTML = '';
    emptyState.hidden = false;
    return;
  }
  emptyState.hidden = true;

  // Una tarjeta por método, destacando al ganador.
  methodCards.innerHTML = MODEL_ORDER.map((key) => {
    const values = metricsSource[key];
    if (!values) return '';
    const clarity = clarityLabel(values.silhouette);
    const isWinner = best.key === key;
    return `
      <article class="method-card ${isWinner ? 'is-winner' : ''} clarity-${clarity.level}">
        ${isWinner ? '<span class="pill">Mejor en esta prueba</span>' : ''}
        <h4>${NAMES_MAP[key]}</h4>
        <p class="method-blurb">${METHOD_BLURBS[key]}</p>
        <dl class="method-stats">
          <div>
            <dt>Claridad</dt>
            <dd><span class="clarity-tag clarity-${clarity.level}">${clarity.text}</span></dd>
          </div>
          <div>
            <dt>Montones</dt>
            <dd>${values.n_clusters}</dd>
          </div>
          <div>
            <dt>Sin grupo</dt>
            <dd>${values.n_noise === 0 ? 'Ninguno' : values.n_noise}</dd>
          </div>
        </dl>
        <p class="method-verdict">${clarity.tip}</p>
      </article>
    `;
  }).join('');
}

/**
 * Dibuja los paneles técnicos opcionales con silueta, CH y Davies-Bouldin.
 * @param {object|null} metrics Datos de comparación.
 */
function buildChart(metrics) {
  const metricsSource = readMetricsSource(metrics);

  if (!findBestModel(metrics)) {
    chartBox.innerHTML = '';
    return;
  }

  // Configuración de cada métrica técnica: nombre, ayuda y dirección deseable.
  const metricConfig = [
    {
      key: 'silhouette',
      label: 'Silueta (claridad)',
      help: 'Más alto = grupos más claros.',
      better: 'higher',
      color: '#22d3ee',
    },
    {
      key: 'calinski_harabasz',
      label: 'Calinski-Harabasz',
      help: 'Más alto = montones más compactos.',
      better: 'higher',
      color: '#fbbf24',
    },
    {
      key: 'davies_bouldin',
      label: 'Davies-Bouldin',
      help: 'Más bajo = menos mezcla entre grupos.',
      better: 'lower',
      color: '#34d399',
    },
  ];

  const colors = ['#64748b', '#22d3ee', '#34d399'];

  chartBox.innerHTML = metricConfig
    .map(({ key, label, help, better, color }) => {
      const values = MODEL_ORDER.map((modelName) => metricsSource[modelName]?.[key]);
      const numericValues = values.filter((value) => typeof value === 'number');
      const lower = Math.min(...numericValues);
      const upper = Math.max(...numericValues);

      // Lista de valores por método dentro de cada panel.
      const modelRows = MODEL_ORDER
        .map((modelName, index) => {
          const value = metricsSource[modelName]?.[key];
          const displayValue = typeof value !== 'number'
            ? 'Sin dato'
            : key === 'calinski_harabasz'
              ? value.toFixed(1)
              : value.toFixed(3);

          return `
            <div class="model-row">
              <span><span class="tag" style="background:${colors[index]};"></span>${SHORT_NAMES[modelName]}</span>
              <strong>${displayValue}</strong>
            </div>
          `;
        })
        .join('');

      // Mejor valor según si la métrica debe subir o bajar.
      const winnerValue = MODEL_ORDER
        .map((modelName) => metricsSource[modelName]?.[key])
        .filter((value) => typeof value === 'number')
        .reduce((bestValue, current) => {
          if (better === 'lower') return Math.min(bestValue, current);
          return Math.max(bestValue, current);
        }, better === 'lower' ? Number.POSITIVE_INFINITY : Number.NEGATIVE_INFINITY);

      const displayValue = key === 'calinski_harabasz'
        ? winnerValue.toFixed(1)
        : winnerValue.toFixed(3);
      // Porcentaje visual del donut relativo al rango de valores actuales.
      const percent = better === 'lower'
        ? Math.max(20, 100 - ((winnerValue - lower) / Math.max(upper - lower || 1, 1)) * 100)
        : Math.max(20, ((winnerValue - lower) / Math.max(upper - lower || 1, 1)) * 100);

      return `
        <div class="metric-panel">
          <h3>${label}</h3>
          <p class="metric-help">${help}</p>
          <div class="metric-body">
            <div class="donut" style="--value:${percent}; --color:${color};">
              <span class="donut-value">${displayValue}</span>
            </div>
            <div class="model-list">
              ${modelRows}
            </div>
          </div>
        </div>
      `;
    })
    .join('');
}

/**
 * Genera la tabla comparativa sencilla y resalta la fila del mejor método.
 * @param {object|null} data Datos de comparación.
 */
function renderComparisonTable(data) {
  const metricsSource = readMetricsSource(data);
  const best = findBestModel(data);

  if (!best) {
    comparisonTable.innerHTML =
      '<tbody><tr><td colspan="5">Primero crea viajes y luego agrupa para ver la tabla.</td></tr></tbody>';
    return;
  }

  const rows = MODEL_ORDER.map((key) => ({
    key,
    name: NAMES_MAP[key],
    values: metricsSource[key],
  }));

  comparisonTable.innerHTML = `
    <thead>
      <tr>
        <th>Método</th>
        <th>Claridad de los grupos</th>
        <th>Montones</th>
        <th>Viajes sin grupo</th>
        <th>Veredicto fácil</th>
      </tr>
    </thead>
    <tbody>
      ${rows.map((row) => {
        const clarity = clarityLabel(row.values?.silhouette);
        return `
          <tr class="${row.key === best.key ? 'winner-row' : ''}">
            <td>${row.name}</td>
            <td><span class="clarity-tag clarity-${clarity.level}">${clarity.text}</span></td>
            <td>${row.values ? row.values.n_clusters : '-'}</td>
            <td>${row.values ? (row.values.n_noise === 0 ? 'Ninguno' : row.values.n_noise) : '-'}</td>
            <td>${clarity.tip}</td>
          </tr>
        `;
      }).join('')}
    </tbody>
  `;
}

/**
 * Coordina la actualización completa de la vista al recibir métricas del backend.
 * @param {object} data Respuesta con resultados de clustering.
 */
function renderMetrics(data) {
  renderJson(data);
  updateSummary(data);
  buildMethodCards(data);
  buildChart(data);
  renderComparisonTable(data);
  lastMetrics = data;
}

/**
 * Restablece los resultados visibles sin borrar el dataset ni los artefactos guardados.
 */
function clearResults() {
  lastMetrics = null;
  renderJson({ status: 'idle' });
  updateSummary(null);
  buildMethodCards(null);
  buildChart(null);
  renderComparisonTable(null);
  setStatus('Resultados borrados. Vuelve a crear viajes de ejemplo para otra prueba.');
}

/**
 * Solicita al servidor un archivo Excel con las métricas de la comparación actual.
 */
async function exportComparison() {
  if (!findBestModel(lastMetrics)) {
    setStatus('Primero crea los viajes y agrúpalos; después podrás descargar el Excel.', true);
    return;
  }

  setStatus('Preparando archivo Excel...');

  try {
    // Envía las métricas actuales al backend para construir el archivo .xlsx.
    const response = await fetch('/api/export-comparison', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(lastMetrics),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'No se pudo exportar la comparación.');
    }

    // Convierte la respuesta binaria en una descarga iniciada por el navegador.
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'comparacion_clustering.xlsx';
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
    setStatus('Comparación exportada como archivo Excel (.xlsx).');
  } catch (error) {
    setStatus(error.message, true);
  }
}

/**
 * Llama al backend para generar el dataset sintético con la semilla y el tamaño indicados.
 */
async function generateDataset() {
  const sampleSize = Number(sampleSizeInput.value);
  const seed = Number(seedInput.value);

  // Validación de rangos antes de llamar al servidor.
  if (!Number.isInteger(sampleSize) || sampleSize < 50 || sampleSize > 10000) {
    setStatus('Escribe una cantidad entera de viajes entre 50 y 10 000.', true);
    sampleSizeInput.focus();
    return;
  }

  if (!Number.isInteger(seed) || seed < 1 || seed > 9999) {
    setStatus('Escribe un número entero entre 1 y 9 999 para repetir la prueba.', true);
    seedInput.focus();
    return;
  }

  setStatus('Creando viajes de ejemplo...');

  try {
    const response = await fetch('/api/generate-dataset', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ sample_size: sampleSize, seed }),
    });

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || 'No se pudieron crear los viajes de ejemplo.');
    }

    // Al crear viajes nuevos se limpian resultados viejos para evitar confusiones.
    clearResults();
    renderJson(data);
    setStatus(`${data.sample_size} viajes listos. Ahora pulsa “Agrupar y comparar”.`);
  } catch (error) {
    renderJson({ error: error.message });
    setStatus(error.message, true);
  }
}

/**
 * Ejecuta el clustering desde el backend y muestra los resultados en lenguaje sencillo.
 */
async function clusterModel() {
  setStatus('Agrupando viajes y preparando la explicación...');

  try {
    const response = await fetch('/api/cluster-model', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({}),
    });

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || 'No se pudieron comparar los agrupamientos.');
    }

    renderMetrics(data);
    const bestModel = findBestModel(data);
    setStatus(bestModel
      ? `Listo. En esta prueba ganó ${bestModel.shortName}. Mira el resumen en verde.`
      : 'La comparación terminó, pero no hay métricas para mostrar.');
  } catch (error) {
    renderJson({ error: error.message });
    setStatus(error.message, true);
  }
}

/**
 * Carga las métricas almacenadas para mostrar de inmediato el último resultado disponible.
 */
async function loadMetrics() {
  try {
    const response = await fetch('/api/metrics');
    const data = await response.json();
    renderMetrics(data);
    setStatus(findBestModel(data)
      ? 'Se cargó una comparación anterior. Puedes repetir la prueba o descargar el Excel.'
      : 'Empieza pulsando “Crear viajes de ejemplo”.');
  } catch (error) {
    renderJson({ error: 'No se pudieron cargar las métricas.' });
    setStatus('No se pudo cargar una comparación anterior. Puedes crear una prueba nueva.', true);
  }
}

// Registra los eventos de la interfaz para cada botón disponible.
generateBtn.addEventListener('click', generateDataset);
clusterBtn.addEventListener('click', clusterModel);
clearBtn.addEventListener('click', clearResults);
exportBtn.addEventListener('click', exportComparison);

// Inicializa la vista con el estado base y carga cualquier comparación previa.
updateSummary(null);
loadMetrics();

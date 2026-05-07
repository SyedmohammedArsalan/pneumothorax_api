// ── Stats ─────────────────────────────────────────────────────────────────
async function loadStats() {
  const r = await fetch('/api/stats');
  const d = await r.json();

  ['total','pos','neg'].forEach(k => {
    const val = d[k === 'pos' ? 'positive' : k === 'neg' ? 'negative' : 'total'];
    document.getElementById(`h-${k}`).textContent = val;
    document.getElementById(`d-${k}`).textContent = val;
  });
  document.getElementById('d-conf').textContent =
    (d.avg_confidence * 100).toFixed(1) + '%';

  // Donut chart
  new Chart(document.getElementById('donutChart'), {
    type: 'doughnut',
    data: {
      labels: ['Positive', 'Normal'],
      datasets: [{ data: [d.positive, d.negative],
                   backgroundColor: ['#ef4444','#10b981'], borderWidth: 0 }]
    },
    options: { plugins: { legend: { labels: { color: '#e2e8f0' }}},
               cutout: '65%' }
  });
}

// Global stats (static reference data)
new Chart(document.getElementById('barChart'), {
  type: 'bar',
  data: {
    labels: ['USA','UK','Germany','Australia','Pakistan','India','Canada'],
    datasets: [{
      label: 'Cases per 100k',
      data: [18, 15, 12, 14, 8, 7, 16],
      backgroundColor: '#3b82f6'
    }]
  },
  options: {
    plugins: { legend: { labels: { color: '#e2e8f0' }}},
    scales: {
      x: { ticks: { color: '#64748b' }, grid: { color: '#1e293b' }},
      y: { ticks: { color: '#64748b' }, grid: { color: '#1e293b' }}
    }
  }
});

new Chart(document.getElementById('lineChart'), {
  type: 'line',
  data: {
    labels: ['0-10','11-20','21-30','31-40','41-50','51-60','60+'],
    datasets: [{
      label: 'Risk Score',
      data: [2, 15, 28, 18, 12, 9, 6],
      borderColor: '#f59e0b', backgroundColor: 'rgba(245,158,11,0.1)',
      tension: 0.4, fill: true
    }]
  },
  options: {
    plugins: { legend: { labels: { color: '#e2e8f0' }}},
    scales: {
      x: { ticks: { color: '#64748b' }, grid: { color: '#1e293b' }},
      y: { ticks: { color: '#64748b' }, grid: { color: '#1e293b' }}
    }
  }
});

// ── History ───────────────────────────────────────────────────────────────
async function loadHistory() {
  const r    = await fetch('/api/history');
  const data = await r.json();
  const el   = document.getElementById('historyTable');

  if (!data.length) {
    el.innerHTML = '<p style="color:var(--muted)">No scans yet.</p>';
    return;
  }

  el.innerHTML = `
    <div class="history-row header">
      <span>#</span><span>Filename</span><span>Result</span>
      <span>Confidence</span><span>Date</span>
    </div>
    ${data.map(s => `
    <div class="history-row">
      <span style="color:var(--muted)">${s.id}</span>
      <span>${s.filename}</span>
      <span class="${s.has_ptx ? 'tag-pos' : 'tag-neg'}">
        ${s.has_ptx ? '⚠️ Positive' : '✅ Normal'}
      </span>
      <span>${(s.confidence * 100).toFixed(1)}%</span>
      <span style="color:var(--muted);font-size:.8rem">
        ${new Date(s.created_at).toLocaleString()}
      </span>
    </div>`).join('')}
  `;
}

// ── Upload & Predict ──────────────────────────────────────────────────────
const dropZone   = document.getElementById('dropZone');
const fileInput  = document.getElementById('fileInput');
const previewBox = document.getElementById('previewBox');
const previewImg = document.getElementById('previewImg');
const analyseBtn = document.getElementById('analyseBtn');
const loader     = document.getElementById('loader');
const resultBox  = document.getElementById('resultBox');
let   selectedFile = null;

dropZone.addEventListener('click', () => fileInput.click());
dropZone.addEventListener('dragover', e => { e.preventDefault(); dropZone.style.borderColor='#3b82f6' });
dropZone.addEventListener('dragleave', () => dropZone.style.borderColor='');
dropZone.addEventListener('drop', e => { e.preventDefault(); handleFile(e.dataTransfer.files[0]) });
fileInput.addEventListener('change', () => handleFile(fileInput.files[0]));

function handleFile(file) {
  if (!file) return;
  selectedFile = file;
  previewImg.src = URL.createObjectURL(file);
  previewBox.classList.remove('hidden');
  resultBox.classList.add('hidden');
}

analyseBtn.addEventListener('click', async () => {
  if (!selectedFile) return;
  loader.classList.remove('hidden');
  previewBox.classList.add('hidden');
  resultBox.classList.add('hidden');

  const form = new FormData();
  form.append('file', selectedFile);

  try {
    const r = await fetch('/api/predict', { method: 'POST', body: form });
    const d = await r.json();
    if (!r.ok) throw new Error(d.detail);

    // Verdict banner
    const banner = document.getElementById('verdictBanner');
    banner.textContent = d.verdict;
    banner.className = d.has_pneumothorax ? 'verdict-pos' : 'verdict-neg';

    // Images
    const overlayImg  = document.getElementById('overlayImg');
    const heatmapImg  = document.getElementById('heatmapImg');
    const resultImages = document.querySelector('.result-images');

    if (d.has_pneumothorax && d.overlay_b64) {
      overlayImg.src  = 'data:image/png;base64,' + d.overlay_b64;
      heatmapImg.src  = 'data:image/png;base64,' + d.heatmap_b64;
      resultImages.style.display = 'grid';
    } else {
      resultImages.style.display = 'none';
    }

    resultBox.classList.remove('hidden');
    await loadStats();
    await loadHistory();
  } catch(e) {
    alert('Error: ' + e.message);
    previewBox.classList.remove('hidden');
  } finally {
    loader.classList.add('hidden');
  }
});

// ── Init ──────────────────────────────────────────────────────────────────
loadStats();
loadHistory();
// =====================================================
// HELPER: Fetch with Authentication Token
// =====================================================
async function fetchWithAuth(url, options = {}) {
    const token = localStorage.getItem('access_token');
    if (!token) {
        window.location.href = '/login';
        throw new Error('No token');
    }
    options.headers = {
        ...options.headers,
        'Authorization': `Bearer ${token}`
    };
    const response = await fetch(url, options);
    if (response.status === 401) {
        localStorage.removeItem('access_token');
        window.location.href = '/login';
        throw new Error('Unauthorized');
    }
    return response;
}

// =====================================================
// STATS & CHARTS (with retry)
// =====================================================
async function loadStats() {
    const r = await fetchWithAuth('/api/stats');
    const d = await r.json();

    document.getElementById('hero-total').textContent = d.total;
    document.getElementById('hero-pos').textContent = d.positive;
    document.getElementById('hero-neg').textContent = d.negative;
    document.getElementById('d-total').textContent = d.total;
    document.getElementById('d-pos').textContent = d.positive;
    document.getElementById('d-neg').textContent = d.negative;
    document.getElementById('d-conf').textContent = (d.avg_confidence * 100).toFixed(1) + '%';

    // Donut chart
    if (window.donutChart && typeof window.donutChart.destroy === 'function') window.donutChart.destroy();
    const donutCanvas = document.getElementById('donutChart');
    if (donutCanvas) {
        window.donutChart = new Chart(donutCanvas, {
            type: 'doughnut',
            data: { labels: ['Positive', 'Normal'], datasets: [{ data: [d.positive, d.negative], backgroundColor: ['#ef4444','#10b981'], borderWidth: 0 }] },
            options: { responsive: true, maintainAspectRatio: true, plugins: { legend: { labels: { color: '#e2e8f0' } } }, cutout: '65%' }
        });
    }
}

async function loadModelMetrics() {
    try {
        const r = await fetchWithAuth('/api/model_performance');
        const data = await r.json();
        const diceEl = document.getElementById('diceValue');
        if (diceEl) diceEl.textContent = data.dice.toFixed(4);
    } catch(e) { console.error('Metrics error', e); }
}

function initGlobalCharts() {
    // Bar chart
    const barCanvas = document.getElementById('barChart');
    if (barCanvas) {
        // Destroy existing chart if any
        if (window.barChart && typeof window.barChart.destroy === 'function') window.barChart.destroy();
        window.barChart = new Chart(barCanvas, {
            type: 'bar',
            data: { labels: ['USA','UK','Germany','Australia','Pakistan','India','Canada'], datasets: [{ label: 'Cases per 100k', data: [18,15,12,14,8,7,16], backgroundColor: '#14b8a6', borderRadius: 6 }] },
            options: { responsive: true, maintainAspectRatio: true, plugins: { legend: { labels: { color: '#e2e8f0' } } }, scales: { x: { ticks: { color: '#64748b' }, grid: { color: '#1e293b' } }, y: { ticks: { color: '#64748b' }, grid: { color: '#1e293b' } } } }
        });
        console.log('Bar chart initialized');
    } else {
        console.error('barChart canvas not found');
    }

    // Line chart
    const lineCanvas = document.getElementById('lineChart');
    if (lineCanvas) {
        if (window.lineChart && typeof window.lineChart.destroy === 'function') window.lineChart.destroy();
        window.lineChart = new Chart(lineCanvas, {
            type: 'line',
            data: { labels: ['0-10','11-20','21-30','31-40','41-50','51-60','60+'], datasets: [{ label: 'Risk Score', data: [2,15,28,18,12,9,6], borderColor: '#f59e0b', backgroundColor: 'rgba(245,158,11,0.1)', tension: 0.4, fill: true, pointBackgroundColor: '#f59e0b' }] },
            options: { responsive: true, maintainAspectRatio: true, plugins: { legend: { labels: { color: '#e2e8f0' } } }, scales: { x: { ticks: { color: '#64748b' }, grid: { color: '#1e293b' } }, y: { ticks: { color: '#64748b' }, grid: { color: '#1e293b' } } } }
        });
        console.log('Line chart initialized');
    } else {
        console.error('lineChart canvas not found');
    }
}

async function loadHistory() {
    const r = await fetchWithAuth('/api/history');
    const data = await r.json();
    const el = document.getElementById('historyTable');
    if (!data.length) { el.innerHTML = '<div class="history-row"><span>No scans yet.</span></div>'; return; }
    let html = `<div class="history-row header"><span>#</span><span>Filename</span><span>Result</span><span>Confidence</span><span>Date</span></div>`;
    data.forEach(s => {
        html += `<div class="history-row">
            <span>${s.id}</span>
            <span>${escapeHtml(s.filename)}</span>
            <span class="${s.has_ptx ? 'tag-pos' : 'tag-neg'}">${s.has_ptx ? '⚠️ Positive' : '✅ Normal'}</span>
            <span>${(s.confidence * 100).toFixed(1)}%</span>
            <span>${new Date(s.created_at).toLocaleString()}</span>
        </div>`;
    });
    el.innerHTML = html;
}

function escapeHtml(str) { if (!str) return ''; return str.replace(/[&<>]/g, function(m) { if (m === '&') return '&amp;'; if (m === '<') return '&lt;'; if (m === '>') return '&gt;'; return m; }); }

// =====================================================
// UPLOAD & PREDICT
// =====================================================
const dropZone = document.getElementById('dropZone');
const fileInput = document.getElementById('fileInput');
const previewBox = document.getElementById('previewBox');
const previewImg = document.getElementById('previewImg');
const analyseBtn = document.getElementById('analyseBtn');
const loader = document.getElementById('loader');
const resultBox = document.getElementById('resultBox');
let selectedFile = null;

if (dropZone) {
    dropZone.addEventListener('click', () => fileInput.click());
    dropZone.addEventListener('dragover', e => { e.preventDefault(); dropZone.style.borderColor = '#14b8a6'; });
    dropZone.addEventListener('dragleave', () => dropZone.style.borderColor = '');
    dropZone.addEventListener('drop', e => { e.preventDefault(); handleFile(e.dataTransfer.files[0]); });
}
if (fileInput) fileInput.addEventListener('change', () => handleFile(fileInput.files[0]));

function handleFile(file) { if (!file) return; selectedFile = file; previewImg.src = URL.createObjectURL(file); previewBox.classList.remove('hidden'); resultBox.classList.add('hidden'); }

if (analyseBtn) {
    analyseBtn.addEventListener('click', async () => {
        if (!selectedFile) return;
        loader.classList.remove('hidden');
        previewBox.classList.add('hidden');
        resultBox.classList.add('hidden');

        const form = new FormData();
        form.append('file', selectedFile);

        try {
            const r = await fetchWithAuth('/api/predict', { method: 'POST', body: form });
            const d = await r.json();
            if (!r.ok) throw new Error(d.detail);

            const banner = document.getElementById('verdictBanner');
            banner.textContent = d.verdict;
            banner.className = 'verdict-banner ' + (d.has_pneumothorax ? 'verdict-pos' : 'verdict-neg');

            // Severity
            const severityBox = document.getElementById('severityBox');
            if (d.severity && d.has_pneumothorax) {
                severityBox.style.display = 'block';
                document.getElementById('severityPercent').innerHTML = `<strong>${d.severity.level}</strong> (${d.severity.percentage}% of lung field)`;
                const bar = document.getElementById('severityBar');
                bar.style.width = `${Math.min(d.severity.percentage, 100)}%`;
                bar.style.backgroundColor = d.severity.color;
                document.getElementById('severityDesc').innerText = d.severity.description;
            } else { severityBox.style.display = 'none'; }

            // Reliability badge
            const badgeDiv = document.getElementById('reliabilityBadge');
            if (d.reliability && d.has_pneumothorax) {
                badgeDiv.style.display = 'block';
                badgeDiv.style.backgroundColor = d.reliability.color + '20';
                badgeDiv.style.border = `1px solid ${d.reliability.color}`;
                badgeDiv.innerHTML = `<strong>Reliability: ${d.reliability.level}</strong><br>${d.reliability.description}`;
            } else { badgeDiv.style.display = 'none'; }

            // Images (overlay, heatmap, Grad‑CAM)
            if (d.has_pneumothorax && d.overlay_b64) {
                document.getElementById('overlayImg').src = 'data:image/png;base64,' + d.overlay_b64;
                document.getElementById('heatmapImg').src = 'data:image/png;base64,' + d.heatmap_b64;
                if (d.gradcam_b64) {
                    document.getElementById('gradcamImg').src = 'data:image/png;base64,' + d.gradcam_b64;
                    console.log('Grad-CAM image set');
                } else {
                    console.warn('No Grad-CAM image from backend');
                    document.getElementById('gradcamImg').src = '';
                }
                const grid = document.querySelector('.analysis-grid');
                if (grid) grid.style.display = 'grid';
            } else {
                const grid = document.querySelector('.analysis-grid');
                if (grid) grid.style.display = 'none';
            }

            resultBox.classList.remove('hidden');
            await loadStats();
            await loadHistory();
        } catch(e) {
            alert('Error: ' + e.message);
            previewBox.classList.remove('hidden');
        } finally { loader.classList.add('hidden'); }
    });
}

// =====================================================
// INITIALIZATION
// =====================================================
if (window.location.pathname === '/' || window.location.pathname === '/index.html') {
    if (!localStorage.getItem('access_token')) {
        window.location.href = '/login';
    } else {
        // Wait for DOM to be fully loaded
        document.addEventListener('DOMContentLoaded', () => {
            initGlobalCharts();
            loadStats();
            loadHistory();
            loadModelMetrics();
        });
    }
}

// =====================================================
// LOGOUT
// =====================================================
const logoutBtn = document.getElementById('logoutBtn');
if (logoutBtn) logoutBtn.addEventListener('click', () => { localStorage.removeItem('access_token'); window.location.href = '/login'; });
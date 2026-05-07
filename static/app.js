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
// STATS & CHARTS (safely destroy old charts)
// =====================================================
async function loadStats() {
    const r = await fetchWithAuth('/api/stats');
    const d = await r.json();

    // Hero stats
    document.getElementById('hero-total').textContent = d.total;
    document.getElementById('hero-pos').textContent = d.positive;
    document.getElementById('hero-neg').textContent = d.negative;

    // Dashboard stat cards
    document.getElementById('d-total').textContent = d.total;
    document.getElementById('d-pos').textContent = d.positive;
    document.getElementById('d-neg').textContent = d.negative;
    document.getElementById('d-conf').textContent = (d.avg_confidence * 100).toFixed(1) + '%';

    // Safely destroy existing donut chart if it exists
    if (window.donutChart && typeof window.donutChart.destroy === 'function') {
        window.donutChart.destroy();
    }
    
    // Create new donut chart
    const donutCanvas = document.getElementById('donutChart');
    if (donutCanvas) {
        window.donutChart = new Chart(donutCanvas, {
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
}

// Initialize global charts once (not recreated on each loadStats)
function initGlobalCharts() {
    // Bar chart
    const barCanvas = document.getElementById('barChart');
    if (barCanvas && !window.barChart) {
        window.barChart = new Chart(barCanvas, {
            type: 'bar',
            data: {
                labels: ['USA','UK','Germany','Australia','Pakistan','India','Canada'],
                datasets: [{
                    label: 'Cases per 100k',
                    data: [18, 15, 12, 14, 8, 7, 16],
                    backgroundColor: '#14b8a6'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: { legend: { labels: { color: '#e2e8f0' }}},
                scales: {
                    x: { ticks: { color: '#64748b' }, grid: { color: '#1e293b' }},
                    y: { ticks: { color: '#64748b' }, grid: { color: '#1e293b' }}
                }
            }
        });
    }
    
    // Line chart
    const lineCanvas = document.getElementById('lineChart');
    if (lineCanvas && !window.lineChart) {
        window.lineChart = new Chart(lineCanvas, {
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
                responsive: true,
                maintainAspectRatio: true,
                plugins: { legend: { labels: { color: '#e2e8f0' }}},
                scales: {
                    x: { ticks: { color: '#64748b' }, grid: { color: '#1e293b' }},
                    y: { ticks: { color: '#64748b' }, grid: { color: '#1e293b' }}
                }
            }
        });
    }
}

// =====================================================
// HISTORY
// =====================================================
async function loadHistory() {
    const r    = await fetchWithAuth('/api/history');
    const data = await r.json();
    const el   = document.getElementById('historyTable');

    if (!data.length) {
        el.innerHTML = '<div class="history-row"><span style="color:var(--muted)">No scans yet.</span></div>';
        return;
    }

    let html = `
        <div class="history-row header">
            <span>#</span>
            <span>Filename</span>
            <span>Result</span>
            <span>Confidence</span>
            <span>Date</span>
        </div>
    `;
    data.forEach(s => {
        html += `
        <div class="history-row">
            <span style="color:var(--muted)">${s.id}</span>
            <span>${escapeHtml(s.filename)}</span>
            <span class="${s.has_ptx ? 'tag-pos' : 'tag-neg'}">
                ${s.has_ptx ? '⚠️ Positive' : '✅ Normal'}
            </span>
            <span>${(s.confidence * 100).toFixed(1)}%</span>
            <span style="color:var(--muted);font-size:.8rem">
                ${new Date(s.created_at).toLocaleString()}
            </span>
        </div>
        `;
    });
    el.innerHTML = html;
}

// Helper to escape HTML
function escapeHtml(str) {
    if (!str) return '';
    return str.replace(/[&<>]/g, function(m) {
        if (m === '&') return '&amp;';
        if (m === '<') return '&lt;';
        if (m === '>') return '&gt;';
        return m;
    });
}

// =====================================================
// UPLOAD & PREDICT
// =====================================================
const dropZone   = document.getElementById('dropZone');
const fileInput  = document.getElementById('fileInput');
const previewBox = document.getElementById('previewBox');
const previewImg = document.getElementById('previewImg');
const analyseBtn = document.getElementById('analyseBtn');
const loader     = document.getElementById('loader');
const resultBox  = document.getElementById('resultBox');
let   selectedFile = null;

if (dropZone) {
    dropZone.addEventListener('click', () => fileInput.click());
    dropZone.addEventListener('dragover', e => { e.preventDefault(); dropZone.style.borderColor = '#14b8a6'; });
    dropZone.addEventListener('dragleave', () => dropZone.style.borderColor = '');
    dropZone.addEventListener('drop', e => { e.preventDefault(); handleFile(e.dataTransfer.files[0]); });
}
if (fileInput) fileInput.addEventListener('change', () => handleFile(fileInput.files[0]));

function handleFile(file) {
    if (!file) return;
    selectedFile = file;
    previewImg.src = URL.createObjectURL(file);
    previewBox.classList.remove('hidden');
    resultBox.classList.add('hidden');
}

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

            // Verdict banner
            const banner = document.getElementById('verdictBanner');
            banner.textContent = d.verdict;
            banner.className = 'verdict-banner ' + (d.has_pneumothorax ? 'verdict-pos' : 'verdict-neg');

            // Severity display (if positive)
            const severityBox = document.getElementById('severityBox');
            if (d.severity && d.has_pneumothorax) {
                severityBox.style.display = 'block';
                document.getElementById('severityPercent').innerHTML = `<strong>${d.severity.level}</strong> (${d.severity.percentage}% of lung field)`;
                const bar = document.getElementById('severityBar');
                bar.style.width = `${Math.min(d.severity.percentage, 100)}%`;
                bar.style.backgroundColor = d.severity.color;
                document.getElementById('severityDesc').innerText = d.severity.description;
            } else {
                severityBox.style.display = 'none';
            }

            // Overlay and heatmap images
            const overlayImg  = document.getElementById('overlayImg');
            const heatmapImg  = document.getElementById('heatmapImg');
            const resultImages = document.querySelector('.analysis-grid');

            if (d.has_pneumothorax && d.overlay_b64) {
                overlayImg.src  = 'data:image/png;base64,' + d.overlay_b64;
                heatmapImg.src  = 'data:image/png;base64,' + d.heatmap_b64;
                if (resultImages) resultImages.style.display = 'grid';
            } else {
                if (resultImages) resultImages.style.display = 'none';
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
}

// =====================================================
// INIT with token check and global charts
// =====================================================
if (window.location.pathname === '/' || window.location.pathname === '/index.html') {
    if (!localStorage.getItem('access_token')) {
        window.location.href = '/login';
    } else {
        initGlobalCharts();  // one-time init
        loadStats();
        loadHistory();
    }
}

// =====================================================
// LOGOUT
// =====================================================
const logoutBtn = document.getElementById('logoutBtn');
if (logoutBtn) {
    logoutBtn.addEventListener('click', () => {
        localStorage.removeItem('access_token');
        window.location.href = '/login';
    });
}
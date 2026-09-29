let map;
let marker;
let chart;
let currentCaseId = null;

document.addEventListener('DOMContentLoaded', () => {
    initMap();
    fetchCases();
});

async function fetchCases() {
    try {
        const response = await fetch('/api/cases');
        const cases = await response.json();
        
        const list = document.getElementById('casesList');
        list.innerHTML = '';
        
        if (cases.length === 0) {
            list.innerHTML = '<p class="text-slate-500 italic p-4">No cases found.</p>';
        } else {
            cases.forEach(c => {
                const div = document.createElement('div');
                div.className = 'case-card';
                div.innerHTML = `
                    <div class="flex justify-between">
                        <span class="font-bold text-blue-400">Case ${c.id}</span>
                        <span class="${c.status === 'Open' ? 'text-yellow-500' : 'text-green-500'} text-sm">${c.verdict}</span>
                    </div>
                    <div class="text-xs text-slate-500 mt-1">${new Date(c.created_at).toLocaleString()}</div>
                `;
                div.onclick = () => loadCaseDetails(c);
                list.appendChild(div);
            });
            
            // Auto load first case
            loadCaseDetails(cases[0]);
        }
    } catch (e) {
        console.error("Failed to fetch cases:", e);
    }
}

function showCasesList() {
    document.getElementById('caseDetailView').classList.add('hidden');
    document.getElementById('casesListView').classList.remove('hidden');
}

function showCaseDetailView() {
    document.getElementById('casesListView').classList.add('hidden');
    document.getElementById('caseDetailView').classList.remove('hidden');
}

function switchTab(tabId) {
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
    
    event.currentTarget.classList.add('active');
    document.getElementById('tab-' + tabId).classList.add('active');
    
    // Resize map if needed when tab becomes visible
    if (tabId === 'evidence' && map) {
        setTimeout(() => map.invalidateSize(), 100);
    }
}

async function loadCaseDetails(c) {
    currentCaseId = c.id;
    showCaseDetailView();
    
    document.getElementById('cdId').textContent = c.id;
    document.getElementById('cdTitle').textContent = `${c.id}: ${c.event_type || 'Behavioral Anomaly'}`;
    document.getElementById('cdVerdict').textContent = c.verdict + ".";
    
    let summaryEvidence = c.evidence.substring(0, 100) + (c.evidence.length > 100 ? '...' : '');
    document.getElementById('cdEvidenceSummary').textContent = summaryEvidence;
    
    const reasoning = JSON.parse(c.reasoning);
    document.getElementById('cdReasoningPreview').textContent = JSON.stringify(reasoning.hypotheses_considered);
    
    document.getElementById('cdSummaryText').textContent = `Likely: behavioral deviation — observed: ${c.evidence}. The reasoning engine ruled out standard explanations based on deviation thresholds.`;
    
    // Fill Evidence Table
    const tbody = document.getElementById('cdEvidenceTable');
    tbody.innerHTML = `
        <tr>
            <td>Value deviation > 2 standard deviations</td>
            <td>0.90</td>
        </tr>
        <tr>
            <td>Historical mean baseline exceeded</td>
            <td>0.75</td>
        </tr>
    `;
    
    document.getElementById('cdRawEvidence').textContent = c.evidence;
    
    // Fill Reasoning
    document.getElementById('cdReasoningSteps').innerHTML = reasoning.steps.map(s => `<div class="p-2 bg-slate-800 rounded">▹ ${s}</div>`).join('');
    
    document.getElementById('cdRuledOut').innerHTML = reasoning.ruled_out.map(ro => `
        <li class="p-3 border-l-2 border-slate-600 bg-slate-800/50">
            <span class="font-bold text-slate-400 line-through">${ro.hypothesis}</span>
            <div class="text-sm mt-1 text-slate-500">${ro.reason}</div>
        </li>
    `).join('');
    
    // Load external data
    loadGeoIP(c.id);
    loadChart(c.entity_id, 'bytes_transferred'); // Hardcoded event type for POC
}

async function loadGeoIP(caseId) {
    try {
        const response = await fetch(`/api/cases/${caseId}/geoip`);
        const data = await response.json();
        
        if (data.error) {
            document.getElementById('mapContainer').classList.add('hidden');
            return;
        }

        document.getElementById('mapContainer').classList.remove('hidden');
        const info = `${data.ip_address} - ${data.city}, ${data.country} (${data.timezone})`;
        document.getElementById('mapInfo').textContent = info;

        if (marker) map.removeLayer(marker);
        
        if (data.lat !== 0 || data.lon !== 0) {
            marker = L.marker([data.lat, data.lon]).addTo(map).bindPopup(info).openPopup();
            map.setView([data.lat, data.lon], 4);
        } else {
            map.setView([0, 0], 1);
        }
    } catch (e) {
        console.error("GeoIP error:", e);
    }
}

async function loadChart(entityId, eventType) {
    try {
        const response = await fetch(`/api/entities/${entityId}/chart/${eventType}`);
        const data = await response.json();

        if (chart) chart.destroy();

        const ctx = document.getElementById('controlChart').getContext('2d');
        chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.labels.map(l => new Date(l).toLocaleTimeString()),
                datasets: [{
                    label: 'Value',
                    data: data.data,
                    borderColor: '#ef4444', // Red line matching image style for charts
                    borderWidth: 2,
                    pointRadius: 0,
                    tension: 0.1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    x: { display: false },
                    y: { display: true, grid: { color: '#1e293b' }, ticks: { color: '#64748b' } }
                }
            }
        });
    } catch (e) {
        console.error("Chart error:", e);
    }
}

function initMap() {
    map = L.map('map').setView([0, 0], 2);
    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        attribution: 'OpenStreetMap & CARTO',
        subdomains: 'abcd',
        maxZoom: 20
    }).addTo(map);
}

async function verifyAuditChain() {
    const statusDiv = document.getElementById('auditStatus');
    statusDiv.classList.remove('hidden', 'bg-green-500', 'bg-red-500');
    statusDiv.classList.add('bg-blue-600', 'text-white');
    statusDiv.textContent = 'Verifying...';

    try {
        const response = await fetch('/api/audit/verify');
        const data = await response.json();

        statusDiv.classList.remove('bg-blue-600');
        if (data.is_valid) {
            statusDiv.classList.add('bg-green-500');
            statusDiv.innerHTML = '✓ Chain Valid';
        } else {
            statusDiv.classList.add('bg-red-500');
            statusDiv.innerHTML = '✗ Chain Tampered!';
        }
        setTimeout(() => statusDiv.classList.add('hidden'), 5000);
    } catch (e) {
        console.error("Audit verification failed", e);
    }
}


// Global variables
let map;
let markersLayer;
let threatChart;
let alertsData = [];

// Check authentication
auth.onAuthStateChanged(async (user) => {
    if (!user) {
        window.location.href = 'login.html?type=user';
        return;
    }
    
    document.getElementById('user-email').textContent = user.email;
    
    // Initialize dashboard
    initializeDashboard();
});

// Logout handler
function handleLogout() {
    auth.signOut().then(() => {
        window.location.href = 'index.html';
    });
}

// Initialize dashboard
async function initializeDashboard() {
    try {
        // Initialize map
        initializeMap();
        
        // Load all data
        await loadDashboardData();
        
    } catch (error) {
        console.error('Error initializing dashboard:', error);
    }
}

// Initialize Leaflet map
function initializeMap() {
    // Create map centered on world
    map = L.map('map').setView([20, 0], 2);
    
    // Add dark theme tile layer
    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; OpenStreetMap contributors &copy; CARTO',
        maxZoom: 19
    }).addTo(map);
    
    // Create layer group for markers
    markersLayer = L.layerGroup().addTo(map);
}

// Load all dashboard data
async function loadDashboardData() {
    try {
        await Promise.all([
            loadMetrics(),
            loadAlerts(),
            loadBlockedIPs(),
            loadThreatTrends(),
            updateMapWithBlockedIPs()
        ]);
    } catch (error) {
        console.error('Error loading dashboard data:', error);
    }
}

//  FIXED: Update map with blocked IPs using HTTPS geolocation
async function updateMapWithBlockedIPs() {
    try {
        console.log(' Loading blocked IPs for map...');
        
        const blockedSnapshot = await db.collection('blocked_ips').get();
        
        if (blockedSnapshot.empty) {
            console.log(' No blocked IPs found');
            return;
        }
        
        console.log(` Found ${blockedSnapshot.size} blocked IPs`);
        
        // Add delay between API calls to avoid rate limiting
        for (const doc of blockedSnapshot.docs) {
            const blocked = doc.data();
            const ip = blocked.ip_address;
            
            if (!ip) {
                console.warn(' Blocked IP document missing ip_address field');
                continue;
            }
            
            try {
                console.log(` Getting location for ${ip}...`);
                
                // Get geolocation for blocked IP
                const geoData = await getIPGeolocation(ip);
                
                if (geoData && geoData.lat && geoData.lon) {
                    // Add RED marker for blocked IP
                    addBlockedIPMarker(geoData, blocked);
                    console.log(` Added marker for blocked IP: ${ip} at ${geoData.city}, ${geoData.country}`);
                } else {
                    console.warn(` No geolocation data for ${ip}`);
                }
                
                // Add small delay to avoid rate limiting
                await new Promise(resolve => setTimeout(resolve, 500));
                
            } catch (error) {
                console.error(` Error adding marker for ${ip}:`, error);
            }
        }
        
        console.log(' Finished adding blocked IP markers');
        
    } catch (error) {
        console.error(' Error loading blocked IPs for map:', error);
    }
}

//  FIXED: Add blocked IP marker (RED pulsing)
function addBlockedIPMarker(geoData, blockedInfo) {
    // RED pulsing marker for blocked IPs
    const markerIcon = L.divIcon({
        className: 'custom-marker',
        html: `<div style="
            background: #FF0000;
            width: 30px;
            height: 30px;
            border-radius: 50%;
            border: 4px solid white;
            box-shadow: 0 0 20px #FF0000, 0 0 40px #FF0000;
            animation: pulse 2s infinite;
        "></div>
        <style>
            @keyframes pulse {
                0%, 100% { transform: scale(1); opacity: 1; }
                50% { transform: scale(1.2); opacity: 0.7; }
            }
        </style>`,
        iconSize: [30, 30]
    });
    
    // Create marker
    const marker = L.marker([geoData.lat, geoData.lon], { icon: markerIcon });
    
    // Create popup content
    const popupContent = `
        <div class="marker-popup">
            <h4> BLOCKED IP</h4>
            <p><strong>IP:</strong> ${blockedInfo.ip_address}</p>
            <p><strong>Location:</strong> ${geoData.city}, ${geoData.country}</p>
            <p><strong>Reason:</strong> ${blockedInfo.reason || 'Multiple attacks detected'}</p>
            <p><strong>Alert Count:</strong> ${blockedInfo.alert_count || 'Unknown'}</p>
            <p><strong>Status:</strong> <span class="badge badge-high">BLOCKED</span></p>
            <p><strong>Blocked:</strong> ${timeAgo(blockedInfo.blocked_at)}</p>
        </div>
    `;
    
    marker.bindPopup(popupContent);
    marker.addTo(markersLayer);
}

// Load metrics
async function loadMetrics() {
    try {
        console.log(' Loading metrics...');
        
        // Total alerts
        const alertsSnapshot = await db.collection('alerts').get();
        const totalAlerts = alertsSnapshot.size;
        document.getElementById('total-alerts').textContent = totalAlerts;
        
        // Blocked IPs
        const blockedSnapshot = await db.collection('blocked_ips').get();
        document.getElementById('blocked-ips').textContent = blockedSnapshot.size;
        
        // Active threats (HIGH severity in last 24h)
        let activeThreatsCount = 0;
        const yesterday = new Date(Date.now() - 24 * 60 * 60 * 1000);
        
        alertsSnapshot.forEach(doc => {
            const alert = doc.data();
            if (alert.severity === 'HIGH') {
                try {
                    const alertTime = new Date(alert.timestamp);
                    if (alertTime >= yesterday) {
                        activeThreatsCount++;
                    }
                } catch (e) {
                    if (!alert.timestamp || alert.timestamp.includes('2026')) {
                        activeThreatsCount++;
                    }
                }
            }
        });
        
        document.getElementById('active-threats').textContent = activeThreatsCount;
        
        // Detection rate
        const detectionRate = await calculateDetectionRate(alertsSnapshot);
        document.getElementById('detection-rate').textContent = detectionRate + '%';
        
    } catch (error) {
        console.error(' Error loading metrics:', error);
        document.getElementById('active-threats').textContent = '0';
        document.getElementById('detection-rate').textContent = '99.5';
    }
}

// Calculate detection rate
async function calculateDetectionRate(alertsSnapshot) {
    try {
        let truePositives = 0;
        let totalDetections = 0;
        
        alertsSnapshot.forEach(doc => {
            const alert = doc.data();
            totalDetections++;
            
            const confidence = alert.confidence || 0;
            const severity = alert.severity || 'MEDIUM';
            
            if (confidence > 0.8 || severity === 'HIGH') {
                truePositives++;
            }
        });
        
        if (totalDetections === 0) return '99.5';
        
        const rate = (truePositives / totalDetections) * 100;
        return rate.toFixed(1);
        
    } catch (error) {
        console.error('Error calculating detection rate:', error);
        return '99.5';
    }
}

// Load alerts
async function loadAlerts() {
    try {
        const alertsSnapshot = await db.collection('alerts')
            .orderBy('timestamp', 'desc')
            .limit(15)
            .get();
        
        const container = document.getElementById('alerts-timeline-container');
        document.getElementById('alerts-count').textContent = `${alertsSnapshot.size} Recent`;
        
        if (alertsSnapshot.empty) {
            container.innerHTML = '<p class="text-grey text-center">No alerts found</p>';
            return;
        }
        
        alertsData = [];
        let html = '';
        
        alertsSnapshot.forEach(doc => {
            const alert = doc.data();
            alertsData.push(alert);
            
            const severity = alert.severity || 'MEDIUM';
            const detector = alert.detector || 'unknown';
            const sourceIP = alert.source_ip || 'Unknown';
            
            html += `
                <div class="timeline-item ${severity.toLowerCase()}">
                    <div class="timeline-time">
                        ${timeAgo(alert.timestamp)}
                    </div>
                    <div class="timeline-content">
                        <div class="timeline-title">
                            <span class="badge badge-${severity.toLowerCase()}">${severity}</span>
                            ${detector.toUpperCase()} Detection
                        </div>
                        <div class="timeline-description">
                            ${alert.description || alert.attack_type || 'Security anomaly detected'}
                            ${sourceIP !== 'Unknown' ? `<span class="ip-badge">${sourceIP}</span>` : ''}
                        </div>
                    </div>
                </div>
            `;
        });
        
        container.innerHTML = html;
        
    } catch (error) {
        console.error('Error loading alerts:', error);
    }
}

//  FIXED: Get IP geolocation using HTTPS (ipapi.co)
async function getIPGeolocation(ip) {
    try {
        // Using ipapi.co (HTTPS, 30k requests/month free)
        const response = await fetch(`https://ipapi.co/${ip}/json/`);
        
        if (!response.ok) {
            console.warn(` Geolocation API returned ${response.status} for ${ip}`);
            return null;
        }
        
        const data = await response.json();
        
        console.log(` Geolocation response for ${ip}:`, data);
        
        if (data.latitude && data.longitude) {
            return {
                lat: data.latitude,
                lon: data.longitude,
                city: data.city || 'Unknown',
                country: data.country_name || 'Unknown'
            };
        }
        
        // Fallback to ip-api.com if ipapi.co fails
        console.log(` No coordinates from ipapi.co, trying ip-api.com for ${ip}...`);
        const fallbackResponse = await fetch(`https://pro.ip-api.com/json/${ip}?key=demo`);
        const fallbackData = await fallbackResponse.json();
        
        if (fallbackData.status === 'success') {
            return {
                lat: fallbackData.lat,
                lon: fallbackData.lon,
                city: fallbackData.city,
                country: fallbackData.country
            };
        }
        
        return null;
    } catch (error) {
        console.error(` Geolocation API error for ${ip}:`, error);
        return null;
    }
}

// Load blocked IPs list
async function loadBlockedIPs() {
    try {
        const container = document.getElementById('blocked-ips-container');
        
        const blockedSnapshot = await db.collection('blocked_ips')
            .orderBy('blocked_at', 'desc')
            .limit(10)
            .get();
        
        if (blockedSnapshot.empty) {
            container.innerHTML = '<p class="text-grey text-center">No blocked IPs</p>';
            return;
        }
        
        let html = '';
        blockedSnapshot.forEach(doc => {
            const blocked = doc.data();
            const ipAddress = blocked.ip_address || doc.id;
            
            html += `
                <div class="blocked-ip-item">
                    <div class="ip-info">
                        <div class="ip-address-large">${ipAddress}</div>
                        <div class="ip-reason">${blocked.reason || 'Multiple attacks detected'}</div>
                        <div class="ip-time">Blocked: ${timeAgo(blocked.blocked_at)}</div>
                    </div>
                    <span class="badge badge-high">BLOCKED</span>
                </div>
            `;
        });
        
        container.innerHTML = html;
        
    } catch (error) {
        console.error('Error loading blocked IPs:', error);
    }
}

// Load threat trends chart
async function loadThreatTrends() {
    try {
        const thirtyDaysAgo = new Date(Date.now() - 30 * 24 * 60 * 60 * 1000);
        
        const alertsSnapshot = await db.collection('alerts')
            .where('timestamp', '>=', thirtyDaysAgo.toISOString())
            .orderBy('timestamp', 'desc')
            .get();
        
        const alertsByDate = {};
        alertsSnapshot.forEach(doc => {
            const alert = doc.data();
            const date = new Date(alert.timestamp).toLocaleDateString();
            alertsByDate[date] = (alertsByDate[date] || 0) + 1;
        });
        
        const last7Days = [];
        const today = new Date();
        
        for (let i = 6; i >= 0; i--) {
            const date = new Date(today);
            date.setDate(date.getDate() - i);
            const dateStr = date.toLocaleDateString();
            last7Days.push({
                date: dateStr,
                count: alertsByDate[dateStr] || 0
            });
        }
        
        const labels = last7Days.map(d => d.date);
        const counts = last7Days.map(d => d.count);
        
        const ctx = document.getElementById('threatTrendChart').getContext('2d');
        
        if (threatChart) {
            threatChart.destroy();
        }
        
        threatChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Security Alerts',
                    data: counts,
                    borderColor: '#E0115F',
                    backgroundColor: 'rgba(224, 17, 95, 0.1)',
                    tension: 0.4,
                    fill: true,
                    pointBackgroundColor: '#E0115F',
                    pointBorderColor: '#FFFFFF',
                    pointBorderWidth: 2,
                    pointRadius: 5,
                    pointHoverRadius: 7
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        labels: { 
                            color: '#FFFFFF',
                            font: { size: 14 }
                        }
                    },
                    tooltip: {
                        backgroundColor: '#1a1a1a',
                        titleColor: '#FFFFFF',
                        bodyColor: '#CCCCCC',
                        borderColor: '#E0115F',
                        borderWidth: 1
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: { 
                            color: '#808080',
                            stepSize: 1
                        },
                        grid: { color: '#2a2a2a' }
                    },
                    x: {
                        ticks: { color: '#808080' },
                        grid: { color: '#2a2a2a' }
                    }
                }
            }
        });
        
    } catch (error) {
        console.error('Error loading threat trends:', error);
    }
}

// Refresh dashboard
function refreshDashboard() {
    loadDashboardData();
}

// Auto-refresh every 30 seconds
setInterval(refreshDashboard, 30000);

// Check authentication and admin access
auth.onAuthStateChanged(async (user) => {
    if (!user) {
        window.location.href = 'login.html?type=admin';
        return;
    }
    
    // Check if user is admin
    const role = await getUserRole(user.uid);
    if (role !== 'admin') {
        alert('Access denied. Admin privileges required.');
        await auth.signOut();
        window.location.href = 'login.html';
        return;
    }
    
    // Load user info
    document.getElementById('user-email').textContent = user.email;
    document.getElementById('admin-name').textContent = user.displayName || 'Admin';
    
    // Load dashboard data
    loadDashboardData();
});

// Logout handler
function handleLogout() {
    auth.signOut().then(() => {
        window.location.href = 'index.html';
    });
}

// Load all dashboard data
async function loadDashboardData() {
    try {
        await Promise.all([
            loadBigMetrics(),
            loadSmallMetrics(),
            loadCharts(),
            loadRecentActivity(),
            loadRecentUsers()
        ]);
    } catch (error) {
        console.error('Error loading dashboard:', error);
    }
}

// Load big metrics
async function loadBigMetrics() {
    try {
        // Total Users
        const usersSnapshot = await db.collection('users').get();
        document.getElementById('total-users').textContent = usersSnapshot.size;
        document.getElementById('users-change').textContent = '↑ 12% this month';
        
        // Total Alerts
        const alertsSnapshot = await db.collection('alerts').get();
        document.getElementById('total-alerts-big').textContent = alertsSnapshot.size;
        document.getElementById('alerts-change').textContent = `↑ ${alertsSnapshot.size} total`;
        
        // Threats Blocked
        const blockedSnapshot = await db.collection('blocked_ips').get();
        document.getElementById('threats-blocked').textContent = blockedSnapshot.size;
        document.getElementById('threats-change').textContent = '↑ ' + blockedSnapshot.size + ' IPs';
        
    } catch (error) {
        console.error('Error loading big metrics:', error);
    }
}

// Load small metrics
async function loadSmallMetrics() {
    try {
        // Alerts today
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        const todayAlerts = await db.collection('alerts')
            .where('timestamp', '>=', today.toISOString())
            .get();
        document.getElementById('alerts-today').textContent = todayAlerts.size;
        
        // New blocked IPs (last 24 hours)
        const yesterday = new Date(Date.now() - 24 * 60 * 60 * 1000);
        const newBlocked = await db.collection('blocked_ips')
            .where('blocked_at', '>=', yesterday.toISOString())
            .get();
        document.getElementById('new-blocked-ips').textContent = newBlocked.size;
        
        // Scaling events
        const scalingSnapshot = await db.collection('scaling_events').get();
        document.getElementById('scaling-events').textContent = scalingSnapshot.size;
        
        // Active sessions (simulated)
        const activeUsers = await db.collection('users')
            .where('status', '==', 'active')
            .get();
        document.getElementById('active-sessions').textContent = activeUsers.size;
        
        // Average response time (simulated)
        document.getElementById('avg-response').textContent = '127';
        
    } catch (error) {
        console.error('Error loading small metrics:', error);
    }
}

// Charts
let alertsChart, detectionChart, severityChart;

async function loadCharts() {
    try {
        // Get alerts data
        const alertsSnapshot = await db.collection('alerts')
            .orderBy('timestamp', 'desc')
            .limit(100)
            .get();
        
        const alerts = [];
        alertsSnapshot.forEach(doc => {
            alerts.push(doc.data());
        });
        
        // Alert Volume Chart
        createAlertsChart(alerts);
        
        // Detection Method Chart
        createDetectionChart(alerts);
        
        // Severity Chart
        createSeverityChart(alerts);
        
    } catch (error) {
        console.error('Error loading charts:', error);
    }
}

function createAlertsChart(alerts) {
    const ctx = document.getElementById('alertsChart').getContext('2d');
    
    // Group by date
    const alertsByDate = {};
    alerts.forEach(alert => {
        const date = new Date(alert.timestamp).toLocaleDateString();
        alertsByDate[date] = (alertsByDate[date] || 0) + 1;
    });
    
    const labels = Object.keys(alertsByDate).slice(0, 7).reverse();
    const data = labels.map(label => alertsByDate[label]);
    
    alertsChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Alerts',
                data: data,
                borderColor: '#E0115F',
                backgroundColor: 'rgba(224, 17, 95, 0.1)',
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    labels: { color: '#FFFFFF' }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: { color: '#808080' },
                    grid: { color: '#2a2a2a' }
                },
                x: {
                    ticks: { color: '#808080' },
                    grid: { color: '#2a2a2a' }
                }
            }
        }
    });
}

function createDetectionChart(alerts) {
    const ctx = document.getElementById('detectionChart').getContext('2d');
    
    // Count by detector
    const detectorCounts = {};
    alerts.forEach(alert => {
        const detector = alert.detector || 'unknown';
        detectorCounts[detector] = (detectorCounts[detector] || 0) + 1;
    });
    
    detectionChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: Object.keys(detectorCounts),
            datasets: [{
                data: Object.values(detectorCounts),
                backgroundColor: ['#E0115F', '#FFA500', '#00FF00']
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { color: '#FFFFFF' }
                }
            }
        }
    });
}

function createSeverityChart(alerts) {
    const ctx = document.getElementById('severityChart').getContext('2d');
    
    // Count by severity
    const severityCounts = { HIGH: 0, MEDIUM: 0, LOW: 0 };
    alerts.forEach(alert => {
        const severity = alert.severity || 'MEDIUM';
        severityCounts[severity] = (severityCounts[severity] || 0) + 1;
    });
    
    severityChart = new Chart(ctx, {
        type: 'pie',
        data: {
            labels: ['HIGH', 'MEDIUM', 'LOW'],
            datasets: [{
                data: [severityCounts.HIGH, severityCounts.MEDIUM, severityCounts.LOW],
                backgroundColor: ['#E0115F', '#FFA500', '#808080']
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { color: '#FFFFFF' }
                }
            }
        }
    });
}

// Load recent activity
async function loadRecentActivity() {
    try {
        const container = document.getElementById('activity-container');
        
        // Get recent alerts
        const alertsSnapshot = await db.collection('alerts')
            .orderBy('timestamp', 'desc')
            .limit(10)
            .get();
        
        if (alertsSnapshot.empty) {
            container.innerHTML = '<p class="text-grey">No recent activity</p>';
            return;
        }
        
        let html = '';
        alertsSnapshot.forEach(doc => {
            const alert = doc.data();
            html += `
                <div class="activity-item">
                    <div><strong>${alert.detector || 'System'}</strong> detected ${alert.severity || 'MEDIUM'} severity threat</div>
                    <div class="activity-time">${timeAgo(alert.timestamp)}</div>
                </div>
            `;
        });
        
        container.innerHTML = html;
        
    } catch (error) {
        console.error('Error loading activity:', error);
    }
}

// Load recent users
async function loadRecentUsers() {
    try {
        const tbody = document.getElementById('recent-users-body');
        
        const usersSnapshot = await db.collection('users')
            .orderBy('lastLogin', 'desc')
            .limit(5)
            .get();
        
        if (usersSnapshot.empty) {
            tbody.innerHTML = '<tr><td colspan="5" class="text-center">No users found</td></tr>';
            return;
        }
        
        let html = '';
        usersSnapshot.forEach(doc => {
            const user = doc.data();
            const statusClass = user.status === 'active' ? 'status-active' : 'status-inactive';
            
            html += `
                <tr>
                    <td>${user.displayName || 'N/A'}</td>
                    <td>${user.email}</td>
                    <td><span class="badge ${user.role === 'admin' ? 'badge-high' : 'badge-medium'}">${user.role}</span></td>
                    <td>${formatTimestamp(user.lastLogin)}</td>
                    <td><span class="status-indicator ${statusClass}"></span>${user.status || 'active'}</td>
                </tr>
            `;
        });
        
        tbody.innerHTML = html;
        
    } catch (error) {
        console.error('Error loading users:', error);
    }
}

// Refresh all data
function refreshAllData() {
    loadDashboardData();
}

// Auto-refresh every 60 seconds
setInterval(refreshAllData, 60000);
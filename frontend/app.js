const API_URL = 'http://localhost:8000';

document.addEventListener('DOMContentLoaded', () => {
    checkAuth();
    initApp();
});

function checkAuth() {
    const user = JSON.parse(localStorage.getItem('user'));
    if (!user) {
        window.location.href = 'login.html';
        return;
    }
    // Update User Info in Sidebar
    document.querySelector('.user-info h4').innerText = user.full_name;
    document.querySelector('.user-card img').src = `https://ui-avatars.com/api/?name=${user.full_name}&background=6366f1&color=fff`;

    // Logout Logic
    // Create logout button if not exists or handle in sidebar
    const nav = document.querySelector('.nav-links');
    if (!document.getElementById('logout-btn')) {
        const li = document.createElement('li');
        li.innerHTML = `<a href="#" id="logout-btn" style="color:#ef4444;"><i class="fa-solid fa-sign-out-alt"></i> <span>Logout</span></a>`;
        nav.appendChild(li);
        document.getElementById('logout-btn').addEventListener('click', () => {
            localStorage.removeItem('user');
            window.location.href = 'login.html';
        });
    }
}

function initApp() {
    // Fill user balance immediately (simulated for now, can be fetched)
    const user = JSON.parse(localStorage.getItem('user'));
    if (user) {
        document.getElementById('total-vol').innerText = new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' }).format(user.balance || 0);
    }

    // Set default timestamp
    const now = new Date();
    now.setMinutes(now.getMinutes() - now.getTimezoneOffset());
    document.getElementById('timestamp').value = now.toISOString().slice(0, 16);

    // Listeners
    document.getElementById('check-form').addEventListener('submit', handlePayment);
    document.getElementById('close-result').addEventListener('click', () => {
        document.getElementById('result-overlay').classList.add('hidden');
    });

    // File Upload
    const fileInput = document.getElementById('csv-upload');
    if (fileInput) {
        fileInput.addEventListener('change', handleUpload);
    }

    fetchStats();
}

async function handleUpload(e) {
    const file = e.target.files[0];
    if (!file) return;

    const status = document.getElementById('upload-status');
    status.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Uploading & Analyzing...';

    const formData = new FormData();
    formData.append('file', file);

    try {
        const res = await fetch(`${API_URL}/upload`, {
            method: 'POST',
            body: formData
        });
        const data = await res.json();

        if (res.ok) {
            status.innerHTML = `<span style="color: var(--success)"><i class="fa-solid fa-check"></i> Processed ${data.total_processed} Rows. Found ${data.fraud_found} High Risks.</span>`;
            // Optional: Refresh stats or show modal with report
        } else {
            status.innerHTML = `<span style="color: var(--danger)">Error: ${data.detail}</span>`;
        }
    } catch (err) {
        // MOCK UPLOAD
        console.warn("Backend unavailable, using Mock Upload", err);
        setTimeout(() => {
            const mockProcessed = Math.floor(Math.random() * 500) + 50;
            const mockFraud = Math.floor(mockProcessed * 0.05); // 5% fraud rate
            status.innerHTML = `<span style="color: var(--success)"><i class="fa-solid fa-check"></i> [DEMO MODE] Processed ${mockProcessed} Rows. Found ${mockFraud} High Risks.</span>`;
        }, 1500);
    }
}


async function fetchStats() {
    try {
        const res = await fetch(`${API_URL}/stats`);
        if (!res.ok) throw new Error("Backend Error");
        const data = await res.json();

        animateValue("total-txns", 0, data.total_transactions, 1500);
        animateValue("fraud-txns", 0, data.fraud_detected, 1500);
        renderAlerts(data.recent_alerts);
        renderChart(data);

    } catch (err) {
        console.warn("Using Demo Data for Stats", err);
        // DEMO DATA
        const demoStats = {
            total_transactions: 3420,
            fraud_detected: 124,
            recent_alerts: [
                { merchant: "Overseas Gambling Site", amount: 25000, time: new Date().toISOString(), risk: "High" },
                { merchant: "Unusual Electronics Store", amount: 89000, time: new Date(Date.now() - 3600000).toISOString(), risk: "High" },
                { merchant: "Crypto Wallet Transfer", amount: 15400, time: new Date(Date.now() - 7200000).toISOString(), risk: "High" }
            ]
        };

        animateValue("total-txns", 0, demoStats.total_transactions, 1500);
        animateValue("fraud-txns", 0, demoStats.fraud_detected, 1500);
        renderAlerts(demoStats.recent_alerts);
        renderChart(null); // Will use default chart data
    }
}

function renderAlerts(alerts) {
    const list = document.getElementById('alerts-list');
    list.innerHTML = '';

    alerts.forEach(alert => {
        const li = document.createElement('li');
        li.className = 'alert-item';

        const date = new Date(alert.time);
        const timeStr = date.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' });
        const amt = new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' }).format(alert.amount);

        li.innerHTML = `
            <div class="alert-icon-box">
                <i class="fa-solid fa-triangle-exclamation"></i>
            </div>
            <div class="alert-info">
                <h5>${alert.merchant}</h5>
                <span>${timeStr} • ${amt}</span>
            </div>
            <div class="alert-risk">HIGH RISK</div>
        `;
        list.appendChild(li);
    });
}

// Chart Logic (Same as before)
let fraudChartInstance = null;
function renderChart(data) {
    const ctx = document.getElementById('fraudChart').getContext('2d');
    const hours = ['00:00', '04:00', '08:00', '12:00', '16:00', '20:00', 'Now'];
    const safeData = [120, 50, 200, 450, 500, 350, 150];
    const fraudData = [10, 2, 5, 8, 12, 15, 3];

    if (fraudChartInstance) fraudChartInstance.destroy();

    fraudChartInstance = new Chart(ctx, {
        type: 'line',
        data: {
            labels: hours,
            datasets: [
                {
                    label: 'Safe',
                    data: safeData,
                    borderColor: '#10b981',
                    backgroundColor: 'rgba(16, 185, 129, 0.1)',
                    tension: 0.4,
                    fill: true
                },
                {
                    label: 'Fraud',
                    data: fraudData,
                    borderColor: '#ef4444',
                    backgroundColor: 'rgba(239, 68, 68, 0.1)',
                    tension: 0.4,
                    fill: true
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'top', labels: { color: '#94a3b8' } }
            },
            scales: {
                y: {
                    grid: { color: 'rgba(255,255,255,0.05)' },
                    ticks: { color: '#94a3b8' }
                },
                x: {
                    grid: { display: false },
                    ticks: { color: '#94a3b8' }
                }
            }
        }
    });
}

// Handle Payment Simulation
async function handlePayment(e) {
    e.preventDefault();
    const btn = document.querySelector('.btn-scan');
    const originalText = btn.innerHTML;

    // Loading State
    btn.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin"></i> Processing...';
    btn.disabled = true;

    const user = JSON.parse(localStorage.getItem('user'));

    const payload = {
        username: user.username,
        merchant: document.getElementById('merchant').value,
        amount: parseFloat(document.getElementById('amount').value),
        category: document.getElementById('category').value,
        timestamp: document.getElementById('timestamp').value
    };

    try {
        const res = await fetch(`${API_URL}/transaction/pay`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await res.json();

        if (!res.ok) {
            alert(data.detail);
            return;
        }

        // Update Balance
        if (!data.is_fraud) {
            user.balance = data.new_balance;
            localStorage.setItem('user', JSON.stringify(user));
            document.getElementById('total-vol').innerText = new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' }).format(user.balance);
        }

        showResult(data);
    } catch (err) {
        // MOCK TRANSACTION LOGIC
        console.warn("Backend unavailable, using Mock Logic", err);

        const isFraud = payload.amount > 20000 || payload.merchant.toLowerCase().includes('crypto') || payload.merchant.toLowerCase().includes('gambling');
        const riskScore = isFraud ? Math.floor(Math.random() * 30) + 70 : Math.floor(Math.random() * 20);

        const mockResponse = {
            status: isFraud ? "Failed (Fraud)" : "Success",
            is_fraud: isFraud,
            risk_score: riskScore,
            new_balance: isFraud ? user.balance : user.balance - payload.amount
        };

        if (!mockResponse.is_fraud) {
            user.balance = mockResponse.new_balance;
            localStorage.setItem('user', JSON.stringify(user));
            document.getElementById('total-vol').innerText = new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' }).format(user.balance);
        }

        setTimeout(() => showResult(mockResponse), 1000); // Simulate network delay

    } finally {
        btn.innerHTML = originalText;
        btn.disabled = false;
    }
}

function showResult(data) {
    const overlay = document.getElementById('result-overlay');
    const circle = document.querySelector('.progress-ring__circle');
    const statusText = document.getElementById('status-text');
    const statusDesc = document.getElementById('status-desc');

    overlay.classList.remove('hidden');

    // Circle Animation
    const radius = circle.r.baseVal.value;
    const circumference = radius * 2 * Math.PI;

    circle.style.strokeDasharray = `${circumference} ${circumference}`;
    circle.style.strokeDashoffset = circumference;

    const offset = circumference - (data.risk_score / 100) * circumference;
    setTimeout(() => { circle.style.strokeDashoffset = offset; }, 100);

    // UI Update
    let color = '#10b981';
    let text = "Payment Successful";
    let desc = "Transaction validated and processed.";

    if (data.risk_score > 70) {
        color = '#ef4444';
        text = "Transfer Blocked!";
        desc = "High fraud risk detected. Money not deducted.";
    } else if (data.risk_score > 40) {
        color = '#f59e0b';
        text = "Review Advised";
        desc = "Payment processed but flagged for review.";
    }

    circle.style.stroke = color;
    statusText.style.color = color;
    statusText.innerText = text;
    statusDesc.innerText = desc;

    animateValue('score-val', 0, data.risk_score, 1000);
}

function animateValue(id, start, end, duration) {
    const obj = document.getElementById(id);
    let startTimestamp = null;
    const step = (timestamp) => {
        if (!startTimestamp) startTimestamp = timestamp;
        const progress = Math.min((timestamp - startTimestamp) / duration, 1);
        obj.innerHTML = Math.floor(progress * (end - start) + start);
        if (progress < 1) {
            window.requestAnimationFrame(step);
        }
    };
    window.requestAnimationFrame(step);
}

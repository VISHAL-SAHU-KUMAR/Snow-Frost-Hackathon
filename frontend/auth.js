const API_URL = 'http://localhost:8000';

document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.getElementById('login-form');
    const signupForm = document.getElementById('signup-form');

    if (loginForm) {
        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const btn = loginForm.querySelector('button');
            const originalText = btn.innerText;
            btn.innerText = "Verifying...";
            btn.disabled = true;

            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;

            try {
                const res = await fetch(`${API_URL}/auth/login`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ username, password })
                });

                let data;
                try { data = await res.json(); } catch (e) { throw new Error("Backend Offline"); }

                if (res.ok) {
                    localStorage.setItem('user', JSON.stringify(data));
                    window.location.href = 'index.html';
                } else {
                    alert(data.detail || "Login Failed");
                }
            } catch (err) {
                // FALLBACK FOR DEMO / NETLIFY HOSTING
                console.warn("Backend unavailable, using Demo Mode", err);
                const mockUser = {
                    status: "success",
                    username: username || "demo_user",
                    full_name: "Demo User",
                    balance: 50000.0
                };
                localStorage.setItem('user', JSON.stringify(mockUser));
                alert("⚠️ Backend Disconnected. Entering Demo Mode.");
                window.location.href = 'index.html';
            } finally {
                btn.innerText = originalText;
                btn.disabled = false;
            }
        });
    }

    if (signupForm) {
        signupForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const btn = signupForm.querySelector('button');
            const originalText = btn.innerText;
            btn.innerText = "Creating...";
            btn.disabled = true;

            const fullname = document.getElementById('fullname').value;
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;

            try {
                const res = await fetch(`${API_URL}/auth/register`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ full_name: fullname, username, password })
                });

                let data;
                try { data = await res.json(); } catch (e) { throw new Error("Backend Offline"); }

                if (res.ok) {
                    alert("Account Created! Please Login.");
                    window.location.href = 'login.html';
                } else {
                    alert(data.detail || "Signup Failed");
                }
            } catch (err) {
                // FALLBACK FOR DEMO
                console.warn("Backend unavailable, using Demo Mode", err);
                alert("⚠️ Backend Disconnected. Account created in Mock Mode.");
                window.location.href = 'login.html';
            } finally {
                btn.innerText = originalText;
                btn.disabled = false;
            }
        });
    }

    const resetForm = document.getElementById('reset-form');
    if (resetForm) {
        resetForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const btn = resetForm.querySelector('button');
            const originalText = btn.innerText;
            btn.innerText = "Updating...";
            btn.disabled = true;

            const username = document.getElementById('username').value;
            const password = document.getElementById('new-password').value;

            try {
                const res = await fetch(`${API_URL}/auth/reset-password`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ username, password })
                });
                const data = await res.json();

                if (res.ok) {
                    alert("Password Reset Successful! Please Login.");
                    window.location.href = 'login.html';
                } else {
                    alert(data.detail || "Reset Failed (User not found?)");
                }
            } catch (err) {
                alert("Connection Error");
            } finally {
                btn.innerText = originalText;
                btn.disabled = false;
            }
        });
    }
});

# Deploying to Netlify (Demo Mode)

Since this project uses a Python Backend (FastAPI) which is not natively supported by Netlify's standard static hosting, we have implemented a **Smart Demo Mode**.

## How it works
1.  **Frontend (Netlify)**: The HTML/CSS/JS files can be hosted on Netlify.
2.  **Backend (Local/Render)**:
    *   If the frontend cannot connect to `localhost:8000` (which implies it's running on the cloud), it automatically switches to **Demo Mode**.
    *   **Demo Mode** simulates login, transactions, and fraud detection using Javascript logic in the browser.

## Steps to Deploy on Netlify
1.  Go to [Netlify Drop](https://app.netlify.com/drop).
2.  Drag and drop the **`frontend`** folder (from your project) into the upload area.
3.  That's it! Your site is live.

## Features in Demo Mode
- **Login**: Works with any username/password.
- **Dashboard**: Shows sample data and graphs.
- **Fraud Check**: Try entering an amount > 20,000 or Merchant "Crypto" to see a Fraud Alert!
- **File Upload**: Simulates a CSV analysis.

## For Full Production (Backend + Frontend)
If you want the real Python backend online:
1.  Deploy the `backend` folder to **Render.com** (it's free for Python).
2.  Update `frontend/app.js` line 1: `const API_URL = 'YOUR_RENDER_URL';`
3.  Deploy `frontend` to Netlify.

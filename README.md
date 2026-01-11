# SmartWallet Fraud Shield

## Overview
AI-Driven UPI Fraud Detection Engine that detects unusual spending patterns using an Isolation Forest ML model.

## Tech Stack
- **Frontend**: HTML5, CSS3 (Glassmorphism), JavaScript (Vanilla)
- **Backend**: FastAPI (Python)
- **ML**: Scikit-Learn (Isolation Forest)
- **Data**: Synthetic Transaction Data (Faker)

## Setup & Run

### 1. Backend
Navigate to `backend` folder and install dependencies:
```bash
cd backend
pip install -r requirements.txt
```

Generate Data & Train Model (Already done, but to retrain):
```bash
python generate_data.py
python train_model.py
```

Start API Server:
```bash
python -m uvicorn main:app --reload --port 8000
```

### 2. Frontend
You can simply open `frontend/index.html` in your browser, or serve it:
```bash
cd frontend
python -m http.server 5500
```
Then visit `http://localhost:5500`

## Features
- **Dashboard**: Real-time stats of safe vs fraud transactions.
- **Risk Check**: Input transaction details to get AI risk assessment.
- **Alerts**: Recent high-risk transactions.


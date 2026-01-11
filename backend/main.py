from fastapi import FastAPI, HTTPException, Depends, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
import joblib
import pandas as pd
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import load_model
from datetime import datetime
import os
import sqlite3
# from passlib.context import CryptContext # Removing flaky bcrypt
from werkzeug.security import generate_password_hash, check_password_hash
from typing import Optional
import io

# --- App Setup ---
app = FastAPI(title="SmartWallet Fraud Shield")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Database Setup (SQLite) ---
DB_NAME = "smartwallet.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (username TEXT PRIMARY KEY, password TEXT, full_name TEXT, balance REAL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS user_transactions
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, merchant TEXT, 
                  amount REAL, category TEXT, timestamp TEXT, status TEXT, risk_score INTEGER)''')
    conn.commit()
    conn.close()

init_db()

# --- Security/Auth ---
# pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return check_password_hash(hashed_password, plain_password)

def get_password_hash(password):
    return generate_password_hash(password)

class UserRegister(BaseModel):
    username: str
    password: str
    full_name: str

class LoginRequest(BaseModel):
    username: str
    password: str

# --- ML Model Loading ---
model = None
preprocessor = None
threshold = 0.05 

def load_artifacts():
    global model, preprocessor, threshold
    try:
        preprocessor = joblib.load("preprocessor.joblib")
        model = load_model("autoencoder_model.h5")
        if os.path.exists('threshold.txt'):
            with open('threshold.txt', 'r') as f:
                threshold = float(f.read())
        print("ML Artifacts Loaded.")
    except Exception as e:
        print(f"Error loading artifacts: {e}")

load_artifacts()

# --- Endpoints: Auth ---

@app.post("/auth/register")
def register(user: UserRegister):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    try:
        hashed_pw = get_password_hash(user.password)
        c.execute("INSERT INTO users VALUES (?, ?, ?, ?)", 
                  (user.username, hashed_pw, user.full_name, 50000.0))
        conn.commit()
        return {"status": "success", "message": "User registered successfully"}
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Username already exists")
    finally:
        conn.close()

@app.post("/auth/login")
def login(creds: LoginRequest):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT password, full_name, balance FROM users WHERE username=?", (creds.username,))
    row = c.fetchone()
    conn.close()
    
    if not row or not verify_password(creds.password, row[0]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    return {
        "status": "success", 
        "username": creds.username, 
        "full_name": row[1],
        "balance": row[2]
    }

@app.post("/auth/reset-password")
def reset_password(creds: LoginRequest):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # Check if user exists
    c.execute("SELECT username FROM users WHERE username=?", (creds.username,))
    if not c.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="User not found")
        
    # Update Password
    new_hash = get_password_hash(creds.password)
    c.execute("UPDATE users SET password=? WHERE username=?", (new_hash, creds.username))
    conn.commit()
    conn.close()
    
    return {"status": "success", "message": "Password updated successfully"}

# --- Endpoints: Features ---

class TransactionRequest(BaseModel):
    username: str
    merchant: str
    amount: float
    category: str
    timestamp: Optional[str] = None

@app.post("/transaction/pay")
def process_payment(txn: TransactionRequest):
    # 1. Check Balance
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT balance FROM users WHERE username=?", (txn.username,))
    row = c.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="User not found")
    
    current_balance = row[0]
    if current_balance < txn.amount:
        conn.close()
        raise HTTPException(status_code=400, detail="Insufficient Balance")

    # 2. Run Fraud Check (ML Prediction)
    if not model: load_artifacts()
    
    dt = datetime.now()
    if txn.timestamp:
        try:
            dt = datetime.fromisoformat(txn.timestamp.replace('Z', '+00:00'))
        except: pass
        
    input_df = pd.DataFrame([{
        'Merchant': txn.merchant,
        'Category': txn.category,
        'Amount': txn.amount,
        'Hour': dt.hour,
        'DayOfWeek': dt.weekday(),
    }])
    
    try:
        processed_data = preprocessor.transform(input_df)
        recomposed = model.predict(processed_data, verbose=0)
        mse = np.mean(np.power(processed_data - recomposed, 2))
    except:
        mse = 0
    
    ratio = mse / threshold
    risk_score = int(min(99, ratio * 50)) if ratio < 1 else int(min(99, 60 + (ratio-1)*20))
    is_fraud = risk_score > 70
    
    status_text = "Failed (Fraud)" if is_fraud else "Success"
    
    # 3. Update DB
    if not is_fraud:
        new_balance = current_balance - txn.amount
        c.execute("UPDATE users SET balance=? WHERE username=?", (new_balance, txn.username))
    else:
        new_balance = current_balance # No deduction
    
    c.execute("INSERT INTO user_transactions (username, merchant, amount, category, timestamp, status, risk_score) VALUES (?, ?, ?, ?, ?, ?, ?)",
              (txn.username, txn.merchant, txn.amount, txn.category, dt.isoformat(), status_text, risk_score))
    
    conn.commit()
    conn.close()
    
    return {
        "status": status_text,
        "is_fraud": is_fraud,
        "risk_score": risk_score,
        "new_balance": new_balance
    }

@app.post("/upload")
async def upload_transactions(file: UploadFile = File(...)):
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Invalid file format. Please upload CSV.")
    
    try:
        content = await file.read()
        df = pd.read_csv(io.StringIO(content.decode('utf-8')))
        
        # Validation: Check columns
        required = ['Merchant', 'Amount', 'Category']
        if not all(col in df.columns for col in required):
             raise HTTPException(status_code=400, detail=f"Missing columns. Required: {required}")
        
        # In a real app, we would Retrain Model here or update statistics.
        # For this Hackathon demo, we will analyze the file and return a report.
        
        results = []
        fraud_count = 0
        
        if not model: load_artifacts()
        
        # Batch Predict
        for _, row in df.iterrows():
            # Basic preprocessing row by row (not efficient for big data but fine for demo)
            dt = datetime.now() 
            if 'Timestamp' in row:
                try: dt = pd.to_datetime(row['Timestamp'])
                except: pass
                
            input_df = pd.DataFrame([{
                'Merchant': row['Merchant'],
                'Category': row['Category'],
                'Amount': row['Amount'],
                'Hour': dt.hour,
                'DayOfWeek': dt.weekday(),
            }])
            
            try:
                proc = preprocessor.transform(input_df)
                rec = model.predict(proc, verbose=0)
                mse = np.mean(np.power(proc - rec, 2))
                is_anom = mse > threshold
            except: is_anom = False
            
            if is_anom: fraud_count += 1
            results.append({
                "Merchant": row['Merchant'],
                "Amount": row['Amount'],
                "Risk": "High" if is_anom else "Safe"
            })
            
        return {
            "total_processed": len(df),
            "fraud_found": fraud_count,
            "preview": results[:10]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stats")
def get_stats():
    # Return fake stats or DB stats
    return {
        "total_transactions": 2540,
        "fraud_detected": 89,
        "total_volume": 1250000.0,
        "recent_alerts": [
            {"merchant": "Unknown Global Store", "amount": 45000, "time": datetime.now().isoformat(), "risk": "High"},
            {"merchant": "Crypto Exchange Pvt", "amount": 12000, "time": datetime.now().isoformat(), "risk": "High"}
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

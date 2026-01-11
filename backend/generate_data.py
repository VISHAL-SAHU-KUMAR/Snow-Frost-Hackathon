import pandas as pd
import numpy as np
from faker import Faker
import random
from datetime import datetime, timedelta

fake = Faker('en_IN')
Faker.seed(42)

def generate_transactions(num_transactions=1000):
    data = []
    
    # Common highly used merchants
    merchants = ['Swiggy', 'Zomato', 'Uber', 'Ola', 'Amazon', 'Flipkart', 'Paytm', 'Jio', 'Airtel', 'Netflix']
    expenses = ['Food', 'Food', 'Travel', 'Travel', 'Shopping', 'Shopping', 'Utility', 'Utility', 'Utility', 'Subscription']
    
    # Generate normal transactions
    for _ in range(int(num_transactions * 0.95)):
        merchant_idx = random.randint(0, len(merchants)-1)
        merchant = merchants[merchant_idx]
        category = expenses[merchant_idx]
        
        amount = round(random.uniform(50, 2000), 2)
        if category == 'Shopping':
            amount = round(random.uniform(500, 5000), 2)
            
        date = fake.date_time_between(start_date='-90d', end_date='now')
        
        # Normal hours 7 AM to 11 PM
        if date.hour < 7:
            date = date.replace(hour=random.randint(7, 23))
            
        data.append({
            'Transaction ID': fake.uuid4(),
            'Timestamp': date,
            'Merchant': merchant,
            'Category': category,
            'Amount': amount,
            'Status': 'Success',
            'Location': fake.city(),
            'Flag': 0 # Not Fraud
        })

    # Generate anomalies/fraud
    for _ in range(int(num_transactions * 0.05)):
        fraud_type = random.choice(['HighAmount', 'UnknownMerchant', 'OddTime'])
        
        if fraud_type == 'HighAmount':
            merchant = random.choice(merchants)
            amount = round(random.uniform(10000, 50000), 2)
            date = fake.date_time_between(start_date='-90d', end_date='now')
            category = 'Shopping'
            
        elif fraud_type == 'UnknownMerchant':
            merchant = fake.company() + " Pvt Ltd"
            amount = round(random.uniform(100, 5000), 2)
            date = fake.date_time_between(start_date='-90d', end_date='now')
            category = 'Transfer'
            
        elif fraud_type == 'OddTime':
            merchant = random.choice(merchants)
            amount = round(random.uniform(50, 5000), 2)
            # Midnight hours
            date = fake.date_time_between(start_date='-90d', end_date='now').replace(hour=random.randint(1, 4))
            category = 'Unknown'
            
        data.append({
            'Transaction ID': fake.uuid4(),
            'Timestamp': date,
            'Merchant': merchant,
            'Category': category,
            'Amount': amount,
            'Status': 'Success',
            'Location': fake.city(),
            'Flag': 1 # Fraud/Anomaly
        })
        
    df = pd.DataFrame(data)
    # Shuffle
    df = df.sample(frac=1).reset_index(drop=True)
    return df

if __name__ == "__main__":
    print("Generating synthetic data...")
    df = generate_transactions(1000)
    save_path = "../data/transactions.csv"
    df.to_csv(save_path, index=False)
    print(f"Data saved to {save_path}")

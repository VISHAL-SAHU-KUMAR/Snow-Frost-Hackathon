import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler, OneHotEncoder, OrdinalEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
import joblib
import datetime

def train():
    print("Loading data...")
    df = pd.read_csv('../data/transactions.csv')
    
    # Feature Engineering
    df['Timestamp'] = pd.to_datetime(df['Timestamp'])
    df['Hour'] = df['Timestamp'].dt.hour
    df['DayOfWeek'] = df['Timestamp'].dt.dayofweek
    
    # Select features for model
    # We use Merchant, Category, Amount, Hour
    # For constraints, we might limit high cardinality columns like Merchant for OneHot, or use Ordinal.
    # For this demo, let's use OrdinalEncoder for Merchant to keep it simple, or hashing.
    # Given the small set of merchants in generator, we can use OneHot or Ordinal.
    
    features = ['Amount', 'Hour', 'DayOfWeek', 'Category', 'Merchant']
    X = df[features]
    
    # Preprocessing
    # Numeric: Amount, Hour, DayOfWeek
    numeric_features = ['Amount', 'Hour', 'DayOfWeek']
    categorical_features = ['Category', 'Merchant']
    
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', StandardScaler(), numeric_features),
            ('cat', OrdinalEncoder(handle_unknown='use_encoded_value', unknown_value=-1), categorical_features)
        ])
    
    # Model: Isolation Forest
    # Contamination is the proportion of outliers in the data set.
    clf = IsolationForest(contamination=0.05, random_state=42, n_jobs=-1)
    
    pipeline = Pipeline(steps=[('preprocessor', preprocessor),
                               ('classifier', clf)])
    
    print("Training model...")
    pipeline.fit(X)
    
    # Evaluate briefly
    df['pred'] = pipeline.predict(X)
    df['score'] = pipeline.decision_function(X) # lower score = more anomalous
    
    # Isolation Forest: -1 for outliers, 1 for inliers.
    # Our generated data has Flag 1 for fraud.
    # Let's map pred -1 to Fraud (1) and 1 to Normal (0) to check basic alignment (though unsupervised)
    df['pred_mapped'] = df['pred'].apply(lambda x: 1 if x == -1 else 0)
    
    print("Model trained.")
    print("Saving model...")
    joblib.dump(pipeline, 'model.joblib')
    print("Model saved to backend/model.joblib")

if __name__ == "__main__":
    train()

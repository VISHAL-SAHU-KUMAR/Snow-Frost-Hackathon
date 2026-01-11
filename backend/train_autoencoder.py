import pandas as pd
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Model, load_model
from tensorflow.keras.layers import Input, Dense, Dropout, BatchNormalization
from tensorflow.keras.callbacks import EarlyStopping
from sklearn.preprocessing import StandardScaler, OneHotEncoder, MinMaxScaler
from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
import joblib
import os

# Set random seed for reproducibility
np.random.seed(42)
tf.random.set_seed(42)

def build_autoencoder(input_dim):
    # Encoder
    input_layer = Input(shape=(input_dim,))
    
    # Compress 
    encoded = Dense(32, activation='relu')(input_layer)
    encoded = BatchNormalization()(encoded)
    encoded = Dropout(0.2)(encoded)
    
    encoded = Dense(16, activation='relu')(encoded)
    encoded = Dense(8, activation='relu')(encoded) # Bottleneck
    
    # Decoder
    decoded = Dense(16, activation='relu')(encoded)
    decoded = Dense(32, activation='relu')(decoded)
    decoded = BatchNormalization()(decoded)
    
    output_layer = Dense(input_dim, activation='sigmoid')(decoded) # Sigmoid for normalized data [0,1]
    
    autoencoder = Model(inputs=input_layer, outputs=output_layer)
    autoencoder.compile(optimizer='adam', loss='mse')
    return autoencoder

def train_and_save():
    print("Loading data...")
    if not os.path.exists('../data/transactions.csv'):
        print("Data file not found!")
        return

    df = pd.read_csv('../data/transactions.csv')
    
    # Feature Engineering
    df['Timestamp'] = pd.to_datetime(df['Timestamp'])
    df['Hour'] = df['Timestamp'].dt.hour
    df['DayOfWeek'] = df['Timestamp'].dt.dayofweek
    
    # IMPORTANT: Autoencoders for Anomaly Detection should be trained ONLY on NORMAL data.
    # The idea is: The model learns to reconstruct 'Normal' perfectly. 
    # When it sees 'Fraud', it fails to reconstruct it (High Error).
    
    # Filter normal transactions needed for training
    # In our synthetic data, Flag=0 is Normal
    normal_df = df[df['Flag'] == 0]
    
    features = ['Amount', 'Hour', 'DayOfWeek', 'Category', 'Merchant']
    
    # Prepare Data
    X_normal = normal_df[features]
    X_all = df[features] # For final threshold calculation
    
    # Preprocessing
    # Numeric: Scale to 0-1 for Neural Network (MinMaxScaler is good for Autoencoders with Sigmoid output)
    numeric_features = ['Amount', 'Hour', 'DayOfWeek']
    categorical_features = ['Category', 'Merchant']
    
    # We need a robust preprocessing pipeline
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', MinMaxScaler(), numeric_features),
            ('cat', OneHotEncoder(handle_unknown='ignore', sparse_output=False), categorical_features)
        ],
        verbose_feature_names_out=False
    )
    
    print("Preprocessing data...")
    # Fit only on normal data
    X_train_processed = preprocessor.fit_transform(X_normal)
    
    # Split for validation
    X_train, X_val = train_test_split(X_train_processed, test_size=0.2, random_state=42)
    
    input_dim = X_train.shape[1]
    print(f"Input Dimension: {input_dim}")
    
    # Build Model
    autoencoder = build_autoencoder(input_dim)
    autoencoder.summary()
    
    # Train
    print("Training Autoencoder...")
    early_stopping = EarlyStopping(monitor='val_loss', patience=5, restore_best_weights=True)
    
    history = autoencoder.fit(
        X_train, X_train, # Autoencoder maps Input -> Input
        epochs=50,
        batch_size=32,
        shuffle=True,
        validation_data=(X_val, X_val),
        callbacks=[early_stopping],
        verbose=1
    )
    
    # Calculate Threshold for Anomaly
    # We look at the reconstruction error on the training set
    reconstructions = autoencoder.predict(X_train_processed)
    # MSE for each sample
    mse = np.mean(np.power(X_train_processed - reconstructions, 2), axis=1)
    
    # Threshold: Mean + 3 Std Dev (or a percentile like 95th)
    threshold = np.mean(mse) + 3 * np.std(mse) 
    print(f"Anomaly Threshold: {threshold}")
    
    # Save Artifacts
    print("Saving model and preprocessor...")
    autoencoder.save('autoencoder_model.h5')
    joblib.dump(preprocessor, 'preprocessor.joblib')
    
    # Save threshold for API usage
    with open('threshold.txt', 'w') as f:
        f.write(str(threshold))
        
    print("Training Complete. Model saved.")

if __name__ == "__main__":
    train_and_save()

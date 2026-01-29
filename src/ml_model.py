import pandas as pd
import numpy as np
from typing import List, Dict, Tuple
import pickle
from pathlib import Path
from datetime import datetime

# ============================================================================
# Simple Decision Tree
# ============================================================================
class SimpleTree:
    def __init__(self, max_depth=5):
        self.max_depth = max_depth
        self.tree = None
    
    def fit(self, X, y, depth=0):
        """Build a simple tree by finding best splits"""
        if depth >= self.max_depth or len(y) < 10:
            return np.mean(y)
        
        best_score = float('inf')
        best_feature = None
        best_split = None
        
        for feature in range(X.shape[1]):
            split_value = np.median(X[:, feature])
            left_mask = X[:, feature] <= split_value
            right_mask = ~left_mask
            
            if np.sum(left_mask) < 5 or np.sum(right_mask) < 5:
                continue
            
            left_error = np.var(y[left_mask]) * np.sum(left_mask)
            right_error = np.var(y[right_mask]) * np.sum(right_mask)
            score = left_error + right_error
            
            if score < best_score:
                best_score = score
                best_feature = feature
                best_split = split_value
        
        if best_feature is None:
            return np.mean(y)
        
        left_mask = X[:, best_feature] <= best_split
        right_mask = ~left_mask
        
        return {
            'feature': best_feature,
            'split': best_split,
            'left': self.fit(X[left_mask], y[left_mask], depth + 1),
            'right': self.fit(X[right_mask], y[right_mask], depth + 1)
        }
    
    def predict_one(self, x, node):
        """Predict one sample"""
        if not isinstance(node, dict):
            return node
        
        if x[node['feature']] <= node['split']:
            return self.predict_one(x, node['left'])
        else:
            return self.predict_one(x, node['right'])
    
    def predict(self, X):
        """Predict multiple samples"""
        return np.array([self.predict_one(x, self.tree) for x in X])


# ============================================================================
# Simple Random Forest
# ============================================================================
class SimpleForest:
    def __init__(self, n_trees=10, max_depth=5):
        self.n_trees = n_trees
        self.max_depth = max_depth
        self.trees = []
    
    def fit(self, X, y):
        """Train multiple trees on random samples"""
        print(f"Training {self.n_trees} trees...")
        
        for i in range(self.n_trees):
            indices = np.random.choice(len(X), len(X), replace=True)
            X_sample = X[indices]
            y_sample = y[indices]
            
            tree = SimpleTree(max_depth=self.max_depth)
            tree.tree = tree.fit(X_sample, y_sample)
            self.trees.append(tree)
            
            if (i + 1) % 5 == 0:
                print(f"  {i + 1}/{self.n_trees} complete")
        
        print("✓ Training done!")
    
    def predict(self, X):
        """Average predictions from all trees"""
        predictions = np.array([tree.predict(X) for tree in self.trees])
        return np.mean(predictions, axis=0)


# ============================================================================
# Power Prediction Service
# ============================================================================
class PowerPredictionService:
    """Service for managing and using the power prediction model"""
    
    def __init__(self, model_path: str = "data/power_model.pkl"):
        self.model_path = Path(model_path)
        self.model = None
        self.model_stats = None
        
    def train_model(self, csv_path: str) -> Dict:
        """Train a new model from CSV data"""
        print("Loading data...")
        df = pd.read_csv(csv_path)
        
        # Extract time features
        df['DateTime'] = pd.to_datetime(df['Time'], format='%m/%d/%Y %H:%M')
        df['Month'] = df['DateTime'].dt.month
        df['DayOfWeek'] = df['DateTime'].dt.dayofweek
        df['Hour'] = df['DateTime'].dt.hour
        df['Minute'] = df['DateTime'].dt.minute
        
        # Clean power data
        df['Power'] = df['Main_Transformer'].str.replace(',', '').str.replace(' W', '').astype(float) / 1000
        df = df.dropna(subset=['Power'])
        
        print(f"✓ Loaded {len(df)} records")
        
        # Prepare features
        features = ['Month', 'DayOfWeek', 'Hour', 'Minute']
        X = df[features].values
        y = df['Power'].values
        
        # Split into train/test
        split = int(0.8 * len(X))
        indices = np.random.permutation(len(X))
        X_train, y_train = X[indices[:split]], y[indices[:split]]
        X_test, y_test = X[indices[split:]], y[indices[split:]]
        
        # Train model
        self.model = SimpleForest(n_trees=10, max_depth=8)
        self.model.fit(X_train, y_train)
        
        # Evaluate
        y_pred = self.model.predict(X_test)
        mae = np.mean(np.abs(y_pred - y_test))
        rmse = np.sqrt(np.mean((y_pred - y_test) ** 2))
        r2 = 1 - np.sum((y_test - y_pred) ** 2) / np.sum((y_test - np.mean(y_test)) ** 2)
        
        self.model_stats = {
            'mae': float(mae),
            'rmse': float(rmse),
            'r2': float(r2),
            'train_samples': len(X_train),
            'test_samples': len(X_test),
            'power_range': {
                'min': float(df['Power'].min()),
                'max': float(df['Power'].max()),
                'mean': float(df['Power'].mean())
            },
            'trained_at': datetime.now().isoformat()
        }
        
        # Save model
        self.save_model()
        
        return self.model_stats
    
    def save_model(self):
        """Save model to disk"""
        self.model_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.model_path, 'wb') as f:
            pickle.dump({
                'model': self.model,
                'stats': self.model_stats
            }, f)
        print(f"✓ Model saved to {self.model_path}")
    
    def load_model(self):
        """Load model from disk"""
        if not self.model_path.exists():
            raise FileNotFoundError(f"Model not found at {self.model_path}")
        
        with open(self.model_path, 'rb') as f:
            data = pickle.load(f)
            self.model = data['model']
            self.model_stats = data['stats']
        print(f"✓ Model loaded from {self.model_path}")
    
    def predict_single(self, month: int, day_of_week: int, hour: int, minute: int) -> float:
        """Predict power for a single time point"""
        if self.model is None:
            raise ValueError("Model not loaded. Call load_model() first.")
        
        X = np.array([[month, day_of_week, hour, minute]])
        prediction = self.model.predict(X)[0]
        return float(prediction)
    
    def predict_24h(self, month: int, day_of_week: int, interval_minutes: int = 5) -> List[Dict]:
        """Generate 24-hour predictions"""
        if self.model is None:
            raise ValueError("Model not loaded. Call load_model() first.")
        
        predictions = []
        
        for hour in range(24):
            for minute in range(0, 60, interval_minutes):
                pred = self.predict_single(month, day_of_week, hour, minute)
                predictions.append({
                    'hour': hour,
                    'minute': minute,
                    'time': f"{hour:02d}:{minute:02d}",
                    'power_kw': round(pred, 2)
                })
        
        return predictions
    
    def predict_week(self, month: int, start_day: int = 0) -> Dict[str, List[Dict]]:
        """Generate predictions for a full week"""
        if self.model is None:
            raise ValueError("Model not loaded. Call load_model() first.")
        
        day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        week_predictions = {}
        
        for i in range(7):
            day_of_week = (start_day + i) % 7
            day_name = day_names[day_of_week]
            week_predictions[day_name] = self.predict_24h(month, day_of_week, interval_minutes=60)
        
        return week_predictions
    
    def get_stats(self) -> Dict:
        """Get model statistics"""
        if self.model_stats is None:
            raise ValueError("Model stats not available. Train or load model first.")
        return self.model_stats


# Global instance
power_prediction_service = PowerPredictionService()
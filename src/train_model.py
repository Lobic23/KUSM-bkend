from src.ml_model import power_prediction_service
import sys

def main():
    print("="*60)
    print("TRAINING POWER PREDICTION MODEL")
    print("="*60 + "\n")
    
    # Path to your Power.csv file
    csv_path = "src/data/Power.csv"
    
    try:
        # Train the model
        stats = power_prediction_service.train_model(csv_path)
        
        # Display results
        print("\n" + "="*60)
        print("TRAINING COMPLETE")
        print("="*60)
        print(f"MAE:  {stats['mae']:.2f} kW")
        print(f"RMSE: {stats['rmse']:.2f} kW")
        print(f"R²:   {stats['r2']:.4f}")
        print(f"\nTrain samples: {stats['train_samples']}")
        print(f"Test samples:  {stats['test_samples']}")
        print(f"\nPower range: {stats['power_range']['min']:.1f} - {stats['power_range']['max']:.1f} kW")
        print(f"Trained at: {stats['trained_at']}")
        print("="*60 + "\n")
        
        print("✓ Model saved and ready to use!")
        print("  Start your FastAPI server to use predictions")
        
    except FileNotFoundError:
        print(f"Error: Could not find {csv_path}")
        print("Please ensure Power.csv is in the data/ directory")
        sys.exit(1)
    except Exception as e:
        print(f"Error during training: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
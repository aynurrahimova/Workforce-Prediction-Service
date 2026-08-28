import pickle
import joblib

# Load the saved FLAML AutoML object
with open("flaml_artifacts/flaml_best_model.pkl", "rb") as f:
    automl = pickle.load(f)

# Check which estimator won
print("Best estimator:", automl.best_estimator)

# Extract the trained model
best_model = automl.model.estimator

print(type(best_model))

# Save only the trained model
joblib.dump(best_model, "flaml_artifacts/lightgbm_model.pkl")

print("LightGBM model saved.")
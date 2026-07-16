import os
import joblib
from abc import ABC, abstractmethod
from typing import Any, Dict

class AthenaMLModel(ABC):
    def __init__(self, model_name: str):
        self.model_name = model_name
        self.model = None
        self.model_dir = os.path.join(os.getcwd(), "data", "models", model_name)
        os.makedirs(self.model_dir, exist_ok=True)

    @abstractmethod
    def preprocess(self, raw_data: Any) -> Any: pass

    @abstractmethod
    def train(self, training_data: Any, labels: Any) -> Dict[str, Any]: pass

    @abstractmethod
    def predict(self, features: Any) -> Any: pass

    def save_artifact(self, artifact_name: str = "model.joblib") -> str:
        if self.model is None: raise ValueError("Model not trained.")
        target_path = os.path.join(self.model_dir, artifact_name)
        joblib.dump(self.model, target_path)
        return target_path

    def load_artifact(self, artifact_name: str = "model.joblib") -> bool:
        target_path = os.path.join(self.model_dir, artifact_name)
        if not os.path.exists(target_path): return False
        self.model = joblib.load(target_path)
        return True

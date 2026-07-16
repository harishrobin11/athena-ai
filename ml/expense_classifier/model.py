from ml.base_model import AthenaMLModel
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from typing import List, Dict, Any, Union

class ExpenseClassifierModel(AthenaMLModel):
    def __init__(self):
        super().__init__(model_name="expense_classifier")
        self.pipeline = Pipeline([
            ('vectorizer', TfidfVectorizer(ngram_range=(1, 2))),
            ('classifier', LogisticRegression(C=1.0, max_iter=500))
        ])
        self.is_fitted = False

    def preprocess(self, raw_data: List[str]) -> List[str]:
        return [str(text).strip().lower() for text in raw_data]

    def train(self, training_data: List[str], labels: List[str]) -> Dict[str, Any]:
        cleaned_inputs = self.preprocess(training_data)
        self.pipeline.fit(cleaned_inputs, labels)
        self.model = self.pipeline
        self.is_fitted = True
        self.save_artifact()
        return {
            "status": "success", 
            "samples_processed": len(cleaned_inputs), 
            "classes_learned": list(self.pipeline.named_steps['classifier'].classes_)
        }

    def predict(self, features: Union[str, List[str]]) -> List[Dict[str, Any]]:
        if isinstance(features, str): 
            features = [features]
        if not self.is_fitted:
            if not self.load_artifact(): 
                return [{"category": "Unassigned Operations", "confidence": 1.0} for _ in features]
            self.pipeline = self.model
            self.is_fitted = True
        cleaned_features = self.preprocess(features)
        predictions = self.pipeline.predict(cleaned_features)
        probabilities = self.pipeline.predict_proba(cleaned_features)
        return [{"category": str(pred), "confidence": float(prob[prob.argmax()])} for pred, prob in zip(predictions, probabilities)]

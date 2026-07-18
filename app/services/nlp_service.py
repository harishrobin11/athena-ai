import spacy
from textblob import TextBlob
from typing import List, Dict, Any
from app.core.logger import logger
from app.services.agent_framework.supervisor import azure_llm
from langchain_core.messages import SystemMessage, HumanMessage

class NLPService:
    def __init__(self):
        try:
            # Load the lightweight local spaCy model for NER
            self.nlp = spacy.load("en_core_web_sm")
            logger.info("Local spaCy model loaded successfully.")
        except Exception as e:
            self.nlp = None
            logger.warning(f"Failed to load spaCy model. NER will be disabled: {e}")

    def extract_entities(self, text: str) -> List[Dict[str, str]]:
        """
        Runs extremely fast localized Named Entity Recognition (NER)
        without hitting the LLM API.
        """
        if not self.nlp:
            return []
            
        doc = self.nlp(text)
        entities = []
        for ent in doc.ents:
            # We filter for the most relevant enterprise entities
            if ent.label_ in ["PERSON", "ORG", "GPE", "LOC", "PRODUCT"]:
                entities.append({
                    "text": ent.text,
                    "label": ent.label_
                })
        
        # Deduplicate while preserving order
        seen = set()
        unique_entities = []
        for e in entities:
            key = f"{e['text']}_{e['label']}"
            if key not in seen:
                seen.add(key)
                unique_entities.append(e)
                
        return unique_entities

    def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """
        Runs localized Sentiment Analysis.
        Polarity ranges from -1.0 (highly negative) to 1.0 (highly positive).
        Subjectivity ranges from 0.0 (objective) to 1.0 (subjective).
        """
        blob = TextBlob(text)
        sentiment = blob.sentiment
        
        category = "Neutral"
        if sentiment.polarity > 0.2:
            category = "Positive"
        elif sentiment.polarity < -0.2:
            category = "Negative"
            
        return {
            "polarity": round(sentiment.polarity, 3),
            "subjectivity": round(sentiment.subjectivity, 3),
            "category": category
        }

    async def summarize_text(self, text: str, max_length: int = 150) -> str:
        """
        Routes summarization to Azure OpenAI to prevent massive local model bloat
        (e.g., downloading BART/T5 weights), while ensuring high-quality abstractive summarization.
        """
        sys_prompt = SystemMessage(
            content=f"You are an expert summarizer. Summarize the following text in under {max_length} words, capturing the most critical details."
        )
        user_prompt = HumanMessage(content=text)
        
        try:
            response = await azure_llm.ainvoke([sys_prompt, user_prompt])
            return response.content.strip()
        except Exception as e:
            logger.error(f"Summarization failed: {e}")
            return "Summarization currently unavailable."

    def classify_intent(self, text: str) -> str:
        """
        Simple localized intent classification using noun phrases and heuristics.
        Can be upgraded to a fast text classifier (e.g., fastText) if needed.
        """
        text_lower = text.lower()
        if any(w in text_lower for w in ["invoice", "billing", "receipt", "payment"]):
            return "FINANCE"
        if any(w in text_lower for w in ["password", "login", "access", "error"]):
            return "IT_SUPPORT"
        if any(w in text_lower for w in ["hire", "pto", "vacation", "benefits"]):
            return "HR"
            
        return "GENERAL"

nlp_service = NLPService()

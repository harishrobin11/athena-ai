#!/usr/bin/env python3
import sys
import os

# Insert the absolute path of the project root to ensure clean package compilation
abs_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if abs_project_root not in sys.path:
    sys.path.insert(0, abs_project_root)

# Now it is completely safe to run our core imports
from ml.expense_classifier.model import ExpenseClassifierModel

def seed_and_train() -> None:
    print("[Athena ML] Initializing Expense Classifier Model...")
    classifier = ExpenseClassifierModel()

    training_data = [
        "Hilton Hotel NYC Stay", "Uber ride to corporate office", "Delta Air Lines flight JFK to LAX", 
        "Marriott business conference lodging", "Lyft airport transport", "Amtrak train ticket",
        "Amazon Web Services AWS EC2 bill", "Google Cloud Platform BigQuery storage", 
        "GitHub Enterprise seats renewal", "Slack Technologies monthly subscription", 
        "Datadog monitoring production cluster", "OpenAI API usage platform billing",
        "Google Ads PPC marketing campaign", "Meta Ads facebook business manager", 
        "HubSpot CRM enterprise software tier", "LinkedIn Talent Solutions job posting",
        "Mailchimp marketing newsletter campaign", "Conference booth sponsorship event",
        "WeWork monthly shared office lease", "Staples printer paper and pens", 
        "Catering for all-hands quarterly meeting", "FedEx express document shipment",
        "Coffee beans and breakroom supplies", "Hardware store maintenance equipment"
    ]

    labels = [
        "Travel & Lodging", "Travel & Lodging", "Travel & Lodging", 
        "Travel & Lodging", "Travel & Lodging", "Travel & Lodging",
        "Software & SaaS", "Software & SaaS", 
        "Software & SaaS", "Software & SaaS", 
        "Software & SaaS", "Software & SaaS",
        "Marketing & Growth", "Marketing & Growth", 
        "Marketing & Growth", "Marketing & Growth",
        "Marketing & Growth", "Marketing & Growth",
        "Office Operations", "Office Operations", 
        "Office Operations", "Office Operations",
        "Office Operations", "Office Operations"
    ]

    print(f"[Athena ML] Ingesting {len(training_data)} baseline accounting tokens...")
    results = classifier.train(training_data, labels)
    
    print("\n=== Training Execution Report ===")
    print(f"Status:            {results['status'].upper()}")
    print(f"Samples Processed: {results['samples_processed']}")
    print(f"Classes Learned:   {results['classes_learned']}")
    print("=================================\n")

if __name__ == "__main__":
    seed_and_train()

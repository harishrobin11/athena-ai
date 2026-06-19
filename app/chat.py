from .prompts import SYSTEM_PROMPT
from .llm import ask_llm
from .memory import init_db, save_message, load_history


def chat():
    # Initialize database
    init_db()

    print("Athena AI")
    print("Type 'exit' to quit.\n")

    while True:
        user = input("You: ")

        if user.lower() == "exit":
            print("Athena: Goodbye!")
            break

        # Save user message
        save_message("user", user)

        # Load previous messages
        history = load_history()

        # Build conversation context
        conversation = SYSTEM_PROMPT + "\n\nConversation History:\n"

        for role, content in history:
            conversation += f"{role}: {content}\n"

        # Ask Athena
        answer = ask_llm(conversation, user)

        # Save Athena's reply
        save_message("assistant", answer)

        print("\nAthena:")
        print(answer)
        print()
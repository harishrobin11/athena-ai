from app.tools.conversation_search import (
    search_conversations_tool,
)

results = search_conversations_tool(
    "leave",
    user_id=1,
)

print(results)
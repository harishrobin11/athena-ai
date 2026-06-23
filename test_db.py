from app.memory.database import (
    init_db,
    list_conversations,
)

init_db()

for conversation in list_conversations():
    print(conversation)
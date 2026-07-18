import traceback
from datetime import datetime
from app.db.database import get_db, Base, engine
from app.db.models import User, Conversation, Message, Document, Organization, Workspace, UserRole
from app.memory.conversation_vector_store import ConversationVectorStore

def init_db():
    # Automatically create all tables
    Base.metadata.create_all(bind=engine)

def create_user(username: str, email: str, hashed_password: str, department: str = 'General'):
    db = next(get_db())
    try:
        # Create the user
        user = User(username=username, email=email, password_hash=hashed_password)
        db.add(user)
        db.flush() # Flush to get user.id

        # Scaffold default Organization and Workspace
        org = Organization(name=f"{username.capitalize()}'s Org")
        db.add(org)
        db.flush()

        workspace = Workspace(name="Default Workspace", organization_id=org.id)
        db.add(workspace)
        db.flush()

        # Link user to the org via UserRole
        role = "admin" if username.lower() == "admin" else "member"
        user_role = UserRole(user_id=user.id, organization_id=org.id, role=role, department=department)
        db.add(user_role)

        db.commit()
    finally:
        db.close()

def get_user_by_username(username: str):
    db = next(get_db())
    try:
        user = db.query(User).filter(User.username == username).first()
        if user:
            # Get the user's primary role/department (if they have multiple orgs, just pick first for legacy support)
            primary_role = db.query(UserRole).filter(UserRole.user_id == user.id).first()
            department = primary_role.department if primary_role else "GENERAL"
            
            # Match the legacy tuple structure: id, username, email, password_hash, department, created_at
            return (user.id, user.username, user.email, user.password_hash, department, str(user.created_at))
        return None
    finally:
        db.close()

def create_conversation(title, user_id, workspace_id=None):
    db = next(get_db())
    try:
        conv = Conversation(title=title, user_id=user_id, workspace_id=workspace_id)
        db.add(conv)
        db.commit()
        db.refresh(conv)
        return conv.id
    finally:
        db.close()

def list_conversations(user_id, workspace_id=None):
    db = next(get_db())
    try:
        query = db.query(Conversation).filter(Conversation.user_id == user_id)
        if workspace_id:
            query = query.filter(Conversation.workspace_id == workspace_id)
        convs = query.order_by(Conversation.id.desc()).all()
        # Returns id, title, created_at
        return [(c.id, c.title, str(c.created_at)) for c in convs]
    finally:
        db.close()

def search_conversations(query_str, user_id, workspace_id=None):
    db = next(get_db())
    try:
        query = db.query(Conversation).filter(
            Conversation.user_id == user_id, 
            Conversation.title.like(f"%{query_str}%")
        )
        if workspace_id:
            query = query.filter(Conversation.workspace_id == workspace_id)
        convs = query.order_by(Conversation.id.desc()).all()
        return [(c.id, c.title, str(c.created_at)) for c in convs]
    finally:
        db.close()

def delete_conversation(conversation_id, user_id):
    db = next(get_db())
    try:
        conv = db.query(Conversation).filter(Conversation.id == conversation_id, Conversation.user_id == user_id).first()
        if conv:
            db.delete(conv)
            db.commit()
    finally:
        db.close()

def update_conversation_title(conversation_id, title):
    db = next(get_db())
    try:
        conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if conv:
            conv.title = title
            db.commit()
    finally:
        db.close()

def get_conversation_owner(conversation_id):
    db = next(get_db())
    try:
        conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if conv:
            return (conv.user_id,)
        return None
    finally:
        db.close()

def get_conversation_user_id(conversation_id):
    owner = get_conversation_owner(conversation_id)
    return owner[0] if owner else None

def save_message(conversation_id, role, content):
    db = next(get_db())
    try:
        msg = Message(conversation_id=conversation_id, role=role, content=content)
        db.add(msg)
        db.commit()
    finally:
        db.close()

    try:
        print("Saving message to Chroma...")
        user_id = get_conversation_user_id(conversation_id)
        if user_id is not None:
            store = ConversationVectorStore()
            store.add_message(
                message=content,
                user_id=user_id,
                conversation_id=conversation_id,
                role=role,
                timestamp=datetime.utcnow().isoformat(),
            )
    except Exception as e:
        print("===== Conversation Embedding Error =====")
        traceback.print_exc()

def get_messages(conversation_id):
    db = next(get_db())
    try:
        messages = db.query(Message).filter(Message.conversation_id == conversation_id).order_by(Message.id.asc()).all()
        return [(m.role, m.content) for m in messages]
    finally:
        db.close()

def load_history(conversation_id, limit=20):
    db = next(get_db())
    try:
        messages = db.query(Message).filter(Message.conversation_id == conversation_id).order_by(Message.id.asc()).limit(limit).all()
        return [(m.role, m.content) for m in messages]
    finally:
        db.close()

def add_document(user_id, filename, object_key, bucket="athena-documents", workspace_id=None):
    db = next(get_db())
    try:
        doc = Document(
            user_id=user_id, 
            filename=filename, 
            object_key=object_key, 
            bucket=bucket, 
            workspace_id=workspace_id
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)
        return doc.id
    finally:
        db.close()

def list_documents(user_id, workspace_id=None):
    db = next(get_db())
    try:
        query = db.query(Document).filter(Document.user_id == user_id)
        if workspace_id:
            query = query.filter(Document.workspace_id == workspace_id)
        docs = query.order_by(Document.id.desc()).all()
        # Returns id, filename, uploaded_at
        return [(d.id, d.filename, str(d.uploaded_at)) for d in docs]
    finally:
        db.close()

def delete_document_by_user(filename, user_id):
    db = next(get_db())
    try:
        doc = db.query(Document).filter(Document.filename == filename, Document.user_id == user_id).first()
        if doc:
            db.delete(doc)
            db.commit()
            return True
        return False
    finally:
        db.close()

def owns_document(filename, user_id):
    db = next(get_db())
    try:
        doc = db.query(Document).filter(Document.filename == filename, Document.user_id == user_id).first()
        return doc is not None
    finally:
        db.close()

def get_stats(workspace_id: int | None = None):
    db = next(get_db())
    try:
        doc_q = db.query(Document)
        conv_q = db.query(Conversation)
        msg_q = db.query(Message).join(Conversation)
        
        if workspace_id:
            doc_q = doc_q.filter(Document.workspace_id == workspace_id)
            conv_q = conv_q.filter(Conversation.workspace_id == workspace_id)
            msg_q = msg_q.filter(Conversation.workspace_id == workspace_id)
            
        docs = doc_q.count()
        convs = conv_q.count()
        msgs = msg_q.count()
        
        return {
            "documents": docs,
            "conversations": convs,
            "messages": msgs,
        }
    finally:
        db.close()
from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    response: str
    
    
class UploadResponse(BaseModel):
    chunks: int
    filename: str    
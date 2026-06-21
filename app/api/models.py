from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str


class Source(BaseModel):
    filename: str
    page: int


class ChatResponse(BaseModel):
    response: str
    sources: list[Source]


class UploadResponse(BaseModel):
    chunks: int
    filename: str

class DocumentInfo(BaseModel):
    filename: str


class DocumentsResponse(BaseModel):
    documents: list[DocumentInfo]

class DeleteResponse(BaseModel):
    success: bool
    filename: str
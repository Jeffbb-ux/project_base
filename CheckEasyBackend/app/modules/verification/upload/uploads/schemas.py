from pydantic import BaseModel

class UploadPassportResponse(BaseModel):
    message: str
    file_path: str
    verification_status: str

    class Config:
        orm_mode = True
from pydantic import BaseModel, Field, EmailStr


class ResumeExtractRequest(BaseModel):
    text: str = Field(min_length=1, max_length=5000)


class ResumeExtractResponse(BaseModel):
    name: str | None = None
    email: EmailStr | None = None
    phone: str | None = None
    skills: list[str] = []
    education: str | None = None
    experience_years: float | None = Field(default=None, ge=0)
    confidence: float = Field(ge=0.0, le=1.0)
    needs_review: bool
from pydantic import BaseModel, Field


class AuthRequest(BaseModel):
    username: str
    password: str


class AuthResponse(BaseModel):
    id: int
    username: str
    role: str
    token: str


class DreamRequest(BaseModel):
    title: str
    content: str
    dreamDate: str
    moodScore: int = Field(ge=1, le=5)


class DreamResponse(BaseModel):
    id: int
    title: str
    content: str
    dreamDate: str
    moodScore: int
    isPublic: bool
    auditStatus: str
    anonymousName: str | None = None


class AnalysisResponse(BaseModel):
    dreamId: int
    matchedKeywords: str
    ruleBasedResult: str
    aiResult: str
    riskLevel: str


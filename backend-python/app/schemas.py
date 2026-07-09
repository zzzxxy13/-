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
    ownerId: int | None = None
    username: str | None = None
    isPublic: bool
    auditStatus: str
    likes: int = 0
    comments: int = 0
    isLiked: bool = False
    isAnonymous: bool | None = None
    anonymousName: str | None = None


class AnalysisResponse(BaseModel):
    dreamId: int
    matchedKeywords: str
    ruleBasedResult: str
    aiResult: str
    riskLevel: str


class ShareRequest(BaseModel):
    isAnonymous: bool = True


class CommentCreate(BaseModel):
    content: str = Field(min_length=1, max_length=500)


class CommentResponse(BaseModel):
    id: int
    dreamId: int
    username: str
    content: str
    createdAt: str


class LikeResponse(BaseModel):
    likes: int
    isLiked: bool


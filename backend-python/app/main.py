from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .analysis_skill import analyze_dream, detect_risk
from .auth import make_token, parse_token, require_admin
from .database import get_conn, init_db, password_hash
from .schemas import AnalysisResponse, AuthRequest, AuthResponse, DreamRequest, DreamResponse

app = FastAPI(title="梦境馆 Python API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    init_db(seed=True)


def dream_row_to_response(row) -> DreamResponse:
    return DreamResponse(
        id=row["id"],
        title=row["title"],
        content=row["content"],
        dreamDate=row["dream_date"],
        moodScore=row["mood_score"],
        isPublic=bool(row["is_public"]),
        auditStatus=row["audit_status"],
        anonymousName=row["anonymous_name"],
    )


def require_owner_dream(user_id: int, dream_id: int):
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM dream_records WHERE id = ?", (dream_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="梦境不存在")
    if row["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="无权访问该梦境")
    return row


@app.post("/api/auth/register", response_model=AuthResponse)
def register(payload: AuthRequest):
    with get_conn() as conn:
        exists = conn.execute("SELECT id FROM users WHERE username = ?", (payload.username,)).fetchone()
        if exists:
            raise HTTPException(status_code=400, detail="用户名已存在")
        cursor = conn.execute(
            "INSERT INTO users(username, password_hash, role) VALUES (?, ?, 'USER')",
            (payload.username, password_hash(payload.password)),
        )
        user_id = cursor.lastrowid
    return AuthResponse(id=user_id, username=payload.username, role="USER", token=make_token(user_id, "USER"))


@app.post("/api/auth/login", response_model=AuthResponse)
def login(payload: AuthRequest):
    with get_conn() as conn:
        user = conn.execute("SELECT * FROM users WHERE username = ?", (payload.username,)).fetchone()
    if not user or user["password_hash"] != password_hash(payload.password):
        raise HTTPException(status_code=400, detail="用户名或密码错误")
    return AuthResponse(
        id=user["id"],
        username=user["username"],
        role=user["role"],
        token=make_token(user["id"], user["role"]),
    )


@app.post("/api/dreams", response_model=DreamResponse)
def create_dream(payload: DreamRequest, user=Depends(parse_token)):
    with get_conn() as conn:
        cursor = conn.execute(
            """
            INSERT INTO dream_records(user_id, title, content, dream_date, mood_score)
            VALUES (?, ?, ?, ?, ?)
            """,
            (user["id"], payload.title, payload.content, payload.dreamDate, payload.moodScore),
        )
        row = conn.execute("SELECT * FROM dream_records WHERE id = ?", (cursor.lastrowid,)).fetchone()
    return dream_row_to_response(row)


@app.get("/api/dreams", response_model=list[DreamResponse])
def list_my_dreams(user=Depends(parse_token)):
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT * FROM dream_records
            WHERE user_id = ?
            ORDER BY dream_date DESC, created_at DESC
            """,
            (user["id"],),
        ).fetchall()
    return [dream_row_to_response(row) for row in rows]


@app.get("/api/dreams/{dream_id}", response_model=DreamResponse)
def get_dream(dream_id: int, user=Depends(parse_token)):
    return dream_row_to_response(require_owner_dream(user["id"], dream_id))


@app.put("/api/dreams/{dream_id}", response_model=DreamResponse)
def update_dream(dream_id: int, payload: DreamRequest, user=Depends(parse_token)):
    require_owner_dream(user["id"], dream_id)
    with get_conn() as conn:
        conn.execute(
            """
            UPDATE dream_records
            SET title = ?, content = ?, dream_date = ?, mood_score = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (payload.title, payload.content, payload.dreamDate, payload.moodScore, dream_id),
        )
        row = conn.execute("SELECT * FROM dream_records WHERE id = ?", (dream_id,)).fetchone()
    return dream_row_to_response(row)


@app.delete("/api/dreams/{dream_id}")
def delete_dream(dream_id: int, user=Depends(parse_token)):
    require_owner_dream(user["id"], dream_id)
    with get_conn() as conn:
        conn.execute("DELETE FROM dream_records WHERE id = ?", (dream_id,))
    return {"message": "删除成功"}


@app.post("/api/dreams/{dream_id}/analyze", response_model=AnalysisResponse)
def analyze(dream_id: int, user=Depends(parse_token)):
    dream = require_owner_dream(user["id"], dream_id)
    result = analyze_dream(dream_id, dream["content"], dream["mood_score"])
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO dream_analyses(dream_id, matched_keywords, rule_based_result, ai_result, risk_level)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                dream_id,
                result["matchedKeywords"],
                result["ruleBasedResult"],
                result["aiResult"],
                result["riskLevel"],
            ),
        )
    return AnalysisResponse(**result)


@app.get("/api/dreams/{dream_id}/analysis", response_model=AnalysisResponse)
def latest_analysis(dream_id: int, user=Depends(parse_token)):
    require_owner_dream(user["id"], dream_id)
    with get_conn() as conn:
        row = conn.execute(
            """
            SELECT * FROM dream_analyses
            WHERE dream_id = ?
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (dream_id,),
        ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="暂无分析结果")
    return AnalysisResponse(
        dreamId=dream_id,
        matchedKeywords=row["matched_keywords"] or "",
        ruleBasedResult=row["rule_based_result"] or "",
        aiResult=row["ai_result"] or "",
        riskLevel=row["risk_level"],
    )


@app.post("/api/dreams/{dream_id}/share", response_model=DreamResponse)
def share_dream(dream_id: int, user=Depends(parse_token)):
    dream = require_owner_dream(user["id"], dream_id)
    status = "PENDING" if detect_risk(dream["content"]) else "PUBLISHED"
    anonymous_name = f"梦游者{1000 + dream_id}"
    with get_conn() as conn:
        conn.execute(
            """
            UPDATE dream_records
            SET is_public = 1, audit_status = ?, anonymous_name = ?
            WHERE id = ?
            """,
            (status, anonymous_name, dream_id),
        )
        row = conn.execute("SELECT * FROM dream_records WHERE id = ?", (dream_id,)).fetchone()
    return dream_row_to_response(row)


@app.get("/api/community/dreams", response_model=list[DreamResponse])
def community_dreams():
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT * FROM dream_records
            WHERE is_public = 1 AND audit_status = 'PUBLISHED' AND deleted_by_admin = 0
            ORDER BY created_at DESC
            """
        ).fetchall()
    return [dream_row_to_response(row) for row in rows]


@app.get("/api/community/dreams/{dream_id}", response_model=DreamResponse)
def community_detail(dream_id: int):
    with get_conn() as conn:
        row = conn.execute(
            """
            SELECT * FROM dream_records
            WHERE id = ? AND is_public = 1 AND audit_status = 'PUBLISHED' AND deleted_by_admin = 0
            """,
            (dream_id,),
        ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="该梦境未公开")
    return dream_row_to_response(row)


@app.get("/api/admin/community/dreams", response_model=list[DreamResponse])
def admin_dreams(user=Depends(parse_token)):
    require_admin(user)
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM dream_records WHERE is_public = 1 ORDER BY created_at DESC"
        ).fetchall()
    return [dream_row_to_response(row) for row in rows]


@app.put("/api/admin/community/dreams/{dream_id}/hide", response_model=DreamResponse)
def hide_dream(dream_id: int, user=Depends(parse_token)):
    require_admin(user)
    with get_conn() as conn:
        conn.execute("UPDATE dream_records SET audit_status = 'HIDDEN' WHERE id = ?", (dream_id,))
        row = conn.execute("SELECT * FROM dream_records WHERE id = ?", (dream_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="梦境不存在")
    return dream_row_to_response(row)


@app.delete("/api/admin/community/dreams/{dream_id}")
def admin_delete_dream(dream_id: int, user=Depends(parse_token)):
    require_admin(user)
    with get_conn() as conn:
        conn.execute(
            "UPDATE dream_records SET deleted_by_admin = 1, audit_status = 'DELETED' WHERE id = ?",
            (dream_id,),
        )
    return {"message": "管理员已删除"}


from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .analysis_skill import analyze_dream, detect_risk
from .auth import make_token, parse_token, require_admin
from .database import get_conn, init_db, password_hash
from .schemas import (
    AnalysisResponse,
    AuthRequest,
    AuthResponse,
    CommentCreate,
    CommentResponse,
    DreamRequest,
    DreamResponse,
    LikeResponse,
    ShareRequest,
)

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


class LikeRequest(BaseModel):
    isLiked: bool = True


def _row_has(row, field: str, default):
    return row[field] if field in row.keys() else default


def dream_row_to_response(row) -> DreamResponse:
    return DreamResponse(
        id=row["id"],
        title=row["title"],
        content=row["content"],
        dreamDate=row["dream_date"],
        moodScore=row["mood_score"],
        ownerId=row["user_id"],
        isPublic=bool(row["is_public"]),
        username=row["username"] if "username" in row.keys() else None,
        auditStatus=row["audit_status"],
        likes=row["likes"] if "likes" in row.keys() else _row_has(row, "likes_count", 0),
        comments=row["comments"] if "comments" in row.keys() else _row_has(row, "comments_count", 0),
        isAnonymous=bool(_row_has(row, "anonymous_name", False)),
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


def get_current_user_optional(authorization: str | None = Header(default=None)):
    if not authorization:
        return None
    try:
        return parse_token(authorization)
    except HTTPException:
        return None


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
            SELECT dr.*, u.username
              FROM dream_records dr
              JOIN users u ON u.id = dr.user_id
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
def share_dream(dream_id: int, payload: ShareRequest, user=Depends(parse_token)):
    dream = require_owner_dream(user["id"], dream_id)
    status = "PENDING" if detect_risk(dream["content"]) else "PUBLISHED"
    anonymous_name = f"梦游者{1000 + dream_id}" if payload.isAnonymous else None
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
def community_dreams(
    user=Depends(get_current_user_optional),
):
    uid = user["id"] if user else None
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT
              dr.id, dr.user_id, dr.title, dr.content, dr.mood_score, dr.dream_date, dr.is_public, dr.audit_status, dr.anonymous_name, dr.created_at,
              u.username,
              COALESCE(lc.cnt, 0) AS likes,
              COALESCE(cm.cnt, 0) AS comments,
              CASE WHEN ul.id IS NOT NULL THEN 1 ELSE 0 END AS isLiked
            FROM dream_records dr
            LEFT JOIN users u ON u.id = dr.user_id
            LEFT JOIN (
              SELECT dream_id, COUNT(*) AS cnt FROM dream_likes GROUP BY dream_id
            ) lc ON lc.dream_id = dr.id
            LEFT JOIN (
              SELECT dream_id, COUNT(*) AS cnt FROM dream_comments WHERE is_deleted = 0 GROUP BY dream_id
            ) cm ON cm.dream_id = dr.id
            LEFT JOIN dream_likes ul ON ul.dream_id = dr.id AND ul.user_id = ?
            WHERE dr.is_public = 1 AND dr.audit_status = 'PUBLISHED' AND dr.deleted_by_admin = 0
            ORDER BY dr.created_at DESC
            """,
            (uid,),
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
    return DreamResponse(
        id=row["id"],
        title=row["title"],
        content=row["content"],
        dreamDate=row["dream_date"],
        moodScore=row["mood_score"],
        ownerId=row["user_id"],
        isPublic=bool(row["is_public"]),
        username=None,
        auditStatus=row["audit_status"],
        likes=0,
        comments=0,
        isAnonymous=bool(row["anonymous_name"]),
        anonymousName=row["anonymous_name"],
    )


@app.get("/api/community/dreams/{dream_id}/comments", response_model=list[CommentResponse])
def list_comments(dream_id: int):
    with get_conn() as conn:
        dream = conn.execute("SELECT id FROM dream_records WHERE id = ?", (dream_id,)).fetchone()
        if not dream:
            raise HTTPException(status_code=404, detail="该梦境不存在")
        rows = conn.execute(
            """
            SELECT dc.id, dc.dream_id, u.username, dc.content, dc.created_at
            FROM dream_comments dc
            LEFT JOIN users u ON u.id = dc.user_id
            WHERE dc.dream_id = ? AND dc.is_deleted = 0
            ORDER BY dc.created_at DESC
            """,
            (dream_id,),
        ).fetchall()
    return [
        CommentResponse(
            id=row["id"],
            dreamId=row["dream_id"],
            username=row["username"] or "匿名用户",
            content=row["content"],
            createdAt=row["created_at"],
        )
        for row in rows
    ]


@app.post("/api/community/dreams/{dream_id}/comments", response_model=CommentResponse)
def create_comment(dream_id: int, payload: CommentCreate, user=Depends(parse_token)):
    if len(payload.content.strip()) == 0:
        raise HTTPException(status_code=400, detail="评论内容不能为空")
    with get_conn() as conn:
        dream = conn.execute("SELECT is_public, deleted_by_admin FROM dream_records WHERE id = ?", (dream_id,)).fetchone()
        if not dream or not dream["is_public"] or dream["deleted_by_admin"]:
            raise HTTPException(status_code=404, detail="该梦境不可评论")
        cursor = conn.execute(
            "INSERT INTO dream_comments(dream_id, user_id, content) VALUES (?, ?, ?)",
            (dream_id, user["id"], payload.content.strip()),
        )
        row = conn.execute(
            """
            SELECT dc.id, dc.dream_id, u.username, dc.content, dc.created_at
            FROM dream_comments dc
            JOIN users u ON u.id = dc.user_id
            WHERE dc.id = ?
            """,
            (cursor.lastrowid,),
        ).fetchone()
    return CommentResponse(
        id=row["id"],
        dreamId=row["dream_id"],
        username=row["username"] or "匿名用户",
        content=row["content"],
        createdAt=row["created_at"],
    )


@app.delete("/api/admin/comments/{comment_id}")
def admin_delete_comment(comment_id: int, user=Depends(parse_token)):
    require_admin(user)
    with get_conn() as conn:
        row = conn.execute("SELECT id FROM dream_comments WHERE id = ?", (comment_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="评论不存在")
        conn.execute("UPDATE dream_comments SET is_deleted = 1 WHERE id = ?", (comment_id,))
    return {"message": "评论已删除"}


@app.post("/api/community/dreams/{dream_id}/like", response_model=LikeResponse)
def toggle_like(dream_id: int, payload: LikeRequest, user=Depends(parse_token)):
    with get_conn() as conn:
        dream = conn.execute("SELECT id FROM dream_records WHERE id = ?", (dream_id,)).fetchone()
        if not dream:
            raise HTTPException(status_code=404, detail="梦境不存在")
        if payload.isLiked:
            conn.execute(
                "INSERT OR IGNORE INTO dream_likes(dream_id, user_id) VALUES (?, ?)",
                (dream_id, user["id"]),
            )
        else:
            conn.execute(
                "DELETE FROM dream_likes WHERE dream_id = ? AND user_id = ?",
                (dream_id, user["id"]),
            )
        count = conn.execute(
            "SELECT COUNT(*) AS c FROM dream_likes WHERE dream_id = ?", (dream_id,)
        ).fetchone()["c"]
        liked = (
            conn.execute(
                "SELECT id FROM dream_likes WHERE dream_id = ? AND user_id = ?",
                (dream_id, user["id"]),
            ).fetchone()
            is not None
        )
    return LikeResponse(likes=count, isLiked=bool(liked))


@app.delete("/api/community/dreams/{dream_id}")
def hide_from_community(dream_id: int, user=Depends(parse_token)):
    with get_conn() as conn:
        dream = conn.execute("SELECT * FROM dream_records WHERE id = ?", (dream_id,)).fetchone()
        if not dream or dream["user_id"] != user["id"]:
            raise HTTPException(status_code=404, detail="梦境不存在")
        conn.execute(
            "UPDATE dream_records SET is_public = 0, audit_status = 'PRIVATE' WHERE id = ?",
            (dream_id,),
        )
    return {"message": "已取消分享"}


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


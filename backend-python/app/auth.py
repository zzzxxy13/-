from fastapi import Header, HTTPException


def make_token(user_id: int, role: str) -> str:
    return f"user-{user_id}-{role}"


def parse_token(authorization: str | None = Header(default=None)):
    if not authorization or not authorization.startswith("Bearer user-"):
        raise HTTPException(status_code=401, detail="未登录或 token 格式错误")
    token = authorization.replace("Bearer ", "", 1)
    parts = token.split("-")
    if len(parts) != 3:
        raise HTTPException(status_code=401, detail="token 格式错误")
    return {"id": int(parts[1]), "role": parts[2]}


def require_admin(user: dict):
    if user["role"] != "ADMIN":
        raise HTTPException(status_code=403, detail="需要管理员权限")


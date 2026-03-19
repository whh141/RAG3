from fastapi import APIRouter

from app.api.routes import chat, eval, kb, ws_chat

api_router = APIRouter()
api_router.include_router(kb.router, prefix="/api/kb", tags=["kb"])
api_router.include_router(chat.router, prefix="/api/chat", tags=["chat"])
api_router.include_router(eval.router, prefix="/api/eval", tags=["evaluation"])
api_router.include_router(ws_chat.router, tags=["ws-chat"])

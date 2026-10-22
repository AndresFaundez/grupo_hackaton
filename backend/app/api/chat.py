from fastapi import APIRouter, Depends, HTTPException

from app.agent.chat import ChatUnavailable
from app.agent.llm import LLMError
from app.models import ChatRequest, ChatResponse
from app.services import Services, get_services

router = APIRouter(tags=["chat"])


@router.post("/clusterings/{clustering_id}/chat", response_model=ChatResponse)
def chat(clustering_id: str, req: ChatRequest, services: Services = Depends(get_services)) -> ChatResponse:
    record = services.clustering(clustering_id)
    try:
        return services.chat.chat(record, req)
    except ChatUnavailable as e:
        raise HTTPException(503, str(e)) from e
    except LLMError as e:
        raise HTTPException(502, str(e)) from e
    except ValueError as e:
        raise HTTPException(422, str(e)) from e

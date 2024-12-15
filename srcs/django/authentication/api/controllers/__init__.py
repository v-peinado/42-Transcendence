from ninja import Router
from typing import Dict, Any

router = Router()

@router.get("/hello")
def hello_world(request) -> Dict[str, Any]:
    return {"message": "Hello World"}
from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def root():
    html_content = """
    <html>
        <head>
            <title>Discord2VRC</title>
        </head>
        <body>
            <h1>Nothing to see here!</h1>
        </body>
    </html>
    """
    return HTMLResponse(content=html_content, status_code=200)

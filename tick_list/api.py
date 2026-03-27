from fastapi import FastAPI

from tick_list.mcp import mcp

mcp_app = mcp.http_app(path="/")

# CRITICAL: pass lifespan from FastMCP to avoid session manager failures
app = FastAPI(title="Climbing Diary", lifespan=mcp_app.lifespan)
app.mount("/mcp", mcp_app)


@app.get("/health")
async def health():
    return {"status": "ok"}

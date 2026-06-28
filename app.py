from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uuid
import time

app = FastAPI()

EMAIL = "23f3003796@ds.study.iitm.ac.in"

RATE_LIMIT = 14
WINDOW = 10

ALLOWED_ORIGINS = [
    "https://app-djdund.example.com",
    "https://exam.sanand.workers.dev",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

buckets = {}


@app.middleware("http")
async def middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID")
    if not request_id:
        request_id = str(uuid.uuid4())

    request.state.request_id = request_id

    if request.method != "OPTIONS":
        client = request.headers.get("X-Client-Id", "default")

        now = time.time()

        hits = buckets.get(client, [])
        hits = [t for t in hits if now - t < WINDOW]

        if len(hits) >= RATE_LIMIT:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded"},
                headers={"X-Request-ID": request_id},
            )

        hits.append(now)
        buckets[client] = hits

    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id

    return response


@app.get("/")
def root():
    return {"status": "ok"}


@app.get("/ping")
def ping(request: Request):
    return {
        "email": EMAIL,
        "request_id": request.state.request_id,
    }

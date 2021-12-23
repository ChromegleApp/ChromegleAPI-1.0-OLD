from fastapi import FastAPI
from nsfw_detector import predict
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    docs_url='/', redoc_url="/docs", title="Chromegle Internal API", version="1.0.0", openapi_url="/api-docs",
    description="Internal API for the Chromegle Chrome Extension",
)

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

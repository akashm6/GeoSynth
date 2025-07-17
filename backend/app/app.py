from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.routes import router as base_router
from routes.auth import router as auth_router

# fastapi entrypoint file
app = FastAPI()
origins = [
    "http://localhost:3000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*']
)

app.include_router(base_router)
app.include_router(auth_router)
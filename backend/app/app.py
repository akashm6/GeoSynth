from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.routes import router as base_router
from app.routes.auth import router as auth_router

# fastapi entrypoint file
app = FastAPI()
origins = [
    "http://localhost:3000",
    "https://geosynth-five.vercel.app/",
    "https://geosynth-akmohan0303-7865s-projects.vercel.app/",
    "https://geosynth-git-main-akmohan0303-7865s-projects.vercel.app/"
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
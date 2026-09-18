from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.config import ROOT, CORS_ORIGINS
from app.routers.media import router, graph
@asynccontextmanager
async def lifespan(app):
    yield
    await graph.http.aclose()
app = FastAPI(title='Central de Mídias Líder', version='0.2.0', lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=CORS_ORIGINS, allow_methods=['GET','POST'], allow_headers=['*'])
@app.get('/health')
def health():
    return {'status':'ok'}
app.include_router(router)
if (ROOT / 'frontend').is_dir():
    app.mount('/', StaticFiles(directory=ROOT / 'frontend', html=True), name='frontend')

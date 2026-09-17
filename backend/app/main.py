from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.config import ROOT, CORS_ORIGINS
from app.routers.media import router
app = FastAPI(title='Central de Mídias Líder', version='0.1.0')
app.add_middleware(CORSMiddleware, allow_origins=CORS_ORIGINS, allow_methods=['GET'], allow_headers=['*'])
@app.get('/health')
def health():
    return {'status':'ok'}
app.include_router(router)
if (ROOT / 'frontend').is_dir():
    app.mount('/', StaticFiles(directory=ROOT / 'frontend', html=True), name='frontend')

import contextlib, io, os, shutil, uuid
from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, FileResponse
from PIL import Image

from model    import ModelService
from database import init_db, save_scan, get_history, get_stats
from schemas  import PredictionResponse, StatsResponse
from utils    import make_overlay, make_heatmap

PKL_PATH = "pneumothorax_deployment_v1.pkl"
service  = ModelService()

@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    service.load(PKL_PATH)
    yield

app = FastAPI(title="PneumoAI", version="2.0.0", lifespan=lifespan)

app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])

os.makedirs("uploads", exist_ok=True)
app.mount("/static",  StaticFiles(directory="static"),  name="static")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
templates = Jinja2Templates(directory="templates")


def get_service():
    if service.model is None:
        raise HTTPException(503, "Model not loaded.")
    return service


# ── Pages ─────────────────────────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


# ── API ───────────────────────────────────────────────────────────────────
@app.get("/api/health")
def health():
    return {"status": "ok", "model_loaded": service.model is not None}


@app.get("/api/stats", response_model=StatsResponse)
def stats():
    return StatsResponse(**get_stats())


@app.get("/api/history")
def history():
    return get_history(20)


@app.post("/api/predict", response_model=PredictionResponse)
async def predict(
    file: UploadFile = File(...),
    svc:  ModelService = Depends(get_service),
):
    if file.content_type not in ("image/jpeg", "image/png"):
        raise HTTPException(422, "JPEG or PNG only.")

    raw = await file.read()
    try:
        pil_img = Image.open(io.BytesIO(raw))
    except Exception:
        raise HTTPException(400, "Cannot read image.")

    # Save upload
    ext      = os.path.splitext(file.filename)[1] or ".png"
    fname    = f"{uuid.uuid4().hex}{ext}"
    fpath    = os.path.join("uploads", fname)
    with open(fpath, "wb") as f:
        f.write(raw)

    result  = svc.predict(pil_img)
    overlay = heatmap = None
    if result["has_pneumothorax"]:
        overlay = make_overlay(pil_img, result["binary_mask"])
        heatmap = make_heatmap(result["prob_map"])

    verdict = (
        f"⚠️ Pneumothorax Detected — {result['confidence']*100:.1f}% confidence"
        if result["has_pneumothorax"]
        else f"✅ No Pneumothorax — {result['confidence']*100:.1f}% probability"
    )

    save_scan(file.filename, fpath, verdict,
              result["confidence"], result["has_pneumothorax"])

    scan_id = get_history(1)[0]["id"]

    return PredictionResponse(
        has_pneumothorax = result["has_pneumothorax"],
        confidence       = result["confidence"],
        verdict          = verdict,
        overlay_b64      = overlay,
        heatmap_b64      = heatmap,
        scan_id          = scan_id,
    )


@app.get("/api/scan/{scan_id}/image")
def get_scan_image(scan_id: int):
    import sqlite3
    con = sqlite3.connect("pneumoai.db")
    row = con.execute("SELECT filepath FROM scans WHERE id=?",
                      (scan_id,)).fetchone()
    con.close()
    if not row or not os.path.exists(row[0]):
        raise HTTPException(404, "Not found.")
    return FileResponse(row[0])
from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI(title="Rumor Detection API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health():
    return {"ok": True}


@app.post("/api/detection/verdict")
async def detection_verdict(
    title: str = Form(...),
    image: UploadFile = File(...),
):
    image_bytes = await image.read()

    print("\n=== Incoming detection request ===")
    print(f"title: {title}")
    print(f"image filename: {image.filename}")
    print(f"image content_type: {image.content_type}")
    print(f"image size(bytes): {len(image_bytes)}")
    print("=== End request ===\n")

    verdict = "Fake" if len(title.strip()) > 12 else "Real"
    category = "mismatch" if verdict == "Fake" else "consistent"
    confidence = 93 if verdict == "Fake" else 81

    return {
        "verdict": verdict,
        "category": category,
        "confidence": confidence,
        "reasoning": "三路证据显示标题与图片存在明显不一致，综合裁决为疑似谣言。"
        if verdict == "Fake"
        else "文本与图片语义基本一致，当前样本更接近真实信息。",
    }

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from veridict import MAC_Judge

app = FastAPI(title="Rumor Detection API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
async def health():
    return {"ok": True}

@app.post("/api/detection/verdict")
async def detection_verdict(  # 改为 async def
    title: str = Form(...),
    image: UploadFile = File(...),
):
    print("\n=== Incoming detection request ===")
    print(f"title: {title}")
    print(f"image filename: {image.filename}")
    print(f"image content_type: {image.content_type}")
    print("=== End request ===\n")

    verdict = await MAC_Judge(news_caption=title, image=image)  # 等待
    print(verdict)
    return verdict  # 原代码返回 verdict, 是元组，根据需求可调整
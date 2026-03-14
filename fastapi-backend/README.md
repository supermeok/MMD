# FastAPI Backend (Rumor Demo)

## 1) Install

```powershell
cd d:\Users\ASUS\Desktop\MAC-frontend\fastapi-backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## 2) Run

```powershell
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

## 3) Env

`fastapi-backend\.env` is used for local secrets. The tracked template is `fastapi-backend\.env.example`.

```env
DASHSCOPE_API_KEY=your_dashscope_api_key
QWEN_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
QWEN_MODEL=qwen3.5-plus
QWEN_VL_MODEL=qwen3.5-plus
QWEN_TEXT_MODEL=qwen3.5-plus
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

## 4) API

- `POST /api/detection/analyze`
- `POST /api/detection/verdict`
  - `multipart/form-data`
  - fields:
    - `title`: string
    - `image`: file
  - response:
    - `verdict`: final judgement
    - `agents`: outputs from `text_analysis`, `visual_investigate`, `consistency_check`
    - `judge`: judge-stage summary
    - `meta`: total elapsed time and model info

The three evidence agents now run in parallel on the backend via `asyncio.gather(...)`, so total latency is close to the slowest branch instead of the sum of all three branches.

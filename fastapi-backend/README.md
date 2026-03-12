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

## 3) API

- `POST /api/detection/verdict`
  - `multipart/form-data`
  - fields:
    - `title`: string
    - `image`: file

The server prints incoming values in console:
- title
- image filename
- image content type
- image size(bytes)

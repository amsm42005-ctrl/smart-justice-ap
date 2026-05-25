import os
import json
from fastapi import FastAPI, UploadFile, File, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
import google.generativeai as genai
from pydantic import BaseModel, Field
from typing import List, Optional

app = FastAPI(title="منصة العدالة الذكية Pro")

# السماح بالاتصال الشامل بدون أي قيود أمنية تعطل الموبايل
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# مفتاح الجمناي الخاص بك
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "AIzaSyBrbQCnY-vNO_s7MBOTroKXKmUgaj0jLkc")
X_SECURITY_TOKEN = "Ahmed2004"

try:
    genai.configure(api_key=GEMINI_API_KEY)
except Exception as e:
    print(f"Gemini Configuration Error: {e}")

class LegalAnalysis(BaseModel):
    errors: List[str] = Field(description="قائمة بالأخطاء وبطلان الإجراءات")
    evidence: List[str] = Field(description="قائمة بأدلة البراءة المستنتجة")
    loopholes: List[str] = Field(description="قائمة بالثغرات القانونية المقترحة للدفاع")

# 🌍 1. تشغيل واجهة التطبيق فوراً عند فتح الرابط
@app.get("/", response_class=HTMLResponse)
async def get_index():
    try:
        with open("index.html", "r", encoding="utf-8") as f:
            return f.read()
    except:
        return "<h3>خطأ: ملف index.html غير موجود بجانب ملف main.py!</h3>"

# 🖼️ 2. توفير الصورة كأيقونة وخلفية للتطبيق
@app.get("/icon.jpg")
async def get_icon():
    if os.path.exists("icon.jpg"):
        return FileResponse("icon.jpg")
    return HTTPException(status_code=404, detail="Image not found")

# ☕ 3. أمر لمنع السيرفر من النوم (Ping endpoint)
@app.get("/api/ping")
async def ping():
    return {"status": "alive"}

# ⚙️ 4. الفحص المستندي الذكي والمحمي بكلمة سرك
@app.post("/api/analyze")
async def analyze_case(
    files: List[UploadFile] = File(...),
    x_token: Optional[str] = Header(None, alias="X-Token")
):
    if x_token != X_SECURITY_TOKEN:
        raise HTTPException(status_code=401, detail="عذراً، الوصول غير مصرح به!")

    prompt = """
    أنت مستشار قانوني مصري مخضرم وحوت في محاكم الجنايات والجنح ومحكمة النقض.
    أمامك مجموعة من الصور لملف قضية أو محضر ضبط رسمي مصري واحد. المطلوب تحليلها بدقة واستخرج أخطاء بطلان الإجراءات، أدلة البراءة، والثغرات القانونية في قالب JSON باللغة العربية.
    """
    gemini_contents = [prompt]

    try:
        for file in files:
            contents = await file.read()
            gemini_contents.append({"mime_type": "image/jpeg", "data": contents})

        # الاعتماد على الموديل الأسرع والأحدث لمعالجة الصور فوراً
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            generation_config={"response_mime_type": "application/json", "response_schema": LegalAnalysis}
        )
        response = model.generate_content(gemini_contents)
        return json.loads(response.text.strip())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
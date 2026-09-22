FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY app/knowledge ./app/knowledge
COPY web ./web
# 生成示例财务库
RUN python -c "from app.tools import db; print(db.seed(force=True))"

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

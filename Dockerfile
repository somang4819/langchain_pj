# 1단계: 빌드 환경 (경량화를 위해 python:3.11-slim 사용)
FROM python:3.11-slim

# 환경 변수 설정
# .pyc 파일을 생성하지 않도록 설정
ENV PYTHONDONTWRITEBYTECODE 1
# 로그가 버퍼링 없이 즉시 출력되도록 설정 (디버깅 용이)
ENV PYTHONUNBUFFERED 1

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 의존성 설치 (MySQL 연동을 위한 클라이언트 라이브러리 등 필요시)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libmariadb-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --upgrade pip

# 의존성 파일 복사 및 설치
COPY requirements.txt .
RUN pip install --use-deprecated=legacy-resolver -r requirements.txt
RUN playwright install --with-deps chromium

# 소스 코드 복사
COPY . .

# FastAPI 실행 (Uvicorn 사용)
# K8s 연동을 위해 호스트를 0.0.0.0으로 설정
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
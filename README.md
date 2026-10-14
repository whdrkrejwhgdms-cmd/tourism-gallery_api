# 한국관광공사 API 이미지 갤러리

Flask 웹사이트로 키워드 검색 결과를 이미지 카드로 표시하고, 이미지를 누르면 관광지 상세정보를 조회합니다.

## Windows에서 실행

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
$env:TOUR_API_KEY="여기에_새_인증키"
python app.py
```

브라우저에서 `http://127.0.0.1:5000`을 엽니다.

## Render 배포

- GitHub 저장소에 프로젝트 파일과 폴더를 업로드합니다.
- Render에서 **New → Web Service**를 선택하고 저장소를 연결합니다.
- Build Command: `pip install -r requirements.txt`
- Start Command: `gunicorn app:app`
- Instance Type: Free
- Environment에서 Key `TOUR_API_KEY`, Value에 새 인증키를 추가합니다.

인증키를 소스 코드나 GitHub에 직접 넣지 마세요. 갤러리는 `firstimage2`를 우선 사용하고, 없으면 `firstimage`를 사용합니다. API 이용 한도와 정책을 준수하세요.

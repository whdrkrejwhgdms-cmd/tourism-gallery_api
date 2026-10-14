관광정보 갤러리 상세페이지 수정 파일

포함 파일
- app.py
- templates/index.html
- templates/detail.html

적용 방법
1. 프로젝트의 기존 app.py를 백업합니다.
2. 이 폴더의 app.py로 기존 app.py를 교체합니다.
3. templates/index.html과 templates/detail.html도 각각 교체합니다.
4. 기존 templates/base.html, requirements.txt, Render 설정은 그대로 유지합니다.
5. Render 환경변수 TOUR_API_KEY에 유효한 한국관광공사 API 인증키가 설정되어 있는지 확인합니다.
6. GitHub에 변경사항을 올려 Render 재배포 후 검색과 상세페이지를 확인합니다.

변경 내용
- 갤러리 링크에서 제목, 주소, 이미지, 전화번호 등 기본 정보를 상세페이지로 전달합니다.
- 상세 API 호출을 공통정보와 소개정보로 분리합니다.
- API 호출이 실패해도 검색 결과에서 전달받은 기본 정보는 표시합니다.
- 상세 API 오류를 화면에 안내하고 서버 로그에도 기록합니다.

보안
- 인증키를 app.py에 직접 넣지 마세요. Render의 TOUR_API_KEY 환경변수로 관리하세요.

# 한국관광공사 API 이미지 갤러리

Flask 웹사이트로 키워드 검색 결과를 이미지 카드로 표시하고, 이미지를 누르면 관광지 상세정보를 조회합니다. 회원가입, 로그인, 로그아웃 기능을 포함합니다.

## 준비물

- Windows에 설치한 [Git for Windows](https://git-scm.com/download/win)
- Python 3.10 이상
- GitHub 저장소에 코드를 쓸 수 있는 권한
- 한국관광공사 API 인증키

## GitHub 토큰 발급 및 안전하게 인증하기

GitHub 비밀번호 대신 Personal Access Token(PAT)을 사용합니다. 토큰은 비밀번호와 같은 비밀정보입니다.

1. GitHub의 **Settings → Developer settings → Personal access tokens**에서 토큰을 발급합니다.
2. Fine-grained token을 선택한 경우 다음과 같이 설정합니다.
   - **Resource owner:** 저장소 소유자
   - **Repository access:** `tourism-gallery_api`만 선택
   - **Repository permissions → Contents:** `Read and write`
3. Classic token을 사용하는 경우 `repo` 권한이 필요합니다.
4. 토큰을 발급할 때만 복사합니다. 소스코드, README, 명령어, Git 원격 주소에 토큰을 직접 입력하거나 다른 사람과 공유하지 마세요. 이 저장소의 계정 자체에 쓰기 권한이 있어야 하며, 토큰만으로 저장소 권한이 생기지는 않습니다.
5. 앞서 채팅이나 다른 공개된 장소에 붙여넣은 토큰은 **GitHub Settings에서 폐기(revoke)**하고 새 토큰을 발급하세요.

Git for Windows에 포함된 Git Credential Manager를 사용하면 토큰을 Git 원격 주소나 명령 기록에 넣지 않고 HTTPS 인증에 사용할 수 있습니다. 아래 명령은 Windows 자격 증명 관리자에 인증 정보를 안전하게 저장하도록 설정합니다.

```powershell
git config --global credential.helper manager
```

### PAT를 입력하는 위치

PAT를 저장소 파일이나 `.env`에 넣는 것이 아닙니다. 위 설정을 마친 뒤 `git push origin main`을 실행했을 때 인증 창이 나타나면 다음과 같이 입력합니다.

- 브라우저가 열리면 GitHub 계정으로 로그인하고 권한 승인을 완료합니다. PAT를 별도로 입력할 필요가 없습니다.
- 터미널에서 `Username`을 물으면 GitHub 사용자 이름을 입력합니다.
- 이어서 `Password`를 물으면 새 PAT를 붙여넣고 Enter를 누릅니다. 터미널에는 붙여넣은 글자나 별표가 표시되지 않는 것이 정상입니다.
- Git Credential Manager 창이 열리면 해당 창의 GitHub 인증 절차를 따릅니다. PAT 입력란이 표시되는 경우 그곳에 붙여넣습니다.

인증을 성공하면 Git Credential Manager가 Windows 자격 증명 관리자에 보관하므로 이후 푸시에서는 다시 입력하지 않을 수 있습니다. 토큰을 직접 Windows 자격 증명 관리자에 등록할 필요는 없습니다. 잘못된 계정이나 만료된 토큰이 저장되어 인증이 반복해서 실패하면 Windows에서 **자격 증명 관리자 → Windows 자격 증명**을 열고 GitHub 관련 항목만 제거한 다음 `git push origin main`을 다시 실행해 새 PAT로 인증하세요.

> GitHub PAT는 GitHub 저장소에 코드를 업로드하기 위한 자격 증명입니다. 앱의 한국관광공사 `TOUR_API_KEY`와는 서로 다른 키입니다. `TOUR_API_KEY`는 아래 **Windows에서 실행** 및 **Render 배포** 절차에 따라 환경 변수로 설정하며, GitHub PAT를 앱 설정이나 소스 코드에 넣지 마세요.

## 처음 한 번: 저장소 받기

아직 저장소를 내려받지 않았다면 프로젝트를 둘 폴더의 상위 위치에서 실행합니다.

```powershell
git clone https://github.com/whdrkrejwhgdms-cmd/tourism-gallery_api.git
Set-Location tourism-gallery_api
```

이미 이 프로젝트 폴더에서 작업 중이라면 다시 `clone`하지 말고 다음의 **수정사항 GitHub에 올리기** 절차를 사용하세요. 현재 저장소 주소와 브랜치를 확인하려면 다음을 실행합니다.

```powershell
git remote -v
git branch --show-current
```

원격 주소가 `https://github.com/whdrkrejwhgdms-cmd/tourism-gallery_api.git`, 브랜치가 `main`인지 확인합니다.

## 수정사항 GitHub에 올리기

프로젝트 폴더에서 PowerShell을 열고 다음 순서로 실행합니다.

```powershell
# 현재 폴더와 변경사항 확인
git status

# 이번에 올릴 파일만 지정해 스테이징
git add README.md requirements.txt app.py templates

# 변경사항을 커밋으로 저장
git commit -m "Describe your changes"

# 원격 main에 새 변경사항이 있으면 먼저 가져와 재적용
git pull --rebase origin main

# GitHub에 업로드
git push origin main
```

실제로 변경한 파일에 맞춰 `git add` 뒤의 경로를 조정하세요. 모든 변경 파일을 올릴 때는 `git add -A`를 사용할 수 있지만, 올리면 안 되는 파일이 없는지 먼저 `git status`로 확인하세요. 특히 `.env`, 토큰, 비밀번호, 개인 데이터, 로컬 데이터베이스, 가상환경, 임시 ZIP 파일은 올리지 마세요.

`git commit`에서 “nothing to commit”이 나오면 커밋할 새 변경사항이 없는 것입니다. 로컬에 이미 커밋된 변경사항을 업로드하려면 `git pull --rebase origin main` 다음에 `git push origin main`을 실행하면 됩니다.

### GitHub 인증 프롬프트가 표시되면

최초 HTTPS 푸시에서 Git Credential Manager가 브라우저 인증을 열거나 자격 증명을 물어볼 수 있습니다.

- Username을 물으면 GitHub 사용자 이름을 입력합니다.
- Password를 물으면 **GitHub 계정 비밀번호가 아니라 새 PAT**를 붙여넣습니다. 입력 중 문자가 화면에 표시되지 않는 것은 정상입니다.
- 인증 정보 저장 여부를 확인하면 Windows 자격 증명 관리자에 저장하도록 허용합니다. 이후에는 대개 다시 토큰을 입력할 필요가 없습니다.

토큰을 `git push` 명령에 붙이거나 아래처럼 원격 주소에 포함하지 마세요. 이러한 방법은 토큰을 명령 기록이나 `.git/config`에 노출할 수 있습니다.

```text
https://TOKEN@github.com/owner/repository.git
```

### 푸시 결과 확인

푸시한 커밋과 원격 브랜치가 같은지 확인합니다.

```powershell
git status --short --branch
git rev-parse HEAD
git ls-remote origin refs/heads/main
```

마지막 두 명령의 커밋 해시가 같고, 상태에 `ahead`가 표시되지 않으면 로컬 커밋이 GitHub의 `main`에 반영된 것입니다. GitHub 웹사이트의 저장소에서 브랜치가 `main`인지 확인한 뒤 파일이나 최신 커밋을 확인할 수도 있습니다.

### 인증 또는 권한 오류 해결

- **403 / Permission denied:** 현재 인증된 GitHub 계정에 저장소 쓰기 권한이 있는지, 토큰이 올바른 저장소를 대상으로 하며 `Contents: Read and write`(또는 Classic `repo`) 권한을 갖는지 확인합니다. 토큰은 저장소 권한을 우회하지 않습니다.
- **브라우저가 열리지 않거나 잘못된 계정으로 인증:** Windows **자격 증명 관리자 → Windows 자격 증명**에서 GitHub 관련 저장 항목을 삭제한 후 `git push origin main`을 다시 실행하고 올바른 계정으로 인증합니다.
- **원격에 다른 커밋이 있음:** `git pull --rebase origin main`을 실행한 후 푸시합니다. 충돌이 발생하면 충돌 파일을 수정하고 `git add <파일>` 및 `git rebase --continue`를 실행합니다.
- 푸시가 거부되었다고 `--force`를 사용하지 마세요. 다른 사람의 커밋을 덮어쓸 수 있습니다.

## Windows에서 실행

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
$env:TOUR_API_KEY="여기에_새_인증키"
$env:SECRET_KEY="충분히_긴_임의의_비밀값"
python app.py
```

브라우저에서 `http://127.0.0.1:5000`을 엽니다. 관광 API 인증키와 `SECRET_KEY`는 소스코드나 GitHub에 저장하지 마세요.

## Render 배포

- Render에서 **New → Web Service**를 선택하고 GitHub 저장소 `whdrkrejwhgdms-cmd/tourism-gallery_api`를 연결합니다.
- 배포 브랜치를 `main`으로 설정합니다.
- Build Command: `pip install -r requirements.txt`
- Start Command: `gunicorn app:app`
- Environment에 `TOUR_API_KEY`와 `SECRET_KEY`를 안전한 환경 변수로 설정합니다.
- `DATABASE_URL`을 설정하지 않으면 로컬 SQLite 데이터베이스를 사용합니다. 배포 환경에서는 Render PostgreSQL 등 영구 데이터베이스의 연결 문자열을 `DATABASE_URL` 환경 변수로 설정하는 것을 권장합니다.

GitHub에 푸시한 것과 웹사이트 배포가 완료된 것은 별개입니다. Render 대시보드에서 최신 `main` 커밋에 대한 배포가 성공했는지 확인하세요.

## 관광정보 이미지

갤러리는 `firstimage2`를 우선 사용하고, 없으면 `firstimage`를 사용합니다. 한국관광공사 API 이용 한도와 정책을 준수하세요.

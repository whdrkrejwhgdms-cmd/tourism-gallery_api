import os
import requests
from pathlib import Path

from flask import (
    Flask, render_template, request, abort,
    redirect, url_for, flash
)

from flask_login import (
    LoginManager, login_user, logout_user,
    login_required, current_user
)

from extensions import db
from models import User


app = Flask(__name__)

# ==========================================
# 1. 기본 설정
# ==========================================

app.config["SECRET_KEY"] = os.environ.get(
    "SECRET_KEY",
    "local-development-key-change-before-deployment"
)

# 로컬에서는 SQLite, 배포 환경에서는 DATABASE_URL 사용
database_url = os.environ.get("DATABASE_URL", "").strip()

if database_url.startswith("postgres://"):
    database_url = database_url.replace(
        "postgres://", "postgresql://", 1
    )

# app.py가 있는 폴더를 기준으로 데이터베이스 경로 지정
BASE_DIR = Path(__file__).resolve().parent

# instance 폴더 생성
INSTANCE_DIR = BASE_DIR / "instance"
INSTANCE_DIR.mkdir(parents=True, exist_ok=True)

# 데이터베이스 설정
database_url = os.environ.get("DATABASE_URL", "").strip()

if database_url.startswith("postgres://"):
    database_url = database_url.replace(
        "postgres://", "postgresql://", 1
    )

if database_url:
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
else:
    database_file = INSTANCE_DIR / "tourism.db"
    app.config["SQLALCHEMY_DATABASE_URI"] = (
        "sqlite:///" + database_file.as_posix()
    )

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

# Flask-Login 설정
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
login_manager.login_message = "로그인이 필요한 기능입니다."


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


# 데이터베이스 테이블 생성
with app.app_context():
    db.create_all()


# ==========================================
# 2. 관광정보 API 설정
# ==========================================

BASE_URL = "https://apis.data.go.kr/B551011/KorService2"
SERVICE_KEY = os.environ.get("TOUR_API_KEY", "").strip()
PAGE_SIZE = 20

CONTENT_TYPES = {
    "12": "관광지",
    "14": "문화시설",
    "15": "행사·공연·축제",
    "25": "여행코스",
    "28": "레포츠",
    "32": "숙박",
    "38": "쇼핑",
    "39": "음식점"
}


# ==========================================
# 3. 관광정보 API 호출
# ==========================================

def api_get(operation, params=None):
    """한국관광공사 API를 호출합니다."""

    if not SERVICE_KEY:
        raise RuntimeError(
            "API 인증키가 없습니다. TOUR_API_KEY 설정을 확인하세요."
        )

    query = {
        "serviceKey": SERVICE_KEY,
        "MobileOS": "ETC",
        "MobileApp": "TourInfoGallery",
        "_type": "json",
        "numOfRows": PAGE_SIZE,
        "pageNo": 1,
    }

    query.update(params or {})

    response = requests.get(
        f"{BASE_URL}/{operation}",
        params=query,
        timeout=25
    )

    response.raise_for_status()

    try:
        data = response.json()
    except ValueError as exc:
        raise RuntimeError(
            "관광공사 API가 JSON이 아닌 응답을 반환했습니다."
        ) from exc

    api_response = data.get("response", data)
    header = api_response.get("header", {})

    code = str(header.get("resultCode", ""))

    if code and code != "0000":
        raise RuntimeError(
            f"관광공사 API 오류({code}): "
            f"{header.get('resultMsg', '오류')}"
        )

    body = api_response.get("body", {})
    raw = body.get("items", {}).get("item", [])

    if isinstance(raw, dict):
        items = [raw]
    elif isinstance(raw, list):
        items = raw
    else:
        items = []

    return items, int(body.get("totalCount") or 0)


def image_url(item):
    image = (
        item.get("firstimage2")
        or item.get("firstimage")
        or ""
    ).strip()

    if image.startswith(("https://", "http://")):
        return image

    return ""


def search_places(keyword, page, content_type):
    params = {
        "keyword": keyword,
        "numOfRows": PAGE_SIZE,
        "pageNo": page
    }

    if content_type:
        params["contentTypeId"] = content_type

    items, total_count = api_get("searchKeyword2", params)

    places = []

    for item in items:
        img = image_url(item)

        if img:
            item["gallery_image"] = img
            item["content_type_name"] = CONTENT_TYPES.get(
                str(item.get("contenttypeid", "")),
                "기타"
            )
            places.append(item)

    total_pages = max(
        1,
        (total_count + PAGE_SIZE - 1) // PAGE_SIZE
    )

    return places, total_count, total_pages


def get_detail_part(
    operation, content_id, content_type_id, params=None
):
    """상세 API 한 종류를 호출합니다."""

    request_params = {
        "contentId": content_id,
        "contentTypeId": content_type_id,
        "numOfRows": 1,
        "pageNo": 1
    }

    request_params.update(params or {})

    items, _ = api_get(operation, request_params)

    return items[0] if items else {}


# ==========================================
# 4. 회원가입
# ==========================================

@app.route("/register", methods=["GET", "POST"])
def register():

    if current_user.is_authenticated:
        return redirect(url_for("account"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        password_confirm = request.form.get(
            "password_confirm", ""
        )

        if not email or "@" not in email:
            flash("올바른 이메일 주소를 입력하세요.", "error")

        elif len(password) < 8:
            flash("비밀번호는 8자 이상 입력하세요.", "error")

        elif password != password_confirm:
            flash("비밀번호가 서로 일치하지 않습니다.", "error")

        elif User.query.filter_by(email=email).first():
            flash("이미 가입된 이메일입니다.", "error")

        else:
            user = User(email=email)
            user.set_password(password)

            db.session.add(user)
            db.session.commit()

            login_user(user)

            flash("회원가입이 완료되었습니다.", "success")

            return redirect(url_for("account"))

    return render_template("register.html")


# ==========================================
# 5. 로그인
# ==========================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if current_user.is_authenticated:
        return redirect(url_for("account"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            login_user(user)

            flash("로그인되었습니다.", "success")

            next_page = request.args.get("next")

            if next_page and next_page.startswith("/") and not next_page.startswith("//"):
                return redirect(next_page)

            return redirect(url_for("account"))

        flash("이메일 또는 비밀번호를 확인하세요.", "error")

    return render_template("login.html")


# ==========================================
# 6. 로그아웃
# ==========================================

@app.route("/logout", methods=["POST"])
@login_required
def logout():

    logout_user()

    flash("로그아웃되었습니다.", "success")

    return redirect(url_for("index"))


# ==========================================
# 7. 내 계정
# ==========================================

@app.route("/account")
@login_required
def account():

    return render_template("account.html", user=current_user)


# ==========================================
# 8. 관광정보 갤러리
# ==========================================

@app.route("/")
def index():

    keyword = request.args.get("keyword", "서울").strip() or "서울"
    content_type = request.args.get("content_type", "").strip()

    try:
        page = max(1, int(request.args.get("page", "1")))
    except ValueError:
        page = 1

    places, total_count, total_pages, error = [], 0, 1, None

    try:
        places, total_count, total_pages = search_places(
            keyword, page, content_type
        )

        if page > total_pages:
            page = total_pages

            places, total_count, total_pages = search_places(
                keyword, page, content_type
            )

    except (
        requests.RequestException,
        RuntimeError,
        ValueError
    ) as exc:
        error = str(exc)

    return render_template(
        "index.html",
        places=places,
        keyword=keyword,
        content_type=content_type,
        page=page,
        total_pages=total_pages,
        total_count=total_count,
        error=error
    )


# ==========================================
# 9. 관광정보 상세 페이지
# ==========================================

@app.route("/place/<content_id>")
def place_detail(content_id):

    content_type_id = request.args.get(
        "content_type_id", ""
    ).strip()

    if not content_id.isdigit() or not content_type_id.isdigit():
        abort(404)

    place = {
        "contentid": content_id,
        "contenttypeid": content_type_id,
        "title": request.args.get("title", "").strip(),
        "addr1": request.args.get("addr1", "").strip(),
        "addr2": request.args.get("addr2", "").strip(),
        "tel": request.args.get("tel", "").strip(),
        "zipcode": request.args.get("zipcode", "").strip(),
        "firstimage2": request.args.get("image", "").strip(),
        "firstimage": request.args.get("firstimage", "").strip(),
        "mapx": request.args.get("mapx", "").strip(),
        "mapy": request.args.get("mapy", "").strip(),
        "overview": "",
    }

    intro = {}
    errors = []

    try:
        common = get_detail_part(
            "detailCommon2",
            content_id,
            content_type_id,
            {
                "defaultYN": "Y",
                "firstImageYN": "Y",
                "areacodeYN": "Y",
                "catcodeYN": "Y",
                "addrinfoYN": "Y",
                "mapinfoYN": "Y",
                "overviewYN": "Y"
            }
        )

        for key, value in common.items():
            if value not in (None, ""):
                place[key] = value

    except (
        requests.RequestException,
        RuntimeError,
        ValueError
    ) as exc:
        errors.append(f"공통 상세정보 조회: {exc}")

        app.logger.warning(
            "detailCommon2 실패 (contentid=%s): %s",
            content_id, exc
        )

    try:
        intro = get_detail_part(
            "detailIntro2",
            content_id,
            content_type_id
        )

    except (
        requests.RequestException,
        RuntimeError,
        ValueError
    ) as exc:
        errors.append(f"추가 정보 조회: {exc}")

        app.logger.warning(
            "detailIntro2 실패 (contentid=%s): %s",
            content_id, exc
        )

    if not any(
        place.get(key)
        for key in (
            "title", "addr1", "firstimage",
            "firstimage2", "tel"
        )
    ):
        if errors:
            place["title"] = "상세정보 일부를 불러오지 못했습니다"
        else:
            abort(404)

    error = " / ".join(errors) if errors else None

    return render_template(
        "detail.html",
        place=place,
        intro=intro,
        content_type_name=CONTENT_TYPES.get(
            content_type_id, "관광정보"
        ),
        error=error
    )


# ==========================================
# 10. 서버 상태 확인
# ==========================================

@app.route("/health")
def health():
    return {"status": "ok"}


# ==========================================
# 11. 프로그램 실행
# ==========================================

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=False
    )

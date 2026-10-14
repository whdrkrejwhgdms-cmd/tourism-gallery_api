import os
import requests
from flask import Flask, render_template, request, abort

app = Flask(__name__)
BASE_URL = "https://apis.data.go.kr/B551011/KorService2"
SERVICE_KEY = os.environ.get("TOUR_API_KEY", "").strip()
PAGE_SIZE = 20
CONTENT_TYPES = {
    "12": "관광지", "14": "문화시설", "15": "행사·공연·축제",
    "25": "여행코스", "28": "레포츠", "32": "숙박",
    "38": "쇼핑", "39": "음식점"
}


def api_get(operation, params=None):
    """한국관광공사 API를 호출하고 결과 목록과 전체 건수를 반환합니다."""
    if not SERVICE_KEY:
        raise RuntimeError("API 인증키가 없습니다. Render 환경변수 TOUR_API_KEY를 등록하세요.")

    query = {
        "serviceKey": SERVICE_KEY,
        "MobileOS": "ETC",
        "MobileApp": "TourInfoGallery",
        "_type": "json",
        "numOfRows": PAGE_SIZE,
        "pageNo": 1,
    }
    query.update(params or {})

    response = requests.get(f"{BASE_URL}/{operation}", params=query, timeout=25)
    response.raise_for_status()
    try:
        data = response.json()
    except ValueError as exc:
        raise RuntimeError("관광공사 API가 JSON이 아닌 응답을 반환했습니다. 인증키와 API 신청 상태를 확인하세요.") from exc

    api_response = data.get("response", data)
    header = api_response.get("header", {})
    code = str(header.get("resultCode", ""))
    if code and code != "0000":
        raise RuntimeError(f"관광공사 API 오류({code}): {header.get('resultMsg', '오류')}")

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
    image = (item.get("firstimage2") or item.get("firstimage") or "").strip()
    return image if image.startswith(("https://", "http://")) else ""


def search_places(keyword, page, content_type):
    params = {"keyword": keyword, "numOfRows": PAGE_SIZE, "pageNo": page}
    if content_type:
        params["contentTypeId"] = content_type
    items, total_count = api_get("searchKeyword2", params)
    places = []
    for item in items:
        img = image_url(item)
        if img:
            item["gallery_image"] = img
            item["content_type_name"] = CONTENT_TYPES.get(str(item.get("contenttypeid", "")), "기타")
            places.append(item)
    total_pages = max(1, (total_count + PAGE_SIZE - 1) // PAGE_SIZE)
    return places, total_count, total_pages


def get_detail_part(operation, content_id, content_type_id, params=None):
    """상세 API 한 종류를 독립적으로 호출합니다. 실패해도 다른 결과는 유지할 수 있습니다."""
    request_params = {"contentId": content_id, "contentTypeId": content_type_id,
                      "numOfRows": 1, "pageNo": 1}
    request_params.update(params or {})
    items, _ = api_get(operation, request_params)
    return items[0] if items else {}


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
        places, total_count, total_pages = search_places(keyword, page, content_type)
        if page > total_pages:
            page = total_pages
            places, total_count, total_pages = search_places(keyword, page, content_type)
    except (requests.RequestException, RuntimeError, ValueError) as exc:
        error = str(exc)

    return render_template("index.html", places=places, keyword=keyword,
                           content_type=content_type, page=page,
                           total_pages=total_pages, total_count=total_count, error=error)


@app.route("/place/<content_id>")
def place_detail(content_id):
    content_type_id = request.args.get("content_type_id", "").strip()
    if not content_id.isdigit() or not content_type_id.isdigit():
        abort(404)

    # 목록에서 전달받은 기본 정보를 먼저 준비합니다.
    # 상세 API가 실패하더라도 이 기본 정보는 화면에 표시됩니다.
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

    # 공통 상세정보 요청. 검색 결과의 기본 필드는 API 값으로 보완합니다.
    try:
        common = get_detail_part("detailCommon2", content_id, content_type_id, {
            "defaultYN": "Y", "firstImageYN": "Y", "areacodeYN": "Y",
            "catcodeYN": "Y", "addrinfoYN": "Y", "mapinfoYN": "Y", "overviewYN": "Y"
        })
        for key, value in common.items():
            if value not in (None, ""):
                place[key] = value
    except (requests.RequestException, RuntimeError, ValueError) as exc:
        errors.append(f"공통 상세정보 조회: {exc}")
        app.logger.warning("detailCommon2 실패 (contentid=%s): %s", content_id, exc)

    # 소개정보 요청은 공통 상세정보 요청과 분리해 처리합니다.
    try:
        intro = get_detail_part("detailIntro2", content_id, content_type_id)
    except (requests.RequestException, RuntimeError, ValueError) as exc:
        errors.append(f"추가 정보 조회: {exc}")
        app.logger.warning("detailIntro2 실패 (contentid=%s): %s", content_id, exc)

    # 검색 결과에서도 전달되지 않았고 상세 API에도 결과가 없을 때만 404 처리합니다.
    if not any(place.get(key) for key in ("title", "addr1", "firstimage", "firstimage2", "tel")):
        if errors:
            place["title"] = "상세정보 일부를 불러오지 못했습니다"
        else:
            abort(404)

    error = " / ".join(errors) if errors else None
    return render_template("detail.html", place=place, intro=intro,
                           content_type_name=CONTENT_TYPES.get(content_type_id, "관광정보"),
                           error=error)


@app.route("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)

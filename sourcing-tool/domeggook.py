# -*- coding: utf-8 -*-
"""
도매꾹/도매매 Open API로 판촉물 상품을 검색하고, 선택한 상품을
소소기프트 Supabase products 테이블용 INSERT SQL로 변환하는 도구.

공식 API 문서 기준 (openapi.domeggook.com, 상품조회 카테고리):
  - 상품리스트: mode=getItemList
  - 상품상세정보: mode=getItemView

사용법:
  python domeggook.py search "텀블러" --market dome --size 20
  python domeggook.py import 12345678 23456789 --category tumbler --markup 1.5
"""

import os
import sys
import json
import argparse
import urllib.request
import urllib.parse

API_BASE = "https://www.domeggook.com/ssl/api/"


def load_api_key():
    here = os.path.dirname(__file__)
    candidates = ["apikey.txt", ".env", "config.txt"]
    for name in candidates:
        path = os.path.join(here, name)
        if not os.path.exists(path):
            continue
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("DOMEGGOOK_API_KEY="):
                    key = line.split("=", 1)[1].strip()
                elif line and "=" not in line and not line.startswith("#"):
                    key = line  # apikey.txt에 키만 한 줄 적어도 인식
                else:
                    continue
                if key and not key.startswith("여기에"):
                    return key
    sys.exit(
        "API 키 파일을 찾지 못했습니다. sourcing-tool 폴더에 'apikey.txt' 파일을 만들고 "
        "그 안에 발급받은 API 키만 한 줄로 적어서 저장해주세요."
    )


def call_api(params):
    url = API_BASE + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "SosoGiftSourcingTool/1.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.load(resp)
    return data


def search_items(api_key, keyword, market="dome", size=20, page=1, sort="rd"):
    params = {
        "ver": "4.1",
        "mode": "getItemList",
        "aid": api_key,
        "market": market,
        "om": "json",
        "kw": keyword,
        "sz": size,
        "pg": page,
        "so": sort,
    }
    data = call_api(params)
    root = data.get("domeggook", data)  # 응답이 {"domeggook": {...}} 로 한 겹 더 감싸져 있음
    items = root.get("list", {}).get("item", [])
    if isinstance(items, dict):  # 결과가 1건이면 dict로 올 수 있음
        items = [items]
    return items


def get_item_detail(api_key, item_no, market="dome"):
    params = {
        "ver": "4.6",
        "mode": "getItemView",
        "aid": api_key,
        "market": market,
        "om": "json",
        "no": item_no,
    }
    data = call_api(params)
    return data.get("domeggook", data)  # 응답이 {"domeggook": {...}} 로 한 겹 더 감싸져 있음


def parse_base_price(price_value):
    """'1+3800|20+3500|50+3300' 형태(수량별 차등가) 또는 단순 숫자를 처리해
    1개 구매 기준 단가(int)를 반환."""
    if price_value is None:
        return 0
    s = str(price_value)
    if "+" in s:
        first_tier = s.split("|")[0]
        qty, price = first_tier.split("+")
        return int(float(price))
    try:
        return int(float(s))
    except ValueError:
        return 0


def build_search_report(items, out_path):
    rows = []
    for it in items:
        title = it.get("title", "")
        item_no = it.get("no", "")
        wholesale = parse_base_price(it.get("price"))
        thumb = it.get("thumb", "")
        img = thumb if isinstance(thumb, str) else (thumb.get("large") or thumb.get("small") or "")
        rows.append(
            "<tr>"
            "<td><img src='" + str(img) + "' style='width:70px;height:70px;object-fit:cover;border-radius:6px;'></td>"
            "<td>" + str(item_no) + "</td>"
            "<td>" + str(title) + "</td>"
            "<td style='text-align:right;'>" + "{:,}".format(wholesale) + "원</td>"
            "</tr>"
        )
    html = (
        "<!DOCTYPE html><html><head><meta charset='utf-8'>"
        "<style>body{font-family:'Malgun Gothic',sans-serif;padding:20px;}"
        "table{border-collapse:collapse;width:100%;}"
        "th,td{border:1px solid #ddd;padding:8px;font-size:13px;}"
        "th{background:#1E293B;color:#fff;}</style></head><body>"
        "<h2>도매꾹/도매매 검색 결과 (" + str(len(items)) + "건)</h2>"
        "<p>마음에 드는 상품의 '상품번호'를 메모해두세요. "
        "import 명령에 그 번호를 넣으면 실제 상품 데이터로 변환해드립니다.</p>"
        "<table><tr><th>이미지</th><th>상품번호</th><th>상품명</th><th>도매단가(1개 기준)</th></tr>"
        + "".join(rows) +
        "</table></body></html>"
    )
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)


CATEGORY_LABELS = {
    "office": "문구·오피스", "tumbler": "텀블러·보온병", "bag": "가방·에코백",
    "umbrella": "우산", "apparel": "의류·단체복", "cap": "모자",
    "electronics": "IT·전자", "kitchen": "생활·주방", "health": "건강·위생",
    "season": "시즌·기획상품",
}


def build_import_sql(api_key, item_nos, market, category, markup, out_path):
    rows = []
    for no in item_nos:
        detail = get_item_detail(api_key, no, market=market)
        basis = detail.get("basis", {})
        price_info = detail.get("price", {})
        thumb = detail.get("thumb", {})

        name = (basis.get("title") or "").replace("'", "''")[:120]
        wholesale = parse_base_price(price_info.get("dome") or price_info.get("supply"))
        price = round(wholesale * markup / 10) * 10  # 10원 단위 반올림
        old_price = round(price * 1.25 / 10) * 10
        discount_rate = 20
        img = thumb.get("large") or thumb.get("original") or thumb.get("small") or ""
        slug = "dg-" + str(no)

        if wholesale == 0:
            print("경고: 상품번호 " + str(no) + " 가격 정보를 가져오지 못했습니다. 건너뜁니다.")
            continue

        rows.append(
            "('" + slug + "', '" + name + "', '" + category + "', '" + img + "', "
            "null, " + str(old_price) + ", " + str(price) + ", " + str(discount_rate) + ", "
            "0, 0, 0, '#도매소싱', null)"
        )
        print("[OK] " + str(no) + " " + name + " -> 도매" + "{:,}".format(wholesale) + "원 / 판매" + "{:,}".format(price) + "원")

    if not rows:
        print("추가할 상품이 없습니다.")
        return

    sql = (
        "-- 도매꾹/도매매에서 소싱한 상품을 소소기프트 products 테이블에 추가\n"
        "-- 카테고리: " + CATEGORY_LABELS.get(category, category) + "\n"
        "-- Supabase 대시보드 SQL Editor에서 실행하세요.\n\n"
        "insert into products (slug, name, category, image_url, badge, old_price, price, discount_rate, rating, review_count, wish_count, tags, detail_url) values\n"
        + ",\n".join(rows) + ";\n"
    )
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(sql)
    print("\n완료: " + out_path)


def main():
    parser = argparse.ArgumentParser(description="도매꾹/도매매 판촉물 소싱 도구")
    sub = parser.add_subparsers(dest="command", required=True)

    p_search = sub.add_parser("search", help="상품 검색")
    p_search.add_argument("keyword")
    p_search.add_argument("--market", default="dome", choices=["dome", "supply"])
    p_search.add_argument("--size", type=int, default=20)
    p_search.add_argument("--sort", default="rd")

    p_import = sub.add_parser("import", help="선택한 상품을 Supabase용 SQL로 변환")
    p_import.add_argument("item_numbers", nargs="+")
    p_import.add_argument("--market", default="dome", choices=["dome", "supply"])
    p_import.add_argument("--category", required=True, choices=list(CATEGORY_LABELS.keys()))
    p_import.add_argument("--markup", type=float, default=1.5, help="도매가 대비 판매가 배율 (기본 1.5배)")

    args = parser.parse_args()
    api_key = load_api_key()
    out_dir = os.path.join(os.path.dirname(__file__), "output")
    os.makedirs(out_dir, exist_ok=True)

    if args.command == "search":
        items = search_items(api_key, args.keyword, market=args.market, size=args.size, sort=args.sort)
        out_path = os.path.join(out_dir, "search_results.html")
        build_search_report(items, out_path)
        print(str(len(items)) + "건 검색됨. 결과 리포트: " + out_path)

    elif args.command == "import":
        out_path = os.path.join(out_dir, "import.sql")
        build_import_sql(api_key, args.item_numbers, args.market, args.category, args.markup, out_path)


if __name__ == "__main__":
    main()

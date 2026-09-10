import io
import re
from datetime import date
from typing import Optional

import pandas as pd
import streamlit as st

st.set_page_config(page_title="온라인 광고 분석", page_icon="📊", layout="wide")

st.markdown(
    """
    <style>
    .block-container { max-width: 1400px; padding: 2rem 3rem 4rem; }
    [data-testid="stMetric"] { background: #f7f9fc; border: 1px solid #e6eaf0; padding: 0.65rem 0.9rem; border-radius: 8px; }
    [data-testid="stMetricLabel"] { font-size: 0.85rem; }
    [data-testid="stMetricValue"] { font-size: 1.8rem; line-height: 1.15; }
    [data-testid="stDataFrame"] { border: 1px solid #e6eaf0; border-radius: 10px; }
    h1, h2, h3 { letter-spacing: 0; }
    @media (max-width: 1100px) {
        .block-container { padding: 1rem 1.25rem 3rem; }
        [data-testid="stMetric"] { padding: 0.5rem 0.75rem; }
        [data-testid="stMetricValue"] { font-size: 1.35rem; }
        [data-testid="stDataFrame"] { font-size: 0.85rem; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

COLUMN_ALIASES = {
    "month": ["발생월", "판매월", "주문월", "월", "발생일", "주문일", "판매일", "date", "month"],
    "product": ["상품명", "상품명칭", "제품명", "상품", "product", "item"],
    "product_id": ["상품번호", "상품코드", "상품ID", "상품 id", "product id", "item id"],
    "impressions": ["노출수", "노출", "impression", "impressions", "광고노출수"],
    "clicks": ["클릭수", "클릭", "click", "clicks", "광고클릭수"],
    "orders": ["구매수", "구매수량", "주문수", "주문수량", "주문", "판매수량", "orders", "order"],
    "direct_orders": ["직접전환수", "직접 전환수", "direct conversion count", "directorders"],
    "file_total_cost": ["총비용", "총 비용", "total cost", "totalcost"],
    "ad_cost": ["광고비", "소진광고비", "총광고비", "비용", "cost", "spend"],
    "sales": [
        "구매금액", "구매금액금액", "매출액금액", "매출액", "매출금액", "주문금액", "판매금액", "판매액",
        "총매출", "거래액", "전환매출", "광고전환매출", "광고매출", "sales", "revenue",
    ],
    "direct_sales": ["직접전환금액", "직접 전환금액", "direct conversion amount", "directsales"],
    "direct_ad_return": ["직접광고수익률", "직접 광고수익률", "direct ad return", "directroas"],
    "supply_cost": ["공급가", "매입가", "원가", "공급가격", "costprice"],
    "platform_fee": ["수수료", "판매수수료", "플랫폼수수료", "fee"],
    "shipping": ["배송비", "배송비용", "shipping"],
}

DISPLAY_NAMES = {
    "impressions": "노출수", "clicks": "클릭수", "orders": "주문수",
    "ad_cost": "광고비", "sales": "매출", "supply_cost": "공급가",
    "platform_fee": "수수료", "shipping": "배송비",
}


def clean_name(value: object) -> str:
    return re.sub(r"[^a-z0-9가-힣]", "", str(value).lower())


def find_column(columns: list[object], aliases: list[str]) -> Optional[object]:
    cleaned = {clean_name(column): column for column in columns}
    for alias in aliases:
        if clean_name(alias) in cleaned:
            return cleaned[clean_name(alias)]
    for column in columns:
        normalized = clean_name(column)
        if any(clean_name(alias) in normalized for alias in aliases):
            return column
    return None


def parse_number(series: pd.Series) -> pd.Series:
    return pd.to_numeric(
        series.astype(str).str.replace(",", "", regex=False).str.replace("원", "", regex=False).str.replace("%", "", regex=False),
        errors="coerce",
    ).fillna(0)


def parse_month(series: pd.Series) -> pd.Series:
    parsed = pd.to_datetime(series, errors="coerce")
    return parsed.dt.to_period("M").astype("string")


def format_currency_columns(frame: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    formatted = frame.copy()
    for column in columns:
        if column in formatted.columns:
            formatted[column] = formatted[column].map(lambda value: f"{value:,.0f}원")
    return formatted


def read_uploaded_file(uploaded_file) -> pd.DataFrame:
    raw = uploaded_file.getvalue()
    if uploaded_file.name.lower().endswith(".csv"):
        for encoding in ("utf-8-sig", "cp949", "euc-kr", "utf-8"):
            try:
                return pd.read_csv(io.BytesIO(raw), encoding=encoding)
            except UnicodeDecodeError:
                continue
        return pd.read_csv(io.BytesIO(raw))
    workbook = pd.ExcelFile(io.BytesIO(raw))
    frames = []
    for sheet in workbook.sheet_names:
        default_frame = pd.read_excel(io.BytesIO(raw), sheet_name=sheet)
        first_row_text = " ".join(str(value) for value in default_frame.iloc[0].tolist()) if not default_frame.empty else ""
        has_grouped_header = any(label in first_row_text for label in ("수량", "금액", "%"))
        if has_grouped_header:
            multi_header = pd.read_excel(io.BytesIO(raw), sheet_name=sheet, header=[0, 1])
            flattened = []
            for parent, child in multi_header.columns:
                parent_text = "" if str(parent).startswith("Unnamed") else str(parent)
                child_text = "" if str(child).startswith("Unnamed") else str(child)
                flattened.append(" ".join(part for part in (parent_text, child_text) if part).strip())
            multi_header.columns = flattened
            frames.append(multi_header)
        else:
            frames.append(default_frame)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def detect_channel(filename: str) -> str:
    name = filename.lower()
    if "spscst11" in name or "옥션" in filename:
        return "옥션"
    if "지마켓" in filename or "gmarket" in name:
        return "지마켓"
    if "11번가" in filename or "11st" in name:
        return "11번가"
    if "스마트스토어" in filename or "naver" in name:
        return "네이버"
    if "롯데온" in filename or "lotte" in name:
        return "롯데온"
    return re.sub(r"광고|리포트|report", "", flags=re.IGNORECASE, string=filename).rsplit(".", 1)[0].strip(" _-") or filename


def normalize_frame(frame: pd.DataFrame, channel: str) -> tuple[pd.DataFrame, list[str]]:
    if "11번가" in channel:
        total_row = frame.astype(str).apply(
            lambda row: row.str.contains("합계|총합계|총계", case=False, na=False).any(), axis=1
        )
        if total_row.any():
            frame = frame.loc[~total_row].reset_index(drop=True)
        elif len(frame.index) > 0:
            frame = frame.iloc[1:].reset_index(drop=True)
    result = pd.DataFrame(index=frame.index)
    missing = []
    result["채널"] = channel
    for key, aliases in COLUMN_ALIASES.items():
        source = find_column(list(frame.columns), aliases)
        if source is None:
            if key == "month":
                result[key] = pd.Series(pd.NA, index=frame.index, dtype="string")
                continue
            if key in ("product", "product_id"):
                result[key] = [f"상품 {index + 1}" for index in range(len(frame))]
            elif key in ("supply_cost", "platform_fee", "shipping", "file_total_cost"):
                result[key] = 0
            elif key in ("direct_orders", "direct_sales", "direct_ad_return"):
                result[key] = 0
            else:
                result[key] = 0
                missing.append(DISPLAY_NAMES.get(key, key))
        elif key == "month":
            result[key] = parse_month(frame[source])
        elif key in ("product", "product_id"):
            result[key] = frame[source].fillna("상품명 없음").astype(str)
        else:
            result[key] = parse_number(frame[source])
        if key in ("direct_orders", "direct_sales", "direct_ad_return"):
            result[f"{key}_provided"] = source is not None
        if key == "file_total_cost":
            result["file_total_cost_provided"] = source is not None
    if "file_total_cost_provided" not in result:
        result["file_total_cost_provided"] = False
    for key in ("direct_orders", "direct_sales", "direct_ad_return"):
        if f"{key}_provided" not in result:
            result[f"{key}_provided"] = False
    if "롯데온" in channel:
        result["ad_cost"] = 0
    if "11번가" in channel:
        result.loc[result["direct_orders_provided"], "orders"] = result.loc[result["direct_orders_provided"], "direct_orders"]
        result.loc[result["direct_sales_provided"], "sales"] = result.loc[result["direct_sales_provided"], "direct_sales"]
        if "상품번호" in frame.columns or result["product_id"].ne("상품명 없음").any():
            result["product"] = result["product_id"]
    return result, sorted(set(missing))


def analyze(data: pd.DataFrame) -> pd.DataFrame:
    result = data.copy()
    result["CTR"] = result["clicks"] / result["impressions"].replace(0, pd.NA) * 100
    result["구매전환율"] = result["orders"] / result["clicks"].replace(0, pd.NA) * 100
    result["ROAS"] = result["sales"] / result["ad_cost"].replace(0, pd.NA) * 100
    calculated_cost = result["supply_cost"] + result["platform_fee"] + result["shipping"] + result["ad_cost"]
    result["총비용"] = result["file_total_cost"].where(result["file_total_cost_provided"], calculated_cost)
    result["비용대비구매금액"] = result["sales"] / result["총비용"].replace(0, pd.NA) * 100
    direct_return_available = (result["채널"] == "11번가") & result["direct_ad_return_provided"]
    result.loc[direct_return_available, "비용대비구매금액"] = result.loc[direct_return_available, "direct_ad_return"]
    result["수익성판정값"] = result["sales"] - result["총비용"]
    result["광고판정"] = result.apply(recommend_action, axis=1)
    return result.fillna(0)


def recommend_action(row: pd.Series) -> str:
    roas = row["ROAS"] if pd.notna(row["ROAS"]) else 0
    conversion = row["구매전환율"] if pd.notna(row["구매전환율"]) else 0
    if row["impressions"] == 0:
        return "상품정보 개선 필요"
    if row["clicks"] == 0:
        return "상품정보 개선 필요"
    if row["orders"] == 0 and row["clicks"] >= 10:
        return "상품정보 개선 필요"
    if row["수익성판정값"] < 0:
        return "광고 중단"
    if roas >= 300 and conversion >= 2:
        return "광고 확대"
    if roas < 150:
        return "광고 축소"
    return "광고 유지"


st.title("온라인 쇼핑몰 광고 분석")
st.caption("옥션·지마켓·11번가 광고 리포트를 업로드하면 상품별 성과와 개선 방향을 확인합니다.")

with st.sidebar:
    st.header("분석 설정")
    target_roas = st.number_input("목표 ROAS (%)", min_value=0, value=300, step=50)
    attachment_date = st.date_input(
        "파일 첨부 기준일",
        value=date.today(),
        help="기본값은 프로그램을 실행한 날짜입니다. 파일에 이 날짜 이후의 자료가 있으면 자동 제외합니다.",
    )
    st.info("파일 첨부 기준일 이후의 월 자료는 자동으로 제외됩니다.")

uploads = st.file_uploader("광고 리포트 업로드 (.xlsx, .csv)", type=["xlsx", "xls", "csv"], accept_multiple_files=True)

if not uploads:
    st.warning("광고 리포트 파일을 업로드하면 분석이 시작됩니다.")
    st.markdown("**필수 권장 열:** 상품명, 노출수, 클릭수, 주문수, 광고비, 매출")
    st.stop()

frames = []
issues = []
for uploaded in uploads:
    channel = detect_channel(uploaded.name)
    try:
        normalized, missing = normalize_frame(read_uploaded_file(uploaded), channel)
        frames.append(normalized)
        if missing:
            issues.append(f"{uploaded.name}: {', '.join(missing)}")
    except Exception as error:
        st.error(f"{uploaded.name}을 읽지 못했습니다: {error}")

if not frames:
    st.stop()

combined = pd.concat(frames, ignore_index=True)
try:
    cutoff_month = pd.Period(attachment_date.strftime("%Y-%m"), freq="M")
    valid_months = combined["month"].notna()
    combined.loc[valid_months, "month_period"] = combined.loc[valid_months, "month"].map(lambda value: pd.Period(value, freq="M"))
    combined = combined[~valid_months | (combined["month_period"] <= cutoff_month)]
except (ValueError, TypeError):
    st.sidebar.error("파일 첨부 기준일을 확인하세요.")

analysis = analyze(combined)
analysis["ROAS"] = analysis["ROAS"].replace(0, pd.NA)

if issues:
    with st.expander("자동 인식이 안 된 열 확인"):
        for issue in issues:
            st.write(issue)

st.subheader("채널별 성과")
channel_summary = analysis.groupby("채널", as_index=False).agg(
    구매금액=("sales", "sum"), 총비용=("총비용", "sum"), 구매수=("orders", "sum")
)
channel_summary["전환율"] = channel_summary["구매수"] / analysis.groupby("채널")["clicks"].sum().reindex(channel_summary["채널"]).replace(0, pd.NA).to_numpy() * 100
channel_summary["광고수익율"] = channel_summary["구매금액"] / channel_summary["총비용"].replace(0, pd.NA) * 100
channel_display = channel_summary.rename(columns={"총비용": "총 광고비용"})
channel_display = format_currency_columns(channel_display.fillna(0), ["구매금액", "총 광고비용"])
for column in ["전환율", "광고수익율"]:
    channel_display[column] = channel_display[column].map(lambda value: f"{value:.1f}%")
st.dataframe(channel_display, use_container_width=True, hide_index=True)

st.subheader("핵심 상품 현황")
best_sellers, ad_only, needs_improvement = st.columns(3)
with best_sellers:
    st.markdown("**구매수량 상위 상품**")
    best = analysis.sort_values(["orders", "sales"], ascending=False).head(10)
    best_display = best[["product", "orders", "sales"]].rename(columns={"product": "상품명", "orders": "구매수", "sales": "구매금액"})
    st.dataframe(format_currency_columns(best_display, ["구매금액"]), use_container_width=True, hide_index=True)
with ad_only:
    st.markdown("**광고비만 사용하는 상품**")
    spenders = analysis[(analysis["총비용"] >= 5000) & (analysis["sales"] <= 5000)].sort_values(
        "총비용", ascending=False
    )
    spenders_display = spenders[["product", "총비용", "sales", "광고판정"]].rename(
        columns={"product": "상품명", "sales": "구매금액"}
    )
    st.dataframe(format_currency_columns(spenders_display, ["총비용", "구매금액"]), use_container_width=True, hide_index=True)
with needs_improvement:
    st.markdown("**개선이 필요한 상품**")
    improvements = analysis[analysis["광고판정"] == "상품정보 개선 필요"].sort_values("clicks", ascending=False).head(10)
    st.dataframe(
        improvements[["product", "impressions", "clicks", "orders", "광고판정"]].rename(
            columns={"product": "상품명", "impressions": "노출수", "clicks": "클릭수", "orders": "구매수"}
        ),
        use_container_width=True,
        hide_index=True,
    )

st.subheader("상품 우선순위 분석")
priority_columns = st.columns(3) + st.columns(2)

with priority_columns[0]:
    st.markdown("**구매금액이 높은 상품 20개**")
    high_sales = analysis[analysis["sales"] > 0].sort_values("sales", ascending=False).head(20)
    st.dataframe(
        format_currency_columns(high_sales[["product", "sales", "orders"]].rename(
            columns={"product": "상품명", "sales": "구매금액", "orders": "구매수"}
        ), ["구매금액"]),
        use_container_width=True,
        hide_index=True,
    )

with priority_columns[3]:
    st.markdown("**전환율이 높은 상품**")
    high_conversion = analysis[(analysis["clicks"] > 0) & (analysis["orders"] > 0)].sort_values(
        ["구매전환율", "orders"], ascending=False
    ).head(20)
    st.dataframe(
        format_currency_columns(high_conversion[["product", "구매전환율", "orders", "sales"]].rename(
            columns={"product": "상품명", "구매전환율": "전환율", "orders": "구매수", "sales": "구매금액"}
        ), ["구매금액"]),
        use_container_width=True,
        hide_index=True,
    )

with priority_columns[2]:
    st.markdown("**저효율상품**")
    low_ad_return = analysis[(analysis["총비용"] >= 5000) & (analysis["비용대비구매금액"] <= 150)].sort_values(
        ["총비용", "비용대비구매금액"], ascending=[False, True]
    )
    low_ad_return_display = low_ad_return[["product", "총비용", "sales", "비용대비구매금액"]].rename(
        columns={"product": "상품명", "sales": "구매금액", "비용대비구매금액": "광고수익율"}
    )
    low_ad_return_display["광고수익율"] = low_ad_return_display["광고수익율"].round(2).map(lambda value: f"{value:,.2f}%")
    st.dataframe(
        format_currency_columns(low_ad_return_display, ["총비용", "구매금액"]),
        use_container_width=True,
        hide_index=True,
    )

with priority_columns[1]:
    st.markdown("**고효율상품**")
    high_ad_return = analysis[(analysis["총비용"] >= 5000) & (analysis["비용대비구매금액"] >= 250)].sort_values(
        ["총비용", "비용대비구매금액"], ascending=[False, False]
    )
    high_ad_return_display = high_ad_return[["product", "총비용", "sales", "비용대비구매금액"]].rename(
        columns={"product": "상품명", "sales": "구매금액", "비용대비구매금액": "광고수익율"}
    )
    high_ad_return_display["광고수익율"] = high_ad_return_display["광고수익율"].round(2).map(lambda value: f"{value:,.2f}%")
    st.dataframe(
        format_currency_columns(high_ad_return_display, ["총비용", "구매금액"]),
        use_container_width=True,
        hide_index=True,
    )

with priority_columns[4]:
    st.markdown("**노출대비 저효율 상품**")
    low_purchase_after_exposure = analysis[
        (analysis["impressions"] >= 500) & (analysis["sales"] <= 5000)
    ].sort_values(["impressions", "clicks"], ascending=[False, True])
    low_purchase_display = low_purchase_after_exposure[["product", "impressions", "clicks", "sales"]].rename(
        columns={"product": "상품명", "impressions": "노출수", "clicks": "클릭수", "sales": "구매금액"}
    )
    st.dataframe(
        format_currency_columns(low_purchase_display, ["구매금액"]),
        use_container_width=True,
        hide_index=True,
    )

st.subheader("상품별 분석")
status = st.multiselect("판정 필터", sorted(analysis["광고판정"].unique()), default=sorted(analysis["광고판정"].unique()))
filtered = analysis[analysis["광고판정"].isin(status)].copy()
show = filtered[["채널", "product", "impressions", "clicks", "CTR", "orders", "구매전환율", "sales", "총비용", "비용대비구매금액", "광고판정"]].rename(columns={
    "product": "상품명", "impressions": "노출수", "clicks": "클릭수", "CTR": "클릭률", "orders": "구매수", "구매전환율": "전환율", "sales": "구매금액", "비용대비구매금액": "광고수익율"
})
for column in ["클릭률", "전환율", "광고수익율"]:
    show[column] = show[column].round(2)
show_display = format_currency_columns(show.sort_values("구매금액", ascending=False), ["구매금액", "총비용"])
st.dataframe(show_display, use_container_width=True, hide_index=True)

csv_data = show.to_csv(index=False, encoding="utf-8-sig")
st.download_button("분석 결과 CSV 다운로드", csv_data, "광고분석결과.csv", "text/csv")

st.subheader("운영 해석")
st.write(f"현재 목표 ROAS는 {target_roas:,}%입니다. '광고 확대 검토' 상품은 실제 순이익과 재고를 확인한 뒤 예산을 늘리세요.")

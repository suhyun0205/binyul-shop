# 온라인 쇼핑몰 광고 분석 프로그램

광고 API에서 데이터를 직접 가져오거나 옥션, 지마켓, 11번가 등의 광고 리포트 CSV/XLSX 파일을 분석합니다.

## 실행 방법

PowerShell에서 프로젝트 폴더로 이동한 뒤 실행합니다.

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

실행 후 브라우저에서 표시되는 주소를 열고 사이드바에서 `광고 API 직접연동`을 선택합니다.

## 광고 API 직접연동

### 네이버 검색광고

기본 데이터 소스는 네이버 검색광고입니다. 네이버 검색광고 API의 `CUSTOMER_ID`, `API_KEY`, `SECRET_KEY`와 조회할 캠페인 ID가 필요합니다. 앱은 네이버 공식 `/stats` API에 HMAC-SHA256 서명을 만들어 기준일 데이터를 조회합니다. 캠페인 ID는 여러 개 입력할 때 쉼표로 구분합니다.

`.streamlit/secrets.toml`에 저장하면 화면에 매번 입력하지 않아도 됩니다.

프로젝트 안의 `.streamlit/secrets.toml.example`을 복사해 `.streamlit/secrets.toml`로 이름을 바꾼 뒤 실제 값을 한 번만 입력하세요. `.streamlit` 폴더는 Git에서 제외되어 있습니다.

```toml
NAVER_SEARCH_ADS_CUSTOMER_ID = "고객ID"
NAVER_SEARCH_ADS_API_KEY = "API키"
NAVER_SEARCH_ADS_SECRET_KEY = "시크릿키"
NAVER_SEARCH_ADS_CAMPAIGN_IDS = "cmp-a,camp-b"
```

앱은 기준일마다 API에 `GET` 요청을 보내며, 다음 파라미터와 응답 형식을 사용합니다.

- 요청 파라미터: `start_date=YYYY-MM-DD`, `end_date=YYYY-MM-DD`
- 인증 헤더: `Authorization: Bearer API토큰`
- 응답: 행 배열 또는 `{ "data": [...] }`
- 권장 열: `상품번호`, `노출수`, `클릭수`, `주문수`, `광고비`, `매출`

토큰은 `.streamlit/secrets.toml`에 저장할 수 있습니다.

```toml
AD_API_ENDPOINT = "https://광고플랫폼.example.com/api/report"
AD_API_TOKEN = "발급받은_토큰"
AD_API_CHANNEL = "내 광고채널"
```

같은 기준일의 API 응답은 24시간 캐시합니다. 앱을 열지 않아도 매일 자동 수집하려면 Windows 작업 스케줄러 또는 서버 작업이 추가로 필요합니다. 사용 중인 광고 플랫폼명과 공식 API 문서를 주면 해당 플랫폼의 OAuth, 서명, 응답 필드까지 맞춰 고정할 수 있습니다.

## Google Drive로 이동

광고 폴더와 소스 코드는 Google Drive 동기화 폴더로 옮겨도 됩니다. 단, `.venv`는 옮기지 말고 새 위치에서 다시 만들며, 실제 API 키가 들어 있는 `.streamlit/secrets.toml`은 Google Drive에 동기화하지 않는 것을 권장합니다. 코드는 Drive에 두고 비밀 설정은 각 PC의 로컬 `.streamlit/secrets.toml` 또는 환경변수에 따로 보관하세요.

## 자동 분석 항목

- 노출수, 클릭수, CTR
- 주문수, 구매전환율
- 광고비, 매출, ROAS
- 공급가·수수료·배송비를 반영한 예상순이익
- 상품별 광고 확대, 유지, 축소, 중단 또는 페이지 개선 판정

파일별 열 이름이 조금 달라도 주요 한글 열 이름을 자동으로 찾아봅니다. 열 이름이 채널 리포트에서 완전히 다르면 화면의 인식 누락 안내를 확인해 열 이름 매핑을 보완하면 됩니다.

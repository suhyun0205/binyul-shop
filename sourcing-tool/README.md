# 소소기프트 도매꾹/도매매 소싱 도구

공식 도매꾹 Open API(openapi.domeggook.com)를 사용합니다. 스크래핑이 아니라 공식 API라 안전합니다.

## 준비

1. `.env.example`을 복사해서 `.env`로 저장
2. `.env` 안에 발급받은 API 키 입력 (`.env`는 git에 올라가지 않습니다)

## 사용법

### 1) 상품 검색

```
python domeggook.py search "텀블러"
```

실행하면 `output/search_results.html`에 검색 결과(이미지/상품번호/상품명/도매단가)가 저장됩니다. 브라우저로 열어서 확인하세요.

옵션:
- `--market dome` (도매꾹, 기본값) 또는 `--market supply` (도매매)
- `--size 20` 결과 개수 (최대 200)
- `--sort rd` 정렬 (`rd`=랭킹순, `aa`=낮은가격순, `da`=최근등록순)

### 2) 마음에 든 상품을 소소기프트에 추가

검색 결과에서 상품번호를 확인한 뒤:

```
python domeggook.py import 12345678 23456789 --category tumbler --markup 1.5
```

- `--category`: office / tumbler / bag / umbrella / apparel / cap / electronics / kitchen / health / season 중 하나
- `--markup`: 도매가 대비 판매가 배율 (기본 1.5배 = 도매가의 150%로 판매)

실행하면 `output/import.sql`이 생성됩니다. 이 파일 내용을 **Supabase 대시보드 → SQL Editor**에 붙여넣고 실행하면 실제 상품으로 등록됩니다 (바로 반영되지 않고, 직접 실행해야 안전합니다).

## 주의

- 가격은 자동 계산이라, 실제 등록 전에 `import.sql`을 한번 열어서 가격이 적절한지 확인하세요.
- 이미지 URL은 도매꾹 서버 것을 그대로 씁니다. 장기적으로는 직접 다운로드해서 우리 서버에 올리는 게 더 안전합니다 (도매꾹 측 이미지가 삭제되면 깨질 수 있음).

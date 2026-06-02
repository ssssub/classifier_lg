# LG 냉장고 추천 상담 앱

Streamlit 기반 LG 냉장고 추천 웹앱입니다. 사용자의 라이프스타일, 예산, 설치 타입, 사용 패턴, 선호 기능을 바탕으로 실제 엑셀 DB의 제품을 필터링하고 Top 5 추천 결과를 보여줍니다.

## 배포 진입점

Streamlit 앱 파일:

```bash
streamlit_app.py
```

로컬 실행:

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

Windows에서 8501 포트가 이미 사용 중일 수 있으면 아래 파일로 실행하세요. 8501부터 빈 포트를 자동으로 찾아 실행합니다.

```powershell
.\run_lg_advisor.ps1
```

## Streamlit Community Cloud 배포

1. 이 저장소를 GitHub에 push합니다.
2. Streamlit Community Cloud에서 새 앱을 생성합니다.
3. Main file path에 아래 값을 입력합니다.

```text
streamlit_app.py
```

4. 배포하면 앱이 `artifacts/lg-advisor/app.py`를 자동으로 실행합니다.

## 데이터와 이미지

앱은 아래 엑셀 파일을 실제 제품 DB로 사용합니다.

```text
artifacts/lg-advisor/LG_냉장고_대표상품기준_통합DB.xlsx
```

제품 이미지는 엑셀의 `이미지 분류명` 값과 같은 이름의 파일로 매핑됩니다.

```text
artifacts/lg-advisor/public/product_images/
```

## 주요 파일

- `streamlit_app.py`: 배포용 루트 진입점
- `artifacts/lg-advisor/app.py`: Streamlit UI
- `artifacts/lg-advisor/engine.py`: 질문 흐름, 필터링, 추천 정렬
- `artifacts/lg-advisor/data_loader.py`: 엑셀 DB 로딩 및 제품 정규화
- `artifacts/lg-advisor/ui_config.py`: 질문/선택지 텍스트 설정
- `requirements.txt`: 배포 의존성
- `runtime.txt`: 배포 Python 버전

## 로컬 런타임 데이터

`artifacts/lg-advisor/data/sessions.db`는 실행 중 자동 생성되는 로컬 로그 DB입니다. 배포 산출물에는 포함하지 않습니다.

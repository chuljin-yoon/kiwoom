# Kiwoom-Bank
KDA 은행 1팀 1차프로젝트

## Installation

프로젝트 실행 전에 필요한 라이브러리를 설치하세요:

```bash
pip install -r requirements.txt
```

Poetry를 사용하는 경우에는 다음 명령으로 동일한 의존성을 설치할 수 있습니다.

```bash
poetry install
```

그 후 `main.py`를 실행하면 `pandas`, `dart-fss`, `openpyxl` 등 필요한 의존성이 포함됩니다.

## Usage

원하는 회사를 지정하여 재무제표를 내려받을 수 있습니다. 회사명, 고유번호, 종목코드 가운데
하나 이상을 입력하면 됩니다.

```bash
python main.py --corp-name "삼성전자" --output data/samsung.xlsx
```

명령에 `--output`을 지정하지 않으면 각 재무제표의 상위 5개 행이 터미널에 출력됩니다. 기본적으로
공개 데모 API 키를 사용하지만, 환경 변수 `DART_API_KEY` 혹은 `--api-key` 옵션으로 자신만의 키를
설정하면 더 안정적으로 이용할 수 있습니다.

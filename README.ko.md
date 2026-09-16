# KORMARCXML

[English](README.md) · [아키텍처](docs/architecture.md) · [API](docs/api.md)

**KORMARC를 XML 환경에서 처리하기 위한 비공식 오픈소스 프레임워크**입니다.
국립중앙도서관 또는 KS가 제정한 공식 표준이나 공식 제품이 아닙니다.

0.1.0은 ISO 2709 ↔ XML 변환, 계층별 검증, 메타데이터 변환, 화면 표시,
명령줄 도구(CLI), 다른 프로그램에서 불러 쓰는 Python API를 제공합니다.
통합서지용 **KS X 6006-0:2023**을 대상으로 하되, 검증기는 출처를 확인한
일부 규칙만 구현합니다. **오류가 없다는 결과는 KORMARC 전체 규격 준수를
보증하지 않습니다.**

## 1. 처리 구조

ISO 2709 바이트를 읽어 순서가 있는 레코드 모델로 만들고, 일반적인 XML
구조로 저장합니다. 이 공통 데이터를 검증기·변환기·화면 표시기가 재사용합니다.

- 필드·식별기호의 순서, 반복, 공백 지시기호, 한글·한자, 로컬 필드를 보존합니다.
- 디렉터리, 레코드 길이, 기본번지는 출력할 때 바이트 단위로 다시 계산합니다.
- XML 구조 검사와 KORMARC 표시기호·내용 검사를 분리합니다.
- Dublin Core·MODS 출력은 일부 정보를 생략하는 의미 변환입니다.
- 원문 부호화를 유지한 바이트 일치는 지원 조건을 충족한 경우에만 검증합니다.

MARCXML의 XML 이름공간을 사용하지만 KORMARC를 MARC 21로 간주하지 않습니다.
동봉 XSD는 직접 작성한 구조 스키마이며 LC의 공식 XSD와 동일하지 않습니다.

## 2. 설치

Python 3.11 이상이 필요합니다. 내려받은 저장소 폴더에서 실행합니다.

```sh
python -m venv .venv
```

Mac/Linux에서는 `source .venv/bin/activate`, Windows PowerShell에서는
`.venv\Scripts\Activate.ps1`로 가상환경을 활성화합니다.

```sh
python -m pip install -r requirements-dev.lock
python -m pip install --no-deps -e .
kormarcxml --help
```

아직 PyPI에 게시된 패키지라고 주장하지 않습니다. 위 명령은 현재 저장소를
설치합니다. 개발환경이 필요 없다면 `python -m pip install .`도 가능합니다.

## 3. 예제 실행

```sh
python scripts/demo.py
kormarcxml convert examples/book.mrc --from iso2709 --to xml -o examples/converted.xml
kormarcxml validate examples/converted.xml --level 1
kormarcxml validate examples/converted.xml --level 3 -o examples/report.jsonl
kormarcxml transform examples/converted.xml --to html -o examples/catalog.html
kormarcxml convert examples/converted.xml --to iso2709 -o examples/restored.mrc
python -c "from pathlib import Path; assert Path('examples/book.mrc').read_bytes() == Path('examples/restored.mrc').read_bytes()"
```

첫 명령은 합성 시험자료를 만들고 변환·검증·표시·왕복 비교를 실제 실행합니다.
`examples/demo-result.json`에서 결과를 확인합니다. 표준 전체의 검증 결과가
아니라 예제에 대한 처리 결과입니다.

검증 수준은 1: XML 구조, 2: 표시기호·구조, 3: 확인된 내용 규칙까지입니다.
CLI의 2·3단계는 레코드별 XSD 검사도 함께 수행합니다. 1단계는 원본 XML 문서의
구조를 별도로 검사하며, 크기 제한이 적용됩니다.
오류가 없는 1단계 검사는 아무 내용도 출력하지 않습니다. 종료 코드는 성공 0,
검증 오류 1, 처리 실패 2입니다.

## 4. 여러 레코드와 문자 부호화

```sh
kormarcxml batch examples/collection.mrc --from iso2709 --to xml -o examples/collection-output.xml
kormarcxml transform examples/collection-output.xml --to html --output-dir examples/pages
kormarcxml convert examples/book-euc-kr.mrc --from iso2709 --encoding euc-kr --to xml -o examples/legacy.xml
```

`batch`는 레코드를 순차 처리합니다. 여러 레코드의 화면·메타데이터 변환은
`--output-dir`로 파일을 각각 저장합니다. 입력·출력의 `-`는 표준입력·표준출력을
뜻합니다. Windows에서 바이너리 파이프의 바이트 보존을 확인하지 못했다면
ISO 2709 결과는 파일로 저장하십시오.

Leader/09만으로 바이트 부호화를 확정할 수 없는 입력은 명시적인 부호화 지정이
필요합니다. KS X 1001은 문자집합이며 모든 레거시 파일의 바이트 표현이 곧
EUC-KR인 것은 아닙니다. 깨진 문자를 기본값으로 조용히 치환하지 않습니다.

## 5. 시험 및 주요 제한

```sh
python -m pytest -q
python scripts/benchmark.py --records 10000
```

검증 규칙은 부분 집합이며 전거·소장용 규칙, 전체 부호표, BIBFRAME/RDF,
ONIX 가져오기, 자동 교정은 아직 구현하지 않았습니다. 합성 자료만으로
실제 종합목록 운영환경의 성능·완전성을 보증하지 않습니다. 공식 원문 접근에
제약이 있었으며 직접 읽은 자료와 공식 검색 발췌 근거를 구분해 기록했습니다.

[규칙 범위](docs/validation.md), [한계](docs/limitations.md),
[LC 기능 대응표](docs/lc-parity.md), [문자 부호화](docs/encoding.md),
[향후 계획](docs/roadmap.md)을 확인하십시오. 전체 설치·품질 검사 명령과
문서 목록은 [영문 README](README.md)에 있습니다.

프로젝트 자체 코드는 MIT 라이선스입니다. 표준 원문·외부 코드·실제 서지데이터의
사용조건은 별도이며 [출처 및 라이선스](docs/provenance-license.md)를 따릅니다.

# 공통 규정 추가 검수

공식 [X00](https://librarian.nl.go.kr/kormarc/KSX6006-0/sub/X00_X30_X00_000.html), [X10](https://librarian.nl.go.kr/kormarc/KSX6006-0/sub/X00_X30_X10_000.html), [X11](https://librarian.nl.go.kr/kormarc/KSX6006-0/sub/X00_X30_X11_000.html), [X30](https://librarian.nl.go.kr/kormarc/KSX6006-0/sub/X00_X30_X30_000.html)의 해당 본문을 대조했습니다.

- 100/600/700/800의 $b는 제1지시기호 0일 때만 사용합니다. 식별기호가 없으면 이 조건은 적용하지 않습니다.
- 800/810/811/830의 $7은 존재할 때 1~2자리이며 첫 자리에 레코드유형 부호 또는 채움문자를 요구합니다. $7 자체를 필수로 만들지 않습니다.
- 연관 자료의 유형을 현재 레코드의 리더와 같아야 한다고 검사하지 않습니다.

12개 검사 템플릿은 `common-details.json`에 원문 해시와 함께 저장하고 기본 검증기에 통합했습니다. `tests/test_common_details.py`에서 정상·오류·생략·수준 구분을 시험합니다.

아직 남은 범위: $7 두 번째 자리의 전체 의미 조건, 공통 구두법·정보원 판단, $6/$8 연결 관계, 개별 필드와 공통 요약의 예외 대조. 전체 공통 규정 검수 완료를 뜻하지 않습니다.

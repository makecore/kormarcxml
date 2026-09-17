# KORMARC source review and evidence boundaries

KORMARCXML is an independent open-source framework, **not** an NLK or KS standard.
Target: **KS X 6006-0:2023**, integrated bibliographic format. Research date:2026-09-16.
The official [KORMARC entry point](https://librarian.nl.go.kr/kormarc/KSX6006-0/index.html) is the normative starting point.
The official [legacy entry page](https://librarian.nl.go.kr/kormarc/kormarc_2014/index.html) announces the KS revision dated2023-12-07.
The repository does not claim that no later amendment exists: a complete amendment audit was not obtainable.

## Evidence method

Direct website opens returned HTTP417, and a container HTTPS request timed out. Official-domain search results supplied some full page bodies and many snippets. Only statements visible in those materials are registered below. Navigation hits are inventory evidence, not evidence that all field semantics were reviewed. No secondary-site MARC21 assumptions were promoted to KORMARC rules. **This is a partial normative audit, not comprehensive certification.**

`research/verified-rules.json` records short technical facts and source URLs. It is research evidence, not an executable competing rule registry. The runtime registry documents exactly which rules are enforced. `body` means the full relevant page body was supplied through search; `excerpt` means only selected statements were accessible.

## Source inventory and coverage

| Requested area | Official source | Evidence | Findings / boundary |
|---|---|---|---|
| 설계원칙 | [info_004.html](https://librarian.nl.go.kr/kormarc/KSX6006-0/sub/info_004.html) | excerpt | 24-position leader; independent field/subfield repeatability |
| 내용표시기호 | [info_005.html](https://librarian.nl.go.kr/kormarc/KSX6006-0/sub/info_005.html) | excerpt | common008 positions and navigation |
| 리더 | [info_006.html](https://librarian.nl.go.kr/kormarc/KSX6006-0/sub/info_006.html) | excerpt | length24;09 repertoire labels |
| 디렉터리 | [info_007.html](https://librarian.nl.go.kr/kormarc/KSX6006-0/sub/info_007.html) | excerpt | 12-position entries, system generation |
| 00X | [00X_overview.html](https://librarian.nl.go.kr/kormarc/KSX6006-0/sub/00X_overview.html) | excerpt | 001/003 identity;00514;00614;00840; material-specific interpretation partial |
| 01X–09X | [01X_09X_overview.html](https://librarian.nl.go.kr/kormarc/KSX6006-0/sub/01X_09X_overview.html) | excerpt | 020 repeatability;003 refers library code table;082 researched by validator agent |
| X00–X30 | [X00_X30_overview.html](https://librarian.nl.go.kr/kormarc/KSX6006-0/sub/X00_X30_overview.html) | excerpt | shared access-point data across1XX/6XX/7XX/8XX |
| 1XX | [1XX_overview.html](https://librarian.nl.go.kr/kormarc/KSX6006-0/sub/1XX_overview.html) | excerpt | main-entry applicability depends on cataloging rules |
| 20X–24X | [20X_24X_overview.html](https://librarian.nl.go.kr/kormarc/KSX6006-0/sub/20X_24X_overview.html) | excerpt | 245NR, a/b/d/eR;245indicator2 change2022;240NR,242R,243NR |
| 250–28X | [250_28X_overview.html](https://librarian.nl.go.kr/kormarc/KSX6006-0/sub/250_28X_overview.html) | excerpt | 250R,251R,254NR,255R;263NR/discretionary |
| 3XX | [3XX_370.html](https://librarian.nl.go.kr/kormarc/KSX6006-0/sub/3XX_370.html) | body | 370 full field structure;337/353 navigation excerpts |
| 4XX | [4XX_490.html](https://librarian.nl.go.kr/kormarc/KSX6006-0/sub/4XX_490.html) | excerpt | 490R; series statements distinct from series added entries |
| 5XX | [5XX_526.html](https://librarian.nl.go.kr/kormarc/KSX6006-0/sub/5XX_526.html) | excerpt | 526R,ind1=0/8,ind2blank,aNR;500/525/540R |
| 6XX | [6XX_688.html](https://librarian.nl.go.kr/kormarc/KSX6006-0/sub/6XX_688.html) | body | 688full structure including ind2/$2 dependency |
| 70X–75X | [70X_75X_700.html](https://librarian.nl.go.kr/kormarc/KSX6006-0/sub/70X_75X_700.html) | excerpt | 700R,ind1=0/1/3;740R |
| 76X–78X | [76X_78X_772.html](https://librarian.nl.go.kr/kormarc/KSX6006-0/sub/76X_78X_772.html) | excerpt | linking entries;772$dNR,gR,hNR |
| 80X–830 | [80X_830_overview.html](https://librarian.nl.go.kr/kormarc/KSX6006-0/sub/80X_830_overview.html) | navigation | series added-entry category; detailed rules not audited |
| 841–89X | [841_89X_overview.html](https://librarian.nl.go.kr/kormarc/KSX6006-0/sub/841_89X_overview.html) | body | overview/full repeatability list and delegation to holdings standard |
| 9XX | [9XX_940.html](https://librarian.nl.go.kr/kormarc/KSX6006-0/sub/9XX_940.html) | body | 940full local field structure;949/950 partial |
| 부록A | [appendix_a.html](https://librarian.nl.go.kr/kormarc/KSX6006-0/sub/appendix_a.html) | excerpt | control-subfield relationship role; full grammars not audited |
| 부록B | [entry navigation](https://librarian.nl.go.kr/kormarc/KSX6006-0/index.html) | referenced | role/source-code tables referenced by370 and688; complete tables not retrieved |
| 부속서 부호표 | [entry navigation](https://librarian.nl.go.kr/kormarc/KSX6006-0/index.html) | navigation | publication-country/university/language/government/domestic-region/foreign-region/country tables seen in navigation; values not audited |
| 변경 이력 | [3XX_370.html](https://librarian.nl.go.kr/kormarc/KSX6006-0/sub/3XX_370.html) | partial | 370/688 added2022;245/940 filing labels revised2022; no comprehensive delta audit |
| 필수/선택·적용수준 | [6XX_688.html](https://librarian.nl.go.kr/kormarc/KSX6006-0/sub/6XX_688.html) | partial | conditional requiredness distinguished from unconditional; profile-wide mandatory inventory not verified |

## Implementation-critical differences from MARC21

* [005](https://librarian.nl.go.kr/kormarc/KSX6006-0/sub/00X_005.html) uses14digits for its timestamp. Do not import the MARC21 fractional-second16-character rule.
* [006](https://librarian.nl.go.kr/kormarc/KSX6006-0/sub/00X_006.html) covers positions00–13. Do not import the MARC21 length18.
* [245](https://librarian.nl.go.kr/kormarc/KSX6006-0/sub/20X_24X_245.html) is nonrepeatable, but$a,$b,$d,$e repeat. Responsibility is$d/$e; importing a MARC21$c-only crosswalk would miss it. The first indicator includes2. Full indicator enumeration is not inferred from examples.
* [Leader09](https://librarian.nl.go.kr/kormarc/KSX6006-0/sub/info_006.html): blank=KS X1001,a=UCS/Unicode,z=other. KS X1001 identifies a character set; it does not alone establish every byte-encoding arrangement. EUC-KR handling is a declared toolkit convention, not proof of complete legacy Korean encoding coverage. Arbitraryz must not trigger heuristic decoding.
* [940](https://librarian.nl.go.kr/kormarc/KSX6006-0/sub/9XX_940.html) is a documented local-title field. Unknown9XX must be preserved, while semantic validation requires the institution's profile.
* [841–89X](https://librarian.nl.go.kr/kormarc/KSX6006-0/sub/841_89X_overview.html) explicitly directs detailed holdings fields to KS X6006-5. Integrated bibliography transport is not equivalent to implementing the full holdings standard.

## Deferred evidence and completion gates

Before a claim of complete KS validation, review every tag/subfield/indicator, applicability level and mandatory condition against a retrievable official edition. Complete008 material-specific value tables,007 lengths and codes, all annex code tables, main-entry combinations, control-subfield grammars, and the full amendment log remain unaudited. Missing evidence must produce an uncovered-rule status or warning, never an invented prohibition. Retrieve exact official sources, record the reviewed edition/date and field-local locator, independently encode rules, and add positive and negative fixtures before enabling a new constraint.

For domestic code tables, verify the current official table and its reuse conditions before packaging values. Publication-country codes must not be substituted wholesale from MARC21 merely because some values overlap. Language codes and institution identifiers likewise need their own table provenance and update policy.

## Copyright and provenance

Official website search output displays a2023NLK copyright/all-rights-reserved footer. No clear permission to redistribute the complete standard text or annex tables was established. This repository contains independently worded technical facts, source links and synthetic examples; it does not redistribute the standard's explanatory prose, screenshots or a scraped corpus. The project's software license does not license NLK/KS material. Annex ingestion should accept a user-supplied licensed/local data file and preserve provenance and effective dates. This is a record of observed reuse status, not a legal opinion.

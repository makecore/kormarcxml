# Character encoding / 문자부호화

This is an unofficial implementation profile. The official KORMARC Leader/09
reference distinguishes blank (KS X 1001) and `a` (UCS/Unicode):
<https://librarian.nl.go.kr/kormarc/KSX6006-0/sub/info_006.html>.
A coded character repertoire is not a complete byte-serialization specification.

* Leader/09 `a`: this toolkit's default Unicode byte encoding is UTF-8.
* Blank or any other value: supply an explicit encoding. The toolkit does **not**
  silently assume EUC-KR from the reference to KS X 1001.
* Explicit supported Python codecs: `utf-8`, `euc-kr`, `cp949`, and `ascii`.
  CP949 is an opt-in operational adapter, not a claim that its additional
  characters conform to the KS X 1001 repertoire. EUC-KR likewise uses Python's
  actual codec behavior; this release does not enforce a separate repertoire table.
* A non-UTF-8 override combined with Leader/09 `a` is rejected. For intentional
  transcoding, change Leader/09 explicitly in a new record before encoding.
* Other legacy byte encodings require a future codec adapter; they are not guessed.

`decode_record` and `iter_iso2709` default to `errors="strict"`: illegal byte
sequences raise `EncodingError` with rule ID `encoding.invalid_bytes`.
`errors="warn"` and `errors="replacement"` currently both issue `UnicodeWarning`
and substitute U+FFFD. These opt-in modes are **lossy**. Their warnings are Python
warnings, not yet entries in the structured issue list. Writing supports strict
encoding only: an unrepresentable character raises `encoding.unrepresentable`.
No fallback, Unicode normalization, trimming, or silent replacement is performed.

XML output is UTF-8 XML 1.0. Characters prohibited by XML 1.0 (including U+0000)
raise `xml.character`; not all arbitrary byte-bearing MARC data can be represented.
Carriage returns in text are serialized as character references by lxml, preserving
them through XML newline normalization. Combining sequences are retained exactly;
NFC and NFD are never treated as interchangeable in the code-point test.

```python
from dataclasses import replace
from kormarcxml import decode_record, encode_record, record_to_xml

record = decode_record(raw_bytes, encoding="euc-kr")
xml_bytes = record_to_xml(record)  # XML is UTF-8; source Leader/09 is retained
unicode_record = replace(record, leader=record.leader[:9] + "a" + record.leader[10:])
utf8_marc = encode_record(unicode_record)
```

An XML declaration describes the XML serialization, while Leader/09 describes the
MARC record's character-encoding intent. These are distinct layers. XML does not
carry the explicit legacy codec override: retain it in pipeline configuration or
an external provenance manifest when preserving a legacy round trip.

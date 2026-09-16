"""Bounded ISO 2709 codec; directory offsets and lengths are byte counts."""

import codecs
import warnings
from collections.abc import Iterator
from typing import BinaryIO

from .errors import EncodingError, Issue, ParseError
from .model import ControlField, DataField, Record, Subfield

FT, RT, SD = b"\x1e", b"\x1d", b"\x1f"


def _codec(leader: str, encoding: str | None) -> str:
    if encoding is None:
        if leader[9] == "a":
            return "utf-8"
        raise EncodingError(
            "Leader/09 does not unambiguously identify a supported byte codec; specify encoding explicitly",
            "encoding.ambiguous",
            position=9,
        )
    try:
        name = codecs.lookup(encoding).name
    except LookupError as exc:
        raise EncodingError(f"Unknown encoding: {encoding}", "encoding.unknown") from exc
    if name not in {"utf-8", "euc_kr", "cp949", "ascii"}:
        raise EncodingError(
            "Supported explicit codecs: utf-8, euc-kr, cp949, ascii", "encoding.unsupported"
        )
    if leader[9] == "a" and name != "utf-8":
        raise EncodingError(
            "Leader/09 a requires UTF-8; change the leader explicitly before transcoding",
            "encoding.leader_conflict",
            position=9,
        )
    return name


def _text(data: bytes, codec: str, errors: str) -> str:
    if errors not in {"strict", "warn", "replacement"}:
        raise ValueError("errors must be strict, warn or replacement")
    try:
        return data.decode(codec, "strict")
    except UnicodeError as exc:
        if errors == "strict":
            raise EncodingError(str(exc), "encoding.invalid_bytes") from exc
        warnings.warn(
            "Invalid encoded bytes replaced with U+FFFD; round trip is lossy",
            UnicodeWarning,
            stacklevel=3,
        )
        return data.decode(codec, "replace")


def _leader(leader: str) -> None:
    if len(leader) != 24 or not leader.isascii():
        raise ParseError("Leader must contain exactly 24 ASCII characters", "iso.leader_length")
    if leader[10:12] != "22" or leader[20:24] != "4500":
        raise ParseError(
            "Unsupported ISO 2709 indicator/subfield/directory layout (expected 22 and 4500)",
            "iso.layout",
        )


def decode_record(
    data: bytes,
    encoding: str | None = None,
    *,
    errors: str = "strict",
    recover: bool = False,
    issues: list[Issue] | None = None,
) -> Record:
    if len(data) < 26:
        raise ParseError("Record shorter than leader and terminators", "iso.truncated")
    try:
        leader = data[:24].decode("ascii")
    except UnicodeError as exc:
        raise ParseError("Non-ASCII leader", "iso.leader_ascii") from exc
    _leader(leader)
    if not leader[:5].isdigit() or not leader[12:17].isdigit():
        raise ParseError("Record length and base address must be decimal digits", "iso.numeric")
    if int(leader[:5]) != len(data) or data[-1:] != RT:
        raise ParseError("Record length mismatch or missing record terminator", "iso.record_length")
    base = int(leader[12:17])
    if base < 25 or base >= len(data) or (base - 25) % 12 or data[base - 1 : base] != FT:
        raise ParseError("Invalid base address or directory terminator", "iso.directory")
    codec = _codec(leader, encoding)
    fields: list[ControlField | DataField] = []
    spans: list[tuple[int, int]] = []
    for start in range(24, base - 1, 12):
        entry = data[start : start + 12]
        if not entry.isdigit():
            raise ParseError(
                "Directory entry must contain 12 decimal digits",
                "iso.directory_entry",
                position=start,
            )
        tag = entry[:3].decode("ascii")
        length, offset = int(entry[3:7]), int(entry[7:12])
        end = base + offset + length
        if length < 1 or base + offset < base or end > len(data) - 1 or data[end - 1 : end] != FT:
            raise ParseError(
                "Field lies outside record or lacks terminator",
                "iso.field_bounds",
                tag=tag,
                position=start,
            )
        spans.append((offset, offset + length))
        raw = data[base + offset : end - 1]
        if FT in raw or RT in raw:
            raise ParseError("Embedded field/record delimiter", "iso.embedded_delimiter", tag=tag)
        if tag.startswith("00"):
            if SD in raw:
                raise ParseError(
                    "Subfield delimiter in control field", "iso.control_delimiter", tag=tag
                )
            fields.append(ControlField(tag, _text(raw, codec, errors)))
            continue
        if len(raw) < 2 or any(x < 32 or x > 126 for x in raw[:2]):
            raise ParseError("Missing or non-ASCII indicators", "iso.indicators", tag=tag)
        remainder = raw[2:]
        if remainder and not remainder.startswith(SD):
            raise ParseError(
                "Data before first subfield cannot be represented losslessly",
                "iso.unlabelled_data",
                tag=tag,
            )
        subfields = []
        for part in remainder.split(SD)[1:]:
            if not part or not 33 <= part[0] <= 126:
                raise ParseError("Missing or invalid subfield code", "iso.subfield_code", tag=tag)
            subfields.append(Subfield(chr(part[0]), _text(part[1:], codec, errors)))
        fields.append(DataField(tag, chr(raw[0]), chr(raw[1]), subfields))
    cursor = 0
    for lo, hi in sorted(spans):
        if lo != cursor:
            raise ParseError(
                "Directory fields overlap or leave unreferenced bytes", "iso.field_coverage"
            )
        cursor = hi
    if base + cursor != len(data) - 1:
        raise ParseError("Unreferenced bytes in variable fields", "iso.field_coverage")
    if spans != sorted(spans):
        issue = Issue(
            "warning",
            "iso.directory_order",
            "Directory order differs from physical field order; serialization uses directory order",
        )
        if not recover:
            raise ParseError(issue.message, issue.rule_id)
        if issues is not None:
            issues.append(issue)
        else:
            warnings.warn(issue.message, UserWarning, stacklevel=2)
    return Record(leader, fields)


def _read(stream: BinaryIO, size: int) -> bytes:
    chunks = bytearray()
    while len(chunks) < size:
        piece = stream.read(size - len(chunks))
        if not piece:
            break
        chunks.extend(piece)
    return bytes(chunks)


def iter_iso2709(
    stream: BinaryIO,
    encoding: str | None = None,
    *,
    errors: str = "strict",
    recover: bool = False,
    issues: list[Issue] | None = None,
    max_record_length: int = 99999,
) -> Iterator[Record]:
    while True:
        prefix = _read(stream, 5)
        if not prefix:
            return
        if len(prefix) != 5 or not prefix.isdigit():
            raise ParseError(
                "Missing or invalid record length prefix; stream cannot be safely resynchronized",
                "iso.framing",
            )
        size = int(prefix)
        if not 26 <= size <= max_record_length:
            raise ParseError("Record length outside configured limit", "iso.limit")
        tail = _read(stream, size - 5)
        if len(tail) != size - 5:
            raise ParseError("Truncated stream", "iso.truncated")
        yield decode_record(prefix + tail, encoding, errors=errors, recover=recover, issues=issues)


def encode_record(record: Record, encoding: str | None = None, *, errors: str = "strict") -> bytes:
    _leader(record.leader)
    if errors != "strict":
        raise ValueError("Writing supports strict encoding only; repair text explicitly")
    codec = _codec(record.leader, encoding)
    directory, payload = bytearray(), bytearray()

    def value(text: str) -> bytes:
        if any(c in text for c in "\x1d\x1e\x1f"):
            raise ParseError("Text contains an ISO 2709 delimiter", "iso.embedded_delimiter")
        try:
            return text.encode(codec, "strict")
        except UnicodeError as exc:
            raise EncodingError(str(exc), "encoding.unrepresentable") from exc

    for item in record.fields:
        if len(item.tag) != 3 or not item.tag.isascii() or not item.tag.isdigit():
            raise ParseError("Tag must contain three ASCII digits", "iso.tag")
        if isinstance(item, ControlField):
            if not item.tag.startswith("00"):
                raise ParseError("Control field tag must be 00X", "iso.field_type")
            raw = value(item.value)
        else:
            if item.tag.startswith("00"):
                raise ParseError("Data field cannot use 00X tag", "iso.field_type")
            if any(len(i) != 1 or not 32 <= ord(i) <= 126 for i in (item.ind1, item.ind2)):
                raise ParseError(
                    "Indicators must be single printable ASCII characters", "iso.indicators"
                )
            raw = (item.ind1 + item.ind2).encode("ascii")
            for sf in item.subfields:
                if len(sf.code) != 1 or not 33 <= ord(sf.code) <= 126:
                    raise ParseError(
                        "Subfield code must be one printable nonblank ASCII character",
                        "iso.subfield_code",
                    )
                raw += SD + sf.code.encode("ascii") + value(sf.value)
        raw += FT
        if len(raw) > 9999 or len(payload) > 99999:
            raise ParseError("Field length or offset exceeds ISO 2709 directory width", "iso.limit")
        directory.extend(f"{item.tag}{len(raw):04d}{len(payload):05d}".encode("ascii"))
        payload.extend(raw)
    base = 24 + len(directory) + 1
    total = base + len(payload) + 1
    if total > 99999:
        raise ParseError("Record exceeds five-digit ISO 2709 length limit", "iso.limit")
    leader = f"{total:05d}" + record.leader[5:12] + f"{base:05d}" + record.leader[17:]
    return leader.encode("ascii") + directory + FT + payload + RT

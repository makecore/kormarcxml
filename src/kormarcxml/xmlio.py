"""Secure, streaming MARCXML-compatible transport, UTF-8 output."""

from collections.abc import Iterable, Iterator
from importlib.resources import files
from typing import BinaryIO

from lxml import etree

from .errors import Issue, ParseError
from .model import ControlField, DataField, Record, Subfield

NS = "http://www.loc.gov/MARC21/slim"
Q = "{" + NS + "}"


def _element(record: Record) -> etree._Element:
    root = etree.Element(Q + "record", nsmap={None: NS})
    try:
        etree.SubElement(root, Q + "leader").text = record.leader
        for f in record.fields:
            if isinstance(f, ControlField):
                etree.SubElement(root, Q + "controlfield", tag=f.tag).text = f.value
            else:
                el = etree.SubElement(root, Q + "datafield", tag=f.tag, ind1=f.ind1, ind2=f.ind2)
                for sf in f.subfields:
                    etree.SubElement(el, Q + "subfield", code=sf.code).text = sf.value
    except (ValueError, TypeError) as exc:
        raise ParseError(
            "Data contains a character not representable in XML 1.0", "xml.character"
        ) from exc
    return root


def record_to_xml(record: Record) -> bytes:
    return etree.tostring(_element(record), encoding="UTF-8", xml_declaration=True)


def _record(el: etree._Element) -> Record:
    for node in el.iter():
        allowed = {
            Q + "record": set(),
            Q + "leader": set(),
            Q + "controlfield": {"tag"},
            Q + "datafield": {"tag", "ind1", "ind2"},
            Q + "subfield": {"code"},
        }.get(node.tag, set())
        if set(node.attrib) - allowed:
            raise ParseError("Unsupported XML attributes cannot be retained", "xml.attributes")
        if node.tag in {Q + "record", Q + "datafield"} and node.text and node.text.strip():
            raise ParseError("Unexpected mixed text content", "xml.mixed_content")
        if node.tail and node.tail.strip():
            raise ParseError("Unexpected mixed text content", "xml.mixed_content")
    leaders = el.findall(Q + "leader")
    if len(leaders) != 1 or not len(el) or el[0].tag != Q + "leader":
        raise ParseError("Record must start with exactly one leader", "xml.leader")
    if len(leaders[0]):
        raise ParseError("Leader cannot contain child elements", "xml.leader")
    fields: list[ControlField | DataField] = []
    for child in el[1:]:
        if child.tag == Q + "controlfield":
            if len(child):
                raise ParseError("Control field cannot contain child elements", "xml.controlfield")
            fields.append(ControlField(child.get("tag", ""), child.text or ""))
        elif child.tag == Q + "datafield":
            subfields = []
            for sf in child:
                if sf.tag != Q + "subfield" or len(sf):
                    raise ParseError("Unexpected element inside datafield", "xml.subfield")
                subfields.append(Subfield(sf.get("code", ""), sf.text or ""))
            fields.append(
                DataField(
                    child.get("tag", ""), child.get("ind1", ""), child.get("ind2", ""), subfields
                )
            )
        else:
            raise ParseError("Unexpected record child element", "xml.element")
    return Record(leaders[0].text or "", fields)


def iter_xml(stream: BinaryIO, *, max_record_bytes: int = 10_485_760) -> Iterator[Record]:
    """Read records with bounded buffering.

    ``max_record_bytes`` bounds each record's UTF-8 XML serialization, including
    inherited namespace declarations. Input without a complete record is bounded
    separately, with at most one 64 KiB read chunk of accounting slack.
    """
    if max_record_bytes < 1:
        raise ValueError("max_record_bytes must be positive")
    chunk_size = min(65536, max_record_bytes + 1)
    parser = etree.XMLPullParser(
        events=("start", "end"),
        resolve_entities=False,
        load_dtd=False,
        no_network=True,
        huge_tree=False,
        remove_comments=True,
        remove_pis=True,
    )
    depth, root_name, pending = 0, None, 0
    try:
        while True:
            chunk = stream.read(chunk_size)
            if not chunk:
                break
            pending += len(chunk)
            parser.feed(chunk)
            for event, el in parser.read_events():
                if event == "start":
                    depth += 1
                    if depth == 1:
                        root_name = el.tag
                        if el.getroottree().docinfo.doctype:
                            raise ParseError("DTD declarations are prohibited", "xml.dtd")
                        if root_name == Q + "collection" and el.attrib:
                            raise ParseError(
                                "Unsupported collection attributes cannot be retained",
                                "xml.attributes",
                            )
                        if root_name not in {Q + "record", Q + "collection"}:
                            raise ParseError(
                                "Expected MARCXML record or collection root", "xml.root"
                            )
                    elif depth == 2 and root_name == Q + "collection" and el.tag != Q + "record":
                        raise ParseError("Collection may contain only records", "xml.collection")
                    if depth > 5:
                        raise ParseError("Unexpected deeply nested XML", "xml.depth")
                else:
                    collection = el if el.tag == Q + "collection" else el.getparent()
                    if collection is not None and collection.tag == Q + "collection":
                        if (collection.text and collection.text.strip()) or any(
                            child.tail and child.tail.strip() for child in collection
                        ):
                            raise ParseError(
                                "Unexpected mixed text inside collection", "xml.mixed_content"
                            )
                    if el.tag == Q + "record":
                        if depth != (1 if root_name == Q + "record" else 2):
                            raise ParseError("Nested record is forbidden", "xml.nested_record")
                        if (
                            len(etree.tostring(el, encoding="UTF-8", with_tail=False))
                            > max_record_bytes
                        ):
                            raise ParseError(
                                "XML record exceeds configured byte limit", "xml.limit"
                            )
                        yield _record(el)
                        # The parser may already have buffered part of the next
                        # record from this chunk. Retain a conservative count.
                        pending = len(chunk)
                        el.clear()
                        parent = el.getparent()
                        if parent is not None:
                            while el.getprevious() is not None:
                                del parent[0]
                    depth -= 1
            if pending > max_record_bytes + chunk_size:
                raise ParseError(
                    "XML record or inter-record material exceeds configured byte limit", "xml.limit"
                )
        parser.close()
    except etree.XMLSyntaxError as exc:
        raise ParseError(str(exc), "xml.syntax") from exc


def write_xml(records: Iterable[Record], stream: BinaryIO) -> None:
    with etree.xmlfile(stream, encoding="UTF-8") as output:
        output.write_declaration()
        with output.element(Q + "collection", nsmap={None: NS}):
            for record in records:
                output.write(_element(record))


def schema_validate(source: BinaryIO | bytes | str) -> list[Issue]:
    """Validate a bounded document. Collection pipelines should validate per record."""
    import io

    if isinstance(source, str):
        source = io.BytesIO(source.encode("utf-8"))
    elif isinstance(source, bytes):
        source = io.BytesIO(source)
    data = source.read(10_485_761)
    if len(data) > 10_485_760:
        return [
            Issue(
                "error", "xml.limit", "Schema document limit is 10 MiB; validate individual records"
            )
        ]
    parser = etree.XMLParser(
        resolve_entities=False, load_dtd=False, no_network=True, huge_tree=False
    )
    try:
        root = etree.fromstring(data, parser)
        if root.getroottree().docinfo.doctype:
            return [Issue("error", "xml.dtd", "DTD declarations are prohibited")]
        schema = etree.XMLSchema(
            etree.parse(str(files("kormarcxml").joinpath("schema/kormarcxml.xsd")))
        )
        if schema.validate(root):
            return []
        return [
            Issue("error", "xml.schema", error.message, position=error.line)
            for error in schema.error_log
        ]
    except etree.XMLSyntaxError as exc:
        return [Issue("error", "xml.syntax", str(exc))]

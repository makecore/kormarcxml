"""KORMARCXML: an unofficial open-source KORMARC processing framework."""

from .errors import EncodingError, Issue, KormarcError, ParseError
from .iso2709 import decode_record, encode_record, iter_iso2709
from .model import ControlField, DataField, Record, Subfield
from .xmlio import NS, iter_xml, record_to_xml, schema_validate, write_xml

__version__ = "0.1.0"
__all__ = [
    "ControlField",
    "DataField",
    "EncodingError",
    "Issue",
    "KormarcError",
    "NS",
    "ParseError",
    "Record",
    "Subfield",
    "decode_record",
    "encode_record",
    "iter_iso2709",
    "iter_xml",
    "record_to_xml",
    "schema_validate",
    "write_xml",
]

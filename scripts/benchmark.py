"""Bounded-memory end-to-end streaming benchmark with generated on-disk records."""

import argparse
import json
import tempfile
import time
import tracemalloc
from pathlib import Path

from kormarcxml import encode_record, iter_iso2709, iter_xml, write_xml
from demo import sample


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--records", type=int, default=10000)
    p.add_argument("--output")
    args = p.parse_args()
    if args.records < 1:
        p.error("--records must be positive")
    raw = encode_record(sample())
    with tempfile.TemporaryDirectory() as directory:
        binary, xml = Path(directory) / "input.mrc", Path(directory) / "bus.xml"
        with binary.open("wb") as f:
            for _ in range(args.records):
                f.write(raw)
        tracemalloc.start()
        start = time.perf_counter()
        with binary.open("rb") as source, xml.open("wb") as output:
            write_xml(iter_iso2709(source), output)
        count = 0
        with xml.open("rb") as source:
            for record in iter_xml(source):
                assert encode_record(record) == raw
                count += 1
        elapsed = time.perf_counter() - start
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        assert count == args.records
        result = {
            "records": count,
            "seconds": round(elapsed, 3),
            "roundtrip_records_per_second": round(count / elapsed, 1),
            "peak_python_allocated_bytes": peak,
            "iso_bytes": binary.stat().st_size,
            "xml_bytes": xml.stat().st_size,
            "measurement": "Python tracemalloc excludes native lxml/libxml2 allocations; no total RSS claim",
        }
        text = json.dumps(result, indent=2) + "\n"
        if args.output:
            Path(args.output).write_text(text, encoding="utf-8")
        print(text)


if __name__ == "__main__":
    main()

"""Apply only to the reviewed, exact Home Assistant DSMR source."""

import hashlib
import json
from pathlib import Path
import re
import shutil

ROOT = Path("/usr/src/homeassistant/homeassistant/components/dsmr")


def load_expected_source_sha256(config_path: Path) -> str:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    if not isinstance(config, dict):
        raise ValueError(f"{config_path} must contain a JSON object")
    checksum = config.get("dsmr_sensor_sha256")
    if not isinstance(checksum, str) or re.fullmatch(r"[0-9a-f]{64}", checksum) is None:
        raise ValueError(
            f"{config_path}: dsmr_sensor_sha256 must be 64 lowercase hexadecimal characters"
        )
    return checksum


EXPECTED_SOURCE_SHA256 = load_expected_source_sha256(
    Path(__file__).with_name("versions.json")
)


def patched_source(source: bytes) -> str:
    if hashlib.sha256(source).hexdigest() != EXPECTED_SOURCE_SHA256:
        raise RuntimeError("Unreviewed DSMR source; refusing atomic sample patch")
    text = source.decode("utf-8")
    old = "        entities.extend(create_mbus_entities(hass, telegram, entry, dsmr_version))"
    if text.count(old) != 1:
        raise RuntimeError("DSMR acquisition hook no longer matches")
    text = text.replace(
        old,
        "        from .atomic_sensor import AtomicGridSensor\n\n"
        "        entities.append(AtomicGridSensor(entry, telegram))\n" + old,
    )
    compile(text, "dsmr/sensor.py", "exec")
    return text


def main():
    source = ROOT / "sensor.py"
    text = patched_source(source.read_bytes())
    for name in ("atomic_sample.py", "atomic_sensor.py"):
        shutil.copyfile(Path(__file__).with_name(name), ROOT / name)
    source.write_text(text, encoding="utf-8")
    print("Applied checksum-guarded DSMR atomic sample entity patch")


if __name__ == "__main__":
    main()

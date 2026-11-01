"""Apply only to the reviewed, exact Home Assistant DSMR source."""

import hashlib
from pathlib import Path
import shutil

ROOT = Path("/usr/src/homeassistant/homeassistant/components/dsmr")
EXPECTED = "b9a0c9c9ff0d82de52f9574bf41ef3b12501d387de3a37c4211e84a08e0c4b60"


def patched_source(source: bytes) -> str:
    if hashlib.sha256(source).hexdigest() != EXPECTED:
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

"""Install the approved dependency without changing HA's existing packages."""

import importlib
from importlib import metadata
import os
from pathlib import Path
import tempfile

from homeassistant.util.package import install_package
from packaging.version import Version


def main() -> None:
    if metadata.version("homeassistant") != "2026.10.4":
        raise RuntimeError("Unexpected Home Assistant base version")

    installed = {
        distribution.metadata["Name"]: distribution.version
        for distribution in metadata.distributions()
        if distribution.metadata["Name"]
    }
    # The exception applies only to this process, not the image's runtime defaults.
    os.environ.update(
        {
            "PIP_INDEX_URL": "https://pypi.org/simple",
            "PIP_EXTRA_INDEX_URL": "",
            "PIP_FIND_LINKS": "",
            "PIP_CONFIG_FILE": "/dev/null",
            "UV_DEFAULT_INDEX": "https://pypi.org/simple",
            "UV_INDEX_URL": "https://pypi.org/simple",
            "UV_INDEX": "",
            "UV_EXTRA_INDEX_URL": "",
            "UV_FIND_LINKS": "",
            "UV_NO_CONFIG": "true",
            "UV_SYSTEM_PYTHON": "true",
        }
    )
    with tempfile.TemporaryDirectory() as directory:
        constraints = Path(directory) / "constraints.txt"
        constraints.write_text(
            "\n".join(f"{name}=={version}" for name, version in sorted(installed.items()))
            + "\n",
            encoding="utf-8",
        )
        if not install_package(
            "sungrow-isolarcloud==0.20.0",
            upgrade=False,
            constraints=str(constraints),
            timeout=120,
        ):
            raise RuntimeError("Exact Sungrow dependency installation failed; no fallback")

    for name, version in installed.items():
        if metadata.version(name) != version:
            raise RuntimeError(f"Existing base package changed: {name}")
    dependency = metadata.distribution("sungrow-isolarcloud")
    if Version(dependency.version) != Version("0.20.0"):
        raise RuntimeError("Unexpected Sungrow dependency version")
    if Version(metadata.version("pymodbus")) < Version("3.6.0"):
        raise RuntimeError("Sungrow's PyModbus requirement is not satisfied")

    modules = {
        path.parts[0]
        for path in dependency.files or ()
        if len(path.parts) == 2 and path.parts[1] == "__init__.py"
    }
    if not modules:
        raise RuntimeError("No importable Sungrow package found in the distribution")
    for module in sorted(modules):
        importlib.import_module(module)
    print(
        "Verified HA 2026.10.4 and sungrow-isolarcloud 0.20.0 imports; "
        "existing base package versions unchanged. No device connection tested."
    )


if __name__ == "__main__":
    main()

import sys
from pathlib import Path

sys.path.insert(
    0,
    str(
        Path(__file__).resolve().parents[1]
        / "collections"
        / "ansible_collections"
        / "osac"
        / "service"
        / "plugins"
        / "filter"
    ),
)

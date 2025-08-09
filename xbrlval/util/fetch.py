from __future__ import annotations

import pathlib
from typing import Tuple
from urllib.parse import urlparse
import requests

_CACHE_DIR = pathlib.Path(".xbrl_cache")


def fetch_to_bytes(source: str) -> Tuple[bytes, str]:
    parsed = urlparse(source)
    if parsed.scheme in ("http", "https"):
        _CACHE_DIR.mkdir(parents=True, exist_ok=True)
        cache_path = _CACHE_DIR / (source.replace("://", "_").replace("/", "_").replace("?", "_") + ".bin")
        if cache_path.exists():
            return cache_path.read_bytes(), source
        resp = requests.get(source, timeout=60)
        resp.raise_for_status()
        data = resp.content
        cache_path.write_bytes(data)
        return data, source
    else:
        p = pathlib.Path(source)
        return p.read_bytes(), str(p.resolve().as_uri())
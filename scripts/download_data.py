"""Download the NASA Milling dataset (mill.mat) into data/.

The NASA archive is a zip that contains another zip (mill.zip) with mill.mat inside.
"""
import io
import urllib.request
import zipfile
from pathlib import Path

URL = "https://phm-datasets.s3.amazonaws.com/NASA/3.+Milling.zip"
TARGET = Path(__file__).resolve().parent.parent / "data" / "mill.mat"

if TARGET.exists():
    print("mill.mat already downloaded")
else:
    print("Downloading NASA Milling dataset (~15 MB)...")
    outer = zipfile.ZipFile(io.BytesIO(urllib.request.urlopen(URL).read()))
    inner_name = next(name for name in outer.namelist() if name.endswith("mill.zip"))
    inner = zipfile.ZipFile(io.BytesIO(outer.read(inner_name)))
    TARGET.write_bytes(inner.read("mill.mat"))
    print("Saved", TARGET)

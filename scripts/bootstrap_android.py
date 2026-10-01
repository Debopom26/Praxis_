"""Download checksum-verified build tools inside this project only."""
import hashlib
import json
from pathlib import Path
import urllib.request
import xml.etree.ElementTree as ET
import zipfile

root = Path(__file__).resolve().parents[1]
target = root / ".tools"
target.mkdir(exist_ok=True)

def download(url, path, checksum, algorithm="sha256"):
    if not path.exists():
        print("Downloading", path.name, flush=True)
        urllib.request.urlretrieve(url, path)
    h = hashlib.new(algorithm)
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024*1024), b""):
            h.update(chunk)
    if h.hexdigest() != checksum.strip():
        raise RuntimeError("Checksum mismatch: " + path.name)

def extract(archive, directory):
    with zipfile.ZipFile(archive) as z:
        for item in z.infolist():
            if not (directory / item.filename).resolve().is_relative_to(directory.resolve()):
                raise RuntimeError("Unsafe archive path")
        z.extractall(directory)

gradle_url = "https://services.gradle.org/distributions/gradle-8.11.1-bin.zip"
checksum = urllib.request.urlopen(gradle_url + ".sha256").read().decode().strip()
download(gradle_url, target / "gradle-8.11.1-bin.zip", checksum)
if not (target / "gradle-8.11.1/bin/gradle.bat").exists():
    extract(target / "gradle-8.11.1-bin.zip", target)
repo = ET.fromstring(urllib.request.urlopen("https://dl.google.com/android/repository/repository2-1.xml").read())
sdk = target / "android-sdk"
sdk.mkdir(exist_ok=True)
records = {"gradle": {"version": "8.11.1", "sha256": checksum}}
for package_name, destination in [("platforms;android-35", "platforms/android-35"), ("build-tools;35.0.0", "build-tools/35.0.0")]:
    package = next(p for p in repo if p.tag.endswith("remotePackage") and p.attrib.get("path") == package_name
                   and (package_name != "platforms;android-35" or p.findtext("display-name") == "Android SDK Platform 35"))
    archive = next(a for a in package.findall("./archives/archive") if a.findtext("host-os") in [None, "windows"])
    complete = archive.find("complete")
    url = "https://dl.google.com/android/repository/" + complete.findtext("url")
    checksum = complete.findtext("checksum")
    path = target / url.rsplit("/",1)[1]
    download(url, path, checksum, "sha1")
    location = sdk / destination
    if not location.exists():
        stage = target / ("unpack-" + destination.replace("/", "-"))
        extract(path, stage)
        children = list(stage.iterdir())
        if len(children) != 1 or not children[0].is_dir():
            raise RuntimeError("Unexpected Android archive layout")
        location.parent.mkdir(parents=True, exist_ok=True)
        children[0].rename(location)
    records[package_name] = {"url": url, "sha1": checksum}
(root / "docs/android-toolchain.json").write_text(json.dumps(records, indent=2), encoding="utf-8")
print("Project-local Android toolchain ready", flush=True)

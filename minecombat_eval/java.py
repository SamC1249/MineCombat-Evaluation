"""Locate or auto-provision a Java runtime for launching Paper.

Order of preference:
  1. ``JAVA_<version>`` env var (e.g. JAVA_25) -> ``$JAVA_25/bin/java``
  2. ``JAVA_HOME`` if it satisfies the minimum version
  3. ``java`` on PATH if it satisfies the minimum version
  4. A Temurin JRE downloaded from the Adoptium API into
     ``~/.cache/minecombat-eval/jre-<version>/`` (zero user setup)

Only the download path needs the network; everything else is offline.
"""

from __future__ import annotations

import os
import platform
import re
import shutil
import subprocess
import tarfile
import urllib.request
import zipfile
from pathlib import Path


class JavaError(RuntimeError):
    pass


def _cache_dir(version: int) -> Path:
    return Path.home() / ".cache" / "minecombat-eval" / f"jre-{version}"


def java_major(java_bin: Path) -> int | None:
    """Return the major version of a java binary, or None if it can't be read."""
    try:
        proc = subprocess.run(
            [str(java_bin), "-version"], capture_output=True, text=True, timeout=15
        )
    except (OSError, subprocess.SubprocessError):
        return None
    text = proc.stderr or proc.stdout
    m = re.search(r'version "(\d+)(?:\.(\d+))?', text)
    if not m:
        return None
    major = int(m.group(1))
    # Legacy scheme: "1.8.0" means Java 8.
    if major == 1 and m.group(2):
        return int(m.group(2))
    return major


def _bin_in(home: Path) -> Path:
    exe = "java.exe" if os.name == "nt" else "java"
    # macOS JDK/JRE bundles nest the runtime under Contents/Home.
    nested = home / "Contents" / "Home" / "bin" / exe
    if nested.is_file():
        return nested
    return home / "bin" / exe


def _candidate_from_env(version: int) -> Path | None:
    val = os.environ.get(f"JAVA_{version}")
    if val:
        return _bin_in(Path(val).expanduser())
    return None


def _existing_java(version: int) -> Path | None:
    cand = _candidate_from_env(version)
    if cand and cand.is_file() and (java_major(cand) or 0) >= version:
        return cand

    home = os.environ.get("JAVA_HOME")
    if home:
        jb = _bin_in(Path(home).expanduser())
        if jb.is_file() and (java_major(jb) or 0) >= version:
            return jb

    on_path = shutil.which("java")
    if on_path and (java_major(Path(on_path)) or 0) >= version:
        return Path(on_path)

    cached = _bin_in(_cache_dir(version))
    if cached.is_file() and (java_major(cached) or 0) >= version:
        return cached
    return None


def _adoptium_url(version: int) -> str:
    sysname = platform.system().lower()
    os_map = {"darwin": "mac", "linux": "linux", "windows": "windows"}
    if sysname not in os_map:
        raise JavaError(f"unsupported OS for auto JRE download: {sysname}")
    machine = platform.machine().lower()
    if machine in ("x86_64", "amd64"):
        arch = "x64"
    elif machine in ("arm64", "aarch64"):
        arch = "aarch64"
    else:
        raise JavaError(f"unsupported CPU arch for auto JRE download: {machine}")
    return (
        f"https://api.adoptium.net/v3/binary/latest/{version}/ga/"
        f"{os_map[sysname]}/{arch}/jre/hotspot/normal/eclipse"
    )


def _download_jre(version: int) -> Path:
    url = _adoptium_url(version)
    dest = _cache_dir(version)
    dest.mkdir(parents=True, exist_ok=True)
    is_zip = platform.system().lower() == "windows"
    archive = dest / ("jre.zip" if is_zip else "jre.tar.gz")
    print(f"Downloading Temurin JRE {version} from Adoptium …")
    try:
        with urllib.request.urlopen(url, timeout=300) as resp, archive.open("wb") as out:
            shutil.copyfileobj(resp, out)
    except OSError as e:
        raise JavaError(f"JRE download failed ({url}): {e}") from e

    # Extract, then flatten the single top-level dir Adoptium ships.
    staging = dest / ".extract"
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir()
    if is_zip:
        with zipfile.ZipFile(archive) as zf:
            zf.extractall(staging)
    else:
        with tarfile.open(archive, "r:gz") as tf:
            tf.extractall(staging)
    archive.unlink(missing_ok=True)

    tops = [p for p in staging.iterdir() if p.is_dir()]
    root = tops[0] if len(tops) == 1 else staging
    for item in root.iterdir():
        target = dest / item.name
        if target.exists():
            shutil.rmtree(target) if target.is_dir() else target.unlink()
        shutil.move(str(item), str(target))
    shutil.rmtree(staging, ignore_errors=True)

    jb = _bin_in(dest)
    if not jb.is_file():
        raise JavaError(f"extracted JRE but java binary missing under {dest}")
    if os.name != "nt":
        jb.chmod(0o755)
    return jb


def ensure_java(version: int = 25, *, allow_download: bool = True) -> Path:
    """Return a path to a java binary of at least ``version``.

    Downloads a Temurin JRE if none is found and ``allow_download`` is True.
    """
    found = _existing_java(version)
    if found:
        return found
    if not allow_download:
        raise JavaError(
            f"no Java {version}+ found; set JAVA_{version} or install a JDK {version}"
        )
    return _download_jre(version)

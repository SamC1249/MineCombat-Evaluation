"""Bootstrap a local Paper eval server (Paper JAR, plugin, world, config)."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
import zipfile
from pathlib import Path
from typing import Any


class BootstrapError(Exception):
    pass


def repo_root() -> Path:
    env = os.environ.get("MINECOMBAT_EVAL_ROOT")
    if env:
        return Path(env).resolve()
    return Path(__file__).resolve().parents[1]


def data_dir() -> Path:
    return Path(__file__).resolve().parent / "data"


def load_manifest() -> dict[str, Any]:
    packaged = data_dir() / "manifest.json"
    if packaged.is_file():
        return json.loads(packaged.read_text(encoding="utf-8"))
    root = repo_root() / "artifacts" / "manifest.json"
    if root.is_file():
        return json.loads(root.read_text(encoding="utf-8"))
    raise BootstrapError("manifest.json not found (reinstall package or clone repo)")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def download(url: str, dest: Path, *, expected_sha256: str | None = None) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    try:
        with urllib.request.urlopen(url, timeout=120) as resp, tmp.open("wb") as out:
            shutil.copyfileobj(resp, out)
    except urllib.error.URLError as e:
        raise BootstrapError(f"download failed: {url}: {e}") from e
    if expected_sha256:
        got = sha256_file(tmp)
        if got.lower() != expected_sha256.lower():
            tmp.unlink(missing_ok=True)
            raise BootstrapError(f"SHA256 mismatch for {dest.name}: expected {expected_sha256}, got {got}")
    tmp.replace(dest)


def resolve_server(server: str | None) -> Path:
    if server:
        return Path(server).expanduser().resolve()
    env = os.environ.get("SERVER")
    if env:
        return Path(env).expanduser().resolve()
    default = Path.home() / "minecraft-paper-mcbench"
    return default.resolve()


def _java_home(version: str) -> Path:
    key = f"JAVA_{version}"
    val = os.environ.get(key)
    if val:
        return Path(val).expanduser().resolve()
    raise BootstrapError(f"Set {key} in .env or environment (JDK {version} required)")


def build_plugin(*, skip: bool = False) -> Path:
    root = repo_root()
    jar_name = load_manifest().get("plugin_jar", "minecombat-evaluation-0.1.0-SNAPSHOT.jar")
    jar_path = root / "paper-plugin" / "build" / "libs" / jar_name
    if skip and jar_path.is_file():
        return jar_path

    script = root / "scripts" / "run-gradle.sh"
    if script.is_file():
        subprocess.run([str(script), "jar"], cwd=root, check=True)
    else:
        java21 = _java_home("21")
        env = os.environ.copy()
        env["JAVA_HOME"] = str(java21)
        env["PATH"] = f"{java21 / 'bin'}:{env.get('PATH', '')}"
        subprocess.run(["./gradlew", "jar"], cwd=root / "paper-plugin", env=env, check=True)

    if not jar_path.is_file():
        raise BootstrapError(f"plugin JAR missing after build: {jar_path}")
    return jar_path


def _world_zip_path(manifest: dict[str, Any]) -> Path:
    world = manifest["world"]
    zip_name = world["zip_file"]
    local = data_dir() / zip_name
    if local.is_file():
        return local
    root = repo_root() / "artifacts" / "world" / zip_name
    if root.is_file():
        return root
    cache = Path.home() / ".cache" / "minecombat-eval" / zip_name
    if cache.is_file():
        expected = world.get("sha256")
        if expected and sha256_file(cache).lower() != expected.lower():
            cache.unlink()
        else:
            return cache
    url = world.get("download_url")
    if not url:
        raise BootstrapError(f"world zip {zip_name} not found locally and no download_url in manifest")
    print(f"Downloading world {world['id']} …")
    download(url, cache, expected_sha256=world.get("sha256"))
    return cache


def install_world(server: Path, manifest: dict[str, Any], *, force: bool = False) -> None:
    world = manifest["world"]
    level = world["level_name"]
    dest = server / level
    if dest.exists() and not force:
        print(f"World already present: {dest} (use --force-world to replace)")
        return
    if dest.exists():
        shutil.rmtree(dest)
    zip_path = _world_zip_path(manifest)
    expected = world.get("sha256")
    if expected:
        got = sha256_file(zip_path)
        if got.lower() != expected.lower():
            raise BootstrapError(f"world zip SHA256 mismatch: {got} != {expected}")
    dest.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(dest)
    print(f"Installed world {world['id']} → {dest}")


def install_paper(server: Path, manifest: dict[str, Any], *, force: bool = False) -> None:
    jar = server / "paper.jar"
    if jar.is_file() and not force:
        print(f"Paper already present: {jar}")
        return
    url = manifest["paper_url"]
    print(f"Downloading Paper {manifest['paper_version']} build {manifest['paper_build']} …")
    download(url, jar)


def install_plugin(server: Path, plugin_jar: Path) -> None:
    plugins = server / "plugins"
    plugins.mkdir(parents=True, exist_ok=True)
    dest = plugins / plugin_jar.name
    shutil.copy2(plugin_jar, dest)
    print(f"Installed plugin → {dest}")


def sync_config(server: Path) -> None:
    root = repo_root()
    src = root / "paper-plugin" / "src" / "main" / "resources" / "config.yml"
    if not src.is_file():
        raise BootstrapError(f"missing config template: {src}")
    dest_dir = server / "plugins" / "MineCombat-Evaluation"
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / "config.yml"
    if dest.is_file():
        stamp = dest.with_suffix(f".yml.bak.{os.getpid()}")
        shutil.copy2(dest, stamp)
    shutil.copy2(src, dest)
    print(f"Synced config → {dest}")


def write_eula(server: Path) -> None:
    path = server / "eula.txt"
    if path.is_file():
        return
    path.write_text("eula=true\n", encoding="utf-8")
    print(f"Wrote {path}")


def write_server_properties(server: Path, manifest: dict[str, Any]) -> None:
    level = manifest["world"]["level_name"]
    path = server / "server.properties"
    lines: list[str] = []
    if path.is_file():
        lines = path.read_text(encoding="utf-8").splitlines()
    keys = {"level-name": level, "level-type": "minecraft:flat", "online-mode": "true"}
    out: dict[str, str] = {}
    seen: set[str] = set()
    for line in lines:
        if not line.strip() or line.strip().startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        k = k.strip()
        if k in keys:
            out[k] = keys[k]
            seen.add(k)
        else:
            out[k] = v
    for k, v in keys.items():
        if k not in seen:
            out[k] = v
    text = "\n".join(f"{k}={v}" for k, v in out.items()) + "\n"
    path.write_text(text, encoding="utf-8")
    print(f"Updated {path} (level-name={level})")


def bootstrap(
    *,
    server: str | None = None,
    skip_build: bool = False,
    skip_paper: bool = False,
    skip_world: bool = False,
    force_world: bool = False,
    force_paper: bool = False,
) -> Path:
    manifest = load_manifest()
    srv = resolve_server(server)
    srv.mkdir(parents=True, exist_ok=True)
    print(f"Bootstrap target: {srv}")

    if not skip_paper:
        install_paper(srv, manifest, force=force_paper)
    write_eula(srv)
    write_server_properties(srv, manifest)

    plugin_jar = build_plugin(skip=skip_build)
    install_plugin(srv, plugin_jar)
    sync_config(srv)

    if not skip_world:
        install_world(srv, manifest, force=force_world)

    print("\nDone. Start Paper (restart if already running):")
    print(f"  SERVER={srv} ./scripts/run-paper.sh")
    print("  or: minecombat-eval server start")
    print("\nJoin Minecraft localhost once, then run eval / your agent.")
    return srv


def export_world(
    *,
    source: Path | None = None,
    server: str | None = None,
) -> Path:
    """Export mcbench_flat from a live server folder; update manifest hashes."""
    manifest = load_manifest()
    level = manifest["world"]["level_name"]
    if source is None:
        srv = resolve_server(server)
        source = srv / level
    if not source.is_dir():
        raise BootstrapError(f"world folder not found: {source}")

    zip_name = manifest["world"]["zip_file"]
    out_dir = data_dir()
    out_dir.mkdir(parents=True, exist_ok=True)
    zip_path = out_dir / zip_name
    staging = out_dir / ".export-staging"
    if staging.exists():
        shutil.rmtree(staging)
    shutil.copytree(source, staging, ignore=shutil.ignore_patterns("session.lock"))
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for fp in staging.rglob("*"):
            if fp.is_file():
                zf.write(fp, fp.relative_to(staging).as_posix())
    shutil.rmtree(staging)

    digest = sha256_file(zip_path)
    size = zip_path.stat().st_size
    print(f"Exported {zip_path} ({size} bytes, sha256={digest})")

    for rel in (data_dir() / "manifest.json", repo_root() / "artifacts" / "manifest.json"):
        if not rel.is_file():
            continue
        obj = json.loads(rel.read_text(encoding="utf-8"))
        obj["world"]["sha256"] = digest
        obj["world"]["size_bytes"] = size
        rel.write_text(json.dumps(obj, indent=2) + "\n", encoding="utf-8")
        print(f"Updated {rel}")

    artifacts_world = repo_root() / "artifacts" / "world"
    artifacts_world.mkdir(parents=True, exist_ok=True)
    shutil.copy2(zip_path, artifacts_world / zip_name)
    return zip_path

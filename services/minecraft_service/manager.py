import json
import os
import shutil
import signal
import subprocess
import time
import uuid
from pathlib import Path

from .mojang import download_server_jar, list_release_versions
from .properties_util import read_properties, write_properties_preserve

MC_ROOT = Path(os.getenv("MC_ROOT", "/data/minecraft/servers"))
MC_JAVA = os.getenv("MC_JAVA", "/usr/bin/java")
MC_XMX = os.getenv("MC_DEFAULT_XMX", "2G")
INDEX_FILE = MC_ROOT / "index.json"


def _ensure_root() -> None:
    MC_ROOT.mkdir(parents=True, exist_ok=True)
    if not INDEX_FILE.exists():
        INDEX_FILE.write_text("[]", encoding="utf-8")


def _load_index() -> list[dict]:
    _ensure_root()
    return json.loads(INDEX_FILE.read_text(encoding="utf-8") or "[]")


def _save_index(items: list[dict]) -> None:
    _ensure_root()
    INDEX_FILE.write_text(
        json.dumps(items, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _server_dir(server_id: str) -> Path:
    return MC_ROOT / server_id


def _pid_file(server_id: str) -> Path:
    return _server_dir(server_id) / "server.pid"


def _is_running(server_id: str) -> bool:
    pf = _pid_file(server_id)
    if not pf.exists():
        return False
    try:
        pid = int(pf.read_text(encoding="utf-8").strip())
    except ValueError:
        return False
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def _next_port(items: list[dict], start: int = 25565) -> int:
    used: set[int] = set()
    for s in items:
        try:
            used.add(int(s.get("port", 0)))
        except (TypeError, ValueError):
            pass
    port = start
    while port in used:
        port += 1
    return port


def _wait_for_properties(server_id: str, timeout_sec: float = 120.0) -> Path:
    props = _server_dir(server_id) / "server.properties"
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        if props.exists() and props.stat().st_size > 80:
            time.sleep(1.0)  # дать MC дописать файл
            return props
        time.sleep(0.5)
    raise RuntimeError("server.properties не появился вовремя. Смотри console.log")


def list_servers() -> list[dict]:
    items = _load_index()
    for s in items:
        s["running"] = _is_running(s["id"])
        s["status"] = "running" if s["running"] else "stopped"
    return items


def get_server(server_id: str) -> dict | None:
    for s in list_servers():
        if s["id"] == server_id:
            return s
    return None


def start_server(server_id: str) -> None:
    if _is_running(server_id):
        return
    path = _server_dir(server_id)
    jar = path / "server.jar"
    if not jar.exists():
        raise RuntimeError("server.jar не найден")

    log = open(path / "console.log", "a", encoding="utf-8")  # noqa: SIM115
    try:
        proc = subprocess.Popen(
            [
                MC_JAVA,
                "-Xms512M",
                f"-Xmx{MC_XMX}",
                "-jar",
                "server.jar",
                "nogui",
            ],
            cwd=str(path),
            stdout=log,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,
            start_new_session=True,
        )
    except Exception:
        log.close()
        raise

    _pid_file(server_id).write_text(str(proc.pid), encoding="utf-8")


def stop_server(server_id: str) -> None:
    pf = _pid_file(server_id)
    if not pf.exists():
        return
    try:
        pid = int(pf.read_text(encoding="utf-8").strip())
    except ValueError:
        pf.unlink(missing_ok=True)
        return
    try:
        os.kill(pid, signal.SIGTERM)
    except OSError:
        pass
    for _ in range(30):
        try:
            os.kill(pid, 0)
        except OSError:
            break
        time.sleep(0.5)
    else:
        try:
            os.kill(pid, signal.SIGKILL)
        except OSError:
            pass
    pf.unlink(missing_ok=True)


def create_vanilla_server(version: str, name: str | None = None) -> dict:
    """
    jar + eula → старт → ждём server.properties от Minecraft → стоп.
    Свой полный properties не пишем.
    """
    _ensure_root()
    items = _load_index()
    port = _next_port(items)

    server_id = uuid.uuid4().hex[:10]
    path = _server_dir(server_id)
    path.mkdir(parents=True, exist_ok=False)

    download_server_jar(version, str(path / "server.jar"))
    (path / "eula.txt").write_text("eula=true\n", encoding="utf-8")

    meta = {
        "id": server_id,
        "name": name or f"Vanilla {version}",
        "type": "vanilla",
        "version": version,
        "port": port,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "path": str(path),
    }
    items.insert(0, meta)
    _save_index(items)

    start_server(server_id)
    try:
        props_path = _wait_for_properties(server_id, timeout_sec=120.0)
    finally:
        stop_server(server_id)

    # только port / motd, если Minecraft уже создал эти ключи
    updates: dict[str, str] = {}
    current = read_properties(props_path)
    if "server-port" in current:
        updates["server-port"] = str(port)
    if name and "motd" in current:
        updates["motd"] = name
    if updates:
        write_properties_preserve(props_path, updates)

    return meta


def delete_server(server_id: str) -> None:
    if _is_running(server_id):
        stop_server(server_id)
    path = _server_dir(server_id)
    if path.exists():
        shutil.rmtree(path)
    items = [s for s in _load_index() if s["id"] != server_id]
    _save_index(items)


def get_properties(server_id: str) -> dict[str, str]:
    return read_properties(_server_dir(server_id) / "server.properties")


def set_properties(server_id: str, updates: dict[str, str]) -> dict[str, str]:
    """Меняет только существующие ключи, набор полей не трогает."""
    path = _server_dir(server_id) / "server.properties"
    current = read_properties(path)
    clean = {k: str(v) for k, v in updates.items() if k in current}
    write_properties_preserve(path, clean)

    items = _load_index()
    after = read_properties(path)
    for s in items:
        if s["id"] != server_id:
            continue
        if "server-port" in after:
            try:
                s["port"] = int(after["server-port"])
            except ValueError:
                pass
        if after.get("motd"):
            s["name"] = after["motd"]
    _save_index(items)
    return after


def available_versions() -> list[str]:
    return [v["id"] for v in list_release_versions(40)]

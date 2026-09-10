import json
import os
import signal
import subprocess
import time
import uuid
from pathlib import Path

from .mojang import download_server_jar, list_release_versions
from .properties_util import read_properties, write_properties

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
    # процесс жив — грубая проверка
    return True


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


def create_vanilla_server(
    version: str, name: str | None = None, port: int = 25565
) -> dict:
    _ensure_root()
    server_id = uuid.uuid4().hex[:10]
    path = _server_dir(server_id)
    path.mkdir(parents=True, exist_ok=False)

    jar_path = path / "server.jar"
    download_server_jar(version, str(jar_path))

    (path / "eula.txt").write_text("eula=true\n", encoding="utf-8")

    props = {
        "motd": name or f"Minecraft {version}",
        "server-port": str(port),
        "gamemode": "survival",
        "difficulty": "normal",
        "max-players": "10",
        "online-mode": "true",
        "pvp": "true",
        "spawn-monsters": "true",
        "allow-nether": "true",
        "enable-command-block": "false",
        "view-distance": "10",
        "white-list": "false",
        "level-name": "world",
    }
    write_properties(path / "server.properties", props)

    meta = {
        "id": server_id,
        "name": name or f"Vanilla {version}",
        "type": "vanilla",
        "version": version,
        "port": port,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "path": str(path),
    }
    items = _load_index()
    items.insert(0, meta)
    _save_index(items)
    return meta


def start_server(server_id: str) -> None:
    if _is_running(server_id):
        return
    path = _server_dir(server_id)
    jar = path / "server.jar"
    if not jar.exists():
        raise RuntimeError("server.jar не найден")

    log = open(path / "console.log", "a", encoding="utf-8") # noqa: SIM115
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
    _pid_file(server_id).write_text(str(proc.pid), encoding="utf-8")
    # log специально не закрывается — им пользуется дочерний процесс


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
    # ждём до 15 сек
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


def get_properties(server_id: str) -> dict[str, str]:
    return read_properties(_server_dir(server_id) / "server.properties")


def set_properties(server_id: str, updates: dict[str, str]) -> dict[str, str]:
    path = _server_dir(server_id) / "server.properties"
    current = read_properties(path)
    for k, v in updates.items():
        current[str(k)] = str(v)
    write_properties(path, current)

    # синхронизируем port в index
    items = _load_index()
    for s in items:
        if s["id"] == server_id and "server-port" in current:
            try:
                s["port"] = int(current["server-port"])
            except ValueError:
                pass
            if "motd" in current:
                s["name"] = current["motd"] or s.get("name")
    _save_index(items)
    return current


def available_versions() -> list[str]:
    return [v["id"] for v in list_release_versions(40)]

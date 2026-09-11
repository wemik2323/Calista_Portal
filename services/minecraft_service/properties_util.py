from pathlib import Path

LABELS = {
    "motd": "MOTD",
    "server-port": "Порт",
    "gamemode": "Режим игры",
    "difficulty": "Сложность",
    "max-players": "Макс. игроков",
    "online-mode": "Online mode (лицензия)",
    "pvp": "PvP",
    "spawn-monsters": "Спавн монстров",
    "spawn-animals": "Спавн животных",
    "allow-nether": "Ад",
    "enable-command-block": "Command blocks",
    "view-distance": "Обзор",
    "simulation-distance": "Симуляция",
    "white-list": "Whitelist",
    "enforce-whitelist": "Enforce whitelist",
    "level-name": "Имя мира",
    "level-seed": "Сид",
    "level-type": "Тип мира",
    "spawn-protection": "Защита спавна",
    "hardcore": "Хардкор",
    "allow-flight": "Полёт",
}

SELECT_OPTIONS = {
    "gamemode": ["survival", "creative", "adventure", "spectator"],
    "difficulty": ["peaceful", "easy", "normal", "hard"],
}


def read_properties(path: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    if not path.exists():
        return result
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, val = line.split("=", 1)
        result[key.strip()] = val.strip()
    return result


def write_properties_preserve(path: Path, updates: dict[str, str]) -> None:
    """
    Меняет только значения уже существующих ключей.
    Комментарии, порядок строк и набор ключей сохраняются.
    Новые ключи из updates не добавляются.
    """
    if not path.exists():
        raise FileNotFoundError(str(path))

    out: list[str] = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and "=" in stripped:
            key, _old = stripped.split("=", 1)
            key = key.strip()
            if key in updates:
                out.append(f"{key}={updates[key]}")
                continue
        out.append(line)

    path.write_text("\n".join(out) + "\n", encoding="utf-8")


def infer_type(key: str, value: str) -> str:
    if key in SELECT_OPTIONS:
        return "select"
    low = value.strip().lower()
    if low in ("true", "false"):
        return "bool"
    try:
        int(value)
        return "number"
    except ValueError:
        return "text"


def schema_from_properties(props: dict[str, str]) -> list[dict]:
    fields = []
    for key in sorted(props.keys()):
        val = props[key]
        t = infer_type(key, val)
        field = {
            "key": key,
            "label": LABELS.get(key, key),
            "type": t,
            "value": val,
        }
        if t == "select":
            field["options"] = SELECT_OPTIONS[key]
        fields.append(field)
    return fields

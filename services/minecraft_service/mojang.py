import requests

MANIFEST_URL = "https://launchermeta.mojang.com/mc/game/version_manifest_v2.json"


def list_release_versions(limit: int = 40) -> list[dict]:
    r = requests.get(MANIFEST_URL, timeout=30)
    r.raise_for_status()
    data = r.json()
    out = []
    for v in data.get("versions", []):
        if v.get("type") != "release":
            continue
        out.append({"id": v["id"], "url": v["url"]})
        if len(out) >= limit:
            break
    return out


def get_server_jar_url(version_id: str) -> str:
    versions = {v["id"]: v["url"] for v in list_release_versions(200)}
    meta_url = versions.get(version_id)
    if not meta_url:
        # fallback: full manifest scan
        r = requests.get(MANIFEST_URL, timeout=30)
        r.raise_for_status()
        for v in r.json().get("versions", []):
            if v.get("id") == version_id:
                meta_url = v["url"]
                break
    if not meta_url:
        raise RuntimeError(f"Версия не найдена: {version_id}")

    r = requests.get(meta_url, timeout=30)
    r.raise_for_status()
    meta = r.json()
    url = meta.get("downloads", {}).get("server", {}).get("url")
    if not url:
        raise RuntimeError(f"Нет server.jar для {version_id}")
    return url


def download_server_jar(version_id: str, dest_path: str) -> None:
    url = get_server_jar_url(version_id)
    with requests.get(url, stream=True, timeout=120) as r:
        r.raise_for_status()
        with open(dest_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 256):
                if chunk:
                    f.write(chunk)

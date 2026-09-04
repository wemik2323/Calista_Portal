import os
import time

import requests


class QBittorrentClientError(RuntimeError):
    pass


class QBittorrentClient:
    def __init__(self):
        self.base_url = os.getenv("QBIT_URL").rstrip("/")
        self.username = os.getenv("QBIT_USERNAME")
        self.password = os.getenv("QBIT_PASSWORD")
        self.save_path = os.getenv("QBIT_SAVE_PATH", "/data/media/torrents")
        self.session = requests.Session()
        self._logged_in = False

    def login(self) -> None:
        if self._logged_in:
            return

        r = self.session.post(
            f"{self.base_url}/api/v2/auth/login",
            data={"username": self.username, "password": self.password},
            headers={"Referer": self.base_url},
            timeout=15,
        )
        if r.status_code != 200 or r.text.strip() != "Ok.":
            raise QBittorrentClientError("Не удалось войти в qBittorrent")
        self._logged_in = True

    def add_magnet(self, magnet: str) -> None:
        self.login()
        r = self.session.post(
            f"{self.base_url}/api/v2/torrents/add",
            data={
                "urls": magnet,
                "savepath": self.save_path,
                "paused": "false",
            },
            headers={"Referer": self.base_url},
            timeout=30,
        )
        if r.status_code != 200:
            raise QBittorrentClientError(f"Ошибка добавления: {r.status_code} {r.text}")

    def find_torrent_by_magnet(self, magnet: str, wait_sec: float = 3.0) -> dict | None:
        """Ждём метаданные и ищем торрент по hash из magnet."""
        self.login()
        info_hash = _hash_from_magnet(magnet)
        if not info_hash:
            return None

        deadline = time.time() + wait_sec
        while time.time() < deadline:
            r = self.session.get(
                f"{self.base_url}/api/v2/torrents/info",
                headers={"Referer": self.base_url},
                timeout=15,
            )
            if r.status_code == 200:
                for t in r.json():
                    if t.get("hash", "").lower() == info_hash.lower():
                        return t
            time.sleep(0.5)
        return None

    def list_torrents(self) -> list[dict]:
        self.login()
        r = self.session.get(
            f"{self.base_url}/api/v2/torrents/info",
            headers={"Referer": self.base_url},
            timeout=15,
        )
        if r.status_code != 200:
            raise QBittorrentClientError(f"Не удалось получить список: {r.status_code}")
        return r.json()



def _hash_from_magnet(magnet: str) -> str | None:
    # magnet:?xt=urn:btih:<hash>&...
    magnet = magnet.strip()
    key = "urn:btih:"
    low = magnet.lower()
    i = low.find(key)
    if i < 0:
        return None
    start = i + len(key)
    end = start
    while end < len(magnet) and magnet[end] not in "&":
        end += 1
    h = magnet[start:end]
    # qBittorrent обычно отдаёт hex40; base32 (32 символа) тоже бывает
    return h.lower()
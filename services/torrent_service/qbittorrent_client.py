import os
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()


class QBittorrentClientError(RuntimeError):
    pass


class QBittorrentClient:
    def __init__(self):
        self.base_url = os.getenv("QBIT_URL", "http://127.0.0.1:5001").rstrip("/")
        self.username = os.getenv("QBIT_USERNAME", "")
        self.password = os.getenv("QBIT_PASSWORD", "")
        self.save_path = os.getenv("QBIT_SAVE_PATH", "/data/media/torrents")
        self.session = requests.Session()
        self._logged_in = False

    def login(self) -> None:
        if self._logged_in:
            return

        response = self.session.post(
            f"{self.base_url}/api/v2/auth/login",
            data={
                "username": self.username,
                "password": self.password,
            },
            headers={"Referer": self.base_url},
            timeout=15,
        )

        if response.status_code != 200 or response.text.strip() != "Ok.":
            raise QBittorrentClientError("Не удалось войти в qBittorrent")

        self._logged_in = True

    def add_torrent_file(self, torrent_path: str, save_path: str | None = None) -> None:
        self.login()

        path = Path(torrent_path)
        if not path.exists():
            raise QBittorrentClientError(f"Файл не найден: {torrent_path}")

        with path.open("rb") as file:
            response = self.session.post(
                f"{self.base_url}/api/v2/torrents/add",
                files={"torrents": (path.name, file, "application/x-bittorrent")},
                data={
                    "savepath": save_path or self.save_path,
                    "paused": "false",
                },
                headers={"Referer": self.base_url},
                timeout=30,
            )

        if response.status_code != 200:
            raise QBittorrentClientError(
                f"Ошибка добавления торрента: {response.status_code} {response.text}"
            )

    def add_magnet(self, magnet_url: str, save_path: str | None = None) -> None:
        self.login()

        response = self.session.post(
            f"{self.base_url}/api/v2/torrents/add",
            data={
                "urls": magnet_url,
                "savepath": save_path or self.save_path,
                "paused": "false",
            },
            headers={"Referer": self.base_url},
            timeout=30,
        )

        if response.status_code != 200:
            raise QBittorrentClientError(
                f"Ошибка добавления magnet: {response.status_code} {response.text}"
            )

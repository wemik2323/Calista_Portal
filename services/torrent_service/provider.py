from abc import ABC, abstractmethod

from .models import TorrentResult


class TorrentProvider(ABC):
    @abstractmethod
    def search(self, query: str) -> list[TorrentResult]:
        raise NotImplementedError

    @abstractmethod
    def get_torrent(self, torrent_id: str) -> bytes:
        raise NotImplementedError

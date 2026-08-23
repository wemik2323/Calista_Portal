from dataclasses import dataclass


@dataclass
class TorrentResult:
    id: str
    title: str
    size: str
    seeds: int
    peers: int
    torrent_url: str | None = None
    magnet_url: str | None = None

from pathlib import Path
from typing import Protocol


class SFTPDownloader(Protocol):
    def download(self, remote_path: str) -> Path: ...

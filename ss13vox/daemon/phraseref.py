from pathlib import Path

class PhraseRef:
    def __init__(self, id: str, path: Path, url: str) -> None:
        self.id: str = ''
        self.path: Path = path
        self.url: str = url

    def remove(self) -> None:
        if self.path.is_file():
            self.path.unlink()

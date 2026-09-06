"""Local paths only; no authentication data in configuration."""

import os
from dataclasses import dataclass
from pathlib import Path

UESTC_ENTRY = "https://vpn.uestc.edu.cn"


@dataclass(frozen=True)
class Config:
    root: Path

    @classmethod
    def load(cls, root: str | None = None) -> "Config":
        return cls(Path(root or os.environ.get("UESTC_PAPER_HOME") or Path.cwd()).resolve())

    @property
    def runtime(self) -> Path:
        return self.root / "runtime"

    @property
    def profile(self) -> Path:
        return self.runtime / "browser-profile"

    @property
    def downloads(self) -> Path:
        if os.environ.get('UESTC_PAPER_OUTPUT'):
            return Path(os.environ['UESTC_PAPER_OUTPUT']).resolve()
        return self.root / "downloads"

    def setup(self) -> None:
        for directory in (self.runtime, self.downloads):
            directory.mkdir(parents=True, exist_ok=True)
            (directory / ".gitignore").write_text("*\n", encoding="utf-8")

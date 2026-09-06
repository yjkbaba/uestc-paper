"""Publisher adapter contract."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

from ..resolver import Metadata


@dataclass(frozen=True)
class PublisherResolution:
    status: str
    landing_url: str | None = None
    doi: str = ""
    title: str = ""


@dataclass(frozen=True)
class DownloadResult:
    status: str
    path: Path | None = None
    route: str = "IEEE browser"


class PublisherAdapter(ABC):
    @abstractmethod
    def matches(self, metadata: Metadata) -> bool: ...

    @abstractmethod
    def resolve(self, metadata: Metadata) -> PublisherResolution: ...

    @abstractmethod
    def download(self, context, resolution: PublisherResolution, destination: Path,
                 timeout: float = 300) -> DownloadResult: ...

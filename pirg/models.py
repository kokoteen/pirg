from dataclasses import dataclass
from packaging.version import Version
from typing import Optional


@dataclass
class Package:
    name: str
    version: Optional[Version] = None

    def __eq__(self, other) -> bool:
        return self.name == other.name and self.version == other.version

    def __hash__(self) -> int:
        return hash(self.name)

    def __str__(self) -> str:
        return f"{self.name}=={self.version}"

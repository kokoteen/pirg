from dataclasses import dataclass
from packaging.version import Version


@dataclass
class Package:
    name: str
    version: Version = None

    def __eq__(self, other) -> bool:
        return self.name == other.name and self.version == other.version

    def __hash__(self) -> int:
        return hash(self.name)

    def __str__(self) -> str:
        return f"{self.name}=={self.version}"

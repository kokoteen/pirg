from dataclasses import dataclass


@dataclass
class Package:
    name: str
    version: str = None

    def __eq__(self, other) -> bool:
        return self.name == other.name

    def __hash__(self) -> int:
        return hash(self.name)

    def __str__(self) -> str:
        return f"{self.name}=={self.version}"

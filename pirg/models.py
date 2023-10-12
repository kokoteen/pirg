from dataclasses import dataclass
from packaging.version import Version
from packaging.specifiers import SpecifierSet
from typing import Optional


@dataclass
class Package:
    name: str
    suffix: Optional[str] = None
    specifier: Optional[str] = None
    version: Optional[Version] = None

    def __eq__(self, other) -> bool:
        return self.name == other.name and self.version == other.version

    def __hash__(self) -> int:
        return hash(self.name)

    def __str__(self) -> str:
        string = f"{self.name}"
        string += f"[{self.suffix}]" if self.suffix else ""
        string += f"{self.specifier}" if self.specifier else "=="
        string += f"{self.version}"
        return string

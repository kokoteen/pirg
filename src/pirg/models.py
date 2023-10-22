from dataclasses import dataclass
from typing import Optional

from packaging.specifiers import SpecifierSet


@dataclass
class Package:
    name: str
    suffix: Optional[str] = None
    specifier_set: Optional[SpecifierSet] = None

    def __eq__(self, other) -> bool:
        return (
            self.name == other.name
            and self.specifier_set == other.specifier_set
            and self.suffix == other.suffix
        )

    def __hash__(self) -> int:
        return hash(self.name + str(self.suffix) + str(self.specifier_set))

    def __str__(self) -> str:
        string = f"{self.name}"
        string += f"[{self.suffix}]" if self.suffix else ""
        string += f"{str(self.specifier_set)}" if self.specifier_set else ""
        return string

from dataclasses import dataclass


@dataclass
class Package:
    name: str
    version: str = None

    def __eq__(self, other):
        return self.name == other.name

    def __hash__(self):
        return hash(self.name)

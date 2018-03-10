from abc import ABC, abstractmethod

from typing import Dict


class ModuleInterface(ABC):
    @abstractmethod
    def run(self, *args) -> None:
        raise NotImplementedError()

    @abstractmethod
    def results(self) -> None:
        raise NotImplementedError()

    @property
    @abstractmethod
    def progress(self) -> Dict[str, int]:
        pass

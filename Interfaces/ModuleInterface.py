from abc import ABC, abstractmethod


class ModuleInterface(ABC):
    @abstractmethod
    def run(self, *args) -> None:
        raise NotImplementedError()

    @abstractmethod
    def results(self) -> None:
        raise NotImplementedError()

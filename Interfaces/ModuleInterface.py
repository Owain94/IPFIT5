from abc import ABC, abstractmethod


class ModuleInterface(ABC):
    @abstractmethod
    def run(self, *args) -> None:
        """
        Run the code from a module

        :param args: args

        :return: None
        """
        raise NotImplementedError()

    @abstractmethod
    def results(self) -> None:
        """
        Save the results of a module

        :return: None
        """
        raise NotImplementedError()

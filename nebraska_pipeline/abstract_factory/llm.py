from abc import ABC, abstractmethod


class LLM(ABC):
    @abstractmethod
    def ask(self):
        raise NotImplementedError

    @abstractmethod
    def askWithImage(self):
        raise NotImplementedError

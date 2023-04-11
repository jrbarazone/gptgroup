"""Base class for memory providers."""
import abc
from config import AbstractSingleton
import openai


def get_ada_embedding(text):
    text = text.replace("\n", " ")
    return openai.Embedding.create(input=[text], model="text-embedding-ada-002")["data"][0]["embedding"]


class MemoryProviderSingleton(AbstractSingleton):
    @abc.abstractmethod
    def add(self, data, namespace="default"):
        pass

    @abc.abstractmethod
    def get(self, data, namespace="default"):
        pass

    @abc.abstractmethod
    def clear(self):
        pass

    @abc.abstractmethod
    def get_relevant(self, data, num_relevant=5, namespace="default"):
        pass

    @abc.abstractmethod
    def get_stats(self):
        pass

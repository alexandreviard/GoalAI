from abc import ABC, abstractmethod

class League(ABC):
    def __init__(self, country: str, name: str):

        self._country = country
        self._name = name
        self._fbref_url = fbref_url

    @property
    def country(self) -> str:
        return self._country

    @property
    def name(self) -> str:
        return self._name

    @property
    def fbref_url(self) -> str:
        return self._fbref_url

    @abstractmethod
    def mapping(self) -> dict:
        pass


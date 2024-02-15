from abc import ABC, abstractmethod
import pandas as pd
import os
from processing.processing import ProcessingFootball
class League(ABC):
    def __init__(self, country: str, name: str, fbref_url: str):
        self._country = country
        self._name = name
        self._fbref_url = fbref_url
        self.data = DataManager(self)
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

class DataManager:
    def __init__(self, league: League):
        self.league = league
        self._storage_folder = 'storage'

    @property
    def storage_folder(self) -> str:
        return self._storage_folder

    def get_data(self) -> pd.DataFrame:
        data = self.get_raw_data()
        processer = ProcessingFootball()
        return processer.initial_processing(data)

    def get_data_with_features(self) -> pd.DataFrame:
        data = self.get_raw_data()
        processer = ProcessingFootball()
        return processer.features_processing(data)

    def get_data_for_prediction(self):
        data = self.get_raw_data()
        processer = ProcessingFootball()
        return processer.prediction_processing(data)

    def get_data_for_future_prediction(self) -> pd.DataFrame:
        data = self.get_raw_data()
        future_data = self.get_raw_future_matches()
        processer = ProcessingFootball()
        return processer.future_prediction_processing(data, future_data)

    def get_raw_data(self) -> pd.DataFrame:
        path = os.path.join(self.storage_folder, "data", f"{self.league.name}_data.csv")
        data = pd.read_csv(path)
        data = self._mapped_data(data)
        return data

    def get_raw_future_matches(self) -> pd.DataFrame:
        path = os.path.join(self.storage_folder, "future_matches", f"{self.league.name}_future_data.csv")
        data = pd.read_csv(path)
        data = self._mapped_data(data)
        return data

    def _mapped_data(self, data) -> pd.DataFrame:
        mapping = self.league.mapping()
        data['Opponent'] = data['Opponent'].map(mapping).fillna(data['Opponent'])
        data['Team'] = data['Team'].map(mapping).fillna(data['Team'])
        return data

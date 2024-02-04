from downloader.downloader import Downloader
from processing.processing import ProcessingFootball
from leagues.league import League
import os
import pandas as pd

class DataManager:

    def __init__(self, storage_folder: str):
        self._storage_folder = storage_folder

    @property
    def storage_folder(self) -> str:
        return self._storage_folder

    def get_data(self, league:League) -> pd.DataFrame:
        data = self.get_raw_data(league)
        processer = ProcessingFootball()
        return processer.initial_processing(data)
    
    def get_data_with_features(self, league:League) -> pd.DataFrame:
        data = self.get_raw_data(league) 
        processer = ProcessingFootball()
        return processer.features_processing(data)

    def get_data_for_prediction(self, league:League):
        data = self.get_raw_data(league) 
        processer = ProcessingFootball()
        return processer.prediction_processing(data)

    def get_data_for_futur_prediction(self, league:League) -> pd.DataFrame:
        data = self.get_raw_data(league)
        futur_data = self.get_raw_futur_matches(league)
        processer = ProcessingFootball()
        return processer.futur_prediciton_processing(data, futur_data)
        
    def get_raw_data(self, league:League) -> pd.DataFrame:
        path = os.path.join(self.storage_folder, "data", f"{league.name}_data.csv")
        data = pd.read_csv(path)
        data = self._mapped_data(data, league)
        return data

    def get_raw_futur_matches(self, league:League) -> pd.DataFrame:
        path = os.path.join(self.storage_folder, "futur_matches", f"{league.name}_futur_data.csv")
        data = pd.read_csv(path)
        data = self._mapped_data(data, league)
        return data

    def _mapped_data(self, data, league:League) -> pd.DataFrame:
        mapping = league.mapping()
        data['Opponent'] = data['Opponent'].map(mapping).fillna(data['Opponent'])
        data['Team'] = data['Team'].map(mapping).fillna(data['Team'])
        return data
        


#permet de lire ou non un fichier
#premet de vérifier si le fichier existe deja
#aide à la création de ligue
#scrape ou update en fonction d'une league

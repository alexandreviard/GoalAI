import pandas as pd
import json
import os
import numpy as np
import datetime
import time
import requests
from bs4 import BeautifulSoup
from PIL import Image
import io
from processing_data import *

class GetData:

    def __init__(self):

        self.data_folder = "Database"
        self.logos_folder = "Logos"
        self.futur_data_folder = "Futur_data"
        
    def data(self, league):
        data = self._raw_data(league)
        return ProcessingFootball().initial_processing(data)

    def data_with_features(self, league):
        data = self._raw_data(league) 
        return ProcessingFootball().features_processing(data)

    def data_for_prediction(self, league):
        data = self._raw_data(league) 
        return ProcessingFootball().prediction_processing(data)

    def data_for_futur_prediction(self, league):
        data = self._raw_data(league)
        futur_data = self._raw_futur_data(league)
        return ProcessingFootball().futur_prediciton_processing(data, futur_data)
        
    def _raw_data(self, league):
        path = os.path.join(self.data_folder, f"{league}_data.csv")
        data = pd.read_csv(path)
        data = self._mapped_data(data, league)
        return data

    def _raw_futur_data(self, league):
        path = os.path.join(self.futur_data_folder, f"{league}_futur_data.csv")
        data = pd.read_csv(path)
        data = self._mapped_data(data, league)
        return data

    def _mapped_data(self, data, league):
        with open('mapping_team.json', 'r', encoding='utf-8') as file:
            mappings = json.load(file)
        mapping = mappings.get(league, {})
        data['Opponent'] = data['Opponent'].map(mapping).fillna(data['Opponent'])
        data['Team'] = data['Team'].map(mapping).fillna(data['Team'])
        return data
    
    """
    def _read_raw_all_data(self):

        list_data = []
        for fichier in os.listdir(self.data_folder):
            if fichier.endswith('.csv'):
                path = os.path.join(self.data_folder, fichier)
                data = _read_raw_data()
                list_data.append(data)
        
        return pd.concat(list_data, ignore_index=True)
    """








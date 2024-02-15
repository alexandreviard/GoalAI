from abc import abstractmethod, ABC
import pandas as pd
from leagues.league import League

class BaseModel(ABC):
    @abstractmethod
    def train(self, league : League()) -> pd.DataFrame:
        pass
    def predict(self, new_data):
        pass
    def save_results(self, predictions):
        pass

class CatBoost(BaseModel):
    def train(self, league : League()) -> pd.DataFrame:



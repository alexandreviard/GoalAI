from leagues import *
from leagues.league import League
from downloader.downloader import Downloader
import pandas as pd
import json
import os
import numpy as np
import datetime
import time

from PIL import Image
import io

from datamanager import DataManager
from processing.processing import ProcessingFootball


b = Downloader()

c = DataManager('storage')
a = c.get_data_for_futur_prediction(Eredivisie())
b.scrape_or_update(PremierLeague())
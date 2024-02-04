class DataRepository:
    def __init__(self):
        self.headers = {'User-Agent': 'Mozilla/5.0'}
        self.last_request_time = None
        self.request_interval = 3
        self.max_seasons = 6
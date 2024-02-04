from leagues.league import League

class SerieA(League):
    def __init__(self):
        super().__init__(
            country='Italia',
            name='Serie A',
            fbref_url='https://fbref.com/en/comps/13/Serie-A-Stats',
        )
    
    def mapping(self):
        return {
            "Internazionale": "Inter"
        }

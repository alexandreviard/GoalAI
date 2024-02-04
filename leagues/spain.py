from leagues.league import League

class LaLiga(League):
    def __init__(self):
        super().__init__(
            country='Spain',
            name='La Liga',
            fbref_url='https://fbref.com/en/comps/13/La-Liga-Stats',
        )
    
    def mapping(self):
        return {
            "Alaves": "Alavés",
            "Almeria": "Almería",
            "Atletico Madrid": "Atlético Madrid",
            "Cadiz": "Cádiz",
            "Leganes": "Leganés",
            "Real Betis": "Betis"
        }

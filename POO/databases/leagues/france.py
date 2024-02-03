from databases.leagues.league import League

class Ligue1(League):
    def __init__(self):
        super().__init__(
            country='France',
            name='Ligue 1',
            fbref_url='https://fbref.com/en/comps/13/Ligue-1-Stats',
        )

    def mapping(self):
        return {
            "Nimes": "Nîmes",
            "Paris S-G": "Paris Saint-Germain",
            "Saint Etienne": "Saint-Étienne"
        }



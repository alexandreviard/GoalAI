
from leagues.league import League
class PremierLeague(League):
    def __init__(self):
        super().__init__(
            country='England',
            name='Premier League',
            fbref_url='https://fbref.com/en/comps/13/Premier-League-Stats',
        )

    def mapping(self):
        return {
            "Brighton and Hove Albion": "Brighton",
            "Huddersfield Town": "Huddersfield",
            "Manchester United": "Manchester Utd",
            "Newcastle United": "Newcastle Utd",
            "Nottingham Forest": "Nott'ham Forest",
            "Sheffield United": "Sheffield Utd",
            "Tottenham Hotspur": "Tottenham",
            "West Bromwich Albion": "West Brom",
            "West Ham United": "West Ham",
            "Wolverhampton Wanderers": "Wolves"
        }

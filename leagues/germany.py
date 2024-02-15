from leagues.league import League

class Bundesliga(League):
    def __init__(self):
        super().__init__(
            country='Germany',
            name='Bundesliga',
            fbref_url='https://fbref.com/en/comps/13/Bundesliga-Stats',
        )

    def mapping(self):
        return {
            "Bayer Leverkusen": "Leverkusen",
            "Dusseldorf": "Düsseldorf",
            "Eintracht Frankfurt": "Eint Frankfurt",
            "Greuther Furth": "Greuther Fürth",
            "Koln": "Köln",
            "Monchengladbach": "M'Gladbach",
            "Nurnberg": "Nürnberg"
        }


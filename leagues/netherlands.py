from leagues.league import League

class Eredivisie(League):
    def __init__(self):
        super().__init__(
            country='Netherlands',
            name='Eredivisie',
            fbref_url='https://fbref.com/en/comps/13/Eredivisie-Stats',
        )

    def mapping(self) -> dict:
        return {
            "Go Ahead Eagles": "Go Ahead Eag",
            "Sparta Rotterdam": "Sparta R'dam",
            "VVV Venlo": "VVV-Venlo"
        }



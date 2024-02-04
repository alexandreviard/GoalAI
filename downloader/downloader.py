from leagues.league import League
import pandas as pd
import requests
from bs4 import BeautifulSoup
import datetime
import time

class Downloader:

    def __init__(self):
        self.headers = {'User-Agent': 'Mozilla/5.0'}
        self.last_request_time = None
        self.request_interval = 3
        self.max_seasons = 6


    def all_data(self, league: League) -> pd.DataFrame:
        all_seasons_data = []
        
        for saison in range(self.max_seasons):
            teams_urls = self._fetch_team_urls(league.fbref_url)

            for team_url in teams_urls:
                team_data = self._scrape_team_data(team_url)
                team_data = self._scrape_detailed_stats(team_data, requests.get(team_url, headers=self.headers).text)
                all_seasons_data.append(team_data)

        return pd.concat(all_seasons_data, ignore_index=True)

    def latest_data_and_futur_matches(self, league: League) -> (pd.DataFrame, pd.DataFrame):

        futur_matches = []
        all_data = []
        teams_urls = self._fetch_team_urls(league.fbref_url)

        for team_url in teams_urls:
            team_data = self.scrape_team_data(team_url)
            futur_matches.append(team_data)
            team_data = self.scrape_detailed_stats(team_data, requests.get(team_url, headers=self.headers).text)
            all_data.append(team_data)

        return pd.concat(all_seasons_data, ignore_index=True), pd.concat(futur_matches, ignore_index=True)



    def _fetch_team_urls(self, league_url: str) -> list:
        self._rate_limit()
        response = requests.get(league_url, headers=self.headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        teams_urls = ["https://fbref.com" + equipe.get("href")
                    for equipe in soup.select("table.stats_table")[0].find_all("a")
                    if "squads" in equipe.get("href", "")]
        return teams_urls

    def _scrape_team_data(self, team_url: str) -> pd.DataFrame:
        self._rate_limit()
        team_response = requests.get(team_url, headers=self.headers)

        try:
            team_data = pd.read_html(team_response.text, match="Scores")[0]
        except ValueError as e:
            print(f"No tables found with this URL: {team_url} - Erreur: {e}")
            return pd.DataFrame()

        team_name = team_url.split("/")[-1].replace("-Stats", "").replace("-", " ")
        team_data["Team"] = team_name

        #self.scrape_and_save_logo(team_url, team_name)
        return team_data

    def _scrape_detailed_stats(self, team_data: pd.DataFrame, team_response_text: str) -> pd.DataFrame:
        url_stats = {
            f"https://fbref.com{a.get('href')}"
            for a in BeautifulSoup(team_response_text, 'html.parser').find_all("a")
            if "matchlogs/all_comps" in a.get('href', '') and
            any(substring in a.get('href', '') for substring in ["passing/", "shooting", "possession/", "defense/", "keeper"])
        }

        for stats_url in url_stats:
            self._rate_limit()
            stats_response = requests.get(stats_url, headers=self.headers)
            try:
                detailed_stats = pd.read_html(stats_response.text)[0]
            except ValueError as e:
                print(f"No tables found with this URL: {stats_url} - Erreur: {e}")
                return pd.DataFrame()

            if detailed_stats.columns.nlevels > 1:
                detailed_stats.columns = [f"{col}_{branch}"
                                        if "For" not in col and "Unnamed:" not in col
                                        else f"{branch}"
                                        for col, branch in detailed_stats.columns]

            columns_to_drop = ["Time", "Comp", "Round", "Day", "Venue", "Result", "GF", "GA", "Opponent", "Poss"] + [col for col in detailed_stats.columns if 'Report' in col]
            columns_to_drop = [col for col in columns_to_drop if col in detailed_stats.columns]

            detailed_stats.drop(columns_to_drop, axis=1, inplace=True)

            team_data = team_data.merge(detailed_stats, on="Date", how='left')

        return team_data

        
    def _rate_limit(self):
        if self.last_request_time is not None:
            elapsed_time = time.time() - self.last_request_time
            if elapsed_time < self.request_interval:
                time.sleep(self.request_interval - elapsed_time)
        self.last_request_time = time.time()

    
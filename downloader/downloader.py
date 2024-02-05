from leagues.league import League
import pandas as pd
import requests
from bs4 import BeautifulSoup
import datetime
import time
import os

class Downloader:

    def __init__(self):
        self.headers = {'User-Agent': 'Mozilla/5.0'}
        self.last_request_time = None
        self.request_interval = 3
        self.max_seasons = 6


    def scrape_or_update(self, league: League) -> pd.DataFrame:

        csv_file_path = os.path.join('storage/data', f"{league.name}_data.csv")

        if os.path.exists(csv_file_path):
            self.update_data(league)

        else:
            data = self.all_data(league)
            self.save_data(data, csv_file_path)

    def update_data(self, league: League) -> pd.DataFrame:

        path_data = os.path.join('storage/data', f"{league.name}_data.csv")
        path_futur_matches = os.path.join('storage/futur_matches', f"{league.name}_futur_data.csv")
        data = pd.read_csv(path_data)
        futur_matches = pd.read_csv(path_futur_matches)
        now = datetime.datetime.now()

        first_futur_match = pd.to_datetime((futur_matches['Date'] + ' ' + futur_matches['Time']).min())

        if first_futur_match < now + datetime.timedelta(hours = 2):
            scrapping = self.latest_data_and_futur_matches(league)
            data = pd.concat([data, scrapping[0].copy()])
            data.drop_duplicates(subset=['Date', 'Team', 'Opponent'], inplace=True)
            data.to_csv(path_data)

            futur_matches = self._futur_matches_process(scrapping[1].copy())
            self.save_data(futur_matches, path_futur_matches)

        else:
            print("No need to update")
            return

    def all_data(self, league: League) -> pd.DataFrame:
        all_seasons_data = []
        
        for saison in range(self.max_seasons):
            teams_urls = self._fetch_team_urls(league.fbref_url)

            for team_url in teams_urls:
                self.scrape_and_save_logo(team_url, league.name)
                team_data = self._scrape_team_data(team_url)
                team_data = self._scrape_detailed_stats(team_data, requests.get(team_url, headers=self.headers).text)
                team_data = team_data[team_data['Comp'] == league.name]
                all_seasons_data.append(team_data)

        return pd.concat(all_seasons_data, ignore_index=True)


    def latest_data_and_futur_matches(self, league: League) -> (pd.DataFrame, pd.DataFrame):

        futur_matches = []
        all_data = []
        teams_urls = self._fetch_team_urls(league.fbref_url)

        for team_url in teams_urls:
            team_data = self._scrape_team_data(team_url)
            futur_matches.append(team_data[team_data['Comp']==league.name])
            team_data = self._scrape_detailed_stats(team_data, requests.get(team_url, headers=self.headers).text)
            team_data = team_data[team_data['Comp'] == league.name]
            all_data.append(team_data)

        return pd.concat(all_seasons_data, ignore_index=True), pd.concat(futur_matches, ignore_index=True)

    def save_data(self, data, file_path):
        data.to_csv(file_path, index=False)

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

    
    def _futur_matches_process(self, futur_matches, league:League) -> pd.DataFrame:

        futur_matches.dropna(subset=["Date", "Time", "Round"], inplace=True)
        futur_matches['DateTime'] = pd.to_datetime((futur_matches['Date'] + ' ' + futur_matches['Time']))
        futur_matches = futur_matches[futur_matches["Comp"] == league.name]
        futur_matches = futur_matches[futur_matches['DateTime'] >= datetime.datetime.now()].sort_values(by="DateTime")
        
        ten_days = datetime.timedelta(days=10) + first_date
        futur_matches = futur_matches[futur_matches['DateTime'] <= ten_days]

        return futur_matches

    def scrape_and_save_logo(self, team_url, team_name):

            file_path = os.path.join(self.logos_folder, file_name + '.png')
            if os.path.exists(file_path):
                print(f"Le logo existe déjà à {file_path}")
                return

            try:
                self.rate_limit()
                response = requests.get(page_url, headers=self.headers)
                soup = BeautifulSoup(response.text, 'html.parser')
                logo_img = soup.find('img', {'class': 'teamlogo'})

                if logo_img and logo_img.get('src'):
                    logo_url = logo_img['src']
                    self.rate_limit()
                    img_response = requests.get(logo_url)

                    if img_response.status_code == 200:
                        image = Image.open(io.BytesIO(img_response.content))
                        file_path = os.path.join(self.logos_folder, file_name)
                        if not file_path.endswith('.png'):
                            file_path += '.png'
                        image.save(file_path, 'PNG')
                        print(f"Logo saved at {file_path}")
                    else:
                        print("Error during logo download")
                else:
                    print("Logo not found")
            except Exception as e:
                print(f"An error occurred: {e}")

import pandas as pd
import json
import os
import numpy as np
import datetime
import time
import requests
from bs4 import BeautifulSoup
from PIL import Image
import io

class FootballDataScraper:

    def __init__(self, config_file):
        
        self.config_file = config_file
        self.headers = {'User-Agent': 'Mozilla/5.0'}
        self.championnats = self.load_configs()
        self.data_folder = "Database"
        self.logos_folder = "Logos"
        self.futur_data_folder = "Futur_data"
        self.last_request_time = None
        self.request_interval = 3  # secondes
        self.max_seasons = 6

    def load_configs(self):
        # loading config of championship containing which championship are used and their urls
        return pd.read_csv(self.config_file)

    def scrape_or_update(self):
        all_data = {}
        for _, config in self.championnats.iterrows():
            championnat = config['Championnat']
            url = config['URL']
            csv_file_path = os.path.join(self.data_folder, f"{championnat}_data.csv")

            if os.path.exists(csv_file_path):
                data = pd.read_csv(csv_file_path)
                last_update = pd.to_datetime((data['Date'] + ' ' + data['Time']).max())

                if datetime.datetime.now() > last_update + datetime.timedelta(hours = 2):
                    updated_data = self.update_data(url, data)
                    data_updated = updated_data[0].copy()
                    all_data[championnat] = data_updated[data_updated["Comp"]==championnat]
                    futur_data = self.save_futur_data(updated_data[1], championnat)
                    self.save_data(futur_data, os.path.join(self.futur_data_folder, f"{championnat}_futur_data.csv"))
                    
            else:
                data = self.scrape_data(url)
                all_data[championnat] = data[data["Comp"]==championnat]

            self.save_data(all_data[championnat], csv_file_path)
        return all_data

    def scrape_data(self, url):
        
        all_seasons_data = []

        for saison in range(self.max_seasons):

            self.rate_limit()

            response = requests.get(url, headers=self.headers)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            teams_urls = ["https://fbref.com" + equipe.get("href") 
                        for equipe in soup.select("table.stats_table")[0].find_all("a") 
                        if "squads" in equipe.get("href", "")]

            url = f"https://fbref.com{soup.find('a', class_='button2 prev').get('href')}"

            for team_url in teams_urls:

                self.rate_limit()
                team_response = requests.get(team_url, headers=self.headers)
                try:
                    team_data = pd.read_html(team_response.text, match="Scores")[0]
                except ValueError as e:
                    # Gestion de l'exception si aucune table n'est trouvée
                    print(f"Aucune table trouvée dans {team_url} - Erreur: {e}")
                    continue  # Passe à l'itération suivante de la boucle

                team_name = team_url.split("/")[-1].replace("-Stats", "").replace("-", " ")
                team_data["Team"] = team_name

                self.scrape_and_save_logo(team_url, team_name)

                # Récupération des URLs pour les statistiques détaillées
                url_stats = {
                    f"https://fbref.com{a.get('href')}" 
                    for a in BeautifulSoup(team_response.text, 'html.parser').find_all("a") 
                    if "matchlogs/all_comps" in a.get('href', '') and 
                    any(substring in a.get('href', '') for substring in ["passing/", "shooting", "possession/", "defense/", "keeper"])
                }

                # Traitement des statistiques détaillées
                for stats_url in url_stats:

                    self.rate_limit()

                    stats_response = requests.get(stats_url, headers=self.headers)

                    try:
                        detailed_stats = pd.read_html(stats_response.text)[0]
                    except ValueError as e:
                        print(f"Aucune table trouvée dans {stats_url} - Erreur: {e}")
                        continue  # Passe à l'itération suivante de la boucle

                    # Nettoyage des colonnes du DataFrame
                    if detailed_stats.columns.nlevels > 1:
                        detailed_stats.columns = [f"{col}_{branch}" 
                                                if "For" not in col and "Unnamed:" not in col 
                                                else f"{branch}" 
                                                for col, branch in detailed_stats.columns]

                    columns_to_drop = ["Time", "Comp", "Round", "Day", "Venue", "Result", "GF", "GA", "Opponent", "Poss"] + [col for col in detailed_stats.columns if 'Report' in col]
                    columns_to_drop = [col for col in columns_to_drop if col in detailed_stats.columns]

                    detailed_stats.drop(columns_to_drop, axis=1, inplace=True)

                    team_data = team_data.merge(detailed_stats, on="Date")

                # Ajout des données de l'équipe au résultat global
                all_seasons_data.append(team_data)

        return pd.concat(all_seasons_data, ignore_index=True)

    def update_data(self, url, data):

        futur_data = []
        all_data = []
        response = requests.get(url, headers=self.headers)
        soup = BeautifulSoup(response.text, 'html.parser')

        teams_urls = ["https://fbref.com" + equipe.get("href") 
                    for equipe in soup.select("table.stats_table")[0].find_all("a") 
                    if "squads" in equipe.get("href", "")]

        # Traitement similaire à scrape_ligue1_data() pour chaque équipe
        for team_url in teams_urls:

            self.rate_limit()

            team_response = requests.get(team_url, headers=self.headers)
            try:
                team_data = pd.read_html(team_response.text, match="Scores")[0]
            except ValueError as e:
                # Gestion de l'exception si aucune table n'est trouvée
                print(f"Aucune table trouvée dans {team_url} - Erreur: {e}")
                continue  # Passe à l'itération suivante de la boucle

            team_name = team_url.split("/")[-1].replace("-Stats", "").replace("-", " ")
            team_data["Team"] = team_name

            futur_data.append(team_data)


            # Récupération des URLs pour les statistiques détaillées
            url_stats = {
                f"https://fbref.com{a.get('href')}" 
                for a in BeautifulSoup(team_response.text, 'html.parser').find_all("a") 
                if "matchlogs/all_comps" in a.get('href', '') and 
                any(substring in a.get('href', '') for substring in ["passing/", "shooting", "possession/", "defense/", "keeper"])
            }

            for stats_url in url_stats:

                self.rate_limit()

                stats_response = requests.get(stats_url, headers=self.headers)
                
                try:
                    detailed_stats = pd.read_html(stats_response.text)[0]
                except ValueError as e:
                    print(f"Aucune table trouvée dans {stats_url} - Erreur: {e}")
                    continue  # Passe à l'itération suivante de la boucle


                # Nettoyage des colonnes du DataFrame
                if detailed_stats.columns.nlevels > 1:
                    detailed_stats.columns = [f"{col}_{branch}" 
                                            if "For" not in col and "Unnamed:" not in col 
                                            else f"{branch}" 
                                            for col, branch in detailed_stats.columns]

                columns_to_drop = ["Time", "Comp", "Round", "Day", "Venue", "Result", "GF", "GA", "Opponent", "Poss"] + [col for col in detailed_stats.columns if 'Report' in col]
                columns_to_drop = [col for col in columns_to_drop if col in detailed_stats.columns]

                detailed_stats.drop(columns_to_drop, axis=1, inplace=True)

                team_data = team_data.merge(detailed_stats, on="Date")

            # Ajout des données de l'équipe au résultat global
            all_data.append(team_data)

        new_data = pd.concat(all_data, ignore_index=True)

        # Concaténation de la base initiale et de la base nouvelle
        concatenated_df = pd.concat([data, new_data])
        
        # Suppression des doublons basée sur les colonnes "Date", "Team" et "Opponent"
        concatenated_df = concatenated_df.drop_duplicates(subset=['Date', 'Team', 'Opponent'])
            
        return concatenated_df.reset_index(drop=True), pd.concat(futur_data, ignore_index=True)

    def save_data(self, data, file_path):
        # Enregistrer les données dans un fichier CSV
        data.to_csv(file_path, index=False)

    def rate_limit(self):
        if self.last_request_time is not None:
            elapsed_time = time.time() - self.last_request_time
            if elapsed_time < self.request_interval:
                time.sleep(self.request_interval - elapsed_time)
        self.last_request_time = time.time()

    def access_data(self, championnat):
        csv_file_path = os.path.join(self.data_folder, f"{championnat}_data.csv")
        
        if os.path.exists(csv_file_path):
            data = pd.read_csv(csv_file_path)
            return data
        else:
            print(f"Les données pour le championnat '{championnat}' n'existent pas.")

    def scrape_and_save_logo(self, page_url, file_name):

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
                    # Convertir l'image en PNG
                    image = Image.open(io.BytesIO(img_response.content))
                    file_path = os.path.join(self.logos_folder, file_name)
                    if not file_path.endswith('.png'):
                        file_path += '.png'
                    image.save(file_path, 'PNG')
                    print(f"Logo sauvegardé en PNG à {file_path}")
                else:
                    print("Erreur lors du téléchargement de l'image")
            else:
                print("Logo non trouvé sur la page")

        except Exception as e:
            print(f"Une erreur s'est produite : {e}")

    def save_futur_data(self, data, championnat):

        """
        À partir du scrapping on récupère un DataFrame qui contient les futurs journées, il faut le mettre en forme.
        args: DataFrame, le mapping ligue1
        """

        # Supprimer les lignes où les colonnes 'Date', 'Time' et 'Round' sont manquantes.
        data.dropna(subset=["Date", "Time", "Round"], inplace=True)
        data['DateTime'] = pd.to_datetime((data['Date'] + ' ' + data['Time']))
        data = data[data["Comp"] == championnat]

        data = data[data['DateTime'] >= datetime.datetime.now()].sort_values(by="DateTime")


        if data.empty != True:
                first_date = data['DateTime'].iloc[0]
        else:
            return None
        
        ten_days = datetime.timedelta(days=10) + first_date

        # Filtrer pour garder seulement les matchs programmés dans les 10 jours suivant la 'premiere_date_proche'.
        data = data[data['DateTime'] <= ten_days]

        if data.empty == True:
            return None

        else:# Retourner le DataFrame s'il n'est pas vide, sinon retourner None.
            csv_file_path = os.path.join(self.futur_data_folder, f"{championnat}_futur_data.csv")
            if os.path.exists(csv_file_path):
                futur_data = pd.read_csv(csv_file_path)
                last_update = pd.to_datetime((futur_data['Date'] + ' ' + futur_data['Time'])).max()
                if last_update == pd.to_datetime((data['Date'] + ' ' + data['Time'])).max():
                    return futur_data
                else:
                    return pd.concat([futur_data, data]).drop_duplicates(subset=["Team", "Opponent", "Date"])
            else:
                return data


    

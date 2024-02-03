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


class ProcessingFootball:

    def __init__(self):

        self.list_columns = [
            "Total Shots", "Shots on Target", "Shots on Target %", "Goals per Shot", "Total Touches", 
            "Touches in Defensive Penalty Area", "Touches in Defensive Third", "Touches in Midfield Third", 
            "Touches in Attacking Third", "Touches in Attacking Penalty Area", "Dribbles Attempted", 
            "Successful Dribbles", "Successful Dribble %", "Total Carries", "Total Carry Distance", 
            "Progressive Carry Distance", "Progressive Carries", "Carries into Final Third", 
            "Carries into Penalty Area", "Tackles", "Tackles Won", "Tackles in Defensive Third", 
            "Tackles in Midfield Third", "Tackles in Attacking Third", "Dribblers Tackled", 
            "Total Dribbles Against", "Defensive Dribblers Win %", "Interceptions", "Errors Leading to Goal", 
            "Key Passes", "Passes Completed", "Passes Attempted", "Passes into Final Third", 
            "Progressive Passes", "Shots on Target Against", "Keeper Saves", "Keeper Save Percentage"]
        self.foundations_columns = ["DateTime", "Comp", "Season", "Round", "Day", "Venue", "Result", "GF", "GA", "Opponent", "xG", "xGA", "Poss", "Attendance", "Captain", "Formation", "Referee", "Match Report", "Notes", "Team", "Minus 1.5 Goals", "Minus 2.5 Goals", "Minus 3.5 Goals"]


    def initial_processing(self, data): 
        data = self._prepare_basic_columns(data)
        data = self._rename_and_drop_columns(data)
        data = self._calculate_cumulatives_features(data)
        data = self._calculate_ranking(data)
        data = self._features_bookmaker_creation(data)
        return data

    def features_processing(self, data):
        data = self.initial_processing(data)
        data = self.calculate_features_for_model(data)
        return data


    def prediction_processing(self, data):
        data = self.features_processing(data)
        data = self._keep_columns_for_model(data)
        data = self._merge_2_rows_in_one(data)
        return data

    def futur_prediciton_processing(self,data, data_next_match):
        data = self.initial_processing(data)
        data_next_match = self._prepare_basic_columns(data_next_match)
        glob_data = pd.concat([data, data_next_match], sort=False).reset_index(drop=True)
        glob_data = self.calculate_features_for_model(glob_data)
        #glob_data.dropna(subset=['Total Shots_5_Last_Matches_Average'], inplace=True)
        glob_data = self._keep_columns_for_model(glob_data)
        glob_data = self._merge_2_rows_in_one(glob_data)
        return glob_data

    def calculate_features_for_model(self, data):
        data = self._calculate_lagged_features(data)
        data = self._calculate_5_last_match_average(data, self.list_columns)
        data = self._calculate_5_last_match_sum(data, self.list_columns)
        data = self._calculate_5_last_match_std(data, self.list_columns)
        data = self._calculate_5_last_match_form(data)
        data = self._calculate_scaled_season_average(data, self.list_columns)
        return data

    def _prepare_basic_columns(self, data):

        if 'Date' in data.columns and 'Time' in data.columns:
            data['DateTime'] = pd.to_datetime(data['Date'] + ' ' + data['Time'])
            data.drop(["Date", "Time"], axis=1, inplace=True)
            data = data[['DateTime'] + [col for col in data.columns if col != 'DateTime']]
            data['Season'] = data['DateTime'].apply(
                lambda x: f"{x.year}-{x.year + 1}" if x.month >= 8 else f"{x.year - 1}-{x.year}")


        if 'Round' in data.columns:
            data = data[data['Round'].str.startswith('Matchweek')]
            if 'Round' in data.columns:  # Vérification à nouveau en cas de changement
                data['Round'] = data['Round'].str.extract(r'(\d+)').astype(int)


        if 'Formation' in data.columns:
            data['Formation'] = data['Formation'].apply(
                lambda x: x.replace('◆', '') if pd.notnull(x) else x)

        if 'GF' in data.columns and 'GA' in data.columns:
            if data[['GF', 'GA']].notnull().all().all():
                data[['GF', 'GA']] = data[['GF', 'GA']].astype(float).astype(int)
            data['GD'] = data['GF'] - data['GA']
            data["Total_Goals"] = data["GF"] + data["GA"]

        if 'Result' in data.columns:
            data['Points'] = data.apply(lambda row: {'W': 3, 'D': 1, 'L': 0}.get(row['Result']) if pd.notnull(row['Result']) else np.nan, axis=1)
            
        return data


    def _calculate_cumulatives_features(self, data):

        """ Creation of cumulatives columns per season (examle : Points cumulated at each date, goals for cumulated...)
        """

        data.sort_values(by=['Season', 'Round', 'Team'], inplace=True)
        data.reset_index(drop=True, inplace=True)

        cumulative_cols = data.groupby(['Season', 'Team']).agg({
            'Points': 'cumsum',
            'GD': 'cumsum',
            'GF': 'cumsum',
            'GA': 'cumsum'
        }).reset_index()

        data[['Points_Cum', 'GD_Cum', 'GF_Cum', 'GA_Cum']] = cumulative_cols[['Points', 'GD', 'GF', 'GA']]
        
        return data


    def _calculate_ranking(self, data):

        data.sort_values(by=['Season', 'Round', 'Points_Cum', 'GD_Cum'], ascending=[True, True, False, False], inplace=True)
        data['Ranking'] = data.groupby(['Season', 'Round']).cumcount() + 1

        return data

    def _features_bookmaker_creation(self, data):

        data["Minus 1.5 Goals"] = (data["Total_Goals"] <= 1.5).astype(int)
        data["Minus 2.5 Goals"] = (data["Total_Goals"] <= 2.5).astype(int)
        data["Minus 3.5 Goals"] = (data["Total_Goals"] <= 3.5).astype(int)

        return data

    def find_mapping(self, championnat):
        
        # show the difference of team name between the two columns
        # help to modify the file for mapping

        data = read_data(championnat)
        problem_names_1 = set(data['Team'].unique()) - set(data['Opponent'].unique())
        problem_names_2 = set(data['Opponent'].unique()) - set(data['Team'].unique())

        print(sorted(problem_names_1))
        print(sorted(problem_names_2))


    def _rename_and_drop_columns(self, data):
    
        with open('mapping_columns.json', 'r', encoding='utf-8') as file:
            mappings = json.load(file)
        
        precise_renaming_dict = mappings.get("Columns", {})
        
        for old_col, new_col in precise_renaming_dict.items():
            if old_col in data.columns:
                data.rename(columns={old_col: new_col}, inplace=True)

        columns_to_drop = [
            "Standard_Gls", "Launched_Cmp", "Launched_Att", "Launched_Cmp%", 
            "Passes_Att (GK)", "Passes_Thr", "Passes_Launch%", "Passes_AvgLen", 
            "Goal Kicks_Att", "Goal Kicks_Launch%", "Goal Kicks_AvgLen", 
            "Crosses_Opp", "Crosses_Stp", "Crosses_Stp%", "Sweeper_#OPA", 
            "Sweeper_AvgDist", "Penalty Kicks_PKatt", "Performance_GA", 
            "Performance_PSxG", "Performance_PSxG+/-", "Receiving_Rec", 
            "Touches_Live", "Standard_PKatt", "Receiving_PrgR"
        ]

        columns_to_drop = [col for col in columns_to_drop if col in data.columns]
        data.drop(columns=columns_to_drop, inplace=True)

        return data

    def _calculate_lagged_features(self, data):

        data.sort_values(by=['Season', 'Round', 'Team'], inplace=True)
        data.reset_index(drop=True, inplace=True)

        lag_cols = ['Points_Cum', 'GD_Cum', 'GF_Cum', 'GA_Cum']
        data[[f'{col}_Lag' for col in lag_cols]] = data.groupby(['Season', 'Team'])[lag_cols].shift(1)

        # Décalage du classement pour chaque équipe
        data['Ranking_Lag'] = data.groupby(['Team'])['Ranking'].shift(1)

        return data

    def _calculate_5_last_match_form(self, data):

        data.sort_values(by=['Season', 'Round', 'Points_Cum', 'GD_Cum'], ascending=[True, True, False, False], inplace=True)
        
        data["5_Last_Matches_Win"] = data.groupby(['Season', 'Team'])['Result'].transform(
                                    lambda x: (x == "W").shift(1).rolling(window=5, min_periods=1).sum().fillna(0))

        data["5_Last_Matches_Loose"] = data.groupby(['Season', 'Team'])['Result'].transform(
                                    lambda x: (x == "L").shift(1).rolling(window=5, min_periods=1).sum().fillna(0))

        return data
    
    def _calculate_5_last_match_average(self, data, list_columns):

        #data.sort_values(by=['Season', 'Round', 'Points_Cum', 'GD_Cum'], ascending=[True, True, False, False], inplace=True)

        new_columns = pd.DataFrame(index=data.index)

        for col in list_columns:
            new_columns[f'{col}_5_Last_Matches_Average'] = data.groupby(['Season', 'Team'])[col].transform(lambda x: x.shift(1).rolling(window=5, min_periods=5).mean())

        data = pd.concat([data, new_columns], axis=1)

        return data

    def _calculate_5_last_match_sum(self, data, list_columns):

        data.sort_values(by=['Season', 'Round', 'Points_Cum', 'GD_Cum'], ascending=[True, True, False, False], inplace=True)

        new_columns = pd.DataFrame(index=data.index)

        for col in list_columns:
            new_columns[f'{col}_5_Last_Matches_Sum'] = data.groupby(['Season', 'Team'])[col].transform(lambda x: x.shift(1).rolling(window=5, min_periods=5).sum())

        data = pd.concat([data, new_columns], axis=1)

        return data

    def _calculate_5_last_match_std(self, data, list_columns):

        data.sort_values(by=['Season', 'Round', 'Points_Cum', 'GD_Cum'], ascending=[True, True, False, False], inplace=True)

        new_columns = pd.DataFrame(index=data.index)

        for col in list_columns:
            new_columns[f'{col}_5_Last_Matches_Std'] = data.groupby(['Season', 'Team'])[col].transform(lambda x: x.shift(1).rolling(window=5, min_periods=5).std())

        data = pd.concat([data, new_columns], axis=1)

        return data
    

    def _calculate_scaled_season_average(self, data, list_columns):

        data.sort_values(by=['Season', 'Round', 'Points_Cum', 'GD_Cum'], ascending=[True, True, False, False], inplace=True)

        new_columns = pd.DataFrame(index=data.index)

        for col in list_columns:
            new_columns[f'{col}_Scaled_Season_Average' ] = data.groupby(['Season', 'Team'])[col].transform(lambda x: x.expanding().mean())

        def minmax_scale(x):
            return (x - x.min()) / (x.max() - x.min())
            
        data = pd.concat([data, new_columns], axis=1)
        # Ensuite, utilisez cette fonction avec .transform() pour appliquer la normalisation à chaque groupe
        #RRR = A.groupby(['Season', 'Round'])['Tackles'].transform(minmax_scale)

        return data




    def _keep_columns_for_model(self, data):

        columns = self.foundations_columns
        cols_to_keep = [col for col in data.columns if "_Lag" in col or "_5_Last_Matches" in col or '_Scaled_Season_Average' in col or col in columns]

        data = data[cols_to_keep]

        return data

    def _merge_2_rows_in_one(self, data):

        data['MatchID'] = data['DateTime'].astype(str) + '-' + data[['Team', 'Opponent']].apply(sorted, axis=1).str.join('-vs-')

        fixed_columns = ['DateTime', 'Comp', 'Round', 'Day', 'MatchID', 'Season', 'Attendance', 'Referee', 'Match Report', 'Notes', "Minus 1.5 Goals", "Minus 2.5 Goals", "Minus 3.5 Goals"]
        
        moving_variables = [col for col in data.columns if col not in fixed_columns]

        data_home = data[data['Venue'] == 'Home'].copy()
        data_away = data[data['Venue'] == 'Away'].copy()

        rename_dict_home = {col: f"{col}_Home" for col in moving_variables}
        rename_dict_away = {col: f"{col}_Away" for col in moving_variables}
        data_home.rename(columns=rename_dict_home, inplace=True)
        data_away.rename(columns=rename_dict_away, inplace=True)

        data = pd.merge(data_home, data_away, on=fixed_columns, how='inner')

        conditions = [
            data['Result_Home'] == 'W',
            data['Result_Away'] == 'W',
            data['Result_Away'] == 'D'
        ]
        choices = ['W_Home', 'W_Away', 'D']
        data['Result'] = np.select(conditions, choices, default=np.nan)

        data.rename(columns={"Team_Home": "Team Home", "Team_Away": "Team Away"}, inplace=True)

        return data



#Keeper Save Percentage_5_Last_Matches_Std     nan = 432 donc les enlever ou les fixer à zéro
#minmax scaler
#regarder les groupby index (comprendre)
#creer les average de donnees en saison
    


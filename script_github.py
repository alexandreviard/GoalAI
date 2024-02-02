from fonctions import *
from scrapping import *


def update_data_global():

    """
    Met à jour les données de football en récupérant les dernières données scrapeées,
    en traitant ces données, et en les fusionnant avec les données existantes.
    Le script prédit également les futurs matchs de foot scrappés, et atrribue les probabilités associées.
    """

    mapping_equipe = {
    'Nimes': 'Nîmes',
    'Paris S-G': 'Paris Saint Germain',
    'Saint Etienne': 'Saint-Étienne'
    }

    # Obtenir la date et l'heure actuelles
    current_datetime = datetime.now()

    # Lire le fichier CSV contenant les résultats futurs
    future_results = pd.read_csv("Database/results.csv", index_col=0)
    future_results["DateTime"] = pd.to_datetime(future_results["DateTime"])

    # Vérifier si la dernière date dans le fichier est antérieure à la date actuelle
  
    last_date_in_file = future_results["DateTime"].max()
    if last_date_in_file <= current_datetime:

        # Lire le fichier CSV de la base de données actuelle
        current_database = pd.read_csv("Database/dynamic_soccer_database.csv", index_col=0)

        # Scrapper les dernières données de Ligue 1
        latest_data = scrape_latest_ligue1_data()
        new_data = latest_data[0].copy()

        # Ajouter les nouveaux matchs à la base de données actuelle
        updated_database = add_new_matches(base_initiale=current_database, base_nouvelle=new_data)
        updated_database.to_csv("Database/dynamic_soccer_database.csv")

        # Préparer les données pour les prochaines semaines de match
        upcoming_matchweeks = latest_data[1].copy()
        upcoming_matchweeks = find_futur_matchweeks(upcoming_matchweeks, mapping_equipe)

        # Traiter le cas où il n'y a pas de nouveaux matchs à récupérer
        if upcoming_matchweeks is None:
            return
        else:
            # Traiter les données des prochaines semaines de match
            processed_upcoming_matches = preprocess_initial(upcoming_matchweeks.copy(), mapping_equipe)
            processed_upcoming_matches = renommer_colonnes(processed_upcoming_matches)
            processed_upcoming_matches = columns_to_keep(processed_upcoming_matches)

            # Traiter les données mises à jour
            processed_updated_database = preprocess_initial(updated_database.copy(), mapping_equipe)
            processed_updated_database = renommer_colonnes(processed_updated_database)
            processed_updated_database = columns_to_keep(processed_updated_database)
            processed_updated_database = preprocess_variables(processed_updated_database)

            # Fusionner les données traitées
            combined_data = pd.concat([processed_updated_database, processed_upcoming_matches], sort=False).reset_index(drop=True)
            combined_data = preparation_model(combined_data)
            combined_data = preprocess_data(combined_data)

            """
            # Mettre à jour la colonne 'Result' dans future_results
            future_results = future_results.merge(combined_data[['MatchID', 'Result']], on='MatchID', how='left', suffixes=('', '_from_combined'))
            future_results['Result'].update(future_results['Result_from_combined'])
            future_results.drop(columns=['Result_from_combined'], inplace=True)
            
            """
            # Mettre à jour la colonne 'Result'
            future_results = future_results.merge(combined_data[['MatchID', 'Result']], on='MatchID', how='left', suffixes=('', '_from_combined'))
            future_results['Result'].update(future_results['Result_from_combined'])
            future_results.drop(columns=['Result_from_combined'], inplace=True)

            # Mettre à jour la colonne 'Minus 2.5 Goals', si cette colonne existe dans combined_data
            if 'GF_Home' in combined_data.columns:
                future_results = future_results.merge(combined_data[['MatchID', 'GF_Home']], on='MatchID', how='left', suffixes=('', '_from_combined'))
                future_results['GF_Home'].update(future_results['GF_Home_from_combined'])
                future_results.drop(columns=['GF_Home_from_combined'], inplace=True)

            # Mettre à jour la colonne 'Minus 2.5 Goals', si cette colonne existe dans combined_data
            if 'GF_Away' in combined_data.columns:
                future_results = future_results.merge(combined_data[['MatchID', 'GF_Away']], on='MatchID', how='left', suffixes=('', '_from_combined'))
                future_results['GF_Away'].update(future_results['GF_Away_from_combined'])
                future_results.drop(columns=['GF_Away_from_combined'], inplace=True)


            # Traiter les données pour la modélisation et la mise à jour finale
            final_result = modelisation(combined_data, current_datetime, model_type="RandomForest")
            future_results = pd.concat([future_results, final_result]).sort_values(by="DateTime", ascending=False).reset_index(drop=True)

            # Enregistrer les résultats futurs mis à jour
            future_results.to_csv("Database/results.csv")

    return

update_data_global()



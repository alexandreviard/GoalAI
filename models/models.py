class Model():
    def __init__(self, model, target):
        self._model = model
        self._target = target

    @property
    def model(self):
        return self._model

    def modelisation(self, df, cutoff_date, targets=["Result", "Minus 2.5 Goals"], model_type=None, plot_features=False):
        """
        Fonction pour créer et appliquer des modèles de prédiction pour plusieurs cibles.

        :param df: DataFrame contenant les données des matchs.
        :param cutoff_date: Date limite pour séparer les données d'entraînement et de test.
        :param targets: Liste des colonnes cibles pour la prédiction.
        :param plot_features: Booléen indiquant si les importances des caractéristiques doivent être tracées.
        :param model_type: Type de modèle de prédiction à utiliser. Si None, sélectionne automatiquement le meilleur modèle.
        :return: DataFrame avec les prédictions ajoutées pour chaque cible.
        """
        selected_columns = ["DateTime"] + [col for col in df.columns if col.endswith(('Lag1_Home', 'Lag1_Away', 'Lag_Home', 'Lag_Away'))]

        models = {
            'RandomForest': RandomForestClassifier(random_state=42, n_estimators=300, n_jobs=-1),
            'SVC': SVC(random_state=42, probability=True)
        }

        label_encoders = {target: LabelEncoder() for target in targets}

        for target in targets:
            
            X = df[selected_columns].copy()
            X[target] = df[target].astype('category')
            X_train = X[df['DateTime'] <= cutoff_date].dropna()
            y_train = X_train[target]
            X_train.drop(columns=[target, 'DateTime'], errors='ignore', inplace=True)
            y_train = label_encoders[target].fit_transform(y_train)

            
            if plot_features:
                X_test = X[df['DateTime'] > cutoff_date].drop(columns=['DateTime'], errors='ignore').dropna(subset=[col for col in selected_columns if col != 'DateTime'])
                y_test = X_test[target]
                X_test.drop(columns=target, inplace= True)
            else:
                X_test = X[df['DateTime'] > cutoff_date].drop(columns=[target,'DateTime'], errors='ignore').dropna(subset=[col for col in selected_columns if col != 'DateTime'])


            # Sélectionner le meilleur modèle via la validation croisée si aucun modèle n'est spécifié
            best_model = model_type

            if best_model is None:
                best_score = 0
                for name, model in models.items():

                    score = np.mean(cross_val_score(model, X_train, y_train, cv=3))
                    if score > best_score:
                        best_score = score
                        best_model = name

            selected_model = models[best_model]


            # Gestion du Suréchantillonnage
            oversampler = RandomOverSampler(sampling_strategy='all', random_state=5)
            X_train_resampled, y_train_resampled = oversampler.fit_resample(X_train, y_train)

            # Entraînement du modèle sélectionné
            selected_model.fit(X_train_resampled, y_train_resampled)


            # Prédiction des résultats et calcul des probabilités

            y_pred = selected_model.predict(X_test)
            df.loc[X_test.index, f'Predicted_{target}'] = label_encoders[target].inverse_transform(y_pred)


            if hasattr(selected_model, "predict_proba"):
                df.loc[X_test.index, f'Prediction_Probability_{target}'] = np.max(selected_model.predict_proba(X_test), axis=1).round(2)
            else:
                df.loc[X_test.index, f'Prediction_Probability_{target}'] = np.nan

            # Si plot_features est True et le modèle est un RandomForest, tracer les importances des caractéristiques
            if plot_features and isinstance(selected_model, RandomForestClassifier):
                importances = selected_model.feature_importances_
                indices = np.argsort(importances)[::-1]
                plt.figure(figsize=(12, 6))
                plt.title(f'Importance des features: {target}')
                plt.bar(range(X_train_resampled.shape[1]), importances[indices], align='center')
                plt.xticks(range(X_train_resampled.shape[1]), X_train_resampled.columns[indices], rotation=90)
                plt.tight_layout()
                plt.show()

            if plot_features:
                # Calcul de l'accuracy
                accuracy = accuracy_score(label_encoders[target].transform(y_test.dropna()), y_pred[:len(y_test.dropna())])
                print(f"Précision sur les prédictions : '{target}' avec {best_model}: {accuracy:.2f}")



        # Colonnes à retourner
        return_cols = ["DateTime", "Comp", "Saison", "Round", "Day", "Team Home", "GF_Home", "GF_Away", "Team Away", "Result"] + \
                    [col for target in targets for col in (f'Predicted_{target}', f'Prediction_Probability_{target}')] +  ["MatchID"]

        return df[return_cols][(df['DateTime'] > cutoff_date) & (df['Predicted_Result'].notnull())]

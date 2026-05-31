import pandas as pd
import requests
import time
import os  # Pour vérifier si le backup existe

API_KEY = "db1c1e421c66aba5fe3ea45a2851e3fa"

# Charger le fichier des 2000 films
df = pd.read_csv('../data/catalogue_films.csv')
print(f"🔄 Recherche de reviews pour {len(df)} films...")

# ⚠️ LIGNE IMPORTANTE : Si le backup existe déjà, on le charge directement
# Comme ça si tu relances le code, tu n'attends plus !
if os.path.exists('../output/reviews_backup.csv'):
    print("✅ Backup trouvé, chargement direct !")
    df_reviews = pd.read_csv('../output/reviews_backup.csv')  # Chargement instantané
    print(f"✅ {len(df_reviews)} reviews déjà sauvegardées !")
else:
    # Le backup n'existe pas → on télécharge tout depuis l'API
    # Liste vide pour stocker toutes les reviews
    reviews_data = []

    # Boucle sur chaque film
    for idx, row in df.iterrows():
        title = row['original_title_imdb']  # Titre du film
        tmdb_id = row['tmdb_id']  # ID TMDB déjà dans le fichier

        try:
            # Appel API pour récupérer les reviews du film
            reviews_url = f"https://api.themoviedb.org/3/movie/{int(tmdb_id)}/reviews?api_key={API_KEY}"
            reviews_response = requests.get(reviews_url)

            # Si la requête a bien marché (200 = OK)
            if reviews_response.status_code == 200:
                reviews = reviews_response.json().get('results', [])

                # Ajouter chaque review à la liste
                for review in reviews:
                    reviews_data.append({
                        'title': title,
                        'author': review['author'],
                        'content': review['content'],
                    })

            # Afficher la progression et sauvegarder toutes les 50 films
            if (idx + 1) % 50 == 0:
                print(f"  ✅ {idx + 1}/{len(df)} films ({len(reviews_data)} reviews)")
                pd.DataFrame(reviews_data).to_csv('../output/reviews_backup.csv', index=False)
                print(f"  💾 Backup sauvegardé !")

            # Pause pour ne pas surcharger l'API
            time.sleep(0.25)

        except Exception as e:
            # Si erreur sur un film, on affiche et on continue
            print(f"  ⚠️ {title}: {e}")

    # Convertir la liste en DataFrame
    df_reviews = pd.DataFrame(reviews_data)

    # Sauvegarder en CSV
    df_reviews.to_csv('../output/reviews_tmdb.csv', index=False)

    print(f"\n✅ {len(df_reviews)} reviews sauvegardées ! 🎉")
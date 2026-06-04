import pandas as pd
import requests
import time
import os

# ===== CONFIGURATION =====
TMDB_API_KEY = "db1c1e421c66aba5fe3ea45a2851e3fa"

# ===== CHARGER LES DONNÉES =====
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
df = pd.read_csv(os.path.join(BASE_DIR, '..', 'data', 'catalogue_films.csv'))
print(f"✅ {len(df)} films chargés")

# ===== VÉRIFIER SI UN BACKUP EXISTE =====
backup_path = os.path.join(BASE_DIR, '..', 'output', 'french_titles_backup.csv')
if os.path.exists(backup_path):
    df_backup = pd.read_csv(backup_path)
    start_idx = len(df_backup)
    titres_fr = df_backup['title_fr'].tolist()
    print(f"✅ Backup trouvé ! Reprise depuis le film {start_idx}")
else:
    start_idx = 0
    titres_fr = []
    print("🚀 Pas de backup, on repart de zéro")

# ===== FONCTION RÉCUPÉRER TITRE FRANÇAIS =====
def get_french_title(tmdb_id):
    try:
        url = f"https://api.themoviedb.org/3/movie/{int(tmdb_id)}"
        params = {"api_key": TMDB_API_KEY, "language": "fr-FR"}
        response = requests.get(url, params=params)
        data = response.json()
        return data.get('title', None)
    except:
        return None

# ===== RÉCUPÉRER LES TITRES FRANÇAIS =====
print(f"\n🚀 Récupération des titres français depuis le film {start_idx}...")

for idx, row in df.iloc[start_idx:].iterrows():
    if pd.notna(row['tmdb_id']):
        titre = get_french_title(row['tmdb_id'])
        titres_fr.append(titre)
    else:
        titres_fr.append(None)

    # Afficher la progression toutes les 100 films
    if (len(titres_fr)) % 100 == 0:
        print(f"  {len(titres_fr)}/{len(df)} films traités...")

        # Sauvegarde backup toutes les 100 films
        df_temp = df.iloc[:len(titres_fr)].copy()
        df_temp['title_fr'] = titres_fr
        df_temp.to_csv(backup_path, index=False)
        print(f"  💾 Backup sauvegardé !")

    time.sleep(0.15)

# ===== AJOUTER LA COLONNE =====
df['title_fr'] = titres_fr + [None] * (len(df) - len(titres_fr))
df['title_fr'] = df['title_fr'].fillna(df['original_title_imdb'])

print(f"\n✅ Titres français récupérés !")
print(df[['original_title_imdb', 'title_fr']].head(10))

# ===== SAUVEGARDER =====
output_path = os.path.join(BASE_DIR, '..', 'data', 'catalogue_films.csv')
df.to_csv(output_path, index=False)
print(f"\n💾 Fichier final sauvegardé !")
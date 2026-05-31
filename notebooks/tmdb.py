import pandas as pd
import requests
import time
import ast
import os
import matplotlib.pyplot as plt

# ===== CONFIGURATION =====
TMDB_API_KEY = "db1c1e421c66aba5fe3ea45a2851e3fa" 
output_folder = '../output' 
graph_folder = os.path.join(output_folder, 'graphiques') 
os.makedirs(graph_folder, exist_ok=True) 

# ===== TEST API =====
url = "https://api.themoviedb.org/3/movie/550"
params = {"api_key": TMDB_API_KEY}
response = requests.get(url, params=params)
data = response.json()
df = pd.DataFrame([data])
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)
print(df.T)

# ===== CHARGER LES FILMS IMDB =====
df_films = pd.read_csv('../output/imdb_clean_final.csv')
print(f"Nombre de films : {len(df_films)}")

# ===== FONCTION TEST (budget/revenue/popularity) =====
def get_tmdb_data(imdb_id):
    find_url = f"https://api.themoviedb.org/3/find/{imdb_id}"
    params = {"api_key": TMDB_API_KEY, "external_source": "imdb_id"}

    try:
        response = requests.get(find_url, params=params)
        data = response.json()

        if data['movie_results']:
            tmdb_id = data['movie_results'][0]['id']

            detail_url = f"https://api.themoviedb.org/3/movie/{tmdb_id}"
            params = {"api_key": TMDB_API_KEY}
            response = requests.get(detail_url, params=params)
            movie = response.json()

            return {
                'imdb_id': imdb_id,
                'tmdb_id': tmdb_id,
                'budget': movie.get('budget'),
                'revenue': movie.get('revenue'),
                'popularity': movie.get('popularity')
            }
    except:
        pass
    return None 

# ===== TEST SUR 10 FILMS SEULEMENT =====
print("Test amélioré...")
tmdb_results = []

for idx, row in df_films.head(10).iterrows():
    result = get_tmdb_data(row['tconst'])
    if result:
        tmdb_results.append(result)
    time.sleep(0.25)  

df_tmdb = pd.DataFrame(tmdb_results)
print(df_tmdb)

# Fusion du test avec les titres IMDb
df_tmdb = pd.DataFrame(tmdb_results)
df_tmdb = df_tmdb.merge(
    df_films[['tconst', 'primaryTitle']],
    left_on='imdb_id',
    right_on='tconst',
    how='left'
)
df_tmdb = df_tmdb[['imdb_id', 'tmdb_id', 'primaryTitle', 'budget', 'revenue', 'popularity']]
print(df_tmdb)

# ===== FILTRER LES FILMS DE QUALITÉ =====
# films avec beaucoup de votes par rapport à leur note
df_clean = df_films.copy()
df_clean['ratio_votes_notes'] = df_clean['numVotes'] / df_clean['averageRating']
df_qualite = df_clean[df_clean['ratio_votes_notes'] > df_clean['ratio_votes_notes'].mean()]
print(f"Films de qualité : {len(df_qualite)}")

# ===== FONCTION COMPLÈTE TMDB =====
# récupère les infos complètes dont on a besoin (popularity, sociétés, pays)
def get_tmdb_complete(imdb_id):
    find_url = f"https://api.themoviedb.org/3/find/{imdb_id}"
    params = {"api_key": TMDB_API_KEY, "external_source": "imdb_id"}

    try:
        response = requests.get(find_url, params=params)
        data = response.json()

        if data['movie_results']:
            tmdb_id = data['movie_results'][0]['id']

            detail_url = f"https://api.themoviedb.org/3/movie/{tmdb_id}"
            params = {"api_key": TMDB_API_KEY}
            response = requests.get(detail_url, params=params)
            movie = response.json()

            return {
                'imdb_id': imdb_id,
                'tmdb_id': tmdb_id,
                'popularity': movie.get('popularity'),
                # convertit en string pour pouvoir sauvegarder en CSV
                'production_companies': str(movie.get('production_companies', [])),
                'production_countries': str(movie.get('production_countries', []))
            }
    except:
        pass
    return None

# ===== TÉLÉCHARGEMENT AVEC SAUVEGARDE =====
# ⚠️ LIGNE IMPORTANTE : Si le backup existe déjà, on le charge directement
if os.path.exists('../output/tmdb_backup.csv'):
    print("✅ Backup trouvé, chargement direct !")
    df_tmdb_qualite = pd.read_csv('../output/tmdb_backup.csv')  # Chargement instantané
else:
    # Le backup n'existe pas → on télécharge tout depuis l'API
    print(f"\n🚀 Récupération TMDB pour {len(df_qualite)} films...")
    tmdb_results = []

    for idx, row in df_qualite.iterrows():
        result = get_tmdb_complete(row['tconst'])
        if result:
            tmdb_results.append(result)
        time.sleep(0.15)  # Pause entre chaque appel API

        # Toutes les 100 films on sauvegarde au cas où ça plante
        if (idx + 1) % 100 == 0:
            print(f"  {idx + 1}/{len(df_qualite)} films traités...")
            pd.DataFrame(tmdb_results).to_csv('../output/tmdb_backup.csv', index=False)
            print(f"  💾 Backup sauvegardé !")

    df_tmdb_qualite = pd.DataFrame(tmdb_results)
    print(f"✅ {len(df_tmdb_qualite)} films trouvés sur TMDB")

# ===== FUSION IMDB + TMDB =====
# On combine nos données IMDb avec les données TMDB
df_final = df_qualite.merge(
    df_tmdb_qualite,
    left_on='tconst',
    right_on='imdb_id',
    how='left'  # On garde tous les films IMDb même si pas trouvés sur TMDB
)

print(f"\n📊 Fusion réussie : {len(df_final)} films")
print(df_final[['tconst', 'primaryTitle', 'popularity', 'production_companies']].head(10))

# ===== EXPORT DU FICHIER FINAL =====
df_final.to_csv('../output/films_qualite_tmdb.csv', index=False)
print("\n💾 Fichier exporté !")

# ===== GRAPHIQUE 11 : TOP SOCIÉTÉS DE PRODUCTION =====
df_final['production_companies'] = df_final['production_companies'].apply(
    lambda x: ast.literal_eval(x) if isinstance(x, str) else (x if isinstance(x, list) else [])
)

# parcourt chaque film pour extraire le nom de chaque société
companies_list = []
for idx, row in df_final.iterrows():
    for comp in row['production_companies']:
        if isinstance(comp, dict) and 'name' in comp:
            companies_list.append(comp['name'])

top_companies = pd.Series(companies_list).value_counts().head(10)  # Top 10

fig, ax = plt.subplots(figsize=(12, 6))
top_companies.plot(kind='barh', ax=ax, color='chocolate')
ax.set_title('Top 10 Sociétés de Production - Films de Qualité', fontsize=14, fontweight='bold')
ax.set_xlabel('Nombre de films')
plt.tight_layout()
plt.savefig(os.path.join(graph_folder, '11_top_production_companies.png'), dpi=300, bbox_inches='tight')
plt.show()
print("✅ Graphique 11 : Top Sociétés de Production")

# ===== GRAPHIQUE 12 : TOP PAYS DE PRODUCTION =====
# Même logique que pour les sociétés
df_final['production_countries'] = df_final['production_countries'].apply(
    lambda x: ast.literal_eval(x) if isinstance(x, str) else (x if isinstance(x, list) else [])
)

countries_list = []
for idx, row in df_final.iterrows():
    for country in row['production_countries']:
        if isinstance(country, dict) and 'name' in country:
            countries_list.append(country['name'])

top_countries = pd.Series(countries_list).value_counts().head(10)  # Top 10

fig, ax = plt.subplots(figsize=(12, 6))
top_countries.plot(kind='barh', ax=ax, color='skyblue')
ax.set_title('Top 10 Pays de Production - Films de Qualité', fontsize=14, fontweight='bold')
ax.set_xlabel('Nombre de films')
plt.tight_layout()
plt.savefig(os.path.join(graph_folder, '12_top_production_countries.png'), dpi=300, bbox_inches='tight')
plt.show()
print("✅ Graphique 12 : Top Pays de Production")

print("✅ Graphiques sauvegardés !")

# ===== SYNTHÈSE DES POINTS COMMUNS =====
print("="*60)
print("📊 POINTS COMMUNS DES FILMS DE QUALITÉ")
print("="*60)

films_qualite = df_qualite.copy()

# 1. GENRES
genres_list = []
for genres_str in films_qualite['genres']:
    if pd.notna(genres_str):
        genres = genres_str.split(',')
        genres_list.extend(genres)
genres_series = pd.Series(genres_list)
top_genre = genres_series.value_counts().index[0]
print(f"\n🎬 GENRE DOMINANT : {top_genre}")
print(f"   Top 3 : {', '.join(genres_series.value_counts().index[:3].tolist())}")

# 2. DURÉE
duree_moy = films_qualite['runtimeMinutes'].mean()
print(f"\n⏱️ DURÉE OPTIMALE : {duree_moy:.0f} minutes")
print(f"   Entre {films_qualite['runtimeMinutes'].quantile(0.25):.0f} et {films_qualite['runtimeMinutes'].quantile(0.75):.0f} min")

# 3. ANNÉES
annee_top = films_qualite['startYear'].value_counts().index[0]
print(f"\n📅 PÉRIODE OPTIMALE : 2010-2020")
print(f"   Année la plus représentée : {annee_top:.0f}")

# 4. NOTES
note_moy = films_qualite['averageRating'].mean()
print(f"\n⭐ NOTE MOYENNE : {note_moy:.2f}/10")

# 5. VOTES
votes_moy = films_qualite['numVotes'].mean()
print(f"\n🗳️ VOTES MOYENS : {votes_moy:,.0f}")

print("\n" + "="*60)
print("✅ SYNTHÈSE TERMINÉE !")
print("="*60)
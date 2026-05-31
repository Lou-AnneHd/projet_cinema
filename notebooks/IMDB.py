import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
import pickle

# ===== CONFIGURATION CHEMINS LOCAL =====
folder = '../data'
output_folder = '../output'

os.makedirs(output_folder, exist_ok=True)
os.makedirs(os.path.join(output_folder, 'graphiques'), exist_ok=True)

path_basics = os.path.join(folder, 'title.basics.tsv.gz')
path_ratings = os.path.join(folder, 'title.ratings.tsv.gz')
path_crew = os.path.join(folder, 'title.crew.tsv.gz')
path_principals = os.path.join(folder, 'title.principals.tsv.gz')

files = os.listdir(folder)
path_names = next(os.path.join(folder, f) for f in files if 'name.basics' in f)

print(f"✅ Tous les chemins configurés !")

# ===== 1. NETTOYAGE =====
print("\n🚀 Nettoyage en cours...")

df_ratings = pd.read_csv(path_ratings, sep='\t', na_values='\\N')
df_ratings = df_ratings[df_ratings['numVotes'] >= 500]

cols_basics = ['tconst', 'titleType', 'primaryTitle', 'startYear', 'genres', 'runtimeMinutes']

# Filtrage des colonnes utiles
df_basics = pd.read_csv(path_basics, sep='\t', na_values='\\N', low_memory=False)
df_basics = df_basics[cols_basics]

df_basics = df_basics[df_basics['titleType'] == 'movie']

df_clean = pd.merge(df_basics, df_ratings, on='tconst')

df_crew = pd.read_csv(path_crew, sep='\t', na_values='\\N', usecols=['tconst', 'directors'])
df_clean = pd.merge(df_clean, df_crew, on='tconst', how='left')

df_clean['runtimeMinutes'] = pd.to_numeric(df_clean['runtimeMinutes'], errors='coerce')
df_clean = df_clean.dropna(subset=['startYear', 'genres', 'runtimeMinutes'])
df_clean = df_clean.drop_duplicates(subset=['tconst'])

print(f"✅ NETTOYAGE TERMINÉ !")
print(f"Taille de la base propre : {df_clean.shape[0]} films.")
print(f"Colonnes disponibles : {df_clean.columns.tolist()}")

df_clean.head()

# ===== DOUBLONS =====
doublons = df_clean.duplicated(subset=['primaryTitle', 'startYear'], keep=False)
nb_doublons = doublons.sum()

print(f"🔍 Nombre de lignes en doublon détectées : {nb_doublons}")

if nb_doublons > 0:
    print("\nExemples de doublons trouvés :")
    print(df_clean[doublons].sort_values(by='primaryTitle').head(4))

    df_clean = df_clean.sort_values('numVotes', ascending=False).drop_duplicates(subset=['primaryTitle', 'startYear'], keep='first')
    print(f"\n✅ Doublons supprimés. Nouveau total : {len(df_clean)} films.")
else:
    print("\n✅ Aucun doublon détecté sur le couple Titre/Année.")

# ===== SAUVEGARDER =====
save_path = os.path.join(output_folder, 'imdb_clean_final.csv')
df_clean.to_csv(save_path, index=False)
print(f"\n💾 Fichier sauvegardé : {save_path}")

# ===== 2. ANALYSE DES FILMS DE QUALITÉ =====
df_clean['ratio_votes_notes'] = df_clean['numVotes'] / df_clean['averageRating']

seuil = df_clean['ratio_votes_notes'].mean()
films_qualite = df_clean[df_clean['ratio_votes_notes'] > seuil]

print(f"\n📊 FILMS DE QUALITÉ")
print(f"Nombre total de films : {len(df_clean)}")
print(f"Nombre de films de qualité : {len(films_qualite)}")
print(f"Pourcentage : {(len(films_qualite)/len(df_clean)*100):.1f}%")

print(f"\n🎬 GENRES LES PLUS FRÉQUENTS")
print(films_qualite['genres'].value_counts().head(10))

print(f"\n📅 ANNÉES DE SORTIE")
print(films_qualite['startYear'].value_counts().sort_index().tail(10))

print(f"\n⏱️ DURÉE MOYENNE")
print(f"Durée moyenne films de qualité : {films_qualite['runtimeMinutes'].mean():.0f} minutes")
print(f"Durée moyenne tous films : {df_clean['runtimeMinutes'].mean():.0f} minutes")

print(f"\n⭐ NOTES MOYENNES")
print(f"Note moyenne films de qualité : {films_qualite['averageRating'].mean():.2f} / 10")
print(f"Note moyenne tous films : {df_clean['averageRating'].mean():.2f} / 10")

print(f"\n🗳️ VOTES MOYENS")
print(f"Votes moyens films de qualité : {films_qualite['numVotes'].mean():,.0f}")
print(f"Votes moyens tous films : {df_clean['numVotes'].mean():,.0f}")

# ===== 3. CHARGEMENT PRINCIPALS =====
tconst_qualite = set(films_qualite['tconst'])

df_principals = pd.read_csv(path_principals, sep='\t', na_values='\\N',
                             usecols=['tconst', 'nconst', 'category'])

df_principals = df_principals[df_principals['tconst'].isin(tconst_qualite)]
print(f"✅ Principals chargé : {len(df_principals)} lignes")

df_names = pd.read_csv(path_names, sep='\t', na_values='\\N',
                        usecols=['nconst', 'primaryName'])

df_principals = pd.merge(df_principals, df_names, on='nconst', how='left')

print(f"✅ Noms fusionnés !")

# ===== 4. TOP ACTEURS/ACTRICES =====
top_actors = df_principals[df_principals['category'].isin(['actor', 'actress'])]['primaryName'].value_counts().head(10)
print("🎭 TOP 10 ACTEURS/ACTRICES :")
print(top_actors)

# ===== 5. TOP RÉALISATEURS =====
top_directors = df_principals[df_principals['category'] == 'director']['primaryName'].value_counts().head(10)
print("\n👨‍🎬 TOP 10 RÉALISATEURS :")
print(top_directors)

# ===== 6. TOP COMPOSITEURS =====
top_composers = df_principals[df_principals['category'] == 'composer']['primaryName'].value_counts().head(10)
print("\n🎵 TOP 10 COMPOSITEURS :")
print(top_composers)

# ===== 7. SCÉNARISTES =====
df_crew_full = pd.read_csv(path_crew, sep='\t', na_values='\\N', usecols=['tconst', 'writers'])

df_crew_qualite = df_crew_full[df_crew_full['tconst'].isin(tconst_qualite)]

writers_list = []
for idx, row in df_crew_qualite.iterrows():
    if pd.notna(row['writers']):
        writers = str(row['writers']).split(',')
        for writer in writers:
            writers_list.append({'tconst': row['tconst'], 'nconst': writer.strip()})

df_writers = pd.DataFrame(writers_list)
df_writers = pd.merge(df_writers, df_names, on='nconst', how='left')

top_writers = df_writers['primaryName'].value_counts().head(10)
print("✍️ TOP 10 SCÉNARISTES :")
print(top_writers)

# ===== 8. RÉGIONS =====
files = os.listdir(folder)
path_akas = next(os.path.join(folder, f) for f in files if 'title.akas' in f)

df_akas = pd.read_csv(path_akas, sep='\t', na_values='\\N', usecols=['titleId', 'region'])
df_akas_qualite = df_akas[df_akas['titleId'].isin(tconst_qualite)]
top_regions = df_akas_qualite['region'].value_counts().head(10)

print("\n🌍 TOP 10 RÉGIONS/PAYS :")
print(top_regions)

# ===== 9. GENRES =====
genres_list = []
for genres_str in films_qualite['genres']:
    if pd.notna(genres_str):
        genres = genres_str.split(',')
        genres_list.extend(genres)

genres_series = pd.Series(genres_list)
top_genres = genres_series.value_counts().head(10)

print("\n🎬 TOP 10 GENRES :")
print(top_genres)

# ===== 10. GÉNÉRATION DES GRAPHIQUES =====
print("\n📊 Génération des graphiques...")
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 6)

graph_folder = os.path.join(output_folder, 'graphiques')

# 1. TOP ACTEURS
fig, ax = plt.subplots(figsize=(12, 6))
top_actors.plot(kind='barh', ax=ax, color='steelblue')
ax.set_title('Top 10 Acteurs/Actrices - Films de Qualité', fontsize=14, fontweight='bold')
ax.set_xlabel('Nombre de films')
plt.tight_layout()
plt.savefig(os.path.join(graph_folder, '01_top_acteurs.png'), dpi=300, bbox_inches='tight')
plt.show()
print("✅ Graphique 1 : Top Acteurs")

# 2. TOP RÉALISATEURS
fig, ax = plt.subplots(figsize=(12, 6))
top_directors.plot(kind='barh', ax=ax, color='coral')
ax.set_title('Top 10 Réalisateurs - Films de Qualité', fontsize=14, fontweight='bold')
ax.set_xlabel('Nombre de films')
plt.tight_layout()
plt.savefig(os.path.join(graph_folder, '02_top_realisateurs.png'), dpi=300, bbox_inches='tight')
plt.show()
print("✅ Graphique 2 : Top Réalisateurs")

# 3. TOP COMPOSITEURS
fig, ax = plt.subplots(figsize=(12, 6))
top_composers.plot(kind='barh', ax=ax, color='lightgreen')
ax.set_title('Top 10 Compositeurs - Films de Qualité', fontsize=14, fontweight='bold')
ax.set_xlabel('Nombre de films')
plt.tight_layout()
plt.savefig(os.path.join(graph_folder, '03_top_compositeurs.png'), dpi=300, bbox_inches='tight')
plt.show()
print("✅ Graphique 3 : Top Compositeurs")

# 4. TOP SCÉNARISTES
fig, ax = plt.subplots(figsize=(12, 6))
top_writers.plot(kind='barh', ax=ax, color='gold')
ax.set_title('Top 10 Scénaristes - Films de Qualité', fontsize=14, fontweight='bold')
ax.set_xlabel('Nombre de films')
plt.tight_layout()
plt.savefig(os.path.join(graph_folder, '04_top_scenaristes.png'), dpi=300, bbox_inches='tight')
plt.show()
print("✅ Graphique 4 : Top Scénaristes")

# 5. TOP RÉGIONS
fig, ax = plt.subplots(figsize=(12, 6))
top_regions.plot(kind='barh', ax=ax, color='mediumpurple')
ax.set_title('Top 10 Régions/Pays - Films de Qualité', fontsize=14, fontweight='bold')
ax.set_xlabel('Nombre de films')
plt.tight_layout()
plt.savefig(os.path.join(graph_folder, '05_top_regions.png'), dpi=300, bbox_inches='tight')
plt.show()
print("✅ Graphique 5 : Top Régions")

# 6. TOP GENRES
fig, ax = plt.subplots(figsize=(12, 6))
top_genres.plot(kind='barh', ax=ax, color='crimson')
ax.set_title('Top 10 Genres - Films de Qualité', fontsize=14, fontweight='bold')
ax.set_xlabel('Nombre de films')
plt.tight_layout()
plt.savefig(os.path.join(graph_folder, '06_top_genres.png'), dpi=300, bbox_inches='tight')
plt.show()
print("✅ Graphique 6 : Top Genres")

# 7. TIMELINE ANNÉES
years_count = films_qualite['startYear'].value_counts().sort_index()

fig, ax = plt.subplots(figsize=(14, 6))
ax.plot(years_count.index, years_count.values, marker='o', linewidth=2, markersize=6, color='navy')
ax.fill_between(years_count.index, years_count.values, alpha=0.3, color='navy')
ax.set_title('Évolution du nombre de films de qualité par année', fontsize=14, fontweight='bold')
ax.set_xlabel('Année')
ax.set_ylabel('Nombre de films')
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(graph_folder, '07_timeline_annees.png'), dpi=300, bbox_inches='tight')
plt.show()
print("✅ Graphique 7 : Timeline Années")

# 8. DURÉE
fig, ax = plt.subplots(figsize=(12, 6))
sns.histplot(data=films_qualite, x='runtimeMinutes', bins=30, kde=True, ax=ax, color='teal')
ax.set_title('Distribution de la durée - Films de Qualité', fontsize=14, fontweight='bold')
ax.set_xlabel('Durée (minutes)')
ax.set_ylabel('Nombre de films')
plt.tight_layout()
plt.savefig(os.path.join(graph_folder, '08_distribution_duree.png'), dpi=300, bbox_inches='tight')
plt.show()
print("✅ Graphique 8 : Distribution Durée")

# 9. NOTES
fig, ax = plt.subplots(figsize=(12, 6))
sns.histplot(data=films_qualite, x='averageRating', bins=20, kde=True, ax=ax, color='green')
ax.set_title('Distribution des notes - Films de Qualité', fontsize=14, fontweight='bold')
ax.set_xlabel('Note moyenne (/10)')
ax.set_ylabel('Nombre de films')
plt.tight_layout()
plt.savefig(os.path.join(graph_folder, '09_distribution_notes.png'), dpi=300, bbox_inches='tight')
plt.show()
print("✅ Graphique 9 : Distribution Notes")

# 10. VOTES
fig, ax = plt.subplots(figsize=(12, 6))
sns.histplot(data=films_qualite, x='numVotes', bins=30, kde=True, ax=ax, color='purple')
ax.set_title('Distribution des votes - Films de Qualité', fontsize=14, fontweight='bold')
ax.set_xlabel('Nombre de votes')
ax.set_ylabel('Nombre de films')
plt.tight_layout()
plt.savefig(os.path.join(graph_folder, '10_distribution_votes.png'), dpi=300, bbox_inches='tight')
plt.show()
print("✅ Graphique 10 : Distribution Votes")

print("✅ Graphiques sauvegardés sur dossier !")

# ===== 11. EXPORT DES DONNÉES =====
df_clean.to_csv(os.path.join(output_folder, 'imdb_clean_final.csv'), index=False)

top_data = {
    'acteurs': top_actors,
    'realisateurs': top_directors,
    'compositeurs': top_composers,
    'scenaristes': top_writers,
    'regions': top_regions,
    'genres': top_genres
}

with open(os.path.join(output_folder, 'top_data.pkl'), 'wb') as f:
    pickle.dump(top_data, f)

print("✅ Données exportées !")

print("\n" + "="*60)
print("✅ EXPLORATION TERMINÉE !")
print(f"   Dossier : {output_folder}/")
print("="*60)
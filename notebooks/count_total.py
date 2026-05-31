import pandas as pd

#Acteurs
df_principals = pd.read_csv('../data/title.principals.tsv.gz', sep='\t', na_values='\\N')

df = pd.read_csv('../output/imdb_clean_final.csv')
df['ratio_votes_notes'] = df['numVotes'] / df['averageRating']
films_qualite = df[df['ratio_votes_notes'] > df['ratio_votes_notes'].mean()]
tconst_qualite = set(films_qualite['tconst'])

df_p = df_principals[df_principals['tconst'].isin(tconst_qualite)]

print('Acteurs uniques:', df_p[df_p['category'].isin(['actor', 'actress'])]['nconst'].nunique())
print('Réalisateurs uniques:', df_p[df_p['category'] == 'director']['nconst'].nunique())
print('Compositeurs uniques:', df_p[df_p['category'] == 'composer']['nconst'].nunique())

# Scénaristes
df_crew = pd.read_csv('../data/title.crew.tsv.gz', sep='\t', na_values='\\N', usecols=['tconst', 'writers'])
df_crew_qualite = df_crew[df_crew['tconst'].isin(tconst_qualite)]
writers_list = []
for _, row in df_crew_qualite.iterrows():
    if pd.notna(row['writers']):
        for w in str(row['writers']).split(','):
            writers_list.append(w.strip())
print('Scénaristes uniques:', len(set(writers_list)))

# Régions
df_akas = pd.read_csv('../data/title.akas.tsv.gz', sep='\t', na_values='\\N', usecols=['titleId', 'region'])
df_akas_qualite = df_akas[df_akas['titleId'].isin(tconst_qualite)]
print('Régions uniques:', df_akas_qualite['region'].nunique())

# Genres
genres_list = []
for genres_str in films_qualite['genres']:
    if pd.notna(genres_str):
        genres_list.extend(genres_str.split(','))
print('Genres uniques:', len(set(genres_list)))
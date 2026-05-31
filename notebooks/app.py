import streamlit as st
import pandas as pd
import os

# ===== CONFIGURATION DE LA PAGE =====
st.set_page_config(
    page_title="🎬 Cinéma Creuse",
    page_icon="🎬",
    layout="wide"
)

# ===== CHARGER LES DONNÉES =====
@st.cache_data  
def load_data():
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    df = pd.read_csv(os.path.join(BASE_DIR, '..', 'output', 'films_qualite_tmdb.csv'))
    return df

df = load_data()

# ===== TITRE PRINCIPAL =====
st.title("🎬 Cinéma Creuse - Catalogue de Films")

# ===== PAGE D'ACCUEIL =====
st.subheader("🏠 Page d'accueil")

# Choix entre les 10 plus récents ou les 10 meilleures notes
choix = st.radio(
    "Afficher :",
    ["⏱️ Les 10 plus récents", "⭐ Les 10 meilleures notes"]
)

if choix == "⏱️ Les 10 plus récents":
    top10 = df.sort_values('startYear', ascending=False).head(10)
else:
    top10 = df.sort_values('averageRating', ascending=False).head(10)

# Afficher le tableau des 10 films
st.dataframe(
    top10[['primaryTitle', 'startYear', 'averageRating', 'genres']].reset_index(drop=True),
    use_container_width=True
)

# ===== SÉPARATEUR =====
st.divider()

# ===== FILTRES =====
st.subheader("🔍 Filtres")

col1, col2, col3 = st.columns(3)

# --- FILTRE GENRES ---
with col1:
    genres_list = []
    for genres_str in df['genres'].dropna():
        genres_list.extend(genres_str.split(','))
    genres_uniques = sorted(set(genres_list))

    genre_choisi = st.selectbox("🎭 Genre", ["Tous"] + genres_uniques)

# --- FILTRE NOTES ---
with col2:
    note_choisie = st.selectbox(
        "⭐ Note minimale",
        ["Toutes", "5 ⭐", "6 ⭐", "7 ⭐", "8 ⭐", "9 ⭐"]
    )

# --- FILTRE CLASSIQUE / CONTEMPORAIN ---
with col3:
    periode = st.radio(
        "📅 Période",
        ["Tous", "🎞️ Classique (avant 2000)", "🆕 Contemporain (2000+)"]
    )

# ===== APPLIQUER LES FILTRES =====
df_filtre = df.copy()

# Filtre genre
if genre_choisi != "Tous":
    df_filtre = df_filtre[df_filtre['genres'].str.contains(genre_choisi, na=False)]

# Filtre note
if note_choisie != "Toutes":
    note_min = int(note_choisie[0])
    df_filtre = df_filtre[df_filtre['averageRating'] >= note_min]

# Filtre période
if periode == "🎞️ Classique (avant 2000)":
    df_filtre = df_filtre[df_filtre['startYear'] < 2000]
elif periode == "🆕 Contemporain (2000+)":
    df_filtre = df_filtre[df_filtre['startYear'] >= 2000]

# ===== AFFICHER LES RÉSULTATS =====
st.subheader(f"🎬 {len(df_filtre)} films trouvés")

st.dataframe(
    df_filtre[['primaryTitle', 'startYear', 'averageRating', 'genres']].reset_index(drop=True),
    use_container_width=True
)
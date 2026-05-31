import pandas as pd
from textblob import TextBlob
from collections import Counter
import nltk
import string

# Télécharger les ressources nltk nécessaires
nltk.download('stopwords')
nltk.download('punkt')
from nltk.corpus import stopwords

# ===== CHARGER LES REVIEWS =====
df = pd.read_csv('../output/reviews_tmdb.csv')
print(f"📄 {len(df)} reviews chargées")

# ===== 1. NETTOYAGE =====
def clean_text(text):
    # Mettre en minuscules
    text = text.lower()
    # Supprimer la ponctuation
    text = text.translate(str.maketrans('', '', string.punctuation))
    # Supprimer les stopwords anglais
    stop_words = set(stopwords.words('english'))
    words = text.split()
    words = [w for w in words if w not in stop_words]
    return ' '.join(words)

df['clean_content'] = df['content'].apply(clean_text)
print("✅ Nettoyage terminé !")

# ===== 2. ANALYSE DE SENTIMENT =====
def get_sentiment(text):
    analysis = TextBlob(text)
    # Polarity : entre -1 (négatif) et 1 (positif)
    if analysis.sentiment.polarity > 0:
        return 'positive'
    elif analysis.sentiment.polarity < 0:
        return 'negative'
    else:
        return 'neutral'

def get_score(text):
    return round(TextBlob(text).sentiment.polarity, 2)

df['sentiment'] = df['content'].apply(get_sentiment)
df['sentiment_score'] = df['content'].apply(get_score)
print("✅ Analyse de sentiment terminée !")

# ===== 3. MOTS CLÉS PAR FILM =====
def get_keywords(texts, n=10):
    # Réunir tous les mots de toutes les reviews du film
    all_words = ' '.join(texts).split()
    # Compter les plus fréquents
    most_common = Counter(all_words).most_common(n)
    return ', '.join([word for word, count in most_common])

keywords = df.groupby('title')['clean_content'].apply(
    lambda x: get_keywords(x)
).reset_index()
keywords.columns = ['title', 'keywords']

print("✅ Mots clés extraits !")

# ===== 4. RÉSUMÉ PAR FILM =====
summary = df.groupby('title').agg(
    nb_reviews=('sentiment', 'count'),
    nb_positives=('sentiment', lambda x: (x == 'positive').sum()),
    nb_negatives=('sentiment', lambda x: (x == 'negative').sum()),
    score_moyen=('sentiment_score', 'mean')
).reset_index()

summary['score_moyen'] = summary['score_moyen'].round(2)
summary = summary.merge(keywords, on='title', how='left')

print("✅ Résumé par film créé !")
print(summary.head())

# ===== 5. EXPORT =====
df.to_csv('../output/reviews_with_sentiment.csv', index=False)
summary.to_csv('../output/reviews_summary.csv', index=False)

print("\n✅ Fichiers exportés !")
print("   - reviews_with_sentiment.csv (toutes les reviews avec sentiment)")
print("   - reviews_summary.csv (résumé par film)")
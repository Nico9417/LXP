import streamlit as st
import pandas as pd
import re
from openai import AzureOpenAI
import os
from dotenv import load_dotenv

load_dotenv()  # charge les variables du .env

client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_KEY"),
    api_version="2023-07-01-preview",
    azure_endpoint="https://openai-phones-demo.openai.azure.com"
)
# Chargement des données
@st.cache_data
def load_data():
    url = "https://mobileia.blob.core.windows.net/telephones/Dataset_Mobile_avec_EUR.csv?sp=r&st=2025-04-15T06:54:35Z&se=2025-05-01T14:54:35Z&spr=https&sv=2024-11-04&sr=b&sig=MKRx00spEJZPn2rCoFd1kbDkwXHz0ahUyZbnvz6LyOo%3D"
    df = pd.read_csv(url)
    return df

df = load_data()

# Nettoyage de colonnes si nécessaire
def nettoyer_chiffres(texte):
    if isinstance(texte, str):
        chiffres = re.findall(r'\d+', texte)
        return int(chiffres[0]) if chiffres else None
    return texte

df['RAM'] = df['Model Name'].apply(lambda x: nettoyer_chiffres(x) if 'GB RAM' in x else None)
df['Camera'] = df['Model Name'].apply(lambda x: nettoyer_chiffres(x) if 'MP' in x else None)
df['Launched Price (EUR)'] = pd.to_numeric(df['Launched Price (EUR)'], errors='coerce')
df['Company Name'] = df['Company Name'].fillna("Inconnue")

# Analyse IA
def analyser_besoin(question):
    response = client.chat.completions.create(
        model="gpt-35-turbo",
        messages=[
            {"role": "system", "content": "Tu es un assistant qui aide à recommander des téléphones selon le besoin, le budget, la marque ou l'usage."},
            {"role": "user", "content": question}
        ]
    )
    return response.choices[0].message.content

# Recommandation filtrée
def recommander_telephones(budget, ram_min, camera_min, marque_preferee):
    recommandations = []

    for _, row in df.iterrows():
        score = 0
        if pd.notna(row["Launched Price (EUR)"]) and row["Launched Price (EUR)"] <= budget:
            score += 1
        if pd.notna(row["RAM"]) and row["RAM"] >= ram_min:
            score += 1
        if pd.notna(row["Camera"]) and row["Camera"] >= camera_min:
            score += 1
        if marque_preferee.lower() != "sans préférence" and marque_preferee.lower() in row["Company Name"].lower():
            score += 1
        elif marque_preferee.lower() == "sans préférence":
            score += 1

        if score >= 2:
            recommandations.append({
                "📱 Modèle": row["Model Name"],
                "🏷️ Marque": row["Company Name"],
                "💶 Prix (€)": round(row["Launched Price (EUR)"], 2),
                "💾 RAM": row["RAM"] if pd.notna(row["RAM"]) else "❓",
                "📷 Caméra": row["Camera"] if pd.notna(row["Camera"]) else "❓",
                "⭐ Score": score
            })

    return recommandations[:5]

# Interface utilisateur
st.title("📱 Assistant Téléphones IA")

mode = st.radio("Mode de recherche", ["🧠 Langage naturel", "🧮 Formulaire classique"])

if mode == "🧠 Langage naturel":
    st.subheader("💬 Décrivez votre besoin librement")
    question = st.text_area("Exemple : Je veux un Samsung à moins de 500€ pour faire de belles photos")
    if st.button("Analyser avec IA") and question:
        with st.spinner("Analyse avec l'IA..."):
            resultat = analyser_besoin(question)
            st.success("✅ Résultat de l'IA :")
            st.write(resultat)

else:
    st.subheader("🎛️ Filtres classiques")

    budget = st.number_input("Quel est votre budget (€) ?", min_value=50, max_value=3000, value=800, step=50)
    ram_min = st.number_input("RAM minimale (Go)", min_value=1, max_value=32, value=6)
    camera_min = st.number_input("Caméra minimale (MP)", min_value=5, max_value=200, value=20)
    marques = ["Sans préférence"] + sorted(df["Company Name"].dropna().unique())
    marque_preferee = st.selectbox("Marque préférée", marques)

    if st.button("Rechercher"):
        recommandations = recommander_telephones(budget, ram_min, camera_min, marque_preferee)
        st.subheader("📱 Téléphones recommandés :")

        if recommandations:
            for r in recommandations:
                st.markdown(
                    f"- **{r['📱 Modèle']}** | {r['💾 RAM']} Go RAM | {r['📷 Caméra']} MP | {r['💶 Prix (€)']}€ | Score : {r['⭐ Score']}"
                )
        else:
            st.info("Aucun téléphone ne correspond aux critères.")
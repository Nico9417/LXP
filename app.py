import streamlit as st
import pandas as pd
import re
import random

# 🔗 Ton lien SAS ici
url = "https://mobileia.blob.core.windows.net/telephones/Dataset_Mobile_avec_EUR.csv?sp=r&st=2025-04-15T06:54:35Z&se=2025-05-01T14:54:35Z&spr=https&sv=2024-11-04&sr=b&sig=MKRx00spEJZPn2rCoFd1kbDkwXHz0ahUyZbnvz6LyOo%3D"

def load_data():
    df = pd.read_csv(url)

    def extract_number(val):
        try:
            return float(re.search(r"\d+(\.\d+)?", str(val)).group())
        except:
            return float('nan')

    df['RAM'] = df['RAM'].apply(extract_number)
    df['Back Camera'] = df['Back Camera'].apply(extract_number)
    df['Launched Price (EUR)'] = pd.to_numeric(df['Launched Price (EUR)'], errors='coerce')
    return df

df = load_data()

st.title("📱 Assistant IA – Recommandation de Téléphones")

# ▶️ Formulaire utilisateur
st.sidebar.header("🎛️ Vos préférences")

budget = st.sidebar.slider("Quel est votre budget (€) ?", 50, 2000, 500, step=50)
ram_min = st.sidebar.selectbox("RAM minimale (Go)", [2, 4, 6, 8, 12])
camera_min = st.sidebar.slider("Caméra minimale (MP)", 5, 200, 48)

# Marque préférée
marques_disponibles = sorted(df['Company Name'].dropna().unique())
marques_options = ["Aucune"] + marques_disponibles
marque_pref = st.sidebar.selectbox("Marque préférée", marques_options)

# ▶️ Bouton
if st.sidebar.button("🔍 Rechercher"):

    # Filtrage
    if marque_pref.lower() != "aucune":
        df_filtre = df[df['Company Name'].str.lower() == marque_pref.lower()]
    else:
        df_filtre = df.copy()

    results = []

    for _, row in df_filtre.iterrows():
        if pd.isna(row['RAM']) or pd.isna(row['Back Camera']):
            continue

        score = 0
        if row['Launched Price (EUR)'] <= budget:
            score += 2
        if row['RAM'] >= ram_min:
            score += 1
        if row['Back Camera'] >= camera_min:
            score += 1

        if score > 0:
            results.append((score, row))

    if not results:
        st.warning("😕 Aucun téléphone trouvé avec ces critères.")
    else:
        if marque_pref.lower() == "aucune":
            random.shuffle(results)
        else:
            results.sort(key=lambda x: (-x[0], x[1]['Launched Price (EUR)']))

        st.success("📱 Téléphones recommandés :")
        for score, phone in results[:5]:
            ram = f"{int(phone['RAM'])} Go" if pd.notna(phone['RAM']) else "❓"
            cam = f"{int(phone['Back Camera'])} MP" if pd.notna(phone['Back Camera']) else "❓"
            prix = round(phone['Launched Price (EUR)'], 2)

            st.markdown(f"""
            **{phone['Company Name']} {phone['Model Name']}**
            - RAM : {ram}
            - Caméra : {cam}
            - Prix : {prix} €
            - Score : {score}
            ---
            """)
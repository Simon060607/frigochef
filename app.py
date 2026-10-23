import streamlit as st
from groq import Groq

# Configuration de la page Streamlit
st.set_page_config(page_title="FrigoChef AI", page_icon="🍳", layout="centered")

st.title("🍳 FrigoChef AI")
st.write("Transforme tes restes de frigo en repas gourmands, rapides et économiques !")

st.sidebar.header("⚙️ Configuration & Préférences")

# Récupération automatique de la clé via les Secrets Streamlit Cloud
groq_api_key = st.secrets.get("GROQ_API_KEY", "")

# Si la clé n'est pas dans les Secrets, on affiche le champ de saisie
if not groq_api_key:
    groq_api_key = st.sidebar.text_input(
        "Clé d'API Groq (gratuite)", 
        type="password",
        help="Obtiens ta clé gratuite sur console.groq.com"
    )
else:
    st.sidebar.success("Clé d'API activée 🔒")

# Configuration de l'utilisateur
temps_max = st.sidebar.slider("Temps de préparation max (minutes)", 10, 90, 30, step=5)
budget_cible = st.sidebar.select_slider(
    "Budget par portion",
    options=["Très économique (< 2€)", "Raisonné (2€ - 5€)", "Gourmet (> 5€)"]
)
regime = st.sidebar.selectbox(
    "Régime alimentaire", 
    ["Aucun", "Végétarien", "Végan", "Sans gluten", "Sans lactose"]
)
niveau = st.sidebar.select_slider(
    "Niveau de cuisine", 
    options=["Débutant", "Intermédiaire", "Chef"]
)
nb_personnes = st.sidebar.number_input("Nombre de portions", min_value=1, max_value=10, value=2, step=1)

# Formulaire d'ingrédients
ingredients = st.text_area(
    "Ingrédients disponibles dans ton frigo / placard (séparés par des virgules) :",
    placeholder="Ex: 2 œufs, reste de riz, une demi-courgette, sauce soja, un fond de crème, fromage râpé..."
)

# Prompt engineering
def construire_prompt(ingredients, temps_max, budget_cible, regime, niveau, nb_personnes):
    return f"""Tu es un chef cuisinier professionnel et un expert en anti-gaspillage et économie domestique.
Crée une recette gourmande et réalisable en suivant STRICTEMENT les contraintes suivantes :
- Ingrédients principaux disponibles : {ingredients}
- Temps de préparation maximal : {temps_max} minutes
- Cible budgétaire : {budget_cible}
- Nombre de personnes / portions : {nb_personnes}
- Régime alimentaire : {regime}
- Niveau du cuisinier : {niveau}

Présente la réponse dans ce format exact et structuré :
1. **Nom de la recette** (accrocheur)
2. **💰 Estimation du coût** (donne une estimation du coût total ET du coût par portion en euros €, avec un badge d'appréciation ex: Très économique / Raisonnable)
3. **⏱️ Temps de préparation et cuisson**
4. **🛒 Ingrédients utilisés** (distingue clairement ce qui vient du frigo et les basiques du placard comme sel, poivre, huile)
5. **👩‍🍳 Étapes de préparation** (numérotées et claires)
6. **🌱 Astuce Anti-Gaspi & Éco-Chef** (conseil pour valoriser les restes ou réduire davantage le coût)

Rédige la réponse en français de manière conviviale, engageante et motivante.
"""

def generer_recette_groq(client, prompt):
    try:
        models_data = client.models.list().data
        modeles_disponibles = [m.id for m in models_data]
    except Exception:
        modeles_disponibles = []

    priorites = [
        "llama-3.3-70b-versatile",
        "llama-3.1-8b-instant",
        "llama-3.2-3b-preview",
        "gemma2-9b-it"
    ]
    
    modeles_a_tester = [m for m in priorites if m in modeles_disponibles]
    if not modeles_a_tester:
        modeles_a_tester = modeles_disponibles if modeles_disponibles else ["llama-3.3-70b-versatile"]

    derniere_erreur = None
    for model in modeles_a_tester:
        try:
            completion = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=2000
            )
            return completion.choices[0].message.content
        except Exception as e:
            derniere_erreur = e
            continue

    raise Exception(f"Aucun modèle n'a pu répondre. Dernier problème : {derniere_erreur}")

# Bouton de génération
if st.button("Générer ma recette & estimer le coût 🍽️"):
    if not groq_api_key:
        st.error("Aucune clé d'API détectée. Veuillez la configurer dans la barre latérale.")
    elif not ingredients.strip():
        st.warning("Veuillez indiquer au moins un ingrédient.")
    else:
        with st.spinner("Le Chef calcule les coûts et prépare la recette..."):
            try:
                client = Groq(api_key=groq_api_key)
                prompt = construire_prompt(ingredients, temps_max, budget_cible, regime, niveau, nb_personnes)
                
                recette_generee = generer_recette_groq(client, prompt)
                
                st.success("Recette & estimation de coût prêtes !")
                st.markdown(recette_generee)
                
            except Exception as e:
                st.error(f"Une erreur est survenue lors de la génération : {e}")

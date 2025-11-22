import os
import requests
import json
import random 
from google import genai
from google.genai.errors import APIError

# --- 1. Récupération des Clés (Secrets GitHub) ---
# NOTE: L'ID de la Page Facebook est utilisé pour trouver l'ID du compte Instagram.
PAGE_ID = os.getenv("FB_PAGE_ID")
ACCESS_TOKEN = os.getenv("FB_ACCESS_TOKEN") 
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") 

# L'API Instagram est gérée via l'API Graph de Meta (v18.0)
GRAPH_BASE_URL = "https://graph.facebook.com/v18.0"

# --- Liste des sujets pour votre média ---
POST_TOPICS = [
    "La percée de l'IA dans l'analyse financière pour les PME.",
    "L'adoption des énergies renouvelables en Europe : faits et perspectives.",
    "Comment la blockchain réinvente la gestion de la chaîne d'approvisionnement.",
    "Conseils essentiels pour le télétravail sécurisé en 2025.",
    "Un fait fascinant sur l'histoire de l'internet."
]

def generate_ai_content_and_caption(topic):
    """Génère le texte (légende) et utilise VOTRE URL GitHub Pages."""
    
    # 1. URL d'image (VOTRE image statique GitHub Pages)
    # L'image 20200717_215732.jpg doit être dans le dossier assets/
    # Assurez-vous que cette image est bien au format 1:1 (carré) ou 1.91:1 (paysage) pour Instagram.
    image_url = "https://maxencelandais.github.io/Media-Auto-Instagram/assets/20200717_215732.jpg" 
    
    # 2. Générer la légende (texte)
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        prompt = (
            f"Génère une légende Instagram percutante et factuelle de 120 mots maximum sur le sujet : '{topic}'. "
            "Le ton doit être visuel et inviter à l'action. "
            "Termine par 3 hashtags pertinents et un appel à l'action simple (ex: double-tap, commentez)."
        )
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        caption = response.text.strip()
        
    except Exception as e:
        print(f"Erreur de génération IA : {e}")
        caption = f"🚨 Contenu IA de secours pour {topic}. #MediaFrance #Actualités"

    return image_url, caption

def get_instagram_business_id():
    """Récupère l'ID du compte Instagram Business lié à la Page Facebook."""
    # Cet endpoint est utilisé pour trouver l'ID du compte Instagram lié à la Page FB.
    url = f"{GRAPH_BASE_URL}/{PAGE_ID}?fields=instagram_business_account&access_token={ACCESS_TOKEN}"
    
    try:
        r = requests.get(url)
        r.raise_for_status()
        data = r.json()
        
        if 'instagram_business_account' in data:
            insta_id = data['instagram_business_account']['id']
            print(f"✅ ID Instagram Business trouvé: {insta_id}")
            return insta_id
        else:
            print(f"❌ Erreur: Compte Instagram Business non trouvé ou non lié à la Page {PAGE_ID}.")
            print("Vérifiez la liaison de la Page Facebook à Instagram.")
            print("Réponse Meta:", json.dumps(data, indent=4))
            return None
    except requests.exceptions.HTTPError as e:
        print(f"❌ Échec de la requête d'ID Instagram (HTTP): {e}")
        return None

def publish_instagram_media(insta_id, image_url, caption):
    """Effectue la publication en deux étapes sur Instagram."""
    
    # 1. CRÉER LE CONTENEUR MÉDIA (Content Publishing Container)
    print("Étape 1/2: Création du conteneur média...")
    
    media_container_url = f"{GRAPH_BASE_URL}/{insta_id}/media"
    
    container_payload = {
        "image_url": image_url,
        "caption": caption,
        "access_token": ACCESS_TOKEN
    }
    
    r1 = requests.post(media_container_url, data=container_payload)
    data1 = r1.json()
    
    if r1.status_code != 200 or 'id' not in data1:
        print(f"❌ Échec de la création du conteneur. Statut: {r1.status_code}")
        print("Erreur Meta (Conteneur):", json.dumps(data1, indent=4))
        return False
        
    creation_id = data1['id']
    print(f"✅ Conteneur créé avec ID: {creation_id}")
    
    # 2. PUBLIER LE CONTENEUR MÉDIA
    print("Étape 2/2: Publication du conteneur...")
    
    publish_url = f"{GRAPH_BASE_URL}/{insta_id}/media_publish"
    
    publish_payload = {
        "creation_id": creation_id,
        "access_token": ACCESS_TOKEN
    }
    
    r2 = requests.post(publish_url, data=publish_payload)
    data2 = r2.json()
    
    if r2.status_code == 200 and 'id' in data2:
        post_id = data2['id']
        print("\n" + "="*50)
        print("✅ PUBLICATION INSTAGRAM AUTONOME RÉUSSIE !")
        print(f"ID du Post Instagram: {post_id}")
        print("Vérifiez le compte @media_france.")
        print("==================================================")
        return True
    else:
        print(f"❌ Échec de la publication finale. Statut: {r2.status_code}")
        print("Erreur Meta (Publication):", json.dumps(data2, indent=4))
        return False


if __name__ == "__main__":
    if not all([PAGE_ID, ACCESS_TOKEN, GEMINI_API_KEY]):
        print("Erreur : FB_PAGE_ID, FB_ACCESS_TOKEN ou GEMINI_API_KEY ne sont pas définis. Vérifiez les Secrets GitHub.")
        exit(1)

    # 1. Trouver l'ID du compte Instagram lié à la Page FB
    insta_business_id = get_instagram_business_id()
    if not insta_business_id:
        exit(1)

    # Choisit un sujet aléatoire pour la production, utilise le premier pour le test
    topic = POST_TOPICS[0] 
    print(f"\n--- Génération et publication du Post Instagram : {topic} ---")
    
    # 2. Générer l'image et la légende
    image_url, caption = generate_ai_content_and_caption(topic)
    print(f"Légende générée (début) : {caption[:50]}...")
    print(f"URL de l'image utilisée : {image_url}")
    
    # 3. Publier sur Instagram
    publish_instagram_media(insta_business_id, image_url, caption)

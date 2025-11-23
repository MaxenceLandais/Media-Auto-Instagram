import os
import requests
import json
import time  
from google import genai
from google.genai.errors import APIError

# --- 1. Configuration et Clés (Secrets GitHub) ---
PAGE_ID = os.getenv("FB_PAGE_ID")
ACCESS_TOKEN = os.getenv("FB_ACCESS_TOKEN") 
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") 

GRAPH_BASE_URL = "https://graph.facebook.com/v18.0"

# --- Liste des sujets pour votre média ---
POST_TOPICS = [
    "La percée de l'IA dans l'analyse financière pour les PME.",
    "L'adoption des énergies renouvelables en Europe : faits et perspectives.",
    "Comment la blockchain réinvente la gestion de la chaîne d'approvisionnement.",
    "Conseils essentiels pour le télétravail sécurisé en 2025.",
]

# --- 2. Fonctions de Génération de Contenu ---

def generate_ai_content_and_caption(topic):
    """Génère le texte (légende) et utilise une URL de vidéo de test courte."""
    
    # URL de Vidéo de Test ULTRA-COURTE (environ 5 secondes, MP4)
    video_url = "https://test-videos.co.uk/vids/mp4/360/MP4-5s.mp4" 
    
    # Générer la description (texte)
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        prompt = (
            f"Génère une légende vidéo Instagram percutante et factuelle sur le sujet : '{topic}'. "
            "Le ton doit être visuel et inviter à l'action. "
            "Termine par 3 hashtags pertinents et un appel à l'action simple."
        )
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        caption = response.text.strip()
        
    except Exception as e:
        print(f"Erreur de génération IA : {e}")
        caption = f"🚨 Contenu IA de secours pour la vidéo : {topic}. #MediaFrance #Reel"

    return video_url, caption

# --- 3. Fonctions de Publication Instagram ---

def get_instagram_business_id():
    """Récupère l'ID du compte Instagram Business lié à la Page Facebook."""
    url = f"{GRAPH_BASE_URL}/{PAGE_ID}?fields=instagram_business_account&access_token={ACCESS_TOKEN}"
    
    try:
        r = requests.get(url)
        r.raise_for_status()
        data = r.json()
        
        if 'instagram_business_account' in data:
            return data['instagram_business_account']['id']
        else:
            print("❌ Erreur: Compte Instagram Business non trouvé.")
            return None
    except requests.exceptions.HTTPError as e:
        print(f"❌ Échec de la requête d'ID Instagram (HTTP): {e}")
        return None

def check_media_status(creation_id, access_token):
    """Vérifie l'état d'encodage du conteneur vidéo (boucle d'attente prolongée)."""
    
    status_url = f"{GRAPH_BASE_URL}/{creation_id}?fields=status_code&access_token={access_token}"
    
    # Augmentation de la limite d'attente à 3 minutes (36 * 5 secondes)
    max_checks = 36  
    
    for i in range(max_checks):
        r = requests.get(status_url)
        data = r.json()
        
        status = data.get('status_code')
        
        print(f"   [Vérification {i+1}/{max_checks}] Statut de la vidéo: {status}")
        
        if status == 'FINISHED':
            print("   ✅ Vidéo prête à être publiée.")
            return True
        
        if status == 'ERROR':
            print("   ❌ Erreur d'encodage de la vidéo.")
            return False
            
        # Attendre 5 secondes avant la prochaine vérification
        time.sleep(5) 
        
    print(f"   ❌ Délai d'attente dépassé ({max_checks * 5} secondes). Annulation de la publication.")
    return False


def publish_instagram_media(insta_id, video_url, caption):
    """Effectue la publication vidéo en deux étapes sur Instagram avec vérification du statut."""
    
    print("\n--- Début de la publication vidéo sur Instagram (Processus en 2 étapes) ---")
    
    # 1. CRÉER LE CONTENEUR MÉDIA
    print("Étape 1/2: Création du conteneur média...")
    media_container_url = f"{GRAPH_BASE_URL}/{insta_id}/media"
    
    container_payload = {
        "media_type": "REELS",           
        "video_url": video_url,          
        "caption": caption,
        "access_token": ACCESS_TOKEN
    }
    
    r1 = requests.post(media_container_url, data=container_payload)
    data1 = r1.json()
    
    if r1.status_code != 200 or 'id' not in data1:
        print(f"❌ Échec de la création du conteneur. Statut: {r1.status_code}")
        print("Erreur Meta (Conteneur Vidéo):", json.dumps(data1, indent=4))
        return False
        
    creation_id = data1['id']
    print(f"✅ Conteneur vidéo créé avec ID: {creation_id}")
    
    # VÉRIFICATION DE L'ÉTAT DU CONTENEUR
    if not check_media_status(creation_id, ACCESS_TOKEN):
        return False
    
    # 2. PUBLIER LE CONTENEUR MÉDIA
    print("\nÉtape 2/2: Publication du conteneur...")
    publish_url = f"{GRAPH_BASE_URL}/{insta_id}/media_publish"
    
    publish_payload = {
        "creation_id": creation_id,
        "access_token": ACCESS_TOKEN
    }
    
    r2 = requests.post(publish_url, data=publish_payload)
    data2 = r2.json()
    
    if r2.status_code == 200 and 'id' in data2:
        print("\n" + "="*50)
        print("✅ PUBLICATION VIDÉO INSTAGRAM DÉCLENCHÉE AVEC SUCCÈS !")
        print("La vidéo devrait apparaître sur Instagram d'ici quelques instants.")
        print("==================================================")
        return True
    else:
        print(f"❌ Échec de la publication finale Instagram. Statut: {r2.status_code}")
        print("Erreur Meta (Publication Vidéo):", json.dumps(data2, indent=4))
        return False


# --- 4. Main Execution ---

if __name__ == "__main__":
    if not all([PAGE_ID, ACCESS_TOKEN, GEMINI_API_KEY]):
        print("Erreur : Les Secrets GitHub ne sont pas définis.")
        exit(1)

    topic = POST_TOPICS[0] 
    print(f"\n--- Génération de contenu pour la vidéo : {topic} ---")
    
    # Générer l'URL de la vidéo et la légende
    video_url, caption = generate_ai_content_and_caption(topic)
    print(f"Légende générée (début) : {caption[:50]}...")
    print(f"URL de la vidéo utilisée : {video_url}")
    
    # PUBLICATION INSTAGRAM
    insta_business_id = get_instagram_business_id()
    if insta_business_id:
        print(f"✅ ID Instagram Business trouvé: {insta_business_id}")
        publish_instagram_media(insta_business_id, video_url, caption)

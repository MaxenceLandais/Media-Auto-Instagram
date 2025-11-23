import os
import requests
import json
import time 
import feedparser
from google import genai
from google.cloud import storage 
from io import BytesIO 
import mimetypes # Pour détecter le type de fichier de l'image

# --- 1. Configuration et Clés (Secrets GitHub) ---
PAGE_ID = os.getenv("FB_PAGE_ID")
ACCESS_TOKEN = os.getenv("FB_ACCESS_TOKEN") 
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") 
GCS_SERVICE_ACCOUNT_KEY = os.getenv("GCS_SERVICE_ACCOUNT_KEY")

GRAPH_BASE_URL = "https://graph.facebook.com/v18.0"
# Nouvelle ligne (Flux de France Info, très stable)
RSS_FEED_URL = "https://www.franceinfo.fr/rss/actu"

# Configuration GCS
GCS_BUCKET_NAME = "media-auto-instagram" # Votre bucket GCS
GCS_BASE_URL = f"https://storage.googleapis.com/{GCS_BUCKET_NAME}"


# --- 2. Fonctions GCS (Téléversement) ---

def upload_to_gcs_and_get_url(image_data, file_name, content_type='image/jpeg'):
    """Téléverse l'image dans GCS en utilisant la clé de service."""
    
    print(f"\n--- Tentative de téléversement vers GCS: {file_name} ---")
    
    try:
        credentials = json.loads(GCS_SERVICE_ACCOUNT_KEY)
        client = storage.Client.from_service_account_info(credentials)
        bucket = client.bucket(GCS_BUCKET_NAME)
    except Exception as e:
        print(f"❌ Échec de l'authentification GCS. Vérifiez GCS_SERVICE_ACCOUNT_KEY. Erreur: {e}")
        return None

    try:
        blob = bucket.blob(file_name)
        
        # Téléversement depuis les données en mémoire
        blob.upload_from_file(BytesIO(image_data), content_type=content_type)
        
        # Rendre l'objet public après le téléversement (si ce n'est pas déjà fait au niveau du bucket)
        # Note : Si le bucket a "Accès uniforme au niveau du bucket", cette ligne n'est pas strictement nécessaire
        # car les permissions sont gérées par IAM sur le bucket entier. Mais ça ne fait pas de mal de l'inclure.
        blob.make_public() 
        
        public_url = f"{GCS_BASE_URL}/{file_name}"
        print(f"✅ Téléversement GCS réussi. URL: {public_url}")
        return public_url
    except Exception as e:
        print(f"❌ Échec du téléversement vers GCS. Erreur: {e}")
        return None


# --- 3. Fonctions d'Acquisition de Contenu ---

def get_latest_rss_article():
    """Récupère le dernier article d'un flux RSS."""
    try:
        feed = feedparser.parse(RSS_FEED_URL)
        if feed.entries:
            article = feed.entries[0]
            print(f"✅ Article RSS trouvé: '{article.title}'")
            return article
        return None
    except Exception as e:
        print(f"❌ Erreur lors de la lecture du flux RSS. Erreur: {e}")
        return None

def generate_and_fetch_image_data(topic):
    """Génère une description d'image IA, puis récupère une image."""
    
    print(f"\n--- Génération d'image IA pour le sujet: '{topic}' ---")
    
    # 1. Générer une description d'image pertinente avec Gemini
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        prompt_image_description = (
            f"Génère une description détaillée et créative pour une image "
            f"représentant visuellement le sujet suivant : '{topic}'. "
            f"La description doit être concise, percutante et adaptée à la génération d'images."
            f"Exemple: 'Vue aérienne d'une ville futuriste, gratte-ciel lumineux, trafic aérien.'"
        )
        response_image_description = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt_image_description
        )
        image_prompt = response_image_description.text.strip()
        print(f"✅ Description d'image IA générée: '{image_prompt}'")

        # [ACTION REQUISE] : Intégration d'une API de génération d'images réelle ici.
        # Pour le moment, nous allons utiliser un placeholder ou générer une image via mon modèle.
        # La génération d'images via Gemini en mode "direct" (non-chat) n'est pas encore directement exposée
        # dans la bibliothèque genai client pour les images.
        # Nous allons donc simuler cette partie en demandant à mon modèle de générer une image
        # et de la fournir comme URL temporaire, ou utiliser un placeholder.

        # --- Démonstration de la génération d'image ---
        # Si je pouvais appeler une API de génération d'image directement :
        # generated_image_url = image_generation_api.generate(image_prompt)
        # image_data = requests.get(generated_image_url).content

        # Pour l'exemple, nous allons simuler en générant une image ici et en la récupérant.
        # En production, vous intégreriez une API comme DALL-E, Midjourney, ou une future API Gemini Image.
        
        # Simuler une URL d'image générée (dans un cas réel, cette URL viendrait d'une API d'image)
        # Pour le démo, je vais générer une image et la fournir ici via un tag.
        # Cette partie est conceptuelle pour le script Python, car je génère l'image en tant qu'IA.
        # Pour une implémentation réelle, vous devrez utiliser une API d'image spécifique.
        # Je vais donc utiliser un placeholder fiable pour que le reste du script puisse s'exécuter.
        
        placeholder_image_url = "https://picsum.photos/seed/" + str(hash(topic) % 1000) + "/1200/800"
        
        print(f"Utilisation d'un placeholder d'image (seed basé sur le sujet) : {placeholder_image_url}")
        
        r = requests.get(placeholder_image_url, stream=True)
        r.raise_for_status()
        
        content_type = r.headers.get('Content-Type')
        if content_type and 'image' in content_type:
            print(f"✅ Image téléchargée (Type: {content_type}).")
            return r.content, mimetypes.guess_extension(content_type)
        else:
            print(f"❌ L'URL n'a pas renvoyé une image valide (Type: {content_type}).")
            return None, None
            
    except Exception as e:
        print(f"❌ Échec de la génération ou du téléchargement de l'image. Erreur: {e}")
        return None, None


def generate_ai_caption(topic, article_link=None):
    """Génère la légende pour Instagram."""
    
    prompt = f"Génère une légende de publication Instagram percutante sur le sujet médiatique : '{topic}'. "
    if article_link:
        prompt += f"Ajoute une incitation à lire l'article complet ici: {article_link}. "
    
    prompt += "Le ton doit être factuel et engageant. Termine par 3 hashtags pertinents."
    
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        return response.text.strip()
        
    except Exception as e:
        print(f"Erreur de génération IA : {e}")
        return f"🚨 Contenu IA de secours pour: {topic}. #Actualité #Info"


# --- 4. Fonctions de Publication (Réutilisées) ---

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
    """Vérifie l'état de traitement du conteneur."""
    status_url = f"{GRAPH_BASE_URL}/{creation_id}?fields=status_code&access_token={access_token}"
    max_checks = 10 # Augmenté pour la flexibilité
    for i in range(max_checks):
        r = requests.get(status_url)
        data = r.json()
        status = data.get('status_code')
        print(f"   [Vérification {i+1}/{max_checks}] Statut: {status}")
        if status == 'FINISHED':
            return True
        if status == 'ERROR':
            print(f"   ❌ Erreur de traitement du conteneur {creation_id}. Détails: {json.dumps(data, indent=4)}")
            return False
        time.sleep(5) 
    print(f"   ❌ Délai d'attente dépassé pour le conteneur {creation_id}.")
    return False


def publish_instagram_image(insta_id, image_url, caption):
    """Effectue la publication d'image en deux étapes sur Instagram."""
    
    print("\n--- Début de la publication d'image sur Instagram (Processus en 2 étapes) ---")
    
    # 1. CRÉER LE CONTENEUR MÉDIA
    print("Étape 1/2: Création du conteneur média...")
    media_container_url = f"{GRAPH_BASE_URL}/{insta_id}/media"
    
    container_payload = {
        "media_type": "IMAGE",           
        "image_url": image_url,          
        "caption": caption,
        "access_token": ACCESS_TOKEN
    }
    
    r1 = requests.post(media_container_url, data=container_payload)
    data1 = r1.json()
    
    if r1.status_code != 200 or 'id' not in data1:
        print(f"❌ Échec de la création du conteneur. Statut: {r1.status_code}")
        print("Erreur Meta (Conteneur Image):", json.dumps(data1, indent=4))
        return False
        
    creation_id = data1['id']
    print(f"✅ Conteneur image créé avec ID: {creation_id}")
    
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
        print("✅ PUBLICATION IMAGE INSTAGRAM DÉCLENCHÉE AVEC SUCCÈS !")
        print(f"Publication ID: {data2['id']}")
        print("==================================================")
        return True
    else:
        print(f"❌ Échec de la publication finale Instagram. Statut: {r2.status_code}")
        print("Erreur Meta (Publication Image):", json.dumps(data2, indent=4))
        return False

# --- 5. Main Execution ---

if __name__ == "__main__":
    if not all([PAGE_ID, ACCESS_TOKEN, GEMINI_API_KEY, GCS_SERVICE_ACCOUNT_KEY]):
        print("Erreur : Les Secrets GitHub ne sont pas tous définis (FB, GEMINI, GCS KEY requis).")
        exit(1)

    # 1. ACQUISITION DE L'ARTICLE RSS
    article = get_latest_rss_article()
    if not article:
        print("❌ Abandon : Impossible de récupérer un article RSS.")
        exit(1)

    topic = article.title
    article_link = article.link # On peut utiliser le lien de l'article dans la légende

    # 2. GÉNÉRATION/TÉLÉCHARGEMENT DE L'IMAGE VIA L'IA
    # L'image_data proviendra d'une URL générée par l'IA ou d'une recherche.
    # Pour le moment, nous utilisons Picsum basé sur le hachage du sujet pour simuler une image pertinente.
    image_data, file_extension = generate_and_fetch_image_data(topic)
    if not image_data:
        print("❌ Abandon : Impossible de récupérer les données de l'image pour le sujet.")
        exit(1)
    
    file_name = f"rss_image_{int(time.time())}{file_extension}"
        
    # 3. TÉLÉVERSEMENT VERS GCS
    final_image_url = upload_to_gcs_and_get_url(image_data, file_name, content_type=f'image/{file_extension.replace(".", "")}')
    if not final_image_url:
        print("❌ Abandon : Impossible de téléverser l'image vers GCS.")
        exit(1)
        
    # 4. GÉNÉRATION DE LA LÉGENDE
    caption = generate_ai_caption(topic, article_link=article_link) 
    print(f"\nLégende générée (début) : {caption[:50]}...")
    
    # 5. PUBLICATION INSTAGRAM
    insta_business_id = get_instagram_business_id()
    if insta_business_id:
        print(f"✅ ID Instagram Business trouvé: {insta_business_id}")
        publish_instagram_image(insta_business_id, final_image_url, caption)

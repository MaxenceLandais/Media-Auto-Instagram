import os
import requests
import json
import time 
import feedparser
from google import genai
from google.cloud import storage 
from io import BytesIO 
import mimetypes 
from bs4 import BeautifulSoup # <--- IMPORT AJOUTÉ

# --- 1. Configuration et Clés (Secrets GitHub) ---
# (Configuration inchangée)
PAGE_ID = os.getenv("FB_PAGE_ID")
ACCESS_TOKEN = os.getenv("FB_ACCESS_TOKEN") 
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") 
GCS_SERVICE_ACCOUNT_KEY = os.getenv("GCS_SERVICE_ACCOUNT_KEY")

GRAPH_BASE_URL = "https://graph.facebook.com/v18.0"

# Configuration RSS (Google News, ultra-stable avec User-Agent)
RSS_FEED_URL = "https://news.google.com/rss?hl=fr&gl=FR&ceid=FR:fr" 
RSS_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"

# Configuration GCS
GCS_BUCKET_NAME = "media-auto-instagram" 
GCS_BASE_URL = f"https://storage.googleapis.com/{GCS_BUCKET_NAME}"


# --- 2. Fonctions GCS (Téléversement - INCHANGÉE) ---

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
        
        # Téléversement de l'image
        blob.upload_from_file(BytesIO(image_data), content_type=content_type)
        
        public_url = f"{GCS_BASE_URL}/{file_name}"
        print(f"✅ Téléversement GCS réussi. URL: {public_url}")
        return public_url
    except Exception as e:
        print(f"❌ Échec du téléversement vers GCS. Erreur: {e}")
        return None


# --- 3. Fonctions d'Acquisition de Contenu (MODIFIÉES) ---

def extract_media_url_from_entry(entry):
    """Essaie de trouver l'URL d'une image ou d'une vidéo dans une entrée RSS."""
    
    # 1. Tenter l'extraction via la balise Media RSS
    if 'media_content' in entry:
        for media in entry.media_content:
            if 'url' in media and media.get('type', '').startswith(('image/', 'video/')):
                print(f"   --> Média trouvé via media:content: {media.url}")
                return media.url

    # 2. Tenter l'extraction via les balises <img> dans le HTML (description ou summary)
    content_html = entry.get('description', '') or entry.get('summary', '') or entry.get('content', [{}])[0].get('value', '')
    
    if content_html:
        soup = BeautifulSoup(content_html, 'html.parser')
        
        # Recherche de balises <img>
        img_tag = soup.find('img')
        if img_tag and img_tag.get('src'):
            print(f"   --> Image trouvée dans le contenu HTML: {img_tag['src']}")
            return img_tag['src']
            
    return None


def get_latest_rss_article():
    """Récupère le dernier article et tente de trouver une URL média."""
    print(f"\n--- Tentative de récupération RSS depuis : {RSS_FEED_URL} ---")
    
    try:
        feed = feedparser.parse(RSS_FEED_URL, agent=RSS_USER_AGENT)
        
        if feed.status not in (200, 301, 302):
             print(f"❌ Échec de la requête RSS. Statut HTTP: {feed.status}")
             return None

        if feed.entries:
            article = feed.entries[0]
            print(f"✅ Article RSS trouvé: '{article.title}'")
            
            # Tenter d'extraire le média
            article.media_url = extract_media_url_from_entry(article)
            
            return article
        
        print("❌ Flux RSS valide mais aucune entrée trouvée.")
        return None
        
    except Exception as e:
        print(f"❌ Erreur critique lors de la lecture du flux RSS. Erreur: {e}")
        return None


def fetch_media_data(media_url):
    """Télécharge le média à partir de son URL."""
    
    print(f"\n--- Tentative de téléchargement du média d'origine: {media_url} ---")
    
    try:
        r = requests.get(media_url, stream=True, headers={'User-Agent': RSS_USER_AGENT}, timeout=15)
        r.raise_for_status()
        
        content_type = r.headers.get('Content-Type', '').lower()
        
        if content_type.startswith('image/') or content_type.startswith('video/'):
            file_extension = mimetypes.guess_extension(content_type, strict=True) 
            if not file_extension:
                # Fallback pour les images sans extension claire (ex: .jpeg)
                if 'jpeg' in content_type or 'jpg' in content_type:
                    file_extension = ".jpeg"
                elif 'png' in content_type:
                    file_extension = ".png"
                elif 'mp4' in content_type or 'video' in content_type:
                    file_extension = ".mp4"
                else:
                    file_extension = ".dat" # Type inconnu
            
            print(f"✅ Média d'origine téléchargé (Type: {content_type}). Extension: {file_extension}")
            return r.content, file_extension, content_type
        else:
            print(f"❌ L'URL n'a pas renvoyé un type de média valide (Type: {content_type}).")
            return None, None, None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Échec du téléchargement du média d'origine. Erreur: {e}")
        return None, None, None

def generate_and_fetch_image_data(topic):
    """(Fonction de secours) Génère une description d'image IA, puis récupère une image via un placeholder fiable."""
    
    # ... (Le reste de cette fonction reste inchangé, utilisant le placeholder picsum.photos) ...
    # Nous allons la simplifier pour cet exemple pour se concentrer sur la logique principale.
    
    print(f"\n--- Génération d'image IA de secours pour le sujet: '{topic}' ---")
    
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        
        # 1. Génération de la description d'image par l'IA
        # (Prompt simple pour la démo)
        prompt_image_description = f"Génère une description courte pour une image représentant visuellement : '{topic}'."
        response_image_description = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt_image_description
        )
        image_prompt = response_image_description.text.strip()
        print(f"✅ Description d'image IA générée: '{image_prompt}'")
        
        # 2. Téléchargement d'un placeholder
        placeholder_image_url = "https://picsum.photos/seed/" + str(hash(topic) % 1000) + "/1200/800"
        r = requests.get(placeholder_image_url, stream=True, headers={'User-Agent': RSS_USER_AGENT})
        r.raise_for_status()
        
        content_type = r.headers.get('Content-Type')
        file_extension = mimetypes.guess_extension(content_type, strict=True) or ".jpeg"
        print(f"✅ Image PLACEHOLDER téléchargée (Type: {content_type}).")
        
        return r.content, file_extension, content_type

            
    except Exception as e:
        print(f"❌ Échec de la génération de l'image de secours. Erreur: {e}")
        return None, None, None

def generate_ai_caption(topic, article_link=None):
    # (Fonction inchangée)
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


# --- 5. Main Execution (LOGIQUE DE SÉLECTION MODIFIÉE) ---

def publish_instagram_media(insta_id, media_url, caption, media_type):
    """Effectue la publication d'image ou de vidéo en deux étapes sur Instagram."""
    
    print(f"\n--- Début de la publication {media_type} sur Instagram ---")
    
    # Utilisez 'REELS' si c'est une vidéo, 'IMAGE' sinon
    media_type_ig = 'REELS' if media_type.startswith('video') else 'IMAGE'
    
    # 1. CRÉER LE CONTENEUR MÉDIA
    media_container_url = f"{GRAPH_BASE_URL}/{insta_id}/media"
    
    container_payload = {
        "media_type": media_type_ig,           
        "image_url": media_url, # image_url fonctionne pour les photos et les reels/videos courts hébergés
        "caption": caption,
        "access_token": ACCESS_TOKEN
    }
    
    r1 = requests.post(media_container_url, data=container_payload)
    # ... (le reste du code est inchangé)
    data1 = r1.json()
    
    if r1.status_code != 200 or 'id' not in data1:
        print(f"❌ Échec de la création du conteneur. Statut: {r1.status_code}")
        print(f"Erreur Meta (Conteneur {media_type_ig}):", json.dumps(data1, indent=4))
        return False
        
    creation_id = data1['id']
    print(f"✅ Conteneur {media_type_ig} créé avec ID: {creation_id}")
    
    if not check_media_status(creation_id, ACCESS_TOKEN):
        return False
    
    # 2. PUBLIER LE CONTENEUR MÉDIA
    print(f"\nÉtape 2/2: Publication du conteneur {media_type_ig}...")
    publish_url = f"{GRAPH_BASE_URL}/{insta_id}/media_publish"
    publish_payload = { "creation_id": creation_id, "access_token": ACCESS_TOKEN }
    
    r2 = requests.post(publish_url, data=publish_payload)
    data2 = r2.json()
    
    if r2.status_code == 200 and 'id' in data2:
        print("="*50)
        print(f"✅ PUBLICATION {media_type_ig} INSTAGRAM DÉCLENCHÉE AVEC SUCCÈS !")
        print(f"Publication ID: {data2['id']}")
        print("==================================================")
        return True
    else:
        print(f"❌ Échec de la publication finale Instagram. Statut: {r2.status_code}")
        print("Erreur Meta (Publication finale):", json.dumps(data2, indent=4))
        return False

# La fonction publish_instagram_image a été remplacée par publish_instagram_media (plus générale)
# Mais on garde l'appel de check_media_status et get_instagram_business_id intact.

if __name__ == "__main__":
    if not all([PAGE_ID, ACCESS_TOKEN, GEMINI_API_KEY, GCS_SERVICE_ACCOUNT_KEY]):
        print("Erreur : Les Secrets GitHub ne sont pas tous définis (FB, GEMINI, GCS KEY requis).")
        exit(1)

    # 1. ACQUISITION DE L'ARTICLE RSS
    article = get_latest_rss_article()
    if not article:
        exit(1)

    topic = article.title
    article_link = article.link 
    
    media_data, file_extension, content_type = None, None, None

    # --- 2. LOGIQUE DE SÉLECTION DU MÉDIA ---
    if article.get('media_url'):
        # Tenter de télécharger le média d'origine
        media_data, file_extension, content_type = fetch_media_data(article.media_url)
        
    if not media_data:
        print("\n--> Média d'origine non trouvé ou téléchargement échoué. REPLI sur l'IA.")
        # Générer une image de secours (Placeholder + IA pour le prompt)
        media_data, file_extension, content_type = generate_and_fetch_image_data(topic)

    if not media_data:
        print("❌ Abandon : Impossible d'obtenir des données média (origine ou IA).")
        exit(1)
    
    # Déterminer si c'est une image ou une vidéo pour le nom de fichier GCS
    media_type = 'image' if content_type.startswith('image/') else 'video'
    file_name = f"rss_{media_type}_{int(time.time())}{file_extension}"
        
    # 3. TÉLÉVERSEMENT VERS GCS
    final_media_url = upload_to_gcs_and_get_url(media_data, file_name, content_type=content_type)
    if not final_media_url:
        print("❌ Abandon : Impossible de téléverser le média vers GCS.")
        exit(1)
        
    # 4. GÉNÉRATION DE LA LÉGENDE
    caption = generate_ai_caption(topic, article_link=article_link) 
    print(f"\nLégende générée (début) : {caption[:50]}...")
    
    # 5. PUBLICATION INSTAGRAM
    insta_business_id = get_instagram_business_id()
    if insta_business_id:
        print(f"✅ ID Instagram Business trouvé: {insta_business_id}")
        # Appel de la nouvelle fonction générique
        publish_instagram_media(insta_business_id, final_media_url, caption, content_type)

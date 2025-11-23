import os
import requests
import json
import time
import feedparser
import io
import mimetypes 
from google.cloud import storage
from google import genai
from google.genai.errors import APIError
# Imports pour Imagen (Vertex AI) - CORRIGÉS POUR ÉVITER ModuleNotFoundError
from google.cloud import aiplatform 
from google.cloud.aiplatform_v1.services.prediction_service import PredictionServiceClient
from google.cloud.aiplatform_v1 import types # <--- CORRECTION D'IMPORT FINAL
from google.protobuf import json_format
from google.protobuf.struct_pb2 import Value  # Import explicite pour les paramètres de requête
from bs4 import BeautifulSoup 
import base64

# ==============================================================================
# 1. CONFIGURATION GLOBALE & SECRETS
# ==============================================================================

# Variables Meta (Instagram/Facebook)
PAGE_ID = os.getenv("FB_PAGE_ID")
ACCESS_TOKEN = os.getenv("FB_ACCESS_TOKEN")
GRAPH_BASE_URL = "https://graph.facebook.com/v19.0"

# Variables Google Cloud Storage (GCS)
GCS_SERVICE_ACCOUNT_KEY = os.getenv("GCS_SERVICE_ACCOUNT_KEY")
GCS_BUCKET_NAME = "media-auto-instagram"
GCS_PLACEHOLDER_URL = "https://picsum.photos/1200/800" 

# Variables Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Variables GCP/Vertex AI (Confirmées par vos captures)
GCP_PROJECT_ID = "media-auto-instagram" 
GCP_REGION = "us-central1" 

# Configuration RSS
RSS_FEED_URL = "https://news.google.com/rss?hl=fr&gl=FR&ceid=FR:fr" 
RSS_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"

# ==============================================================================
# 2. FONCTIONS D'ACQUISITION DE DONNÉES ET DE MÉDIA
# ==============================================================================

def extract_media_url_from_entry(entry):
    """Essaie de trouver l'URL d'une image ou d'une vidéo dans une entrée RSS."""
    
    if 'media_content' in entry:
        for media in entry.media_content:
            if 'url' in media and media.get('type', '').startswith(('image/', 'video/')):
                print(f"   --> Média trouvé via media:content: {media.url}")
                return media.url
    
    content_html = entry.get('description', '') or entry.get('summary', '') or entry.get('content', [{}])[0].get('value', '')
    
    if content_html:
        soup = BeautifulSoup(content_html, 'html.parser')
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
            
            class Article:
                def __init__(self, title, link, media_url):
                    self.title = title
                    self.link = link
                    self.media_url = media_url
            
            media_url = extract_media_url_from_entry(article)
            
            return Article(article.title, article.link, media_url)
        
        print("❌ Flux RSS valide mais aucune entrée trouvée.")
        return None
        
    except Exception as e:
        print(f"❌ Erreur critique lors de la lecture du flux RSS. Erreur: {e}")
        return None

def fetch_media_data(url):
    """Télécharge les données d'un média (image ou vidéo) à partir d'une URL."""
    if not url:
        return None, None, None
    try:
        r = requests.get(url, timeout=15, stream=True)
        r.raise_for_status()
        content_type = r.headers.get('Content-Type', '').split(';')[0].strip()
        
        if not content_type.startswith(('image/', 'video/')):
            print(f"   Avertissement : Type de contenu non supporté ({content_type}).")
            return None, None, None

        extension = mimetypes.guess_extension(content_type) or '.dat'
        
        return r.content, extension, content_type
    except Exception as e:
        print(f"   ❌ Échec du téléchargement du média depuis {url} : {e}")
        return None, None, None


# ==============================================================================
# 3. FONCTIONS IA & CLOUD STORAGE (GCS)
# ==============================================================================

def generate_and_fetch_image_data(topic):
    """Génère le prompt via Gemini, puis génère l'image via Imagen (Vertex AI)."""
    
    # 1. Génération du prompt (via Gemini)
    if not GEMINI_API_KEY:
        print("❌ Erreur: GEMINI_API_KEY non configurée. Utilisation de l'image de secours.")
        return fetch_media_data(GCS_PLACEHOLDER_URL)
        
    print(f"--- 1. Génération du prompt IA pour Imagen : '{topic}' ---")
    try:
        gemini_client = genai.Client(api_key=GEMINI_API_KEY)
        
        description_prompt = (
            f"Génère une description photo-réaliste, en une seule phrase, pour une image 1:1 "
            f"illustrant le sujet : '{topic}'. L'image doit être symbolique, utiliser des couleurs dramatiques, et éviter le texte."
        )
        
        response_desc = gemini_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=description_prompt
        )
        image_prompt = response_desc.text.strip()
        print(f"✅ Prompt IA généré: '{image_prompt}'")
    except Exception as e:
        print(f"❌ Échec de la génération du prompt Gemini: {e}")
        return fetch_media_data(GCS_PLACEHOLDER_URL)
    
    # 2. Appel à l'API Imagen (Vertex AI)
    print("\n--- 2. Appel à l'API Imagen (Vertex AI) ---")
    try:
        aiplatform.init(project=GCP_PROJECT_ID, location=GCP_REGION)
        
        # Le nom complet de l'endpoint public pour la génération d'images (Imagen 3.0)
        endpoint_name = (
            f"projects/{GCP_PROJECT_ID}/locations/{GCP_REGION}/publishers/google/models/imagen-3.0-generate-002"
        )
        
        # Préparation du client et de la requête via le PredictionServiceClient
        client_options = {"api_endpoint": f"{GCP_REGION}-aiplatform.googleapis.com"}
        client = PredictionServiceClient(client_options=client_options)

        # Les paramètres doivent être passés en JSON valide (via un dictionnaire)
        parameters_dict = {
            "aspectRatio": "1:1",
            "number_of_images": 1,
            "outputMimeType": "image/jpeg",
            "negative_prompt": "text, bad quality, blurry, watermark, low resolution, ugly",
        }

        # Création de la requête. Utilise types.PredictRequest et Value
        request = types.PredictRequest( # <-- UTILISATION CORRECTE DE LA CLASSE IMPORTÉE VIA ALIAS
            endpoint=endpoint_name,
            instances=[{"prompt": image_prompt}],
            parameters=json_format.ParseDict(parameters_dict, Value()), 
        )
        
        # Envoi de la requête
        response_imagen = client.predict(request=request)
        
        # Traitement de la réponse
        if response_imagen.predictions:
            # L'image générée est contenue dans le champ 'bytesBase64'
            img_data_b64 = response_imagen.predictions[0].get('bytesBase64')
            
            if img_data_b64:
                image_binary = base64.b64decode(img_data_b64)
                content_type = 'image/jpeg' 
                file_extension = '.jpeg'
                
                print("✅ Image générée par Imagen (Vertex AI) !")
                return image_binary, file_extension, content_type

        print("❌ Imagen n'a retourné aucune image. Repli sur le placeholder.")
        return fetch_media_data(GCS_PLACEHOLDER_URL)
            
    except Exception as e:
        print(f"❌ Échec critique de l'appel à Imagen. Erreur: {e}. Repli sur le placeholder.")
        return fetch_media_data(GCS_PLACEHOLDER_URL)


def generate_ai_caption(topic, article_link):
    """Génère une légende de post Instagram et des hashtags via l'IA."""
    if not GEMINI_API_KEY:
        return f"Nouvelles importantes : {topic}"
        
    print("--- Génération de légende IA en cours ---")
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        
        prompt = (
            f"Agis comme un rédacteur de 'flash info' sur Instagram. Écris une légende concise "
            f"(moins de 2200 caractères) et percutante pour un post concernant l'article suivant : "
            f"'{topic}'.\n\n"
            f"Le format doit être : 🔴 FLASH INFO : (Titre accrocheur et résumé)... Laisse trois lignes, puis une section d'hashtags pertinents (ex: #Ukraine #Guerre #Politique #FlashInfo...)."
            f"Ajoute le lien de l'article à la fin de la légende : {article_link}"
        )
        
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        
        return response.text.strip()
        
    except Exception as e:
        print(f"❌ Erreur de génération IA : {e}")
        return f"🔴 FLASH INFO : Le sujet du jour est '{topic}'. Plus de détails : {article_link} #Actualité"


def upload_to_gcs_and_get_url(data, file_name, content_type):
    """Téléverse un fichier binaire vers GCS et retourne son URL publique."""
    if not GCS_SERVICE_ACCOUNT_KEY or not GCS_BUCKET_NAME:
        print("❌ Erreur: GCS_SERVICE_ACCOUNT_KEY ou GCS_BUCKET_NAME non configuré.")
        return None
        
    print(f"--- Tentative de téléversement vers GCS: {file_name} ---")
    
    try:
        credentials_info = json.loads(GCS_SERVICE_ACCOUNT_KEY)
        client = storage.Client.from_service_account_info(credentials_info)
        
        bucket = client.bucket(GCS_BUCKET_NAME)
        blob = bucket.blob(file_name)
        
        blob.upload_from_string(data, content_type=content_type)
        
        gcs_url = f"https://storage.googleapis.com/{GCS_BUCKET_NAME}/{file_name}"
        print(f"✅ Téléversement GCS réussi. URL: {gcs_url}")
        return gcs_url
    
    except Exception as e:
        print(f"❌ Échec du téléversement GCS : {e}")
        return None


# ==============================================================================
# 4. FONCTIONS DE PUBLICATION INSTAGRAM
# ==============================================================================

def get_instagram_business_id():
    """Récupère l'ID du compte Instagram Business lié à la Page Facebook."""
    if not all([PAGE_ID, ACCESS_TOKEN]):
         print("❌ Erreur: PAGE_ID ou ACCESS_TOKEN manquant pour l'API Meta.")
         return None
         
    url = f"{GRAPH_BASE_URL}/{PAGE_ID}?fields=instagram_business_account&access_token={ACCESS_TOKEN}"
    try:
        r = requests.get(url)
        r.raise_for_status()
        data = r.json()
        if 'instagram_business_account' in data:
            return data['instagram_business_account']['id']
        else:
            print("❌ Erreur: Compte Instagram Business non trouvé lié à la Page Facebook.")
            return None
    except requests.exceptions.HTTPError as e:
        print(f"❌ Échec de la requête d'ID Instagram (HTTP): {e}")
        return None
    except Exception as e:
        print(f"❌ Erreur lors de la récupération de l'ID Instagram : {e}")
        return None

def check_media_status(creation_id, access_token):
    """Vérifie l'état de traitement du conteneur de média Instagram."""
    status_url = f"{GRAPH_BASE_URL}/{creation_id}?fields=status_code&access_token={access_token}"
    max_checks = 10 
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

def publish_instagram_media(insta_id, media_url, caption, content_type): 
    """Effectue la publication d'image ou de vidéo en deux étapes sur Instagram."""
    
    is_video = content_type.startswith('video/') 
    media_type_ig = 'REELS' if is_video else 'IMAGE'
    media_type_str = 'vidéo/Reel' if is_video else 'image/Photo'

    print(f"\n--- Début de la publication {media_type_str} ({media_type_ig}) sur Instagram ---")
    
    # 1. CRÉER LE CONTENEUR MÉDIA
    media_container_url = f"{GRAPH_BASE_URL}/{insta_id}/media"
    
    container_payload = {
        "media_type": media_type_ig,          
        "caption": caption,
        "access_token": ACCESS_TOKEN
    }
    
    if is_video:
        container_payload["video_url"] = media_url
        container_payload["thumb_offset"] = 0 
    else:
        container_payload["image_url"] = media_url

    r1 = requests.post(media_container_url, data=container_payload)
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


# ==============================================================================
# 5. MAIN EXECUTION
# ==============================================================================

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

    # --- 2. LOGIQUE DE SÉLECTION DU MÉDIA (Priorité à Imagen) ---
    if article.media_url:
        print(f"Tentative de récupération du média d'origine : {article.media_url}")
        media_data, file_extension, content_type = fetch_media_data(article.media_url)
        
    if not media_data:
        print("\n--> Média d'origine non trouvé ou téléchargement échoué. REPLI sur Imagen.")
        media_data, file_extension, content_type = generate_and_fetch_image_data(topic)

    if not media_data:
        print("❌ Abandon : Impossible d'obtenir des données média (origine ou IA).")
        exit(1)
    
    # 3. PRÉPARATION ET TÉLÉVERSEMENT VERS GCS
    media_type_base = 'image' if content_type.startswith('image/') else 'video'
    file_name = f"rss_{media_type_base}_{int(time.time())}{file_extension}"
        
    final_media_url = upload_to_gcs_and_get_url(media_data, file_name, content_type=content_type)
    if not final_media_url:
        print("❌ Abandon : Impossible de téléverser le média vers GCS.")
        exit(1)
        
    # 4. GÉNÉRATION DE LA LÉGENDE
    caption = generate_ai_caption(topic, article_link=article.link) 
    print(f"\nLégende générée (début) : {caption[:50]}...")
    
    # 5. PUBLICATION INSTAGRAM
    insta_business_id = get_instagram_business_id()
    
    if insta_business_id:
        print(f"✅ ID Instagram Business trouvé: {insta_business_id}")
        publish_instagram_media(insta_business_id, final_media_url, caption, content_type)
    else:
        print("❌ Publication Instagram annulée car l'ID Business n'a pas pu être récupéré.")

import os
import requests
import json
import time
import feedparser
import io
from google.cloud import storage
# Importation de l'API Gemini pour la génération d'images et de texte
from google import genai
from google.genai.errors import APIError

# ==============================================================================
# 1. CONFIGURATION GLOBALE & SECRETS (Doit être configuré via GitHub Secrets)
# ==============================================================================

# Variables Meta (Instagram/Facebook)
PAGE_ID = os.getenv("FB_PAGE_ID")
ACCESS_TOKEN = os.getenv("FB_ACCESS_TOKEN")
GRAPH_BASE_URL = "https://graph.facebook.com/v19.0"

# Variables Google Cloud Storage (GCS)
GCS_SERVICE_ACCOUNT_KEY = os.getenv("GCS_SERVICE_ACCOUNT_KEY")
GCS_BUCKET_NAME = "media-auto-instagram" # Remplacez par le nom de votre bucket GCS
GCS_PLACEHOLDER_URL = "https://example.com/placeholder-image.jpg" # URL d'une image de secours statique si nécessaire

# Variables Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# ==============================================================================
# 2. FONCTIONS D'ACQUISITION DE DONNÉES ET DE MÉDIA
# ==============================================================================

def get_latest_rss_article(rss_url="https://news.google.com/rss?hl=fr&gl=FR&ceid=FR:fr"):
    """Récupère le dernier article d'un flux RSS de Google News."""
    print(f"--- Tentative de récupération RSS depuis : {rss_url} ---")
    try:
        feed = feedparser.parse(rss_url)
        if not feed.entries:
            print("❌ Aucun article trouvé dans le flux RSS.")
            return None

        article = feed.entries[0]
        print(f"✅ Article RSS trouvé: '{article.title}'")
        
        # Le lien du média d'origine n'est pas toujours dans le RSS de Google News,
        # on peut l'ajouter si la source est une autre qui le fournit.
        media_url = article.get('media_content', [{}])[0].get('url') if article.get('media_content') else None
        
        # Création d'un objet simple pour retourner les données
        class Article:
            def __init__(self, title, link, media_url=None):
                self.title = title
                self.link = link
                self.media_url = media_url
        
        return Article(article.title, article.link, media_url)
        
    except Exception as e:
        print(f"❌ Erreur lors de la récupération du flux RSS : {e}")
        return None

def fetch_media_data(url):
    """Télécharge les données d'un média (image ou vidéo) à partir d'une URL."""
    if not url:
        return None, None, None
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        content_type = r.headers.get('Content-Type', '').split(';')[0].strip()
        
        if not content_type.startswith(('image/', 'video/')):
            print(f"   Avertissement : Type de contenu non supporté ({content_type}).")
            return None, None, None

        extension = '.' + content_type.split('/')[-1]
        
        # Dans le cas d'une vidéo (Reel), s'assurer qu'elle n'est pas trop longue
        # La vérification de la taille/durée est plus complexe sans télécharger tout le fichier.
        # Pour l'instant, on se contente du type.
        
        return r.content, extension, content_type
    except Exception as e:
        print(f"   ❌ Échec du téléchargement du média depuis {url} : {e}")
        return None, None, None


# ==============================================================================
# 3. FONCTIONS IA & CLOUD STORAGE (GCS)
# ==============================================================================

def generate_ai_caption(topic, article_link):
    """Génère une légende de post Instagram et des hashtags via l'IA."""
    if not GEMINI_API_KEY:
        print("❌ Erreur: GEMINI_API_KEY non configurée.")
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
            config=genai.types.GenerateContentConfig(
                temperature=0.7
            )
        )
        
        return response.text.strip()
        
    except APIError as e:
        print(f"❌ Erreur d'API Gemini (Légende): {e}")
        return f"🔴 FLASH INFO : Le sujet du jour est '{topic}'. Plus de détails : {article_link} #Actualité"
    except Exception as e:
        print(f"❌ Erreur inattendue (Légende): {e}")
        return f"🔴 FLASH INFO : Le sujet du jour est '{topic}'. Plus de détails : {article_link} #Actualité"


def generate_and_fetch_image_data(topic):
    """Génère une image via l'IA et retourne ses données binaires."""
    if not GEMINI_API_KEY:
        print("❌ Erreur: GEMINI_API_KEY non configurée. Utilisation de l'image de secours.")
        return fetch_media_data(GCS_PLACEHOLDER_URL)
        
    print(f"--- Génération d'image IA de secours pour le sujet: '{topic}' ---")

    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        
        # 1. Génération de la description pour DALL-E (ou tout autre modèle de génération d'image)
        description_prompt = (
            f"Génère une description simple, professionnelle et visuellement frappante, en une seule phrase, "
            f"pour une image d'actualité illustrant le sujet suivant : '{topic}'. "
            f"L'image doit être optimisée pour Instagram (carrée, 1080x1080) et avoir un style photo-réaliste, non-cartoon. "
            f"Évite le texte dans l'image et concentre-toi sur le symbolisme et le contexte géopolitique (ex: drapeau, bâtiments officiels, poignée de main). Ne mentionne pas de noms propres."
        )
        
        response_desc = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=description_prompt,
            config=genai.types.GenerateContentConfig(temperature=0.5)
        )
        
        image_prompt = response_desc.text.strip()
        print(f"✅ Description d'image IA générée: '{image_prompt}'")

        # 2. Génération de l'image (Simulation d'une API de génération d'image)
        # NOTE: L'API de génération d'images n'est pas directement exposée ici, nous simulerons
        # un retour d'image de substitution pour maintenir le flux du code.
        # Si vous utilisez une API comme Imagen ou DALL-E, remplacez cette partie.
        print("REMPLACEMENT: Simulation de la génération d'image par une image PLACEHOLDER.")
        
        media_data, extension, content_type = fetch_media_data(GCS_PLACEHOLDER_URL)
        
        if media_data:
            print(f"✅ Image PLACEHOLDER téléchargée (Type: {content_type}).")
            return media_data, extension, content_type
        else:
            return None, None, None

    except APIError as e:
        print(f"❌ Erreur d'API Gemini (Image): {e}")
        return fetch_media_data(GCS_PLACEHOLDER_URL)
    except Exception as e:
        print(f"❌ Erreur inattendue (Image): {e}")
        return fetch_media_data(GCS_PLACEHOLDER_URL)


def upload_to_gcs_and_get_url(data, file_name, content_type):
    """Téléverse un fichier binaire vers GCS et retourne son URL publique."""
    if not GCS_SERVICE_ACCOUNT_KEY or not GCS_BUCKET_NAME:
        print("❌ Erreur: GCS_SERVICE_ACCOUNT_KEY ou GCS_BUCKET_NAME non configuré.")
        return None
        
    print(f"--- Tentative de téléversement vers GCS: {file_name} ---")
    
    try:
        # Configuration des identifiants (nécessaire en environnement non-Cloud)
        key_dict = json.loads(GCS_SERVICE_ACCOUNT_KEY)
        credentials = genai.credentials.from_service_account_info(key_dict)
        storage_client = storage.Client(credentials=credentials)
        
        bucket = storage_client.bucket(GCS_BUCKET_NAME)
        blob = bucket.blob(file_name)
        
        blob.upload_from_string(data, content_type=content_type)
        
        # Rendre le fichier public si nécessaire (dépend de la configuration du bucket)
        blob.make_public() 
        
        gcs_url = blob.public_url
        print(f"✅ Téléversement GCS réussi. URL: {gcs_url}")
        return gcs_url
    
    except Exception as e:
        print(f"❌ Échec du téléversement GCS : {e}")
        return None


# ==============================================================================
# 4. FONCTIONS DE PUBLICATION INSTAGRAM (RÉORGANISÉES POUR ÉVITER NAMEERROR)
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
            print(json.dumps(data, indent=4))
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
    
    # Déterminer le type de média pour l'API
    is_video = content_type.startswith('video/') or content_type.startswith('application/octet-stream') 
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
        container_payload["thumb_offset"] = 0 # Optionnel: définir le temps de la vignette
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

    # --- 2. LOGIQUE DE SÉLECTION DU MÉDIA ---
    if article.media_url:
        print(f"Tentative de récupération du média d'origine : {article.media_url}")
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
    media_type_base = 'image' if content_type.startswith('image/') else 'video'
    file_name = f"rss_{media_type_base}_{int(time.time())}{file_extension}"
        
    # 3. TÉLÉVERSEMENT VERS GCS
    final_media_url = upload_to_gcs_and_get_url(media_data, file_name, content_type=content_type)
    if not final_media_url:
        print("❌ Abandon : Impossible de téléverser le média vers GCS.")
        exit(1)
        
    # 4. GÉNÉRATION DE LA LÉGENDE
    caption = generate_ai_caption(topic, article_link=article_link) 
    print(f"\nLégende générée (début) : {caption[:50]}...")
    
    # 5. PUBLICATION INSTAGRAM
    # C'est ici que l'erreur 'NameError' a été corrigée : la fonction est définie
    # plus haut, ce qui permet à l'interpréteur de la trouver.
    insta_business_id = get_instagram_business_id()
    
    if insta_business_id:
        print(f"✅ ID Instagram Business trouvé: {insta_business_id}")
        publish_instagram_media(insta_business_id, final_media_url, caption, content_type)
    else:
        print("❌ Publication Instagram annulée car l'ID Business n'a pas pu être récupéré.")

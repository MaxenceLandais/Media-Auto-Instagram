import os
import requests
import json
import time # <--- NOUVELLE LIBRAIRIE IMPORTÉE
from google import genai
from google.genai.errors import APIError
# ... (le reste des imports et des fonctions de génération IA restent inchangés) ...

# ... (Fonction get_instagram_business_id reste inchangée) ...


def check_media_status(creation_id, access_token):
    """Vérifie l'état d'encodage du conteneur vidéo."""
    
    status_url = f"{GRAPH_BASE_URL}/{creation_id}?fields=status_code&access_token={access_token}"
    
    max_checks = 12  # Vérifie pendant 1 minute (12 * 5 secondes)
    
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
            
        # Attendre avant la prochaine vérification
        time.sleep(5) 
        
    print("   ❌ Délai d'attente dépassé (60 secondes). Annulation de la publication.")
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
    
    # NOUVEAU: VÉRIFICATION DE L'ÉTAT DU CONTENEUR
    if not check_media_status(creation_id, ACCESS_TOKEN):
        return False # Arrêter si la vidéo n'est pas prête ou s'il y a une erreur.
    
    # 2. PUBLIER LE CONTENEUR MÉDIA (Seulement si le statut est FINISHED)
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
        print("==================================================")
        return True
    else:
        print(f"❌ Échec de la publication finale Instagram. Statut: {r2.status_code}")
        print("Erreur Meta (Publication Vidéo):", json.dumps(data2, indent=4))
        return False

# ... (Le reste du bloc 'if __name__ == "__main__":' reste inchangé) ...

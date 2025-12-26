import vertexai
from vertexai.preview.vision_models import ImageGenerationModel

def generate_image_v3(project_id, location, prompt, bucket_name):
    try:
        # Initialisation du SDK Vertex AI
        vertexai.init(project=project_id, location=location)
        
        # Chargement du modèle Imagen 3
        model = ImageGenerationModel.from_pretrained("imagegeneration@006")
        
        print(f"--- GÉNÉRATION IMAGEN 3 VERS GCS ---")
        
        # Génération de l'image
        # Note: Imagen 3 gère nativement le ratio 4:5 via aspect_ratio
        images = model.generate_images(
            prompt=prompt,
            number_of_images=1,
            aspect_ratio="4:5",
            storage_uri=f"gs://{bucket_name}/"
        )
        
        # Avec storage_uri, 'images' contient les objets générés et sauvés sur GCS
        if images:
            print(f"✅ SUCCÈS : Image générée et stockée sur GCS.")
            for img in images:
                print(f"Fichier : {img._gcs_uri if hasattr(img, '_gcs_uri') else 'Vérifiez votre bucket'}")
        else:
            print("❌ Erreur : Aucune image n'a été retournée.")

    except Exception as e:
        print(f"❌ ERREUR : {e}")

if __name__ == "__main__":
    PROJECT_ID = "media-auto-instagram" 
    LOCATION = "us-central1"
    BUCKET_NAME = "media-auto-instagram"
    
    PROMPT = """Photorealistic portrait of a woman leaning against a dark wooden bedpost, 
    right arm raised holding the post. She is wearing a black lace loungewear set with a crop top, 
    matching shorts and an open sheer floral robe. Environment is a bright bedroom with cream 
    louvered wardrobe doors and a white bed. Soft natural lighting, 85mm lens, f/2.8, 
    elegant lifestyle mood, 8k resolution, sharp focus."""

    generate_image_v3(PROJECT_ID, LOCATION, PROMPT, BUCKET_NAME)

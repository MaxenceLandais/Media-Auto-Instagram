import base64
import os
import datetime
from google.cloud import aiplatform

# IMPORTANT: Utilisation de google.cloud.aiplatform.preview.generative_models
# pour accéder aux modèles d'IA générative comme la génération d'images.
# La manière d'accéder à ces modèles peut changer avec les versions de la bibliothèque.
from google.cloud.aiplatform.generative_models import GenerativeModel, Part

def generate_image_with_vertex_ai(
    project_id: str,
    location: str,
    prompt: str,
    model_name: str = "image-generation", # Nom du modèle pour l'API Gemini/Generative AI
    output_dir: str = "generated_images",
    num_images: int = 1,
    image_width: int = 1024,
    image_height: int = 1024,
    mime_type: str = "image/png"
):
    """
    Génère une ou plusieurs images en utilisant l'API Vertex AI (GenerativeModel).
    """
    try:
        aiplatform.init(project=project_id, location=location)

        # Initialisation du modèle génératif
        # Le nom du modèle peut être "imagegeneration" ou "image-generation" selon la version/API
        # Nous utilisons GenerativeModel qui est plus général pour les modèles d'IA générative.
        model = GenerativeModel(model_name) 

        print(f"Tentative de génération de {num_images} image(s) avec le prompt: '{prompt}'...")

        # Préparation des requêtes. 
        # Pour les modèles d'IA générative modernes, on utilise model.generate_content
        # avec un objet Part pour le texte.
        # Notez que les paramètres comme width/height/sampleCount sont passés
        # dans les "generation_config" ou peuvent être gérés différemment selon le modèle.
        # Pour le modèle 'image-generation', ces paramètres sont souvent implicites ou spécifiques.
        
        # Le modèle "image-generation" est un modèle texte-image, donc le prompt est le contenu.
        # Les options de génération sont souvent dans le paramètre "generation_config".
        
        # Note: La structure exacte des paramètres de génération peut nécessiter des ajustements
        # en fonction de la documentation la plus récente de Google pour le modèle "image-generation".
        # Souvent, cela se fait via un dictionnaire 'generation_config'.
        # Pour la simplicité ici, nous allons appeler la méthode de base en lui passant le prompt.
        
        # Testons d'abord avec un appel direct si le modèle 'image-generation' le supporte
        # ou ajustons avec generation_config si nécessaire.
        # La méthode generate_content attend une liste de "Part" ou des strings.
        
        # Ici, l'appel sera plus simple pour 'image-generation' qui est spécialisé.
        # Si generate_content ne renvoie pas directement des images, il faudra utiliser
        # une méthode d'API REST directe ou une autre classe.
        # L'ancienne classe ImageGenerationModel était plus directe.
        
        # Si le modèle "image-generation" attend simplement un prompt via generate_content
        # et renvoie des images, ça ressemblerait à ceci:
        
        # Ceci est une approximation de comment ça devrait marcher avec GenerativeModel
        # pour un modèle texte-image comme "image-generation".
        # La documentation exacte peut varier pour les paramètres avancés.
        
        # Tenter la génération. La réponse de GenerativeModel.generate_content
        # contient généralement un attribut .candidates[0].content.parts
        # où les images seraient sous forme de .blob.data (base64)
        
        # Pour l'image-generation, il est possible qu'il y ait une méthode plus directe
        # ou que ce soit une API REST qui renvoie directement les données.
        # Si cette méthode échoue, nous devrons revenir à l'API REST via google.api_core.client_options
        # ou une autre structure.

        # Retrying the direct method with GenerativeModel, as 'image-generation' is often accessed this way.
        # The direct 'ImageGenerationModel' class might have been deprecated or moved.
        # The GenerativeModel.generate_content is the standard for Gemini and similar models.
        # For image generation, the content will be the prompt, and response will contain image parts.
        
        # Let's try to call generate_content with the prompt directly
        # and expect the image in the response structure.
        
        # Note: 'image-generation' is a specific model ID, not a generic GenerativeModel for text.
        # We might need to use a different approach.
        
        # The error `has no attribute 'ImageGenerationModel'` means the direct class is gone.
        # The generative_models module usually has GenerativeModel for text/multimodal.
        # For pure image generation (like DALL-E/Imagen), it might be a different client.

        # Let's re-evaluate based on the latest Vertex AI SDK for image generation.
        # The common approach for image generation through Vertex AI is often:
        # aiplatform.Endpoint or aiplatform.Model.predict() for custom models
        # or specific client for foundation models.
        
        # Given the error, the previous `ImageGenerationModel` class is no longer valid.
        # For foundation models like ImageGeneration, Google often provides specialized clients or
        # expects a predict call on a pre-trained model ID.
        
        # Let's try the `aiplatform.gapic.PredictionServiceClient` directly with the model ID.
        # This is a lower-level but more stable way to interact with specific models.

        from google.cloud.aiplatform_v1beta1.services.prediction_service import PredictionServiceClient
        from google.cloud.aiplatform_v1beta1.types import PredictRequest, Value

        client_options = {"api_endpoint": f"{location}-aiplatform.googleapis.com"}
        client = PredictionServiceClient(client_options=client_options)

        # Le payload pour le modèle de génération d'images est une liste d'instances.
        # Chaque instance est un dictionnaire avec le prompt.
        instances_proto = [
            Value(struct_value={"prompt": prompt})._pb
        ]
        
        # Les paramètres peuvent être configurés ici.
        # Pour image-generation, cela inclut souvent la taille, le nombre, etc.
        parameters_proto = Value(struct_value={
            "sample_count": num_images,
            "width": image_width,
            "height": image_height,
            "seed": 42 # Optionnel: pour la reproductibilité
        })._pb

        endpoint = f"projects/{project_id}/locations/{location}/publishers/google/models/{model_name}"

        response = client.predict(
            endpoint=endpoint,
            instances=instances_proto,
            parameters=parameters_proto
        )

        # Créer le répertoire de sortie si nécessaire
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            print(f"Répertoire '{output_dir}' créé.")

        # Traiter la réponse et sauvegarder les images
        if response and response.predictions:
            for i, prediction_value in enumerate(response.predictions):
                # Les prédictions sont des objets Value, il faut accéder au champ struct_value
                # et ensuite au champ "bytesBase64Encoded"
                prediction = prediction_value.struct_value
                if "bytesBase64Encoded" in prediction:
                    image_bytes = base64.b64decode(prediction["bytesBase64Encoded"])
                    
                    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = os.path.join(output_dir, f"generated_image_{timestamp}_{i+1}.{mime_type.split('/')[-1]}")

                    with open(filename, "wb") as f:
                        f.write(image_bytes)
                    print(f"Image {i+1} générée et sauvegardée sous {filename}")
                else:
                    print(f"Avertissement: La prédiction {i+1} ne contient pas de données d'image valides. Contenu: {prediction}")

        else:
            print("Aucune prédiction d'image reçue de l'API Vertex AI.")

    except Exception as e:
        print(f"ERREUR: Une erreur est survenue lors de la génération d'images: {e}")
        print("Vérifiez les points suivants:")
        print("1. Les permissions du compte de service (rôle 'Vertex AI User' ou 'Generative AI User').")
        print("2. La variable GOOGLE_APPLICATION_CREDENTIALS est correctement définie.")
        print("3. Le nom du modèle ('image-generation') et la région ('us-central1') sont corrects et le modèle est disponible.")
        print("4. Les quotas pour la génération d'images dans votre projet.")

if __name__ == "__main__":
    PROJECT_ID = "media-auto-instagram" 
    LOCATION = "us-central1" 
    my_prompt = "Un vaisseau spatial futuriste explorant une nébuleuse colorée, style art numérique détaillé."

    generate_image_with_vertex_ai(
        project_id=PROJECT_ID,
        location=LOCATION,
        prompt=my_prompt,
        model_name="imagegeneration", # Utilisez "imagegeneration" pour ce client GAPIC
        num_images=1,
        image_width=1024,
        image_height=1024,
        mime_type="image/png"
    )

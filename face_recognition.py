import cv2
import numpy as np
from facenet_pytorch import MTCNN, InceptionResnetV1
import torch
from PIL import Image
import base64
import io
import os

def cosine_similarity(a, b):
    """Calculate cosine similarity between two vectors"""
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

class FaceRecognition:
    def __init__(self):
        # Initialize MTCNN for face detection
        self.mtcnn = MTCNN(
            image_size=160, 
            margin=0, 
            min_face_size=20,
            thresholds=[0.6, 0.7, 0.7], 
            factor=0.709, 
            post_process=True,
            device='cpu'
        )
        
        # Initialize InceptionResnetV1 for face recognition
        self.resnet = InceptionResnetV1(pretrained='vggface2').eval()
        
    def extract_face_from_base64(self, base64_string):
        """Extract face from base64 encoded image"""
        try:
            # Remove data URL prefix if present
            if 'data:image' in base64_string:
                base64_string = base64_string.split(',')[1]
            
            # Decode base64 to image
            image_data = base64.b64decode(base64_string)
            image = Image.open(io.BytesIO(image_data))
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            return image
        except Exception as e:
            print(f"Error extracting face from base64: {e}")
            return None
    
    def detect_and_extract_face(self, image):
        """Detect and extract face from PIL image"""
        try:
            # Detect face
            face_tensor = self.mtcnn(image)
            
            if face_tensor is not None:
                return face_tensor
            else:
                print("No face detected in the image")
                return None
                
        except Exception as e:
            print(f"Error detecting face: {e}")
            return None
    
    def get_face_embedding(self, base64_image):
        """Get face embedding from base64 image"""
        try:
            # Extract face from base64
            image = self.extract_face_from_base64(base64_image)
            if image is None:
                return None
            
            # Detect and extract face
            face_tensor = self.detect_and_extract_face(image)
            if face_tensor is None:
                return None
            
            # Get embedding
            with torch.no_grad():
                face_tensor = face_tensor.unsqueeze(0)  # Add batch dimension
                embedding = self.resnet(face_tensor)
                embedding = embedding.detach().cpu().numpy()
                
            return embedding.flatten()
            
        except Exception as e:
            print(f"Error getting face embedding: {e}")
            return None
    
    def calculate_similarity(self, embedding1, embedding2):
        """Calculate cosine similarity between two embeddings"""
        try:
            if embedding1 is None or embedding2 is None:
                return 0.0
            
            # Calculate cosine similarity using our custom function
            similarity = cosine_similarity(embedding1.flatten(), embedding2.flatten())
            return float(similarity)
            
        except Exception as e:
            print(f"Error calculating similarity: {e}")
            return 0.0
    
    def is_same_person(self, embedding1, embedding2, threshold=0.6):
        """Check if two embeddings belong to the same person"""
        similarity = self.calculate_similarity(embedding1, embedding2)
        return similarity >= threshold, similarity
    
    def save_face_image(self, base64_image, filename):
        """Save face image to disk"""
        try:
            image = self.extract_face_from_base64(base64_image)
            if image is None:
                return False
            
            # Create uploads directory if it doesn't exist
            upload_dir = 'static/uploads'
            os.makedirs(upload_dir, exist_ok=True)
            
            # Save image
            filepath = os.path.join(upload_dir, filename)
            image.save(filepath, 'JPEG', quality=85)
            
            return filepath
            
        except Exception as e:
            print(f"Error saving face image: {e}")
            return None

# Global instance
face_recognition = FaceRecognition()
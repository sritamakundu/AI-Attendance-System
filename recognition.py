"""DeepFace embedding and matching helpers.
Embeddings are biometric data: protect the database and use consented images only.
"""
import numpy as np
from deepface import DeepFace
from db import get_embeddings

MODEL="ArcFace"
DETECTOR="opencv"
# ArcFace embeddings are normalized here for cosine distance.
def _embedding(rgb):
    bgr=rgb[:,:,::-1].copy()
    reps=DeepFace.represent(img_path=bgr,model_name=MODEL,detector_backend=DETECTOR,
                            enforce_detection=True,normalization="ArcFace")
    if not reps: raise ValueError("No face found in image.")
    # Enrollment accepts exactly one face to avoid ambiguous identity registration.
    if len(reps)!=1: raise ValueError("Please upload an image containing exactly one face.")
    v=np.asarray(reps[0]["embedding"],dtype=np.float32)
    return v/(np.linalg.norm(v)+1e-12)

def enroll_image(pil_image):
    return _embedding(np.asarray(pil_image.convert("RGB")))

def recognize_faces(rgb_image,threshold=0.68):
    """Find faces in image, embed each, and return best roster proposal per face.
    threshold is cosine distance; lower is closer. Tune using local validation data.
    """
    roster=get_embeddings()
    if not roster: return []
    bgr=rgb_image[:,:,::-1].copy()
    faces=DeepFace.extract_faces(img_path=bgr,detector_backend=DETECTOR,enforce_detection=False,
                                align=True)
    results=[]
    for face in faces:
        area=np.asarray(face["face"])
        # extract_faces returns normalized float RGB face crops; convert to uint8
        crop=np.clip(area*255,0,255).astype(np.uint8) if area.max()<=1.0 else area.astype(np.uint8)
        try:
            v=_embedding(crop)
        except Exception:
            results.append({"student_id":None,"name":"Unknown","score":"—"}); continue
        best=None; bestdist=9
        for s in roster:
            e=s["embedding"]; e=e/(np.linalg.norm(e)+1e-12)
            d=float(1-np.dot(v,e))
            if d<bestdist: bestdist=d; best=s
        if best and bestdist<=threshold:
            results.append({"student_id":best["student_id"],"name":best["name"],"score":round(bestdist,4)})
        else: results.append({"student_id":None,"name":"Unknown","score":round(bestdist,4)})
    return results

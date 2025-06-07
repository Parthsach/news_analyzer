# image_utils.py

from PIL import Image
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
import io
import cv2
import numpy as np
import exifread

def analyze_image(file: bytes, lang: str = "eng", enable_face_detection: bool = True):
    results = {}

    # 1️⃣ Load the image with PIL
    image = Image.open(io.BytesIO(file))
    results["format"] = image.format
    results["size"] = image.size
    results["mode"] = image.mode

    # 2️⃣ OCR Text Extraction
    try:
        text = pytesseract.image_to_string(image, lang=lang)
        results["text"] = text.strip() if text else "No text detected."
    except Exception as e:
        results["text"] = f"OCR error: {str(e)}"

    # 3️⃣ EXIF Metadata
    try:
        exif_file = io.BytesIO(file)
        exif_file.seek(0)
        tags = exifread.process_file(exif_file)
        exif_data = {tag: str(tags[tag]) for tag in tags.keys()}
        results["exif"] = exif_data if exif_data else "No EXIF metadata found."
    except Exception as e:
        results["exif"] = f"EXIF extraction error: {str(e)}"

    # 4️⃣ Object Detection (Optional)
    if enable_face_detection:
        try:
            np_image = np.array(image.convert("RGB"))
            gray = cv2.cvtColor(np_image, cv2.COLOR_RGB2GRAY)
            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
            faces = face_cascade.detectMultiScale(gray, 1.3, 5)
            results["faces_detected"] = len(faces)
        except Exception as e:
            results["faces_detected"] = f"Face detection error: {str(e)}"
    else:
        results["faces_detected"] = "Skipped."

    return results

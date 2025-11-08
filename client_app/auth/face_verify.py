import cv2
import base64
import numpy as np

try:
    import face_recognition
    FACE_RECOG_AVAILABLE = True
except Exception:
    FACE_RECOG_AVAILABLE = False

    # Lightweight fallback for face_recognition: use OpenCV face detector for
    # locations and return a dummy 128-d zero encoding for demos so client flows
    # that expect an encoding can continue. This is INSECURE and only for local
    # demonstration/testing when dlib/face_recognition are unavailable.
    class _FallbackFaceRecog:
        @staticmethod
        def face_encodings(rgb_frame):
            # Return a single zero-vector encoding if a face is detected, else []
            gray = cv2.cvtColor(rgb_frame, cv2.COLOR_RGB2GRAY)
            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            faces = face_cascade.detectMultiScale(gray, 1.1, 4)
            if len(faces) == 0:
                return []
            return [np.zeros(128, dtype=float)]

        @staticmethod
        def face_locations(rgb_small_frame):
            # rgb_small_frame is expected possibly scaled; convert back to BGR for OpenCV
            try:
                bgr = cv2.cvtColor(rgb_small_frame, cv2.COLOR_RGB2BGR)
            except Exception:
                bgr = rgb_small_frame
            gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            faces = face_cascade.detectMultiScale(gray, 1.1, 4)
            # Convert to (top,right,bottom,left)
            locations = []
            for (x, y, w, h) in faces:
                locations.append((y, x+w, y+h, x))
            return locations

    face_recognition = _FallbackFaceRecog()


def bgr_to_jpeg_base64(img_bgr, quality: int = 90) -> str | None:
    if img_bgr is None:
        return None
    ok, buf = cv2.imencode(".jpg", img_bgr, [int(cv2.IMWRITE_JPEG_QUALITY), quality])
    if not ok:
        return None
    return base64.b64encode(buf.tobytes()).decode("ascii")

def capture_face_encoding(frame):
    """Capture face encoding from a video frame"""
    try:
        # Convert BGR to RGB for face_recognition library
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Find face encodings
        face_encodings = face_recognition.face_encodings(rgb_frame)
        
        if face_encodings:
            return face_encodings[0].tolist()  # Convert to list for JSON serialization
        else:
            return None
    except Exception as e:
        print(f"Error capturing face encoding: {e}")
        return None

def detect_faces(frame):
    """Detect faces in a frame and return their locations"""
    try:
        # Try face_recognition library first
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_small_frame)
        # Scale back up face locations
        face_locations = [(top*4, right*4, bottom*4, left*4) for (top, right, bottom, left) in face_locations]
        return face_locations
    except ImportError:
        # Fallback to OpenCV
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        faces = face_cascade.detectMultiScale(gray, 1.1, 4)
        # Convert to same format as face_recognition
        face_locations = [(y, x+w, y+h, x) for (x, y, w, h) in faces]
        return face_locations
    except Exception as e:
        print(f"Error detecting faces: {e}")
        return []

def draw_face_rectangles(frame, face_locations):
    """Draw rectangles around detected faces"""
    display_frame = frame.copy()
    for (top, right, bottom, left) in face_locations:
        cv2.rectangle(display_frame, (left, top), (right, bottom), (0, 255, 0), 2)
        cv2.putText(display_frame, "Face Detected", (left, top-10), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
    return display_frame

def capture_face_photo():
    """Capture a photo using the camera with face detection"""
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        return None, "Could not access camera"
    
    captured_frame = None
    face_encoding = None
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
                
            # Detect faces
            face_locations = detect_faces(frame)
            
            # Draw face rectangles
            display_frame = draw_face_rectangles(frame, face_locations)
            
            cv2.imshow("Face Capture - Press SPACE to capture, ESC to cancel", display_frame)
            
            key = cv2.waitKey(1) & 0xFF
            if key == ord(' '):  # Space to capture
                if face_locations:
                    captured_frame = frame.copy()
                    face_encoding = capture_face_encoding(frame)
                    break
                else:
                    print("No face detected. Please position your face in the camera.")
            elif key == 27:  # ESC to cancel
                break
                
    except Exception as e:
        print(f"Error during face capture: {e}")
        return None, f"Error during capture: {e}"
    finally:
        cap.release()
        cv2.destroyAllWindows()
    
    if captured_frame is not None and face_encoding is not None:
        # Convert to base64
        face_data = bgr_to_jpeg_base64(captured_frame)
        return {
            "face_data": face_data,
            "face_encoding": face_encoding
        }, None
    else:
        return None, "No face captured"
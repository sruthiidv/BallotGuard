import cv2
import face_recognition
import base64


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
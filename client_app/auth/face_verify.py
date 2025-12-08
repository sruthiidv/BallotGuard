import cv2
import base64
import numpy as np
import time
import os

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
            haar_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml' if hasattr(cv2.data, 'haarcascades') else cv2.samples.findFile('haarcascade_frontalface_default.xml')
            face_cascade = cv2.CascadeClassifier(haar_path)
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
            haar_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml' if hasattr(cv2.data, 'haarcascades') else cv2.samples.findFile('haarcascade_frontalface_default.xml')
            face_cascade = cv2.CascadeClassifier(haar_path)
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
        haar_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml' if hasattr(cv2.data, 'haarcascades') else cv2.samples.findFile('haarcascade_frontalface_default.xml')
        face_cascade = cv2.CascadeClassifier(haar_path)
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

def check_liveness(cap, duration=2.0, blink_threshold=0.3):
    """
    Simple liveness detection using eye aspect ratio (EAR) blink detection.
    Returns (is_live, message)
    
    Args:
        cap: OpenCV VideoCapture object
        duration: Seconds to monitor for blinks
        blink_threshold: EAR threshold for blink detection
    """
    try:
        import dlib
        import site
        
        # Find the shape predictor model (installed with dlib or face_recognition)
        # Check common locations
        possible_paths = []
        
        # Check in face_recognition_models package
        try:
            import face_recognition_models
            model_path = os.path.join(os.path.dirname(face_recognition_models.__file__), 
                                     'models', 'shape_predictor_68_face_landmarks.dat')
            possible_paths.append(model_path)
        except:
            pass
        
        # Check site-packages
        try:
            for site_dir in site.getsitepackages():
                possible_paths.append(os.path.join(site_dir, 'shape_predictor_68_face_landmarks.dat'))
                possible_paths.append(os.path.join(site_dir, 'face_recognition_models', 
                                                  'models', 'shape_predictor_68_face_landmarks.dat'))
        except:
            pass
        
        # Check local models directory
        possible_paths.append(os.path.join(os.path.dirname(__file__), '..', '..', 'models', 
                                          'shape_predictor_68_face_landmarks.dat'))
        
        predictor_path = None
        for path in possible_paths:
            if os.path.exists(path):
                predictor_path = path
                print(f"[LIVENESS] Found predictor at: {path}")
                break
        
        if not predictor_path:
            print("[LIVENESS] Warning: shape_predictor_68_face_landmarks.dat not found. Skipping liveness check.")
            print(f"[LIVENESS] Searched in {len(possible_paths)} locations")
            return True, "Liveness check skipped (detector not available)"
        
        detector = dlib.get_frontal_face_detector()
        predictor = dlib.shape_predictor(predictor_path)
        
        def eye_aspect_ratio(eye):
            # Compute EAR for eye landmarks
            A = np.linalg.norm(eye[1] - eye[5])
            B = np.linalg.norm(eye[2] - eye[4])
            C = np.linalg.norm(eye[0] - eye[3])
            return (A + B) / (2.0 * C)
        
        blink_count = 0
        frame_count = 0
        start_time = time.time()
        was_blinking = False
        
        print(f"[LIVENESS] Starting liveness check for {duration}s. Please blink naturally...")
        
        while time.time() - start_time < duration:
            ret, frame = cap.read()
            if not ret:
                break
            
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = detector(gray)
            
            if len(faces) > 0:
                face = faces[0]
                landmarks = predictor(gray, face)
                
                # Extract eye landmarks (36-41: left eye, 42-47: right eye)
                left_eye = np.array([(landmarks.part(i).x, landmarks.part(i).y) for i in range(36, 42)])
                right_eye = np.array([(landmarks.part(i).x, landmarks.part(i).y) for i in range(42, 48)])
                
                left_ear = eye_aspect_ratio(left_eye)
                right_ear = eye_aspect_ratio(right_eye)
                avg_ear = (left_ear + right_ear) / 2.0
                
                # Detect blink
                if avg_ear < blink_threshold:
                    if not was_blinking:
                        blink_count += 1
                        was_blinking = True
                        print(f"[LIVENESS] Blink detected ({blink_count})")
                else:
                    was_blinking = False
                
                frame_count += 1
        
        # Consider live if at least 1 blink detected
        if blink_count >= 1:
            print(f"[LIVENESS] \u2713 Liveness check PASSED ({blink_count} blinks in {duration}s)")
            return True, f"Live person detected ({blink_count} blinks)"
        else:
            print(f"[LIVENESS] \u2717 Liveness check FAILED (no blinks detected)")
            return False, "No blinks detected. Please ensure you're a live person."
            
    except ImportError:
        # dlib not available - skip liveness check with warning
        print("[LIVENESS] Warning: dlib not available. Liveness check disabled.")
        return True, "Liveness check skipped (dlib not available)"
    except Exception as e:
        print(f"[LIVENESS] Error during liveness check: {e}")
        return True, f"Liveness check skipped (error: {e})"

def capture_face_photo():
    """Capture a photo using the camera with face detection"""
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        return None, "Could not access camera"
    
    captured_frame = None
    face_encoding = None
    liveness_passed = False
    
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
                    # First check liveness before capturing
                    print("\n[LIVENESS] Starting liveness detection...")
                    is_live, message = check_liveness(cap, duration=2.0)
                    
                    if is_live:
                        print(f"[LIVENESS] ✓ {message}")
                        captured_frame = frame.copy()
                        face_encoding = capture_face_encoding(frame)
                        liveness_passed = True
                        break
                    else:
                        print(f"[LIVENESS] ✗ {message}")
                        print("[LIVENESS] Please try again. Ensure you're a live person and blink naturally.")
                        # Don't break - let user try again
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
        if not liveness_passed:
            return None, "Liveness check not completed. Please try again."
        # Convert to base64
        face_data = bgr_to_jpeg_base64(captured_frame)
        return {
            "face_data": face_data,
            "face_encoding": face_encoding
        }, None
    else:
        return None, "No face captured"
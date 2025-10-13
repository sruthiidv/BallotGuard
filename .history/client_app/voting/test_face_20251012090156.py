import face_recognition
import sys
print(sys.executable)


image = face_recognition.load_image_file("your_image.jpg")  # Replace with a real image path
face_locations = face_recognition.face_locations(image)

print("Found {} face(s) in this photograph.".format(len(face_locations)))

import cv2
print("Trying to open camera")
try:
    cap = cv2.VideoCapture(0)
    print("Opened:", cap.isOpened())
    if cap.isOpened():
        ret, frame = cap.read()
        print("Read frame:", ret)
    cap.release()
except Exception as e:
    print("Exception:", e)

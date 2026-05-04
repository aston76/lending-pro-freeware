import multiprocessing
import sys
import base64

def camera_worker(title, queue):
    import cv2
    try:
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            queue.put({"success": False, "error": "No camera detected"})
            return
            
        cv2.namedWindow(title, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(title, 800, 600)
        captured = None
        while True:
            ret, frame = cap.read()
            if not ret: break
            df = frame.copy()
            cv2.putText(df, "Press SPACE to Capture, ESC to Cancel", (20, 40), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            cv2.imshow(title, df)
            
            k = cv2.waitKey(1)
            if k == 27:
                break
            elif k == 32:
                captured = frame
                break
        
        cap.release()
        cv2.destroyWindow(title)
        cv2.waitKey(1)
        
        if captured is not None:
            _, buffer = cv2.imencode('.png', captured)
            b64_str = base64.b64encode(buffer).decode('utf-8')
            queue.put({"success": True, "b64": b64_str})
        else:
            queue.put({"success": False, "error": "Cancelled"})
    except Exception as e:
        queue.put({"success": False, "error": str(e)})

if __name__ == '__main__':
    multiprocessing.set_start_method('spawn')
    q = multiprocessing.Queue()
    p = multiprocessing.Process(target=camera_worker, args=("Test", q))
    p.start()
    p.join()
    res = q.get()
    print("Result:", res['success'])

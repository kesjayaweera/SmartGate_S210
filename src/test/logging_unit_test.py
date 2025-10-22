from datetime import datetime
import os
import cv2

logs = []
LOG_ID = 0

def log_event(animal_list, frame, camera_id):
    global LOG_ID
    
    img_dir = os.path.join("logs", "image_logs")    
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    file_name = os.path.join(img_dir, f"{LOG_ID}_{timestamp}.jpg")
    
    cv2.imwrite(file_name, frame)
    
    log_entry = {
        "time": timestamp,
        "animal_type": animal_list,
        "LOG_ID": LOG_ID,
        "file_name": file_name,
        "camera_id": camera_id
    }

    LOG_ID += 1
    logs.append(log_entry)

    log_path = os.path.join("logs", "logs.txt")
    with open(log_path, "a") as f:
        f.write(f"{timestamp} | {animal_list} | {LOG_ID} | {file_name} | {camera_id}\n")

log_event(['cat', 'dog'], cv2.imread(os.path.join("logs", "image_logs", "testimage.png")), camera_id=0)

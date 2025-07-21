import numpy as np
import cv2
from ultralytics import YOLO # skeleton extraction by YOLO deep learning algorithms

def extract_keypoints(modelname,color_image):
    model = YOLO(modelname)

    results = model(color_image)
    high_conf_boxes = []

    all_keypoints = []
    all_keypoints_dict = []
    for r in results:
        boxes = r.boxes
        keypoints = r.keypoints
        # identify boxes with confined higher than 70%
        for box in boxes:
            if box.conf >= 0.7:
                high_conf_boxes.append(box)

        # take only first box --> only one subject
        if high_conf_boxes:
            box = high_conf_boxes[0]
            #b = box.xyxy[0].to('cpu').detach().numpy().copy()
            #c = box.cls

            # trovo i keypoints
            for keypoint in keypoints:
                k = keypoint.xy[0].to('cpu').detach().numpy().copy()
                # round the points to the nearest pixel
                k = np.round(k)
                all_keypoints.append(k)
                ### dictionary
                keypoints_dict={
                    "nose": k[0],
                    "left eye": k[1],
                    "right eye": k[2],
                    "left ear": k[3],
                    "right ear": k[4],
                    "left shoulder": k[5],
                    "right shoulder": k[6],
                    "left elbow": k[7],
                    "right elbow": k[8],
                    "left wrist": k[9],
                    "right wrist": k[10],
                    "left hip": k[11],
                    "right hip": k[12],
                    "left knee": k[13],
                    "right knee": k[14],
                    "left ankle": k[15],
                    "right ankle": k[16]
                }
                all_keypoints_dict.append(keypoints_dict)


    return all_keypoints,all_keypoints_dict

def show_skeleton(skeleton_dicts,color_image):

    for skeleton_dict in skeleton_dicts:
        for key, value in skeleton_dict.items():
            #print(f"Key: {key}, Value: {value}")

            if value[0] != 0 and value[1] != 0 and not(np.isnan(value[0])) and not(np.isnan(value[1])):

                if "left" in key:
                    cv2.circle(color_image, (int(value[0]), int(value[1])),
                               2, (0, 255, 0), thickness=2, lineType=cv2.LINE_4)

                    '''cv2.putText(color_image, text=key, org=(int(value[0]+10), int(value[1]+10)),
                                fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=0.7, color=(0, 0, 0),
                                thickness=2, lineType=cv2.LINE_4)'''
                elif "right" in key:
                    cv2.circle(color_image, (int(value[0]), int(value[1])),
                               2, (0, 255, 0), thickness=2, lineType=cv2.LINE_4)

                    '''cv2.putText(color_image, text=key, org=(int(value[0] - 90), int(value[1]-20)),
                                fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=0.7, color=(0, 0, 0),
                                thickness=2, lineType=cv2.LINE_4)'''
                else:
                    cv2.circle(color_image, (int(value[0]), int(value[1])),
                               2, (0, 255, 0), thickness=2, lineType=cv2.LINE_4)

                    '''cv2.putText(color_image, text=key, org=(int(value[0]), int(value[1])),
                                fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=0.7, color=(0, 0, 0),
                                thickness=2, lineType=cv2.LINE_4)'''

    return color_image

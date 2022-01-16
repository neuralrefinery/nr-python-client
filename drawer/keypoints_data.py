

coco_keypoints = [ "nose", # 0
                     "left_eye", # 1
                     "right_eye", # 2 
                     "left_ear", # 3
                     "right_ear", # 4
                     "left_shoulder", # 5
                     "right_shoulder", # 6
                     "left_elbow", # 7
                     "right_elbow", # 8
                     "left_wrist", # 9
                     "right_wrist", # 10
                     "left_hip", # 11
                     "right_hip", # 12
                     "left_knee", # 13
                     "right_knee", # 14
                     "left_ankle", # 15
                     "right_ankle" # 16
                     ]

coco_pairs = [ (0,1),   # 0 nose to left_eye 
               (0,2),   # 1 nose to right_eye
               (1,3),   # 2 left_eye to left_ear
               (2,4),   # 3 right_eye to right_ear
               (5,6),   # 4 left_shoulder to right_shoulder
               (5,7),   # 5 left_shoulder to left_elbow
               (6,8),   # 6 right_shoulder to right_elbow
               (7,9),   # 7 left_elbow to left_wrist
               (8,10),  # 8 right_elbow to right_wrist
               (11,12), # 9 left_hip to right_hip
               (11,13), # 10 left_hip to left_knee
               (12,14), # 11 right_hip to right_knee
               (13,15), # 12 left_knee to left_ankle
               (14,16)  # 13 right_knee to right_ankle
            ]
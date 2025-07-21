import os
from RECORD_FUNCTIONS import *

def create_dir(path):
    try:
        os.makedirs(path, exist_ok=True)
        print(f"Folder '{path}' created successfully.")
    except Exception as e:
        print(f"Error creating folder '{path}': {e}")

# define root folder name
root_folder = ""
create_dir(root_folder)
# define recording folder name

subject_name = " "
distance = " "
light_conditions = " "
subjectpose = " "
BPM = " "

testconditions = "d_"+distance+"_"+light_conditions+"_"+subjectpose+"_"+BPM

create_dir(root_folder+"\\"+subject_name)
create_dir(root_folder+"\\"+subject_name+"\\"+testconditions)

# demo utilisation of record function
pwts = root_folder+"\\"+subject_name+"\\"+testconditions

record(resolution_level=2,fps_level=3,NFRAMES=15*120,pwts=pwts,tag="") ##




import pyrealsense2 as rs # necessary library to use the RealSense
from skeleton_functions import *
import time
import pickle

def depth_instrinsics_to_dict(depth_intrinsic):
    '''

    :param depth_intrinsic: depth intrinsic params
    :return: the depth intrinsic params saved to a dictionary
    '''
    dict_intrinsic = {
        "width": depth_intrinsic.width,
        "height": depth_intrinsic.height,
        "ppx": depth_intrinsic.ppx,
        "ppy":depth_intrinsic.ppy,
        "fx": depth_intrinsic.fx,
        "fy": depth_intrinsic.fy,
        "model": depth_intrinsic.model,
        "coeff": depth_intrinsic.coeffs,
    }

    return dict_intrinsic

def dict_instrinsic_to_depth(dict_instrinsic):
    '''

    :param dict_instrinsic: dictionary of depth instrinsics
    :return: depth instrinsics format
    '''
    depth_intrinsic = rs.pyrealsense2.intrinsics()
    depth_intrinsic.width = dict_instrinsic["width"]
    depth_intrinsic.height = dict_instrinsic["height"]
    depth_intrinsic.ppx = dict_instrinsic["ppx"]
    depth_intrinsic.ppy = dict_instrinsic["ppy"]
    depth_intrinsic.fx = dict_instrinsic["fx"]
    depth_intrinsic.fy = dict_instrinsic["fy"]
    depth_intrinsic.model = dict_instrinsic["model"]
    depth_intrinsic.coeffs = dict_instrinsic["coeff"]

    return depth_intrinsic

def record(resolution_level=0,fps_level=2,NFRAMES=30,pwts="",tag=""):
    '''
    Basic function for the recording from the Intel RealSense Camera
    :param resolution_level: default is 0 corresponding to maximum resolution (1280x800 RGB, 1280x720 DEPTH);
                             possible values are 0 (max resolution) to 5 (min resolution); check the datasheet
                             for further information on the possible resolution
    :param fps_level: default is 2 which corresponds to 30 frames per second; possible values are 0 (max fps of 90)
                      to 4 (min fps of 5); !! with max resolution only fps_level 2 to 4 are available
    :param NFRAMES:  Number of frames to record; default is 30; the recording can be stopped before the number
                     of passed frames is reached by pressing 'q'; passing np.inf can be an option to have a
                     dynamic recording where the number of frames is not known a priori
    :param pwts: path where to save the color and depth video strem and the depth instrinsics
    :param tag: by default the function save the recordings with pwts+"\\color_data"+tag+".npy" ,
                pwts+"\\depth_data"+tag+".npy" , pwts+"\\depth_instrinsics"+tag+".npy"
    :return:
        color_data [NFRAMES,WIDTH,HEIGHT,RGB_channels] --> recorded color frames
        depth_data [NFRAMES,WIDTH,HEIGHT] --> recorded depth frames
        depth_instrinsics --> values for focal lenghts along x and y for further point cloud extraction
    '''

    # possible resolutions and fps given by the intel RS D455 (by datasheet)
    possible_RGBresolutions = [[1280, 800], [848, 480], [640, 480], [640, 360], [480, 270], [424, 240]]
    possible_Dresolutions = [[1280, 720], [848, 480], [640, 480], [640, 360], [480, 270], [424, 240]]
    possible_frame_rate = [90, 60, 30, 15, 5]

    # check if fps level and resolution are good
    if fps_level<2 and resolution_level==0:
        print("You can not obtain that level of fps with the passed resolution. Either lower the resolution or fps. ")
        return None

    # Create a pipeline
    pipeline = rs.pipeline()

    # Create a config and configure the pipeline to stream
    #  different resolutions of color and depth streams
    config = rs.config()

    # Get device product line for setting a supporting resolution
    pipeline_wrapper = rs.pipeline_wrapper(pipeline)
    pipeline_profile = config.resolve(pipeline_wrapper)
    device = pipeline_profile.get_device()

    config.enable_stream(rs.stream.depth, possible_Dresolutions[resolution_level][0],
                         possible_Dresolutions[resolution_level][1], rs.format.z16, possible_frame_rate[fps_level])
    config.enable_stream(rs.stream.color, possible_RGBresolutions[resolution_level][0],
                         possible_RGBresolutions[resolution_level][1], rs.format.bgr8, possible_frame_rate[fps_level])

    # Start streaming
    profile = pipeline.start(config)

    # Getting the depth sensor's depth scale (see rs-align example for explanation)
    depth_sensor = profile.get_device().first_depth_sensor()
    depth_scale = depth_sensor.get_depth_scale()

    # Create an align object
    # rs.align allows us to perform alignment of depth frames to others frames
    # The "align_to" is the stream type to which we plan to align depth frames.
    align_to = rs.stream.color
    align = rs.align(align_to)
    n = 0

    color_data = []
    depth_data = []
    try:
        while n < NFRAMES:
            # Get frameset of color and depth
            frames = pipeline.wait_for_frames()

            # Align the depth frame to color frame
            aligned_frames = align.process(frames)

            # Get aligned frames
            aligned_depth_frame = aligned_frames.get_depth_frame()  # aligned_depth_frame is a 640x480 depth image
            color_frame = aligned_frames.get_color_frame()

            depth_intrinsics = rs.video_stream_profile(aligned_depth_frame.profile).get_intrinsics()
            # color_intrinsics = rs.video_stream_profile(color_frame.profile).get_intrinsics()

            # Validate that both frames are valid
            if not aligned_depth_frame or not color_frame:
                continue

            color_data.append( np.array(color_frame.get_data()))
            depth_data.append(np.array(aligned_depth_frame.get_data())*depth_scale) # multiplying by depth scale to obtain meters

            depth_image = np.asanyarray(aligned_depth_frame.get_data())
            color_image = np.asanyarray(color_frame.get_data())

            depth_colormap = cv2.applyColorMap(cv2.convertScaleAbs(depth_image, alpha=0.03), cv2.COLORMAP_JET)

            # visualisation with cv2
            cv2.imshow('RGB', color_image)
            cv2.imshow('Depth', depth_colormap)
            key = cv2.waitKey(1)
            # Press esc or 'q' to close the image window
            if key & 0xFF == ord('q') or key == 27:
                cv2.destroyAllWindows()
                break
            n = n + 1
    finally:
        pipeline.stop()

    cv2.destroyAllWindows()
    color_data = np.array(color_data)
    depth_data = np.array(depth_data)

    print('Saving recording..')
    np.save(pwts+"\\color_data" + tag + ".npy", color_data)
    np.save(pwts+"\\depth_data" + tag + ".npy", depth_data)

    depth_intrinsics_dict = depth_instrinsics_to_dict(depth_intrinsics)
    with open(pwts+"\\depth_intrinsics_dict"+tag+".pickle", 'wb') as handle:
        pickle.dump(depth_intrinsics_dict, handle)

    return depth_intrinsics,color_data,depth_data

def record_YOLO(resolution_level=0,fps_level=2,NFRAMES=30,pwts="",tag="",yolo="yolo11n-pose.pt"):
    '''
    Record function that extracts online the skeleton of the subject in the scene. Given the online nature of
    the recording, the passed fps will be probably different from the wanted one; therefore actual_fps it is
    also an output of this function
    :param resolution_level: same as record()
    :param fps_level: same as record()
    :param NFRAMES: same as record()
    :param pwts: same as record()
    :param tag: same as record()
    :param yolo: name of the yolo architecture
    :return: same as record() + skeleton 3d coordinates  + actual fps
    '''

    # possible resolutions and fps given by the intel RS D455 (by datasheet)
    possible_RGBresolutions = [[1280, 800], [848, 480], [640, 480], [640, 360], [480, 270], [424, 240]]
    possible_Dresolutions = [[1280, 720], [848, 480], [640, 480], [640, 360], [480, 270], [424, 240]]
    possible_frame_rate = [90, 60, 30, 15, 5]

    # check if fps level and resolution are good
    if fps_level<2 and resolution_level==0:
        print("You can not obtain that level of fps with the passed resolution. Either lower the resolution or fps. ")
        return None

    # YOLO MODEL
    model = YOLO(yolo)

    # Create a pipeline
    pipeline = rs.pipeline()

    # Create a config and configure the pipeline to stream
    #  different resolutions of color and depth streams
    config = rs.config()

    # Get device product line for setting a supporting resolution
    pipeline_wrapper = rs.pipeline_wrapper(pipeline)
    pipeline_profile = config.resolve(pipeline_wrapper)
    device = pipeline_profile.get_device()

    config.enable_stream(rs.stream.depth, possible_Dresolutions[resolution_level][0],
                         possible_Dresolutions[resolution_level][1], rs.format.z16, possible_frame_rate[fps_level])
    config.enable_stream(rs.stream.color, possible_RGBresolutions[resolution_level][0],
                         possible_RGBresolutions[resolution_level][1], rs.format.bgr8, possible_frame_rate[fps_level])

    # Start streaming
    profile = pipeline.start(config)

    # Getting the depth sensor's depth scale (see rs-align example for explanation)
    depth_sensor = profile.get_device().first_depth_sensor()
    depth_scale = depth_sensor.get_depth_scale()

    # Create an align object
    # rs.align allows us to perform alignment of depth frames to others frames
    # The "align_to" is the stream type to which we plan to align depth frames.
    align_to = rs.stream.color
    align = rs.align(align_to)
    n = 0
    keypoints_acquired_pc = []
    color_data = []
    depth_data = []
    fps = []
    try:
        while n < NFRAMES:
            start = time.time_ns()
            # Get frameset of color and depth
            frames = pipeline.wait_for_frames()
            # Align the depth frame to color frame
            aligned_frames = align.process(frames)

            # Get aligned frames
            aligned_depth_frame = aligned_frames.get_depth_frame()  # aligned_depth_frame is a 640x480 depth image
            color_frame = aligned_frames.get_color_frame()

            depth_intrinsics = rs.video_stream_profile(aligned_depth_frame.profile).get_intrinsics()
            # color_intrinsics = rs.video_stream_profile(color_frame.profile).get_intrinsics()

            # Validate that both frames are valid
            if not aligned_depth_frame or not color_frame:
                continue

            color_data.append(np.array(color_frame.get_data()))
            depth_data.append(np.array(aligned_depth_frame.get_data()) * depth_scale) # multiplying by depth scale to obtain meters

            depth_image = np.asanyarray(aligned_depth_frame.get_data())
            color_image = np.asanyarray(color_frame.get_data())

            all_keypoints, all_keypoints_dict = extract_keypoints(model, color_image)

            all_keypoints_pointcloud = []
            for keypoints in all_keypoints:
                keypoints_pointcloud = pointcloud_keypoints(depth_intrinsics, depth_image, keypoints)

                all_keypoints_pointcloud.append(keypoints_pointcloud)

            if len(all_keypoints_pointcloud)==0:
                all_keypoints_pointcloud.append(np.full((17,3), np.nan))

            keypoints_acquired_pc.append(all_keypoints_pointcloud)

            depth_colormap = cv2.applyColorMap(cv2.convertScaleAbs(depth_image, alpha=0.03), cv2.COLORMAP_JET)

            show_skeleton(all_keypoints_dict, color_image)
            # visualisation with cv2
            cv2.imshow('RGB', color_image)
            cv2.imshow('Depth', depth_colormap)
            key = cv2.waitKey(25)
            # Press esc or 'q' to close the image window
            if key & 0xFF == ord('q') or key == 27:
                cv2.destroyAllWindows()
                break
            n = n + 1
            fps.append(1/((time.time_ns()-start)*1e-9))
    finally:
        pipeline.stop()

    cv2.destroyAllWindows()
    color_data = np.array(color_data)
    depth_data = np.array(depth_data)
    keypoints_acquired_pc = np.array(keypoints_acquired_pc)
    # ci sono problemi con persone multiple pero ok
    # ci sono dei problemi quando non detecta ....
    print('Saving recording...')
    np.save(pwts+"\\color_data" + tag + ".npy", color_data)
    np.save(pwts+"\\depth_data" + tag + ".npy", depth_data)
    depth_intrinsics_dict = depth_instrinsics_to_dict(depth_intrinsics)
    with open(pwts + "\\depth_intrinsics_dict" + tag + ".pickle", 'wb') as handle:
        pickle.dump(depth_intrinsics_dict, handle)
    np.save(pwts+"\\keypoints_acquired_pc" + tag + ".npy", keypoints_acquired_pc)
    np.save(pwts+"\\fps_vector" + tag + ".npy",fps)

    return depth_intrinsics,color_data,depth_data,keypoints_acquired_pc,fps






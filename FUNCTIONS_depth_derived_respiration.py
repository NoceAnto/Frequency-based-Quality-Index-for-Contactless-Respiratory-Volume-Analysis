from skeleton_functions import *
import os

def clean_and_interpolate(series):
    """
    Remove zero and NaN values from a time series and interpolate the values with a simple linear interpolator.

    Parameters:
    series (pd.Series): The input time series with potential zero and NaN values.

    Returns:
    pd.Series: The cleaned and interpolated time series.
    """
    # Replace zero values with NaN

    series = series.replace(0, np.nan)

    # Interpolate the NaN values using linear interpolation
    interpolated_series = series.interpolate(method='linear')

    return interpolated_series

def filter_outlier(matrix, excludeNan=True, excludezero=True,exclude_percentile=True):
    '''
    FUNCTION TO FILTER OUT THE OUTLIER IN A SPECIFIED MATRIX ROI
    :param matrix: matrix of values usually corresponfing to the ROI
    :param excludeNan: True to report a newmatrix vector without the Nan values
    :param excludezero: True to report a newmatrix vector without the zero values
    :param exclude_percentile: True to report a newmatrix vector without the extreme cases values
    :return:
    '''
    if excludeNan:
        newmatrix = matrix[~np.isnan(matrix)]
        if len(newmatrix) == 0:
            corrupted = True
            return newmatrix,corrupted
    # no zeros
    if excludezero:
        newmatrix = newmatrix[newmatrix != 0]
        if len(newmatrix) == 0:
            corrupted = True
            return newmatrix,corrupted

    # Calculate the 0.5 and 99.5 percentiles
    if exclude_percentile:
        percentile_05 = np.percentile(newmatrix, 0.05)
        percentile_995 = np.percentile(newmatrix, 99.5)
        # Filter values based on percentiles
        newmatrix = newmatrix[(newmatrix >= percentile_05) & (newmatrix <= percentile_995)]
        if len(newmatrix) == 0:
            corrupted = True
            return newmatrix,corrupted

    tot_pixels = len(matrix)
    perc_remained_pixels = float(np.size(newmatrix))/float(tot_pixels)

    if perc_remained_pixels<0.8:
        corrupted = True
    else:
        corrupted = False

    return newmatrix, corrupted

def show_mask(A,B,C,D,depth_image,color=(0, 255, 255),filename='image.png'):
    '''
    FUNCTION TO PLOT THE ROI MASK COMPOSED OF CORNER A,B,C,D
    :param A: (Ax,Ay)
    :param B: (Bx,By)
    :param C: (Cx,Cy)
    :param D: (Dx,Dy)
    :param depth_image: depth image
    :param color: what color for the mask
    :param filename: path where to save
    :return:
    '''
    poly_pts = np.array([A, B, C, D], dtype=np.int32)
    cv2.polylines(depth_image, [poly_pts], True, color)
    cv2.fillPoly(depth_image, [poly_pts], color)
    cv2.imwrite(filename,depth_image)

    return None
def compute_mask(A,B,C,D,depth_image):
    '''
    FUNCTION TO COMPUTE THE MASK, MEDIAN AND MEAN OF THE MASK GIVEN THE CORNERS
    param A: (Ax,Ay)
    :param B: (Bx,By)
    :param C: (Cx,Cy)
    :param D: (Dx,Dy)
    :param depth_image:
    :return:
    '''
    poly_pts = np.array([A, B, C, D], dtype=np.int32)

    mask = np.zeros_like(depth_image, dtype=np.uint8)
    cv2.fillPoly(mask, [poly_pts], 255)
    depth_values = depth_image[mask == 255]

    depth_values, corrupted = filter_outlier(depth_values, excludeNan=True, excludezero=True, exclude_percentile=False)
    if not(corrupted):
        mean_depth = np.mean(depth_values)
        median_depth = np.median(depth_values)
        return mean_depth,median_depth,mask
    else:
        return np.nan,np.nan,mask

def extract_resp_ROI(sh_right,sh_left,hip_left,hip_right,depth_image,type = ["torso"],show=False,TAG=""):
    '''
    FUNCTION TO EXTRACT MEAN AND MEDIAN DEPTH VALUE FROM A GIVEN ROI IN A SINGLE TIME FRAME
    :param sh_right:
    :param sh_left:
    :param hip_left:
    :param hip_right:
    :param depth_image:
    :param type: type of ROI you want to extract; a vector of strings ["torso","chest","abdomen",chest_centroid"]
    :return:
    '''
    results = {}

    if "all" in type:
        type = ["torso","chest","abdomen"]

    if "torso" in type:
        A,B,C,D = sh_right,sh_left,hip_left,hip_right ### r,l,l,r
        mean_depth,median_depth,_ = compute_mask(A,B,C,D,depth_image)
        results["torso"] = np.array([mean_depth,median_depth])

        if show:
            depth_colormap = cv2.applyColorMap(cv2.convertScaleAbs(depth_image, alpha=30), cv2.COLORMAP_JET)
            show_mask(A, B, C, D, depth_colormap, color=(0, 255, 255))
            cv2.imwrite("first_frames\\" + TAG + "torso.png", depth_colormap)
            cv2.destroyAllWindows()

    if "chest" in type:
        A, B = sh_right,sh_left
        C = (sh_left+hip_left)/2
        D = (sh_right+hip_right)/2
        mean_depth, median_depth, _ = compute_mask(A, B, C, D, depth_image)
        results["chest"] =  np.array([mean_depth,median_depth])
        if show:
            depth_colormap = cv2.applyColorMap(cv2.convertScaleAbs(depth_image, alpha=30), cv2.COLORMAP_JET)
            show_mask(A, B, C, D, depth_colormap, color=(0, 255, 255))
            cv2.imwrite("first_frames\\" + TAG + "chest.png", depth_colormap)
            cv2.destroyAllWindows()


    if "abdomen" in type:
        A = (sh_right+hip_right)/2
        B = (sh_left+hip_left)/2
        C, D = hip_left,hip_right
        mean_depth, median_depth, _ = compute_mask(A, B, C, D, depth_image)
        results["abdomen"] = np.array([mean_depth,median_depth])
        if show:
            depth_colormap = cv2.applyColorMap(cv2.convertScaleAbs(depth_image, alpha=30), cv2.COLORMAP_JET)
            show_mask(A, B, C, D, depth_colormap, color=(0, 255, 255))
            cv2.imwrite("first_frames\\" + TAG + "abdomen.png", depth_colormap)
            cv2.destroyAllWindows()


    return results

def extract_resp_ROI_video(depth_data,color_data,model,type= ["chest"],TAG="",show=False):
    '''
    FUNCTION TO EXTRACT MEAN AND MEDIAN DEPTH VALUE FROM A GIVEN ROI IN A ALL THE TIME FRAMES (VIDEO)

    :param depth_data:
    :param color_data:
    :param model: YOLO model for the extraction of skeleton points e.g. "yolo11n-pose.pt"
    :param type: roi to select -> watch the function extract_resp_ROI
    :param TAG: other tag to add to the saved image is show is true
    :param show: True/False if you do/don't want to save the first frame

    :return: dictionary containing all the mean, median signals from the selected ROI
    '''
    if not os.path.exists("first_frames"):
        os.makedirs("first_frames")
        print(f"Directory '{'first_frames'}' created.")
    else:
        print(f"Directory '{'first_frames'}' already exists.")
    final_resp_signal = {}
    for key in type:
        final_resp_signal[key] = []

    for frame,(colorimage,depthimage) in enumerate(zip(color_data,depth_data)):

        if frame == 0: # I'll not track the point because we are assuming a static or quasi-static condition
            all_keypoints, all_keypoints_dict = extract_keypoints(model, colorimage)
            sh_right = all_keypoints_dict[0]["right shoulder"]
            sh_left = all_keypoints_dict[0]["left shoulder"]
            hip_left = all_keypoints_dict[0]["left hip"]
            hip_right = all_keypoints_dict[0]["right hip"]

            if show:
                # SHOW THE TRACKING OF THE SKELETON ON THE FIRST FRAME
                depth_colormap = cv2.applyColorMap(cv2.convertScaleAbs(depthimage, alpha=30), cv2.COLORMAP_JET)
                show_skeleton(all_keypoints_dict,depth_colormap)
                cv2.imwrite("first_frames\\" + TAG + "plainPLOT.png", depth_colormap)
                cv2.destroyAllWindows()

            # SHOW THE ROI MASKS
            results = extract_resp_ROI(sh_right, sh_left, hip_left, hip_right, depthimage, type=type, show=show,TAG=TAG)

        else:
            results = extract_resp_ROI(sh_right, sh_left, hip_left, hip_right, depthimage, type=type)

        for key in type:
            final_resp_signal[key].append(results[key])

    for key in type:
        final_resp_signal[key] = np.array(final_resp_signal[key])

    return final_resp_signal





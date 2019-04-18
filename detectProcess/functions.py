import os
import sys
import argparse

import cv2
import numpy as np

import time

# directory in which models are located 
MODELS_DIR = "static/models"


BODY_MODELS = {
    'body_25': {
        'protoFile': "pose/body_25/pose_deploy.prototxt",
        'weightsFile': "pose/body_25/pose_iter_584000.caffemodel",
        'nPoints': 25
    },
    'coco': {
        'protoFile': "pose/coco/pose_deploy_linevec.prototxt",
        'weightsFile': "pose/coco/pose_iter_440000.caffemodel",
        'nPoints': 18
    },
    'mpi': {
        'protoFile': "pose/mpi/pose_deploy_linevec_faster_4_stages.prototxt",
        'weightsFile': "pose/mpi/pose_iter_160000.caffemodel",
        'posePairs': [[0,1], [1,2], [2,3], [3,4], [1,5], [5,6], [6,7],
                     [1,14], [14,8], [8,9], [9,10], [14,11], [11,12], [12,13]],
        'nPoints': 15
    }
}

FACE_MODEL = {
    'protoFile': "face/pose_deploy.prototxt",
    'weightsFile': "face/pose_iter_116000.caffemodel",
    'nPoints': 70,
    'pointIndex': {'chin': 8}
}

HAND_MODEL = {
    'protoFile': "hand/pose_deploy.prototxt",
    'weightsFile': "hand/pose_iter_102000.caffemodel"
}


# input size for detection networks
IN_WIDTH, IN_HEIGHT = 368, 368

# Coco model body keypoints IDs
NOSE = 0
NECK = 1
RIGHT = 2
LEFT = 5

# Face model ID for chin
CHIN = 8

# Live camera parameters
FPS = 1
MIRROR = True

VERBOSE = False


print('Loading body model...')

body_model = BODY_MODELS['coco']

protoFile = os.path.join(MODELS_DIR, body_model['protoFile'])
weightsFile = os.path.join(MODELS_DIR, body_model['weightsFile'])
body_net = cv2.dnn.readNetFromCaffe(protoFile, weightsFile)
body_net.setPreferableTarget(1) # DNN_TARGET_OPENCL

n_points_body = body_model['nPoints']

print('Loading face keypoints detection model...')

protoFile = os.path.join(MODELS_DIR, FACE_MODEL['protoFile'])
weightsFile = os.path.join(MODELS_DIR, FACE_MODEL['weightsFile'])
face_net = cv2.dnn.readNetFromCaffe(protoFile, weightsFile)
face_net.setPreferableTarget(1) # DNN_TARGET_OPENCL

n_points_face = FACE_MODEL['nPoints']

def dist(pt1, pt2):
    """Calculates the Euclidean distance between two points,
    which are (x, y) tuples."""

    return np.sqrt( (pt2[1] - pt1[1]) ** 2 + (pt2[0] - pt1[0]) ** 2 )


def get_keypoints(prob_maps, n_points, frame_h, frame_w, thresh):
    """Estimates the locations of keypoints from probability maps
    output by detection networks.

    Returns keypoints with probability scores greater than a threshold.
    """

    _, _, out_h, out_w = prob_maps.shape

    points = []
    for i in range(n_points):

        prob_map = prob_maps[0, i, :, :]
        min_val, prob, min_loc, point = cv2.minMaxLoc(prob_map)

        if VERBOSE:
            print('{:}: {:.4f}'.format(point, prob))

        x = (point[0] / out_w) * frame_w
        y = (point[1] / out_h) * frame_h

        x, y = int(x), int(y)

        if prob > thresh:
            points.append((x, y))
        else:
            points.append(None)

    return points



class KeyPointDetector(object):
    """ A simple class for detecting body and face keypoints.

    The class takes as input a pre-trained body detection network,
    a pre-trained face detection network, and the number of keypoints
    detected by each.
    """
    def __init__(self, body_net, face_net, n_points_body, n_points_face):

        self.body_net = body_net
        self.face_net = face_net

        self.n_points_body = n_points_body
        self.n_points_face = n_points_face

    def run(self, frame):
        """ Runs keypoint detections on a single frame and returns
        the frame with keypoints and shoulder marked.
        """

        frameHeight, frameWidth, _ = frame.shape

        blob = cv2.dnn.blobFromImage(frame, 1/255., (IN_WIDTH, IN_WIDTH), (0, 0, 0),
                                    swapRB=False, crop=False)

        # detect body keypoints
        self.body_net.setInput(blob)
        tic = time.time()
        body_out = self.body_net.forward()
        toc = time.time()
        print('Body keypoints: forward pass in {:.2f}s'.format(toc - tic))
        tic = time.time()
        body_points = get_keypoints(body_out, self.n_points_body,
                                    frameHeight, frameWidth,
                                    0.08)
        toc = time.time()
        print('Body keypoints: keypoints retrieval in {:.2f}s'.format(toc - tic))


        # detect face keypoints
        self.face_net.setInput(blob)
        tic = time.time()
        face_out = self.face_net.forward()
        toc = time.time()
        print('Face keypoints: forward pass in {:.2f}s'.format(toc - tic))
        tic = time.time()
        face_points = get_keypoints(face_out, self.n_points_face,
                                    frameHeight, frameWidth,
                                    0.16)
        toc = time.time()
        print('Face keypoints: keypoints retrieval in {:.2f}s'.format(toc - tic))

        # display body keypoint and its ID
        for j, pt in enumerate(body_points):
            if pt:
                cv2.circle(frame, (pt[0], pt[1]),
                           int(8 * frameWidth / 1280), (0, 255, 255),
                           thickness=-1, lineType=cv2.FILLED)
                cv2.putText(frame, '{}'.format(j), (pt[0], pt[1]), cv2.FONT_HERSHEY_SIMPLEX,
                            0.64 * frameWidth / 960, (0, 0, 255),
                            2, lineType=cv2.LINE_AA)

        # display face keypoint
        for j, pt in enumerate(face_points):
            if pt:
                cv2.circle(frame, (pt[0], pt[1]),
                           2, (0, 255, 255),
                           thickness=-1, lineType=cv2.FILLED)

        # special marker for chin keypoint
        if face_points[CHIN]:
            cv2.drawMarker(frame, face_points[CHIN], (255, 0, 255),
                           cv2.MARKER_TRIANGLE_DOWN, 16, 2)

        # display shoulder to neck lines
        if body_points[RIGHT] and body_points[NECK]:
            cv2.line(frame, body_points[RIGHT], body_points[NECK], (0, 0, 204), 2)
        if body_points[LEFT] and body_points[NECK]:
            cv2.line(frame, body_points[LEFT], body_points[NECK], (0, 51, 255), 2)


        # estimate and display shoulder arch (if both shoulder joints detected)
        if body_points[RIGHT] and body_points[LEFT]:

            rite = body_points[RIGHT]
            left = body_points[LEFT]

            x = (rite[0] + left[0]) / 2
            y = (rite[1] + left[1]) / 2

            x, y = int(x), int(y)

            drl = dist(rite, left)

            hw, hh = int(0.5 * drl), int(0.125 * drl)

            if VERBOSE:
                print('rite:', rite)
                print('left:', left)
                print('cntr: (%d, %d)' % (x, y))
                print('dist: %.2f' % drl)

            cv2.ellipse(frame, (x, y), (hw, hh), 0, 180, 360, (51, 153, 0), 2, lineType=8)

        return frame


detector = KeyPointDetector(body_net, face_net, n_points_body, n_points_face)

# process uploaded image and saves output_image
def processImage(imgpath, filename):

    img = os.path.basename(imgpath)

    print('Loading single image...')
    print(imgpath)

    print('Running keypoints detection on image...')
    frame = cv2.imread(imgpath)

    # run detector on the image
    frame = detector.run(frame)

    # save output_image to the result folder
    outputfilepath = "static/result/" + filename + "_output.jpg"
    cv2.imwrite(outputfilepath, frame)

    return outputfilepath


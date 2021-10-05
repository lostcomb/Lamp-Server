import cv2
from collections import deque
from threading import Thread, Event

RESIZE_FACTOR = 0.5
MIN_COUNTOUR_AREA = 2500
MAX_LAST_OFF_X = 125


class Detector:
    def __init__(self, switch):
        self._switch = switch
        self._event = Event()
        self._frame = None
        self._detections = deque(maxlen=4)
        self._camera = cv2.VideoCapture(0)
        if not self._camera.isOpened():
            raise Exception("Cannot connect to camera")

        self._thread = Thread(target=self._detect, daemon=True)

    def start(self):
        self._thread.start()
        self._event.wait()

    @property
    def frame(self):
        self._event.wait()
        return cv2.imencode(".jpg", self._frame)[1].tobytes()

    @frame.setter
    def frame(self, value):
        self._frame = value
        self._event.set()
        self._event.clear()

    def _detect(self):
        avg = None

        while True:
            _, frame = self._camera.read()
            frame = cv2.resize(
                frame, None, fx=RESIZE_FACTOR, fy=RESIZE_FACTOR, interpolation=cv2.INTER_NEAREST
            )
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            blured = cv2.GaussianBlur(frame, (21, 21), 0)

            if avg is None:
                avg = blured.copy().astype("float")
                continue

            diff = cv2.absdiff(blured, cv2.convertScaleAbs(avg))
            cv2.accumulateWeighted(blured, avg, 0.5)

            _, thresholded = cv2.threshold(diff, 5, 255, cv2.THRESH_BINARY)
            thresholded = cv2.dilate(thresholded, None)
            contours, _ = cv2.findContours(thresholded, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            self._detections.append(self._extract_detection(contours))
            self._check_for_trigger()

            for point in self._detections:
                if point is not None:
                    cv2.circle(frame, point, 10, 255, -1)

            self.frame = frame

    def _extract_detection(self, contours):
        if not contours:
            return None

        max_contour = max(contours, key=cv2.contourArea)
        if cv2.contourArea(max_contour) > MIN_COUNTOUR_AREA:
            M = cv2.moments(max_contour)
            cx = int(M["m10"] / M["m00"])
            cy = int(M["m01"] / M["m00"])
            return (cx, cy)

    def _check_for_trigger(self):
        detections = list(self._detections)
        if len(detections) < 4 or any(d is None for d in detections):
            return

        xs = [d[0] for d in detections]
        diffs = [a - b for a, b in zip(xs, xs[1:])]

        # Switch on
        if all(d < 0 for d in diffs):
            self._switch.on()

        # Switch off
        final_x = xs[-1]
        if all(d > 0 for d in diffs) and final_x < MAX_LAST_OFF_X:
            self._switch.off()
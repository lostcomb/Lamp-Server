#!/usr/bin/env python3
from switch import Switch
from detector import Detector
from flask import Flask, Response, render_template, redirect, url_for

app = Flask(__name__)
switch = Switch()
detector = Detector(switch)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/toggle_switch", methods=["POST"])
def toggle_switch():
    switch.toggle()
    return redirect(url_for("index"))


@app.route("/video_feed")
def video_feed():
    def _frames():
        while True:
            yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + detector.frame + b"\r\n"

    return Response(_frames(), mimetype="multipart/x-mixed-replace; boundary=frame")


if __name__ == "__main__":
    detector.start()
    app.run(host="0.0.0.0", threaded=True)
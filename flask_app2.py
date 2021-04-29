# flask_app2.py

from flask import Flask, render_template, Response

# Camera_multiをインポートしています。
from camera_multi import Camera
# from camera_single import Camera

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

def gen(camera):
    while True:
        frame = camera.get_frame()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')
               
@app.route('/video_feed')
def video_feed():
    return Response(gen(Camera()),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    print('stop: ctrl+c')
    #  threaded=Trueにしています。
    app.run(host="0.0.0.0", port=5000, debug=True, threaded=True)
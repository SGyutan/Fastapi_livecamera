# FastAPIでOpencv Streaming

### はじめに

最近、FastAPIが使いやすいということでFastAPIを試しに使ってみることにしました。

題材は、以前投稿した[FlaskとOpenCVで live streaming](https://qiita.com/Gyutan/items/1f81afacc7cac0b07526)のFastAPI版です。

stackoverflowにすでにこの書き換えの記事が投稿されていますが、前回投稿したものに合わせて少し書き換えたものを覚えとして記載します。

[FASTAPI: Not able to render html page](https://stackoverflow.com/questions/63667466/fastapi-not-able-to-render-html-page)


FastAPIの解説については、様々な投稿があります。
公式（日本語）も充実しています。
[FastAPI](https://fastapi.tiangolo.com/ja/)
[FlaskからFastAPIにスムーズに移行する](https://ichi.pro/flask-kara-fastapi-ni-sumu-zu-ni-ikosuru-224628603966359) 
[FastAPIとPythonを使用してAPIを高速に構築する](https://ichi.pro/fastapi-to-python-o-shiyoshite-api-o-kosoku-ni-kochikusuru-255341594090036)
[FastAPI 入門](https://okakyo.myvnc.com/article/fastapi-starter-1/)

FastAPIは、Web 部分はStarlette、データ部分はPydanticの上に構築されており、以下の記事に詳しい解説があります。
[FastAPIでStarletteとPydanticはどのように使われているか](https://qiita.com/bee2/items/d629d8acc102cf92b7b2)


FastAPIの基本は、Requestに対して、JSONをResponceします。
一方で、HTMLのテンプレートを使うこともできます。(公式ドキュメント)
[カスタムレスポンス - HTML、ストリーム、ファイル、その他のレスポンス](https://fastapi.tiangolo.com/ja/advanced/custom-response/)



### 前回投稿したFlask（再掲）の復習

この部分は、前回と重複なので読み飛ばしても構いません。

#### ホルダー構成

```
─── static
|   └── js(必要があれば）
|   |   └──main.js
|   └── main.cs
├── templates
│   └── index.html
├──  camera_single.py　（処理する関数）
└──  flask_app.py (メインプログラム)
```

```html
 <!-- index.html -->
<html>
  <head>
    <title>Video Streaming Demonstration</title>
  </head>
  <body>
    <h1>Video Streaming Demonstration</h1>
    <img src="{{ url_for('video_feed') }}">
    <!-- jinja2のテンプレートの書き方です。/video_feedを呼び出しています。 -->
  </body>
</html>

```
Staticホルダーは今回も空です。

```python
# camera_single.py

import cv2

class Camera():
    def __init__(self):
        self.video = cv2.VideoCapture(0)

        # Opencvのカメラをセットします。(0)はノートパソコンならば組み込まれているカメラ

    def __del__(self):
        self.video.release()

    def get_frame(self):
        success, image = self.video.read()
        ret, jpeg = cv2.imencode('.jpg', image)
        return jpeg.tobytes()

        # read()は、二つの値を返すので、success, imageの2つ変数で受けています。
        # OpencVはデフォルトでは raw imagesなので JPEGに変換
        # ファイルに保存する場合はimwriteを使用、メモリ上に格納したい時はimencodeを使用
        # cv2.imencode() は numpy.ndarray() を返すので .tobytes() で bytes 型に変換
```

```Python
# flask_app.py

from flask import Flask, render_template, Response

from camera_single import Camera

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

    # "/" を呼び出したときには、indexが表示される。

def gen(camera):
    while True:
        frame = camera.get_frame()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

# returnではなくジェネレーターのyieldで逐次出力。
# Generatorとして働くためにgenとの関数名にしている
# Content-Type（送り返すファイルの種類として）multipart/x-mixed-replace を利用。
# HTTP応答によりサーバーが任意のタイミングで複数の文書を返し、紙芝居的にレンダリングを切り替えさせるもの。
#（※以下に解説参照あり）

@app.route('/video_feed')
def video_feed():
    return Response(gen(Camera()),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    print('stop: ctrl+c')
    app.run(host="0.0.0.0", debug=True, port=5000)

# 0.0.0.0はすべてのアクセスを受け付けます。    
# webブラウザーには、「localhost:5000」と入力
```

#### マルチアクセスへの対応

[FlaskとOpenCVでカメラ画像をストリーミングして複数ブラウザでアクセスする](https://qiita.com/RIckyBan/items/a7dea207d266ef835c48)

この記事で

> この実装では複数ブラウザ・タブからのアクセスに対応しておらず、別のタブからアクセスしても画像は表示されません。

そこで、参考の記事ではcamera_single.pyを以下のように書き換えています。cameraの継承元のBaseCameraクラスも作成します。詳しい実装の解説は記事を参考にしてください。

```python
# camera_multi.py

import cv2
from base_camera import BaseCamera


class Camera(BaseCamera):
    def __init__(self):
        super().__init__()

    # over-wride of BaseCamera class frames method
    @staticmethod
    def frames():
        camera = cv2.VideoCapture(0)
        if not camera.isOpened():
            raise RuntimeError('Could not start camera.')

        while True:
            # read current frame
            _, img = camera.read()

            # encode as a jpeg image and return it
            yield cv2.imencode('.jpg', img)[1].tobytes()
```


```python
# base_camera.py
import copy
import time
import threading
try:
    from greenlet import getcurrent as get_ident
except ImportError:
    try:
        from thread import get_ident
    except ImportError:
        from _thread import get_ident


class CameraEvent(object):
    """An Event-like class that signals all active clients when a new frame is
    available.
    """
    def __init__(self):
        self.events = {}

    def wait(self):
        """Invoked from each client's thread to wait for the next frame."""
        ident = get_ident()
        if ident not in self.events:
            # this is a new client
            # add an entry for it in the self.events dict
            # each entry has two elements, a threading.Event() and a timestamp
            self.events[ident] = [threading.Event(), time.time()]
        return self.events[ident][0].wait()

    def set(self):
        """Invoked by the camera thread when a new frame is available."""
        now = time.time()
        remove = []
        for ident, event in self.events.items():
            if not event[0].isSet():
                # if this client's event is not set, then set it
                # also update the last set timestamp to now
                event[0].set()
                event[1] = now
            else:
                # if the client's event is already set, it means the client
                # did not process a previous frame
                # if the event stays set for more than 5 seconds, then assume
                # the client is gone and remove it
                if now - event[1] > 5:
                    remove.append(ident)

        for ident in remove:        
            del self.events[ident]

    def clear(self):
        """Invoked from each client's thread after a frame was processed."""
        self.events[get_ident()][0].clear()


class BaseCamera(object):
    thread = None  # background thread that reads frames from camera
    frame = None  # current frame is stored here by background thread
    last_access = 0  # time of last client access to the camera
    event = CameraEvent()

    def __init__(self):
        """Start the background camera thread if it isn't running yet."""
        if BaseCamera.thread is None:
            BaseCamera.last_access = time.time()

            # start background frame thread
            BaseCamera.thread = threading.Thread(target=self._thread)
            BaseCamera.thread.start()

            # wait until frames are available
            while self.get_frame() is None:
                time.sleep(0)

    def get_frame(self):
        """Return the current camera frame."""
        BaseCamera.last_access = time.time()

        # wait for a signal from the camera thread
        BaseCamera.event.wait()
        BaseCamera.event.clear()

        return BaseCamera.frame

    @staticmethod
    def frames():
        """"Generator that returns frames from the camera."""
        raise RuntimeError('Must be implemented by subclasses.')

    @classmethod
    def _thread(cls):
        """Camera background thread."""
        print('Starting camera thread.')
        frames_iterator = cls.frames() #call for frames method (Staticmethod)
        for frame in frames_iterator:
            BaseCamera.frame = frame
            BaseCamera.event.set()  # send signal to clients
            time.sleep(0)

            # if there hasn't been any clients asking for frames in
            # the last 10 seconds then stop the thread
            if time.time() - BaseCamera.last_access > 10:
                frames_iterator.close()
                print('Stopping camera thread due to inactivity.')
                break
        BaseCamera.thread = None
```

```python
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
```

### FastAPIへの書き換え

```python
# fastapi_app.py

import uvicorn

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, StreamingResponse
# from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# from camera_single import Camera
from camera_multi import Camera

app = FastAPI()

# app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
   return templates.TemplateResponse('index.html', {"request": request})

def gen(camera):
    """Video streaming generator function."""
    while True:
        frame = camera.get_frame()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


@app.get('/video_feed', response_class=HTMLResponse)
async def video_feed():
    """Video streaming route. Put this in the src attribute of an img tag."""
    return  StreamingResponse(gen(Camera()),
                    media_type='multipart/x-mixed-replace; boundary=frame')


if __name__ == "__main__":
    print('stop: ctrl+c')
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

Flaskとの主な変更点
・/Video_feedのレスポンスにStreamingResponseに変更、mimetypeをmedia_typeに変更
・/indexのレスポンスがrender_templateからtemplates.TemplateResponseに変更

@app.get("/", response_class=HTMLResponse)のresponse_classを指定することでドキュメントが自動生成されます。

http://localhost:8000/docs
でアクセスできます。

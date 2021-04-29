
"""
参考：
https://stackoverflow.com/questions/63667466/fastapi-not-able-to-render-html-page
Flaskのひとつのインスタンスでのアクセスでひとつのファイルにまとめたもの

"""

import uvicorn

from fastapi import FastAPI, Request, Response
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates

import cv2

app = FastAPI(debug=True)

templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


def gen_frames():
    cap = cv2.VideoCapture(0)

    while True:
        # for cap in caps:
        # # Capture frame-by-frame
        success, frame0 = cap.read()  # read the camera frame

        ret, buffer = cv2.imencode('.jpg', frame0)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')  


@app.get('/video_feed', response_class=HTMLResponse)
async def video_feed():
    """Video streaming route. Put this in the src attribute of an img tag."""
    return StreamingResponse(gen_frames(),
                    media_type='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=8000)
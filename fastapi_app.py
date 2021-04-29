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
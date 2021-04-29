# 動画ファイルを指定して再生する方法
import uvicorn
from fastapi import FastAPI
from fastapi.responses import StreamingResponse

some_file_path = "WIN_20210301_13_18_56_Pro.mp4"
app = FastAPI()


@app.get("/")
def main():
    file_like = open(some_file_path, mode="rb")
    return StreamingResponse(file_like, media_type="video/mp4")

if __name__ == "__main__":
    print('stop: ctrl+c')
    uvicorn.run(app, host="0.0.0.0", port=8000)

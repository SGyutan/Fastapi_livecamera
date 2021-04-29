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
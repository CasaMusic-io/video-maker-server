from flask import Flask, request, jsonify
import os
import uuid
import subprocess
from PIL import Image
import requests

app = Flask(__name__)

def descargar(url, nombre):
    r = requests.get(url)
    with open(nombre, 'wb') as f:
        f.write(r.content)

@app.route("/crear-video", methods=["POST"])
def crear_video():
    data = request.get_json()
    
    id = str(uuid.uuid4())
    carpeta = f"proyectos/{id}"
    os.makedirs(carpeta, exist_ok=True)

    # Descargar archivos
    fondo = f"{carpeta}/fondo.mp4"
    portada = f"{carpeta}/portada.png"
    logo1 = f"{carpeta}/logo1.png"
    logo2 = f"{carpeta}/logo2.png"
    audio = f"{carpeta}/audio.mp3"
    miniatura = f"{carpeta}/miniatura.png"
    salida = f"{carpeta}/video.mp4"

    descargar(data["fondo_video"], fondo)
    descargar(data["portada"], portada)
    descargar(data["logo1"], logo1)
    descargar(data["logo2"], logo2)
    descargar(data["audio"], audio)

    duracion = data["duracion"]
    titulo = data["titulo"]

    # Crear miniatura
    fondo_img = Image.open(fondo if fondo.endswith(".png") else portada).resize((1280, 720))
    portada_img = Image.open(portada).resize((400, 400))
    logo1_img = Image.open(logo1).resize((100, 100))

    fondo_img.paste(portada_img, (440, 160))
    fondo_img.paste(logo1_img, (20, 20))
    fondo_img.save(miniatura)

    # Crear video con ffmpeg (simplificado)
    comando = [
        "ffmpeg",
        "-i", fondo,
        "-i", logo1,
        "-i", logo2,
        "-i", portada,
        "-i", audio,
        "-filter_complex",
        "[0:v][1:v] overlay=10:10 [v1]; [v1][2:v] overlay=W-w-10:H/2-h/2 [v2]; [v2][3:v] overlay=W-w-420:H/2-h/2",
        "-map", "[v2]",
        "-map", "4:a",
        "-t", str(duracion),
        "-y", salida
    ]
    subprocess.run(comando)

    return jsonify({
        "video_url": f"/{salida}",
        "thumbnail_url": f"/{miniatura}",
        "status": "success"
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

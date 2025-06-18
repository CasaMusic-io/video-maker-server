from flask import Flask, request, jsonify
import os
import uuid
import subprocess
from PIL import Image
import requests

app = Flask(__name__)

def descargar(url, ruta_destino):
    try:
        print(f"Descargando: {url}")
        r = requests.get(url)
        r.raise_for_status()
        with open(ruta_destino, 'wb') as f:
            f.write(r.content)
    except Exception as e:
        raise Exception(f"Error al descargar {url}: {e}")

@app.route("/crear-video", methods=["POST"])
def crear_video():
    try:
        data = request.get_json()
        print("JSON recibido:", data)

        # Validar campos requeridos
        campos = ["fondo_video", "portada", "logo1", "logo2", "audio", "duracion", "titulo"]
        for campo in campos:
            if campo not in data or not data[campo]:
                return jsonify({"error": f"Falta el campo '{campo}'"}), 400

        # Procesar duración
        duracion = data["duracion"]
        if isinstance(duracion, str) and ":" in duracion:
            partes = duracion.split(":")
            partes = [int(p) for p in partes]
            if len(partes) == 3:
                h, m, s = partes
            elif len(partes) == 2:
                h, m, s = 0, partes[0], partes[1]
            else:
                h, m, s = 0, 0, partes[0]
            duracion_segundos = h*3600 + m*60 + s
        else:
            try:
                duracion_segundos = int(float(duracion))
            except Exception:
                return jsonify({"error": "Duración inválida"}), 400

        # Carpeta única por proyecto
        id_unico = str(uuid.uuid4())
        carpeta = f"proyectos/{id_unico}"
        os.makedirs(carpeta, exist_ok=True)

        # Rutas locales de archivos
        fondo = f"{carpeta}/fondo.mp4"
        portada = f"{carpeta}/portada.png"
        logo1 = f"{carpeta}/logo1.png"
        logo2 = f"{carpeta}/logo2.png"
        audio = f"{carpeta}/audio.mp3"
        miniatura = f"{carpeta}/miniatura.png"
        salida = f"{carpeta}/video.mp4"

        # Descargar archivos
        descargar(data["fondo_video"], fondo)
        descargar(data["portada"], portada)
        descargar(data["logo1"], logo1)
        descargar(data["logo2"], logo2)
        descargar(data["audio"], audio)

        # Generar miniatura: solo usa imágenes, nunca video
        print("Creando miniatura...")
        fondo_img = Image.new("RGB", (1280, 720), color=(0, 0, 0))
        portada_img = Image.open(portada).resize((400, 400))
        logo1_img = Image.open(logo1).resize((100, 100))
        fondo_img.paste(portada_img, (440, 160))
        fondo_img.paste(logo1_img, (20, 20))
        fondo_img.save(miniatura)

        print("Llamando ffmpeg...")
        comando = [
            "ffmpeg",
            "-i", fondo,
            "-i", logo1,
            "-i", logo2,
            "-i", portada,
            "-i", audio,
            "-filter_complex",
            "[0:v][1:v] overlay=10:10 [v1];" +
            " [v1][2:v] overlay=W-w-10:H/2-h/2 [v2];" +
            " [v2][3:v] overlay=W-w-420:H/2-h/2",
            "-map", "[v2]",
            "-map", "4:a",
            "-t", str(duracion_segundos),
            "-y", salida
        ]
        resultado = subprocess.run(comando, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        if resultado.returncode != 0:
            print("Error de ffmpeg:", resultado.stderr.decode())
            return jsonify({
                "error": "Error al crear video con ffmpeg",
                "detalle": resultado.stderr.decode()
            }), 500

        print("Video generado correctamente:", salida)

        return jsonify({
            "status": "success",
            "video_url": f"/{salida}",
            "thumbnail_url": f"/{miniatura}"
        })

    except Exception as e:
        print("Error general:", str(e))
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    # Railway usa el puerto 5000
    app.run(host="0.0.0.0", port=5000)

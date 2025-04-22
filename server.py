
from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
from PIL import Image, ImageDraw, ImageFont
import tempfile, shutil, os, zipfile

app = Flask(__name__)
CORS(app)
@app.route("/api/add_watermarks", methods=["POST"])
def add_watermarks():
    temp_dir = tempfile.mkdtemp()
    output_dir = os.path.join(temp_dir, "output")
    os.makedirs(output_dir, exist_ok=True)

    text = request.form["text"]
    font_name = request.form["font"]
    font_size = int(request.form["font_size"])
    color = request.form["color"].lstrip("#")
    opacity = int(request.form["opacity"])
    angle = int(request.form["angle"])
    tile = request.form["tile"] == "true"

    font_paths = {
        "Roboto": "fonts/Roboto-Regular.ttf",
        "DejaVuSans-Bold": "fonts/DejaVuSans-Bold.ttf",
        "Arial": "fonts/Arial.ttf"
    }

    font_path = font_paths.get(font_name, "fonts/Roboto-Regular.ttf")
    font = ImageFont.truetype(font_path, font_size)

    files = request.files.getlist("images")
    for f in files:
        img = Image.open(f.stream).convert("RGBA")
        watermark_layer = Image.new("RGBA", img.size, (255, 255, 255, 0))
        draw = ImageDraw.Draw(watermark_layer)

        rgba = tuple(int(color[i:i+2], 16) for i in (0, 2, 4)) + (opacity,)

        if tile:
            for y in range(0, img.height, font_size * 3):
                for x in range(0, img.width, font_size * 6):
                    draw.text((x, y), text, font=font, fill=rgba)
        else:
            text_width, text_height = draw.textsize(text, font)
            x = img.width - text_width - 20
            y = img.height - text_height - 20
            draw.text((x, y), text, font=font, fill=rgba)

        rotated = watermark_layer.rotate(angle, expand=0)
        watermarked = Image.alpha_composite(img, rotated)

        filename = os.path.join(output_dir, f.filename)
        watermarked.convert("RGB").save(filename)

    zip_path = os.path.join(temp_dir, "result.zip")
    with zipfile.ZipFile(zip_path, "w") as zf:
        for fname in os.listdir(output_dir):
            zf.write(os.path.join(output_dir, fname), arcname=fname)

    return jsonify({"download_url": f"/download/{os.path.basename(zip_path)}"})

@app.route("/download/<filename>")
def download_file(filename):
    path = os.path.join(tempfile.gettempdir(), filename)
    if not os.path.exists(path):
        return "Файл не найден", 404

    # НЕ УДАЛЯЕМ СРАЗУ — пусть скачает
    return send_file(path, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)

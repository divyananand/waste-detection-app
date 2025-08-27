from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import torch
import numpy as np
import cv2
import os
import sys
import time

# 👇 Add YOLOv5 path to Python sys path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'yolov5')))

# ✅ Import YOLOv5 utils & model
from models.common import DetectMultiBackend
from utils.general import non_max_suppression
from utils.augmentations import letterbox

# 🔧 Flask app setup
app = Flask(__name__)
CORS(app)

# 📂 Make sure static/results exists
RESULTS_FOLDER = os.path.join("static", "results")
os.makedirs(RESULTS_FOLDER, exist_ok=True)

# 🧠 Load the trained model
model_path = '../yolov5/runs/train/waste_yolo_improved/weights/best.pt'
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model = DetectMultiBackend(model_path, device=device)
model.eval()
names = model.names  # class id → label mapping

def scale_coords(img1_shape, coords, img0_shape, ratio_pad=None):
    """Rescale coords (xyxy) from img1_shape to img0_shape"""
    if ratio_pad is None:
        gain = min(img1_shape[0] / img0_shape[0], img1_shape[1] / img0_shape[1])  # gain = old / new
        pad = (img1_shape[1] - img0_shape[1] * gain) / 2, (img1_shape[0] - img0_shape[0] * gain) / 2  # wh padding
    else:
        gain = ratio_pad[0][0]
        pad = ratio_pad[1]

    coords[:, [0, 2]] -= pad[0]  # x padding
    coords[:, [1, 3]] -= pad[1]  # y padding
    coords[:, :4] /= gain
    coords[:, :4] = coords[:, :4].clamp(min=0)
    return coords

# ✅ Health check route
@app.route('/')
def home():
    return "✅ Waste Detection Flask Backend is Running!"

# 📸 Endpoint to detect waste in uploaded image
@app.route('/detect', methods=['POST'])
def detect():
    if 'image' not in request.files:
        return jsonify({'error': 'No image uploaded'}), 400

    file = request.files['image']
    img_bytes = np.frombuffer(file.read(), np.uint8)
    img = cv2.imdecode(img_bytes, cv2.IMREAD_COLOR)

    # 🔁 Preprocess for YOLOv5
    img_resized = letterbox(img, 640, stride=32, auto=True)[0]
    img_resized = img_resized.transpose((2, 0, 1))[::-1]  # BGR → RGB
    img_resized = np.ascontiguousarray(img_resized)

    img_tensor = torch.from_numpy(img_resized).to(device)
    img_tensor = img_tensor.float() / 255.0
    if img_tensor.ndimension() == 3:
        img_tensor = img_tensor.unsqueeze(0)

    # 🔮 Run model inference
    pred = model(img_tensor, augment=False, visualize=False)
    pred = non_max_suppression(pred, conf_thres=0.25, iou_thres=0.45)[0]

    result = []
    if pred is not None and len(pred):
        pred[:, :4] = scale_coords(img_tensor.shape[2:], pred[:, :4], img.shape).round()
        for *box, conf, cls in pred:
            x1, y1, x2, y2 = map(int, box)

            # Save detection info
            result.append({
                'class': names[int(cls)],
                'confidence': round(float(conf), 4)
            })

            # 🖼️ Draw bounding box + label
            label = f"{names[int(cls)]} {conf:.2f}"
            cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(img, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX,
                        0.6, (0, 255, 0), 2)

    # 💾 Save annotated image
    filename = f"result_{int(time.time())}.jpg"
    save_path = os.path.join(RESULTS_FOLDER, filename)
    cv2.imwrite(save_path, img)

    # Build response
    response = {
        'detections': result,
        'image_url': f"/results/{filename}"  # 👈 updated path
    }

    return jsonify(response)

# 🖼️ Serve saved images
@app.route('/results/<path:filename>')
def serve_result(filename):
    return send_from_directory(RESULTS_FOLDER, filename)

# 🚀 Run the Flask server
if __name__ == '__main__':
    app.run(debug=True)

from fastapi import FastAPI
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import base64
import cv2
import numpy as np
from io import BytesIO
from PIL import Image
import requests

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

VIDEOS_FOLDER = "E:/Downloads new/dataset_de_soyza/converted"
API_A_URL = "http://localhost:8002/run_pipeline"  # Server A must run separately

def generate_thumbnail(video_path):
    cap = cv2.VideoCapture(video_path)
    success, frame = cap.read()
    if not success:
        cap.release()
        return None

    cap.set(cv2.CAP_PROP_POS_MSEC, 1000)
    success, frame = cap.read()

    if success:
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(frame_rgb)
        pil_image.thumbnail((300, 300))
        buffer = BytesIO()
        pil_image.save(buffer, format="JPEG")
        encoded = base64.b64encode(buffer.getvalue()).decode('utf-8')
        cap.release()
        return encoded

    cap.release()
    return None

def get_video_list():
    return sorted([f for f in os.listdir(VIDEOS_FOLDER) if f.endswith(".mp4")])

@app.get("/thumbnails")
async def get_thumbnails():
    thumbnails = []
    for filename in get_video_list():
        video_path = os.path.join(VIDEOS_FOLDER, filename)
        video_id = os.path.splitext(filename)[0]
        thumb = generate_thumbnail(video_path)
        if thumb:
            thumbnails.append({"video_id": video_id, "thumbnail": thumb})
    return {"thumbnails": thumbnails}

@app.get("/metrics/{video_id}")
async def get_metrics(video_id: str):
    dataset = "VIDEOPULSE"
    try:
        response = requests.post(API_A_URL, json={"vid_idx": video_id, "dataset": dataset})
        if response.status_code != 200:
            return JSONResponse({"error": response.text}, status_code=response.status_code)

        data = response.json()

        readable_data = {
            "Ground Truth Heart Rate": data.get("gt_hr"),
            "Predicted Heart Rate": data.get("pd_hr"),
            "SpO2 Ground Truth": data.get("gt_spo2"),
            "SpO2 Predicted": data.get("pd_spo2"),
            "Mean Absolute Error": data.get("mae"),
            "Root Mean Squared Error": data.get("rmse"),
            "GT_PPG": data.get("gt_ppg"),
            "PD_PPG": data.get("pd_ppg"),
        }
        return readable_data
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/video/{video_id}")
async def get_video(video_id: str):
    for filename in os.listdir(VIDEOS_FOLDER):
        if filename.startswith(video_id):
            video_path = os.path.join(VIDEOS_FOLDER, filename)
            return StreamingResponse(open(video_path, "rb"), media_type="video/mp4")
    return JSONResponse({"error": "Video not found"}, status_code=404)

import streamlit as st
import requests
import base64
import matplotlib.pyplot as plt

FASTAPI_URL = "http://localhost:8000"
THUMBNAILS_PER_BATCH = 5
MIN_THUMBNAILS = THUMBNAILS_PER_BATCH

def fetch_thumbnails():
    response = requests.get(f"{FASTAPI_URL}/thumbnails")
    return response.json()["thumbnails"] if response.status_code == 200 else []

def fetch_metrics(video_id):
    response = requests.get(f"{FASTAPI_URL}/metrics/{video_id}")
    return response.json() if response.status_code == 200 else None

def get_video_url(video_id):
    return f"{FASTAPI_URL}/video/{video_id}"

def plot_ppg(gt_ppg, pd_ppg):
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(gt_ppg, label="GT PPG", linewidth=2)
    ax.plot(pd_ppg, label="PD PPG", linestyle="--")
    ax.set_title("GT vs PD PPG")
    ax.set_xlabel("Sample Index")
    ax.set_ylabel("Amplitude")
    ax.legend()
    ax.grid(True)
    return fig

def main():
    st.set_page_config(layout="wide")
    st.title("🎞️ Video Pulse Signal Extraction")

    if "thumb_limit" not in st.session_state:
        st.session_state["thumb_limit"] = THUMBNAILS_PER_BATCH
    if "selected_video" not in st.session_state:
        st.session_state["selected_video"] = None

    thumbnails = fetch_thumbnails()
    visible_thumbs = thumbnails[:st.session_state["thumb_limit"]]

    cols = st.columns(3)
    for i, thumb in enumerate(visible_thumbs):
        with cols[i % 3]:
            st.image(base64.b64decode(thumb["thumbnail"]), use_container_width=True)
            if st.button(thumb["video_id"], key=thumb["video_id"]):
                st.session_state["selected_video"] = thumb["video_id"]

    col1, col2 = st.columns(2)
    if st.session_state["thumb_limit"] < len(thumbnails):
        if col1.button("➕ Show More"):
            st.session_state["thumb_limit"] += THUMBNAILS_PER_BATCH
            st.rerun()
    if st.session_state["thumb_limit"] > MIN_THUMBNAILS:
        if col2.button("➖ Show Less"):
            st.session_state["thumb_limit"] -= THUMBNAILS_PER_BATCH
            st.rerun()

    if st.session_state["selected_video"]:
        st.markdown("---")
        st.subheader(f"▶️ Playing Video: **{st.session_state['selected_video']}**")
        st.video(get_video_url(st.session_state["selected_video"]))

        st.markdown("### 📊 Extracted Metrics")
        metrics = fetch_metrics(st.session_state["selected_video"])
        if metrics:
            for label, value in metrics.items():
                if label not in ["GT_PPG", "PD_PPG"]:
                    st.markdown(f"**{label}:** {value}")

            if "GT_PPG" in metrics and "PD_PPG" in metrics:
                fig = plot_ppg(metrics["GT_PPG"], metrics["PD_PPG"])
                st.pyplot(fig)

if __name__ == "__main__":
    main()

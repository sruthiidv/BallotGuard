import cv2, base64

def bgr_to_jpeg_base64(img_bgr, quality: int = 90) -> str | None:
    if img_bgr is None:
        return None
    ok, buf = cv2.imencode(".jpg", img_bgr, [int(cv2.IMWRITE_JPEG_QUALITY), quality])
    if not ok:
        return None
    return base64.b64encode(buf.tobytes()).decode("ascii")

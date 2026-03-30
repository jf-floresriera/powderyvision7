# pipeline.py - PowderyVision7 simplificado
# - El panel "Recorte de hoja detectada" muestra: RECORTE (crop) + BOX + TEXTO (grande) estilo tu ejemplo
# - leaf_crop_path = crop limpio (sin box) para uso interno/depuración
# - Mensaje mejorado cuando la confianza es baja (EN/ES)
# - Recorte más focalizado:
#     (1) usa bbox "tight" de la MÁSCARA (si existe) -> más cerrado que pred.boxes
#     (2) opcional: shrink adicional configurable
#     (3) opción: elegir componente más cercano al centro (útil cuando hay varias hojas)

import os
import time
import cv2
import numpy as np
from ultralytics import YOLO
from segment_mildew import segmentar_lesiones

CLS_MODEL_PATH = "models/yolo11m-cls_best.pt"
SEG_MODEL_PATH = "models/yolo11n_leaf_seg_win.pt"

CLASS_INFO = {
    "pea_healthy": {
        "species": "pea", "crop_name_es": "Arveja",
        "status": "healthy", "status_es": "sana",
        "disease": None, "disease_es": None
    },
    "pea_powderymildew": {
        "species": "pea", "crop_name_es": "Arveja",
        "status": "diseased", "status_es": "enferma",
        "disease": "powdery mildew", "disease_es": "mildiu polvoso"
    },
    "tomato_healthy": {
        "species": "tomato", "crop_name_es": "Tomate",
        "status": "healthy", "status_es": "sana",
        "disease": None, "disease_es": None
    },
    "tomato_powderymildew": {
        "species": "tomato", "crop_name_es": "Tomate",
        "status": "diseased", "status_es": "enferma",
        "disease": "powdery mildew", "disease_es": "mildiu polvoso"
    },
    "background": {
        "species": None, "crop_name_es": None,
        "status": "background", "status_es": "sin_hoja"
    }
}

CLASES_SANAS = {"pea_healthy", "tomato_healthy"}
CLASE_BACKGROUND = "background"

# Umbral mínimo para aceptar el box de hoja (si te está bloqueando, bájalo a 0.25–0.35)
CONF_MIN_LEAF = 0.50

# Umbrales de tamaño "razonable" del box (para evitar cajas gigantes)
MAX_AREA_RATIO = 0.55   # >55% del área de la imagen = demasiado grande
MIN_AREA_RATIO = 0.01   # <1% del área = ruido (ajusta si las hojas son pequeñas)

# ========= RECORTE MÁS FOCALIZADO =========
# 0.10–0.35 (más alto = recorte más cerrado)
SHRINK_PCT = 0.18

# Si True: cuando hay varios componentes en la máscara, elige el más cercano al centro
# (suele ayudar a quedarte con UNA hoja cuando hay varias)
PICK_CC_NEAREST_CENTER = True

# ========= ESTILO DE BOX/TEXTO EN EL RECORTE (como tu ejemplo) =========
PURPLE = (128, 0, 128)   # BGR morado
BOX_THICK = 20           # grosor del borde
FONT_SCALE = 2.2         # sube a 3.0 o 4.0 si lo quieres aún más grande
TEXT_THICK = 6           # sube a 8–12 si lo quieres aún más grueso
LABEL_PAD = 16           # padding del fondo del texto
LABEL_BORDER_THICK = 6   # borde morado del fondo de etiqueta

# Cargar modelos una sola vez
cls_model = YOLO(CLS_MODEL_PATH)
seg_model = YOLO(SEG_MODEL_PATH)


def bilingual(en: str, es: str) -> str:
    """Formato estándar: English / Español"""
    return f"{en} / {es}"


def _shrink_box(x1, y1, x2, y2, H, W, shrink_pct=0.18):
    """Encoge el box hacia adentro para un recorte más focalizado."""
    bw = x2 - x1
    bh = y2 - y1
    if bw <= 0 or bh <= 0:
        return x1, y1, x2, y2

    dx = int(bw * shrink_pct / 2.0)
    dy = int(bh * shrink_pct / 2.0)

    x1s = x1 + dx
    y1s = y1 + dy
    x2s = x2 - dx
    y2s = y2 - dy

    # Evitar que quede demasiado pequeño
    min_w = max(40, int(bw * 0.25))
    min_h = max(40, int(bh * 0.25))

    if (x2s - x1s) < min_w:
        cx = (x1 + x2) // 2
        x1s = cx - min_w // 2
        x2s = cx + min_w // 2

    if (y2s - y1s) < min_h:
        cy = (y1 + y2) // 2
        y1s = cy - min_h // 2
        y2s = cy + min_h // 2

    # Clip
    x1s = max(0, min(x1s, W - 1))
    x2s = max(1, min(x2s, W))
    y1s = max(0, min(y1s, H - 1))
    y2s = max(1, min(y2s, H))

    if x2s <= x1s or y2s <= y1s:
        return x1, y1, x2, y2

    return x1s, y1s, x2s, y2s


def _tight_bbox_from_mask(mask_bin, H, W):
    """
    Calcula bbox tight (x1,y1,x2,y2) a partir de máscara binaria (0/255).
    x2,y2 son exclusivos (útiles para slicing).
    """
    if mask_bin is None:
        return None
    ys, xs = np.where(mask_bin > 0)
    if len(xs) == 0 or len(ys) == 0:
        return None

    x1 = int(xs.min()); x2 = int(xs.max()) + 1
    y1 = int(ys.min()); y2 = int(ys.max()) + 1

    x1 = max(0, min(x1, W - 1))
    x2 = max(1, min(x2, W))
    y1 = max(0, min(y1, H - 1))
    y2 = max(1, min(y2, H))

    if x2 <= x1 or y2 <= y1:
        return None
    return x1, y1, x2, y2


def _pick_cc_from_mask(mask_bin, pick_nearest_center=True):
    """
    mask_bin: uint8 (0/255)
    Retorna: máscara (0/255) de un SOLO componente conectado.
    Si pick_nearest_center=True, elige el componente cuyo centro está más cerca del centro de la imagen.
    Si False, elige el componente de mayor área.
    """
    if mask_bin is None or mask_bin.size == 0:
        return mask_bin

    m = (mask_bin > 0).astype(np.uint8)
    n, labels, stats, centroids = cv2.connectedComponentsWithStats(m, connectivity=8)

    if n <= 1:
        return mask_bin

    H, W = m.shape[:2]
    cx_img, cy_img = (W / 2.0), (H / 2.0)

    best_label = None
    best_score = None

    for lab in range(1, n):
        area = float(stats[lab, 4])
        cx, cy = centroids[lab]

        if pick_nearest_center:
            dist2 = (cx - cx_img) ** 2 + (cy - cy_img) ** 2
            score = dist2 / max(area, 1.0)
            if best_score is None or score < best_score:
                best_score = score
                best_label = lab
        else:
            if best_score is None or area > best_score:
                best_score = area
                best_label = lab

    out = np.zeros_like(m, dtype=np.uint8)
    out[labels == best_label] = 255
    return out


def run_full_pipeline(bgr_image, save_root="static/results", prefix="img"):
    os.makedirs(save_root, exist_ok=True)

    # Guardar original
    orig_path = os.path.join(save_root, f"{prefix}_orig.png")
    cv2.imwrite(orig_path, bgr_image)

    # ----- 1) CLASIFICACIÓN -----
    t0 = time.time()
    cls_results = cls_model(bgr_image, verbose=False)
    t1 = time.time()
    pred_cls = cls_results[0]

    top_idx = int(pred_cls.probs.top1)
    top_conf = float(pred_cls.probs.top1conf)
    cls_name = cls_model.names[top_idx]
    cls_time_ms = (t1 - t0) * 1000

    info = CLASS_INFO.get(cls_name, {})
    salida = {
        "ok": True,
        "cls_name": cls_name,
        "cls_conf": top_conf,
        "cls_time_ms": cls_time_ms,
        "species": info.get("species"),
        "crop_name_es": info.get("crop_name_es"),
        "status": info.get("status"),
        "status_es": info.get("status_es"),
        "disease": info.get("disease"),
        "disease_es": info.get("disease_es"),

        # Imágenes
        "orig_img_path": "/" + orig_path.replace("\\", "/"),
        "crop_img_path": None,       # recorte con caja + texto grande
        "leaf_crop_path": None,      # crop limpio
        "seg_vis_path": None,
        "panel_img_path": None,

        # Estado
        "seg_ok": False,
        "leaf_conf": 0.0,
        "leaf_box_xyxy": None,
        "seg_time_ms": 0.0,
        "severidad_pct": 0.0,
        "is_healthy": False,
        "msg": None,
    }

    # Si es background
    if cls_name == CLASE_BACKGROUND:
        salida["ok"] = False
        salida["msg"] = bilingual(
            "No leaf detected in the image (background class).",
            "No se detectó una hoja en la imagen (clase background)."
        )
        return salida

    # Si es sana, no seguimos
    if cls_name in CLASES_SANAS:
        salida["is_healthy"] = True
        return salida

    # ----- 2) DETECCIÓN/SEGMENTACIÓN DE HOJA -----
    t2 = time.time()
    seg_results = seg_model(bgr_image, verbose=False)
    t3 = time.time()
    salida["seg_time_ms"] = (t3 - t2) * 1000

    pred = seg_results[0]
    if pred.boxes is None or len(pred.boxes) == 0:
        salida["ok"] = False
        salida["msg"] = bilingual(
            "Leaf detection failed (empty boxes).",
            "No se pudo detectar la hoja para hacer el recorte (boxes vacíos)."
        )
        return salida

    boxes = pred.boxes
    confs = boxes.conf.detach().cpu().numpy()
    xyxy_all = boxes.xyxy.detach().cpu().numpy()

    H, W = bgr_image.shape[:2]
    img_area = float(H * W)

    candidates = []
    for i in range(len(xyxy_all)):
        x1, y1, x2, y2 = map(int, xyxy_all[i])

        x1 = max(0, min(x1, W - 1))
        x2 = max(1, min(x2, W))
        y1 = max(0, min(y1, H - 1))
        y2 = max(1, min(y2, H))

        bw = max(0, x2 - x1)
        bh = max(0, y2 - y1)
        if bw == 0 or bh == 0:
            continue

        area_ratio = (bw * bh) / img_area
        if MIN_AREA_RATIO <= area_ratio <= MAX_AREA_RATIO:
            candidates.append((i, float(confs[i]), float(area_ratio), x1, y1, x2, y2))

    if len(candidates) == 0:
        best_i = int(np.argmax(confs))
        best_conf = float(confs[best_i])
        x1, y1, x2, y2 = map(int, xyxy_all[best_i])

        x1 = max(0, min(x1, W - 1))
        x2 = max(1, min(x2, W))
        y1 = max(0, min(y1, H - 1))
        y2 = max(1, min(y2, H))
    else:
        candidates = sorted(candidates, key=lambda t: (-t[1], t[2]))
        best_i, best_conf, _, x1, y1, x2, y2 = candidates[0]

    # Confianza baja (MENSAJE EN/ES)
    if best_conf < CONF_MIN_LEAF:
        salida["ok"] = False
        salida["msg"] = bilingual(
            f"Low-confidence leaf detection (conf={best_conf:.2f} < {CONF_MIN_LEAF:.2f}). "
            "Please retake the photo with better focus and closer to the leaf.",
            f"La hoja fue detectada con baja confianza (conf={best_conf:.2f} < {CONF_MIN_LEAF:.2f}). "
            "Por favor, vuelve a tomar la fotografía con un mejor enfoque y más cerca de la hoja."
        )
        return salida

    if x2 <= x1 or y2 <= y1:
        salida["ok"] = False
        salida["msg"] = bilingual(
            f"Invalid bounding box (xyxy): {(x1, y1, x2, y2)}",
            f"Caja inválida (xyxy): {(x1, y1, x2, y2)}"
        )
        return salida

    # ===== bbox tight desde máscara =====
    mask_bin = None
    if pred.masks is not None:
        try:
            m = pred.masks.data[int(best_i)].detach().cpu().numpy()
            m = (m > 0.5).astype(np.uint8) * 255
            mask_bin = cv2.resize(m, (W, H), interpolation=cv2.INTER_NEAREST)
            mask_bin = _pick_cc_from_mask(mask_bin, pick_nearest_center=PICK_CC_NEAREST_CENTER)
        except Exception:
            mask_bin = None

    tight = _tight_bbox_from_mask(mask_bin, H, W) if mask_bin is not None else None
    if tight is not None:
        x1, y1, x2, y2 = tight

    # Shrink adicional
    x1, y1, x2, y2 = _shrink_box(x1, y1, x2, y2, H, W, shrink_pct=SHRINK_PCT)

    bw2 = max(1, x2 - x1)
    bh2 = max(1, y2 - y1)
    area_ratio2 = (bw2 * bh2) / img_area

    salida["leaf_conf"] = float(best_conf)
    salida["leaf_box_xyxy"] = [int(x1), int(y1), int(x2), int(y2)]
    salida["seg_ok"] = True

    # --- Crop limpio ---
    crop_bgr = bgr_image[y1:y2, x1:x2].copy()
    if crop_bgr.size == 0:
        salida["ok"] = False
        salida["msg"] = bilingual(
            "Empty crop. Please check bounding box coordinates.",
            "El recorte quedó vacío (revisa coordenadas del box)."
        )
        return salida

    crop_path = os.path.join(save_root, f"{prefix}_leaf_crop.png")
    cv2.imwrite(crop_path, crop_bgr)
    salida["leaf_crop_path"] = "/" + crop_path.replace("\\", "/")

    # --- Crop con box + texto grande ---
    boxed_crop = crop_bgr.copy()
    ch, cw = boxed_crop.shape[:2]

    cv2.rectangle(boxed_crop, (0, 0), (cw - 1, ch - 1), PURPLE, BOX_THICK)

    label = f"leaf  conf={best_conf:.2f}  area={area_ratio2:.2f}"

    (tw, th), baseline = cv2.getTextSize(
        label, cv2.FONT_HERSHEY_SIMPLEX, FONT_SCALE, TEXT_THICK
    )

    x_text = 10
    y_text = max(th + 20, 40)

    x2_bg = min(cw - 1, x_text + tw + LABEL_PAD)
    y1_bg = max(0, y_text - th - LABEL_PAD)
    y2_bg = min(ch - 1, y_text + baseline + LABEL_PAD)

    cv2.rectangle(boxed_crop, (x_text, y1_bg), (x2_bg, y2_bg), (255, 255, 255), -1)
    cv2.rectangle(boxed_crop, (x_text, y1_bg), (x2_bg, y2_bg), PURPLE, LABEL_BORDER_THICK)

    cv2.putText(
        boxed_crop,
        label,
        (x_text + 8, y_text),
        cv2.FONT_HERSHEY_SIMPLEX,
        FONT_SCALE,
        PURPLE,
        TEXT_THICK,
        cv2.LINE_AA
    )

    boxed_path = os.path.join(save_root, f"{prefix}_leaf_boxed.png")
    cv2.imwrite(boxed_path, boxed_crop)
    salida["crop_img_path"] = "/" + boxed_path.replace("\\", "/")

    # ----- 3) SEGMENTACIÓN MILDIU EN CROP -----
    crop_rgb = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2RGB)

    seg_data = segmentar_lesiones(crop_rgb)
    panel = seg_data["panel"]
    severidad = float(seg_data["severidad"])

    panel_bgr = cv2.cvtColor(panel, cv2.COLOR_RGB2BGR)
    panel_path = os.path.join(save_root, f"{prefix}_panel.png")
    cv2.imwrite(panel_path, panel_bgr)

    salida["panel_img_path"] = "/" + panel_path.replace("\\", "/")
    salida["seg_vis_path"] = salida["panel_img_path"]
    salida["severidad_pct"] = severidad
    salida["is_healthy"] = False

    return salida
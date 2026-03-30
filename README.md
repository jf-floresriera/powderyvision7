
# PowderyVision7

PowderyVision7 is a web application built with **Flask** and **YOLO-based** computer vision models to detect and estimate the severity of **powdery mildew** on **pea** and **tomato** leaves.

The tool is designed as a support system for farmers, students, and technicians, and as an applied AI demonstrator for plant disease detection.

---

## Goal

- Automatically detect powdery mildew symptoms on leaves.  
- Estimate the **percentage of affected leaf area** (disease severity).  
- Provide a clear, multilingual interface.  
- Integrate leaf detection, segmentation, classification, and visual explanation in a single pipeline.

---

## How it works

The application performs several steps:

- Leaf detection and segmentation with a YOLO segmentation model.  
- Health status classification (healthy leaf vs. leaf with powdery mildew).  
- Severity estimation based on the affected area.  
- Display of key metrics:
  - YOLO class and confidence (%).  
  - Classification and segmentation times.  
  - Leaf detection confidence.  
  - Estimated powdery mildew severity (% of leaf area).

Usage flow:

1. Go to the **Input** tab.  
2. Upload a pea or tomato leaf image.  
3. Click **Analyze**.  
4. Inspect results, segmentation masks, and complementary analysis.

---

## Image guidelines

- Use only **pea** or **tomato** leaves.  
- Prefer good lighting, simple background, and sharp focus.  
- Keep the camera stable when taking the photo.  
- Check the preview before running the analysis.

---

## Online demo

The app is deployed as a Hugging Face Space:

`jf-floresriera / powderyvision7`  
(Add the full Space URL here.)

---

## Run locally

Requirements:

- Python 3.10+  
- `git` and `git-lfs`  
- Dependencies listed in `requirements.txt`

```bash
git clone https://github.com/jf-floresriera/powderyvision7.git
cd powderyvision7

git lfs install

python3 -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate

pip install -r requirements.txt
python app.py
```

Open in your browser: `http://127.0.0.1:5000`

---

## Project structure

```text
powderyvision7/
├── app.py
├── pipeline.py
├── generate_icons.py
├── models/
├── static/
├── templates/
├── requirements.txt
├── Dockerfile
└── README.md
```

---

## Metrics in the UI

For each analyzed image, the interface reports:

- Inferred crop / species (pea or tomato).  
- Health status (healthy leaf or leaf with powdery mildew).  
- YOLO class and confidence (%).  
- Inference times (classification and segmentation).  
- Leaf detection confidence.  
- Estimated powdery mildew severity (% of leaf area).

> All recommendations are indicative and must be validated with a local professional before making management decisions.

---

## Languages

The interface and messages are available in:

- Spanish  
- English  
- Portuguese  

---

## Credits

Developed at the **Agrocomputation and Epidemiological Analysis Lab 227**, Faculty of Agricultural Sciences, **National University of Colombia, Bogotá campus**.

Leaf images were collected by the author in crops related to the faculty’s **circular economy** project.

---

## Author

**Jesús Enrique Flores Riera**

- LinkedIn: https://www.linkedin.com/in/flores-riera/  
- Email: jesusenriqueflores36@gmail.com  
- Hugging Face: https://huggingface.co/jf-floresriera  
- GitHub: https://github.com/jf-floresriera

# PowderyVision7

PowderyVision7 es una aplicación web basada en **Flask** y modelos **YOLO** para detectar y estimar la severidad de **mildiu polvoso (oídio)** en hojas de **arveja** y **tomate** mediante visión por computador.

La herramienta está pensada como apoyo para agricultores, estudiantes y técnicos, y también como plataforma de demostración de IA aplicada a fitopatología.

---

## Objetivo

- Detectar automáticamente la presencia de mildiu polvoso en hojas.
- Estimar la **severidad (%)** del daño sobre el área foliar.
- Proveer una interfaz clara, multilingüe y orientada al usuario.
- Integrar todas las etapas: detección de hoja, segmentación, clasificación y explicación visual.

---

## Cómo funciona

La aplicación combina varios pasos de visión por computador:

- Detección y segmentación de la hoja con un modelo YOLO de segmentación.
- Clasificación del estado sanitario (hoja sana vs. hoja con mildiu).
- Cálculo de la severidad estimada a partir del área afectada.
- Visualización de métricas clave:
  - Clase YOLO y confianza (%).
  - Tiempos de clasificación y segmentación.
  - Confianza en la detección de la hoja.
  - Severidad estimada sobre el área foliar.

Flujo de uso:

1. Ir a la pestaña **Input**.  
2. Subir una imagen de hoja (arveja o tomate).  
3. Hacer clic en **Analyze**.  
4. Revisar resultados, segmentación y análisis complementario.

---

## Recomendaciones para las imágenes

- Utilizar solo hojas de **arveja** o **tomate**.  
- Buena iluminación, fondo sencillo y hoja enfocada.  
- Mantener la cámara estable.  
- Confirmar la vista previa antes de iniciar el análisis.

---

## Demo en línea

Aplicación desplegada como Space en Hugging Face:

`jf-floresriera / powderyvision7`  
(Agrega aquí el enlace completo al Space.)

---

## Ejecución local

Requisitos:

- Python 3.10 o superior  
- `git` y `git-lfs`  
- Dependencias de `requirements.txt`

Pasos:

```bash
git clone https://github.com/jf-floresriera/powderyvision7.git
cd powderyvision7

git lfs install  # opcional, si usas modelos grandes

python3 -m venv venv
source venv/bin/activate   # En Windows: venv\Scripts\activate

pip install -r requirements.txt
python app.py
```

Luego abrir en el navegador:

- `http://127.0.0.1:5000`

---

## Estructura del proyecto

```text
powderyvision7/
├── app.py                # Aplicación Flask principal
├── pipeline.py           # Pipeline de inferencia
├── generate_icons.py     # Utilidades para iconos/recursos
├── models/               # Modelos YOLO y pesos entrenados
├── static/               # CSS, JS, imágenes estáticas y resultados
├── templates/            # Plantillas HTML
├── requirements.txt      # Dependencias de Python
├── Dockerfile            # Despliegue en contenedor
└── README.md             # Documentación del proyecto
```

---

## Métricas mostradas

Tras analizar una imagen, la interfaz muestra:

- Especie / cultivo inferido.  
- Estado sanitario:
  - Hoja sana.  
  - Hoja con mildiu polvoso.  
- Clase YOLO con su confianza (%).  
- Tiempo de clasificación y de segmentación.  
- Confianza en la detección de la hoja.  
- Severidad estimada de mildiu (%) sobre el área foliar.

> Las recomendaciones son orientativas y deben validarse siempre con un profesional local.

---

## Idiomas

La aplicación ofrece mensajes y resultados en:

- Español  
- Inglés  
- Portugués  

---

## Uso responsable

Esta herramienta no sustituye el diagnóstico profesional.  
Está pensada como apoyo al manejo de enfermedades, a la docencia y a la investigación en fitopatología y agrocomputación.

---

## Créditos y agradecimientos

Trabajo desarrollado en el **Laboratorio de Agrocomputación y Análisis Epidemiológico 227**, Facultad de Ciencias Agrarias, **Universidad Nacional de Colombia, sede Bogotá**.

Las imágenes del proyecto fueron capturadas por el autor en cultivos vinculados al proyecto de **economía circular** de la facultad.

Agradecimientos a:

- Helber Balaguera  
- Rodrigo Gil Catañeda  
- Joaquín Guillermo Ramírez  
- Nicolás Duarte Cano  

---

## Autor

**Jesús Enrique Flores Riera**

- LinkedIn: https://www.linkedin.com/in/flores-riera/  
- Correo: jesusenriqueflores36@gmail.com  
- Hugging Face: https://huggingface.co/jf-floresriera  
- GitHub: https://github.com/jf-floresriera

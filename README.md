# 🔍 Deepfake Detective: AI Media Forensics & News Verification

### An AI-powered platform for detecting manipulated media and verifying online information.

Deepfake Detective is an AI-powered media investigation and news verification platform designed to help users examine potentially manipulated images, videos, and audio recordings while checking the credibility of online news and factual claims.

The project combines machine learning, deep learning, media analysis, and evidence-based verification techniques to provide users with useful information about suspicious digital content.

---

## 🌟 1. Project Overview

With the rapid development of artificial intelligence, creating realistic synthetic images, videos, and audio recordings has become increasingly accessible.

Although generative AI has many positive applications, it can also be misused to create misleading media, impersonate individuals, and spread misinformation.

Traditional verification methods can be time-consuming and difficult for ordinary users.

**Deepfake Detective** addresses this problem by bringing multiple media investigation and information verification features together in one platform.

### 🎯 Problem Statement

The increasing availability of AI-generated media and misleading online information creates challenges in identifying manipulated content and verifying the authenticity of digital information.

There is a need for an accessible platform that assists users in investigating suspicious media and evaluating factual claims using AI-based analysis and supporting evidence.

### 💡 Proposed Solution

Deepfake Detective provides a unified platform that:

* Screens images for possible AI generation.
* Analyzes video content using sampled frames.
* Examines audio recordings for possible synthetic speech.
* Extracts information from online news articles.
* Checks claims against published fact-checking records.
* Searches for supporting and contradicting evidence.
* Generates investigation results through an interactive dashboard.
* Provides downloadable investigation reports.

---

## ⚙️ 2. Key Features

### 🖼️ AI Image Detection

* Upload images for AI-generated media screening.
* Uses the Detectra image detection model.
* Processes images using resizing, cropping, and normalization.
* Displays the predicted classification and confidence score.
* Provides an assessment note explaining the experimental nature of the result.

### 🎥 AI Video Detection

* Upload videos for investigation.
* Extracts and analyzes video frames.
* Samples up to 9 frames uniformly across the video.
* Combines frame-level findings to provide an overall assessment.

### 🎙️ AI Audio Detection

* Upload audio recordings for analysis.
* Uses a pretrained voice fake detection model.
* Processes audio using ONNX Runtime.
* Displays model predictions and confidence scores.
* Helps screen recordings for possible AI-generated speech.

### 📰 News Verification

* Accepts public news article URLs.
* Extracts article content when website access permits.
* Allows users to paste article text manually when automatic extraction is unavailable.
* Helps identify factual claims for further investigation.

### 🔎 Evidence-Based Fact Verification

* Searches for supporting and contradicting information.
* Uses Tavily Search API for evidence discovery.
* Uses Google Fact Check Tools API to retrieve existing fact-check reviews.
* Uses Google Gemini models to assist with evidence evaluation.
* Provides three possible verdicts:

  * **Supported:** Available evidence supports the claim.
  * **Contradicted:** Available evidence conflicts with the claim.
  * **Unverified:** Available evidence is insufficient to reach a reliable conclusion.

### 📊 Investigation Dashboard

* Interactive Streamlit interface.
* Displays media analysis and verification results.
* Organizes findings into understandable sections.
* Provides a downloadable PDF investigation report.

---

## 🧠 3. Technical Implementation & AI Models

The project combines pretrained machine learning models, ONNX inference, external APIs, and evidence-based verification.

### Image Detection Model

| Component          | Details                  |
| ------------------ | ------------------------ |
| Model Name         | Detectra                 |
| Model Repository   | `TensorFold/detectra-v1` |
| Model File         | `model.onnx`             |
| Runtime            | ONNX Runtime             |
| Execution Provider | CPU                      |
| Input Resolution   | 384 × 384 pixels         |

**Implementation:**

The image is converted into RGB format, resized, center-cropped, and normalized before being passed to the ONNX model.

The model output is converted into an AI-generated probability using a sigmoid function. The system then displays the predicted class and corresponding confidence score.

### Audio Detection Model

| Component        | Details                                 |
| ---------------- | --------------------------------------- |
| Model Name       | Voice Fake Detector                     |
| Model Repository | `Shanmugapriya6/voice-fake-detector-v1` |
| Model File       | `best_model.onnx`                       |
| Runtime          | ONNX Runtime                            |

**Implementation:**

The pretrained audio detection model is used to analyze uploaded audio recordings and classify them according to its available prediction labels.

The model is hosted separately because of its large file size.

### Video Detection

| Component        | Details                          |
| ---------------- | -------------------------------- |
| Model            | CakeLens                         |
| Model Identifier | V5                               |
| Analysis Method  | Frame-based analysis             |
| Frame Sampling   | Up to 9 uniformly sampled frames |

**Implementation:**

The video detector extracts frames at different points in the uploaded video and analyzes the selected frames.

The frame-level findings are used to generate an overall video assessment.

### News and Evidence Verification

| Component                | Technology / API            | Version or Identifier |
| ------------------------ | --------------------------- | --------------------- |
| Fact Checking            | Google Fact Check Tools API | `v1alpha1`            |
| Evidence Search          | Tavily Search API           | Advanced Search       |
| AI Evidence Verification | Google Gemini API           | `v1beta`              |

**Preferred Gemini models:**

* `gemini-2.5-flash`
* `gemini-2.5-flash-lite`
* `gemini-2.0-flash`

The application checks available Gemini models and selects an appropriate supported model.

**Implementation:**

1. Extract or receive the user's factual claim.
2. Search for relevant information using Tavily.
3. Retrieve existing fact-check reviews using Google Fact Check Tools.
4. Evaluate the available evidence using Gemini.
5. Generate an evidence-based verdict.

The system does not automatically classify a claim as false simply because supporting information cannot be found. Insufficient evidence results in an **Unverified** verdict.

---

## 🏗️ 4. System Architecture

The application follows a modular architecture, separating individual investigation features into different Python modules.

```text
                   DEEPFAKE DETECTIVE
                          |
                    Streamlit App
                          |
           +---------------+---------------+
           |               |               |
      Image Module    Video Module     Audio Module
           |               |               |
        Detectra       Frame-Based      Voice Fake
        ONNX Model      Analysis       Detector ONNX
           |               |               |
           +---------------+---------------+
                          |
                  News Verification
                          |
              +------------+------------+
              |            |            |
           Article       Fact Check    Evidence
          Extraction       API         Search
                                      |
                                   Gemini API
                          |
                    Results Dashboard
                          |
                    PDF Investigation
                        Report
```

### Project Structure

```text
Deepfake-Detective/
│
├── app.py
│
├── modules/
│   ├── image_detector.py
│   ├── image_detector_second.py
│   ├── video_detector.py
│   ├── audio_detector.py
│   ├── news_verifier.py
│   ├── metadata_analyzer.py
│   ├── fact_checker.py
│   └── evidence_verifier.py
│
├── models/
│   └── audio/
│       └── best_model.onnx
│
├── screenshots/
│
├── requirements.txt
├── .gitignore
└── README.md
```

*The audio model is downloaded separately and is not included in the GitHub repository.*

---

## 🛠️ 5. Technologies Used

| Technology                  | Purpose                         |
| --------------------------- | ------------------------------- |
| Python                      | Core programming language       |
| Streamlit                   | Interactive web application     |
| PyTorch                     | Machine learning framework      |
| Transformers                | Pretrained model support        |
| ONNX Runtime                | Model inference                 |
| Hugging Face Hub            | Model repository and downloads  |
| NumPy                       | Numerical processing            |
| Pillow                      | Image processing                |
| OpenCV                      | Video processing                |
| FFmpeg                      | Audio/video processing          |
| Google Gemini API           | AI-assisted evidence evaluation |
| Tavily Search API           | Evidence discovery              |
| Google Fact Check Tools API | Published fact-check retrieval  |
| ReportLab                   | PDF report generation           |

---

## 🚀 6. Installation & Setup

Follow these steps to run Deepfake Detective locally.

### Prerequisites

* Python 3.11 recommended.
* Git.
* FFmpeg.
* Internet connection for model downloads and external APIs.

### Step 1: Clone the Repository

```bash
git clone https://github.com/Diya9867/Deepfake-Detective.git
```

### Step 2: Open the Project Folder

```bash
cd Deepfake-Detective
```

### Step 3: Create a Virtual Environment

```bash
python -m venv venv
```

Activate it on Windows:

```bash
venv\Scripts\activate
```

### Step 4: Install Dependencies

```bash
pip install -r requirements.txt
```

Install additional application dependencies if they are not already included:

```bash
pip install streamlit reportlab onnxruntime huggingface_hub
```

### Step 5: Download the Audio Model

The audio model is hosted separately because of its large file size.

**Download Audio Detection Model:**

https://drive.google.com/file/d/1oI8UmchgaW8TlpchoDB2ptX6nzyJI4id/view?usp=sharing

Place the downloaded file in:

```text
models/audio/best_model.onnx
```

### Step 6: Install FFmpeg

Install FFmpeg and make sure its `bin` directory is added to your Windows PATH.

### Step 7: Run the Application

```bash
streamlit run app.py
```

The application will open in your browser.

---

## 📸 7. Application Screenshots

The following screenshots demonstrate the different features and working interface of Deepfake Detective.

### 🏠 Home Page

![Home Page 1](screenshots/home%20page.png.png)

![Home Page 2](screenshots/home%20page%202.png.png)

### 🖼️ Image Detection

![Image Detection 1](screenshots/image%201.png.png)

![Image Detection 2](screenshots/image%20investigation%202.png.png)

### 🎥 Video Detection

![Video Detection 1](screenshots/video%20investigation%201.png.png)

![Video Detection 2](screenshots/video%20investigation%202.png.png)

### 🎙️ Audio Detection

![Audio Detection 1](screenshots/audioinvestigation%201.png.png)

![Audio Detection 2](screenshots/audio%20invistdigation%202.png.png)

### 📰 News Verification

![News Verification 1](screenshots/news%201.png.png)

![News Verification 2](screenshots/news%202.png.png)

![News Verification 3](screenshots/news%203.png.png)

![News Verification 4](screenshots/news%204.png.png)

![News Verification 5](screenshots/news%205.png.png)

### 📊 Investigation Dashboard

![Dashboard 1](screenshots/dashboard%201.png.png)

![Dashboard 2](screenshots/dashboard%202.png.png)

---

## 📈 8. Testing & Results

The application has been tested locally to check its major features and model integration.

Testing includes:

* Image upload and AI-image screening.
* Audio upload and model inference.
* Video upload and frame-based analysis.
* News article extraction.
* Manual article text submission.
* Fact-check search and evidence retrieval.
* Evidence-based claim classification.
* PDF report generation.

### Result Interpretation

The application provides model predictions, confidence scores, and evidence-based findings to assist users in investigating digital content.

The displayed confidence scores represent model outputs and should not automatically be interpreted as verified real-world accuracy.

No overall accuracy percentage is claimed without a formal evaluation using a suitable labelled test dataset.

---

## 🌍 9. Real-World Impact & Usefulness

Deepfake Detective aims to make digital media investigation and information verification more accessible.

### Potential Applications

* **Students and Researchers:** Investigating AI-generated content and misinformation.
* **Journalists:** Supporting preliminary verification of digital media and online claims.
* **Social Media Users:** Examining suspicious images, videos, audio recordings, and news.
* **Digital Media Professionals:** Supporting initial media authenticity assessments.
* **General Public:** Developing awareness of manipulated media and misleading information.

### Social Impact

The project promotes responsible digital information consumption by encouraging users to investigate media rather than immediately trusting or sharing it.

It brings multiple verification capabilities into one accessible platform, reducing the need to use separate tools for every investigation.

---

## ⚠️ 10. Limitations

* AI detection results are probabilistic and may produce incorrect classifications.
* Detection performance can vary depending on image quality, compression, editing, and generation techniques.
* Video analysis uses sampled frames and may not identify every manipulation occurring between frames.
* Audio detection performance may vary across languages, recording conditions, and voice types.
* Some websites restrict automated article extraction or require authentication.
* Evidence search results may be incomplete or unavailable.
* An Unverified result does not mean that a claim is false.
* The application is an investigative assistance tool, not a substitute for professional forensic examination.

---

## 🔮 11. Future Scope

Future improvements may include:

* Testing models on larger and more diverse datasets.
* Improving multilingual audio detection.
* Adding more advanced video analysis techniques.
* Improving detection of manipulated regions within images.
* Adding additional independent fact-checking sources.
* Improving evidence ranking and source reliability assessment.
* Deploying the application on a scalable cloud platform.
* Expanding downloadable investigation reports.

---

## 🎬 12. Demo & Presentation

**GitHub Repository:**

https://github.com/Diya9867/Deepfake-Detective

---

## 👩‍💻 13. Developer

**Developed by:** Diya Dubey

**Project Name:** Deepfake Detective: AI Media Forensics & News Verification

**Domain:** Artificial Intelligence, Machine Learning, Digital Media Forensics, and Fact Verification.

---

## ⚖️ 14. Disclaimer

Deepfake Detective is an experimental AI-assisted investigation platform.

Its results are intended to support preliminary analysis and awareness. They should not be treated as definitive proof that media is authentic or manipulated, or that a factual claim is true or false.

Users should independently review the available evidence and consult appropriate experts when making important decisions.


# DevVocal: Real-Time Voice-Driven AI Workspace Agent

> **Submission Track:** Best Use of Speechmatics Bonus Award  
> **Tech Stack:** Python, Speechmatics Real-Time WebSocket API, Google GenAI SDK, SoundDevice, Pyttsx3

---

## 📺 Video Demo
[Watch DevVocal in Action](https://drive.google.com/file/d/117NGzgoFysc0kKWUDSGVg6vfUSau0dU0/view?usp=sharing)


## 🎯 Overview
Developers spend countless hours switching windows, typing repetitive CLI commands, and manually managing environments. **DevVocal** is an autonomous, hands-free desktop voice assistant built to turn real-time natural language into instant system execution.

Powered by **Speechmatics Real-Time WebSocket streaming**, DevVocal captures live microphone input, transcribes spoken commands with sub-second latency, resolves intent using advanced LLM reasoning, and autonomously runs terminal commands or answers technical questions—completely hands-free.

---

## ⚡ Architecture Flow

[ User Microphone ]
│
▼ (PCM 16-bit 16kHz Stream)
[ SoundDevice Raw Stream ]
│
▼ (Real-Time WebSocket)
[ Speechmatics Real-Time API ] ───► Ultra-Low Latency Transcription
│
▼ (Debounced Sentence Buffer)
[ Gemini Reasoning Engine ] ───► Intent Extraction & Safe Command Generation
│
┌────┴──────────────────────────┐
▼                               ▼
[ System CLI Execution ]     [ Offline TTS Audio Response ]
(e.g., git status, dir, code) (Real-Time Speaker Feedback)


---

## ✨ Key Features
* **Sub-Second Voice Ingestion:** Leverages Speechmatics' low-latency real-time API over persistent WebSockets.
* **Intelligent Sentence Debouncing:** Collects rapid-fire speech bursts and dynamically waits for natural conversational pauses before executing.
* **Self-Hearing Acoustic Lock:** Automatically mutes microphone capture during audio output to prevent audio feedback loops.
* **Resilient Model Routing:** Features automated fallback handling across model endpoints to ensure zero downtime during server traffic spikes.
* **Local System Control:** Maps complex voice intent to direct PowerShell/Bash terminal commands safely.

---

## 🚀 Quickstart

### 1. Prerequisites
* Python 3.10+
* Free API Keys: [Speechmatics Portal](https://portal.speechmatics.com/) and [Google AI Studio](https://aistudio.google.com/)

### 2. Installation
Clone the repository and install dependencies:
```bash
git clone [https://github.com/YOUR_USERNAME/devvocal-agent.git](https://github.com/YOUR_USERNAME/devvocal-agent.git)
cd devvocal-agent
python -m venv venv

# Windows
.\venv\Scripts\Activate.ps1

# Linux / macOS
source venv/bin/activate

pip install sounddevice numpy pyttsx3 google-genai speechmatics-rt python-dotenv
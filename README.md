🚨 Emergency Response Speech Translation Tool 
This project is an AI-powered emergency response tool developed for the Tamil Nadu Police.
It enables real-time speech-to-text, translation, and text-to-speech to help police officers communicate effectively with citizens across different languages during emergencies.

🎯 Purpose
Tamil Nadu is a multilingual state where citizens may speak Tamil, Hindi, English, or Telugu. During emergency calls or field interactions, language barriers can delay response times.

This tool bridges that gap by:

Converting speech to text from uploaded/recorded audio.

Detecting the spoken language automatically.

Translating the detected text into Tamil (for police use).

Converting text back into speech for faster communication.

Allowing reply recording so officers can respond instantly in the detected language.

Key Features
Speech-to-Text – Converts emergency call recordings or live input into text.
Language Detection – Identifies if the caller is speaking in Tamil, Hindi, English, or Telugu.
Translation – Automatically translates caller’s message into Tamil.
Text-to-Speech (TTS) – Reads out both caller’s message & police response for quick communication.
Reply Mode – Officers can record a reply in Tamil, which is instantly played back in the caller’s language.
User-Friendly Web App – Built with Flask and simple UI for fast adoption.

🛠️ Tech Stack
Backend: Python, Flask

Speech Recognition: speech_recognition (Google API)

Translation & Detection: googletrans, langdetect

Text-to-Speech: gTTS (Google Text-to-Speech)

Audio Handling: pydub, pygame

Frontend: Flask + Jinja Templates (HTML/CSS)


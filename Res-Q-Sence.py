import json
from flask import Flask, render_template, request, Response
import speech_recognition as sr
from googletrans import Translator, LANGUAGES
import os
from pydub import AudioSegment, silence
from gtts import gTTS
import tempfile
import pygame
from langdetect import detect

app = Flask(_name_)
translator = Translator()
recognizer = sr.Recognizer()

def detect_language(text):
    """Detects the language of a given text"""
    return detect(text)

def text_to_speech(text):
    """Convert text to speech and play it in real-time"""
    if not text.strip():
        print("⚠ The text is empty! Nothing to convert to speech.")
        return

    # Detect the language
    language = detect_language(text)
    print(f"🔍 Detected Language: {language}")

    # Convert text to speech
    tts = gTTS(text=text, lang=language, slow=False)

    # Create a temporary audio file
    temp_audio = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
    temp_audio_path = temp_audio.name
    temp_audio.close()
    
    # Save speech to temp file
    tts.save(temp_audio_path)

    # Play audio automatically
    play_audio(temp_audio_path)

    # Delete the temporary file after playing
    os.remove(temp_audio_path)

def play_audio(file_path):
    """Plays the given audio file"""
    pygame.mixer.init()
    pygame.mixer.music.load(file_path)
    pygame.mixer.music.play()

    # Wait until audio is finished playing
    while pygame.mixer.music.get_busy():
        continue

    pygame.mixer.quit()

@app.route('/')  
def home():
    return render_template('index.html')  

@app.route('/speech-to-text', methods=['POST'])
def speech_to_text():
    """Convert speech to text, detect language, and translate it"""
    if 'file' not in request.files:
        return Response(json.dumps({"error": "No audio file uploaded"}), mimetype="application/json")

    audio_file = request.files['file']
    audio_path = "temp_audio.wav"
    audio_file.save(audio_path)

    try:
        audio = AudioSegment.from_wav(audio_path)
        audio = audio.set_channels(1).set_frame_rate(16000).normalize()

        chunks = []
        chunk_length = 3000  
        silence_threshold = -40  
        hold_duration = 7000  

        start = 0
        while start < len(audio):
            end = start + chunk_length
            chunk = audio[start:end]

            silent_parts = silence.detect_silence(chunk, silence_thresh=silence_threshold, min_silence_len=hold_duration)
            if silent_parts:
                break 

            chunks.append(chunk)
            start += chunk_length

        detected_texts = []

        for index, chunk in enumerate(chunks):
            chunk_path = f"chunk_{index}.wav"
            chunk.export(chunk_path, format="wav")

            with sr.AudioFile(chunk_path) as source:
                recognizer.adjust_for_ambient_noise(source, duration=0.5)  
                audio_data = recognizer.record(source)

                try:
                    detected_text = recognizer.recognize_google(audio_data, language="hi-IN,en-IN,te-IN")
                except sr.UnknownValueError:
                    detected_text = ""
                except sr.RequestError as e:
                    return Response(json.dumps({"error": f"Speech recognition failed: {str(e)}"}), mimetype="application/json")

                detected_texts.append(detected_text)
            os.remove(chunk_path)  

    except sr.UnknownValueError:
        return Response(json.dumps({"error": "Speech recognition failed: Could not understand the audio"}), mimetype="application/json")
    except Exception as e:
        return Response(json.dumps({"error": f"Speech recognition failed: {str(e)}"}), mimetype="application/json")

    os.remove(audio_path)

    detected_lang = "Unknown"
    detected_lang_name = "Unknown"
    if detected_texts and detected_texts[0]:
        try:
            detected_lang = translator.detect(detected_texts[0]).lang
            detected_lang_name = LANGUAGES.get(detected_lang, "Unknown")
        except Exception:
            detected_lang = "Unknown"
            detected_lang_name = "Unknown"

    translated_texts = []
    for text in detected_texts:
        if text:
            try:
                translated_texts.append(text if detected_lang == 'ta' else translator.translate(text, src=detected_lang, dest='ta').text)
            except Exception:
                translated_texts.append("Translation Error")
        else:
            translated_texts.append("No Speech Detected")

    return render_template('output.html', original_texts=detected_texts, original_language=detected_lang_name, translated_texts=translated_texts, detected_language_code=detected_lang)
@app.route('/record-reply', methods=['POST'])
def record_reply():
    """Record a reply, detect its language, and play the recognized text as speech (without translation)"""

    # Get the detected language from the frontend
    detected_input_lang = request.form.get("detected_lang")  # Get language from request

    if not detected_input_lang:
        print("❌ Error: Detected language is missing.")
        return Response(json.dumps({"error": "Detected language is missing"}), mimetype="application/json")

    # *Convert language code for Google Speech Recognition*
    google_speech_languages = {
        "hi": "hi-IN",  # Hindi
        "ta": "ta-IN",  # Tamil
        "en": "en-IN"   # English (Indian)
    }
    
    recognition_lang = google_speech_languages.get(detected_input_lang, "en-IN")  # Default to English if not found

    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source, duration=1)  # Reduce noise
        try:
            print(f"🎙 Recording reply in {recognition_lang}... Speak now!")
            audio_data = recognizer.listen(source, timeout=15, phrase_time_limit=10)
            print("✅ Audio captured, processing...")

            # *Use detected input language for recognition*
            reply_text = recognizer.recognize_google(audio_data, language=recognition_lang)
            print(f"📝 Recognized Reply Text: {reply_text}")

            if not reply_text:
                return Response(json.dumps({"error": "No speech detected"}), mimetype="application/json")

        except sr.UnknownValueError:
            print("❌ Could not understand speech.")
            return Response(json.dumps({"error": "Could not understand the reply"}), mimetype="application/json")

        except sr.RequestError as e:
            print(f"❌ Speech recognition failed: {e}")
            return Response(json.dumps({"error": f"Speech recognition failed: {str(e)}"}), mimetype="application/json")

        except Exception as e:
            print(f"❌ General error: {e}")
            return Response(json.dumps({"error": f"Unexpected error: {str(e)}"}), mimetype="application/json")

    # *Play the recognized reply text directly (without translation)*
    try:
        print(f"🔊 Playing the recognized reply text: {reply_text}")

        tts = gTTS(text=reply_text, lang=detected_input_lang, slow=False)
        temp_audio_path = "static/reply_audio.mp3"
        tts.save(temp_audio_path)

        # *Auto-play the generated speech*
        os.system(f"start {temp_audio_path}")  # This works for Windows

        response_data = json.dumps({
            "reply_text": reply_text,
            "detected_language": detected_input_lang,
            "audio_url": "/" + temp_audio_path
        })

        return Response(response_data, mimetype="application/json")

    except Exception as e:
        print(f"❌ Error generating audio: {e}")
        return Response(json.dumps({"error": "Error generating audio"}), mimetype="application/json")

if _name_ == '_main_':
    app.run(debug=True)
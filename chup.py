import tkinter as tk
from tkinter import messagebox
from queue import Queue
from threading import Thread
import pyaudio
import json
from vosk import Model, KaldiRecognizer
import time
import cv2

messages = Queue()
recordings = Queue()

recording_label = None
output_text = None  # Declare output_text globally
recognition_model = None
recording_window = None

def load_model():
    model = Model(model_name="vosk-model-en-us-0.22")
    rec = KaldiRecognizer(model, 16000)
    rec.SetWords(True)
    return rec

recognition_model = load_model()

def start_recording():
    messages.put(True)
    recording_label.config(text="Recording... Speak Now")
    record = Thread(target=record_microphone)
    record.start()
    transcribe = Thread(target=speech_recognition)
    transcribe.start()

def stop_recording():
    messages.get()
    recording_label.config(text="Recording stopped")
    # Optionally, you can stop the recording thread here if needed

def open_record_window():
    welcome_window.withdraw()  # Hide the welcome window
    global recording_window, output_text
    recording_window = tk.Toplevel()
    recording_window.title("Voice Recorder")
    recording_window.attributes('-fullscreen', True)
    recording_window.configure(bg='#ADD8E6')  # Light Blue background color

    # Center the window on the screen
    window_width = recording_window.winfo_reqwidth()
    window_height = recording_window.winfo_reqheight()
    screen_width = recording_window.winfo_screenwidth()
    screen_height = recording_window.winfo_screenheight()

    x = (screen_width // 2) - (window_width // 2)
    y = (screen_height // 2) - (window_height // 2)

    recording_window.geometry("+%d+%d" % (x, y))

    global recording_label
    recording_label = tk.Label(recording_window, text="", bg='#ADD8E6', font=("Helvetica", 18))
    recording_label.pack(pady=20)

    instructions_text = """
    Please speak in the given format:
    My Name is [Your Name]
    I am [age] years old
    I would like to be verified 
    My social security number is [your number]

    After the audio recording, you will be redirected to click your have your picture taken
    """
    instructions_label = tk.Label(recording_window, text=instructions_text, bg='#ADD8E6', font=("Helvetica", 14))
    instructions_label.pack(pady=20)

    record_button = tk.Button(recording_window, text="Record", command=start_recording, font=("Helvetica", 16))
    record_button.pack(pady=20)

    stop_button = tk.Button(recording_window, text="Stop", command=stop_recording, font=("Helvetica", 16))
    stop_button.pack(pady=20)

    global output_text
    output_text = tk.Text(recording_window, height=10, width=50, font=("Helvetica", 14))
    output_text.pack(pady=20)

    save_button = tk.Button(recording_window, text="Save Transcription", command=lambda: save_transcription_to_file(output_text), font=("Helvetica", 16))
    save_button.pack(pady=20)

    close_button = tk.Button(recording_window, text="Close", command=close_recording_window, font=("Helvetica", 16))
    close_button.pack(pady=20)

def close_recording_window():
    recording_window.destroy()
    open_capture_window()

def open_capture_window():
    cam = cv2.VideoCapture(0)
    cv2.namedWindow("Press Escape to close")

    img_counter = 0
    while True:
        ret, frame = cam.read()

        if not ret:
            print("Failed to grab frame")
            break

        cv2.imshow("Press Spacebar to click picture (Press escape after picture is taken)", frame)

        k = cv2.waitKey(1)

        if k % 256 == 27:
            print("Escape hit, closing the app")
            thank_you_window()
            break

        elif k % 256 == 32:
            img_name = "opencv_frame_{}.png".format(img_counter)
            cv2.imwrite(img_name, frame)
            print("Image taken")
            img_counter += 1

    cam.release()
    cv2.destroyAllWindows()

def thank_you_window():
    thank_you_window = tk.Toplevel()
    thank_you_window.title("Thank You")
    thank_you_window.attributes('-fullscreen', True)
    thank_you_window.configure(bg='#ADD8E6')  # Light Blue background color

    # Center the window on the screen
    window_width = thank_you_window.winfo_reqwidth()
    window_height = thank_you_window.winfo_reqheight()
    x = (screen_width // 2) - (window_width // 2)
    y = (screen_height // 2) - (window_height // 2)

    thank_you_window.geometry("+%d+%d" % (x, y))

    thank_you_label = tk.Label(thank_you_window, text="Thank You!", font=("Helvetica", 24), bg='#ADD8E6')
    thank_you_label.pack(pady=(screen_height // 4, 40))

    thank_you_window.after(3000, lambda: thank_you_window.destroy())  # Close the window after 3 seconds

# Record and transcribe
CHANNELS = 1
FRAME_RATE = 16000
RECORD_SECONDS = 15
AUDIO_FORMAT = pyaudio.paInt16
SAMPLE_SIZE = 2

def record_microphone(chunk=1024):
    p = pyaudio.PyAudio()

    stream = p.open(format=AUDIO_FORMAT,
                    channels=CHANNELS,
                    rate=FRAME_RATE,
                    input=True,
                    frames_per_buffer=chunk)

    frames = []

    while not messages.empty():
        data = stream.read(chunk)
        frames.append(data)
        if len(frames) >= (FRAME_RATE * RECORD_SECONDS) / chunk:
            recordings.put(frames.copy())
            frames = []

    stream.stop_stream()
    stream.close()
    p.terminate()

def speech_recognition():
    while not messages.empty() and recording_window:
        frames = recordings.get()
        recognition_model.AcceptWaveform(b''.join(frames))
        result = json.loads(recognition_model.Result())
        text = result.get('text', '')
        update_output_text(text)
        time.sleep(0.5)  # Adjusted sleep time for faster recognition

def update_output_text(text):
    if output_text:
        output_text.insert(tk.END, text + "\n")
        output_text.see(tk.END)

def save_transcription_to_file(output_text_widget):
    transcription = output_text_widget.get("1.0", tk.END)
    with open("transcription.txt", "w") as file:
        file.write(transcription)

# Create a welcome window with both functionalities
welcome_window = tk.Tk()
welcome_window.title("Online KYC Assistant")
welcome_window.attributes('-fullscreen', True)
welcome_window.configure(bg='#ADD8E6')  # Light Blue background color

# Center the window on the screen
window_width = welcome_window.winfo_reqwidth()
window_height = welcome_window.winfo_reqheight()
screen_width = welcome_window.winfo_screenwidth()
screen_height = welcome_window.winfo_screenheight()

x = (screen_width // 2) - (window_width // 2)
y = (screen_height // 2) - (window_height // 2)

welcome_window.geometry("+%d+%d" % (x, y))

welcome_label = tk.Label(welcome_window, text="Welcome to Online KYC Assistant", font=("Helvetica", 22), bg='#ADD8E6')
welcome_label.pack(pady=(screen_height // 4, 40))  # Adjust the padding to center vertically

record_button = tk.Button(welcome_window, text="Record Voice", command=open_record_window, font=("Helvetica", 18))
record_button.pack(pady=20)

welcome_window.mainloop()
    
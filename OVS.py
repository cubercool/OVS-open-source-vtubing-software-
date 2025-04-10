#by cubercool7, (place your name here for now)
import pygame
import sys
import sounddevice as sd
import numpy as np
import tkinter as tk
from tkinter import filedialog, Scale, ttk
import time
import random

# Global variables
idle_image_path = 'idle.png'
talking_image_path = 'talking.png'
blink_image_path = 'blink.png'
talking_multiplier = 3.0
baseline_noise_level = 0.0
is_talking = False
is_blinking = False
blink_duration = 0.2
blink_timer = 0.0
blink_interval = random.uniform(3, 8)
audio_stream = None
screen = None
running_pygame = False
current_image = None
idle_pygame_image = None
talking_pygame_image = None
blink_pygame_image = None
silence_counter = 0

def load_images():
    global idle_pygame_image, talking_pygame_image, blink_pygame_image
    try:
        idle_pygame_image = pygame.image.load(idle_image_path).convert_alpha()
        talking_pygame_image = pygame.image.load(talking_image_path).convert_alpha()
        blink_pygame_image = pygame.image.load(blink_image_path).convert_alpha()
    except pygame.error as e:
        tk.messagebox.showerror("Image Load Error", f"Error loading images: {e}")
        idle_pygame_image = None
        talking_pygame_image = None
        blink_pygame_image = None

def select_idle_image():
    global idle_image_path
    file_path = filedialog.askopenfilename(defaultextension=".png", filetypes=[("PNG files", "*.png"), ("All files", "*.*")])
    if file_path:
        idle_image_path = file_path
        idle_image_label.config(text=f"Idle Image: {idle_image_path.split('/')[-1]}")

def select_talking_image():
    global talking_image_path
    file_path = filedialog.askopenfilename(defaultextension=".png", filetypes=[("PNG files", "*.png"), ("All files", "*.*")])
    if file_path:
        talking_image_path = file_path
        talking_image_label.config(text=f"Talking Image: {talking_image_path.split('/')[-1]}")

def select_blink_image():
    global blink_image_path
    file_path = filedialog.askopenfilename(defaultextension=".png", filetypes=[("PNG files", "*.png"), ("All files", "*.*")])
    if file_path:
        blink_image_path = file_path
        blink_image_label.config(text=f"Blink Image: {blink_image_path.split('/')[-1]}")

def update_multiplier(value):
    global talking_multiplier
    try:
        talking_multiplier = float(value)
        multiplier_label.config(text=f"Talking Multiplier: {talking_multiplier:.2f}")
    except ValueError:
        tk.messagebox.showerror("Invalid Input", "Please enter a valid number for the multiplier.")

def update_blink_duration(value):
    global blink_duration
    try:
        blink_duration = float(value)
        blink_duration_label.config(text=f"Blink Duration: {blink_duration:.2f} sec")
    except ValueError:
        tk.messagebox.showerror("Invalid Input", "Please enter a valid number for blink duration.")

def update_blink_interval_min(value):
    global blink_interval_min
    try:
        blink_interval_min = float(value)
        blink_interval_min_label.config(text=f"Min Interval: {blink_interval_min:.2f} sec")
        update_blink_interval()
    except ValueError:
        tk.messagebox.showerror("Invalid Input", "Please enter a valid number for min blink interval.")

def update_blink_interval_max(value):
    global blink_interval_max
    try:
        blink_interval_max = float(value)
        blink_interval_max_label.config(text=f"Max Interval: {blink_interval_max:.2f} sec")
        update_blink_interval()
    except ValueError:
        tk.messagebox.showerror("Invalid Input", "Please enter a valid number for max blink interval.")

def update_blink_interval():
    global blink_interval, blink_interval_min, blink_interval_max
    blink_interval = random.uniform(blink_interval_min, blink_interval_max)

def calculate_baseline_noise_internal():
    global baseline_noise_level
    samplerate = 44100
    duration = 0.5
    print("Calibrating noise level... Please be silent.")
    try:
        recording = sd.rec(int(samplerate * duration), samplerate=samplerate, channels=1, dtype='float32')
        print(f"Recording shape: {recording.shape}") # Debugging
        sd.wait()
        print("Calibration finished.") # Debugging
        baseline_noise_level = np.linalg.norm(recording) / len(recording) / duration if duration > 0 else 0.0
        baseline_label.config(text=f"Baseline Noise: {baseline_noise_level:.4f}")
    except sd.PortAudioError:
        tk.messagebox.showerror("Audio Error", "Could not access audio device.")

def run_pygame_blocking(audio_stream, samplerate):
    global running_pygame, current_image, screen, idle_pygame_image, talking_pygame_image, blink_pygame_image, baseline_noise_level, talking_multiplier, is_talking, silence_counter, is_blinking, blink_duration, blink_timer, blink_interval
    silence_threshold = 10
    last_time = time.time()

    while running_pygame:
        current_time = time.time()
        delta_time = current_time - last_time
        last_time = current_time

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running_pygame = False
                stop_pngtuber()
                root.destroy()
                return

        try:
            indata, overflowed = audio_stream.read(audio_stream.blocksize)
            if overflowed:
                print('Audio input overflowed')
            volume_norm = np.linalg.norm(indata) * 10
            talking_threshold = max(0.5, baseline_noise_level * talking_multiplier)

            if not is_blinking:
                if volume_norm > talking_threshold and not is_talking:
                    current_image = talking_pygame_image
                    is_talking = True
                    silence_counter = 0
                elif volume_norm <= talking_threshold and is_talking:
                    silence_counter += 1
                    if silence_counter >= silence_threshold:
                        current_image = idle_pygame_image
                        is_talking = False
                        silence_counter = 0
                elif not is_talking:
                    silence_counter = 0

                # Blink logic
                blink_timer += delta_time
                if blink_timer >= blink_interval and blink_pygame_image:
                    current_image = blink_pygame_image
                    is_blinking = True
                    blink_timer = 0.0
                    update_blink_interval() # Get a new random interval
                    blinking_start_time = current_time
            else:
                # Currently blinking
                if current_time - blinking_start_time >= blink_duration:
                    is_blinking = False
                    if is_talking:
                        current_image = talking_pygame_image
                    else:
                        current_image = idle_pygame_image

        except sd.PortAudioError as e:
            print(f"Audio input error: {e}")
            break

        if screen and current_image:
            screen.fill((0, 0, 0, 0))
            image_rect = current_image.get_rect(center=screen.get_rect().center)
            screen.blit(current_image, image_rect)
            pygame.display.flip()

        pygame.time.delay(16)
    if audio_stream.is_active():
        audio_stream.stop()
        audio_stream.close()

def start_pngtuber():
    global running_pygame, audio_stream, screen, current_image, idle_pygame_image, talking_pygame_image, blink_pygame_image, stop_button, is_blinking
    is_blinking = False

    if not running_pygame and idle_image_path and talking_image_path and blink_image_path:
        loading_window = tk.Toplevel(root)
        loading_window.title("Initializing...")
        loading_label = tk.Label(loading_window, text="Initializing Pygame...")
        loading_label.pack(padx=20, pady=10)
        progress_bar = ttk.Progressbar(loading_window, mode='indeterminate')
        progress_bar.pack(padx=20, pady=5)
        progress_bar.start(50)
        root.update()

        pygame.init()
        loading_label.config(text="Loading Images...")
        root.update()
        screen_width = 400
        screen_height = 300
        screen = pygame.display.set_mode((screen_width, screen_height), pygame.SRCALPHA)
        pygame.display.set_caption("Voice-Activated PNGTuber")
        load_images()

        if idle_pygame_image and talking_pygame_image and blink_pygame_image:
            current_image = idle_pygame_image
            is_talking = False
            running_pygame = True
            loading_label.config(text="Calibrating Microphone...")
            root.update()
            calculate_baseline_noise_internal()
            try:
                samplerate = 44100
                blocksize = 1024
                channels = 1
                dtype = 'float32'
                audio_stream = sd.InputStream(samplerate=samplerate, blocksize=blocksize, channels=channels, dtype=dtype)
                audio_stream.start()
                loading_window.destroy()
                root.update()
                stop_button.config(state=tk.NORMAL)
                run_pygame_blocking(audio_stream, samplerate)
            except sd.PortAudioError as e:
                loading_window.destroy()
                root.update()
                tk.messagebox.showerror("Audio Error", f"Could not access audio device: {e}")
        else:
            loading_window.destroy()
            root.update()
            tk.messagebox.showerror("Image Error", "Failed to load images. Please check the file paths.")
    elif not blink_pygame_image:
        tk.messagebox.showwarning("Warning", "Blink image not selected. Blinking will be disabled.")

def stop_pngtuber():
    global running_pygame, audio_stream, screen, stop_button
    if running_pygame:
        running_pygame = False
        if audio_stream and audio_stream.is_active():
            audio_stream.stop()
            audio_stream.close()
            audio_stream = None
        if screen:
            pygame.quit()
            screen = None
        stop_button.config(state=tk.DISABLED)

def on_closing():
    stop_pngtuber()
    root.destroy()

# Tkinter UI setup
root = tk.Tk()
root.title("PNGTuber Control")

welcome_label = tk.Label(root, text="Welcome to the OVS", font=("Arial", 16))
welcome_label.pack(pady=10)

idle_button = tk.Button(root, text="Select Idle Image", command=select_idle_image)
idle_button.pack(pady=5)
idle_image_label = tk.Label(root, text=f"Idle Image: {idle_image_path.split('/')[-1]}")
idle_image_label.pack()

talking_button = tk.Button(root, text="Select Talking Image", command=select_talking_image)
talking_button.pack(pady=5)
talking_image_label = tk.Label(root, text=f"Talking Image: {talking_image_path.split('/')[-1]}")
talking_image_label.pack()

blink_button = tk.Button(root, text="Select Blink Image", command=select_blink_image)
blink_button.pack(pady=5)
blink_image_label = tk.Label(root, text=f"Blink Image: {blink_image_path.split('/')[-1]}")
blink_image_label.pack()

# Blink Duration Slider
blink_duration_frame = tk.Frame(root)
blink_duration_frame.pack(pady=5)
blink_duration_label = tk.Label(blink_duration_frame, text=f"Blink Duration: {blink_duration:.2f} sec")
blink_duration_label.pack(side=tk.LEFT)
blink_duration_scale = Scale(blink_duration_frame, from_=0.05, to=1.0, resolution=0.05, orient=tk.HORIZONTAL, label="Blink Length", command=update_blink_duration)
blink_duration_scale.set(blink_duration)
blink_duration_scale.pack(side=tk.LEFT, fill=tk.X, expand=True)

# Blink Interval Sliders
blink_interval_frame = tk.Frame(root)
blink_interval_frame.pack(pady=5)

blink_interval_min_label = tk.Label(blink_interval_frame, text=f"Min Interval: {3.0:.2f} sec") # Default min
blink_interval_min_label.pack(side=tk.LEFT)
blink_interval_min_scale = Scale(blink_interval_frame, from_=1.0, to=10.0, resolution=0.5, orient=tk.HORIZONTAL, label="Blink Interval (Min)", command=update_blink_interval_min)
blink_interval_min_scale.set(3.0) # Default min
blink_interval_min_scale.pack(side=tk.LEFT, fill=tk.X, expand=True)

blink_interval_max_label = tk.Label(blink_interval_frame, text=f"Max Interval: {8.0:.2f} sec") # Default max
blink_interval_max_label.pack(side=tk.LEFT)
blink_interval_max_scale = Scale(blink_interval_frame, from_=blink_interval_min_scale.get(), to=15.0, resolution=0.5, orient=tk.HORIZONTAL, label="Blink Interval (Max)", command=update_blink_interval_max)
blink_interval_max_scale.set(8.0) # Default max
blink_interval_max_scale.pack(side=tk.LEFT, fill=tk.X, expand=True)

multiplier_frame = tk.Frame(root)
multiplier_frame.pack(pady=5)
multiplier_label = tk.Label(multiplier_frame, text=f"Talking Multiplier: {talking_multiplier:.2f}")
multiplier_label.pack(side=tk.LEFT)
multiplier_scale = Scale(multiplier_frame, from_=0.1, to=30.0, resolution=0.1, orient=tk.HORIZONTAL, label="Adjust Sensitivity", command=update_multiplier)
multiplier_scale.set(talking_multiplier)
multiplier_scale.pack(side=tk.LEFT, fill=tk.X, expand=True)

baseline_button = tk.Button(root, text="Calibrate Noise Level", command=lambda: calculate_baseline_noise_internal())
baseline_button.pack(pady=5)
baseline_label = tk.Label(root, text=f"Baseline Noise: {baseline_noise_level:.4f}")
baseline_label.pack()

start_button = tk.Button(root, text="Start PNGTuber", command=start_pngtuber)
start_button.pack(pady=10)

stop_button = tk.Button(root, text="Stop PNGTuber", command=stop_pngtuber, state=tk.DISABLED)
stop_button.pack(pady=5)

root.protocol("WM_DELETE_WINDOW", on_closing)

root.mainloop()

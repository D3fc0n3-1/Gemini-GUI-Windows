import os
import threading
import json
import customtkinter as ctk
from tkinterdnd2 import DND_FILES, TkinterDnD
from google import genai
import speech_recognition as sr
# For Local Voice (Optional but recommended for your J6 background)
# pip install vosk 

class GeminiApp(TkinterDnD.Tk):
    def __init__(self):
        super().__init__()

        # Window Config
        self.title("Gemini Command Center - 2026 Edition")
        self.geometry("1100x750")
        
        # Appearance
        ctk.set_appearance_mode("Dark")
        self.configure(bg="#212121") # Match CTK Dark Mode

        # Sidebar
        self.sidebar = ctk.CTkFrame(self, width=240, corner_radius=0)
        self.sidebar.pack(side="left", fill="y")
        
        self.logo = ctk.CTkLabel(self.sidebar, text="GEMINI v3.0", font=ctk.CTkFont(size=22, weight="bold"))
        self.logo.pack(pady=30)

        self.model_var = ctk.StringVar(value="Gemini 3 Flash")
        self.model_menu = ctk.CTkOptionMenu(self.sidebar, values=["Gemini 3 Flash", "Gemini 2.5 Pro"], variable=self.model_var)
        self.model_menu.pack(pady=10, padx=20)

        self.voice_btn = ctk.CTkButton(self.sidebar, text="🎤 Voice (Local)", fg_color="#A80000", hover_color="#7A0000", command=self.start_voice)
        self.voice_btn.pack(pady=20, padx=20)

        # Main Chat Area
        self.chat_display = ctk.CTkTextbox(self, state="disabled", wrap="word", font=("Consolas", 14))
        self.chat_display.pack(expand=True, fill="both", padx=20, pady=20)

        # Input Area
        self.input_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.input_frame.pack(fill="x", padx=20, pady=(0, 20))

        self.input_entry = ctk.CTkEntry(self.input_frame, placeholder_text="Type or drop files/logs here...", height=40)
        self.input_entry.pack(side="left", fill="x", expand=True)
        self.input_entry.bind("<Return>", lambda e: self.send_message())

        # Register Drag and Drop
        self.input_entry.drop_target_register(DND_FILES)
        self.input_entry.dnd_bind('<<Drop>>', self.handle_drop)

        self.send_btn = ctk.CTkButton(self.input_frame, text="Execute", width=120, height=40, command=self.send_message)
        self.send_btn.pack(side="right", padx=(10, 0))

    def handle_drop(self, event):
        path = event.data.strip('{}') # Handles Windows paths with spaces
        if os.path.isfile(path):
            self.log_to_chat(f"[*] SYSTEM: Analyzing local file: {os.path.basename(path)}")
            threading.Thread(target=self.process_file, args=(path,), daemon=True).start()

    def process_file(self, path):
        try:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            self.call_gemini(f"Analyze this file for security risks or errors:\n\n{content}")
        except Exception as e:
            self.log_to_chat(f"[!] Error reading file: {e}")

    def start_voice(self):
        self.voice_btn.configure(text="LISTENING...", fg_color="#FF0000")
        threading.Thread(target=self.listen_thread, daemon=True).start()

    def listen_thread(self):
        r = sr.Recognizer()
        with sr.Microphone() as source:
            try:
                r.adjust_for_ambient_noise(source)
                audio = r.listen(source, timeout=5)
                text = r.recognize_google(audio) # Swapping to Vosk is an easy switch later
                self.after(0, lambda: self.input_entry.insert(0, text))
                self.after(0, self.send_message)
            except Exception as e:
                self.log_to_chat(f"[!] Voice Error: {str(e)}")
            finally:
                self.after(0, lambda: self.voice_btn.configure(text="🎤 Voice (Local)", fg_color="#A80000"))

    def log_to_chat(self, msg):
        self.chat_display.configure(state="normal")
        self.chat_display.insert("end", f"{msg}\n\n")
        self.chat_display.configure(state="disabled")
        self.chat_display.see("end")

    def send_message(self):
        prompt = self.input_entry.get()
        if prompt:
            self.log_to_chat(f"User: {prompt}")
            self.input_entry.delete(0, "end")
            threading.Thread(target=self.call_gemini, args=(prompt,), daemon=True).start()

    def call_gemini(self, prompt):
        api_key = os.environ.get('GOOGLE_API_KEY')
        if not api_key:
            self.log_to_chat("[!] ERROR: GOOGLE_API_KEY not found in environment variables.")
            return

        model_id = "models/gemini-3-flash-preview" if "Flash" in self.model_var.get() else "models/gemini-2.5-pro"
        
        try:
            client = genai.Client(api_key=api_key, http_options={'api_version': 'v1beta'})
            response = client.models.generate_content(model=model_id, contents=prompt)
            self.log_to_chat(f"Gemini: {response.text}")
        except Exception as e:
            self.log_to_chat(f"[!] API Error: {str(e)}")

if __name__ == "__main__":
    app = GeminiApp()
    app.mainloop()
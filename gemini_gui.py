import os
import sys
import threading
import customtkinter as ctk
from tkinterdnd2 import DND_FILES, TkinterDnD
from google import genai
import speech_recognition as sr

# Integrating TkinterDnD with CustomTkinter
class Tk(ctk.CTk, TkinterDnD.DnDWrapper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.TkdndVersion = TkinterDnD._load_tkdnd(self)

class GeminiApp(Tk):
    def __init__(self):
        super().__init__()

        self.title("Gemini Pro Command Center")
        self.geometry("1000x700")
        
        # --- Drag and Drop Setup ---
        self.drop_target_register(DND_FILES)
        self.dnd_bind('<<Drop>>', self.handle_drop)

        # UI Layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Sidebar
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        self.logo = ctk.CTkLabel(self.sidebar, text="GEMINI v3.0", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo.pack(pady=20)

        self.model_var = ctk.StringVar(value="Gemini 3 Flash")
        self.model_menu = ctk.CTkOptionMenu(self.sidebar, values=["Gemini 3 Flash", "Gemini 2.5 Pro"], variable=self.model_var)
        self.model_menu.pack(pady=10)

        self.voice_btn = ctk.CTkButton(self.sidebar, text="🎤 Voice Command", fg_color="darkred", command=self.start_voice)
        self.voice_btn.pack(pady=20)

        # Main Area
        self.chat_display = ctk.CTkTextbox(self, state="disabled", wrap="word")
        self.chat_display.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")

        # Input Area
        self.input_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.input_frame.grid(row=1, column=1, padx=20, pady=(0, 20), sticky="ew")
        self.input_frame.grid_columnconfigure(0, weight=1)

        self.input_entry = ctk.CTkEntry(self.input_frame, placeholder_text="Type or drop files here...")
        self.input_entry.grid(row=0, column=0, sticky="ew")
        self.input_entry.bind("<Return>", lambda e: self.send_message())

        self.send_btn = ctk.CTkButton(self.input_frame, text="Send", command=self.send_message)
        self.send_btn.grid(row=0, column=1, padx=(10, 0))

    def handle_drop(self, event):
        file_path = event.data.strip('{}') # Remove brackets Windows adds for paths with spaces
        if os.path.isfile(file_path):
            self.log_to_chat(f"📁 File attached: {os.path.basename(file_path)}")
            threading.Thread(target=self.process_file, args=(file_path,), daemon=True).start()

    def process_file(self, path):
        try:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            self.call_gemini(f"Analyze this file content:\n\n{content}")
        except Exception as e:
            self.log_to_chat(f"Error reading file: {e}")

    def start_voice(self):
        self.voice_btn.configure(text="Listening...", fg_color="red")
        threading.Thread(target=self.listen_thread, daemon=True).start()

    def listen_thread(self):
        r = sr.Recognizer()
        with sr.Microphone() as source:
            try:
                audio = r.listen(source, timeout=5)
                text = r.recognize_google(audio)
                self.input_entry.delete(0, "end")
                self.input_entry.insert(0, text)
                self.send_message()
            except Exception as e:
                self.log_to_chat(f"Voice Error: {str(e)}")
            finally:
                self.after(0, lambda: self.voice_btn.configure(text="🎤 Voice Command", fg_color="darkred"))

    def log_to_chat(self, msg):
        self.chat_display.configure(state="normal")
        self.chat_display.insert("end", f"{msg}\n\n")
        self.chat_display.configure(state="disabled")
        self.chat_display.see("end")

    def send_message(self):
        prompt = self.input_entry.get()
        if prompt:
            self.log_to_chat(f"You: {prompt}")
            self.input_entry.delete(0, "end")
            threading.Thread(target=self.call_gemini, args=(prompt,), daemon=True).start()

    def call_gemini(self, prompt):
        # API Logic using genai Client...
        api_key = os.environ.get('GOOGLE_API_KEY')
        client = genai.Client(api_key=api_key, http_options={'api_version': 'v1beta'})
        model_id = "models/gemini-3-flash-preview" if "Flash" in self.model_var.get() else "models/gemini-2.5-pro"
        try:
            response = client.models.generate_content(model=model_id, contents=prompt)
            self.log_to_chat(f"Gemini: {response.text}")
        except Exception as e:
            self.log_to_chat(f"API Error: {str(e)}")

if __name__ == "__main__":
    app = GeminiApp()
    app.mainloop()
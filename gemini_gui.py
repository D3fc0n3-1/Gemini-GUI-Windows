import customtkinter as ctk
import os
import threading
from google import genai

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class GeminiApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Gemini Desktop - Windows 11 Edition")
        self.geometry("900x600")

        # Layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- Sidebar ---
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        self.logo_label = ctk.CTkLabel(self.sidebar, text="GEMINI AI", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.pack(padx=20, pady=(20, 10))

        self.model_label = ctk.CTkLabel(self.sidebar, text="Select Model:")
        self.model_label.pack(pady=(20, 0))
        
        self.model_var = ctk.StringVar(value="Gemini 3 Flash")
        self.model_menu = ctk.CTkOptionMenu(self.sidebar, values=["Gemini 3 Flash", "Gemini 2.5 Pro"], variable=self.model_var)
        self.model_menu.pack(pady=10)

        self.key_btn = ctk.CTkButton(self.sidebar, text="Update API Key", command=self.update_key)
        self.key_btn.pack(pady=20)

        # --- Main Chat Area ---
        self.chat_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.chat_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        self.chat_frame.grid_columnconfigure(0, weight=1)
        self.chat_frame.grid_rowconfigure(0, weight=1)

        self.chat_display = ctk.CTkTextbox(self.chat_frame, state="disabled", wrap="word")
        self.chat_display.grid(row=0, column=0, sticky="nsew")

        self.input_entry = ctk.CTkEntry(self.chat_frame, placeholder_text="Type your prompt here...")
        self.input_entry.grid(row=1, column=0, pady=(20, 0), sticky="ew")
        self.input_entry.bind("<Return>", lambda e: self.send_message())

        self.send_btn = ctk.CTkButton(self.chat_frame, text="Send", command=self.send_message)
        self.send_btn.grid(row=1, column=1, padx=(10, 0), pady=(20, 0))

    def update_key(self):
        dialog = ctk.CTkInputDialog(text="Paste your Google API Key:", title="API Configuration")
        key = dialog.get_input()
        if key:
            os.system(f'setx GOOGLE_API_KEY "{key}"')
            self.log_to_chat("System: API Key updated. Restart app to apply.")

    def log_to_chat(self, message):
        self.chat_display.configure(state="normal")
        self.chat_display.insert("end", f"{message}\n\n")
        self.chat_display.configure(state="disabled")
        self.chat_display.see("end")

    def send_message(self):
        prompt = self.input_entry.get()
        if not prompt: return
        
        self.log_to_chat(f"You: {prompt}")
        self.input_entry.delete(0, "end")
        
        # Run API call in a separate thread so GUI doesn't freeze
        threading.Thread(target=self.call_gemini, args=(prompt,), daemon=True).start()

    def call_gemini(self, prompt):
        api_key = os.environ.get('GOOGLE_API_KEY')
        if not api_key:
            self.log_to_chat("Error: GOOGLE_API_KEY not found in environment variables.")
            return

        model_id = "models/gemini-3-flash-preview" if "Flash" in self.model_var.get() else "models/gemini-2.5-pro"
        
        try:
            client = genai.Client(api_key=api_key, http_options={'api_version': 'v1beta'})
            response = client.models.generate_content(model=model_id, contents=prompt)
            self.log_to_chat(f"Gemini: {response.text}")
        except Exception as e:
            self.log_to_chat(f"API Error: {str(e)}")

if __name__ == "__main__":
    app = GeminiApp()
    app.mainloop()
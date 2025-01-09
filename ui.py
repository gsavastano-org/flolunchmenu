import tkinter as tk
from tkinter import scrolledtext, filedialog, ttk
from threading import Thread
import asyncio
from app.core.config import Config
from script_runner import ScriptRunner  # Import the logic class

class ApplicationUI(tk.Frame):
    def __init__(self, master=None, script_runner=None):
        super().__init__(master)
        self.master = master
        self.master.title("Weekly Meal Order Form Generator")
        self.pack(padx=20, pady=20)
        self.script_runner = script_runner
        self.selected_image_paths = {
            'Monday': {'path': None, 'label': None},
            'Tuesday': {'path': None, 'label': None},
            'Wednesday': {'path': None, 'label': None},
            'Thursday': {'path': None, 'label': None},
            'Friday': {'path': None, 'label': None}
        }
        self.progress_var = tk.IntVar(value=0)
        self.create_widgets()

    def create_widgets(self):
        # --- Style ---
        style = ttk.Style()
        style.configure('TButton', padding=5, font=('Arial', 12))
        style.configure('TLabel', font=('Arial', 12))
        style.configure('TLabelframe.Label', font=('Arial', 14, 'bold'))

        # --- Upload Frame ---
        upload_frame = ttk.LabelFrame(self, text="Select Menu Images", padding=10)
        upload_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
        for i, day in enumerate(days):
            ttk.Label(upload_frame, text=f"{day}:").grid(row=i, column=0, sticky="w", pady=5)
            button = ttk.Button(upload_frame, text="Browse", command=lambda d=day: self.upload_file(d))
            button.grid(row=i, column=1, sticky="ew", padx=5, pady=5)
            label_var = tk.StringVar(value="No file selected")
            label = ttk.Label(upload_frame, textvariable=label_var)
            label.grid(row=i, column=2, sticky="ew", padx=5, pady=5)
            self.selected_image_paths[day]['label_var'] = label_var

        # --- Controls Frame ---
        controls_frame = ttk.Frame(self)
        controls_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=10)
        controls_frame.columnconfigure(0, weight=1)
        controls_frame.columnconfigure(1, weight=1)

        self.start_button = ttk.Button(controls_frame, text="Generate Form", command=self.run_script_in_thread)
        self.start_button.grid(row=0, column=0, sticky="ew", padx=5)

        self.clear_button = ttk.Button(controls_frame, text="Clear", command=self.clear_form)
        self.clear_button.grid(row=0, column=1, sticky="ew", padx=5)

        # --- Progress Bar ---
        self.progress_bar = ttk.Progressbar(self, variable=self.progress_var, orient="horizontal", length=300, mode="determinate")
        self.progress_bar.grid(row=2, column=0, sticky="ew", padx=10, pady=10)

        # --- Output Frame ---
        output_frame = ttk.LabelFrame(self, text="Process Log", padding=10)
        output_frame.grid(row=3, column=0, sticky="nsew", padx=10, pady=10)
        self.output_text = scrolledtext.ScrolledText(output_frame, wrap=tk.WORD, font=("Courier New", 10), height=10)
        self.output_text.pack(expand=True, fill='both')

        # --- Exit Button ---
        self.exit_button = ttk.Button(self, text="Exit", command=self.master.destroy)
        self.exit_button.grid(row=4, column=0, sticky="ew", padx=10, pady=10)
        self.exit_button.config(state=tk.NORMAL) # Always enabled

    def upload_file(self, day):
        filepath = filedialog.askopenfilename(
            filetypes=[("JPEG files", "*.jpeg"), ("All files", "*.*")]
        )
        if filepath:
            self.selected_image_paths[day]['path'] = filepath
            self.selected_image_paths[day]['label_var'].set(filepath.split("/")[-1])

    def run_script_in_thread(self):
        if not all(data['path'] for data in self.selected_image_paths.values()):
            self.log_message("Error: Please select an image for each day.", error=True)
            return

        # Disable buttons during script execution
        self.start_button.config(state=tk.DISABLED)
        self.clear_button.config(state=tk.DISABLED)

        self.output_text.delete('1.0', tk.END)  # Clear output
        self.progress_var.set(0)

        # Prepare data for the script runner
        image_paths = {day: data['path'] for day, data in self.selected_image_paths.items()}

        # Run the script in a separate thread
        thread = Thread(target=self._run_async_script, args=(image_paths,))
        thread.start()

    def _run_async_script(self, image_paths):
        asyncio.run(self.script_runner.run_script(image_paths, self))

    def log_message(self, message, error=False):
        """Logs a message to the output widget and console."""
        print(message)  # Keep console logging for debugging
        self.output_text.insert(tk.END, message + "\n")
        if error:
            self.output_text.tag_add("error", "end -2 lines", "end -1 lines")
            self.output_text.tag_config("error", foreground="red")
        self.output_text.see(tk.END)  # Scroll to the end

    def update_progress(self, value):
        self.progress_var.set(value)

    def enable_buttons(self):
        self.start_button.config(state=tk.NORMAL)
        self.clear_button.config(state=tk.NORMAL)

    def clear_form(self):
        """Resets the form to its initial state."""
        for day_data in self.selected_image_paths.values():
            day_data['path'] = None
            day_data['label_var'].set("No file selected")
        self.output_text.delete('1.0', tk.END)
        self.progress_var.set(0)

def main():
    root = tk.Tk()
    config = Config()
    script_runner = ScriptRunner(config)
    app_ui = ApplicationUI(master=root, script_runner=script_runner)
    root.mainloop()

if __name__ == "__main__":
    main()
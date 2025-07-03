# 💨 hydraHog.exe  
### _Cut one core, two shall rise._  

![hydraHog banner](image.png)  

> ⚠️ **This script is a digital gremlin. It consumes CPU & RAM like your ex eats through your Netflix account. Use it for laughs, memes, or to teach someone humility.**

---

## 🤖 What It Does
- Can auto-start on boot (like a clingy ex).
- Slowly maxes out **RAM** and **CPU** to 99%+ (adjustable).
- Triggers **fake warning popups** urging for a hardware upgrade.
- After 5 minutes (or whatever you set it to) of hogging, it attempts a **BSOD** (Windows crash).
- If you kill it via Task Manager? It **respawns**. Yeah. _Hydra-style._

---

## 🔥 Features
| Feature         | Description                                                  |
|----------------|--------------------------------------------------------------|
| 📯 RAM Gobbling | Eats memory in chunks and touches it frequently to stay hot |
| 🔥 CPU Frenzy   | Uses all cores to compute... absolutely nothing              |
| 🔂 Resurrection | If a process is killed, it comes back. **Always.**           |
| ⌨️ Hotkey CTRL+ALT+P | Pauses the chaos if you dare                             |
| 💣 BSOD Timer   | Optional “nuke” timer for full system crash                  |

---

## ⚙️ Installation
```bash
git clone https://github.com/hyprZona/hydraHog.exe.git
cd hydraHog.exe
python hydraHog.py
```

---

### 🧪 How To Add It to Auto-Start (a.k.a. “How to Haunt Their Reboot”)
> 💀 _Yes, we’re going full gremlin. No shame._

**Step 1:** Make a shortcut  
- Right-click `hydraHog.exe` (or `.py` if uncompiled) > **Create Shortcut**

**Step 2:** Toss it into Startup like it owes you RAM  
- Hit `Win + R` → type `shell:startup` → Enter  
- Drop that shortcut in the folder that opens.  
- Done. Welcome to Eternal Boot Lag™.

---

### 🛠️ How to Compile It Into a `.exe` with Icon
> ⚠️ _This is for those who want the full disguise — system process cosplay level._

**Step 1:** Install `pyinstaller`
```bash
pip install pyinstaller
```

**Step 2:** Build your imposter `.exe`
```bash
pyinstaller --noconfirm --onefile --windowed --icon=youricon.ico hydraHog.py
```

- `--windowed` = No ugly terminal popping up.
- `--icon` = Use your custom `.ico` (like our HydraHog parody logo).
- `--onefile` = Single `.exe` output. Clean and deployable.

**Step 3:** Find your `.exe` in the `dist/` folder. Toss it into Startup as explained earlier. Set. Trap. Laugh.

---

### 📆 Recommended Icon (Optional but hilarious)
![hydraHog Icon](hydraHog.png)  
> Or use anything dumb. Like a Notepad icon. Or Shrek. Confuse. Always confuse.

---

### 💨 Example Use Cases
- 🤪 _Stress test_ a laptop from 2009 (it will scream).
- 🧠 _Psychological warfare_ against a coworker.
- 🎉 _April Fools_, any day of the year.
- 💻 _Teach_ your little sibling humility for installing Chrome extensions like it's candy.

---

### 🙈 Warning
This is not malware. But it sure as hell behaves like one.

- 🔐 **Use responsibly.**
- ⚰️ Don’t try this on production machines unless you have a death wish.
- 👀 It _will_ lag, crash, or force a reboot if left unchecked.  
- 💡 You **must** run on an admin profile for the BSOD trick to work.

---

### 🤝 Credits
- Built by [hyprZona](https://github.com/hyprZona) aka dVlpr — bringing digital chaos one fork at a time.
- Inspired by the sheer audacity of old RAM-hogging Flash games and your grandma’s Vista.

---

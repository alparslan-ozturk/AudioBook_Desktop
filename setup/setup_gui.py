import os
import sys
import subprocess
import threading
import shutil
import tkinter as tk
from tkinter import ttk, scrolledtext
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).parent.resolve()
VENV = BASE / "xtts-env"
VENV_PY = VENV / "Scripts" / "python.exe"
REQ = BASE / "requirements.txt"

STEPS = [
    "Python 3.11 kontrol / kurulum",
    "ffmpeg kontrol / kurulum",
    "Visual C++ Build Tools kontrol",
    "Sanal ortam (venv) kurulum",
    "PyTorch CUDA kurulum",
    "requirements kurulum (TTS+XTTS)",
    "XTTS model on-indirme",
    "Masaustu kisayolu",
]

def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    term.configure(state="normal")
    term.insert(tk.END, f"[{ts}] {msg}\n")
    term.see(tk.END)
    term.configure(state="disabled")

def ilerleme(pct, txt=None):
    bar["value"] = pct
    if txt:
        durum_var.set(txt)
    root.update_idletasks()

def calistir(cmd, timeout=600):
    log(f"$ {' '.join(cmd[:6])}{' ...' if len(cmd) > 6 else ''}")
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, cwd=str(BASE))
        if r.returncode != 0:
            err = (r.stderr or r.stdout or "")[-1500:]
            log(f"HATA ({r.returncode}): {err}")
            return False
        log("OK")
        return True
    except Exception as e:
        log(f"HATA: {e}")
        return False

def adim_isaret(i, ok=True):
    lbls[i].config(text=("✔ " if ok else "✘ ") + STEPS[i], foreground="green" if ok else "red")

def kurulum():
    btn.config(state="disabled")
    threading.Thread(target=is_parcacigi, daemon=True).start()

def is_parcacigi():
    try:
        # 1 - Python 3.11
        ilerleme(5, STEPS[0])
        log("Python 3.11 araniyor...")
        py311 = shutil.which("py") is not None
        ok311 = False
        if py311:
            r = subprocess.run(["py", "-3.11", "--version"], capture_output=True, text=True)
            ok311 = r.returncode == 0
        if not ok311:
            log("Python 3.11 kuruluyor (winget, ~1-2 dk)...")
            if not calistir(["winget", "install", "-e", "--id", "Python.Python.3.11",
                             "--accept-source-agreements", "--accept-package-agreements"], timeout=600):
                raise RuntimeError("Python 3.11 kurulamadi")
        adim_isaret(0)

        # 2 - ffmpeg
        ilerleme(15, STEPS[1])
        if shutil.which("ffmpeg") is None:
            log("ffmpeg kuruluyor (winget)...")
            if not calistir(["winget", "install", "-e", "--id", "Gyan.FFmpeg",
                             "--accept-source-agreements", "--accept-package-agreements"], timeout=600):
                raise RuntimeError("ffmpeg kurulamadi")
            # PATH yenile
            import winreg
            log("PATH yenilendi, devam ediliyor.")
        else:
            log("ffmpeg zaten kurulu.")
        adim_isaret(1)

        # 3 - Build Tools (kontrol, yoksa kur)
        ilerleme(25, STEPS[2])
        vswhere = Path(os.environ.get("ProgramFiles(x86)", "")) / "Microsoft Visual Studio" / "Installer" / "vswhere.exe"
        if not vswhere.exists():
            log("Build Tools kuruluyor (biraz surer, ~5-10 dk)...")
            calistir(["winget", "install", "-e", "--id", "Microsoft.VisualStudio.2022.BuildTools",
                      "--override", "--wait --quiet --add Microsoft.VisualStudio.Workload.VCTools --includeRecommended",
                      "--accept-source-agreements", "--accept-package-agreements"], timeout=1800)
        else:
            log("Build Tools mevcut gorunuyor.")
        adim_isaret(2)

        # 4 - venv
        ilerleme(35, STEPS[3])
        if not VENV_PY.exists():
            log("venv olusturuluyor...")
            if not calistir(["py", "-3.11", "-m", "venv", str(VENV)], timeout=300):
                raise RuntimeError("venv olusturulamadi")
        else:
            log("venv zaten var.")
        adim_isaret(3)

        # 5 - torch CUDA
        ilerleme(50, STEPS[4])
        log("PyTorch CUDA kuruluyor (~2-3 GB, 3-5 dk)...")
        if not calistir([str(VENV_PY), "-m", "pip", "install", "--upgrade", "pip"], timeout=300):
            raise RuntimeError("pip guncellenemedi")
        if not calistir([str(VENV / "Scripts" / "pip.exe"), "install", "torch", "torchvision", "torchaudio",
                         "--index-url", "https://download.pytorch.org/whl/cu121"], timeout=1800):
            raise RuntimeError("torch kurulamadi")
        adim_isaret(4)

        # 6 - requirements
        ilerleme(70, STEPS[5])
        log("TTS + bagimliliklar kuruluyor (~4-5 dk)...")
        if not calistir([str(VENV / "Scripts" / "pip.exe"), "install", "-r", str(REQ)], timeout=1800):
            raise RuntimeError("requirements kurulamadi")
        adim_isaret(5)

        # 7 - model on-indirme
        ilerleme(85, STEPS[6])
        log("XTTS modeli indiriliyor (~2 GB, ilk sefer)...")
        code = "from TTS.api import TTS; TTS('tts_models/multilingual/multi-dataset/xtts_v2')"
        r = subprocess.run([str(VENV_PY), "-c", code], input="y\n", capture_output=True, text=True, timeout=1800, cwd=str(BASE))
        if r.returncode != 0:
            log(f"Model indirme uyarisi: {(r.stderr or '')[-800:]}")
        else:
            log("Model hazir.")
        adim_isaret(6)

        # 8 - kisayol
        ilerleme(95, STEPS[7])
        bat = BASE / "app-calistir.bat"
        bat.write_text(f'@echo off\nchcp 65001 >nul\ncd /d "{BASE}"\n"{VENV_PY}" "{BASE / "app.py"}"\npause\n', encoding="utf-8")
        desk = Path(os.path.join(os.path.expanduser("~"), "Desktop"))
        lnk = desk / "Sesli Kitap.lnk"
        ps = f'$s=(New-Object -ComObject WScript.Shell).CreateShortcut("{lnk}");$s.TargetPath="{bat}";$s.WorkingDirectory="{BASE}";$s.Save()'
        subprocess.run(["powershell", "-Command", ps], capture_output=True)
        log(f"Kisayol: {lnk}")
        adim_isaret(7)

        ilerleme(100, "Tamamlandi - Masaustunden cift tikla!")
        log("BITTI. Artik son kullanici sadece Masaustu > Sesli Kitap'a cift tiklar.")
    except Exception as e:
        log(f"KURULUM DURDU: {e}")
        durum_var.set("Hata - loga bak")
    finally:
        root.after(0, lambda: btn.config(state="normal"))

root = tk.Tk()
root.title("Sesli Kitap - Kurulum")
root.geometry("700x620")
root.minsize(620, 540)

durum_var = tk.StringVar(value="Hazir")
frm = ttk.Frame(root, padding=12)
frm.pack(fill="both", expand=True)

ttk.Label(frm, text="Kurulum Adimlari (otomatik):", font=("Segoe UI", 10, "bold")).pack(anchor="w")
lbls = []
for s in STEPS:
    l = ttk.Label(frm, text="○ " + s)
    l.pack(anchor="w", padx=10)
    lbls.append(l)

btn = ttk.Button(frm, text="KURULUMU BASLAT", command=kurulum)
btn.pack(pady=10)
ttk.Label(frm, textvariable=durum_var).pack()

term = scrolledtext.ScrolledText(frm, height=14, state="disabled", bg="#111", fg="#0f0", font=("Consolas", 9))
term.pack(fill="both", expand=True, pady=(6,0))

bar = ttk.Progressbar(root, mode="determinate", maximum=100, value=0)
bar.pack(fill="x", side="bottom")

log(f"Klasor: {BASE}")
log("Baslamak icin KURULUMU BASLAT'a bas. Hicbir seyi elle yapmana gerek yok.")
root.mainloop()

"""
Actividad formativa 3 - Implementación y evaluación de filtros digitales
Materia: Señales y Sistemas
Alumno: Mario Alberto Zavala González

Este script:
  1. Crea una señal de prueba compuesta (5 Hz + 50 Hz + 120 Hz) con ruido blanco.
  2. Diseña tres filtros:
       - Pasa bajos  IIR Butterworth   (deja pasar 5 Hz)
       - Pasa altos  IIR Chebyshev I   (deja pasar 120 Hz)
       - Pasa bandas FIR con ventana Hamming (deja pasar 50 Hz)
  3. Aplica los filtros a la señal.
  4. Grafica la señal antes y después, los espectros y la respuesta en frecuencia.
  5. Calcula métricas (SNR y atenuación) para evaluar la efectividad.
  6. Compara diferentes órdenes del filtro Butterworth.

Uso:
    pip install -r requirements.txt
    python filtros_digitales.py
Las gráficas se guardan en la carpeta "figuras/".
"""

import os
import numpy as np
import matplotlib
matplotlib.use("Agg")          # permite guardar imágenes sin abrir ventanas
import matplotlib.pyplot as plt
from scipy import signal

os.makedirs("figuras", exist_ok=True)
np.random.seed(42)             # semilla para que el ruido sea siempre el mismo

# ============================================================
# 1. DEFINICIÓN DE LA SEÑAL DE ENTRADA
# ============================================================
fs = 1000                      # frecuencia de muestreo [Hz]
T = 2.0                        # duración de la señal [s]
t = np.arange(0, T, 1 / fs)    # vector de tiempo

# Componentes de la señal (cada una será el objetivo de un filtro)
s_5 = 1.0 * np.sin(2 * np.pi * 5 * t)      # baja frecuencia
s_50 = 0.7 * np.sin(2 * np.pi * 50 * t)    # frecuencia media
s_120 = 0.5 * np.sin(2 * np.pi * 120 * t)  # alta frecuencia
ruido = 0.6 * np.random.randn(len(t))      # ruido blanco gaussiano

x = s_5 + s_50 + s_120 + ruido             # señal compuesta con ruido


def espectro(senal):
    """Devuelve frecuencias y magnitud de la FFT (solo lado positivo)."""
    N = len(senal)
    X = np.fft.rfft(senal * np.hanning(N))
    f = np.fft.rfftfreq(N, 1 / fs)
    mag = 2 * np.abs(X) / np.sum(np.hanning(N))
    return f, mag


def snr_db(referencia, senal):
    """SNR en dB: potencia de la referencia entre la potencia del error."""
    error = senal - referencia
    return 10 * np.log10(np.sum(referencia ** 2) / np.sum(error ** 2))


# --- Gráfica de la señal original (tiempo y frecuencia) ---
fig, ax = plt.subplots(2, 1, figsize=(10, 6))
ax[0].plot(t[:500], x[:500], color="gray", lw=0.8)
ax[0].set_title("Señal de entrada: 5 Hz + 50 Hz + 120 Hz + ruido blanco")
ax[0].set_xlabel("Tiempo [s]"); ax[0].set_ylabel("Amplitud"); ax[0].grid(alpha=.3)
f, X = espectro(x)
ax[1].plot(f, X, color="black", lw=0.8)
ax[1].set_xlim(0, 250)
ax[1].set_title("Espectro de la señal de entrada")
ax[1].set_xlabel("Frecuencia [Hz]"); ax[1].set_ylabel("Magnitud"); ax[1].grid(alpha=.3)
plt.tight_layout(); plt.savefig("figuras/01_senal_entrada.png", dpi=150); plt.close()

# ============================================================
# 2. DISEÑO DE LOS FILTROS
# ============================================================
nyq = fs / 2                   # frecuencia de Nyquist

# a) Pasa bajos IIR Butterworth, orden 4, corte en 20 Hz
b_lp, a_lp = signal.butter(N=4, Wn=20 / nyq, btype="low")

# b) Pasa altos IIR Chebyshev tipo I, orden 4, rizo 1 dB, corte en 100 Hz
b_hp, a_hp = signal.cheby1(N=4, rp=1, Wn=100 / nyq, btype="high")

# c) Pasa bandas FIR con ventana Hamming, 201 coeficientes, banda 40-60 Hz
numtaps = 201
b_bp = signal.firwin(numtaps, [40, 60], window="hamming", pass_zero=False, fs=fs)
a_bp = 1.0                     # un FIR no tiene denominador

filtros = {
    "Pasa bajos (Butterworth IIR, fc=20 Hz)": (b_lp, a_lp, s_5, "tab:blue"),
    "Pasa altos (Chebyshev I IIR, fc=100 Hz)": (b_hp, a_hp, s_120, "tab:red"),
    "Pasa bandas (FIR Hamming, 40-60 Hz)": (b_bp, a_bp, s_50, "tab:green"),
}

# --- Respuesta en frecuencia de los tres filtros ---
fig, ax = plt.subplots(figsize=(10, 4.5))
for nombre, (b, a, _, color) in filtros.items():
    w, h = signal.freqz(b, a, worN=4096, fs=fs)
    ax.plot(w, 20 * np.log10(np.maximum(np.abs(h), 1e-8)), label=nombre, color=color)
for fr in (5, 50, 120):
    ax.axvline(fr, color="gray", ls=":", lw=1)
ax.set_xlim(0, 250); ax.set_ylim(-100, 5)
ax.set_title("Respuesta en frecuencia (magnitud) de los filtros diseñados")
ax.set_xlabel("Frecuencia [Hz]"); ax.set_ylabel("Magnitud [dB]")
ax.grid(alpha=.3); ax.legend(loc="lower right", fontsize=9)
plt.tight_layout(); plt.savefig("figuras/02_respuesta_frecuencia.png", dpi=150); plt.close()

# ============================================================
# 3. APLICACIÓN DE LOS FILTROS A LA SEÑAL
# ============================================================
# filtfilt filtra hacia adelante y hacia atrás: no hay desfase en la salida
salidas = {}
for nombre, (b, a, _, _) in filtros.items():
    salidas[nombre] = signal.filtfilt(b, a, x)

# ============================================================
# 4. VISUALIZACIÓN DE RESULTADOS
# ============================================================
# --- Señal filtrada vs. componente ideal (dominio del tiempo) ---
fig, axs = plt.subplots(3, 1, figsize=(10, 8))
idx = (t >= 0.5) & (t < 0.9)   # ventana central (evita efectos de borde)
for ax, (nombre, (b, a, ideal, color)) in zip(axs, filtros.items()):
    ax.plot(t[idx], x[idx], color="lightgray", lw=0.8, label="Entrada con ruido")
    ax.plot(t[idx], ideal[idx], "k--", lw=1, label="Componente ideal")
    ax.plot(t[idx], salidas[nombre][idx], color=color, lw=1.3, label="Salida filtrada")
    ax.set_title(nombre); ax.set_ylabel("Amplitud"); ax.grid(alpha=.3)
    ax.legend(loc="upper right", fontsize=8)
axs[-1].set_xlabel("Tiempo [s]")
plt.tight_layout(); plt.savefig("figuras/03_tiempo_antes_despues.png", dpi=150); plt.close()

# --- Espectros antes y después ---
fig, axs = plt.subplots(3, 1, figsize=(10, 8))
f, X = espectro(x)
for ax, (nombre, (_, _, _, color)) in zip(axs, filtros.items()):
    fy, Y = espectro(salidas[nombre])
    ax.plot(f, X, color="lightgray", lw=0.8, label="Antes")
    ax.plot(fy, Y, color=color, lw=1.2, label="Después")
    ax.set_xlim(0, 250); ax.set_title(nombre); ax.set_ylabel("Magnitud")
    ax.grid(alpha=.3); ax.legend(loc="upper right", fontsize=8)
axs[-1].set_xlabel("Frecuencia [Hz]")
plt.tight_layout(); plt.savefig("figuras/04_espectro_antes_despues.png", dpi=150); plt.close()

# ============================================================
# 5. MÉTRICAS DE EFECTIVIDAD
# ============================================================
print("\n=== Métricas de efectividad ===")
filas = []
for nombre, (b, a, ideal, _) in filtros.items():
    _, h = signal.freqz(b, a, worN=[5, 50, 120], fs=fs)
    gan = 20 * np.log10(np.maximum(np.abs(h), 1e-12))
    zona = (t >= 0.2) & (t <= T - 0.2)          # se ignoran los bordes
    snr_antes = snr_db(ideal[zona], x[zona])
    snr_desp = snr_db(ideal[zona], salidas[nombre][zona])
    filas.append((nombre, gan[0], gan[1], gan[2], snr_antes, snr_desp))
    print(f"{nombre}")
    print(f"   Ganancia en 5/50/120 Hz: {gan[0]:7.1f} / {gan[1]:7.1f} / {gan[2]:7.1f} dB")
    print(f"   SNR antes: {snr_antes:6.1f} dB   SNR después: {snr_desp:6.1f} dB"
          f"   Mejora: {snr_desp - snr_antes:+.1f} dB")

with open("resultados.csv", "w", encoding="utf-8") as fcsv:
    fcsv.write("filtro,ganancia_5Hz_dB,ganancia_50Hz_dB,ganancia_120Hz_dB,snr_antes_dB,snr_despues_dB\n")
    for fila in filas:
        fcsv.write(f"\"{fila[0]}\"," + ",".join(f"{v:.2f}" for v in fila[1:]) + "\n")

# ============================================================
# 6. COMPARACIÓN DE CONFIGURACIONES (orden del Butterworth)
# ============================================================
fig, axs = plt.subplots(1, 2, figsize=(11, 4))
print("\n=== Pasa bajos Butterworth con distinto orden ===")
for orden, color in zip((2, 4, 8), ("tab:orange", "tab:blue", "tab:purple")):
    b, a = signal.butter(orden, 20 / nyq, btype="low")
    w, h = signal.freqz(b, a, worN=4096, fs=fs)
    axs[0].plot(w, 20 * np.log10(np.maximum(np.abs(h), 1e-8)), color=color, label=f"Orden {orden}")
    y = signal.filtfilt(b, a, x)
    zona = (t >= 0.2) & (t <= T - 0.2)
    snr = snr_db(s_5[zona], y[zona])
    g50 = 20 * np.log10(abs(signal.freqz(b, a, worN=[50], fs=fs)[1][0]))
    print(f"   Orden {orden}: ganancia en 50 Hz = {g50:6.1f} dB, SNR = {snr:5.1f} dB")
    axs[1].plot(t[idx], y[idx], color=color, lw=1.1, label=f"Orden {orden}")
axs[0].set_xlim(0, 150); axs[0].set_ylim(-100, 5); axs[0].axvline(20, color="gray", ls=":")
axs[0].set_title("Respuesta en frecuencia según el orden")
axs[0].set_xlabel("Frecuencia [Hz]"); axs[0].set_ylabel("Magnitud [dB]")
axs[0].grid(alpha=.3); axs[0].legend()
axs[1].plot(t[idx], s_5[idx], "k--", lw=1, label="Ideal 5 Hz")
axs[1].set_title("Salida en el tiempo según el orden")
axs[1].set_xlabel("Tiempo [s]"); axs[1].grid(alpha=.3); axs[1].legend(fontsize=8)
plt.tight_layout(); plt.savefig("figuras/05_comparacion_orden.png", dpi=150); plt.close()

print("\nListo. Gráficas guardadas en la carpeta 'figuras/' y métricas en 'resultados.csv'.")

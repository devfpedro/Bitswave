import os
import sys

# Permite rodar o mixer sem dispositivo de áudio real (CI / headless).
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

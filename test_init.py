import os
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
import pygame
pygame.init()
from main import GameCoordinator
print("Initializing GameCoordinator in headless mode...")
coord = GameCoordinator()
print("GameCoordinator initialized successfully!")

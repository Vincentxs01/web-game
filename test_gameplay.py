import os
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
import pygame
pygame.init()

from main import GameCoordinator

def test_gameplay():
    print("Initializing GameCoordinator...")
    coord = GameCoordinator()
    
    # Set up screen for drawing tests (even in dummy mode, a surface is needed)
    coord.screen = pygame.Surface((1000, 600))
    
    dt = 1.0 / 60.0
    
    # 1. 測試 MENU 狀態 (主選單)
    print("Testing MENU state...")
    coord.state = "MENU"
    for _ in range(15):
        coord.update(dt)
        coord.render()
        
    # 2. 測試 LEVEL_SELECT 狀態 (關卡選擇)
    print("Testing LEVEL_SELECT state...")
    coord.state = "LEVEL_SELECT"
    for _ in range(15):
        coord.update(dt)
        coord.render()
        
    # 3. 測試 GAMEPLAY 狀態 (遊戲中)
    print("Testing GAMEPLAY state...")
    coord.load_game_level(0)
    for _ in range(30):
        coord.update(dt)
        coord.render()
            
    print("Headless gameplay simulation completed successfully!")

if __name__ == "__main__":
    test_gameplay()

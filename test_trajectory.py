import os
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
import pygame
pygame.init()

from main import GameCoordinator
from pygame.math import Vector2

def test_launch(launch_force):
    coord = GameCoordinator()
    coord.load_game_level(0) # Load Level 1
    
    # Get active bird
    bird = coord.slingshot.active_bird
    if not bird:
        print("No active bird!")
        return
        
    print(f"\n--- Testing Launch with force={launch_force} ---")
    
    # Set launch force
    coord.slingshot.launch_force = launch_force
    
    # Simulate drag to (100, 480)
    slingshot_center = Vector2(150, 432)
    drag_pos = Vector2(100, 480)
    launch_vector = slingshot_center - drag_pos
    
    # Launch bird
    bird.vel = launch_vector * launch_force
    bird.is_launched = True
    coord.birds_queue.remove(bird)
    coord.birds_in_air.append(bird)
    
    dt = 1.0 / 60.0
    for frame in range(1, 61):
        coord.update_gameplay(dt)
        print(f"Frame {frame}: pos={bird.pos}, vel={bird.vel}")
        # Stop trace if bird hits the ground or goes out of bounds
        if bird.pos.y >= 500:
            print(f"Bird hit ground at frame {frame}!")
            break

if __name__ == "__main__":
    test_launch(3.6)
    test_launch(10.5)

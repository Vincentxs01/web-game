import os
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
import pygame
pygame.init()

from main import GameCoordinator
from pygame.math import Vector2

def simulate_level_launches(level_idx):
    coord = GameCoordinator()
    coord.load_game_level(level_idx)
    
    print(f"\n======================================")
    print(f"--- Simulating Level {level_idx+1}: {coord.level_name} ---")
    print(f"======================================")
    
    # We will simulate launching all birds one by one until the level ends or we run out.
    bird_idx = 0
    dt = 1.0 / 60.0
    
    while True:
        print(f"\n[Status] Queue len: {len(coord.birds_queue)}, In air: {len(coord.birds_in_air)}, Active: {coord.slingshot.active_bird is not None}, State: {coord.state}")
        
        # If there's an active bird, launch it!
        if coord.slingshot.active_bird and not coord.birds_in_air:
            bird = coord.slingshot.active_bird
            print(f"===> Launching bird {bird_idx}: type={bird.bird_type}")
            
            # Simulate launch by setting velocity and is_launched
            bird.vel = Vector2(500, -300)
            bird.is_launched = True
            
            # Emulate game's handle_gameplay_events:
            coord.birds_in_air.append(bird)
            coord.slingshot.active_bird = None
            coord.last_shot_time = pygame.time.get_ticks()
            
            bird_idx += 1
            
        # Update simulation until the flying bird stops
        ticks_simulated = 0
        while coord.birds_in_air and ticks_simulated < 300: # limit to 5 seconds of flight
            coord.update_gameplay(dt)
            ticks_simulated += 1
            if coord.state in ("VICTORY", "DEFEAT"):
                break
                
        if coord.state in ("VICTORY", "DEFEAT"):
            print(f"Level ended in state: {coord.state}!")
            break
            
        # If no birds in air and no active bird, we are done
        if not coord.birds_in_air and not coord.slingshot.active_bird and not coord.birds_queue:
            print("No birds left anywhere!")
            break
            
        # Check for infinite loop / freeze
        if ticks_simulated >= 300:
            print("[Warning] Bird in air did not stop after 5 seconds!")
            # Manually force stop for next iteration trace
            for b in list(coord.birds_in_air):
                coord.physics_world.remove_body(b)
                coord.birds_in_air.remove(b)
            coord.prepare_next_bird()

if __name__ == "__main__":
    simulate_level_launches(1) # Level 2
    simulate_level_launches(2) # Level 3

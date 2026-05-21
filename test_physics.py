import os
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
import pygame
pygame.init()

from main import GameCoordinator

def debug_sim_level(level_idx):
    coord = GameCoordinator()
    coord.load_game_level(level_idx)
    
    print(f"\n======================================")
    print(f"--- Lifecyle Trace Level {level_idx+1}: {coord.level_name} ---")
    print(f"======================================")
    
    # Print initial pigs
    print("Initial Pigs:")
    for i, body in enumerate(coord.physics_world.bodies):
        if body.category == "pig":
            print(f"  Pig {i}: pos={body.pos}, radius={body.radius}, health={body.health}")
            
    dt = 1.0 / 60.0
    for frame in range(1, 41):
        coord.update_gameplay(dt)
        if coord.physics_world.damage_events:
            print(f"Frame {frame} Damage Events:")
            for ev in coord.physics_world.damage_events:
                b = ev["body"]
                print(f"  {b.category} ({b.material if b.category=='block' else getattr(b, 'pig_type', 'pig')}): damage={ev['damage']:.2f}, health_left={b.health:.2f}, pos={b.pos}, destroyed={ev['destroyed']}")

if __name__ == "__main__":
    debug_sim_level(0)
    debug_sim_level(1)
    debug_sim_level(2)

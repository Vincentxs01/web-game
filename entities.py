import pygame
from pygame.math import Vector2
import math
import random
from physics import PhysicsBody
from sound import sound_manager
from assets import assets

class Bird(PhysicsBody):
    def __init__(self, x, y, bird_type="red"):
        self.bird_type = bird_type
        self.has_used_ability = False
        self.is_launched = False
        self.launch_time = 0
        
        # 依鳥類設定基礎物理屬性
        if bird_type == "red":
            super().__init__(x, y, shape_type="circle", mass=1.0, restitution=0.25, 
                             friction=0.2, radius=15.0, category="bird", material="bird")
        elif bird_type == "yellow": # Chuck: 衝刺鳥
            super().__init__(x, y, shape_type="circle", mass=0.8, restitution=0.15, 
                             friction=0.2, radius=14.0, category="bird", material="bird")
        elif bird_type == "blue":   # Blue: 分裂鳥
            super().__init__(x, y, shape_type="circle", mass=0.5, restitution=0.3, 
                             friction=0.1, radius=10.0, category="bird", material="bird")
        elif bird_type == "bomb":   # Bomb: 爆炸鳥
            super().__init__(x, y, shape_type="circle", mass=3.0, restitution=0.1, 
                             friction=0.4, radius=20.0, category="bird", material="bird")

    def trigger_ability(self, physics_world):
        """觸發鳥類的特殊技能，返回需要新加載到物理世界的物體列表"""
        if self.has_used_ability or not self.is_launched:
            return []
            
        self.has_used_ability = True
        new_bodies = []
        
        if self.bird_type == "yellow":
            # 1. 黃鳥：點擊後極速衝刺，強烈衝擊力
            sound_manager.play("boost")
            self.vel = self.vel.normalize() * 1100.0 # 提速
            
        elif self.bird_type == "blue":
            # 2. 藍鳥：分裂成三隻，各朝不同角度飛去
            sound_manager.play("boost")
            # 獲取當前速度大小與方向
            speed = self.vel.length()
            if speed < 10.0:
                speed = 500.0
            angle = math.atan2(self.vel.y, self.vel.x)
            
            # 分裂角度
            spread_angle = 0.18 # 約 10 度
            
            # 上方分裂鳥
            bird_up = Bird(self.pos.x, self.pos.y - 10, "blue")
            bird_up.is_launched = True
            bird_up.has_used_ability = True
            bird_up.launch_time = self.launch_time
            bird_up.vel = Vector2(math.cos(angle - spread_angle), math.sin(angle - spread_angle)) * (speed * 1.1)
            
            # 下方分裂鳥
            bird_down = Bird(self.pos.x, self.pos.y + 10, "blue")
            bird_down.is_launched = True
            bird_down.has_used_ability = True
            bird_down.launch_time = self.launch_time
            bird_down.vel = Vector2(math.cos(angle + spread_angle), math.sin(angle + spread_angle)) * (speed * 1.1)
            
            # 本身略微加速
            self.vel = self.vel.normalize() * (speed * 1.1)
            
            new_bodies.extend([bird_up, bird_down])
            
        elif self.bird_type == "bomb":
            # 3. 黑鳥：引爆衝擊波
            self.explode(physics_world)
            
        return new_bodies

    def explode(self, physics_world):
        """黑鳥爆炸，對周圍物體施加強大脈衝與傷害"""
        sound_manager.play("explosion")
        explosion_radius = 160.0
        max_force = 1200.0
        
        # 遍歷物理世界中所有的物體
        for body in list(physics_world.bodies):
            if body == self or body.is_static:
                continue
                
            to_body = body.pos - self.pos
            dist = to_body.length()
            
            if dist < explosion_radius:
                normal = to_body.normalize() if dist > 0 else Vector2(0, -1)
                # 距離越近，衝擊力越大
                factor = 1.0 - (dist / explosion_radius)
                push_force = max_force * factor
                
                # 給物體施加向外推動的速度
                body.vel += normal * (push_force * body.inv_mass * 1.4)
                
                # 對豬和方塊造成傷害
                if body.category in ("pig", "block"):
                    body.take_damage(push_force * 0.9)
                    # 觸發物理世界的傷害事件
                    physics_world.damage_events.append({
                        "pos": Vector2(body.pos.x, body.pos.y),
                        "damage": push_force * 0.9,
                        "destroyed": body.is_destroyed,
                        "body": body
                    })
                    
        # 標記自己為已銷毀
        self.is_destroyed = True

    def draw(self, screen, camera_offset):
        """渲染鳥"""
        if self.is_destroyed:
            return
            
        # 取得對應貼圖
        tex_name = f"bird_{self.bird_type}"
        radius = int(self.radius)
        size = radius * 2
        surf = assets.get_texture(tex_name, size, size)
        
        # 旋轉貼圖（根據當前運動速度方向進行微幅偏轉，增加生動感）
        if self.vel.length_squared() > 100:
            angle = math.degrees(math.atan2(-self.vel.y, self.vel.x))
            # 限制旋轉幅度
            angle = max(-45, min(45, angle))
            rotated_surf = pygame.transform.rotate(surf, angle)
            new_rect = rotated_surf.get_rect()
            draw_pos = (self.pos.x - new_rect.width//2 - camera_offset.x, 
                        self.pos.y - new_rect.height//2 - camera_offset.y)
            screen.blit(rotated_surf, draw_pos)
        else:
            draw_pos = (self.pos.x - radius - camera_offset.x, 
                        self.pos.y - radius - camera_offset.y)
            screen.blit(surf, draw_pos)

class Slingshot:
    def __init__(self, x, y):
        self.pos = Vector2(x, y) # 彈弓底座與拉力中心
        self.fork_left = Vector2(x - 14, y - 48)
        self.fork_right = Vector2(x + 14, y - 48)
        self.active_bird = None
        self.is_dragging = False
        self.drag_pos = Vector2(x, y - 48)
        self.max_drag_radius = 70.0
        self.launch_force = 16.5 # 發射力度乘數 (由 14.5 調整為 16.5，以配合較高重力 1150.0)

    def handle_event(self, event, mouse_pos, camera_offset):
        """滑鼠互動邏輯"""
        if not self.active_bird or self.active_bird.is_launched:
            return False
            
        # 滑鼠在世界坐標系下的位置
        world_mouse = Vector2(mouse_pos[0] + camera_offset.x, mouse_pos[1] + camera_offset.y)
        slingshot_center = Vector2(self.pos.x, self.pos.y - 48)
        
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # 檢查點擊是否靠近鳥或彈弓中心
            dist = (world_mouse - self.active_bird.pos).length()
            if dist < 40.0 or (world_mouse - slingshot_center).length() < 35.0:
                self.is_dragging = True
                self.drag_pos = Vector2(world_mouse.x, world_mouse.y)
                
        elif event.type == pygame.MOUSEMOTION and self.is_dragging:
            # 限制拖拽半徑
            offset = world_mouse - slingshot_center
            if offset.length() > self.max_drag_radius:
                self.drag_pos = slingshot_center + offset.normalize() * self.max_drag_radius
            else:
                self.drag_pos = world_mouse
            
            # 同步更新鳥的位置
            self.active_bird.pos = Vector2(self.drag_pos.x, self.drag_pos.y)
            
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1 and self.is_dragging:
            self.is_dragging = False
            slingshot_center = Vector2(self.pos.x, self.pos.y - 48)
            launch_vector = slingshot_center - self.drag_pos
            
            # 發射小鳥！
            if launch_vector.length() > 5.0:
                self.active_bird.vel = launch_vector * self.launch_force
                self.active_bird.is_launched = True
                self.active_bird.launch_time = pygame.time.get_ticks()
                sound_manager.play("launch")
                launched_bird = self.active_bird
                self.active_bird = None
                return launched_bird
            else:
                # 歸位
                self.active_bird.pos = slingshot_center
                
        return False

    def draw_dots(self, screen, camera_offset, gravity_y):
        """繪製發射預測軌跡小圓點 (步進模擬重力與空氣阻力，以獲得 100% 精準與平滑的軌跡)"""
        if not self.is_dragging or not self.active_bird:
            return
            
        slingshot_center = Vector2(self.pos.x, self.pos.y - 48)
        launch_vector = slingshot_center - self.drag_pos
        initial_vel = launch_vector * self.launch_force
        
        # 模擬軌跡點 (模擬 1.5 秒飛行的真實物理軌跡)
        steps = 22
        px = self.active_bird.pos.x
        py = self.active_bird.pos.y
        vx = initial_vel.x
        vy = initial_vel.y
        
        # 每點間隔 0.05 秒。
        # 為了保證模擬精度，使用 0.01 秒作為子步長，每 5 步渲染一個點
        sim_dt = 0.01
        for i in range(1, steps + 1):
            for _ in range(5):
                # 施加重力
                vy += gravity_y * sim_dt
                # 空氣阻力 (小鳥阻力為 0.03)
                drag = 0.03
                vx *= (1.0 - drag * sim_dt)
                vy *= (1.0 - drag * sim_dt)
                # 更新位置
                px += vx * sim_dt
                py += vy * sim_dt
                
            # 漸小與漸淡的小圓點
            alpha = int(255 * (1.0 - (i / steps)))
            dot_radius = max(1, int(4 * (1.0 - (i / steps))))
            
            # 建立帶透明度的白點
            dot_surf = pygame.Surface((dot_radius * 2, dot_radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(dot_surf, (255, 255, 255, alpha), (dot_radius, dot_radius), dot_radius)
            screen.blit(dot_surf, (px - dot_radius - camera_offset.x, py - dot_radius - camera_offset.y))

    def draw_rubber_bands(self, screen, camera_offset, draw_front=False):
        """繪製彈弓的拉伸皮筋"""
        if not self.active_bird:
            return
            
        slingshot_center = Vector2(self.pos.x, self.pos.y - 48)
        # 後側皮筋 (draw_front=False) 與前側皮筋 (draw_front=True)
        # 這樣可以形成小鳥被包裹在皮筋中間的層級視覺效果！
        
        band_color = (80, 40, 15) # 深褐色皮筋
        
        if self.is_dragging:
            thickness = max(2, int(8 - (self.active_bird.pos - slingshot_center).length() / 12))
            
            if not draw_front:
                # 繪製左叉到鳥後側
                pygame.draw.line(screen, band_color, 
                                 (self.fork_left.x - camera_offset.x, self.fork_left.y - camera_offset.y),
                                 (self.active_bird.pos.x - camera_offset.x, self.active_bird.pos.y - camera_offset.y), 
                                 thickness)
            else:
                # 繪製右叉到鳥前側，以及鳥身後方的皮筋交接袋
                pygame.draw.line(screen, band_color, 
                                 (self.fork_right.x - camera_offset.x, self.fork_right.y - camera_offset.y),
                                 (self.active_bird.pos.x - camera_offset.x, self.active_bird.pos.y - camera_offset.y), 
                                 thickness)
                
                # 皮筋交接皮兜
                pouch_rect = pygame.Rect(self.active_bird.pos.x - 7 - camera_offset.x, 
                                         self.active_bird.pos.y - 4 - camera_offset.y, 14, 8)
                pygame.draw.rect(screen, (50, 25, 5), pouch_rect, border_radius=3)
        else:
            # 未拉動狀態，皮筋靜止掛在兩叉間
            if draw_front:
                pygame.draw.line(screen, band_color, 
                                 (self.fork_left.x - camera_offset.x, self.fork_left.y - camera_offset.y),
                                 (self.fork_right.x - camera_offset.x, self.fork_right.y - camera_offset.y), 4)

    def draw_back(self, screen, camera_offset):
        """渲染彈弓後景皮筋"""
        self.draw_rubber_bands(screen, camera_offset, draw_front=False)

    def draw_slingshot(self, screen, camera_offset):
        """渲染彈弓支架與前景皮筋"""
        # 繪製木架
        surf = assets.get_texture("slingshot", 36, 100)
        screen.blit(surf, (self.pos.x - 18 - camera_offset.x, self.pos.y - 100 - camera_offset.y))
        
        # 繪製前景皮筋
        self.draw_rubber_bands(screen, camera_offset, draw_front=True)


class Particle:
    def __init__(self, x, y, dx, dy, color, p_type="rect", size=None, life=1.0):
        self.pos = Vector2(x, y)
        self.vel = Vector2(dx, dy)
        self.color = color
        self.p_type = p_type # "rect", "circle", "triangle", "smoke"
        self.size = size if size else random.randint(4, 8)
        self.life = life
        self.max_life = life
        self.angle = random.uniform(0, 360)
        self.rot_speed = random.uniform(-180, 180)

    def update(self, dt):
        # 阻力與重力更新
        self.vel.y += 350 * dt # 重力下落
        self.vel *= (1.0 - 0.5 * dt)
        self.pos += self.vel * dt
        self.angle += self.rot_speed * dt
        self.life -= dt

    def draw(self, screen, camera_offset):
        alpha = max(0, min(255, int(255 * (self.life / self.max_life))))
        size = max(1, int(self.size * (self.life / self.max_life)))
        
        # 依類型繪製
        if self.p_type == "smoke":
            # 煙霧顆粒：半透明圓形膨脹
            smoke_size = max(1, int(self.size * (2.0 - self.life / self.max_life)))
            surf = pygame.Surface((smoke_size*2, smoke_size*2), pygame.SRCALPHA)
            pygame.draw.circle(surf, (self.color[0], self.color[1], self.color[2], alpha // 2), 
                               (smoke_size, smoke_size), smoke_size)
            screen.blit(surf, (self.pos.x - smoke_size - camera_offset.x, self.pos.y - smoke_size - camera_offset.y))
        elif self.p_type == "rect":
            # 木屑碎片：旋轉矩形
            surf = pygame.Surface((size*2, size), pygame.SRCALPHA)
            surf.fill((self.color[0], self.color[1], self.color[2], alpha))
            rotated = pygame.transform.rotate(surf, self.angle)
            rect = rotated.get_rect(center=(self.pos.x - camera_offset.x, self.pos.y - camera_offset.y))
            screen.blit(rotated, rect.topleft)
        elif self.p_type == "triangle":
            # 冰渣晶瑩碎片：三角形
            surf = pygame.Surface((size*2, size*2), pygame.SRCALPHA)
            points = [(size, 0), (0, size*2), (size*2, size*2)]
            pygame.draw.polygon(surf, (self.color[0], self.color[1], self.color[2], alpha), points)
            rotated = pygame.transform.rotate(surf, self.angle)
            rect = rotated.get_rect(center=(self.pos.x - camera_offset.x, self.pos.y - camera_offset.y))
            screen.blit(rotated, rect.topleft)
        else: # "circle"
            # 石頭碎末
            surf = pygame.Surface((size*2, size*2), pygame.SRCALPHA)
            pygame.draw.circle(surf, (self.color[0], self.color[1], self.color[2], alpha), (size, size), size)
            screen.blit(surf, (self.pos.x - size - camera_offset.x, self.pos.y - size - camera_offset.y))


class ParticleSystem:
    def __init__(self):
        self.particles = []

    def spawn_shards(self, x, y, material, count=8):
        """根據材質生成碰撞碎片"""
        colors = {
            "wood": (211, 137, 71),
            "ice": (200, 240, 255),
            "stone": (150, 150, 150),
            "pig": (100, 230, 130)
        }
        color = colors.get(material, (255, 255, 255))
        p_type = "rect" if material == "wood" else ("triangle" if material == "ice" else ("circle" if material == "pig" else "circle"))
        
        for _ in range(count):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(50, 250)
            dx = math.cos(angle) * speed
            dy = math.sin(angle) * speed - random.uniform(50, 100) # 給予一定朝上的衝力
            
            p = Particle(x, y, dx, dy, color, p_type, size=random.randint(4, 10), life=random.uniform(0.5, 0.9))
            self.particles.append(p)

    def spawn_smoke(self, x, y, count=10, radius=20):
        """生成大爆炸煙霧"""
        for _ in range(count):
            angle = random.uniform(0, math.pi * 2)
            dist = random.uniform(0, radius)
            px = x + math.cos(angle) * dist
            py = y + math.sin(angle) * dist
            
            speed = random.uniform(10, 80)
            dx = math.cos(angle) * speed
            dy = math.sin(angle) * speed - 20 # 緩慢上升
            
            p = Particle(px, py, dx, dy, (220, 220, 220), "smoke", size=random.randint(8, 20), life=random.uniform(0.6, 1.2))
            self.particles.append(p)

    def update(self, dt):
        for p in self.particles[:]:
            p.update(dt)
            if p.life <= 0:
                self.particles.remove(p)

    def draw(self, screen, camera_offset):
        for p in self.particles:
            p.draw(screen, camera_offset)


class FloatingText:
    def __init__(self, x, y, text, color=(255, 255, 255), size=24):
        self.pos = Vector2(x, y)
        self.vel = Vector2(random.uniform(-20, 20), -80.0) # 向上飄動並隨機偏斜
        self.text = text
        self.color = color
        self.size = size
        self.life = 1.0 # 1 秒存活時間
        self.font = pygame.font.SysFont("Comic Sans MS", size, bold=True)

    def update(self, dt):
        self.pos += self.vel * dt
        # 模擬慢慢減速
        self.vel *= (1.0 - 0.8 * dt)
        self.life -= dt

    def draw(self, screen, camera_offset):
        alpha = max(0, min(255, int(255 * self.life)))
        # 繪製文字
        text_surf = self.font.render(self.text, True, self.color)
        
        # 建立透明 Surface 支持漸淡
        txt_w, txt_h = text_surf.get_size()
        fade_surf = pygame.Surface((txt_w, txt_h), pygame.SRCALPHA)
        fade_surf.blit(text_surf, (0, 0))
        
        # 套用透明度包絡線
        alpha_surf = pygame.Surface((txt_w, txt_h), pygame.SRCALPHA)
        alpha_surf.fill((255, 255, 255, alpha))
        fade_surf.blit(alpha_surf, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        
        screen.blit(fade_surf, (self.pos.x - txt_w//2 - camera_offset.x, self.pos.y - txt_h//2 - camera_offset.y))

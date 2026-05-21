import pygame
from pygame.math import Vector2
import math

class PhysicsBody:
    def __init__(self, x, y, shape_type="circle", mass=1.0, is_static=False, 
                 restitution=0.2, friction=0.3, radius=15.0, width=30.0, height=30.0,
                 max_health=100.0, category="block", material="wood"):
        self.pos = Vector2(x, y)
        self.vel = Vector2(0, 0)
        self.shape_type = shape_type # "circle" 或 "rect"
        self.is_static = is_static
        
        if is_static:
            self.mass = float('inf')
            self.inv_mass = 0.0
        else:
            self.mass = float(mass)
            self.inv_mass = 1.0 / self.mass
            
        self.restitution = restitution
        self.friction = friction
        
        # 尺寸
        self.radius = radius
        self.width = width
        self.height = height
        
        # 生命值與破損狀態
        self.max_health = max_health
        self.health = max_health
        self.is_destroyed = False
        
        # 分類與屬性
        self.category = category  # "bird", "pig", "block", "ground"
        self.material = material  # "wood", "ice", "stone", "iron"
        
        # 額外用於渲染與追蹤的欄位
        self.trail = [] # 追蹤歷史軌跡
        self.score_value = 100 if category == "block" else (500 if category == "pig" else 0)

    def take_damage(self, amount):
        if self.is_static or self.is_destroyed:
            return False
        self.health -= amount
        if self.health <= 0:
            self.is_destroyed = True
            return True # 代表此物體被徹底摧毀了
        return False

def check_collision_circle_circle(c1, c2):
    d = c2.pos - c1.pos
    dist = d.length()
    min_dist = c1.radius + c2.radius
    if dist >= min_dist:
        return False, None, 0
    if dist == 0:
        return True, Vector2(0, 1), min_dist
    normal = d / dist
    return True, normal, min_dist - dist

def check_collision_rect_rect(rect_a, rect_b):
    d = rect_b.pos - rect_a.pos
    hw_a = rect_a.width / 2.0
    hw_b = rect_b.width / 2.0
    overlap_x = hw_a + hw_b - abs(d.x)
    if overlap_x <= 0:
        return False, None, 0
        
    hh_a = rect_a.height / 2.0
    hh_b = rect_b.height / 2.0
    overlap_y = hh_a + hh_b - abs(d.y)
    if overlap_y <= 0:
        return False, None, 0
        
    # 重疊較少的那一軸即為碰撞法線方向
    if overlap_x < overlap_y:
        normal = Vector2(1.0 if d.x > 0 else -1.0, 0.0)
        return True, normal, overlap_x
    else:
        normal = Vector2(0.0, 1.0 if d.y > 0 else -1.0)
        return True, normal, overlap_y

def check_collision_circle_rect(c, r):
    d = c.pos - r.pos
    hw = r.width / 2.0
    hh = r.height / 2.0
    
    # 尋找矩形上最靠近圓心的點
    cx = max(-hw, min(hw, d.x))
    cy = max(-hh, min(hh, d.y))
    
    closest = r.pos + Vector2(cx, cy)
    to_circle = c.pos - closest
    dist = to_circle.length()
    
    if dist < c.radius and dist > 0:
        normal = to_circle / dist
        penetration = c.radius - dist
        return True, normal, penetration
    elif dist == 0:
        # 圓心正好落在矩形內部
        dx_left = d.x + hw
        dx_right = hw - d.x
        dy_top = d.y + hh
        dy_bottom = hh - d.y
        min_d = min(dx_left, dx_right, dy_top, dy_bottom)
        
        if min_d == dx_left:
            normal = Vector2(-1.0, 0.0)
        elif min_d == dx_right:
            normal = Vector2(1.0, 0.0)
        elif min_d == dy_top:
            normal = Vector2(0.0, -1.0)
        else:
            normal = Vector2(0.0, 1.0)
            
        penetration = c.radius + min_d
        return True, normal, penetration
        
    return False, None, 0

def check_collision(a, b):
    if a.shape_type == "circle" and b.shape_type == "circle":
        return check_collision_circle_circle(a, b)
    elif a.shape_type == "rect" and b.shape_type == "rect":
        return check_collision_rect_rect(a, b)
    elif a.shape_type == "circle" and b.shape_type == "rect":
        collided, normal, pen = check_collision_circle_rect(a, b)
        if collided:
            return True, -normal, pen
    elif a.shape_type == "rect" and b.shape_type == "circle":
        return check_collision_circle_rect(b, a)
    return False, None, 0

class PhysicsWorld:
    def __init__(self, gravity_y=1150.0):
        self.bodies = []
        self.gravity = Vector2(0.0, gravity_y)
        self.substeps = 6 # 子步數，確保堆疊穩定
        self.damage_events = [] # 記錄損害事件，用於生成粒子與分數漂浮文字
        self.impact_sounds = [] # 記錄需要播放的撞擊音效

    def add_body(self, body):
        self.bodies.append(body)

    def remove_body(self, body):
        if body in self.bodies:
            self.bodies.remove(body)

    def clear(self):
        self.bodies.clear()
        self.damage_events.clear()
        self.impact_sounds.clear()

    def update(self, dt):
        self.damage_events.clear()
        self.impact_sounds.clear()
        
        # 限制 dt，防止極端卡頓導致單幀時間過長
        dt = min(dt, 0.03)
        sub_dt = dt / self.substeps
        
        for step in range(self.substeps):
            # 1. 施加重力並更新位置 (Euler 積分)
            for body in self.bodies:
                if not body.is_static:
                    # 未發射的小鳥不參與物理模擬（不受重力影響、不更新位置）
                    if body.category == "bird" and not getattr(body, "is_launched", False):
                        continue
                    # 施加重力
                    body.vel += self.gravity * sub_dt
                    # 空氣阻力
                    drag = 0.03 if body.category == "bird" else 0.15
                    body.vel *= (1.0 - drag * sub_dt)
                    # 更新位置
                    body.pos += body.vel * sub_dt

            # 2. 檢測並解決碰撞
            for i in range(len(self.bodies)):
                for j in range(i + 1, len(self.bodies)):
                    a = self.bodies[i]
                    b = self.bodies[j]
                    
                    # 未發射的小鳥不參與任何碰撞檢測
                    if a.category == "bird" and not getattr(a, "is_launched", False):
                        continue
                    if b.category == "bird" and not getattr(b, "is_launched", False):
                        continue
                    
                    if a.is_static and b.is_static:
                        continue
                        
                    collided, normal, penetration = check_collision(a, b)
                    if collided:
                        self.resolve_collision(a, b, normal, penetration)

        # 3. 過濾掉已被銷毀的物體
        destroyed_bodies = [b for b in self.bodies if b.is_destroyed]
        for b in destroyed_bodies:
            self.remove_body(b)

    def resolve_collision(self, a, b, normal, penetration):
        # 相對速度
        rv = b.vel - a.vel
        
        # 沿法線方向的速度分量
        vel_along_normal = rv.dot(normal)
        
        # 如果兩者正在遠離，則不進行脈衝處理
        if vel_along_normal > 0:
            return
            
        # 計算反彈係數
        e = min(a.restitution, b.restitution)
        
        # 計算脈衝強度
        total_inv_mass = a.inv_mass + b.inv_mass
        if total_inv_mass == 0:
            return
            
        j = -(1.0 + e) * vel_along_normal / total_inv_mass
        
        # 施加碰撞脈衝
        a.vel -= a.inv_mass * j * normal
        b.vel += b.inv_mass * j * normal
        
        # 切線向量 (摩擦力作用方向)
        rv = b.vel - a.vel
        tangent = rv - (rv.dot(normal)) * normal
        if tangent.length_squared() > 1e-5:
            tangent = tangent.normalize()
            jt = -rv.dot(tangent) / total_inv_mass
            
            # 庫倫摩擦力定律
            mu = math.sqrt(a.friction * b.friction)
            max_jt = j * mu
            jt = max(-max_jt, min(max_jt, jt))
            
            # 施加摩擦力脈衝
            a.vel -= a.inv_mass * jt * tangent
            b.vel += b.inv_mass * jt * tangent
            
        # 位置修正 (Position Correction) 以防物體相互穿透 (解決重疊抖動)
        percent = 0.5  # 修正比例 (0.2 到 0.8 之間)
        slop = 0.02    # 容忍穿透量
        correction = (max(penetration - slop, 0.0) / total_inv_mass) * percent * normal
        if not a.is_static:
            a.pos -= a.inv_mass * correction
        if not b.is_static:
            b.pos += b.inv_mass * correction

        # --- 損害計算系統 ---
        # 碰撞產生的衝擊能量大小與 j 成正比
        impact_energy = j
        
        # 定義不同材質的傷害閾值與承受能力
        # wood, ice, stone, iron / bird, pig, ground
        
        # 只有在衝擊力超過閾值時才造成傷害
        threshold_map = {
            "wood": 65.0,
            "ice": 20.0,
            "stone": 160.0,
            "pig": 15.0,
            "bird": 9999.0 # 鳥類本身不承受生命值傷害
        }
        
        damage_scale_map = {
            "wood": 0.45,
            "ice": 0.9,
            "stone": 0.25,
            "pig": 1.5,
            "bird": 0.0
        }
        
        # 決定聲音類型
        if impact_energy > 60.0:
            sound_type = None
            
            # 依據材質選擇撞擊聲 (移除 category == "pig" 強制播放 pig_pop 的邏輯，回歸為只在死亡時播放)
            mats = [a.material, b.material]
            if "stone" in mats:
                sound_type = "stone_impact"
            elif "wood" in mats or "pig" in mats or "bird" in mats:
                sound_type = "wood_impact"
            elif "ice" in mats:
                sound_type = "ice_impact"
            
            if sound_type and sound_type not in self.impact_sounds:
                self.impact_sounds.append(sound_type)

        # 應用傷害
        for body in (a, b):
            if body.is_static or body.category == "bird":
                continue
                
            mat = body.material if body.category == "block" else "pig"
            thresh = threshold_map.get(mat, 50.0)
            
            if impact_energy > thresh:
                damage = (impact_energy - thresh) * damage_scale_map.get(mat, 0.5)
                # 稍微加入一些隨機化
                damage *= (0.8 + 0.4 * math.sin(impact_energy))
                
                # 僅當此物體碰撞前未被銷毀時才扣血並追加傷害事件，防止同幀多個子步重複死亡 popped
                old_destroyed = body.is_destroyed
                if not old_destroyed:
                    body.take_damage(damage)
                    
                    # 觸發傷害事件
                    self.damage_events.append({
                        "pos": Vector2(body.pos.x, body.pos.y),
                        "damage": damage,
                        "destroyed": body.is_destroyed,
                        "body": body
                    })

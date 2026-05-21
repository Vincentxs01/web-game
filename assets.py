import pygame
import math
import random

# 初始化 pygame 以便建立 Surface
pygame.init()

# 調色盤定義
COLOR_SKY_TOP = (116, 185, 255)      # 陽光透澈藍 (Pastel Sky Blue)
COLOR_SKY_BOTTOM = (250, 240, 230)   # 澄澈白/粉橘 (Pastel Warm White)
COLOR_HILL_FAR = (168, 218, 220)      # 遠景粉藍綠 (Pastel Blue-Green)
COLOR_HILL_MID = (120, 224, 143)      # 中景清新嫩綠 (Pastel Light Green)
COLOR_HILL_NEAR = (95, 226, 156)      # 近景活力草綠 (Pastel Green)
COLOR_WOOD = (196, 120, 56)        # 溫暖原木棕
COLOR_WOOD_DARK = (139, 69, 19)    # 深褐木紋
COLOR_ICE = (173, 232, 244)        # 透亮冰藍
COLOR_ICE_SHINE = (224, 251, 252)  # 冰塊反光白
COLOR_STONE = (127, 143, 166)      # 石頭冷灰
COLOR_STONE_DARK = (87, 101, 116)  # 石頭陰影深灰

class AssetLibrary:
    def __init__(self):
        self.textures = {}

    def get_texture(self, name, width=0, height=0, material="wood"):
        """取得緩存的紋理，如果不存在則動態生成"""
        key = (name, width, height, material)
        if key in self.textures:
            return self.textures[key]
            
        # 依名稱動態生成紋理
        if name == "sky":
            surf = self.create_sky(width, height)
        elif name == "hill":
            surf = self.create_hill_layer(width, height, material) # 這裡 material 代指顏色
        elif name == "cloud":
            surf = self.create_cloud_texture(width, height)
        elif name == "block":
            surf = self.create_block(width, height, material)
        elif name == "bird_red":
            surf = self.create_red_bird(width) # width 代指直徑
        elif name == "bird_yellow":
            surf = self.create_yellow_bird(width)
        elif name == "bird_blue":
            surf = self.create_blue_bird(width)
        elif name == "bird_bomb":
            surf = self.create_bomb_bird(width)
        elif name == "pig_minion":
            surf = self.create_minion_pig(width)
        elif name == "pig_helmet":
            surf = self.create_helmet_pig(width)
        elif name == "pig_king":
            surf = self.create_king_pig(width)
        elif name == "slingshot":
            surf = self.create_slingshot_texture(width, height)
        else:
            surf = pygame.Surface((width, height), pygame.SRCALPHA)
            surf.fill((255, 0, 255)) # 錯誤粉紅粉紫
            
        self.textures[key] = surf
        return surf

    def create_sky(self, w, h):
        """建立天空垂直漸層背景與溫暖太陽光暈"""
        surf = pygame.Surface((w, h))
        for y in range(h):
            # 計算漸層比例
            ratio = y / h
            r = int(COLOR_SKY_TOP[0] * (1 - ratio) + COLOR_SKY_BOTTOM[0] * ratio)
            g = int(COLOR_SKY_TOP[1] * (1 - ratio) + COLOR_SKY_BOTTOM[1] * ratio)
            b = int(COLOR_SKY_TOP[2] * (1 - ratio) + COLOR_SKY_BOTTOM[2] * ratio)
            pygame.draw.line(surf, (r, g, b), (0, y), (w, y))
            
        # 繪製暖陽光暈
        sun_surf = pygame.Surface((w, h), pygame.SRCALPHA)
        sun_center = (w - 150, 100)
        # 外層擴散光暈
        for r_offset, alpha in [(85, 8), (65, 16), (45, 30)]:
            pygame.draw.circle(sun_surf, (255, 253, 220, alpha), sun_center, r_offset)
        # 太陽核心
        pygame.draw.circle(sun_surf, (255, 245, 190), sun_center, 30)
        surf.blit(sun_surf, (0, 0))
        return surf

    def create_hill_layer(self, w, h, hill_type):
        """建立帶有起伏的山丘/地面紋理，並帶有精細裝飾"""
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        color = COLOR_HILL_FAR
        amplitude = 25
        frequency = 0.005
        y_offset = h * 0.4
        
        if hill_type == "far":
            color = COLOR_HILL_FAR
            amplitude = 40
            frequency = 0.003
            y_offset = h * 0.1
        elif hill_type == "mid":
            color = COLOR_HILL_MID
            amplitude = 25
            frequency = 0.006
            y_offset = h * 0.3
        elif hill_type == "near":
            color = COLOR_HILL_NEAR
            amplitude = 15
            frequency = 0.012
            y_offset = h * 0.5

        # 繪製曲線山丘
        points = [(0, h)]
        for x in range(0, w + 10, 10):
            # 正弦波合成山丘曲線
            y = h - (y_offset + amplitude * math.sin(x * frequency) + (amplitude/3) * math.sin(x * frequency * 2.3))
            points.append((x, y))
        points.append((w, h))
        
        pygame.draw.polygon(surf, color, points)
        
        # 使用隨機數生成裝飾 (使用 hash 來維持確定性 seed，避免重複生成不同貼圖)
        val = 0
        for char in hill_type:
            val += ord(char)
        random.seed(val)
        
        # 為近景草地添加小草與野花裝飾
        if hill_type == "near":
            for x in range(20, w, 35):
                base_y = h - (y_offset + amplitude * math.sin(x * frequency) + (amplitude/3) * math.sin(x * frequency * 2.3))
                # 畫幾根小草
                pygame.draw.line(surf, (46, 204, 113), (x, base_y), (x - 4, base_y - 9), 2)
                pygame.draw.line(surf, (46, 204, 113), (x, base_y), (x, base_y - 11), 2)
                pygame.draw.line(surf, (46, 204, 113), (x, base_y), (x + 4, base_y - 9), 2)
                
                # 隨機畫小野花
                if random.random() < 0.3:
                    flower_y = base_y - 4
                    fx = x + 10
                    # 綠色花莖
                    pygame.draw.line(surf, (46, 204, 113), (fx, base_y), (fx, flower_y), 2)
                    # 繽紛花瓣 (粉紅、黃、粉藍)
                    color_petal = random.choice([(255, 116, 185), (254, 202, 87), (255, 159, 243)])
                    pygame.draw.circle(surf, color_petal, (fx - 2, flower_y), 2)
                    pygame.draw.circle(surf, color_petal, (fx + 2, flower_y), 2)
                    pygame.draw.circle(surf, color_petal, (fx, flower_y - 2), 2)
                    pygame.draw.circle(surf, color_petal, (fx, flower_y + 2), 2)
                    # 白色花心
                    pygame.draw.circle(surf, (255, 255, 255), (fx, flower_y), 1)
        
        # 為中景山丘添加小灌木裝飾
        elif hill_type == "mid":
            for x in range(30, w, 60):
                base_y = h - (y_offset + amplitude * math.sin(x * frequency) + (amplitude/3) * math.sin(x * frequency * 2.3))
                if random.random() < 0.25:
                    # 灌木由多個綠色小圓重疊組成
                    bush_color = (106, 176, 76)
                    pygame.draw.circle(surf, bush_color, (x, int(base_y - 3)), 6)
                    pygame.draw.circle(surf, bush_color, (x - 4, int(base_y - 2)), 4)
                    pygame.draw.circle(surf, bush_color, (x + 4, int(base_y - 2)), 4)
                
        return surf

    def create_cloud_texture(self, w, h):
        """建立帶有輕微層次與立體感的蓬鬆白雲紋理"""
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        # 由複數個白色半透明圓形與底層微弱灰色陰影疊加而成
        r_base = h // 3
        
        # 1. 繪製底部陰影層 (稍低、偏灰藍色，增加雲的厚重感)
        shadow_surf = pygame.Surface((w, h), pygame.SRCALPHA)
        s_color = (200, 214, 229, 130) # 灰藍色半透明
        pygame.draw.circle(shadow_surf, s_color, (w // 3, h // 2 + 3), int(r_base * 1.2))
        pygame.draw.circle(shadow_surf, s_color, (w // 2, h // 2 + 3 - 5), int(r_base * 1.5))
        pygame.draw.circle(shadow_surf, s_color, (2 * w // 3, h // 2 + 3), int(r_base * 1.1))
        pygame.draw.ellipse(shadow_surf, s_color, (r_base, h - r_base * 2 + 2, w - r_base * 2, r_base * 2))
        surf.blit(shadow_surf, (0, 0))
        
        # 2. 繪製白雲本體層 (純白)
        w_color = (255, 255, 255, 220)
        # 底部橢圓
        pygame.draw.ellipse(surf, w_color, (r_base, h - r_base * 2, w - r_base * 2, r_base * 2))
        # 左側圓頂
        pygame.draw.circle(surf, w_color, (w // 3, h // 2), int(r_base * 1.2))
        # 中間主圓頂
        pygame.draw.circle(surf, w_color, (w // 2, h // 2 - 5), int(r_base * 1.5))
        # 右側圓頂
        pygame.draw.circle(surf, w_color, (2 * w // 3, h // 2), int(r_base * 1.1))
        
        # 3. 頂部高光層 (內側更純亮，增加蓬鬆度)
        highlight_color = (255, 255, 255, 245)
        pygame.draw.circle(surf, highlight_color, (w // 2, h // 2 - 8), int(r_base * 1.0))
        pygame.draw.circle(surf, highlight_color, (w // 3 + 2, h // 2 - 3), int(r_base * 0.8))
        
        return surf

    def create_block(self, w, h, material):
        """建立木、冰、石等材質的方塊紋理，支援不同尺寸"""
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        rect = pygame.Rect(0, 0, w, h)
        
        if material == "wood":
            # 填滿原木色
            surf.fill(COLOR_WOOD)
            # 邊框與陰影
            pygame.draw.rect(surf, COLOR_WOOD_DARK, rect, 3)
            pygame.draw.rect(surf, (243, 156, 18), rect, 1) # 內側高光亮邊
            # 繪製木質年輪與木紋線條
            for i in range(1, 4):
                line_y = int(h * (i / 4.0))
                pygame.draw.line(surf, COLOR_WOOD_DARK, (4, line_y), (w - 4, line_y), 1)
            # 四角圓形小鉚釘
            if w >= 15 and h >= 15:
                for dx, dy in [(6, 6), (w-6, 6), (6, h-6), (w-6, h-6)]:
                    pygame.draw.circle(surf, COLOR_WOOD_DARK, (dx, dy), 2)
                    
        elif material == "ice":
            # 填滿冰藍色（帶點透明度）
            surf.fill((COLOR_ICE[0], COLOR_ICE[1], COLOR_ICE[2], 180))
            # 冰塊邊框
            pygame.draw.rect(surf, COLOR_ICE_SHINE, rect, 2)
            # 繪製冰塊內側裂痕
            random.seed(w * h) # 固定隨機數，確保紋理一致
            for _ in range(3):
                x1, y1 = random.randint(4, w-4), random.randint(4, h-4)
                x2, y2 = x1 + random.randint(-15, 15), y1 + random.randint(-15, 15)
                x2 = max(4, min(w-4, x2))
                y2 = max(4, min(h-4, y2))
                pygame.draw.line(surf, (255, 255, 255, 200), (x1, y1), (x2, y2), 1)
            # 冰冷高光
            pygame.draw.polygon(surf, (255, 255, 255, 100), [(2, 2), (w-2, 2), (2, h-2)])
            
        elif material == "stone":
            # 填滿灰色
            surf.fill(COLOR_STONE)
            # 邊框與凹凸感
            pygame.draw.rect(surf, COLOR_STONE_DARK, rect, 3)
            # 石頭表面雜訊與裂縫
            random.seed(w + h)
            for _ in range(2):
                x1, y1 = random.randint(5, w-5), random.randint(5, h-5)
                x2, y2 = x1 + random.randint(-10, 10), y1 + random.randint(-10, 10)
                x2 = max(5, min(w-5, x2))
                y2 = max(5, min(h-5, y2))
                pygame.draw.line(surf, COLOR_STONE_DARK, (x1, y1), (x2, y2), 2)
            # 繪製高光小斑塊
            for _ in range(4):
                rx = random.randint(3, w-6)
                ry = random.randint(3, h-6)
                pygame.draw.rect(surf, (189, 195, 199), (rx, ry, 3, 3))
                
        return surf

    def create_red_bird(self, diameter):
        """繪製超精緻小紅鳥"""
        r = diameter // 2
        surf = pygame.Surface((diameter, diameter), pygame.SRCALPHA)
        center = (r, r)
        
        # 1. 頂部羽毛
        pygame.draw.ellipse(surf, (192, 41, 43), (r - 6, 0, 12, 12))
        pygame.draw.ellipse(surf, (192, 41, 43), (r - 12, 2, 10, 10))
        
        # 2. 鳥身紅球
        pygame.draw.circle(surf, (231, 76, 60), center, r - 2)
        pygame.draw.circle(surf, (192, 41, 43), center, r - 2, 2) # 暗色輪廓
        
        # 3. 肚皮（白色半圓形）
        belly_surf = pygame.Surface((diameter, diameter), pygame.SRCALPHA)
        pygame.draw.circle(belly_surf, (245, 246, 250), (r, r + 4), r - 5)
        # 用剪裁方式只保留下半身
        surf.blit(belly_surf, (0, 0), pygame.Rect(0, r - 2, diameter, r + 2))
        
        # 4. 眼睛（兩顆大眼睛緊貼在一起）
        eye_r = 5
        eye_y = r - 3
        # 左眼
        pygame.draw.circle(surf, (255, 255, 255), (r + 1, eye_y), eye_r)
        pygame.draw.circle(surf, (0, 0, 0), (r + 1, eye_y), eye_r, 1)
        pygame.draw.circle(surf, (0, 0, 0), (r + 2, eye_y), 2) # 瞳孔
        # 右眼
        pygame.draw.circle(surf, (255, 255, 255), (r + 8, eye_y), eye_r)
        pygame.draw.circle(surf, (0, 0, 0), (r + 8, eye_y), eye_r, 1)
        pygame.draw.circle(surf, (0, 0, 0), (r + 8, eye_y), 2) # 瞳孔
        
        # 5. 憤怒的粗黑眉毛
        pygame.draw.polygon(surf, (44, 62, 80), [(r - 5, eye_y - 7), (r + 11, eye_y - 5), (r + 3, eye_y - 2)])
        
        # 6. 黃色大嘴巴（三角形）
        pygame.draw.polygon(surf, (241, 196, 15), [(r + 2, r + 1), (r + 13, r + 4), (r + 2, r + 7)])
        pygame.draw.polygon(surf, (211, 84, 0), [(r + 2, r + 1), (r + 13, r + 4), (r + 2, r + 7)], 1)
        
        return surf

    def create_yellow_bird(self, diameter):
        """繪製超萌三角形黃鳥 (Chuck)"""
        r = diameter // 2
        surf = pygame.Surface((diameter, diameter), pygame.SRCALPHA)
        
        # 1. 頂部大黑羽毛
        pygame.draw.polygon(surf, (44, 62, 80), [(r - 10, 2), (r, 12), (r - 2, 0)])
        pygame.draw.polygon(surf, (44, 62, 80), [(r - 4, 0), (r + 4, 10), (r + 2, 2)])
        
        # 2. 三角形身體
        points = [(r, 4), (2, diameter - 3), (diameter - 2, diameter - 3)]
        pygame.draw.polygon(surf, (241, 196, 15), points)
        pygame.draw.polygon(surf, (219, 178, 10), points, 2)
        
        # 3. 白色肚皮
        pygame.draw.ellipse(surf, (245, 246, 250), (r - 8, diameter - 12, 16, 9))
        
        # 4. 雙眼
        eye_y = r + 1
        pygame.draw.circle(surf, (255, 255, 255), (r - 2, eye_y), 4)
        pygame.draw.circle(surf, (0, 0, 0), (r - 2, eye_y), 1)
        pygame.draw.circle(surf, (255, 255, 255), (r + 4, eye_y), 4)
        pygame.draw.circle(surf, (0, 0, 0), (r + 4, eye_y), 1)
        
        # 5. 淺紅眉毛
        pygame.draw.line(surf, (192, 57, 43), (r - 6, eye_y - 4), (r, eye_y - 2), 2)
        pygame.draw.line(surf, (192, 57, 43), (r + 8, eye_y - 4), (r + 2, eye_y - 2), 2)
        
        # 6. 長長橘色鳥嘴
        pygame.draw.polygon(surf, (230, 126, 34), [(r - 1, eye_y + 1), (r + 12, eye_y + 4), (r - 1, eye_y + 7)])
        
        return surf

    def create_blue_bird(self, diameter):
        """繪製小藍鳥 (The Blues)"""
        r = diameter // 2
        surf = pygame.Surface((diameter, diameter), pygame.SRCALPHA)
        center = (r, r)
        
        # 1. 藍色圓形身體
        pygame.draw.circle(surf, (52, 152, 219), center, r - 1)
        pygame.draw.circle(surf, (41, 128, 185), center, r - 1, 1)
        
        # 2. 橘紅色眼眶
        pygame.draw.circle(surf, (230, 126, 34), (r - 3, r - 2), 4)
        pygame.draw.circle(surf, (230, 126, 34), (r + 3, r - 2), 4)
        
        # 3. 雙眼與黑色瞳孔
        pygame.draw.circle(surf, (255, 255, 255), (r - 2, r - 2), 3)
        pygame.draw.circle(surf, (0, 0, 0), (r - 2, r - 2), 1)
        pygame.draw.circle(surf, (255, 255, 255), (r + 3, r - 2), 3)
        pygame.draw.circle(surf, (0, 0, 0), (r + 3, r - 2), 1)
        
        # 4. 黃色小鳥嘴
        pygame.draw.polygon(surf, (241, 196, 15), [(r, r), (r + 6, r + 2), (r, r + 4)])
        
        # 5. 頭頂一根小毛
        pygame.draw.line(surf, (41, 128, 185), (r, 1), (r - 3, -1), 2)
        
        return surf

    def create_bomb_bird(self, diameter):
        """繪製大黑鳥 (Bomb)"""
        r = diameter // 2
        surf = pygame.Surface((diameter, diameter), pygame.SRCALPHA)
        center = (r, r)
        
        # 1. 頂部引信炸彈線
        pygame.draw.line(surf, (44, 62, 80), (r, r), (r, 2), 3)
        pygame.draw.circle(surf, (241, 196, 15), (r, 2), 3) # 黃色引信頭
        
        # 2. 黑色重型圓形鳥身
        pygame.draw.circle(surf, (44, 62, 80), center, r - 2)
        pygame.draw.circle(surf, (24, 34, 45), center, r - 2, 2)
        
        # 3. 額頭灰色斑點
        pygame.draw.circle(surf, (127, 140, 141), (r, r - 10), 5)
        
        # 4. 紅色憤怒雙眼
        eye_y = r - 3
        # 左眼
        pygame.draw.circle(surf, (255, 255, 255), (r - 5, eye_y), 5)
        pygame.draw.circle(surf, (231, 76, 60), (r - 5, eye_y), 3) # 紅色眼珠
        pygame.draw.circle(surf, (0, 0, 0), (r - 4, eye_y), 1)
        # 右眼
        pygame.draw.circle(surf, (255, 255, 255), (r + 5, eye_y), 5)
        pygame.draw.circle(surf, (231, 76, 60), (r + 5, eye_y), 3)
        pygame.draw.circle(surf, (0, 0, 0), (r + 4, eye_y), 1)
        
        # 5. 鮮明黃色鳥嘴
        pygame.draw.polygon(surf, (241, 196, 15), [(r - 2, r + 2), (r + 9, r + 5), (r - 2, r + 10)])
        
        return surf

    def create_minion_pig(self, diameter):
        """繪製普通綠豬 (Minion Pig)"""
        r = diameter // 2
        surf = pygame.Surface((diameter, diameter), pygame.SRCALPHA)
        center = (r, r)
        
        # 1. 綠色圓形豬身
        pygame.draw.circle(surf, (46, 204, 113), center, r - 2)
        pygame.draw.circle(surf, (39, 174, 96), center, r - 2, 2)
        
        # 2. 豬耳朵
        pygame.draw.circle(surf, (46, 204, 113), (r - 9, 3), 4)
        pygame.draw.circle(surf, (231, 76, 60), (r - 9, 3), 2) # 耳內粉紅色
        pygame.draw.circle(surf, (46, 204, 113), (r + 9, 3), 4)
        pygame.draw.circle(surf, (231, 76, 60), (r + 9, 3), 2)
        
        # 3. 搞怪的呆萌大眼睛
        eye_y = r - 4
        # 左眼
        pygame.draw.circle(surf, (255, 255, 255), (r - 6, eye_y), 5)
        pygame.draw.circle(surf, (0, 0, 0), (r - 6, eye_y), 1) # 瞳孔偏左
        # 右眼
        pygame.draw.circle(surf, (255, 255, 255), (r + 6, eye_y), 5)
        pygame.draw.circle(surf, (0, 0, 0), (r + 5, eye_y), 1) # 瞳孔偏右
        
        # 4. 豬鼻子 (深綠大橢圓形)
        snout_w, snout_h = 12, 8
        pygame.draw.ellipse(surf, (39, 174, 96), (r - snout_w//2, r - 2, snout_w, snout_h))
        pygame.draw.ellipse(surf, (30, 130, 70), (r - snout_w//2, r - 2, snout_w, snout_h), 1)
        # 鼻孔
        pygame.draw.circle(surf, (20, 90, 50), (r - 3, r + 2), 2)
        pygame.draw.circle(surf, (20, 90, 50), (r + 3, r + 2), 2)
        
        # 5. 傻傻的微笑
        pygame.draw.arc(surf, (39, 174, 96), (r - 6, r + 3, 12, 6), math.pi, 2.0 * math.pi, 2)
        
        return surf

    def create_helmet_pig(self, diameter):
        """繪製帶金屬頭盔的綠豬"""
        surf = self.create_minion_pig(diameter)
        r = diameter // 2
        
        # 繪製一個精美的灰色金屬頭盔覆蓋在上半部
        helmet_surf = pygame.Surface((diameter, diameter), pygame.SRCALPHA)
        # 繪製鋼盔圓頂
        pygame.draw.arc(helmet_surf, (149, 165, 166), (1, 1, diameter - 2, diameter), math.pi * 0.05, math.pi * 0.95, r)
        # 繪製頭盔沿邊輪廓
        pygame.draw.ellipse(helmet_surf, (127, 140, 141), (0, r - 6, diameter, 5))
        # 繪製頭盔帶子(小皮帶在下巴位置)
        pygame.draw.line(helmet_surf, (110, 80, 40), (2, r - 2), (2, r + 6), 2)
        pygame.draw.line(helmet_surf, (110, 80, 40), (diameter - 3, r - 2), (diameter - 3, r + 6), 2)
        
        # 疊加鋼盔到豬頭上
        surf.blit(helmet_surf, (0, 0))
        return surf

    def create_king_pig(self, diameter):
        """繪製帶皇冠的巨無霸國王豬"""
        surf = self.create_minion_pig(diameter)
        r = diameter // 2
        
        # 在頂部繪製一頂金黃色的炫酷皇冠
        crown_surf = pygame.Surface((diameter, diameter), pygame.SRCALPHA)
        # 皇冠底部基座
        base_y = r - 12
        pygame.draw.rect(crown_surf, (241, 196, 15), (r - 10, base_y, 20, 4))
        # 皇冠的三個尖角 (三角形)
        # 左尖角
        pygame.draw.polygon(crown_surf, (241, 196, 15), [(r - 10, base_y), (r - 8, base_y - 10), (r - 3, base_y)])
        # 中間尖角 (最高)
        pygame.draw.polygon(crown_surf, (241, 196, 15), [(r - 5, base_y), (r, base_y - 14), (r + 5, base_y)])
        # 右尖角
        pygame.draw.polygon(crown_surf, (241, 196, 15), [(r + 3, base_y), (r + 8, base_y - 10), (r + 10, base_y)])
        
        # 皇冠寶石 (紅藍亮點)
        pygame.draw.circle(crown_surf, (231, 76, 60), (r - 7, base_y + 2), 1) # 紅色
        pygame.draw.circle(crown_surf, (52, 152, 219), (r, base_y + 2), 1)    # 藍色
        pygame.draw.circle(crown_surf, (231, 76, 60), (r + 7, base_y + 2), 1) # 紅色
        # 皇冠尖端寶石圓珠
        pygame.draw.circle(crown_surf, (255, 255, 255), (r - 8, base_y - 10), 2)
        pygame.draw.circle(crown_surf, (255, 255, 255), (r, base_y - 14), 2.5)
        pygame.draw.circle(crown_surf, (255, 255, 255), (r + 8, base_y - 10), 2)

        # 疊加皇冠
        surf.blit(crown_surf, (0, 0))
        return surf

    def create_slingshot_texture(self, w, h):
        """建立極具立體感的木質彈弓紋理"""
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        # 繪製主幹
        pygame.draw.rect(surf, (110, 70, 30), (w//2 - 4, h//2, 8, h//2))
        pygame.draw.rect(surf, (70, 45, 20), (w//2 - 4, h//2, 8, h//2), 1)
        
        # 繪製 Y 型左分叉和右分叉
        pygame.draw.polygon(surf, (110, 70, 30), [(w//2 - 4, h//2 + 2), (w//2 + 4, h//2 + 2), (w - 2, 2), (w - 10, 0)])
        pygame.draw.polygon(surf, (110, 70, 30), [(w//2 - 4, h//2 + 2), (w//2 + 4, h//2 + 2), (2, 2), (10, 0)])
        
        # 分叉輪廓線
        pygame.draw.polygon(surf, (70, 45, 20), [(w//2 - 4, h//2 + 2), (w//2 + 4, h//2 + 2), (w - 2, 2), (w - 10, 0)], 1)
        pygame.draw.polygon(surf, (70, 45, 20), [(w//2 - 4, h//2 + 2), (w//2 + 4, h//2 + 2), (2, 2), (10, 0)], 1)
        
        # 在頂部皮筋懸掛處加點金屬螺栓
        pygame.draw.circle(surf, (127, 140, 141), (6, 2), 2)
        pygame.draw.circle(surf, (127, 140, 141), (w - 6, 2), 2)
        
        return surf

# 全局調用單例
assets = AssetLibrary()

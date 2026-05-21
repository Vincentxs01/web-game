import pygame
from pygame.math import Vector2
import sys
import math
import random
import json
import os

# 導入自定義組件
from physics import PhysicsWorld, PhysicsBody
from sound import sound_manager
from assets import assets
from entities import Bird, Slingshot, ParticleSystem, FloatingText
from levels import load_level, save_custom_level

# 視窗解析度設定
SCREEN_WIDTH = 960
SCREEN_HEIGHT = 540
FPS = 60

# 存檔路徑
SAVE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "save_data.json")

# 系統常見中文字型後備清單，解決中文字型缺失時顯示為豆腐框的問題
CHINESE_FONTS = ['microsoftjhenghei', 'microsoftyahei', 'simhei', 'dengxian', 'mingliu', 'dfkai-sb', 'arial']

class GameCoordinator:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("憤怒鳥 Python 克隆版 (Angry Birds)")
        self.clock = pygame.time.Clock()
        
        # 初始化音效並播放背景音樂
        sound_manager.init_sounds()
        sound_manager.play_music()
        
        # 遊戲狀態: "MENU", "LEVEL_SELECT", "GAMEPLAY", "EDITOR", "VICTORY", "DEFEAT"
        self.state = "MENU"
        
        # 遊戲數據
        self.score = 0
        self.high_scores = {"0": 0, "1": 0, "2": 0, "custom": 0}
        self.load_save_data()
        
        # 當前關卡索引 (0, 1, 2 或 "custom")
        self.current_level_idx = 0
        self.level_name = ""
        
        # 實體與引擎
        self.physics_world = PhysicsWorld()
        self.slingshot = Slingshot(150, 480)
        self.particle_system = ParticleSystem()
        self.floating_texts = []
        
        # 關卡小鳥隊列與在空中的小鳥
        self.birds_queue = []
        self.birds_in_air = []
        
        # 鏡頭與畫面震動
        self.camera_offset = Vector2(0, 0)
        self.camera_target_x = 0.0
        self.shake_intensity = 0.0
        
        # 判定剩餘時間
        self.state_timer = 0
        self.last_shot_time = 0
        self.level_completed = False
        self.level_failed = False
        
        # --- 關卡編輯器專用屬性 ---
        self.editor_blocks = [] # 儲存擺放的方塊 {"material": x, "x": x, "y": y, "width": w, "height": h, "shape_type": "rect"}
        self.editor_pigs = []   # 儲存擺放的豬 {"pig_type": x, "x": x, "y": y}
        self.editor_selected_tool = "block_wood" # 當前選中工具: "block_wood", "block_ice", "block_stone", "pig_minion", "pig_helmet", "pig_king"
        self.editor_block_orientation = "vertical" # 方塊方向: "vertical", "horizontal", "square"

        # 註冊音效播放時的字幕回呼與字幕列表
        sound_manager.subtitle_callback = self.on_sound_played
        self.subtitles = []  # [{"text": "...", "timer": 1.5}]
        
        # 初始化動態白雲 (x, y, speed, w, h)
        self.clouds = [
            {"x": 100, "y": 80, "speed": 12, "w": 120, "h": 60},
            {"x": 450, "y": 140, "speed": 8, "w": 180, "h": 90},
            {"x": 800, "y": 60, "speed": 15, "w": 100, "h": 50},
        ]

    def update_clouds(self, dt):
        """更新動態雲朵位置"""
        import random
        for cloud in self.clouds:
            cloud["x"] -= cloud["speed"] * dt
            # 如果雲朵完全移出左側螢幕，從右側重新出現，並隨機分配高度與速度
            if cloud["x"] + cloud["w"] < -50:
                cloud["x"] = SCREEN_WIDTH + random.randint(20, 100)
                cloud["y"] = random.randint(30, 150)
                cloud["speed"] = random.randint(6, 15)

    def load_save_data(self):
        """載入存檔（高分紀錄）- 已停用，每次重開遊玩重新記錄"""
        pass

    def write_save_data(self):
        """保存高分紀錄 - 已停用，每次重開遊玩重新記錄"""
        pass

    def load_game_level(self, level_idx):
        """加載關卡並初始化世界"""
        self.current_level_idx = level_idx
        data = load_level(level_idx)
        self.level_name = data["name"]
        
        # 1. 重設世界與狀態
        self.physics_world.clear()
        self.particle_system.particles.clear()
        self.floating_texts.clear()
        self.birds_queue.clear()
        self.birds_in_air.clear()
        
        self.score = 0
        self.camera_offset = Vector2(0, 0)
        self.camera_target_x = 0.0
        self.shake_intensity = 0.0
        self.level_completed = False
        self.level_failed = False
        self.state_timer = 0
        
        # 2. 建立靜態地面 (PhysicsBody)
        # 地面高度改為 500 到 520 (中心 510)，寬度延長到 1600
        ground = PhysicsBody(800, 510, shape_type="rect", is_static=True, 
                             restitution=0.1, friction=0.6, width=1600, height=20, 
                             category="ground", material="stone")
        self.physics_world.add_body(ground)
        
        # 3. 實例化方塊並加入物理世界
        for b in data["blocks"]:
            block_body = PhysicsBody(b["x"], b["y"], shape_type="rect", 
                                     mass=1.2 if b["material"] == "wood" else (0.4 if b["material"] == "ice" else 3.0),
                                     restitution=0.1 if b["material"] == "stone" else 0.2,
                                     friction=0.3 if b["material"] == "ice" else 0.4,
                                     width=b["width"], height=b["height"],
                                     max_health=40.0 if b["material"] == "wood" else (15.0 if b["material"] == "ice" else 120.0),
                                     category="block", material=b["material"])
            self.physics_world.add_body(block_body)
            
        # 4. 實例化豬隻並加入物理世界
        for p in data["pigs"]:
            pig_body = PhysicsBody(p["x"], p["y"], shape_type="circle",
                                   mass=1.0 if p["pig_type"] == "minion" else (1.5 if p["pig_type"] == "helmet" else 3.5),
                                   restitution=0.15, friction=0.3,
                                   radius=15.0 if p["pig_type"] != "king" else 24.0,
                                   max_health=15.0 if p["pig_type"] == "minion" else (35.0 if p["pig_type"] == "helmet" else 60.0),
                                   category="pig", material="pig")
            # 依類型設置特殊屬性以供 assets 識別渲染
            pig_body.pig_type = p["pig_type"]
            self.physics_world.add_body(pig_body)
            
        # 5. 建立小鳥排隊隊列
        # 彈弓中心拉力位置大概在 (150, 432)
        slingshot_center = Vector2(150, 432)
        for i, bird_type in enumerate(data["birds"]):
            # 隊列中其餘小鳥站在左側地面排隊
            if i == 0:
                bird = Bird(slingshot_center.x, slingshot_center.y, bird_type)
                self.slingshot.active_bird = bird
            else:
                bird = Bird(110 - i * 30, 485, bird_type)
            self.birds_queue.append(bird)
            self.physics_world.add_body(bird)
            
        self.state = "GAMEPLAY"

    def run(self):
        """遊戲主循環"""
        running = True
        while running:
            # 限制幀率，取得每幀毫秒數
            dt = self.clock.tick(FPS) / 1000.0
            
            running = self.handle_events()
            self.update(dt)
            self.render()
            
        pygame.quit()
        sys.exit()

    def handle_events(self):
        mouse_pos = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
                
            # 按鍵盤 ESC 退出到主選單
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                if self.state in ("GAMEPLAY", "LEVEL_SELECT", "EDITOR"):
                    self.state = "MENU"
                elif self.state == "MENU":
                    return False
                    
            if self.state == "MENU":
                self.handle_menu_events(event, mouse_pos)
            elif self.state == "LEVEL_SELECT":
                self.handle_level_select_events(event, mouse_pos)
            elif self.state == "GAMEPLAY":
                self.handle_gameplay_events(event, mouse_pos)
            elif self.state == "EDITOR":
                self.handle_editor_events(event, mouse_pos)
            elif self.state in ("VICTORY", "DEFEAT"):
                self.handle_game_over_events(event, mouse_pos)
                
        return True

    def handle_menu_events(self, event, mouse_pos):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # 點擊 "開始遊戲" 按鈕 (960x540 中間，自適應新尺寸: 370 <= x <= 590, 270 <= y <= 326)
            if 370 <= mouse_pos[0] <= 590 and 270 <= mouse_pos[1] <= 326:
                sound_manager.play("boost")
                self.state = "LEVEL_SELECT"

    def handle_level_select_events(self, event, mouse_pos):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # 關卡 1、2、3 的點擊
            # 關卡 1: (150, 200, 160, 100)
            # 關卡 2: (400, 200, 160, 100)
            # 關卡 3: (650, 200, 160, 100)
            if 200 <= mouse_pos[1] <= 300:
                if 150 <= mouse_pos[0] <= 310:
                    sound_manager.play("launch")
                    self.load_game_level(0)
                elif 400 <= mouse_pos[0] <= 560:
                    sound_manager.play("launch")
                    self.load_game_level(1)
                elif 650 <= mouse_pos[0] <= 810:
                    sound_manager.play("launch")
                    self.load_game_level(2)

    def handle_gameplay_events(self, event, mouse_pos):
        # 1. 彈弓拖拽與發射處理
        launched_bird = self.slingshot.handle_event(event, mouse_pos, self.camera_offset)
        if launched_bird:
            self.birds_in_air.append(launched_bird)
            self.last_shot_time = pygame.time.get_ticks()
            
        # 2. 快捷重置關卡 (R 鍵)
        if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
            self.load_game_level(self.current_level_idx)
            
        # 3. 飛行中點擊左鍵觸發特殊技能
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if not self.slingshot.is_dragging:
                # 遍歷天空中尚未觸發技能的小鳥
                for bird in self.birds_in_air:
                    if not bird.has_used_ability:
                        # 觸發技能，分裂鳥會返回新鳥
                        new_birds = bird.trigger_ability(self.physics_world)
                        for nb in new_birds:
                            self.physics_world.add_body(nb)
                            self.birds_in_air.append(nb)
                        # 一次點擊只觸發一隻鳥的技能 (最前面的)
                        break

    def handle_editor_events(self, event, mouse_pos):
        world_mouse = Vector2(mouse_pos[0] + self.camera_offset.x, mouse_pos[1] + self.camera_offset.y)
        
        # 編輯器視窗按鈕點擊
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # 頂部工具列按鈕 (橫排 x 軸)
            # 各按鈕矩形：
            # 1. 木箱 (10, 10, 80, 35)
            # 2. 冰箱 (100, 10, 80, 35)
            # 3. 石箱 (190, 10, 80, 35)
            # 4. 普通豬 (290, 10, 80, 35)
            # 5. 頭盔豬 (380, 10, 80, 35)
            # 6. 國王豬 (470, 10, 80, 35)
            # 7. 方向切換 (570, 10, 80, 35)
            # 8. 保存 (680, 10, 80, 35)
            # 9. 測試遊玩 (770, 10, 80, 35)
            # 10. 清空 (860, 10, 80, 35)
            if 10 <= mouse_pos[1] <= 45:
                if 10 <= mouse_pos[0] <= 90:
                    self.editor_selected_tool = "block_wood"
                    sound_manager.play("ice_impact")
                elif 100 <= mouse_pos[0] <= 180:
                    self.editor_selected_tool = "block_ice"
                    sound_manager.play("ice_impact")
                elif 190 <= mouse_pos[0] <= 270:
                    self.editor_selected_tool = "block_stone"
                    sound_manager.play("ice_impact")
                elif 290 <= mouse_pos[0] <= 370:
                    self.editor_selected_tool = "pig_minion"
                    sound_manager.play("ice_impact")
                elif 380 <= mouse_pos[0] <= 460:
                    self.editor_selected_tool = "pig_helmet"
                    sound_manager.play("ice_impact")
                elif 470 <= mouse_pos[0] <= 550:
                    self.editor_selected_tool = "pig_king"
                    sound_manager.play("ice_impact")
                elif 570 <= mouse_pos[0] <= 650:
                    # 切換方塊擺放方向
                    orientations = ["vertical", "horizontal", "square"]
                    idx = (orientations.index(self.editor_block_orientation) + 1) % 3
                    self.editor_block_orientation = orientations[idx]
                    sound_manager.play("boost")
                elif 680 <= mouse_pos[0] <= 760:
                    # 保存關卡
                    save_custom_level(self.editor_blocks, self.editor_pigs)
                    sound_manager.play("victory")
                elif 770 <= mouse_pos[0] <= 850:
                    # 測試遊玩自定義關卡
                    save_custom_level(self.editor_blocks, self.editor_pigs)
                    sound_manager.play("launch")
                    self.load_game_level("custom")
                elif 860 <= mouse_pos[0] <= 940:
                    # 清空關卡
                    self.editor_blocks.clear()
                    self.editor_pigs.clear()
                    sound_manager.play("defeat")
                return # 點擊工具列不進行方塊放置
                
            # 點擊遊戲畫面放置物體 (避開底座與左側發射區)
            if world_mouse.x > 300 and world_mouse.y < 510:
                # 網格對齊 (對齊 10 像素以利疊高)
                grid_x = round(world_mouse.x / 10.0) * 10
                grid_y = round(world_mouse.y / 10.0) * 10
                
                # 放置方塊
                if self.editor_selected_tool.startswith("block"):
                    mat = self.editor_selected_tool.split("_")[1]
                    # 決定尺寸
                    w, h = 20, 80
                    if self.editor_block_orientation == "horizontal":
                        w, h = 80, 20
                    elif self.editor_block_orientation == "square":
                        w, h = 40, 40
                        
                    # 防重複重疊：檢查此位置是否已有極為靠近的方塊
                    duplicate = False
                    for b in self.editor_blocks:
                        if abs(b["x"] - grid_x) < 15 and abs(b["y"] - grid_y) < 15:
                            duplicate = True
                            break
                    if not duplicate:
                        self.editor_blocks.append({
                            "material": mat,
                            "x": grid_x,
                            "y": grid_y,
                            "width": w,
                            "height": h,
                            "shape_type": "rect"
                        })
                        sound_manager.play("wood_impact" if mat == "wood" else ("ice_impact" if mat == "ice" else "stone_impact"))
                        
                # 放置豬
                elif self.editor_selected_tool.startswith("pig"):
                    pig_t = self.editor_selected_tool.split("_")[1]
                    
                    duplicate = False
                    for p in self.editor_pigs:
                        if abs(p["x"] - grid_x) < 20 and abs(p["y"] - grid_y) < 20:
                            duplicate = True
                            break
                    if not duplicate:
                        self.editor_pigs.append({
                            "pig_type": pig_t,
                            "x": grid_x,
                            "y": grid_y
                        })
                        sound_manager.play("pig_pop")

        # 右鍵刪除點擊處的物體
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
            # 遍歷檢查方塊是否被點擊
            for b in self.editor_blocks[:]:
                hw = b["width"] / 2
                hh = b["height"] / 2
                if b["x"] - hw <= world_mouse.x <= b["x"] + hw and b["y"] - hh <= world_mouse.y <= b["y"] + hh:
                    self.editor_blocks.remove(b)
                    sound_manager.play("wood_impact")
                    return
            # 遍歷檢查豬是否被點擊
            for p in self.editor_pigs[:]:
                radius = 15 if p["pig_type"] != "king" else 24
                dist = (Vector2(p["x"], p["y"]) - world_mouse).length()
                if dist < radius:
                    self.editor_pigs.remove(p)
                    sound_manager.play("pig_pop")
                    return

    def handle_game_over_events(self, event, mouse_pos):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # 勝利/失敗面板按鈕點擊
            # 1. 重新挑戰按鈕 (400 <= x <= 470, 360 <= y <= 410)
            # 2. 回關卡選擇按鈕 (490 <= x <= 560, 360 <= y <= 410)
            if 360 <= mouse_pos[1] <= 410:
                if 400 <= mouse_pos[0] <= 470:
                    sound_manager.play("launch")
                    self.load_game_level(self.current_level_idx)
                elif 490 <= mouse_pos[0] <= 560:
                    sound_manager.play("boost")
                    self.state = "LEVEL_SELECT"

    def update(self, dt):
        self.update_clouds(dt)
        if self.state == "GAMEPLAY":
            self.update_gameplay(dt)
        elif self.state == "EDITOR":
            # 編輯器支援鍵盤 A / D 左右平移視野
            keys = pygame.key.get_pressed()
            if keys[pygame.K_a] or keys[pygame.K_LEFT]:
                self.camera_offset.x = max(0.0, self.camera_offset.x - 400.0 * dt)
            if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
                self.camera_offset.x = min(700.0, self.camera_offset.x + 400.0 * dt)
        
        # 畫面震動衰減
        if self.shake_intensity > 0.1:
            self.shake_intensity *= 0.88 # 快速 decay

        # 更新字幕計時器並移除過期字幕
        for sub in self.subtitles[:]:
            sub["timer"] -= dt
            if sub["timer"] <= 0:
                self.subtitles.remove(sub)

    def update_gameplay(self, dt):
        # 1. 物理引擎更新一幀
        self.physics_world.update(dt)
        
        # 2. 處理物理碰撞回饋 (播放音效、生成碎片、累加得分)
        # 處理撞擊音效播放
        for snd in self.physics_world.impact_sounds:
            sound_manager.play(snd)
            
        # 處理傷害與破損事件
        for ev in self.physics_world.damage_events:
            body = ev["body"]
            is_destroyed = ev["destroyed"]
            pos = ev["pos"]
            
            # 方塊碎屑粒子
            if body.category == "block":
                self.particle_system.spawn_shards(pos.x, pos.y, body.material, count=4 if not is_destroyed else 10)
                
                # 損壞加分
                points = int(ev["damage"] * 5)
                points = max(10, min(1000, points))
                self.score += points
                
                if is_destroyed:
                    # 徹底損毀加高分
                    self.score += body.score_value
                    self.floating_texts.append(FloatingText(pos.x, pos.y, f"+{body.score_value}", color=(235, 150, 50)))
                    
            # 綠豬受損與 popped 處理
            elif body.category == "pig":
                if is_destroyed:
                    self.particle_system.spawn_shards(pos.x, pos.y, "pig", count=14)
                    self.particle_system.spawn_smoke(pos.x, pos.y, count=8, radius=15)
                    self.score += body.score_value
                    self.floating_texts.append(FloatingText(pos.x, pos.y, f"+{body.score_value}", color=(100, 255, 100), size=30))
                    self.shake_intensity = min(15.0, self.shake_intensity + 6.0) # Popped 震屏
                    sound_manager.play("pig_pop")
                else:
                    # 僅受傷：產生少量碎片與些許受傷加分，但不消除或播放 popped 音效
                    self.particle_system.spawn_shards(pos.x, pos.y, "pig", count=4)
                    points = int(ev["damage"] * 3)
                    points = max(10, min(150, points))
                    self.score += points
                
        # 3. 粒子系統與懸浮漂浮字更新
        self.particle_system.update(dt)
        for t in self.floating_texts[:]:
            t.update(dt)
            if t.life <= 0:
                self.floating_texts.remove(t)
                
        # 4. 偵測並更新空中的小鳥狀態
        for bird in self.birds_in_air[:]:
            # 給予歷史小鳥軌跡點繪製 (以時間定時存檔)
            ticks = pygame.time.get_ticks()
            if int(ticks / 50) % 2 == 0:
                if not bird.trail or (bird.trail[-1] - bird.pos).length() > 10.0:
                    bird.trail.append(Vector2(bird.pos.x, bird.pos.y))
                    if len(bird.trail) > 30:
                        bird.trail.pop(0)
                        
            # 判斷小鳥是否「幾乎停止運動」或已被銷毀 (例如爆炸鳥)
            is_stopped = False
            if getattr(bird, "is_destroyed", False):
                is_stopped = True
            # 運動太慢 (速度小於 8 像素/s)
            elif bird.vel.length_squared() < 64.0 and (ticks - bird.launch_time) > 1200:
                is_stopped = True
            # 發射時間超過 5 秒，強制停止以防物理抖動卡死
            elif (ticks - bird.launch_time) > 5000:
                is_stopped = True
            # 或者掉落到螢幕底部以下
            elif bird.pos.y > 510 or bird.pos.x > 1500 or bird.pos.x < -100:
                is_stopped = True
                
            if is_stopped:
                # 飛完消失，生成最後一抹塵煙
                self.particle_system.spawn_smoke(bird.pos.x, bird.pos.y, count=5, radius=10)
                self.physics_world.remove_body(bird)
                if bird in self.birds_in_air:
                    self.birds_in_air.remove(bird)
                
                # 只有當所有空中飛行的鳥都已停止消失時，才拉入下一隻鳥，防止分裂鳥觸發多次載入或提前消耗隊列
                if len(self.birds_in_air) == 0:
                    self.prepare_next_bird()

        # 5. 滑動相機鏡頭：緊密跟隨最前面的飛天小鳥
        if self.birds_in_air:
            # 追隨領先的鳥
            lead_bird = self.birds_in_air[0]
            self.camera_target_x = lead_bird.pos.x - 320.0
        else:
            # 滑動回彈弓原位
            self.camera_target_x = 0.0
            
        # 限制相機邊界，防止視野滑出關卡背景
        self.camera_target_x = max(0.0, min(640.0, self.camera_target_x))
        # 鏡頭緩動
        self.camera_offset.x += (self.camera_target_x - self.camera_offset.x) * 0.08

        # 6. 勝負終局狀態判定
        self.check_level_end_conditions()

    def prepare_next_bird(self):
        """將下一隻排隊的小鳥放到彈弓上"""
        # 從排隊隊列中移除已經發射或損毀的第一隻鳥
        if self.birds_queue:
            active_was = self.birds_queue[0]
            self.birds_queue.pop(0)
            
        if self.birds_queue:
            next_bird = self.birds_queue[0]
            # 緩動將其傳送到彈弓拉力點
            next_bird.pos = Vector2(150, 432)
            self.slingshot.active_bird = next_bird
        else:
            self.slingshot.active_bird = None

    def check_level_end_conditions(self):
        """判斷關卡是否通關或失敗"""
        # 計算活著的豬的數量
        pigs = [b for b in self.physics_world.bodies if b.category == "pig"]
        
        if len(pigs) == 0 and not self.level_completed:
            # 通關勝利！
            self.level_completed = True
            self.state_timer = pygame.time.get_ticks()
            sound_manager.play("victory")
            
            # 給予剩餘鳥加成高分！
            bonus = len(self.birds_queue) * 10000
            if self.slingshot.active_bird:
                # 彈弓上那一隻也算
                bonus += 10000
            self.score += bonus
            
            # 保存高分
            key = str(self.current_level_idx)
            if self.score > self.high_scores.get(key, 0):
                self.high_scores[key] = self.score
                self.write_save_data()
                
        elif len(pigs) > 0 and len(self.birds_queue) == 0 and len(self.birds_in_air) == 0 and not self.slingshot.active_bird:
            # 無鳥可用，且無在空小鳥，但還有豬存活 -> 失敗！
            if not self.level_failed:
                # 給予 2 秒的延遲判定期，好讓最後倒塌的方塊有可能壓死豬
                self.level_failed = True
                self.state_timer = pygame.time.get_ticks()
                
        # 判定時間到了切換狀態
        ticks = pygame.time.get_ticks()
        if self.level_completed and (ticks - self.state_timer) > 1500:
            self.state = "VICTORY"
        elif self.level_failed and (ticks - self.state_timer) > 2000:
            # 再次檢查是不是最後方塊塌陷砸死了豬！
            pigs_check = [b for b in self.physics_world.bodies if b.category == "pig"]
            if len(pigs_check) == 0:
                self.level_failed = False
                self.level_completed = True
                self.state = "VICTORY"
                # 加分與存檔
                bonus = 10000 # 剛好最後砸死
                self.score += bonus
                key = str(self.current_level_idx)
                if self.score > self.high_scores.get(key, 0):
                    self.high_scores[key] = self.score
                    self.write_save_data()
            else:
                self.state = "DEFEAT"
                sound_manager.play("defeat")

    def render(self):
        # 應用畫面震動位移
        render_offset = Vector2(self.camera_offset.x, self.camera_offset.y)
        if self.shake_intensity > 0.1:
            render_offset.x += random.uniform(-self.shake_intensity, self.shake_intensity)
            render_offset.y += random.uniform(-self.shake_intensity, self.shake_intensity)
            
        # 依狀態進行繪製
        if self.state == "MENU":
            self.render_menu()
        elif self.state == "LEVEL_SELECT":
            self.render_level_select()
        elif self.state == "GAMEPLAY":
            self.render_gameplay(render_offset)
        elif self.state == "EDITOR":
            self.render_editor()
        elif self.state in ("VICTORY", "DEFEAT"):
            self.render_gameplay(render_offset)
            self.render_game_over()
            
        # 繪製音效字幕
        self.render_subtitles()
            
        pygame.display.flip()

    def render_menu(self):
        """渲染主選單界面"""
        # 繪製漸層天空 (內含太陽光暈)
        sky = assets.get_texture("sky", SCREEN_WIDTH, SCREEN_HEIGHT)
        self.screen.blit(sky, (0, 0))
        
        # 繪製動態白雲
        for cloud in self.clouds:
            cloud_surf = assets.get_texture("cloud", cloud["w"], cloud["h"])
            self.screen.blit(cloud_surf, (int(cloud["x"]), int(cloud["y"])))
        
        # 繪製背景山丘 (靜止)
        hill_far = assets.get_texture("hill", SCREEN_WIDTH, SCREEN_HEIGHT, "far")
        hill_mid = assets.get_texture("hill", SCREEN_WIDTH, SCREEN_HEIGHT, "mid")
        hill_near = assets.get_texture("hill", SCREEN_WIDTH, SCREEN_HEIGHT, "near")
        
        self.screen.blit(hill_far, (0, 0))
        self.screen.blit(hill_mid, (0, 0))
        self.screen.blit(hill_near, (0, 0))
        
        # 繪製主標題 "ANGRY BIRDS" (逐字動態漸層描邊波浪特效)
        title_font = pygame.font.SysFont("Comic Sans MS", 68, bold=True)
        title_text = "ANGRY BIRDS"
        
        # 用 title_font.size 獲取字元大小以精確置中
        char_widths = [title_font.size(c)[0] for c in title_text]
        total_width = sum(char_widths) + 4 * (len(title_text) - 1)
        
        start_x = SCREEN_WIDTH // 2 - total_width // 2
        start_y = 75
        ticks = pygame.time.get_ticks()
        
        current_x = start_x
        for i, char in enumerate(title_text):
            if char == " ":
                current_x += 20
                continue
                
            # 每個字母相位延遲不同，形成起伏波浪
            y_wave = math.sin(ticks * 0.005 + i * 0.6) * 7
            
            # 描邊特效：在八個方向偏置 3 像素渲染黑色文字輪廓
            char_shadow = title_font.render(char, True, (20, 20, 20))
            for dx in (-3, 0, 3):
                for dy in (-3, 0, 3):
                    if dx != 0 or dy != 0:
                        self.screen.blit(char_shadow, (current_x + dx, start_y + y_wave + dy))
            
            # 奇偶字母交替顏色 (橙色與金黃)
            char_color = (255, 127, 80) if i % 2 == 0 else (255, 215, 0)
            char_surf = title_font.render(char, True, char_color)
            self.screen.blit(char_surf, (current_x, start_y + y_wave))
            
            current_x += char_widths[i] + 4
        
        # 繪製按鈕，添加滑鼠懸停脈衝與 3D 卡通效果
        mouse_pos = pygame.mouse.get_pos()
        btn_font = pygame.font.SysFont(CHINESE_FONTS, 20, bold=True)
        
        # "開始遊戲" 按鈕
        btn_w, btn_h = 220, 56
        btn_x = SCREEN_WIDTH // 2 - btn_w // 2 # 370
        btn_y = 270
        
        btn_rect_detect = pygame.Rect(btn_x, btn_y, btn_w, btn_h)
        btn1_hover = btn_rect_detect.collidepoint(mouse_pos)
        
        # 懸停放大效果
        if btn1_hover:
            scale_w = int(btn_w * 1.06)
            scale_h = int(btn_h * 1.06)
            draw_x = SCREEN_WIDTH // 2 - scale_w // 2
            draw_y = btn_y - (scale_h - btn_h) // 2
        else:
            scale_w = btn_w
            scale_h = btn_h
            draw_x = btn_x
            draw_y = btn_y
            
        btn_draw_rect = pygame.Rect(draw_x, draw_y, scale_w, scale_h)
        
        # 繪製懸停時的脈動發光外圈
        if btn1_hover:
            glow_offset = 3 + int(math.sin(ticks * 0.012) * 3)
            glow_rect = btn_draw_rect.inflate(glow_offset * 2, glow_offset * 2)
            glow_surf = pygame.Surface((glow_rect.width, glow_rect.height), pygame.SRCALPHA)
            pygame.draw.rect(glow_surf, (255, 230, 0, 90), (0, 0, glow_rect.width, glow_rect.height), border_radius=15)
            self.screen.blit(glow_surf, glow_rect.topleft)
            
        # 繪製 3D 陰影厚度底層
        thick_offset = 6
        shadow_rect = pygame.Rect(btn_draw_rect.x, btn_draw_rect.y + thick_offset, btn_draw_rect.width, btn_draw_rect.height)
        pygame.draw.rect(self.screen, (211, 84, 0), shadow_rect, border_radius=12) # 深橙色底座
        
        # 繪製按鈕主體
        btn_color = (255, 99, 71) if btn1_hover else (255, 127, 80)
        pygame.draw.rect(self.screen, btn_color, btn_draw_rect, border_radius=12)
        pygame.draw.rect(self.screen, (255, 255, 255), btn_draw_rect, 2, border_radius=12) # 白色內邊框
        
        btn1_text = btn_font.render("開始遊戲", True, (255, 255, 255))
        self.screen.blit(btn1_text, (btn_draw_rect.centerx - btn1_text.get_width()//2, btn_draw_rect.centery - btn1_text.get_height()//2))

        # 頁腳版權
        foot_font = pygame.font.SysFont("Arial", 12)
        foot_surf = foot_font.render("Antigravity AI Pair Programming Project 2026", True, (44, 62, 80))
        self.screen.blit(foot_surf, (SCREEN_WIDTH//2 - foot_surf.get_width()//2, SCREEN_HEIGHT - 30))

    def render_level_select(self):
        """渲染關卡選擇界面"""
        # 繪製漸層天空 (內含太陽光暈)
        sky = assets.get_texture("sky", SCREEN_WIDTH, SCREEN_HEIGHT)
        self.screen.blit(sky, (0, 0))
        
        # 繪製動態白雲
        for cloud in self.clouds:
            cloud_surf = assets.get_texture("cloud", cloud["w"], cloud["h"])
            self.screen.blit(cloud_surf, (int(cloud["x"]), int(cloud["y"])))
            
        # 繪製背景山丘
        hill_far = assets.get_texture("hill", SCREEN_WIDTH, SCREEN_HEIGHT, "far")
        hill_mid = assets.get_texture("hill", SCREEN_WIDTH, SCREEN_HEIGHT, "mid")
        hill_near = assets.get_texture("hill", SCREEN_WIDTH, SCREEN_HEIGHT, "near")
        self.screen.blit(hill_far, (0, 0))
        self.screen.blit(hill_mid, (0, 0))
        self.screen.blit(hill_near, (0, 0))
        
        # 大標題
        title_font = pygame.font.SysFont(CHINESE_FONTS, 36, bold=True)
        title_surf = title_font.render("選擇關卡", True, (44, 62, 80))
        title_shadow = title_font.render("選擇關卡", True, (255, 255, 255))
        self.screen.blit(title_shadow, (SCREEN_WIDTH//2 - title_surf.get_width()//2 + 2, 62))
        self.screen.blit(title_surf, (SCREEN_WIDTH//2 - title_surf.get_width()//2, 60))
        
        mouse_pos = pygame.mouse.get_pos()
        level_font = pygame.font.SysFont(CHINESE_FONTS, 18, bold=True)
        
        # 關卡卡片定義，加入代表小鳥與尺寸
        levels_box = [
            {"idx": 0, "name": "關卡 1\n新手訓練", "rect": pygame.Rect(150, 200, 160, 110), "color": (95, 226, 156), "bird": "bird_red", "bird_size": 46},
            {"idx": 1, "name": "關卡 2\n復合城堡", "rect": pygame.Rect(400, 200, 160, 110), "color": (255, 204, 120), "bird": "bird_yellow", "bird_size": 46},
            {"idx": 2, "name": "關卡 3\n國王石城", "rect": pygame.Rect(650, 200, 160, 110), "color": (200, 160, 240), "bird": "bird_bomb", "bird_size": 48},
        ]
        
        for lvl in levels_box:
            hover = lvl["rect"].collidepoint(mouse_pos)
            
            # 卡片顏色與 3D 厚度陰影色
            base_color = lvl["color"]
            shadow_color = [max(0, c - 45) for c in base_color]
            
            # 懸停放大 5%
            if hover:
                rect = lvl["rect"].inflate(10, 10)
                draw_color = base_color
            else:
                rect = lvl["rect"]
                draw_color = [max(0, c - 10) for c in base_color]
                
            # 1. 繪製 3D 陰影底層
            thick = 6
            pygame.draw.rect(self.screen, shadow_color, (rect.x, rect.y + thick, rect.width, rect.height), border_radius=14)
            # 2. 繪製卡片主體
            pygame.draw.rect(self.screen, draw_color, rect, border_radius=14)
            pygame.draw.rect(self.screen, (255, 255, 255), rect, 3 if hover else 1, border_radius=14)
            
            # 3. 渲染深色標題文字以增強對比度
            lines = lvl["name"].split("\n")
            for i, line in enumerate(lines):
                txt_surf = level_font.render(line, True, (44, 62, 80))
                self.screen.blit(txt_surf, (rect.centerx - txt_surf.get_width()//2, rect.top + 18 + i * 24))
                
            # 4. 顯示該關卡的高分紀錄與星級評分 (深色字)
            score = self.high_scores.get(str(lvl["idx"]), 0)
            score_font = pygame.font.SysFont("Arial", 12, bold=True)
            score_surf = score_font.render(f"High Score: {score}", True, (44, 62, 80))
            self.screen.blit(score_surf, (rect.centerx - score_surf.get_width()//2, rect.bottom - 22))
            
            # 5. 繪製代表小鳥頭像於右下角
            bird_tex = assets.get_texture(lvl["bird"], lvl["bird_size"])
            bird_surf = bird_tex.copy()
            
            # 懸停時小鳥產生呼吸跳動動畫
            if hover:
                ticks = pygame.time.get_ticks()
                bird_y_offset = math.sin(ticks * 0.015) * 4
            else:
                bird_y_offset = 0
                bird_surf.set_alpha(160) # 未選中時半透明，降低視覺雜訊
                
            bird_x = rect.right - lvl["bird_size"] + 6
            bird_y = rect.bottom - lvl["bird_size"] + 4 + int(bird_y_offset)
            self.screen.blit(bird_surf, (bird_x, bird_y))

        # 返回按鈕說明
        back_font = pygame.font.SysFont(CHINESE_FONTS, 14, bold=True)
        back_surf = back_font.render("按 ESC 鍵返回主選單", True, (80, 85, 90))
        self.screen.blit(back_surf, (15, 15))

    def render_gameplay(self, offset):
        """渲染核心遊戲畫面 (含物理世界、特效、皮筋與 HUD)"""
        # 1. 繪製漸層天空 (靜止)
        sky = assets.get_texture("sky", SCREEN_WIDTH, SCREEN_HEIGHT)
        self.screen.blit(sky, (0, 0))
        
        # 繪製動態白雲 (帶微弱視差)
        for cloud in self.clouds:
            cloud_surf = assets.get_texture("cloud", cloud["w"], cloud["h"])
            self.screen.blit(cloud_surf, (int(cloud["x"] - offset.x * 0.05), int(cloud["y"])))
        
        # 2. 視差背景滾動層 (多層 hills)
        # 背景山：移動極慢
        hill_far = assets.get_texture("hill", 1600, SCREEN_HEIGHT, "far")
        self.screen.blit(hill_far, (-offset.x * 0.1, 0))
        
        # 中景山：移動中速
        hill_mid = assets.get_texture("hill", 1600, SCREEN_HEIGHT, "mid")
        self.screen.blit(hill_mid, (-offset.x * 0.35, 0))
        
        # 近景山丘與物理世界地面：同步移動
        hill_near = assets.get_texture("hill", 1600, SCREEN_HEIGHT, "near")
        self.screen.blit(hill_near, (-offset.x, 0))

        # 3. 繪製排隊小鳥的淡灰色歷程歷史軌跡
        for bird in self.birds_in_air:
            for pt in bird.trail:
                pygame.draw.circle(self.screen, (220, 220, 220), (int(pt.x - offset.x), int(pt.y - offset.y)), 3)

        # 4. 繪製預測發射軌跡點 (如果在拖拽中)
        self.slingshot.draw_dots(self.screen, offset, self.physics_world.gravity.y)

        # 5. 繪製彈弓拉力皮筋後側
        self.slingshot.draw_back(self.screen, offset)

        # 6. 繪製物理引擎世界中所有剛體物體
        for body in self.physics_world.bodies:
            if body.is_destroyed:
                continue
                
            # 判斷分類渲染
            if body.category == "bird":
                body.draw(self.screen, offset)
            elif body.category == "block":
                # 方塊紋理
                w, h = int(body.width), int(body.height)
                tex = assets.get_texture("block", w, h, body.material)
                
                # 基於生命值比例繪製破碎裂縫 (用黑色畫一些裂痕)
                surf_copy = tex.copy()
                health_ratio = body.health / body.max_health
                if health_ratio < 0.7:
                    # 畫裂縫條數隨生命下降增加
                    num_cracks = 1 if health_ratio > 0.4 else 3
                    random.seed(int(body.pos.x + body.pos.y))
                    for _ in range(num_cracks):
                        cx1, cy1 = random.randint(3, w-3), random.randint(3, h-3)
                        cx2, cy2 = cx1 + random.randint(-15, 15), cy1 + random.randint(-15, 15)
                        cx2 = max(3, min(w-3, cx2))
                        cy2 = max(3, min(h-3, cy2))
                        pygame.draw.line(surf_copy, (40, 30, 20), (cx1, cy1), (cx2, cy2), 1 if health_ratio > 0.4 else 2)
                        
                draw_pos = (body.pos.x - w//2 - offset.x, body.pos.y - h//2 - offset.y)
                self.screen.blit(surf_copy, draw_pos)
                
            elif body.category == "pig":
                # 根據生命值比例選擇綠豬貼圖 (被打慘時頭盔/皇冠會飛走)
                diameter = int(body.radius * 2)
                health_ratio = body.health / body.max_health
                
                if body.pig_type == "helmet" and health_ratio < 0.4:
                    # 頭盔被打飛了！使用普通綠豬作為底圖
                    tex = assets.get_texture("pig_minion", diameter, diameter)
                elif body.pig_type == "king" and health_ratio < 0.4:
                    # 皇冠被震掉了！使用普通綠豬作為底圖
                    tex = assets.get_texture("pig_minion", diameter, diameter)
                else:
                    tex_name = f"pig_{body.pig_type}"
                    tex = assets.get_texture(tex_name, diameter, diameter)
                
                surf_copy = tex.copy()
                r = body.radius
                
                # 依受傷程度動態繪製青腫瘀青、叉叉眼與繃帶
                if health_ratio < 0.7:
                    eye_y = int(r - 4)
                    if health_ratio >= 0.4:
                        # 階段一：輕度受傷 (單眼黑青，嘴角微歪)
                        bruise = pygame.Surface((10, 10), pygame.SRCALPHA)
                        pygame.draw.circle(bruise, (100, 120, 220, 110), (5, 5), 5)
                        surf_copy.blit(bruise, (int(r - 10), eye_y - 4))
                        # 嘴角歪斜 (覆蓋原有的開心微笑)
                        pygame.draw.rect(surf_copy, (46, 204, 113), (int(r - 6), int(r + 3), 12, 5))
                        pygame.draw.line(surf_copy, (20, 90, 50), (int(r - 5), int(r + 5)), (int(r + 5), int(r + 3)), 2)
                    else:
                        # 階段二：重度受傷 (雙眼黑青 + 叉叉眼 + 哭哭嘴 + 額頭繃帶)
                        bruise = pygame.Surface((10, 10), pygame.SRCALPHA)
                        pygame.draw.circle(bruise, (80, 80, 180, 140), (5, 5), 5)
                        surf_copy.blit(bruise, (int(r - 10), eye_y - 4))
                        surf_copy.blit(bruise, (int(r + 1), eye_y - 4))
                        # 畫黑色的 X 形眼睛
                        pygame.draw.line(surf_copy, (0, 0, 0), (int(r - 9), eye_y - 2), (int(r - 3), eye_y + 2), 2)
                        pygame.draw.line(surf_copy, (0, 0, 0), (int(r - 3), eye_y - 2), (int(r - 9), eye_y + 2), 2)
                        pygame.draw.line(surf_copy, (0, 0, 0), (int(r + 3), eye_y - 2), (int(r + 9), eye_y + 2), 2)
                        pygame.draw.line(surf_copy, (0, 0, 0), (int(r + 9), eye_y - 2), (int(r + 3), eye_y + 2), 2)
                        # 嘴角沮喪下撇
                        pygame.draw.rect(surf_copy, (46, 204, 113), (int(r - 6), int(r + 3), 12, 6))
                        pygame.draw.arc(surf_copy, (20, 90, 50), (int(r - 6), int(r + 4), 12, 6), 0, math.pi, 2)
                        # 額頭交叉白色 OK 繃
                        pygame.draw.polygon(surf_copy, (244, 230, 180), [(r - 8, r - 12), (r + 8, r - 6), (r + 7, r - 3), (r - 9, r - 9)])
                        pygame.draw.polygon(surf_copy, (244, 230, 180), [(r - 8, r - 6), (r + 8, r - 12), (r + 9, r - 9), (r - 7, r - 3)])
                        
                draw_pos = (body.pos.x - body.radius - offset.x, body.pos.y - body.radius - offset.y)
                self.screen.blit(surf_copy, draw_pos)

        # 7. 繪製彈弓前側支架與前景皮筋
        self.slingshot.draw_slingshot(self.screen, offset)

        # 8. 繪製粒子特效
        self.particle_system.draw(self.screen, offset)

        # 9. 繪製懸浮得分字
        for t in self.floating_texts:
            t.draw(self.screen, offset)

        # 10. 渲染頂部 UI HUD
        hud_font = pygame.font.SysFont(CHINESE_FONTS, 18, bold=True)
        # 得分
        score_surf = hud_font.render(f"得分: {self.score}", True, (44, 62, 80))
        self.screen.blit(score_surf, (20, 20))
        # 關卡高分
        high_key = str(self.current_level_idx)
        best = max(self.score, self.high_scores.get(high_key, 0))
        best_surf = hud_font.render(f"最高紀錄: {best}", True, (44, 62, 80))
        self.screen.blit(best_surf, (20, 48))
        
        # 關卡名稱
        name_surf = hud_font.render(self.level_name, True, (230, 126, 34))
        self.screen.blit(name_surf, (SCREEN_WIDTH//2 - name_surf.get_width()//2, 20))
        
        # 重設小提示
        tip_font = pygame.font.SysFont(CHINESE_FONTS, 13)
        tip_surf = tip_font.render("按 R 重置關卡 | 按 ESC 返回", True, (100, 110, 120))
        self.screen.blit(tip_surf, (SCREEN_WIDTH - tip_surf.get_width() - 20, 20))

    def render_editor(self):
        """渲染自定義關卡編輯器界面"""
        sky = assets.get_texture("sky", SCREEN_WIDTH, SCREEN_HEIGHT)
        self.screen.blit(sky, (0, 0))
        
        # 繪製地面參考線 (y = 510)
        pygame.draw.line(self.screen, (231, 76, 60), (0, 510), (SCREEN_WIDTH, 510), 2)
        
        # 繪製已擺放的方塊
        for b in self.editor_blocks:
            w, h = b["width"], b["height"]
            tex = assets.get_texture("block", w, h, b["material"])
            self.screen.blit(tex, (b["x"] - w//2, b["y"] - h//2))
            
        # 繪製已擺放的豬
        for p in self.editor_pigs:
            diameter = 30 if p["pig_type"] != "king" else 48
            tex = assets.get_texture(f"pig_{p['pig_type']}", diameter, diameter)
            self.screen.blit(tex, (p["x"] - diameter//2, p["y"] - diameter//2))

        # 繪製左下側靜止彈弓，作為擺放參考
        slingshot_tex = assets.get_texture("slingshot", 36, 100)
        self.screen.blit(slingshot_tex, (150 - 18, 510 - 100))

        # 繪製頂部工具列
        pygame.draw.rect(self.screen, (44, 62, 80), (0, 0, SCREEN_WIDTH, 55))
        pygame.draw.line(self.screen, (52, 73, 94), (0, 55), (SCREEN_WIDTH, 55), 2)
        
        # 定義按鈕橫排
        btn_font = pygame.font.SysFont(CHINESE_FONTS, 12, bold=True)
        tools = [
            ("block_wood", "木箱", pygame.Rect(10, 10, 80, 35), (211, 137, 71)),
            ("block_ice", "冰箱", pygame.Rect(100, 10, 80, 35), (173, 232, 244)),
            ("block_stone", "石箱", pygame.Rect(190, 10, 80, 35), (149, 165, 166)),
            ("pig_minion", "普通綠豬", pygame.Rect(290, 10, 80, 35), (46, 204, 113)),
            ("pig_helmet", "頭盔綠豬", pygame.Rect(380, 10, 80, 35), (127, 140, 141)),
            ("pig_king", "國王巨豬", pygame.Rect(470, 10, 80, 35), (241, 196, 15)),
        ]
        
        # 繪製工具按鈕
        for tool_id, label, rect, color in tools:
            is_selected = (self.editor_selected_tool == tool_id)
            pygame.draw.rect(self.screen, color, rect, border_radius=6)
            pygame.draw.rect(self.screen, (255, 255, 255) if is_selected else (44, 62, 80), rect, 3 if is_selected else 1, border_radius=6)
            
            # 文字色
            txt_color = (0, 0, 0) if tool_id in ("block_ice", "pig_minion", "pig_king") else (255, 255, 255)
            txt_surf = btn_font.render(label, True, txt_color)
            self.screen.blit(txt_surf, (rect.centerx - txt_surf.get_width()//2, rect.centery - txt_surf.get_height()//2))

        # 特殊功能按鈕
        functions = [
            ("orient", f"方向:{self.editor_block_orientation}", pygame.Rect(570, 10, 80, 35), (155, 89, 182)),
            ("save", "保存關卡", pygame.Rect(680, 10, 80, 35), (46, 204, 113)),
            ("play", "測試遊玩", pygame.Rect(770, 10, 80, 35), (231, 76, 60)),
            ("clear", "清空", pygame.Rect(860, 10, 80, 35), (192, 57, 43)),
        ]
        
        for func_id, label, rect, color in functions:
            pygame.draw.rect(self.screen, color, rect, border_radius=6)
            pygame.draw.rect(self.screen, (255, 255, 255), rect, 1, border_radius=6)
            txt_surf = btn_font.render(label, True, (255, 255, 255))
            self.screen.blit(txt_surf, (rect.centerx - txt_surf.get_width()//2, rect.centery - txt_surf.get_height()//2))

        # 繪製滑鼠處的懸浮擺放预览輪廓
        m_pos = pygame.mouse.get_pos()
        if m_pos[1] > 55 and m_pos[0] > 300:
            grid_x = round(m_pos[0] / 10.0) * 10
            grid_y = round(m_pos[1] / 10.0) * 10
            
            if self.editor_selected_tool.startswith("block"):
                w, h = 20, 80
                if self.editor_block_orientation == "horizontal":
                    w, h = 80, 20
                elif self.editor_block_orientation == "square":
                    w, h = 40, 40
                # 畫虛線預覽矩形
                pygame.draw.rect(self.screen, (255, 255, 255), (grid_x - w//2, grid_y - h//2, w, h), 2)
            else:
                radius = 15 if self.editor_selected_tool != "pig_king" else 24
                pygame.draw.circle(self.screen, (255, 255, 255), (grid_x, grid_y), radius, 2)

        # 編輯提示
        tip_font = pygame.font.SysFont(CHINESE_FONTS, 12)
        tip_surf = tip_font.render("左鍵放置 | 右鍵刪除 | 按 ESC 返回主選單", True, (255, 255, 255))
        self.screen.blit(tip_surf, (20, SCREEN_HEIGHT - 22))

    def render_game_over(self):
        """渲染遊戲勝利/失敗覆蓋面板"""
        # 高質感半透明亮白背景層
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((255, 255, 255, 150))
        self.screen.blit(overlay, (0, 0))
        
        # 面板框 (400x260，置中)
        panel_rect = pygame.Rect(SCREEN_WIDTH//2 - 200, SCREEN_HEIGHT//2 - 130, 400, 260)
        pygame.draw.rect(self.screen, (248, 249, 250), panel_rect, border_radius=15)
        pygame.draw.rect(self.screen, (189, 195, 199), panel_rect, 3, border_radius=15)
        
        # 勝敗文字
        title_font = pygame.font.SysFont(CHINESE_FONTS, 36, bold=True)
        if self.state == "VICTORY":
            title_surf = title_font.render("關卡挑戰成功！", True, (230, 126, 34))
        else:
            title_surf = title_font.render("挑戰失敗...", True, (231, 76, 60))
            
        self.screen.blit(title_surf, (panel_rect.centerx - title_surf.get_width()//2, panel_rect.top + 30))
        
        # 分數資訊
        score_font = pygame.font.SysFont(CHINESE_FONTS, 20, bold=True)
        score_surf = score_font.render(f"最終得分: {self.score}", True, (44, 62, 80))
        self.screen.blit(score_surf, (panel_rect.centerx - score_surf.get_width()//2, panel_rect.top + 95))
        
        # 繪製星級評分 (3 顆大金星)
        # 勝利時，依分數劃分星級
        stars = 0
        if self.state == "VICTORY":
            if self.current_level_idx == 0:
                stars = 1 if self.score < 6000 else (2 if self.score < 12000 else 3)
            elif self.current_level_idx == 1:
                stars = 1 if self.score < 8000 else (2 if self.score < 16000 else 3)
            elif self.current_level_idx == 2:
                stars = 1 if self.score < 9000 else (2 if self.score < 15000 else 3)
            else: # custom
                stars = 3 # 自定義關卡一律滿星
                
        # 繪製星星圖標 (利用圓形與多邊形簡化或直接用字體符號，這裡繪製美麗的幾何五角星)
        star_font = pygame.font.SysFont("Arial", 40)
        star_x_start = panel_rect.centerx - 70
        for i in range(3):
            # 實心金黃色星星或空心亮灰星
            color = (241, 196, 15) if i < stars else (189, 195, 199)
            star_char = "★" if i < stars else "☆"
            star_surf = pygame.font.SysFont(CHINESE_FONTS, 42).render(star_char, True, color)
            self.screen.blit(star_surf, (star_x_start + i * 50 - 10, panel_rect.top + 135))

        # 按鈕：重新挑戰與回關卡選擇 (圓形小按鈕圖標)
        mouse_pos = pygame.mouse.get_pos()
        btn_font = pygame.font.SysFont(CHINESE_FONTS, 12, bold=True)
        
        # 重新挑戰
        btn1_hover = (400 <= mouse_pos[0] <= 470 and 360 <= mouse_pos[1] <= 410)
        btn1_color = (46, 204, 113) if btn1_hover else (39, 174, 96)
        btn1_rect = pygame.Rect(400, 360, 70, 40)
        pygame.draw.rect(self.screen, btn1_color, btn1_rect, border_radius=8)
        pygame.draw.rect(self.screen, (255, 255, 255), btn1_rect, 1, border_radius=8)
        btn1_text = btn_font.render("重新挑戰", True, (255, 255, 255))
        self.screen.blit(btn1_text, (btn1_rect.centerx - btn1_text.get_width()//2, btn1_rect.centery - btn1_text.get_height()//2))
        
        # 回選單
        btn2_hover = (490 <= mouse_pos[0] <= 560 and 360 <= mouse_pos[1] <= 410)
        btn2_color = (52, 152, 219) if btn2_hover else (41, 128, 185)
        btn2_rect = pygame.Rect(490, 360, 70, 40)
        pygame.draw.rect(self.screen, btn2_color, btn2_rect, border_radius=8)
        pygame.draw.rect(self.screen, (255, 255, 255), btn2_rect, 1, border_radius=8)
        btn2_text = btn_font.render("選擇關卡", True, (255, 255, 255))
        self.screen.blit(btn2_text, (btn2_rect.centerx - btn2_text.get_width()//2, btn2_rect.centery - btn2_text.get_height()//2))

    def on_sound_played(self, sound_name):
        """當音效播放時，新增對應的字幕"""
        subtitle_map = {
            "launch": "【發射小鳥！】",
            "boost": "【小鳥技能加速！】",
            "wood_impact": "【碰撞木頭】",
            "ice_impact": "【碰撞冰塊】",
            "stone_impact": "【碰撞石頭】",
            "pig_pop": "【綠豬被消滅！】",
            "explosion": "【大爆炸！！！】",
            "victory": "【關卡挑戰成功！】",
            "defeat": "【挑戰失敗...】"
        }
        text = subtitle_map.get(sound_name)
        if text:
            # 避免在極短時間內重複堆疊完全相同的字幕
            for sub in self.subtitles:
                if sub["text"] == text and sub["timer"] > 1.0:
                    sub["timer"] = 1.5
                    return
            self.subtitles.append({"text": text, "timer": 1.5})
            if len(self.subtitles) > 3:  # 最多顯示 3 行字幕
                self.subtitles.pop(0)

    def render_subtitles(self):
        """在畫面底部中央渲染音效字幕"""
        if not self.subtitles:
            return
            
        font = pygame.font.SysFont(CHINESE_FONTS, 18, bold=True)
        y_offset = SCREEN_HEIGHT - 70 - (len(self.subtitles) - 1) * 26
        
        for sub in self.subtitles:
            text_surf = font.render(sub["text"], True, (255, 255, 255))
            
            # 加上半透明背景黑色飾板以利閱讀
            bg_width = text_surf.get_width() + 24
            bg_height = text_surf.get_height() + 10
            bg_rect = pygame.Rect(0, 0, bg_width, bg_height)
            bg_rect.center = (SCREEN_WIDTH // 2, y_offset)
            
            # 計算淡出透明度
            alpha = 255
            if sub["timer"] < 0.3:
                alpha = int(255 * (sub["timer"] / 0.3))
                
            # 繪製半透明背景板
            bg_surf = pygame.Surface((bg_width, bg_height), pygame.SRCALPHA)
            bg_surf.fill((0, 0, 0, int(160 * (alpha / 255.0))))
            self.screen.blit(bg_surf, bg_rect.topleft)
            
            # 繪製文字 (套用透明度)
            text_alpha_surf = pygame.Surface((text_surf.get_width(), text_surf.get_height()), pygame.SRCALPHA)
            text_alpha_surf.fill((255, 255, 255, alpha))
            text_surf.blit(text_alpha_surf, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            
            self.screen.blit(text_surf, (bg_rect.centerx - text_surf.get_width() // 2, bg_rect.centery - text_surf.get_height() // 2))
            y_offset += 26

if __name__ == "__main__":
    game = GameCoordinator()
    game.run()

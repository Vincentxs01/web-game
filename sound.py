import os
import wave
import struct
import math
import random

# 音效合成設定
SAMPLE_RATE = 44100
SOUND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".sounds")


def save_wav(filename, samples):
    """將樣本列表保存為 16-bit 單聲道 WAV 檔案"""
    os.makedirs(SOUND_DIR, exist_ok=True)
    filepath = os.path.join(SOUND_DIR, filename)
    with wave.open(filepath, 'wb') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2) # 16-bit PCM
        wav_file.setframerate(SAMPLE_RATE)
        for s in samples:
            # 限制在 -1.0 到 1.0 之間
            s = max(-1.0, min(1.0, s))
            val = int(s * 32767.0)
            data = struct.pack('<h', val)
            wav_file.writeframesraw(data)

def get_low_pass_noise(num_samples, alpha=0.15):
    """一階低通濾波器：y[n] = alpha * x[n] + (1 - alpha) * y[n-1]
    用於濾除白噪音的高頻沙沙聲，產生厚重低沉的撞擊/爆炸聲
    """
    samples = []
    prev = 0.0
    # 補償因濾波造成的振幅衰減，使音量水平與白噪音相當
    scale = math.sqrt((2.0 - alpha) / alpha) if alpha > 0 else 1.0
    for _ in range(num_samples):
        white = random.uniform(-1.0, 1.0)
        filtered = alpha * white + (1.0 - alpha) * prev
        prev = filtered
        samples.append(filtered * scale)
    return samples

def generate_launch():
    """發射聲音：頻率由低到高掃描"""
    duration = 0.25
    num_samples = int(SAMPLE_RATE * duration)
    samples = []
    f1, f2 = 250.0, 750.0
    for i in range(num_samples):
        t = i / SAMPLE_RATE
        # 線性頻率掃描的相位積分公式
        phase = 2.0 * math.pi * (f1 * t + (f2 - f1) * (t ** 2) / (2.0 * duration))
        # 漸變包絡線避免爆音
        envelope = math.sin(math.pi * t / duration)
        samples.append(math.sin(phase) * envelope * 0.5)
    save_wav("launch.wav", samples)

def generate_boost():
    """加速聲音：快速的高頻衝刺"""
    duration = 0.18
    num_samples = int(SAMPLE_RATE * duration)
    samples = []
    f1, f2 = 450.0, 1350.0
    for i in range(num_samples):
        t = i / SAMPLE_RATE
        phase = 2.0 * math.pi * (f1 * t + (f2 - f1) * (t ** 2) / (2.0 * duration))
        # 指數衰減包絡
        envelope = math.exp(-3.0 * t / duration) * math.sin(math.pi * t / duration)
        samples.append(math.sin(phase) * envelope * 0.6)
    save_wav("boost.wav", samples)

def generate_wood_impact():
    """木頭撞擊：低頻重擊混入低通濾波噪音"""
    duration = 0.15
    num_samples = int(SAMPLE_RATE * duration)
    samples = []
    f1, f2 = 180.0, 60.0
    # 木頭撞擊需要沉悶的聲效，使用 alpha=0.10
    noise_samples = get_low_pass_noise(num_samples, alpha=0.10)
    for i in range(num_samples):
        t = i / SAMPLE_RATE
        phase = 2.0 * math.pi * (f1 * t + (f2 - f1) * (t ** 2) / (2.0 * duration))
        sine_val = math.sin(phase)
        noise_val = noise_samples[i]
        # 混音：80% 正弦波 + 20% 噪音
        mixed = 0.8 * sine_val + 0.2 * noise_val
        envelope = math.exp(-8.0 * t)
        samples.append(mixed * envelope * 0.7)
    save_wav("wood_impact.wav", samples)

def generate_ice_impact():
    """冰塊撞擊：高頻清脆鈴聲，極快衰減"""
    duration = 0.08
    num_samples = int(SAMPLE_RATE * duration)
    samples = []
    f1, f2 = 1800.0, 1200.0
    for i in range(num_samples):
        t = i / SAMPLE_RATE
        phase = 2.0 * math.pi * (f1 * t + (f2 - f1) * (t ** 2) / (2.0 * duration))
        sine_val = math.sin(phase)
        # 加入一點高頻諧波使聲音更清脆
        harm = math.sin(2.0 * phase) * 0.3
        envelope = math.exp(-25.0 * t)
        samples.append((sine_val + harm) * envelope * 0.5)
    save_wav("ice_impact.wav", samples)

def generate_stone_impact():
    """石頭撞擊：更沉重的低頻轟鳴，伴隨低頻噪音"""
    duration = 0.25
    num_samples = int(SAMPLE_RATE * duration)
    samples = []
    f1, f2 = 100.0, 45.0
    # 石頭碰撞極其沉悶，使用 alpha=0.08
    noise_samples = get_low_pass_noise(num_samples, alpha=0.08)
    for i in range(num_samples):
        t = i / SAMPLE_RATE
        phase = 2.0 * math.pi * (f1 * t + (f2 - f1) * (t ** 2) / (2.0 * duration))
        sine_val = math.sin(phase)
        noise_val = noise_samples[i]
        mixed = 0.7 * sine_val + 0.3 * noise_val
        envelope = math.exp(-12.0 * t)
        samples.append(mixed * envelope * 0.8)
    save_wav("stone_impact.wav", samples)

def generate_pig_pop():
    """綠豬消滅：氣泡破裂聲"""
    duration = 0.15
    num_samples = int(SAMPLE_RATE * duration)
    samples = []
    # 頻率快速上揚後微降
    for i in range(num_samples):
        t = i / SAMPLE_RATE
        f = 350.0 + 450.0 * math.sin(math.pi * t / duration)
        phase = 2.0 * math.pi * f * t
        envelope = math.sin(math.pi * t / duration) * math.exp(-2.0 * t)
        samples.append(math.sin(phase) * envelope * 0.6)
    save_wav("pig_pop.wav", samples)

def generate_explosion():
    """炸彈爆炸：猛烈的低通噪音爆炸，伴隨低音餘震"""
    duration = 0.6
    num_samples = int(SAMPLE_RATE * duration)
    samples = []
    # 爆炸需要一定的猛烈感，使用 alpha=0.20
    noise_samples = get_low_pass_noise(num_samples, alpha=0.20)
    for i in range(num_samples):
        t = i / SAMPLE_RATE
        # 低音餘震
        rumble = math.sin(2.0 * math.pi * 50.0 * t) * 0.5
        # 低通濾波噪音
        noise_val = noise_samples[i]
        # 混音與指數衰減
        mixed = 0.3 * rumble + 0.7 * noise_val
        envelope = math.exp(-7.0 * t)
        samples.append(mixed * envelope * 0.9)
    save_wav("explosion.wav", samples)

def generate_victory():
    """勝利音效：歡樂的 C 大調琶音"""
    # 琶音音符：C5(523Hz), E5(659Hz), G5(784Hz), C6(1046Hz)
    notes = [523.25, 659.25, 784.00, 1046.50]
    note_duration = 0.12
    samples = []
    for note_f in notes:
        num_samples = int(SAMPLE_RATE * note_duration)
        for i in range(num_samples):
            t = i / SAMPLE_RATE
            phase = 2.0 * math.pi * note_f * t
            envelope = math.sin(math.pi * t / note_duration) * 0.4
            samples.append(math.sin(phase) * envelope)
    # 最後一個音符拉長衰減
    num_samples = int(SAMPLE_RATE * 0.3)
    for i in range(num_samples):
        t = i / SAMPLE_RATE
        phase = 2.0 * math.pi * notes[-1] * t
        envelope = math.exp(-5.0 * t) * 0.4
        samples.append(math.sin(phase) * envelope)
    save_wav("victory.wav", samples)

def generate_defeat():
    """失敗音效：悲傷的降音程"""
    # 音符：G4(392Hz), Eb4(311Hz), C4(262Hz)
    notes = [392.00, 311.13, 261.63]
    note_duration = 0.2
    samples = []
    for note_f in notes:
        num_samples = int(SAMPLE_RATE * note_duration)
        for i in range(num_samples):
            t = i / SAMPLE_RATE
            phase = 2.0 * math.pi * note_f * t
            envelope = math.sin(math.pi * t / note_duration) * 0.4
            samples.append(math.sin(phase) * envelope)
    # 最後一個音拉長
    num_samples = int(SAMPLE_RATE * 0.4)
    for i in range(num_samples):
        t = i / SAMPLE_RATE
        phase = 2.0 * math.pi * notes[-1] * t
        envelope = math.exp(-3.0 * t) * 0.4
        samples.append(math.sin(phase) * envelope)
    save_wav("defeat.wav", samples)

def generate_bgm():
    """生成一個 6 秒長度的 8-bit 風格背景音樂 (BGM)"""
    duration = 6.0
    num_samples = int(SAMPLE_RATE * duration)
    samples = [0.0] * num_samples
    
    # 1. 伴奏和弦 (C - G - Am - F)
    # 每個和弦 1.5 秒
    chords = [
        # C (C3, E3, G3)
        [130.81, 164.81, 196.00],
        # G (G2, B2, D3)
        [98.00, 123.47, 146.83],
        # Am (A2, C3, E3)
        [110.00, 130.81, 164.81],
        # F (F2, A2, C3)
        [87.31, 110.00, 130.81]
    ]
    
    # 2. 主旋律音符 (每 0.25 秒一個音符，共 24 個音符)
    melody = [
        # C5, E5, G5, C6, G5, E5 (C 和弦期間)
        523.25, 659.25, 783.99, 1046.50, 783.99, 659.25,
        # B4, D5, G5, B5, G5, D5 (G 和弦期間)
        493.88, 587.33, 783.99, 987.77, 783.99, 587.33,
        # A4, C5, E5, A5, E5, C5 (Am 和弦期間)
        440.00, 523.25, 659.25, 880.00, 659.25, 523.25,
        # F4, A4, C5, F5, C5, A4 (F 和弦期間)
        349.23, 440.00, 523.25, 698.46, 523.25, 440.00
    ]
    
    note_duration = 0.25
    
    # 合成伴奏音軌
    for chord_idx, chord_freqs in enumerate(chords):
        start_time = chord_idx * 1.5
        end_time = start_time + 1.5
        start_sample = int(start_time * SAMPLE_RATE)
        end_sample = int(end_time * SAMPLE_RATE)
        
        for i in range(start_sample, end_sample):
            t = i / SAMPLE_RATE
            val = 0.0
            for freq in chord_freqs:
                # 使用軟和弦 (正弦波，低音量)
                val += math.sin(2.0 * math.pi * freq * t)
            # 稍微平滑地淡入淡出每個和弦以防爆音
            chord_t = t - start_time
            envelope = 1.0
            if chord_t < 0.1:
                envelope = chord_t / 0.1
            elif chord_t > 1.4:
                envelope = (1.5 - chord_t) / 0.1
            
            samples[i] += (val / len(chord_freqs)) * 0.12 * envelope
            
    # 合成旋律音軌
    for note_idx, freq in enumerate(melody):
        start_time = note_idx * note_duration
        end_time = start_time + note_duration
        start_sample = int(start_time * SAMPLE_RATE)
        end_sample = int(end_time * SAMPLE_RATE)
        
        for i in range(start_sample, end_sample):
            t = i / SAMPLE_RATE
            # 使用乾淨的正弦波
            val = math.sin(2.0 * math.pi * freq * t)
            
            # 旋律的包絡線：快速彈起並指數衰減 (Pluck 效果)
            note_t = t - start_time
            envelope = math.exp(-6.0 * note_t) * math.sin(math.pi * note_t / note_duration)
            
            samples[i] += val * 0.15 * envelope
            
    save_wav("bgm.wav", samples)

def build_all_sounds(force=True):
    """生成所有音效。若 force=True，則一律重新生成以覆蓋舊版"""
    os.makedirs(SOUND_DIR, exist_ok=True)
    sounds = {
        "launch.wav": generate_launch,
        "boost.wav": generate_boost,
        "wood_impact.wav": generate_wood_impact,
        "ice_impact.wav": generate_ice_impact,
        "stone_impact.wav": generate_stone_impact,
        "pig_pop.wav": generate_pig_pop,
        "explosion.wav": generate_explosion,
        "victory.wav": generate_victory,
        "defeat.wav": generate_defeat,
        "bgm.wav": generate_bgm,
    }
    for filename, generator in sounds.items():
        filepath = os.path.join(SOUND_DIR, filename)
        if force or not os.path.exists(filepath):
            print(f"程序化生成音效：{filename}...")
            generator()

# 自動構建（如果有缺失則重建）
build_all_sounds(force=False)

# 用於載入 Pygame 音效的管理器
class SoundManager:
    def __init__(self):
        self.sounds = {}
        self.enabled = True
        self.subtitle_callback = None
        self.last_played = {}  # 記錄每個音效上一次播放的毫秒數，用於限流
        
    def init_sounds(self):
        """初始化 Pygame 混音器並加載音效"""
        import pygame
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=SAMPLE_RATE, size=-16, channels=1, buffer=512)
            
            sound_files = [
                "launch", "boost", "wood_impact", "ice_impact", 
                "stone_impact", "pig_pop", "explosion", "victory", "defeat"
            ]
            for name in sound_files:
                path = os.path.join(SOUND_DIR, f"{name}.wav")
                if os.path.exists(path):
                    self.sounds[name] = pygame.mixer.Sound(path)
        except Exception as e:
            print(f"音效初始化失敗（可能缺少音訊設備）：{e}")
            self.enabled = False

    def play(self, name):
        """播放音效，加入物理碰撞音效冷卻限流以防止雜音堆疊"""
        if self.enabled and name in self.sounds:
            import pygame
            # 針對 "impact" 材質撞擊音效進行 120ms 限流防抖
            if "impact" in name:
                now = pygame.time.get_ticks()
                last = self.last_played.get(name, 0)
                if now - last < 120:
                    return
                self.last_played[name] = now
                
            self.sounds[name].play()
        if self.subtitle_callback:
            self.subtitle_callback(name)

    def play_music(self):
        """循環播放柔和的 8-bit 背景音樂 (BGM)"""
        if not self.enabled:
            return
        import pygame
        try:
            path = os.path.join(SOUND_DIR, "bgm.wav")
            if os.path.exists(path):
                pygame.mixer.music.load(path)
                pygame.mixer.music.set_volume(0.35)  # 柔和的背景音量
                pygame.mixer.music.play(-1)          # -1 代表循環播放
        except Exception as e:
            print(f"背景音樂播放失敗：{e}")

    def stop_music(self):
        """停止背景音樂"""
        import pygame
        try:
            pygame.mixer.music.stop()
        except Exception as e:
            print(f"背景音樂停止失敗：{e}")

# 單例模式方便全局調用
sound_manager = SoundManager()

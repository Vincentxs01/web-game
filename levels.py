import os
import json

CUSTOM_LEVEL_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "custom_level.json")

# 內建關卡配置
BUILTIN_LEVELS = [
    # --- 關卡 1：新手訓練場 ---
    {
        "name": "新手訓練場",
        "birds": ["red", "yellow", "blue"],
        "blocks": [
            # 兩根木柱，上方鋪一橫木板
            {"material": "wood", "x": 600, "y": 460, "width": 20, "height": 80, "shape_type": "rect"},
            {"material": "wood", "x": 680, "y": 460, "width": 20, "height": 80, "shape_type": "rect"},
            {"material": "wood", "x": 640, "y": 410, "width": 120, "height": 20, "shape_type": "rect"},
        ],
        "pigs": [
            # 普通小豬在板上
            {"pig_type": "minion", "x": 640, "y": 385}
        ]
    },
    
    # --- 關卡 2：冰木複合堡壘 ---
    {
        "name": "冰木防禦城堡",
        "birds": ["yellow", "blue", "red", "bomb"],
        "blocks": [
            # 底層木架
            {"material": "wood", "x": 580, "y": 460, "width": 20, "height": 80, "shape_type": "rect"},
            {"material": "wood", "x": 700, "y": 460, "width": 20, "height": 80, "shape_type": "rect"},
            {"material": "wood", "x": 640, "y": 410, "width": 160, "height": 20, "shape_type": "rect"},
            # 上層冰架
            {"material": "ice", "x": 610, "y": 365, "width": 16, "height": 70, "shape_type": "rect"},
            {"material": "ice", "x": 670, "y": 365, "width": 16, "height": 70, "shape_type": "rect"},
            {"material": "ice", "x": 640, "y": 322, "width": 100, "height": 16, "shape_type": "rect"},
        ],
        "pigs": [
            # 頭盔豬在下層庇護所，普通豬在上層冰架上
            {"pig_type": "helmet", "x": 640, "y": 485},
            {"pig_type": "minion", "x": 640, "y": 299}
        ]
    },
    
    # --- 關卡 3：巨石國王城堡 ---
    {
        "name": "巨石國王城堡",
        "birds": ["red", "yellow", "bomb", "bomb", "blue"],
        "blocks": [
            # 底層三根厚重石柱
            {"material": "stone", "x": 540, "y": 450, "width": 30, "height": 100, "shape_type": "rect"},
            {"material": "stone", "x": 640, "y": 450, "width": 30, "height": 100, "shape_type": "rect"},
            {"material": "stone", "x": 740, "y": 450, "width": 30, "height": 100, "shape_type": "rect"},
            {"material": "stone", "x": 640, "y": 390, "width": 240, "height": 20, "shape_type": "rect"},
            # 中層木架
            {"material": "wood", "x": 580, "y": 340, "width": 20, "height": 80, "shape_type": "rect"},
            {"material": "wood", "x": 700, "y": 340, "width": 20, "height": 80, "shape_type": "rect"},
            {"material": "wood", "x": 640, "y": 290, "width": 160, "height": 20, "shape_type": "rect"},
            # 頂層冰架
            {"material": "ice", "x": 615, "y": 245, "width": 15, "height": 70, "shape_type": "rect"},
            {"material": "ice", "x": 665, "y": 245, "width": 15, "height": 70, "shape_type": "rect"},
            {"material": "ice", "x": 640, "y": 202, "width": 80, "height": 15, "shape_type": "rect"},
        ],
        "pigs": [
            # 國王豬與頭盔豬坐鎮城堡 (調整 Y 坐標使其完美貼合支撐面，防止初始碰撞震碎城堡)
            {"pig_type": "king", "x": 640, "y": 356},
            {"pig_type": "helmet", "x": 590, "y": 485},
            {"pig_type": "helmet", "x": 690, "y": 485},
            {"pig_type": "minion", "x": 640, "y": 179.5}
        ]
    }
]

def load_level(level_idx):
    """
    加載關卡資料。
    level_idx 從 0 開始 (0=關卡1, 1=關卡2, 2=關卡3)
    如果是 "custom"，則加載本地自定義 JSON 檔案
    """
    if level_idx == "custom":
        if os.path.exists(CUSTOM_LEVEL_FILE):
            try:
                with open(CUSTOM_LEVEL_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return data
            except Exception as e:
                print(f"自定義關卡加載錯誤，將使用預設關卡：{e}")
                
        # 預設自定義關卡
        return {
            "name": "自定義關卡",
            "birds": ["red", "yellow", "bomb"],
            "blocks": [
                {"material": "wood", "x": 640, "y": 460, "width": 80, "height": 80, "shape_type": "rect"}
            ],
            "pigs": [
                {"pig_type": "minion", "x": 640, "y": 380}
            ]
        }
    
    # 載入內建關卡
    idx = max(0, min(len(BUILTIN_LEVELS) - 1, level_idx))
    # 回傳關卡複製品，避免原數據在遊戲運行中被修改
    original = BUILTIN_LEVELS[idx]
    return {
        "name": original["name"],
        "birds": list(original["birds"]),
        "blocks": [dict(b) for b in original["blocks"]],
        "pigs": [dict(p) for p in original["pigs"]]
    }

def save_custom_level(blocks_data, pigs_data, birds_queue=None):
    """保存自定義關卡至 JSON"""
    if birds_queue is None:
        birds_queue = ["red", "yellow", "blue", "bomb"]
        
    data = {
        "name": "自定義關卡",
        "birds": list(birds_queue),
        "blocks": blocks_data,
        "pigs": pigs_data
    }
    
    try:
        with open(CUSTOM_LEVEL_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        print("自定義關卡已成功保存！")
        return True
    except Exception as e:
        print(f"保存自定義關卡失敗：{e}")
        return False

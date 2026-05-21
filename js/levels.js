const CUSTOM_LEVEL_KEY = 'angry_birds_custom_level';

export const BUILTIN_LEVELS = [
  {
    name: '新手訓練場',
    birds: ['red', 'yellow', 'blue'],
    blocks: [
      { material: 'wood', x: 600, y: 460, width: 20, height: 80, shape_type: 'rect' },
      { material: 'wood', x: 680, y: 460, width: 20, height: 80, shape_type: 'rect' },
      { material: 'wood', x: 640, y: 410, width: 120, height: 20, shape_type: 'rect' },
    ],
    pigs: [{ pig_type: 'minion', x: 640, y: 385 }],
  },
  {
    name: '冰木防禦城堡',
    birds: ['yellow', 'blue', 'red', 'bomb'],
    blocks: [
      { material: 'wood', x: 580, y: 460, width: 20, height: 80, shape_type: 'rect' },
      { material: 'wood', x: 700, y: 460, width: 20, height: 80, shape_type: 'rect' },
      { material: 'wood', x: 640, y: 410, width: 160, height: 20, shape_type: 'rect' },
      { material: 'ice', x: 610, y: 365, width: 16, height: 70, shape_type: 'rect' },
      { material: 'ice', x: 670, y: 365, width: 16, height: 70, shape_type: 'rect' },
      { material: 'ice', x: 640, y: 322, width: 100, height: 16, shape_type: 'rect' },
    ],
    pigs: [
      { pig_type: 'helmet', x: 640, y: 485 },
      { pig_type: 'minion', x: 640, y: 299 },
    ],
  },
  {
    name: '巨石國王城堡',
    birds: ['red', 'yellow', 'bomb', 'bomb', 'blue'],
    blocks: [
      { material: 'stone', x: 540, y: 450, width: 30, height: 100, shape_type: 'rect' },
      { material: 'stone', x: 640, y: 450, width: 30, height: 100, shape_type: 'rect' },
      { material: 'stone', x: 740, y: 450, width: 30, height: 100, shape_type: 'rect' },
      { material: 'stone', x: 640, y: 390, width: 240, height: 20, shape_type: 'rect' },
      { material: 'wood', x: 580, y: 340, width: 20, height: 80, shape_type: 'rect' },
      { material: 'wood', x: 700, y: 340, width: 20, height: 80, shape_type: 'rect' },
      { material: 'wood', x: 640, y: 290, width: 160, height: 20, shape_type: 'rect' },
      { material: 'ice', x: 615, y: 245, width: 15, height: 70, shape_type: 'rect' },
      { material: 'ice', x: 665, y: 245, width: 15, height: 70, shape_type: 'rect' },
      { material: 'ice', x: 640, y: 202, width: 80, height: 15, shape_type: 'rect' },
    ],
    pigs: [
      { pig_type: 'king', x: 640, y: 356 },
      { pig_type: 'helmet', x: 590, y: 485 },
      { pig_type: 'helmet', x: 690, y: 485 },
      { pig_type: 'minion', x: 640, y: 179.5 },
    ],
  },
];

const DEFAULT_CUSTOM = {
  name: '自定義關卡',
  birds: ['red', 'yellow', 'bomb'],
  blocks: [
    { material: 'wood', x: 640, y: 460, width: 80, height: 80, shape_type: 'rect' },
  ],
  pigs: [{ pig_type: 'minion', x: 640, y: 380 }],
};

export function loadLevel(levelIdx) {
  if (levelIdx === 'custom') {
    try {
      const raw = localStorage.getItem(CUSTOM_LEVEL_KEY);
      if (raw) return JSON.parse(raw);
    } catch (_) {
      /* use default */
    }
    return { ...DEFAULT_CUSTOM };
  }

  const idx = Math.max(0, Math.min(BUILTIN_LEVELS.length - 1, levelIdx));
  const original = BUILTIN_LEVELS[idx];
  return {
    name: original.name,
    birds: [...original.birds],
    blocks: original.blocks.map((b) => ({ ...b })),
    pigs: original.pigs.map((p) => ({ ...p })),
  };
}

export function saveCustomLevel(blocks, pigs, birds = ['red', 'yellow', 'blue', 'bomb']) {
  const data = {
    name: '自定義關卡',
    birds: [...birds],
    blocks,
    pigs,
  };
  localStorage.setItem(CUSTOM_LEVEL_KEY, JSON.stringify(data));
  return true;
}

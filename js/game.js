import { Vec2 } from './vec2.js';
import { PhysicsWorld, PhysicsBody } from './physics.js';
import { soundManager } from './sound.js';
import { assets } from './assets.js';
import { Bird, Slingshot, ParticleSystem, FloatingText } from './entities.js';
import { loadLevel, saveCustomLevel } from './levels.js';

export const SCREEN_WIDTH = 960;
export const SCREEN_HEIGHT = 540;
const FPS = 60;

export class GameCoordinator {
  constructor(canvas) {
    this.canvas = canvas;
    this.ctx = canvas.getContext('2d');
    this.state = 'MENU';
    this.score = 0;
    this.highScores = { 0: 0, 1: 0, 2: 0, custom: 0 };
    this.currentLevelIdx = 0;
    this.levelName = '';
    this.physicsWorld = new PhysicsWorld();
    this.slingshot = new Slingshot(150, 480);
    this.particleSystem = new ParticleSystem();
    this.floatingTexts = [];
    this.birdsQueue = [];
    this.birdsInAir = [];
    this.cameraOffset = new Vec2(0, 0);
    this.cameraTargetX = 0;
    this.shakeIntensity = 0;
    this.stateTimer = 0;
    this.levelCompleted = false;
    this.levelFailed = false;
    this.editorBlocks = [];
    this.editorPigs = [];
    this.editorSelectedTool = 'block_wood';
    this.editorBlockOrientation = 'vertical';
    this.subtitles = [];
    this.clouds = [
      { x: 100, y: 80, speed: 12, w: 120, h: 60 },
      { x: 450, y: 140, speed: 8, w: 180, h: 90 },
      { x: 800, y: 60, speed: 15, w: 100, h: 50 },
    ];
    this.pointer = { x: 0, y: 0 };
    this.keys = {};
    this.lastTime = 0;
    this.rafId = null;

    soundManager.subtitleCallback = (name) => this.onSoundPlayed(name);
    this.bindEvents();
  }

  async init() {
    await soundManager.init();
    soundManager.playMusic();
    this.lastTime = performance.now();
    this.loop();
  }

  bindEvents() {
    const toCanvas = (clientX, clientY) => {
      const rect = this.canvas.getBoundingClientRect();
      const scaleX = SCREEN_WIDTH / rect.width;
      const scaleY = SCREEN_HEIGHT / rect.height;
      return {
        x: (clientX - rect.left) * scaleX,
        y: (clientY - rect.top) * scaleY,
      };
    };

    this.canvas.addEventListener('pointerdown', (e) => {
      soundManager.unlock();
      const p = toCanvas(e.clientX, e.clientY);
      this.pointer.x = p.x;
      this.pointer.y = p.y;
      this.onPointerDown(p.x, p.y, e.button);
      if (this.state === 'GAMEPLAY') this.canvas.setPointerCapture(e.pointerId);
    });

    this.canvas.addEventListener('pointermove', (e) => {
      const p = toCanvas(e.clientX, e.clientY);
      this.pointer.x = p.x;
      this.pointer.y = p.y;
      this.onPointerMove(p.x, p.y);
    });

    this.canvas.addEventListener('pointerup', (e) => {
      const p = toCanvas(e.clientX, e.clientY);
      this.onPointerUp(p.x, p.y, e.button);
    });

    window.addEventListener('keydown', (e) => {
      this.keys[e.key.toLowerCase()] = true;
      if (e.key === 'Escape') {
        if (['GAMEPLAY', 'LEVEL_SELECT', 'EDITOR'].includes(this.state)) {
          this.state = 'MENU';
        }
      }
      if (e.key.toLowerCase() === 'r' && this.state === 'GAMEPLAY') {
        this.loadGameLevel(this.currentLevelIdx);
      }
    });
    window.addEventListener('keyup', (e) => {
      this.keys[e.key.toLowerCase()] = false;
    });

    window.addEventListener('resize', () => this.resizeCanvas());
    this.canvas.addEventListener('contextmenu', (e) => e.preventDefault());
    this.resizeCanvas();
  }

  resizeCanvas() {
    const maxW = window.innerWidth;
    const maxH = window.innerHeight - 8;
    const scale = Math.min(maxW / SCREEN_WIDTH, maxH / SCREEN_HEIGHT, 1);
    this.canvas.style.width = `${SCREEN_WIDTH * scale}px`;
    this.canvas.style.height = `${SCREEN_HEIGHT * scale}px`;
  }

  onPointerDown(x, y, button) {
    if (this.state === 'MENU' && button === 0) {
      if (x >= 370 && x <= 590 && y >= 270 && y <= 326) {
        soundManager.play('boost');
        this.state = 'LEVEL_SELECT';
      }
    } else if (this.state === 'LEVEL_SELECT' && button === 0) {
      const eb = this._editorBtn;
      if (
        eb &&
        x >= eb.x &&
        x <= eb.x + eb.w &&
        y >= eb.y &&
        y <= eb.y + eb.h
      ) {
        soundManager.play('boost');
        this.state = 'EDITOR';
        this.cameraOffset.set(0, 0);
        try {
          const custom = loadLevel('custom');
          this.editorBlocks = custom.blocks.map((b) => ({ ...b }));
          this.editorPigs = custom.pigs.map((p) => ({ ...p }));
        } catch (_) {
          this.editorBlocks = [];
          this.editorPigs = [];
        }
        return;
      }
      if (y >= 200 && y <= 300) {
        if (x >= 150 && x <= 310) {
          soundManager.play('launch');
          this.loadGameLevel(0);
        } else if (x >= 400 && x <= 560) {
          soundManager.play('launch');
          this.loadGameLevel(1);
        } else if (x >= 650 && x <= 810) {
          soundManager.play('launch');
          this.loadGameLevel(2);
        }
      }
    } else if (this.state === 'GAMEPLAY' && button === 0) {
      const world = new Vec2(x + this.cameraOffset.x, y + this.cameraOffset.y);
      const launched = this.slingshot.handlePointerDown(world);
      if (!launched && !this.slingshot.isDragging) {
        for (const bird of this.birdsInAir) {
          if (!bird.hasUsedAbility) {
            const newBirds = bird.triggerAbility(this.physicsWorld);
            for (const nb of newBirds) {
              this.physicsWorld.addBody(nb);
              this.birdsInAir.push(nb);
            }
            break;
          }
        }
      }
    } else if (this.state === 'EDITOR') {
      this.handleEditorClick(x, y, button);
    } else if (['VICTORY', 'DEFEAT'].includes(this.state) && button === 0) {
      if (y >= 360 && y <= 410) {
        if (x >= 400 && x <= 470) {
          soundManager.play('launch');
          this.loadGameLevel(this.currentLevelIdx);
        } else if (x >= 490 && x <= 560) {
          soundManager.play('boost');
          this.state = 'LEVEL_SELECT';
        }
      }
    }
  }

  onPointerMove(x, y) {
    if (this.state === 'GAMEPLAY' && this.slingshot.isDragging) {
      const world = new Vec2(x + this.cameraOffset.x, y + this.cameraOffset.y);
      this.slingshot.handlePointerMove(world);
    }
  }

  onPointerUp(x, y, button) {
    if (this.state === 'GAMEPLAY' && button === 0) {
      const launched = this.slingshot.handlePointerUp();
      if (launched) {
        this.birdsInAir.push(launched);
      }
    }
  }

  handleEditorClick(screenX, screenY, button) {
    const worldX = screenX + this.cameraOffset.x;
    const worldY = screenY + this.cameraOffset.y;

    if (button === 0 && screenY <= 45) {
      if (screenX >= 10 && screenX <= 90) this.editorSelectedTool = 'block_wood';
      else if (screenX >= 100 && screenX <= 180) this.editorSelectedTool = 'block_ice';
      else if (screenX >= 190 && screenX <= 270) this.editorSelectedTool = 'block_stone';
      else if (screenX >= 290 && screenX <= 370) this.editorSelectedTool = 'pig_minion';
      else if (screenX >= 380 && screenX <= 460) this.editorSelectedTool = 'pig_helmet';
      else if (screenX >= 470 && screenX <= 550) this.editorSelectedTool = 'pig_king';
      else if (screenX >= 570 && screenX <= 650) {
        const o = ['vertical', 'horizontal', 'square'];
        this.editorBlockOrientation =
          o[(o.indexOf(this.editorBlockOrientation) + 1) % 3];
        soundManager.play('boost');
      } else if (screenX >= 680 && screenX <= 760) {
        saveCustomLevel(this.editorBlocks, this.editorPigs);
        soundManager.play('victory');
      } else if (screenX >= 770 && screenX <= 850) {
        saveCustomLevel(this.editorBlocks, this.editorPigs);
        soundManager.play('launch');
        this.loadGameLevel('custom');
      } else if (screenX >= 860 && screenX <= 940) {
        this.editorBlocks = [];
        this.editorPigs = [];
        soundManager.play('defeat');
      }
      return;
    }

    if (button === 0 && worldX > 300 && worldY < 510) {
      const gridX = Math.round(worldX / 10) * 10;
      const gridY = Math.round(worldY / 10) * 10;
      if (this.editorSelectedTool.startsWith('block')) {
        const mat = this.editorSelectedTool.split('_')[1];
        let w = 20,
          h = 80;
        if (this.editorBlockOrientation === 'horizontal') [w, h] = [80, 20];
        else if (this.editorBlockOrientation === 'square') [w, h] = [40, 40];
        const dup = this.editorBlocks.some(
          (b) => Math.abs(b.x - gridX) < 15 && Math.abs(b.y - gridY) < 15
        );
        if (!dup) {
          this.editorBlocks.push({
            material: mat,
            x: gridX,
            y: gridY,
            width: w,
            height: h,
            shape_type: 'rect',
          });
          soundManager.play(
            mat === 'wood' ? 'wood_impact' : mat === 'ice' ? 'ice_impact' : 'stone_impact'
          );
        }
      } else if (this.editorSelectedTool.startsWith('pig')) {
        const pigT = this.editorSelectedTool.split('_')[1];
        const dup = this.editorPigs.some(
          (p) => Math.abs(p.x - gridX) < 20 && Math.abs(p.y - gridY) < 20
        );
        if (!dup) {
          this.editorPigs.push({ pig_type: pigT, x: gridX, y: gridY });
          soundManager.play('pig_pop');
        }
      }
    } else if (button === 2) {
      for (let i = this.editorBlocks.length - 1; i >= 0; i--) {
        const b = this.editorBlocks[i];
        if (
          worldX >= b.x - b.width / 2 &&
          worldX <= b.x + b.width / 2 &&
          worldY >= b.y - b.height / 2 &&
          worldY <= b.y + b.height / 2
        ) {
          this.editorBlocks.splice(i, 1);
          soundManager.play('wood_impact');
          return;
        }
      }
      for (let i = this.editorPigs.length - 1; i >= 0; i--) {
        const p = this.editorPigs[i];
        const radius = p.pig_type === 'king' ? 24 : 15;
        if (Vec2.sub(new Vec2(p.x, p.y), new Vec2(worldX, worldY)).length() < radius) {
          this.editorPigs.splice(i, 1);
          soundManager.play('pig_pop');
          return;
        }
      }
    }
  }

  loadGameLevel(levelIdx) {
    this.currentLevelIdx = levelIdx;
    const data = loadLevel(levelIdx);
    this.levelName = data.name;
    this.physicsWorld.clear();
    this.particleSystem.particles = [];
    this.floatingTexts = [];
    this.birdsQueue = [];
    this.birdsInAir = [];
    this.score = 0;
    this.cameraOffset.set(0, 0);
    this.cameraTargetX = 0;
    this.shakeIntensity = 0;
    this.levelCompleted = false;
    this.levelFailed = false;
    this.stateTimer = 0;

    const ground = new PhysicsBody(800, 510, {
      shapeType: 'rect',
      isStatic: true,
      restitution: 0.1,
      friction: 0.6,
      width: 1600,
      height: 20,
      category: 'ground',
      material: 'stone',
    });
    this.physicsWorld.addBody(ground);

    for (const b of data.blocks) {
      const mass = b.material === 'wood' ? 1.2 : b.material === 'ice' ? 0.4 : 3;
      const maxHealth =
        b.material === 'wood' ? 40 : b.material === 'ice' ? 15 : 120;
      this.physicsWorld.addBody(
        new PhysicsBody(b.x, b.y, {
          shapeType: 'rect',
          mass,
          restitution: b.material === 'stone' ? 0.1 : 0.2,
          friction: b.material === 'ice' ? 0.3 : 0.4,
          width: b.width,
          height: b.height,
          maxHealth,
          category: 'block',
          material: b.material,
        })
      );
    }

    for (const p of data.pigs) {
      const body = new PhysicsBody(p.x, p.y, {
        shapeType: 'circle',
        mass: p.pig_type === 'minion' ? 1 : p.pig_type === 'helmet' ? 1.5 : 3.5,
        restitution: 0.15,
        friction: 0.3,
        radius: p.pig_type === 'king' ? 24 : 15,
        maxHealth: p.pig_type === 'minion' ? 15 : p.pig_type === 'helmet' ? 35 : 60,
        category: 'pig',
        material: 'pig',
        pigType: p.pig_type,
      });
      body.pigType = p.pig_type;
      this.physicsWorld.addBody(body);
    }

    const slingshotCenter = new Vec2(150, 432);
    data.birds.forEach((birdType, i) => {
      const bird =
        i === 0
          ? new Bird(slingshotCenter.x, slingshotCenter.y, birdType)
          : new Bird(110 - i * 30, 485, birdType);
      if (i === 0) this.slingshot.activeBird = bird;
      this.birdsQueue.push(bird);
      this.physicsWorld.addBody(bird);
    });

    this.state = 'GAMEPLAY';
  }

  updateClouds(dt) {
    for (const cloud of this.clouds) {
      cloud.x -= cloud.speed * dt;
      if (cloud.x + cloud.w < -50) {
        cloud.x = SCREEN_WIDTH + 20 + Math.random() * 80;
        cloud.y = 30 + Math.random() * 120;
        cloud.speed = 6 + Math.random() * 9;
      }
    }
  }

  update(dt) {
    this.updateClouds(dt);
    if (this.state === 'GAMEPLAY') this.updateGameplay(dt);
    else if (this.state === 'EDITOR') {
      if (this.keys.a || this.keys.arrowleft)
        this.cameraOffset.x = Math.max(0, this.cameraOffset.x - 400 * dt);
      if (this.keys.d || this.keys.arrowright)
        this.cameraOffset.x = Math.min(700, this.cameraOffset.x + 400 * dt);
    }
    if (this.shakeIntensity > 0.1) this.shakeIntensity *= 0.88;
    for (let i = this.subtitles.length - 1; i >= 0; i--) {
      this.subtitles[i].timer -= dt;
      if (this.subtitles[i].timer <= 0) this.subtitles.splice(i, 1);
    }
  }

  updateGameplay(dt) {
    this.physicsWorld.update(dt);
    for (const snd of this.physicsWorld.impactSounds) soundManager.play(snd);

    for (const ev of this.physicsWorld.damageEvents) {
      const body = ev.body;
      const pos = ev.pos;
      if (body.category === 'block') {
        this.particleSystem.spawnShards(
          pos.x,
          pos.y,
          body.material,
          ev.destroyed ? 10 : 4
        );
        let points = Math.floor(ev.damage * 5);
        points = Math.max(10, Math.min(1000, points));
        this.score += points;
        if (ev.destroyed) {
          this.score += body.scoreValue;
          this.floatingTexts.push(
            new FloatingText(pos.x, pos.y, `+${body.scoreValue}`, [235, 150, 50])
          );
        }
      } else if (body.category === 'pig') {
        if (ev.destroyed) {
          this.particleSystem.spawnShards(pos.x, pos.y, 'pig', 14);
          this.particleSystem.spawnSmoke(pos.x, pos.y, 8, 15);
          this.score += body.scoreValue;
          this.floatingTexts.push(
            new FloatingText(pos.x, pos.y, `+${body.scoreValue}`, [100, 255, 100], 30)
          );
          this.shakeIntensity = Math.min(15, this.shakeIntensity + 6);
          soundManager.play('pig_pop');
        } else {
          this.particleSystem.spawnShards(pos.x, pos.y, 'pig', 4);
          let points = Math.floor(ev.damage * 3);
          points = Math.max(10, Math.min(150, points));
          this.score += points;
        }
      }
    }

    this.particleSystem.update(dt);
    for (let i = this.floatingTexts.length - 1; i >= 0; i--) {
      this.floatingTexts[i].update(dt);
      if (this.floatingTexts[i].life <= 0) this.floatingTexts.splice(i, 1);
    }

    const now = performance.now();
    for (let i = this.birdsInAir.length - 1; i >= 0; i--) {
      const bird = this.birdsInAir[i];
      if (Math.floor(now / 50) % 2 === 0) {
        if (
          !bird.trail.length ||
          Vec2.sub(bird.pos, bird.trail[bird.trail.length - 1]).length() > 10
        ) {
          bird.trail.push(bird.pos.clone());
          if (bird.trail.length > 30) bird.trail.shift();
        }
      }
      let isStopped = false;
      if (bird.isDestroyed) isStopped = true;
      else if (bird.vel.lengthSquared() < 64 && now - bird.launchTime > 1200)
        isStopped = true;
      else if (now - bird.launchTime > 5000) isStopped = true;
      else if (bird.pos.y > 510 || bird.pos.x > 1500 || bird.pos.x < -100)
        isStopped = true;

      if (isStopped) {
        this.particleSystem.spawnSmoke(bird.pos.x, bird.pos.y, 5, 10);
        this.physicsWorld.removeBody(bird);
        this.birdsInAir.splice(i, 1);
        if (this.birdsInAir.length === 0) this.prepareNextBird();
      }
    }

    if (this.birdsInAir.length) {
      this.cameraTargetX = this.birdsInAir[0].pos.x - 320;
    } else {
      this.cameraTargetX = 0;
    }
    this.cameraTargetX = Math.max(0, Math.min(640, this.cameraTargetX));
    this.cameraOffset.x += (this.cameraTargetX - this.cameraOffset.x) * 0.08;
    this.checkLevelEndConditions();
  }

  prepareNextBird() {
    if (this.birdsQueue.length) this.birdsQueue.shift();
    if (this.birdsQueue.length) {
      const next = this.birdsQueue[0];
      next.pos.set(150, 432);
      this.slingshot.activeBird = next;
    } else {
      this.slingshot.activeBird = null;
    }
  }

  checkLevelEndConditions() {
    const pigs = this.physicsWorld.bodies.filter((b) => b.category === 'pig');
    const now = performance.now();

    if (pigs.length === 0 && !this.levelCompleted) {
      this.levelCompleted = true;
      this.stateTimer = now;
      soundManager.play('victory');
      let bonus = this.birdsQueue.length * 10000;
      if (this.slingshot.activeBird) bonus += 10000;
      this.score += bonus;
      const key = String(this.currentLevelIdx);
      if (this.score > (this.highScores[key] || 0)) this.highScores[key] = this.score;
    } else if (
      pigs.length > 0 &&
      this.birdsQueue.length === 0 &&
      this.birdsInAir.length === 0 &&
      !this.slingshot.activeBird &&
      !this.levelFailed
    ) {
      this.levelFailed = true;
      this.stateTimer = now;
    }

    if (this.levelCompleted && now - this.stateTimer > 1500) {
      this.state = 'VICTORY';
    } else if (this.levelFailed && now - this.stateTimer > 2000) {
      const pigsCheck = this.physicsWorld.bodies.filter((b) => b.category === 'pig');
      if (pigsCheck.length === 0) {
        this.levelFailed = false;
        this.levelCompleted = true;
        this.state = 'VICTORY';
        this.score += 10000;
      } else {
        this.state = 'DEFEAT';
        soundManager.play('defeat');
      }
    }
  }

  onSoundPlayed(soundName) {
    const map = {
      launch: '【發射小鳥！】',
      boost: '【小鳥技能加速！】',
      wood_impact: '【碰撞木頭】',
      ice_impact: '【碰撞冰塊】',
      stone_impact: '【碰撞石頭】',
      pig_pop: '【綠豬被消滅！】',
      explosion: '【大爆炸！！！】',
      victory: '【關卡挑戰成功！】',
      defeat: '【挑戰失敗...】',
    };
    const text = map[soundName];
    if (!text) return;
    for (const sub of this.subtitles) {
      if (sub.text === text && sub.timer > 1) {
        sub.timer = 1.5;
        return;
      }
    }
    this.subtitles.push({ text, timer: 1.5 });
    if (this.subtitles.length > 3) this.subtitles.shift();
  }

  loop() {
    const now = performance.now();
    const dt = Math.min((now - this.lastTime) / 1000, 0.05);
    this.lastTime = now;
    this.update(dt);
    this.render();
    this.rafId = requestAnimationFrame(() => this.loop());
  }

  render() {
    const ctx = this.ctx;
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.clearRect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT);

    const offset = this.cameraOffset.clone();
    if (this.shakeIntensity > 0.1) {
      offset.x += (Math.random() - 0.5) * this.shakeIntensity * 2;
      offset.y += (Math.random() - 0.5) * this.shakeIntensity * 2;
    }

    if (this.state === 'MENU') this.renderMenu();
    else if (this.state === 'LEVEL_SELECT') this.renderLevelSelect();
    else if (this.state === 'GAMEPLAY') this.renderGameplay(offset);
    else if (this.state === 'EDITOR') this.renderEditor();
    else if (['VICTORY', 'DEFEAT'].includes(this.state)) {
      this.renderGameplay(offset);
      this.renderGameOver();
    }
    this.renderSubtitles();
  }

  drawSkyAndHills(parallax = 0) {
    const ctx = this.ctx;
    ctx.drawImage(
      assets.getTexture('sky', SCREEN_WIDTH, SCREEN_HEIGHT),
      0,
      0
    );
    for (const cloud of this.clouds) {
      ctx.drawImage(
        assets.getTexture('cloud', cloud.w, cloud.h),
        cloud.x - parallax * 0.05,
        cloud.y
      );
    }
    ctx.drawImage(
      assets.getTexture('hill', 1600, SCREEN_HEIGHT, 'far'),
      -parallax * 0.1,
      0
    );
    ctx.drawImage(
      assets.getTexture('hill', 1600, SCREEN_HEIGHT, 'mid'),
      -parallax * 0.35,
      0
    );
    ctx.drawImage(
      assets.getTexture('hill', 1600, SCREEN_HEIGHT, 'near'),
      -parallax,
      0
    );
  }

  renderMenu() {
    this.drawSkyAndHills(0);
    const ctx = this.ctx;
    const t = performance.now();

    ctx.font = 'bold 68px "Comic Sans MS", sans-serif';
    const title = 'ANGRY BIRDS';
    let x = SCREEN_WIDTH / 2 - 200;
    for (let i = 0; i < title.length; i++) {
      const ch = title[i];
      if (ch === ' ') {
        x += 20;
        continue;
      }
      const wave = Math.sin(t * 0.005 + i * 0.6) * 7;
      ctx.fillStyle = '#141414';
      for (const [dx, dy] of [
        [-3, -3],
        [0, -3],
        [3, -3],
        [-3, 0],
        [3, 0],
        [-3, 3],
        [0, 3],
        [3, 3],
      ]) {
        ctx.fillText(ch, x + dx, 75 + wave + dy);
      }
      ctx.fillStyle = i % 2 === 0 ? 'rgb(255,127,80)' : 'rgb(255,215,0)';
      ctx.fillText(ch, x, 75 + wave);
      x += ctx.measureText(ch).width + 4;
    }

    const btnW = 220;
    const btnH = 56;
    const btnX = SCREEN_WIDTH / 2 - btnW / 2;
    const btnY = 270;
    const hover =
      this.pointer.x >= btnX &&
      this.pointer.x <= btnX + btnW &&
      this.pointer.y >= btnY &&
      this.pointer.y <= btnY + btnH;

    let drawX = btnX;
    let drawY = btnY;
    let drawW = btnW;
    let drawH = btnH;
    if (hover) {
      drawW = Math.floor(btnW * 1.06);
      drawH = Math.floor(btnH * 1.06);
      drawX = SCREEN_WIDTH / 2 - drawW / 2;
      drawY = btnY - (drawH - btnH) / 2;
    }

    if (hover) {
      const glow = 3 + Math.sin(t * 0.012) * 3;
      ctx.fillStyle = 'rgba(255,230,0,0.35)';
      this.roundRect(drawX - glow, drawY - glow, drawW + glow * 2, drawH + glow * 2, 15);
      ctx.fill();
    }
    ctx.fillStyle = 'rgb(211,84,0)';
    this.roundRect(drawX, drawY + 6, drawW, drawH, 12);
    ctx.fill();
    ctx.fillStyle = hover ? 'rgb(255,99,71)' : 'rgb(255,127,80)';
    this.roundRect(drawX, drawY, drawW, drawH, 12);
    ctx.fill();
    ctx.strokeStyle = '#fff';
    ctx.lineWidth = 2;
    this.roundRect(drawX, drawY, drawW, drawH, 12);
    ctx.stroke();
    ctx.fillStyle = '#fff';
    ctx.font = 'bold 20px "Microsoft JhengHei", sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText('開始遊戲', drawX + drawW / 2, drawY + drawH / 2 + 7);
    ctx.textAlign = 'left';

    ctx.font = '12px Arial';
    ctx.fillStyle = 'rgb(44,62,80)';
    ctx.textAlign = 'center';
    ctx.fillText(
      'Antigravity AI Pair Programming Project 2026',
      SCREEN_WIDTH / 2,
      SCREEN_HEIGHT - 20
    );
    ctx.textAlign = 'left';
  }

  renderLevelSelect() {
    this.drawSkyAndHills(0);
    const ctx = this.ctx;
    ctx.font = 'bold 36px "Microsoft JhengHei", sans-serif';
    ctx.fillStyle = '#fff';
    ctx.textAlign = 'center';
    ctx.fillText('選擇關卡', SCREEN_WIDTH / 2 + 2, 62);
    ctx.fillStyle = 'rgb(44,62,80)';
    ctx.fillText('選擇關卡', SCREEN_WIDTH / 2, 60);

    const levels = [
      { idx: 0, name: ['關卡 1', '新手訓練'], rect: [150, 200, 160, 110], color: [95, 226, 156], bird: 'bird_red' },
      { idx: 1, name: ['關卡 2', '復合城堡'], rect: [400, 200, 160, 110], color: [255, 204, 120], bird: 'bird_yellow' },
      { idx: 2, name: ['關卡 3', '國王石城'], rect: [650, 200, 160, 110], color: [200, 160, 240], bird: 'bird_bomb' },
    ];

    for (const lvl of levels) {
      const [rx, ry, rw, rh] = lvl.rect;
      const hover =
        this.pointer.x >= rx &&
        this.pointer.x <= rx + rw &&
        this.pointer.y >= ry &&
        this.pointer.y <= ry + rh;
      const rect = hover ? [rx - 5, ry - 5, rw + 10, rh + 10] : lvl.rect;
      const shadow = lvl.color.map((c) => Math.max(0, c - 45));
      ctx.fillStyle = `rgb(${shadow.join(',')})`;
      this.roundRect(rect[0], rect[1] + 6, rect[2], rect[3], 14);
      ctx.fill();
      const base = hover ? lvl.color : lvl.color.map((c) => Math.max(0, c - 10));
      ctx.fillStyle = `rgb(${base.join(',')})`;
      this.roundRect(rect[0], rect[1], rect[2], rect[3], 14);
      ctx.fill();
      ctx.strokeStyle = '#fff';
      ctx.lineWidth = hover ? 3 : 1;
      this.roundRect(rect[0], rect[1], rect[2], rect[3], 14);
      ctx.stroke();
      ctx.font = 'bold 18px "Microsoft JhengHei", sans-serif';
      ctx.fillStyle = 'rgb(44,62,80)';
      ctx.fillText(lvl.name[0], rect[0] + rect[2] / 2, rect[1] + 36);
      ctx.fillText(lvl.name[1], rect[0] + rect[2] / 2, rect[1] + 60);
      ctx.font = 'bold 12px Arial';
      const hs = this.highScores[String(lvl.idx)] || 0;
      ctx.fillText(`High Score: ${hs}`, rect[0] + rect[2] / 2, rect[1] + rect[3] - 14);
      const birdTex = assets.getTexture(lvl.bird, 46, 46);
      ctx.globalAlpha = hover ? 1 : 0.6;
      ctx.drawImage(birdTex, rect[0] + rect[2] - 40, rect[1] + rect[3] - 44);
      ctx.globalAlpha = 1;
    }

    ctx.font = 'bold 14px "Microsoft JhengHei", sans-serif';
    ctx.fillStyle = 'rgb(80,85,90)';
    ctx.textAlign = 'left';
    ctx.fillText('按 ESC 鍵返回主選單', 15, 28);

    const editBtn = { x: SCREEN_WIDTH - 180, y: 14, w: 165, h: 32 };
    const editHover =
      this.pointer.x >= editBtn.x &&
      this.pointer.x <= editBtn.x + editBtn.w &&
      this.pointer.y >= editBtn.y &&
      this.pointer.y <= editBtn.y + editBtn.h;
    ctx.fillStyle = editHover ? 'rgb(155,89,182)' : 'rgb(142,68,173)';
    this.roundRect(editBtn.x, editBtn.y, editBtn.w, editBtn.h, 8);
    ctx.fill();
    ctx.fillStyle = '#fff';
    ctx.font = 'bold 13px "Microsoft JhengHei", sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText('關卡編輯器', editBtn.x + editBtn.w / 2, editBtn.y + 21);
    ctx.textAlign = 'left';
    this._editorBtn = editBtn;
  }

  renderGameplay(offset) {
    this.drawSkyAndHills(offset.x);
    const ctx = this.ctx;

    for (const bird of this.birdsInAir) {
      for (const pt of bird.trail) {
        ctx.fillStyle = 'rgb(220,220,220)';
        ctx.beginPath();
        ctx.arc(pt.x - offset.x, pt.y - offset.y, 3, 0, Math.PI * 2);
        ctx.fill();
      }
    }

    this.slingshot.drawDots(ctx, offset, this.physicsWorld.gravity.y);
    this.slingshot.drawBack(ctx, offset);

    for (const body of this.physicsWorld.bodies) {
      if (body.isDestroyed) continue;
      if (body.category === 'bird') body.draw(ctx, offset);
      else if (body.category === 'block')
        assets.drawBlockWithCracks(ctx, body, offset);
      else if (body.category === 'pig') assets.drawPig(ctx, body, offset);
    }

    this.slingshot.drawSlingshot(ctx, offset);
    this.particleSystem.draw(ctx, offset);
    for (const t of this.floatingTexts) t.draw(ctx, offset);

    ctx.font = 'bold 18px "Microsoft JhengHei", sans-serif';
    ctx.fillStyle = 'rgb(44,62,80)';
    ctx.fillText(`得分: ${this.score}`, 20, 32);
    const key = String(this.currentLevelIdx);
    const best = Math.max(this.score, this.highScores[key] || 0);
    ctx.fillText(`最高紀錄: ${best}`, 20, 58);
    ctx.fillStyle = 'rgb(230,126,34)';
    ctx.textAlign = 'center';
    ctx.fillText(this.levelName, SCREEN_WIDTH / 2, 32);
    ctx.textAlign = 'left';
    ctx.font = '13px "Microsoft JhengHei", sans-serif';
    ctx.fillStyle = 'rgb(100,110,120)';
    ctx.fillText('按 R 重置關卡 | 按 ESC 返回', SCREEN_WIDTH - 220, 28);
  }

  renderEditor() {
    const ctx = this.ctx;
    ctx.drawImage(
      assets.getTexture('sky', SCREEN_WIDTH, SCREEN_HEIGHT),
      0,
      0
    );
    ctx.strokeStyle = 'rgb(231,76,60)';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(0, 510);
    ctx.lineTo(SCREEN_WIDTH, 510);
    ctx.stroke();

    for (const b of this.editorBlocks) {
      const tex = assets.getTexture('block', b.width, b.height, b.material);
      ctx.drawImage(tex, b.x - b.width / 2, b.y - b.height / 2);
    }
    for (const p of this.editorPigs) {
      const d = p.pig_type === 'king' ? 48 : 30;
      const tex = assets.getTexture(`pig_${p.pig_type}`, d, d);
      ctx.drawImage(tex, p.x - d / 2, p.y - d / 2);
    }

    const slTex = assets.getTexture('slingshot', 36, 100);
    ctx.drawImage(slTex, 150 - 18, 410);

    ctx.fillStyle = 'rgb(44,62,80)';
    ctx.fillRect(0, 0, SCREEN_WIDTH, 55);
    const tools = [
      ['block_wood', '木箱', 10, [211, 137, 71]],
      ['block_ice', '冰箱', 100, [173, 232, 244]],
      ['block_stone', '石箱', 190, [149, 165, 166]],
      ['pig_minion', '普通綠豬', 290, [46, 204, 113]],
      ['pig_helmet', '頭盔綠豬', 380, [127, 140, 141]],
      ['pig_king', '國王巨豬', 470, [241, 196, 15]],
    ];
    ctx.font = 'bold 12px "Microsoft JhengHei", sans-serif';
    for (const [id, label, tx, col] of tools) {
      ctx.fillStyle = `rgb(${col.join(',')})`;
      this.roundRect(tx, 10, 80, 35, 6);
      ctx.fill();
      if (this.editorSelectedTool === id) {
        ctx.strokeStyle = '#fff';
        ctx.lineWidth = 3;
      } else {
        ctx.strokeStyle = 'rgb(44,62,80)';
        ctx.lineWidth = 1;
      }
      this.roundRect(tx, 10, 80, 35, 6);
      ctx.stroke();
      ctx.fillStyle = id === 'block_ice' || id.includes('pig') ? '#000' : '#fff';
      ctx.textAlign = 'center';
      ctx.fillText(label, tx + 40, 30);
    }
    ctx.textAlign = 'left';

    if (this.pointer.y > 55 && this.pointer.x > 300) {
      const gridX = Math.round(this.pointer.x / 10) * 10;
      const gridY = Math.round(this.pointer.y / 10) * 10;
      ctx.strokeStyle = '#fff';
      ctx.lineWidth = 2;
      if (this.editorSelectedTool.startsWith('block')) {
        let w = 20,
          h = 80;
        if (this.editorBlockOrientation === 'horizontal') [w, h] = [80, 20];
        else if (this.editorBlockOrientation === 'square') [w, h] = [40, 40];
        ctx.strokeRect(gridX - w / 2, gridY - h / 2, w, h);
      } else {
        const radius = this.editorSelectedTool === 'pig_king' ? 24 : 15;
        ctx.beginPath();
        ctx.arc(gridX, gridY, radius, 0, Math.PI * 2);
        ctx.stroke();
      }
    }

    ctx.fillStyle = '#fff';
    ctx.font = '12px "Microsoft JhengHei", sans-serif';
    ctx.fillText('左鍵放置 | 右鍵刪除 | A/D 平移 | ESC 返回', 20, SCREEN_HEIGHT - 12);
    ctx.fillText('工具列：方向/保存/測試/清空 請點擊頂部按鈕區', 20, SCREEN_HEIGHT - 28);
  }

  renderGameOver() {
    const ctx = this.ctx;
    ctx.fillStyle = 'rgba(255,255,255,0.6)';
    ctx.fillRect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT);
    const px = SCREEN_WIDTH / 2 - 200;
    const py = SCREEN_HEIGHT / 2 - 130;
    ctx.fillStyle = 'rgb(248,249,250)';
    this.roundRect(px, py, 400, 260, 15);
    ctx.fill();
    ctx.strokeStyle = 'rgb(189,195,199)';
    ctx.lineWidth = 3;
    this.roundRect(px, py, 400, 260, 15);
    ctx.stroke();

    ctx.textAlign = 'center';
    ctx.font = 'bold 36px "Microsoft JhengHei", sans-serif';
    ctx.fillStyle =
      this.state === 'VICTORY' ? 'rgb(230,126,34)' : 'rgb(231,76,60)';
    ctx.fillText(
      this.state === 'VICTORY' ? '關卡挑戰成功！' : '挑戰失敗...',
      SCREEN_WIDTH / 2,
      py + 60
    );
    ctx.font = 'bold 20px "Microsoft JhengHei", sans-serif';
    ctx.fillStyle = 'rgb(44,62,80)';
    ctx.fillText(`最終得分: ${this.score}`, SCREEN_WIDTH / 2, py + 115);

    let stars = 0;
    if (this.state === 'VICTORY') {
      const thresholds = [
        [6000, 12000],
        [8000, 16000],
        [9000, 15000],
      ];
      if (this.currentLevelIdx === 'custom') stars = 3;
      else if (typeof this.currentLevelIdx === 'number') {
        const [t1, t2] = thresholds[this.currentLevelIdx] || [9000, 15000];
        stars = this.score < t1 ? 1 : this.score < t2 ? 2 : 3;
      }
    }
    ctx.font = '42px sans-serif';
    for (let i = 0; i < 3; i++) {
      ctx.fillStyle = i < stars ? 'rgb(241,196,15)' : 'rgb(189,195,199)';
      ctx.fillText(i < stars ? '★' : '☆', SCREEN_WIDTH / 2 - 50 + i * 50, py + 165);
    }

    const btn1Hover =
      this.pointer.x >= 400 &&
      this.pointer.x <= 470 &&
      this.pointer.y >= 360 &&
      this.pointer.y <= 410;
    const btn2Hover =
      this.pointer.x >= 490 &&
      this.pointer.x <= 560 &&
      this.pointer.y >= 360 &&
      this.pointer.y <= 410;
    ctx.font = 'bold 12px "Microsoft JhengHei", sans-serif';
    ctx.fillStyle = btn1Hover ? 'rgb(46,204,113)' : 'rgb(39,174,96)';
    this.roundRect(400, 360, 70, 40, 8);
    ctx.fill();
    ctx.fillStyle = '#fff';
    ctx.fillText('重新挑戰', 435, 385);
    ctx.fillStyle = btn2Hover ? 'rgb(52,152,219)' : 'rgb(41,128,185)';
    this.roundRect(490, 360, 70, 40, 8);
    ctx.fill();
    ctx.fillText('選擇關卡', 525, 385);
    ctx.textAlign = 'left';
  }

  renderSubtitles() {
    if (!this.subtitles.length) return;
    const ctx = this.ctx;
    let y = SCREEN_HEIGHT - 70 - (this.subtitles.length - 1) * 26;
    ctx.textAlign = 'center';
    for (const sub of this.subtitles) {
      const alpha = sub.timer < 0.3 ? sub.timer / 0.3 : 1;
      ctx.font = 'bold 18px "Microsoft JhengHei", sans-serif';
      const w = ctx.measureText(sub.text).width + 24;
      ctx.fillStyle = `rgba(0,0,0,${0.6 * alpha})`;
      this.roundRect(SCREEN_WIDTH / 2 - w / 2, y - 14, w, 28, 6);
      ctx.fill();
      ctx.fillStyle = `rgba(255,255,255,${alpha})`;
      ctx.fillText(sub.text, SCREEN_WIDTH / 2, y + 4);
      y += 26;
    }
    ctx.textAlign = 'left';
  }

  roundRect(x, y, w, h, r) {
    const ctx = this.ctx;
    ctx.beginPath();
    ctx.moveTo(x + r, y);
    ctx.lineTo(x + w - r, y);
    ctx.quadraticCurveTo(x + w, y, x + w, y + r);
    ctx.lineTo(x + w, y + h - r);
    ctx.quadraticCurveTo(x + w, y + h, x + w - r, y + h);
    ctx.lineTo(x + r, y + h);
    ctx.quadraticCurveTo(x, y + h, x, y + h - r);
    ctx.lineTo(x, y + r);
    ctx.quadraticCurveTo(x, y, x + r, y);
    ctx.closePath();
  }
}

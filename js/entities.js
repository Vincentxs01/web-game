import { Vec2 } from './vec2.js';
import { PhysicsBody } from './physics.js';
import { assets } from './assets.js';
import { soundManager } from './sound.js';

export class Bird extends PhysicsBody {
  constructor(x, y, birdType = 'red') {
    const specs = {
      red: { mass: 1, restitution: 0.25, friction: 0.2, radius: 15 },
      yellow: { mass: 0.8, restitution: 0.15, friction: 0.2, radius: 14 },
      blue: { mass: 0.5, restitution: 0.3, friction: 0.1, radius: 10 },
      bomb: { mass: 3, restitution: 0.1, friction: 0.4, radius: 20 },
    };
    const s = specs[birdType] || specs.red;
    super(x, y, {
      shapeType: 'circle',
      mass: s.mass,
      restitution: s.restitution,
      friction: s.friction,
      radius: s.radius,
      category: 'bird',
      material: 'bird',
    });
    this.birdType = birdType;
    this.hasUsedAbility = false;
    this.isLaunched = false;
    this.launchTime = 0;
  }

  triggerAbility(physicsWorld) {
    if (this.hasUsedAbility || !this.isLaunched) return [];
    this.hasUsedAbility = true;
    const newBodies = [];

    if (this.birdType === 'yellow') {
      soundManager.play('boost');
      const len = this.vel.length();
      if (len > 1e-5) {
        this.vel.normalize().scale(1100);
      }
    } else if (this.birdType === 'blue') {
      soundManager.play('boost');
      let speed = this.vel.length();
      if (speed < 10) speed = 500;
      const angle = Math.atan2(this.vel.y, this.vel.x);
      const spread = 0.18;

      const birdUp = new Bird(this.pos.x, this.pos.y - 10, 'blue');
      birdUp.isLaunched = true;
      birdUp.hasUsedAbility = true;
      birdUp.launchTime = this.launchTime;
      birdUp.vel = new Vec2(
        Math.cos(angle - spread) * speed * 1.1,
        Math.sin(angle - spread) * speed * 1.1
      );

      const birdDown = new Bird(this.pos.x, this.pos.y + 10, 'blue');
      birdDown.isLaunched = true;
      birdDown.hasUsedAbility = true;
      birdDown.launchTime = this.launchTime;
      birdDown.vel = new Vec2(
        Math.cos(angle + spread) * speed * 1.1,
        Math.sin(angle + spread) * speed * 1.1
      );

      if (this.vel.length() > 1e-5) {
        this.vel.normalize().scale(speed * 1.1);
      }
      newBodies.push(birdUp, birdDown);
    } else if (this.birdType === 'bomb') {
      this.explode(physicsWorld);
    }
    return newBodies;
  }

  explode(physicsWorld) {
    soundManager.play('explosion');
    const explosionRadius = 160;
    const maxForce = 1200;

    for (const body of [...physicsWorld.bodies]) {
      if (body === this || body.isStatic) continue;
      const toBody = Vec2.sub(body.pos, this.pos);
      const dist = toBody.length();
      if (dist < explosionRadius) {
        const normal =
          dist > 0 ? toBody.clone().normalize() : new Vec2(0, -1);
        const factor = 1 - dist / explosionRadius;
        const pushForce = maxForce * factor;
        body.vel.x += normal.x * pushForce * body.invMass * 1.4;
        body.vel.y += normal.y * pushForce * body.invMass * 1.4;
        if (body.category === 'pig' || body.category === 'block') {
          body.takeDamage(pushForce * 0.9);
          physicsWorld.damageEvents.push({
            pos: body.pos.clone(),
            damage: pushForce * 0.9,
            destroyed: body.isDestroyed,
            body,
          });
        }
      }
    }
    this.isDestroyed = true;
  }

  draw(ctx, offset) {
    if (this.isDestroyed) return;
    const tex = assets.getTexture(
      `bird_${this.birdType}`,
      Math.round(this.radius * 2),
      Math.round(this.radius * 2)
    );
    const x = this.pos.x - this.radius - offset.x;
    const y = this.pos.y - this.radius - offset.y;
    if (this.vel.lengthSquared() > 100) {
      const angle = Math.atan2(-this.vel.y, this.vel.x);
      const clamped = Math.max(-0.78, Math.min(0.78, angle));
      ctx.save();
      ctx.translate(this.pos.x - offset.x, this.pos.y - offset.y);
      ctx.rotate(clamped);
      ctx.drawImage(tex, -this.radius, -this.radius);
      ctx.restore();
    } else {
      ctx.drawImage(tex, x, y);
    }
  }
}

export class Slingshot {
  constructor(x, y) {
    this.pos = new Vec2(x, y);
    this.forkLeft = new Vec2(x - 14, y - 48);
    this.forkRight = new Vec2(x + 14, y - 48);
    this.activeBird = null;
    this.isDragging = false;
    this.dragPos = new Vec2(x, y - 48);
    this.maxDragRadius = 70;
    this.launchForce = 16.5;
  }

  center() {
    return new Vec2(this.pos.x, this.pos.y - 48);
  }

  handlePointerDown(worldMouse) {
    if (!this.activeBird || this.activeBird.isLaunched) return false;
    const center = this.center();
    const distBird = Vec2.sub(worldMouse, this.activeBird.pos).length();
    const distCenter = Vec2.sub(worldMouse, center).length();
    if (distBird < 40 || distCenter < 35) {
      this.isDragging = true;
      this.dragPos.copy(worldMouse);
      return true;
    }
    return false;
  }

  handlePointerMove(worldMouse) {
    if (!this.isDragging || !this.activeBird) return;
    const center = this.center();
    const offset = Vec2.sub(worldMouse, center);
    if (offset.length() > this.maxDragRadius) {
      offset.normalize().scale(this.maxDragRadius);
      this.dragPos.set(center.x + offset.x, center.y + offset.y);
    } else {
      this.dragPos.copy(worldMouse);
    }
    this.activeBird.pos.copy(this.dragPos);
  }

  handlePointerUp() {
    if (!this.isDragging || !this.activeBird) return null;
    this.isDragging = false;
    const center = this.center();
    const launchVector = Vec2.sub(center, this.dragPos);
    if (launchVector.length() > 5) {
      this.activeBird.vel = launchVector.clone().scale(this.launchForce);
      this.activeBird.isLaunched = true;
      this.activeBird.launchTime = performance.now();
      soundManager.play('launch');
      const launched = this.activeBird;
      this.activeBird = null;
      return launched;
    }
    this.activeBird.pos.copy(center);
    return null;
  }

  drawDots(ctx, offset, gravityY) {
    if (!this.isDragging || !this.activeBird) return;
    const center = this.center();
    const launchVector = Vec2.sub(center, this.dragPos);
    const initialVel = launchVector.clone().scale(this.launchForce);
    let px = this.activeBird.pos.x;
    let py = this.activeBird.pos.y;
    let vx = initialVel.x;
    let vy = initialVel.y;
    const steps = 22;
    const simDt = 0.01;
    const drag = 0.03;

    for (let i = 1; i <= steps; i++) {
      for (let s = 0; s < 5; s++) {
        vy += gravityY * simDt;
        vx *= 1 - drag * simDt;
        vy *= 1 - drag * simDt;
        px += vx * simDt;
        py += vy * simDt;
      }
      const alpha = 1 - i / steps;
      const dotR = Math.max(1, Math.floor(4 * (1 - i / steps)));
      ctx.fillStyle = `rgba(255,255,255,${alpha})`;
      ctx.beginPath();
      ctx.arc(px - offset.x, py - offset.y, dotR, 0, Math.PI * 2);
      ctx.fill();
    }
  }

  drawRubber(ctx, offset, front) {
    if (!this.activeBird) return;
    const center = this.center();
    const bandColor = 'rgb(80,40,15)';
    if (this.isDragging) {
      const thickness = Math.max(
        2,
        Math.floor(8 - Vec2.sub(this.activeBird.pos, center).length() / 12)
      );
      ctx.strokeStyle = bandColor;
      ctx.lineWidth = thickness;
      ctx.lineCap = 'round';
      if (!front) {
        ctx.beginPath();
        ctx.moveTo(this.forkLeft.x - offset.x, this.forkLeft.y - offset.y);
        ctx.lineTo(
          this.activeBird.pos.x - offset.x,
          this.activeBird.pos.y - offset.y
        );
        ctx.stroke();
      } else {
        ctx.beginPath();
        ctx.moveTo(this.forkRight.x - offset.x, this.forkRight.y - offset.y);
        ctx.lineTo(
          this.activeBird.pos.x - offset.x,
          this.activeBird.pos.y - offset.y
        );
        ctx.stroke();
        ctx.fillStyle = 'rgb(50,25,5)';
        ctx.fillRect(
          this.activeBird.pos.x - 7 - offset.x,
          this.activeBird.pos.y - 4 - offset.y,
          14,
          8
        );
      }
    } else if (front) {
      ctx.strokeStyle = bandColor;
      ctx.lineWidth = 4;
      ctx.beginPath();
      ctx.moveTo(this.forkLeft.x - offset.x, this.forkLeft.y - offset.y);
      ctx.lineTo(this.forkRight.x - offset.x, this.forkRight.y - offset.y);
      ctx.stroke();
    }
  }

  drawBack(ctx, offset) {
    this.drawRubber(ctx, offset, false);
  }

  drawSlingshot(ctx, offset) {
    const tex = assets.getTexture('slingshot', 36, 100);
    ctx.drawImage(
      tex,
      this.pos.x - 18 - offset.x,
      this.pos.y - 100 - offset.y
    );
    this.drawRubber(ctx, offset, true);
  }
}

export class Particle {
  constructor(x, y, dx, dy, color, pType = 'rect', size = null, life = 1) {
    this.pos = new Vec2(x, y);
    this.vel = new Vec2(dx, dy);
    this.color = color;
    this.pType = pType;
    this.size = size ?? 4 + Math.floor(Math.random() * 4);
    this.life = life;
    this.maxLife = life;
    this.angle = Math.random() * 360;
    this.rotSpeed = Math.random() * 360 - 180;
  }

  update(dt) {
    this.vel.y += 350 * dt;
    const damp = 1 - 0.5 * dt;
    this.vel.x *= damp;
    this.vel.y *= damp;
    this.pos.x += this.vel.x * dt;
    this.pos.y += this.vel.y * dt;
    this.angle += this.rotSpeed * dt;
    this.life -= dt;
  }

  draw(ctx, offset) {
    const alpha = Math.max(0, Math.min(1, this.life / this.maxLife));
    const size = Math.max(1, Math.floor(this.size * (this.life / this.maxLife)));
    const x = this.pos.x - offset.x;
    const y = this.pos.y - offset.y;
    const [r, g, b] = this.color;
    ctx.save();
    ctx.globalAlpha = alpha;
    if (this.pType === 'smoke') {
      const smokeSize = Math.max(1, Math.floor(this.size * (2 - this.life / this.maxLife)));
      ctx.fillStyle = `rgba(${r},${g},${b},${alpha * 0.5})`;
      ctx.beginPath();
      ctx.arc(x, y, smokeSize, 0, Math.PI * 2);
      ctx.fill();
    } else if (this.pType === 'triangle') {
      ctx.fillStyle = `rgb(${r},${g},${b})`;
      ctx.translate(x, y);
      ctx.rotate((this.angle * Math.PI) / 180);
      ctx.beginPath();
      ctx.moveTo(0, -size);
      ctx.lineTo(-size, size);
      ctx.lineTo(size, size);
      ctx.closePath();
      ctx.fill();
    } else {
      ctx.fillStyle = `rgb(${r},${g},${b})`;
      ctx.beginPath();
      ctx.arc(x, y, size, 0, Math.PI * 2);
      ctx.fill();
    }
    ctx.restore();
  }
}

export class ParticleSystem {
  constructor() {
    this.particles = [];
  }

  spawnShards(x, y, material, count = 8) {
    const colors = {
      wood: [211, 137, 71],
      ice: [200, 240, 255],
      stone: [150, 150, 150],
      pig: [100, 230, 130],
    };
    const color = colors[material] || [255, 255, 255];
    const pType =
      material === 'wood' ? 'rect' : material === 'ice' ? 'triangle' : 'circle';
    for (let i = 0; i < count; i++) {
      const angle = Math.random() * Math.PI * 2;
      const speed = 50 + Math.random() * 200;
      this.particles.push(
        new Particle(
          x,
          y,
          Math.cos(angle) * speed,
          Math.sin(angle) * speed - 50 - Math.random() * 50,
          color,
          pType,
          4 + Math.floor(Math.random() * 6),
          0.5 + Math.random() * 0.4
        )
      );
    }
  }

  spawnSmoke(x, y, count = 10, radius = 20) {
    for (let i = 0; i < count; i++) {
      const angle = Math.random() * Math.PI * 2;
      const dist = Math.random() * radius;
      const px = x + Math.cos(angle) * dist;
      const py = y + Math.sin(angle) * dist;
      const speed = 10 + Math.random() * 70;
      this.particles.push(
        new Particle(
          px,
          py,
          Math.cos(angle) * speed,
          Math.sin(angle) * speed - 20,
          [220, 220, 220],
          'smoke',
          8 + Math.floor(Math.random() * 12),
          0.6 + Math.random() * 0.6
        )
      );
    }
  }

  update(dt) {
    for (let i = this.particles.length - 1; i >= 0; i--) {
      this.particles[i].update(dt);
      if (this.particles[i].life <= 0) this.particles.splice(i, 1);
    }
  }

  draw(ctx, offset) {
    for (const p of this.particles) p.draw(ctx, offset);
  }
}

export class FloatingText {
  constructor(x, y, text, color = [255, 255, 255], size = 24) {
    this.pos = new Vec2(x, y);
    this.vel = new Vec2(Math.random() * 40 - 20, -80);
    this.text = text;
    this.color = color;
    this.size = size;
    this.life = 1;
  }

  update(dt) {
    this.pos.x += this.vel.x * dt;
    this.pos.y += this.vel.y * dt;
    this.vel.x *= 1 - 0.8 * dt;
    this.vel.y *= 1 - 0.8 * dt;
    this.life -= dt;
  }

  draw(ctx, offset) {
    const alpha = Math.max(0, Math.min(1, this.life));
    ctx.save();
    ctx.globalAlpha = alpha;
    ctx.font = `bold ${this.size}px "Comic Sans MS", "Microsoft JhengHei", sans-serif`;
    ctx.fillStyle = `rgb(${this.color[0]},${this.color[1]},${this.color[2]})`;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(this.text, this.pos.x - offset.x, this.pos.y - offset.y);
    ctx.restore();
  }
}

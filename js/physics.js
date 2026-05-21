import { Vec2 } from './vec2.js';

export class PhysicsBody {
  constructor(x, y, opts = {}) {
    const {
      shapeType = 'circle',
      mass = 1,
      isStatic = false,
      restitution = 0.2,
      friction = 0.3,
      radius = 15,
      width = 30,
      height = 30,
      maxHealth = 100,
      category = 'block',
      material = 'wood',
    } = opts;

    this.pos = new Vec2(x, y);
    this.vel = new Vec2(0, 0);
    this.shapeType = shapeType;
    this.isStatic = isStatic;
    this.restitution = restitution;
    this.friction = friction;
    this.radius = radius;
    this.width = width;
    this.height = height;
    this.maxHealth = maxHealth;
    this.health = maxHealth;
    this.isDestroyed = false;
    this.category = category;
    this.material = material;
    this.trail = [];
    this.pigType = opts.pigType;
    this.scoreValue = category === 'block' ? 100 : category === 'pig' ? 500 : 0;

    if (isStatic) {
      this.mass = Infinity;
      this.invMass = 0;
    } else {
      this.mass = mass;
      this.invMass = 1 / mass;
    }
  }

  takeDamage(amount) {
    if (this.isStatic || this.isDestroyed) return false;
    this.health -= amount;
    if (this.health <= 0) {
      this.isDestroyed = true;
      return true;
    }
    return false;
  }
}

function checkCircleCircle(c1, c2) {
  const d = Vec2.sub(c2.pos, c1.pos);
  const dist = d.length();
  const minDist = c1.radius + c2.radius;
  if (dist >= minDist) return { collided: false };
  if (dist === 0) return { collided: true, normal: new Vec2(0, 1), penetration: minDist };
  const normal = d.clone().normalize();
  return { collided: true, normal, penetration: minDist - dist };
}

function checkRectRect(a, b) {
  const d = Vec2.sub(b.pos, a.pos);
  const hwA = a.width / 2;
  const hwB = b.width / 2;
  const overlapX = hwA + hwB - Math.abs(d.x);
  if (overlapX <= 0) return { collided: false };

  const hhA = a.height / 2;
  const hhB = b.height / 2;
  const overlapY = hhA + hhB - Math.abs(d.y);
  if (overlapY <= 0) return { collided: false };

  if (overlapX < overlapY) {
    return {
      collided: true,
      normal: new Vec2(d.x > 0 ? 1 : -1, 0),
      penetration: overlapX,
    };
  }
  return {
    collided: true,
    normal: new Vec2(0, d.y > 0 ? 1 : -1),
    penetration: overlapY,
  };
}

function checkCircleRect(c, r) {
  const d = Vec2.sub(c.pos, r.pos);
  const hw = r.width / 2;
  const hh = r.height / 2;
  const cx = Math.max(-hw, Math.min(hw, d.x));
  const cy = Math.max(-hh, Math.min(hh, d.y));
  const closest = new Vec2(r.pos.x + cx, r.pos.y + cy);
  const toCircle = Vec2.sub(c.pos, closest);
  const dist = toCircle.length();

  if (dist < c.radius && dist > 0) {
    const normal = toCircle.clone().normalize();
    return { collided: true, normal, penetration: c.radius - dist };
  }
  if (dist === 0) {
    const dxL = d.x + hw;
    const dxR = hw - d.x;
    const dyT = d.y + hh;
    const dyB = hh - d.y;
    const minD = Math.min(dxL, dxR, dyT, dyB);
    let normal;
    if (minD === dxL) normal = new Vec2(-1, 0);
    else if (minD === dxR) normal = new Vec2(1, 0);
    else if (minD === dyT) normal = new Vec2(0, -1);
    else normal = new Vec2(0, 1);
    return { collided: true, normal, penetration: c.radius + minD };
  }
  return { collided: false };
}

function checkCollision(a, b) {
  if (a.shapeType === 'circle' && b.shapeType === 'circle') {
    return checkCircleCircle(a, b);
  }
  if (a.shapeType === 'rect' && b.shapeType === 'rect') {
    return checkRectRect(a, b);
  }
  if (a.shapeType === 'circle' && b.shapeType === 'rect') {
    const r = checkCircleRect(a, b);
    if (r.collided) {
      r.normal = r.normal.clone().scale(-1);
    }
    return r;
  }
  if (a.shapeType === 'rect' && b.shapeType === 'circle') {
    return checkCircleRect(b, a);
  }
  return { collided: false };
}

export class PhysicsWorld {
  constructor(gravityY = 1150) {
    this.bodies = [];
    this.gravity = new Vec2(0, gravityY);
    this.substeps = 6;
    this.damageEvents = [];
    this.impactSounds = [];
  }

  addBody(body) {
    this.bodies.push(body);
  }

  removeBody(body) {
    const i = this.bodies.indexOf(body);
    if (i >= 0) this.bodies.splice(i, 1);
  }

  clear() {
    this.bodies = [];
    this.damageEvents = [];
    this.impactSounds = [];
  }

  update(dt) {
    this.damageEvents = [];
    this.impactSounds = [];
    dt = Math.min(dt, 0.03);
    const subDt = dt / this.substeps;

    for (let step = 0; step < this.substeps; step++) {
      for (const body of this.bodies) {
        if (body.isStatic) continue;
        if (body.category === 'bird' && !body.isLaunched) continue;
        body.vel.y += this.gravity.y * subDt;
        const drag = body.category === 'bird' ? 0.03 : 0.15;
        const dragFactor = 1 - drag * subDt;
        body.vel.x *= dragFactor;
        body.vel.y *= dragFactor;
        body.pos.x += body.vel.x * subDt;
        body.pos.y += body.vel.y * subDt;
      }

      for (let i = 0; i < this.bodies.length; i++) {
        for (let j = i + 1; j < this.bodies.length; j++) {
          const a = this.bodies[i];
          const b = this.bodies[j];
          if (a.category === 'bird' && !a.isLaunched) continue;
          if (b.category === 'bird' && !b.isLaunched) continue;
          if (a.isStatic && b.isStatic) continue;

          const { collided, normal, penetration } = checkCollision(a, b);
          if (collided) {
            this.resolveCollision(a, b, normal, penetration);
          }
        }
      }
    }

    const destroyed = this.bodies.filter((b) => b.isDestroyed);
    for (const b of destroyed) this.removeBody(b);
  }

  resolveCollision(a, b, normal, penetration) {
    let rv = Vec2.sub(b.vel, a.vel);
    let velAlongNormal = rv.dot(normal);
    if (velAlongNormal > 0) return;

    const e = Math.min(a.restitution, b.restitution);
    const totalInvMass = a.invMass + b.invMass;
    if (totalInvMass === 0) return;

    let j = (-(1 + e) * velAlongNormal) / totalInvMass;
    a.vel.x -= a.invMass * j * normal.x;
    a.vel.y -= a.invMass * j * normal.y;
    b.vel.x += b.invMass * j * normal.x;
    b.vel.y += b.invMass * j * normal.y;

    rv = Vec2.sub(b.vel, a.vel);
    const rvDotN = rv.dot(normal);
    let tangent = new Vec2(rv.x - rvDotN * normal.x, rv.y - rvDotN * normal.y);
    if (tangent.lengthSquared() > 1e-5) {
      tangent.normalize();
      let jt = -rv.dot(tangent) / totalInvMass;
      const mu = Math.sqrt(a.friction * b.friction);
      const maxJt = j * mu;
      jt = Math.max(-maxJt, Math.min(maxJt, jt));
      a.vel.x -= a.invMass * jt * tangent.x;
      a.vel.y -= a.invMass * jt * tangent.y;
      b.vel.x += b.invMass * jt * tangent.x;
      b.vel.y += b.invMass * jt * tangent.y;
    }

    const percent = 0.5;
    const slop = 0.02;
    const correctionMag =
      (Math.max(penetration - slop, 0) / totalInvMass) * percent;
    if (!a.isStatic) {
      a.pos.x -= a.invMass * correctionMag * normal.x;
      a.pos.y -= a.invMass * correctionMag * normal.y;
    }
    if (!b.isStatic) {
      b.pos.x += b.invMass * correctionMag * normal.x;
      b.pos.y += b.invMass * correctionMag * normal.y;
    }

    const impactEnergy = j;
    const thresholdMap = {
      wood: 65,
      ice: 20,
      stone: 160,
      pig: 15,
      bird: 9999,
    };
    const damageScaleMap = {
      wood: 0.45,
      ice: 0.9,
      stone: 0.25,
      pig: 1.5,
      bird: 0,
    };

    if (impactEnergy > 60) {
      const mats = [a.material, b.material];
      let soundType = null;
      if (mats.includes('stone')) soundType = 'stone_impact';
      else if (mats.some((m) => ['wood', 'pig', 'bird'].includes(m)))
        soundType = 'wood_impact';
      else if (mats.includes('ice')) soundType = 'ice_impact';
      if (soundType && !this.impactSounds.includes(soundType)) {
        this.impactSounds.push(soundType);
      }
    }

    for (const body of [a, b]) {
      if (body.isStatic || body.category === 'bird') continue;
      const mat = body.category === 'block' ? body.material : 'pig';
      const thresh = thresholdMap[mat] ?? 50;
      if (impactEnergy > thresh) {
        let damage =
          (impactEnergy - thresh) * (damageScaleMap[mat] ?? 0.5);
        damage *= 0.8 + 0.4 * Math.sin(impactEnergy);
        if (!body.isDestroyed) {
          body.takeDamage(damage);
          this.damageEvents.push({
            pos: body.pos.clone(),
            damage,
            destroyed: body.isDestroyed,
            body,
          });
        }
      }
    }
  }
}

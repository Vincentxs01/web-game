const COLORS = {
  skyTop: [116, 185, 255],
  skyBottom: [250, 240, 230],
  hillFar: [168, 218, 220],
  hillMid: [120, 224, 143],
  hillNear: [95, 226, 156],
  wood: [196, 120, 56],
  woodDark: [139, 69, 19],
  ice: [173, 232, 244],
  iceShine: [224, 251, 252],
  stone: [127, 143, 166],
  stoneDark: [87, 101, 116],
};

function lerpColor(c1, c2, t) {
  return [
    Math.round(c1[0] * (1 - t) + c2[0] * t),
    Math.round(c1[1] * (1 - t) + c2[1] * t),
    Math.round(c1[2] * (1 - t) + c2[2] * t),
  ];
}

function rgb(c, a = 1) {
  return a < 1 ? `rgba(${c[0]},${c[1]},${c[2]},${a})` : `rgb(${c[0]},${c[1]},${c[2]})`;
}

function seededRandom(seed) {
  let s = seed;
  return () => {
    s = (s * 9301 + 49297) % 233280;
    return s / 233280;
  };
}

class AssetLibrary {
  constructor() {
    this.textures = new Map();
  }

  key(name, w, h, material) {
    return `${name}|${w}|${h}|${material}`;
  }

  getTexture(name, w = 0, h = 0, material = 'wood') {
    const k = this.key(name, w, h, material);
    if (this.textures.has(k)) return this.textures.get(k);

    let canvas;
    switch (name) {
      case 'sky':
        canvas = this.createSky(w, h);
        break;
      case 'hill':
        canvas = this.createHill(w, h, material);
        break;
      case 'cloud':
        canvas = this.createCloud(w, h);
        break;
      case 'block':
        canvas = this.createBlock(w, h, material);
        break;
      case 'bird_red':
        canvas = this.createRedBird(w);
        break;
      case 'bird_yellow':
        canvas = this.createYellowBird(w);
        break;
      case 'bird_blue':
        canvas = this.createBlueBird(w);
        break;
      case 'bird_bomb':
        canvas = this.createBombBird(w);
        break;
      case 'pig_minion':
        canvas = this.createMinionPig(w);
        break;
      case 'pig_helmet':
        canvas = this.createHelmetPig(w);
        break;
      case 'pig_king':
        canvas = this.createKingPig(w);
        break;
      case 'slingshot':
        canvas = this.createSlingshot(w, h);
        break;
      default: {
        canvas = document.createElement('canvas');
        canvas.width = w || 32;
        canvas.height = h || 32;
        const ctx = canvas.getContext('2d');
        ctx.fillStyle = '#ff00ff';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
      }
    }
    this.textures.set(k, canvas);
    return canvas;
  }

  createSky(w, h) {
    const c = document.createElement('canvas');
    c.width = w;
    c.height = h;
    const ctx = c.getContext('2d');
    for (let y = 0; y < h; y++) {
      const ratio = y / h;
      const col = lerpColor(COLORS.skyTop, COLORS.skyBottom, ratio);
      ctx.fillStyle = rgb(col);
      ctx.fillRect(0, y, w, 1);
    }
    const sunX = w - 150;
    const sunY = 100;
    for (const [r, a] of [
      [85, 0.08],
      [65, 0.16],
      [45, 0.3],
    ]) {
      ctx.beginPath();
      ctx.fillStyle = `rgba(255,253,220,${a})`;
      ctx.arc(sunX, sunY, r, 0, Math.PI * 2);
      ctx.fill();
    }
    ctx.beginPath();
    ctx.fillStyle = 'rgb(255,245,190)';
    ctx.arc(sunX, sunY, 30, 0, Math.PI * 2);
    ctx.fill();
    return c;
  }

  createHill(w, h, hillType) {
    const c = document.createElement('canvas');
    c.width = w;
    c.height = h;
    const ctx = c.getContext('2d');
    let color = COLORS.hillFar;
    let amplitude = 40;
    let frequency = 0.003;
    let yOffset = h * 0.1;

    if (hillType === 'mid') {
      color = COLORS.hillMid;
      amplitude = 25;
      frequency = 0.006;
      yOffset = h * 0.3;
    } else if (hillType === 'near') {
      color = COLORS.hillNear;
      amplitude = 15;
      frequency = 0.012;
      yOffset = h * 0.5;
    }

    const points = [[0, h]];
    for (let x = 0; x <= w + 10; x += 10) {
      const y =
        h -
        (yOffset +
          amplitude * Math.sin(x * frequency) +
          (amplitude / 3) * Math.sin(x * frequency * 2.3));
      points.push([x, y]);
    }
    points.push([w, h]);
    ctx.fillStyle = rgb(color);
    ctx.beginPath();
    ctx.moveTo(points[0][0], points[0][1]);
    for (let i = 1; i < points.length; i++) ctx.lineTo(points[i][0], points[i][1]);
    ctx.closePath();
    ctx.fill();

    const rand = seededRandom(hillType.charCodeAt(0) + hillType.length);
    if (hillType === 'near') {
      for (let x = 20; x < w; x += 35) {
        const baseY =
          h -
          (yOffset +
            amplitude * Math.sin(x * frequency) +
            (amplitude / 3) * Math.sin(x * frequency * 2.3));
        ctx.strokeStyle = 'rgb(46,204,113)';
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.moveTo(x, baseY);
        ctx.lineTo(x - 4, baseY - 9);
        ctx.moveTo(x, baseY);
        ctx.lineTo(x, baseY - 11);
        ctx.moveTo(x, baseY);
        ctx.lineTo(x + 4, baseY - 9);
        ctx.stroke();
        if (rand() < 0.3) {
          const fx = x + 10;
          const flowerY = baseY - 4;
          ctx.strokeStyle = 'rgb(46,204,113)';
          ctx.beginPath();
          ctx.moveTo(fx, baseY);
          ctx.lineTo(fx, flowerY);
          ctx.stroke();
          const petal = rand() < 0.33 ? [255, 116, 185] : rand() < 0.66 ? [254, 202, 87] : [255, 159, 243];
          ctx.fillStyle = rgb(petal);
          for (const [ox, oy] of [
            [-2, 0],
            [2, 0],
            [0, -2],
            [0, 2],
          ]) {
            ctx.beginPath();
            ctx.arc(fx + ox, flowerY + oy, 2, 0, Math.PI * 2);
            ctx.fill();
          }
        }
      }
    }
    return c;
  }

  createCloud(w, h) {
    const c = document.createElement('canvas');
    c.width = w;
    c.height = h;
    const ctx = c.getContext('2d');
    const rBase = Math.floor(h / 3);
    const drawBlob = (cx, cy, r, color) => {
      ctx.fillStyle = color;
      ctx.beginPath();
      ctx.arc(cx, cy, r, 0, Math.PI * 2);
      ctx.fill();
    };
    drawBlob(w / 3, h / 2 + 3, rBase * 1.2, 'rgba(200,214,229,0.5)');
    drawBlob(w / 2, h / 2 - 2, rBase * 1.5, 'rgba(200,214,229,0.5)');
    drawBlob((2 * w) / 3, h / 2 + 3, rBase * 1.1, 'rgba(200,214,229,0.5)');
    ctx.fillStyle = 'rgba(255,255,255,0.86)';
    ctx.beginPath();
    ctx.ellipse(w / 2, h - rBase, (w - rBase * 2) / 2, rBase, 0, 0, Math.PI * 2);
    ctx.fill();
    drawBlob(w / 3, h / 2, rBase * 1.2, 'rgba(255,255,255,0.86)');
    drawBlob(w / 2, h / 2 - 5, rBase * 1.5, 'rgba(255,255,255,0.86)');
    drawBlob((2 * w) / 3, h / 2, rBase * 1.1, 'rgba(255,255,255,0.86)');
    drawBlob(w / 2, h / 2 - 8, rBase, 'rgba(255,255,255,0.96)');
    return c;
  }

  createBlock(w, h, material) {
    const c = document.createElement('canvas');
    c.width = w;
    c.height = h;
    const ctx = c.getContext('2d');
    const rand = seededRandom(w * h + material.length);

    if (material === 'wood') {
      ctx.fillStyle = rgb(COLORS.wood);
      ctx.fillRect(0, 0, w, h);
      ctx.strokeStyle = rgb(COLORS.woodDark);
      ctx.lineWidth = 3;
      ctx.strokeRect(1.5, 1.5, w - 3, h - 3);
      for (let i = 1; i < 4; i++) {
        const ly = Math.floor(h * (i / 4));
        ctx.beginPath();
        ctx.moveTo(4, ly);
        ctx.lineTo(w - 4, ly);
        ctx.stroke();
      }
    } else if (material === 'ice') {
      ctx.fillStyle = 'rgba(173,232,244,0.7)';
      ctx.fillRect(0, 0, w, h);
      ctx.strokeStyle = rgb(COLORS.iceShine);
      ctx.lineWidth = 2;
      ctx.strokeRect(1, 1, w - 2, h - 2);
      for (let i = 0; i < 3; i++) {
        const x1 = 4 + Math.floor(rand() * (w - 8));
        const y1 = 4 + Math.floor(rand() * (h - 8));
        ctx.strokeStyle = 'rgba(255,255,255,0.8)';
        ctx.beginPath();
        ctx.moveTo(x1, y1);
        ctx.lineTo(
          Math.max(4, Math.min(w - 4, x1 + rand() * 30 - 15)),
          Math.max(4, Math.min(h - 4, y1 + rand() * 30 - 15))
        );
        ctx.stroke();
      }
    } else {
      ctx.fillStyle = rgb(COLORS.stone);
      ctx.fillRect(0, 0, w, h);
      ctx.strokeStyle = rgb(COLORS.stoneDark);
      ctx.lineWidth = 3;
      ctx.strokeRect(1.5, 1.5, w - 3, h - 3);
    }
    return c;
  }

  createRedBird(d) {
    const c = document.createElement('canvas');
    c.width = d;
    c.height = d;
    const ctx = c.getContext('2d');
    const r = d / 2;
    ctx.fillStyle = 'rgb(231,76,60)';
    ctx.beginPath();
    ctx.arc(r, r, r - 2, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = 'rgb(245,246,250)';
    ctx.beginPath();
    ctx.arc(r, r + 4, r - 5, 0, Math.PI);
    ctx.fill();
    ctx.fillStyle = '#fff';
    ctx.beginPath();
    ctx.arc(r + 1, r - 3, 5, 0, Math.PI * 2);
    ctx.arc(r + 8, r - 3, 5, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = '#000';
    ctx.beginPath();
    ctx.arc(r + 2, r - 3, 2, 0, Math.PI * 2);
    ctx.arc(r + 8, r - 3, 2, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = 'rgb(241,196,15)';
    ctx.beginPath();
    ctx.moveTo(r + 2, r + 1);
    ctx.lineTo(r + 13, r + 4);
    ctx.lineTo(r + 2, r + 7);
    ctx.fill();
    return c;
  }

  createYellowBird(d) {
    const c = document.createElement('canvas');
    c.width = d;
    c.height = d;
    const ctx = c.getContext('2d');
    const r = d / 2;
    ctx.fillStyle = 'rgb(241,196,15)';
    ctx.beginPath();
    ctx.moveTo(r, 4);
    ctx.lineTo(2, d - 3);
    ctx.lineTo(d - 2, d - 3);
    ctx.closePath();
    ctx.fill();
    ctx.fillStyle = '#fff';
    ctx.beginPath();
    ctx.arc(r - 2, r + 1, 4, 0, Math.PI * 2);
    ctx.arc(r + 4, r + 1, 4, 0, Math.PI * 2);
    ctx.fill();
    return c;
  }

  createBlueBird(d) {
    const c = document.createElement('canvas');
    c.width = d;
    c.height = d;
    const ctx = c.getContext('2d');
    const r = d / 2;
    ctx.fillStyle = 'rgb(52,152,219)';
    ctx.beginPath();
    ctx.arc(r, r, r - 1, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = 'rgb(241,196,15)';
    ctx.beginPath();
    ctx.moveTo(r, r);
    ctx.lineTo(r + 6, r + 2);
    ctx.lineTo(r, r + 4);
    ctx.fill();
    return c;
  }

  createBombBird(d) {
    const c = document.createElement('canvas');
    c.width = d;
    c.height = d;
    const ctx = c.getContext('2d');
    const r = d / 2;
    ctx.fillStyle = 'rgb(44,62,80)';
    ctx.beginPath();
    ctx.arc(r, r, r - 2, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = 'rgb(241,196,15)';
    ctx.beginPath();
    ctx.arc(r, 2, 3, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = 'rgb(241,196,15)';
    ctx.beginPath();
    ctx.moveTo(r - 2, r + 2);
    ctx.lineTo(r + 9, r + 5);
    ctx.lineTo(r - 2, r + 10);
    ctx.fill();
    return c;
  }

  createMinionPig(d) {
    const c = document.createElement('canvas');
    c.width = d;
    c.height = d;
    const ctx = c.getContext('2d');
    const r = d / 2;
    ctx.fillStyle = 'rgb(46,204,113)';
    ctx.beginPath();
    ctx.arc(r, r, r - 2, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = 'rgb(39,174,96)';
    ctx.beginPath();
    ctx.ellipse(r, r, 6, 4, 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = '#fff';
    ctx.beginPath();
    ctx.arc(r - 6, r - 4, 5, 0, Math.PI * 2);
    ctx.arc(r + 6, r - 4, 5, 0, Math.PI * 2);
    ctx.fill();
    ctx.strokeStyle = 'rgb(39,174,96)';
    ctx.beginPath();
    ctx.arc(r, r + 6, 6, Math.PI, 0);
    ctx.stroke();
    return c;
  }

  createHelmetPig(d) {
    const c = this.createMinionPig(d);
    const ctx = c.getContext('2d');
    const r = d / 2;
    ctx.strokeStyle = 'rgb(149,165,166)';
    ctx.lineWidth = Math.max(2, r / 4);
    ctx.beginPath();
    ctx.arc(r, r - 4, r - 2, Math.PI * 0.1, Math.PI * 0.9);
    ctx.stroke();
    return c;
  }

  createKingPig(d) {
    const c = this.createMinionPig(d);
    const ctx = c.getContext('2d');
    const r = d / 2;
    ctx.fillStyle = 'rgb(241,196,15)';
    ctx.fillRect(r - 10, r - 12, 20, 4);
    ctx.beginPath();
    ctx.moveTo(r - 10, r - 12);
    ctx.lineTo(r - 8, r - 22);
    ctx.lineTo(r - 3, r - 12);
    ctx.fill();
    ctx.beginPath();
    ctx.moveTo(r, r - 12);
    ctx.lineTo(r, r - 26);
    ctx.lineTo(r + 5, r - 12);
    ctx.fill();
    return c;
  }

  createSlingshot(w, h) {
    const c = document.createElement('canvas');
    c.width = w;
    c.height = h;
    const ctx = c.getContext('2d');
    ctx.fillStyle = 'rgb(110,70,30)';
    ctx.fillRect(w / 2 - 4, h / 2, 8, h / 2);
    ctx.beginPath();
    ctx.moveTo(w / 2 - 4, h / 2 + 2);
    ctx.lineTo(w - 2, 2);
    ctx.lineTo(w - 10, 0);
    ctx.lineTo(w / 2 + 4, h / 2 + 2);
    ctx.lineTo(2, 2);
    ctx.lineTo(10, 0);
    ctx.closePath();
    ctx.fill();
    return c;
  }

  drawBlockWithCracks(ctx, body, offset) {
    const w = Math.round(body.width);
    const h = Math.round(body.height);
    const tex = this.getTexture('block', w, h, body.material);
    const x = body.pos.x - w / 2 - offset.x;
    const y = body.pos.y - h / 2 - offset.y;
    ctx.drawImage(tex, x, y);

    const ratio = body.health / body.maxHealth;
    if (ratio < 0.7) {
      const num = ratio > 0.4 ? 1 : 3;
      const rand = seededRandom(Math.floor(body.pos.x + body.pos.y));
      ctx.strokeStyle = 'rgb(40,30,20)';
      ctx.lineWidth = ratio > 0.4 ? 1 : 2;
      for (let i = 0; i < num; i++) {
        const cx1 = 3 + Math.floor(rand() * (w - 6));
        const cy1 = 3 + Math.floor(rand() * (h - 6));
        let cx2 = cx1 + Math.floor(rand() * 30 - 15);
        let cy2 = cy1 + Math.floor(rand() * 30 - 15);
        cx2 = Math.max(3, Math.min(w - 3, cx2));
        cy2 = Math.max(3, Math.min(h - 3, cy2));
        ctx.beginPath();
        ctx.moveTo(x + cx1, y + cy1);
        ctx.lineTo(x + cx2, y + cy2);
        ctx.stroke();
      }
    }
  }

  drawPig(ctx, body, offset) {
    const diameter = Math.round(body.radius * 2);
    const ratio = body.health / body.maxHealth;
    let texName = `pig_${body.pigType}`;
    if (body.pigType === 'helmet' && ratio < 0.4) texName = 'pig_minion';
    if (body.pigType === 'king' && ratio < 0.4) texName = 'pig_minion';
    const tex = this.getTexture(texName, diameter, diameter);
    const x = body.pos.x - body.radius - offset.x;
    const y = body.pos.y - body.radius - offset.y;
    ctx.drawImage(tex, x, y);

    if (ratio < 0.7) {
      const r = body.radius;
      const eyeY = y + r - 4;
      if (ratio >= 0.4) {
        ctx.fillStyle = 'rgba(100,120,220,0.45)';
        ctx.beginPath();
        ctx.arc(x + r - 10, eyeY - 4, 5, 0, Math.PI * 2);
        ctx.fill();
      } else {
        ctx.strokeStyle = '#000';
        ctx.lineWidth = 2;
        for (const ox of [-9, 3]) {
          ctx.beginPath();
          ctx.moveTo(x + r + ox, eyeY - 2);
          ctx.lineTo(x + r + ox + 6, eyeY + 2);
          ctx.moveTo(x + r + ox + 6, eyeY - 2);
          ctx.lineTo(x + r + ox, eyeY + 2);
          ctx.stroke();
        }
      }
    }
  }
}

export const assets = new AssetLibrary();

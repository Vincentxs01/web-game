const SAMPLE_RATE = 44100;

function lowPassNoise(numSamples, alpha = 0.15) {
  const samples = [];
  let prev = 0;
  const scale = alpha > 0 ? Math.sqrt((2 - alpha) / alpha) : 1;
  for (let i = 0; i < numSamples; i++) {
    const white = Math.random() * 2 - 1;
    const filtered = alpha * white + (1 - alpha) * prev;
    prev = filtered;
    samples.push(filtered * scale);
  }
  return samples;
}

function makeBuffer(ctx, generator) {
  const duration = generator.duration;
  const numSamples = Math.floor(SAMPLE_RATE * duration);
  const samples = generator.build(numSamples);
  const buffer = ctx.createBuffer(1, numSamples, SAMPLE_RATE);
  const data = buffer.getChannelData(0);
  for (let i = 0; i < numSamples; i++) {
    data[i] = Math.max(-1, Math.min(1, samples[i]));
  }
  return buffer;
}

const SOUND_DEFS = {
  launch: {
    duration: 0.25,
    build(n) {
      const out = [];
      const dur = 0.25;
      const f1 = 250;
      const f2 = 750;
      for (let i = 0; i < n; i++) {
        const t = i / SAMPLE_RATE;
        const phase = 2 * Math.PI * (f1 * t + ((f2 - f1) * t * t) / (2 * dur));
        const envelope = Math.sin((Math.PI * t) / dur);
        out.push(Math.sin(phase) * envelope * 0.5);
      }
      return out;
    },
  },
  boost: {
    duration: 0.18,
    build(n) {
      const out = [];
      const dur = 0.18;
      const f1 = 450;
      const f2 = 1350;
      for (let i = 0; i < n; i++) {
        const t = i / SAMPLE_RATE;
        const phase = 2 * Math.PI * (f1 * t + ((f2 - f1) * t * t) / (2 * dur));
        const envelope = Math.exp((-3 * t) / dur) * Math.sin((Math.PI * t) / dur);
        out.push(Math.sin(phase) * envelope * 0.6);
      }
      return out;
    },
  },
  wood_impact: {
    duration: 0.15,
    build(n) {
      const out = [];
      const dur = 0.15;
      const noise = lowPassNoise(n, 0.1);
      const f1 = 180;
      const f2 = 60;
      for (let i = 0; i < n; i++) {
        const t = i / SAMPLE_RATE;
        const phase = 2 * Math.PI * (f1 * t + ((f2 - f1) * t * t) / (2 * dur));
        const mixed = 0.8 * Math.sin(phase) + 0.2 * noise[i];
        out.push(mixed * Math.exp(-8 * t) * 0.7);
      }
      return out;
    },
  },
  ice_impact: {
    duration: 0.08,
    build(n) {
      const out = [];
      const dur = 0.08;
      const f1 = 1800;
      const f2 = 1200;
      for (let i = 0; i < n; i++) {
        const t = i / SAMPLE_RATE;
        const phase = 2 * Math.PI * (f1 * t + ((f2 - f1) * t * t) / (2 * dur));
        const sine = Math.sin(phase);
        const harm = Math.sin(2 * phase) * 0.3;
        out.push((sine + harm) * Math.exp(-25 * t) * 0.5);
      }
      return out;
    },
  },
  stone_impact: {
    duration: 0.25,
    build(n) {
      const out = [];
      const dur = 0.25;
      const noise = lowPassNoise(n, 0.08);
      const f1 = 100;
      const f2 = 45;
      for (let i = 0; i < n; i++) {
        const t = i / SAMPLE_RATE;
        const phase = 2 * Math.PI * (f1 * t + ((f2 - f1) * t * t) / (2 * dur));
        const mixed = 0.7 * Math.sin(phase) + 0.3 * noise[i];
        out.push(mixed * Math.exp(-12 * t) * 0.8);
      }
      return out;
    },
  },
  pig_pop: {
    duration: 0.15,
    build(n) {
      const out = [];
      const dur = 0.15;
      for (let i = 0; i < n; i++) {
        const t = i / SAMPLE_RATE;
        const f = 350 + 450 * Math.sin((Math.PI * t) / dur);
        const phase = 2 * Math.PI * f * t;
        const envelope = Math.sin((Math.PI * t) / dur) * Math.exp(-2 * t);
        out.push(Math.sin(phase) * envelope * 0.6);
      }
      return out;
    },
  },
  explosion: {
    duration: 0.6,
    build(n) {
      const out = [];
      const noise = lowPassNoise(n, 0.2);
      for (let i = 0; i < n; i++) {
        const t = i / SAMPLE_RATE;
        const rumble = Math.sin(2 * Math.PI * 50 * t) * 0.5;
        const mixed = 0.3 * rumble + 0.7 * noise[i];
        out.push(mixed * Math.exp(-7 * t) * 0.9);
      }
      return out;
    },
  },
  victory: {
    duration: 0.78,
    build(n) {
      const notes = [523.25, 659.25, 784, 1046.5];
      const noteDur = 0.12;
      const out = [];
      for (const noteF of notes) {
        const noteN = Math.floor(SAMPLE_RATE * noteDur);
        for (let i = 0; i < noteN; i++) {
          const t = i / SAMPLE_RATE;
          const envelope = Math.sin((Math.PI * t) / noteDur) * 0.4;
          out.push(Math.sin(2 * Math.PI * noteF * t) * envelope);
        }
      }
      const tailN = Math.floor(SAMPLE_RATE * 0.3);
      for (let i = 0; i < tailN; i++) {
        const t = i / SAMPLE_RATE;
        out.push(Math.sin(2 * Math.PI * notes[3] * t) * Math.exp(-5 * t) * 0.4);
      }
      while (out.length < n) out.push(0);
      return out.slice(0, n);
    },
  },
  defeat: {
    duration: 1,
    build(n) {
      const notes = [392, 311.13, 261.63];
      const noteDur = 0.2;
      const out = [];
      for (const noteF of notes) {
        const noteN = Math.floor(SAMPLE_RATE * noteDur);
        for (let i = 0; i < noteN; i++) {
          const t = i / SAMPLE_RATE;
          const envelope = Math.sin((Math.PI * t) / noteDur) * 0.4;
          out.push(Math.sin(2 * Math.PI * noteF * t) * envelope);
        }
      }
      const tailN = Math.floor(SAMPLE_RATE * 0.4);
      for (let i = 0; i < tailN; i++) {
        const t = i / SAMPLE_RATE;
        out.push(Math.sin(2 * Math.PI * notes[2] * t) * Math.exp(-3 * t) * 0.4);
      }
      while (out.length < n) out.push(0);
      return out.slice(0, n);
    },
  },
};

class SoundManager {
  constructor() {
    this.ctx = null;
    this.buffers = {};
    this.bgmBuffer = null;
    this.enabled = true;
    this.subtitleCallback = null;
    this.lastPlayed = {};
    this.bgmSource = null;
    this.bgmGain = null;
    this.ready = false;
    this.wantsMusic = true;
    this._startPromise = null;
  }

  /** 不在載入時建立 AudioContext，僅標記遊戲可啟動 */
  async init() {
    return true;
  }

  /** 必須在使用者手勢後呼叫，才建立並解鎖 AudioContext */
  async ensureStarted() {
    if (this.ready && this.ctx?.state === 'running') return true;
    if (!this.enabled) return false;
    if (this._startPromise) return this._startPromise;

    this._startPromise = (async () => {
      try {
        if (!this.ctx) {
          const Ctx = window.AudioContext || window.webkitAudioContext;
          if (!Ctx) {
            this.enabled = false;
            return false;
          }
          this.ctx = new Ctx();
          for (const [name, def] of Object.entries(SOUND_DEFS)) {
            this.buffers[name] = makeBuffer(this.ctx, def);
          }
          this.buildBgm();
        }
        if (this.ctx.state === 'suspended') {
          await this.ctx.resume();
        }
        this.ready = true;
        if (this.wantsMusic) this._playMusicInternal();
        return true;
      } catch (e) {
        console.warn('Audio start failed:', e);
        this.enabled = false;
        return false;
      } finally {
        this._startPromise = null;
      }
    })();

    return this._startPromise;
  }

  buildBgm() {
    if (!this.ctx) return;
    const duration = 6;
    const n = Math.floor(SAMPLE_RATE * duration);
    const samples = new Float32Array(n);
    const chords = [
      [130.81, 164.81, 196],
      [98, 123.47, 146.83],
      [110, 130.81, 164.81],
      [87.31, 110, 130.81],
    ];
    const melody = [
      523.25, 659.25, 783.99, 1046.5, 783.99, 659.25,
      493.88, 587.33, 783.99, 987.77, 783.99, 587.33,
      440, 523.25, 659.25, 880, 659.25, 523.25,
      349.23, 440, 523.25, 698.46, 523.25, 440,
    ];
    const noteDur = 0.25;

    for (let chordIdx = 0; chordIdx < chords.length; chordIdx++) {
      const startTime = chordIdx * 1.5;
      const startSample = Math.floor(startTime * SAMPLE_RATE);
      const endSample = Math.floor((startTime + 1.5) * SAMPLE_RATE);
      for (let i = startSample; i < endSample && i < n; i++) {
        const t = i / SAMPLE_RATE;
        let val = 0;
        for (const freq of chords[chordIdx]) {
          val += Math.sin(2 * Math.PI * freq * t);
        }
        const chordT = t - startTime;
        let envelope = 1;
        if (chordT < 0.1) envelope = chordT / 0.1;
        else if (chordT > 1.4) envelope = (1.5 - chordT) / 0.1;
        samples[i] += (val / chords[chordIdx].length) * 0.12 * envelope;
      }
    }

    for (let noteIdx = 0; noteIdx < melody.length; noteIdx++) {
      const startSample = Math.floor(noteIdx * noteDur * SAMPLE_RATE);
      const endSample = Math.floor((noteIdx + 1) * noteDur * SAMPLE_RATE);
      const freq = melody[noteIdx];
      for (let i = startSample; i < endSample && i < n; i++) {
        const t = i / SAMPLE_RATE;
        const noteT = t - noteIdx * noteDur;
        const envelope =
          Math.exp(-6 * noteT) * Math.sin((Math.PI * noteT) / noteDur);
        samples[i] += Math.sin(2 * Math.PI * freq * t) * 0.15 * envelope;
      }
    }

    this.bgmBuffer = this.ctx.createBuffer(1, n, SAMPLE_RATE);
    this.bgmBuffer.copyToChannel(samples, 0);
  }

  _playSound(name) {
    if (!this.ready || !this.ctx || !this.buffers[name]) return;
    if (this.ctx.state !== 'running') return;

    if (name.includes('impact')) {
      const now = performance.now();
      if (now - (this.lastPlayed[name] || 0) < 120) return;
      this.lastPlayed[name] = now;
    }

    const source = this.ctx.createBufferSource();
    source.buffer = this.buffers[name];
    const gain = this.ctx.createGain();
    gain.gain.value = 0.7;
    source.connect(gain);
    gain.connect(this.ctx.destination);
    source.start(0);
    if (this.subtitleCallback) this.subtitleCallback(name);
  }

  unlock() {
    return this.ensureStarted();
  }

  play(name) {
    if (!this.enabled) return;
    if (!this.ready) {
      void this.ensureStarted().then((ok) => {
        if (ok) this._playSound(name);
      });
      return;
    }
    this._playSound(name);
  }

  playMusic() {
    this.wantsMusic = true;
    if (this.ready) {
      this._playMusicInternal();
      return;
    }
    void this.ensureStarted();
  }

  _playMusicInternal() {
    if (!this.ready || !this.ctx || !this.bgmBuffer) return;
    if (this.ctx.state !== 'running') return;
    this.stopMusic();
    this.bgmSource = this.ctx.createBufferSource();
    this.bgmSource.buffer = this.bgmBuffer;
    this.bgmSource.loop = true;
    this.bgmGain = this.ctx.createGain();
    this.bgmGain.gain.value = 0.35;
    this.bgmSource.connect(this.bgmGain);
    this.bgmGain.connect(this.ctx.destination);
    this.bgmSource.start(0);
  }

  stopMusic() {
    if (this.bgmSource) {
      try {
        this.bgmSource.stop();
      } catch (_) {}
      this.bgmSource = null;
    }
  }
}

export const soundManager = new SoundManager();

// SPDX-FileCopyrightText: 2026 Jessica Breen
// SPDX-License-Identifier: GPL-3.0-or-later
// Draws the painting on a <canvas>: blank canvas dots, sparkly gems,
// the cyan selection highlight, and "check my work" marks.

import { pointInRing } from './spatial.js';

function mix(hex, target, amt) {
  const n = parseInt(hex.slice(1), 16);
  const t = target === 'white' ? 255 : 0;
  const ch = [(n >> 16) & 255, (n >> 8) & 255, n & 255].map((c) => Math.round(c + (t - c) * amt));
  return `rgb(${ch.join(',')})`;
}

export class Painter {
  constructor(canvas, { flat = false } = {}) {
    this.canvas = canvas;
    this.ctx = canvas.getContext('2d');
    this.flat = flat;
  }

  setGeometry(geoms) {
    this.geoms = geoms;
    let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
    for (const g of geoms) for (const [x, y] of g.ring) {
      minX = Math.min(minX, x); minY = Math.min(minY, y);
      maxX = Math.max(maxX, x); maxY = Math.max(maxY, y);
    }
    this.bounds = { minX, minY, maxX, maxY };
    this.fit();
  }

  fit() {
    const dpr = window.devicePixelRatio || 1;
    const box = this.canvas.parentElement.getBoundingClientRect();
    const { minX, minY, maxX, maxY } = this.bounds;
    const w = maxX - minX, h = maxY - minY;
    const scale = Math.min(box.width / w, box.height / h) * 0.96;
    const cw = Math.max(10, Math.floor(w * scale)), ch = Math.max(10, Math.floor(h * scale));
    this.canvas.style.width = cw + 'px';
    this.canvas.style.height = ch + 'px';
    this.canvas.width = Math.round(cw * dpr);
    this.canvas.height = Math.round(ch * dpr);
    this.scale = scale * dpr;
    this.dpr = dpr;
  }

  toPx(x, y) {
    return [(x - this.bounds.minX) * this.scale, (this.bounds.maxY - y) * this.scale];
  }

  /** Feature index under a mouse position (CSS pixels relative to the canvas). */
  hexAt(mx, my) {
    const x = (mx * this.dpr) / this.scale + this.bounds.minX;
    const y = this.bounds.maxY - (my * this.dpr) / this.scale;
    for (let i = 0; i < this.geoms.length; i++) {
      const g = this.geoms[i];
      if (Math.abs(g.cx - x) > g.r || Math.abs(g.cy - y) > g.r) continue;
      if (pointInRing(x, y, g.ring)) return i;
    }
    return -1;
  }

  path(g, shrink = 1) {
    const ctx = this.ctx;
    ctx.beginPath();
    g.ring.forEach(([x, y], k) => {
      const [px, py] = this.toPx(g.cx + (x - g.cx) * shrink, g.cy + (y - g.cy) * shrink);
      k ? ctx.lineTo(px, py) : ctx.moveTo(px, py);
    });
    ctx.closePath();
  }

  drawGem(g, color) {
    const ctx = this.ctx;
    const [cx, cy] = this.toPx(g.cx, g.cy);
    this.path(g, 0.97);
    ctx.fillStyle = color;
    ctx.fill();
    if (this.flat) return;
    // facets: six triangles, lit from the top left
    const pts = g.ring.map(([x, y]) => this.toPx(g.cx + (x - g.cx) * 0.97, g.cy + (y - g.cy) * 0.97));
    const shades = [-0.18, -0.08, 0.1, 0.28, 0.16, -0.12];
    for (let k = 0; k < 6; k++) {
      const a = pts[k], b = pts[(k + 1) % 6];
      ctx.beginPath();
      ctx.moveTo(cx, cy); ctx.lineTo(a[0], a[1]); ctx.lineTo(b[0], b[1]); ctx.closePath();
      const s = shades[k];
      ctx.fillStyle = s > 0 ? mix(color, 'white', s) : mix(color, 'black', -s);
      ctx.fill();
    }
    // table (flat top of the gem)
    this.path(g, 0.5);
    ctx.fillStyle = mix(color, 'white', 0.12);
    ctx.fill();
    // sparkle
    const r = g.r * this.scale;
    ctx.beginPath();
    ctx.arc(cx - r * 0.28, cy - r * 0.3, Math.max(0.6, r * 0.12), 0, Math.PI * 2);
    ctx.fillStyle = 'rgba(255,255,255,0.75)';
    ctx.fill();
  }

  drawBlank(g) {
    const ctx = this.ctx;
    this.path(g, 0.97);
    ctx.fillStyle = '#efe8dc';
    ctx.fill();
    ctx.strokeStyle = '#d9cfbf';
    ctx.lineWidth = Math.max(0.5, this.dpr * 0.5);
    ctx.stroke();
    const [cx, cy] = this.toPx(g.cx, g.cy);
    ctx.beginPath();
    ctx.arc(cx, cy, Math.max(0.5, g.r * this.scale * 0.1), 0, Math.PI * 2);
    ctx.fillStyle = '#cfc4b1';
    ctx.fill();
  }

  /** Other layers (pond, trail, springs…) drawn on top so students can see what they're comparing against. */
  drawReference(ref) {
    const ctx = this.ctx, lw = Math.max(1.5, this.dpr * 2);
    ctx.save();
    for (const g of ref.geoms) {
      if (g.kind === 'polygon') {
        ctx.beginPath();
        g.ring.forEach(([x, y], k) => { const [px, py] = this.toPx(x, y); k ? ctx.lineTo(px, py) : ctx.moveTo(px, py); });
        ctx.closePath();
        ctx.fillStyle = 'rgba(25, 118, 210, 0.10)';
        ctx.fill();
        ctx.setLineDash([lw * 3, lw * 2]);
        ctx.lineWidth = lw;
        ctx.strokeStyle = '#0d47a1';
        ctx.stroke();
      } else if (g.kind === 'line') {
        ctx.beginPath();
        g.pts.forEach(([x, y], k) => { const [px, py] = this.toPx(x, y); k ? ctx.lineTo(px, py) : ctx.moveTo(px, py); });
        ctx.setLineDash([]);
        ctx.lineWidth = lw * 1.4;
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.9)';
        ctx.stroke();
        ctx.lineWidth = lw * 0.7;
        ctx.strokeStyle = '#4e342e';
        ctx.stroke();
      } else {
        const [px, py] = this.toPx(g.pts[0][0], g.pts[0][1]);
        ctx.beginPath();
        ctx.arc(px, py, lw * 2.2, 0, Math.PI * 2);
        ctx.fillStyle = '#e3f2fd';
        ctx.fill();
        ctx.setLineDash([]);
        ctx.lineWidth = lw;
        ctx.strokeStyle = '#0d47a1';
        ctx.stroke();
      }
    }
    ctx.restore();
  }

  /**
   * paint: array of palette indexes (-1 = empty); colors: palette colors
   * selection: Set of indexes; wrong: Set of indexes; hover: index
   */
  draw({ paint, colors, selection = new Set(), wrong = new Set(), hover = -1, focus = -1, refs = [] }) {
    const ctx = this.ctx;
    ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
    this.geoms.forEach((g, i) => {
      if (paint[i] >= 0) this.drawGem(g, colors[paint[i]]);
      else if (!this.flat) this.drawBlank(g);
      else { this.path(g, 1); ctx.fillStyle = '#efe8dc'; ctx.fill(); }
    });
    if (selection.size) {
      ctx.lineWidth = Math.max(1, this.dpr * 1.6);
      for (const i of selection) {
        this.path(this.geoms[i], 0.93);
        ctx.fillStyle = 'rgba(0, 255, 255, 0.38)';
        ctx.fill();
        ctx.strokeStyle = '#00e5ff';
        ctx.stroke();
      }
    }
    for (const ref of refs) this.drawReference(ref);
    if (wrong.size) {
      ctx.lineWidth = Math.max(1, this.dpr * 1.8);
      ctx.strokeStyle = '#ff1f4b';
      for (const i of wrong) {
        const g = this.geoms[i];
        const [cx, cy] = this.toPx(g.cx, g.cy);
        const r = g.r * this.scale * 0.42;
        ctx.beginPath();
        ctx.moveTo(cx - r, cy - r); ctx.lineTo(cx + r, cy + r);
        ctx.moveTo(cx + r, cy - r); ctx.lineTo(cx - r, cy + r);
        ctx.stroke();
      }
    }
    if (focus >= 0) {
      this.path(this.geoms[focus], 1);
      ctx.lineWidth = Math.max(1.5, this.dpr * 3);
      ctx.strokeStyle = '#ff4fd8';
      ctx.stroke();
    }
    if (hover >= 0) {
      this.path(this.geoms[hover], 1);
      ctx.lineWidth = Math.max(1, this.dpr * 2);
      ctx.strokeStyle = '#ffffff';
      ctx.stroke();
    }
  }
}

// SPDX-FileCopyrightText: 2026 Jessica Breen
// SPDX-License-Identifier: GPL-3.0-or-later
// The attribute table under the painting: every feature and its fields,
// selected rows highlighted, sortable columns, "all / selected" toggle,
// and a drag handle to resize it.

const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const HEIGHT_KEY = 'diamond-data-table-height';

export class AttributeTable {
  constructor({ onRowClick, onRowHover, onResize }) {
    this.el = document.getElementById('attr-table');
    this.table = document.getElementById('at');
    this.scroll = document.getElementById('at-scroll');
    this.note = document.getElementById('at-note');
    this.count = document.getElementById('at-count');
    this.layer = document.getElementById('at-layer');
    this.onRowClick = onRowClick;
    this.onRowHover = onRowHover;
    this.onResize = onResize;
    this.show = 'all';
    this.sort = null;          // { field, dir: 1 | -1 }
    this.focusIndex = -1;
    this.selection = new Set();

    document.getElementById('at-show').addEventListener('click', (e) => {
      const show = e.target.dataset.show;
      if (!show || show === this.show) return;
      this.setShow(show);
    });
    document.getElementById('at-toggle').addEventListener('click', () => this.toggle());

    this.table.addEventListener('click', (e) => {
      const th = e.target.closest('th');
      if (th) { this.sortBy(th.dataset.field); return; }
      const tr = e.target.closest('tr[data-i]');
      if (tr) this.onRowClick(+tr.dataset.i);
    });
    this.table.addEventListener('mouseover', (e) => {
      const tr = e.target.closest('tr[data-i]');
      this.onRowHover(tr ? +tr.dataset.i : -1);
    });
    this.table.addEventListener('mouseleave', () => this.onRowHover(-1));

    this.setupResize();
  }

  // ---------------------------------------------------------------- data
  setData(level, features) {
    this.fields = level.fields;
    this.features = features;
    this.layer.textContent = level.table;
    this.sort = null;
    this.focusIndex = -1;
    this.setShow('all', false);
    this.note.innerHTML = 'Click a hex in the painting, or a row here, to find a feature. Click a column name to sort.';
    this.render();
  }

  setShow(show, rerender = true) {
    this.show = show;
    document.querySelectorAll('#at-show button').forEach((b) => b.classList.toggle('on', b.dataset.show === show));
    if (rerender) this.render();
  }

  sortBy(field) {
    if (this.sort && this.sort.field === field) this.sort.dir *= -1;
    else this.sort = { field, dir: 1 };
    this.render();
  }

  order() {
    let idx = this.features.map((_, i) => i);
    if (this.show === 'sel') idx = idx.filter((i) => this.selection.has(i));
    if (this.sort) {
      const { field, dir } = this.sort;
      const numeric = this.fields.find((f) => f.name === field).type !== 'TEXT';
      idx.sort((a, b) => {
        const va = this.features[a].properties[field], vb = this.features[b].properties[field];
        if (va === null || va === undefined) return 1;
        if (vb === null || vb === undefined) return -1;
        return dir * (numeric ? va - vb : String(va).localeCompare(String(vb)));
      });
    }
    return idx;
  }

  render() {
    if (!this.fields) return;
    const arrow = (f) => (this.sort && this.sort.field === f ? (this.sort.dir > 0 ? ' ▲' : ' ▼') : '');
    const head = `<thead><tr>${this.fields.map((f) =>
      `<th data-field="${esc(f.name)}" title="Sort by ${esc(f.name)}">${esc(f.name)}<span class="arrow">${arrow(f.name)}</span></th>`).join('')}</tr></thead>`;
    const fmt = (v) => (v === null || v === undefined ? '<i>&lt;Null&gt;</i>' : esc(v));
    const rows = this.order().map((i) => {
      const p = this.features[i].properties;
      return `<tr data-i="${i}" class="${this.rowClass(i)}">${this.fields.map((f) =>
        `<td class="${f.type === 'TEXT' ? '' : 'num'}">${fmt(p[f.name])}</td>`).join('')}</tr>`;
    }).join('');
    const empty = this.show === 'sel' && !this.selection.size
      ? `<tbody><tr><td class="empty" colspan="${this.fields.length}">No features are selected.</td></tr></tbody>` : '';
    this.table.innerHTML = head + (empty || `<tbody>${rows}</tbody>`);
    this.rowEls = new Map([...this.table.querySelectorAll('tr[data-i]')].map((tr) => [+tr.dataset.i, tr]));
    this.updateCount();
  }

  rowClass(i) {
    return [this.selection.has(i) ? 'sel' : '', i === this.focusIndex ? 'focus' : ''].join(' ');
  }

  /** Call whenever the selection changes. */
  update(selection) {
    this.selection = selection;
    if (this.show === 'sel') { this.render(); return; }
    if (this.rowEls) for (const [i, tr] of this.rowEls) tr.className = this.rowClass(i);
    this.updateCount();
  }

  updateCount() {
    const n = this.selection.size, total = this.features.length;
    this.count.textContent = `${n} of ${total} selected`;
  }

  /** Highlight one feature's row and scroll to it. */
  focus(i, noteHtml) {
    this.focusIndex = i;
    if (this.show === 'sel' && !this.selection.has(i)) this.setShow('all');
    else if (this.rowEls) for (const [j, tr] of this.rowEls) tr.className = this.rowClass(j);
    if (!this.rowEls.has(i)) this.render();
    const tr = this.rowEls.get(i);
    if (tr) {
      const top = tr.offsetTop - this.scroll.clientHeight / 2;
      this.scroll.scrollTop = Math.max(0, top);
    }
    if (noteHtml) this.note.innerHTML = noteHtml;
    if (this.el.classList.contains('collapsed')) this.toggle();
  }

  // ---------------------------------------------------------------- size
  toggle() {
    const collapsed = this.el.classList.toggle('collapsed');
    document.getElementById('at-toggle').textContent = collapsed ? 'Show' : 'Hide';
    document.getElementById('table-resizer').hidden = collapsed;
    this.onResize();
  }

  setupResize() {
    const handle = document.getElementById('table-resizer');
    let saved = null;
    try { saved = parseInt(localStorage.getItem(HEIGHT_KEY), 10); } catch { /* ignore */ }
    if (saved > 0) this.el.style.height = `${saved}px`;

    let startY = 0, startH = 0;
    const move = (e) => {
      const board = this.el.parentElement.getBoundingClientRect();
      const max = Math.max(120, board.height - 260);       // always leave room for the painting
      const h = Math.min(max, Math.max(90, startH - (e.clientY - startY)));
      this.el.style.height = `${h}px`;
      this.onResize();
    };
    const up = () => {
      handle.classList.remove('dragging');
      document.body.classList.remove('resizing');
      window.removeEventListener('pointermove', move);
      window.removeEventListener('pointerup', up);
      try { localStorage.setItem(HEIGHT_KEY, parseInt(this.el.style.height, 10)); } catch { /* ignore */ }
    };
    handle.addEventListener('pointerdown', (e) => {
      e.preventDefault();
      startY = e.clientY;
      startH = this.el.getBoundingClientRect().height;
      handle.classList.add('dragging');
      document.body.classList.add('resizing');
      window.addEventListener('pointermove', move);
      window.addEventListener('pointerup', up);
    });
    // keyboard: arrow keys resize when the handle has focus
    handle.addEventListener('keydown', (e) => {
      if (e.key !== 'ArrowUp' && e.key !== 'ArrowDown') return;
      e.preventDefault();
      const h = this.el.getBoundingClientRect().height + (e.key === 'ArrowUp' ? 30 : -30);
      this.el.style.height = `${Math.max(90, h)}px`;
      this.onResize();
    });
  }
}

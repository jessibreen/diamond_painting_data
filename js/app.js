// SPDX-FileCopyrightText: 2026 Jessica Breen
// SPDX-License-Identifier: GPL-3.0-or-later
// Diamond Painting with Data: main app. Wires the painting, the query tools and the levels together.

import { QueryEngine, QueryError } from './engine.js';
import { prepare, selectByLocation, applyMethod } from './spatial.js';
import { Painter } from './render.js';
import { AttributeTable } from './table.js';

const $ = (id) => document.getElementById(id);
const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const STORE = 'diamond-data-v1';

const METHOD_LABEL = { new: 'NEW', add: 'ADD', remove: 'REMOVE', subset: 'SUBSET' };
const RELATION_LABEL = { intersects: 'intersect', touches: 'boundary touches', distance: 'within' };

const state = {
  catalogue: null,
  level: null,
  features: [],
  geoms: [],
  target: [],
  paint: [],
  selection: new Set(),
  tour: new Set(),
  undo: [],
  wrong: new Set(),
  hover: -1,
  focus: -1,
  tab: 'attr',
};

let engine, painter, boxPainter, donePainter, attrTable;

// ------------------------------------------------------------ storage
function loadStore() {
  try { return JSON.parse(localStorage.getItem(STORE)) || { done: [], paint: {} }; }
  catch { return { done: [], paint: {} }; }
}
function saveStore(s) { try { localStorage.setItem(STORE, JSON.stringify(s)); } catch { /* private mode */ } }

// ------------------------------------------------------------ startup
async function init() {
  const SQL = await window.initSqlJs({ locateFile: (f) => `vendor/${f}` });
  engine = new QueryEngine(SQL);
  painter = new Painter($('painting'));
  boxPainter = new Painter($('boxart'));
  donePainter = new Painter($('done-canvas'));
  attrTable = new AttributeTable({
    onRowClick: (i) => focusFeature(i, false),
    onRowHover: (i) => { if (i !== state.hover) { state.hover = i; draw(); } },
    onResize: () => { if (state.level) { painter.fit(); draw(); } },
  });

  state.catalogue = await (await fetch('levels/levels.json')).json();
  buildStaticUI();

  const fromHash = parseInt(location.hash.replace('#', ''), 10);
  const playable = state.catalogue.levels.filter((l) => l.available);
  const start = playable.find((l) => l.number === fromHash) || playable[0];
  await loadLevel(start.number);

  window.addEventListener('hashchange', () => {
    const n = parseInt(location.hash.replace('#', ''), 10);
    const lv = state.catalogue.levels.find((l) => l.available && l.number === n);
    if (lv && lv.number !== state.level.number) loadLevel(n);
  });

  new ResizeObserver(() => { if (state.level) { painter.fit(); draw(); } }).observe($('stage'));
  new ResizeObserver(() => { if (state.level) { boxPainter.fit(); boxPainter.draw({ paint: state.target, colors: colors() }); } }).observe(document.querySelector('.boxart-frame'));
}

function buildStaticUI() {
  const ops = ['=', '<>', '>', '<', '>=', '<=', 'AND', 'OR', 'NOT', '( )', "' '", 'LIKE', 'IN ( )', 'BETWEEN', 'IS NULL'];
  $('ops').innerHTML = ops.map((o) => `<button type="button" data-op="${esc(o)}">${esc(o)}</button>`).join('');
  $('ops').addEventListener('click', (e) => {
    const op = e.target.dataset.op;
    if (!op) return;
    if (op === '( )') insert('(', ')');
    else if (op === 'IN ( )') insert(' IN (', ') ');
    else if (op === "' '") insert("'", "'");
    else insert(` ${op} `);
  });

  document.querySelectorAll('.tabs button').forEach((b) =>
    b.addEventListener('click', () => setTab(b.dataset.tab)));
  $('relation').addEventListener('change', () => { $('dist-row').hidden = $('relation').value !== 'distance'; });
  $('run').addEventListener('click', run);
  $('clear-sql').addEventListener('click', () => {
    $('sql').value = '';
    hideMessage();
    $('sql').focus();
  });
  $('sql').addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) { e.preventDefault(); run(); }
  });
  $('fill').addEventListener('click', fill);
  $('fill-color').addEventListener('change', renderFillControls);
  $('clear-sel').addEventListener('click', () => {
    if (!state.selection.size) return;
    pushUndo();
    state.selection = new Set();
    log('CLEAR', 'Cleared the selection');
    refresh();
  });
  $('undo').addEventListener('click', undo);
  $('start').addEventListener('click', () => {
    const s = loadStore();
    s.started = s.started || [];
    if (!s.started.includes(state.level.number)) s.started.push(state.level.number);
    saveStore(s);
    showView('work');
  });
  $('back-lesson').addEventListener('click', () => showView('lesson'));
  $('reset').addEventListener('click', () => {
    if (!confirm('Start this painting over? All gems will be removed.')) return;
    pushUndo();
    state.paint = state.paint.map(() => -1);
    state.selection = new Set();
    $('history').innerHTML = '';
    $('history-count').textContent = '';
    persist();
    refresh();
  });
  $('check').addEventListener('click', checkWork);
  $('done-close').addEventListener('click', () => $('done').close());
  $('done-next').addEventListener('click', () => {
    $('done').close();
    const next = state.catalogue.levels.find((l) => l.available && l.number > state.level.number);
    if (next) loadLevel(next.number);
  });

  const cv = $('painting');
  let raf = 0;
  cv.addEventListener('mousemove', (e) => {
    const r = cv.getBoundingClientRect();
    const i = painter.hexAt(e.clientX - r.left, e.clientY - r.top);
    if (i !== state.hover) {
      state.hover = i;
      cancelAnimationFrame(raf);
      raf = requestAnimationFrame(draw);
    }
  });
  cv.addEventListener('mouseleave', () => { state.hover = -1; draw(); });
  cv.addEventListener('click', (e) => {
    const r = cv.getBoundingClientRect();
    const i = painter.hexAt(e.clientX - r.left, e.clientY - r.top);
    if (i < 0) return;
    focusFeature(i, true);
    tourEvent('identify');
  });
}

function renderLevelNav() {
  const store = loadStore();
  $('levels').innerHTML = state.catalogue.levels.map((l) => {
    const cls = ['lvl', l.number === state.level?.number ? 'current' : '', store.done.includes(l.number) ? 'done' : ''].join(' ');
    const title = l.available ? `Level ${l.number}: ${l.title} (${l.skill})` : `Coming soon: ${l.title} (${l.skill})`;
    return `<button class="${cls}" data-n="${l.number}" title="${esc(title)}" ${l.available ? '' : 'disabled'}>${l.number}</button>`;
  }).join('');
  $('levels').querySelectorAll('button:not(:disabled)').forEach((b) =>
    b.addEventListener('click', () => loadLevel(+b.dataset.n)));
}

// ------------------------------------------------------------ levels
async function loadLevel(n) {
  const level = state.catalogue.levels.find((l) => l.number === n);
  const gj = await (await fetch(`levels/${level.file}`)).json();
  state.level = level;
  state.features = gj.features;
  state.geoms = prepare(gj.features);
  engine.load(level.fields, gj.features, level.table);
  $('table-name').textContent = level.table;
  document.querySelectorAll('.layer-name').forEach((el) => { el.textContent = level.table; });
  $('selecting-layer').textContent = `${level.table} (selected features only)`;
  $('layer-info').innerHTML = `<span title="${esc(level.about)}">Layer <code>${esc(level.table)}</code> · <b>${esc(level.dataset)}</b></span><small>click a field name to insert it</small>`;
  state.target = computeTarget(level);
  history.replaceState(null, '', `#${n}`);

  const saved = loadStore().paint[n];
  state.paint = saved && saved.length === state.features.length ? saved : state.features.map(() => -1);
  state.selection = new Set();
  state.undo = [];
  state.wrong = new Set();
  state.tour = new Set();

  $('level-num').textContent = `Level ${level.number}`;
  $('level-title').textContent = level.title;
  $('level-skill').textContent = level.skill;
  renderLesson(level);
  $('work-title').innerHTML = `Level ${level.number}: <b>${esc(level.title)}</b> · ${esc(level.skill)}`;
  const started = (loadStore().started || []).includes(n);
  showView(started ? 'work' : 'lesson');     // first visit starts on the lesson
  state.focus = -1;
  $('history').innerHTML = '';
  $('history-count').textContent = '';
  $('sql').value = '';
  hideMessage();

  $('tab-loc-btn').disabled = !level.location;
  $('tab-loc-btn').title = level.location ? '' : 'Select by Location unlocks in a later level';
  setTab('attr');

  renderFields();
  renderFillOptions();
  attrTable.setData(level, state.features);
  renderLevelNav();
  painter.setGeometry(state.geoms);
  boxPainter.setGeometry(state.geoms);
  boxPainter.draw({ paint: state.target, colors: colors() });
  refresh();
  if (!$('view-work').hidden) renderTour();
}

/** The finished picture comes from running the color key's solutions in order. */
function computeTarget(level) {
  const paint = state.features.map(() => -1);
  state.owner = state.features.map(() => -1);   // which request gives each hex its final color
  level.requests.forEach((r, q) => {
    let sel = new Set();
    for (const step of r.solution) sel = runStep(step, sel);
    if (!sel.size) console.warn(`Level ${level.number}: request ${q + 1} selects no hexes`);
    for (const i of sel) { paint[i] = r.color; state.owner[i] = q; }
  });
  const empty = paint.filter((v) => v < 0).length;
  if (empty) console.warn(`Level ${level.number}: ${empty} hexes are never painted by the solution`);
  return paint;
}

function runStep(step, current) {
  const result = step.type === 'attribute'
    ? engine.select(step.where)
    : selectByLocation(state.geoms, current, step.relation, step.distance || 0);
  return applyMethod(current, result, step.method);
}

const colors = () => state.level.colors.map((c) => c.color);

// ------------------------------------------------------------ lesson screen
function showView(view) {
  $('view-lesson').hidden = view !== 'lesson';
  $('view-work').hidden = view !== 'work';
  document.querySelector('.panel').scrollTop = 0;
  document.body.classList.toggle('on-lesson', view === 'lesson');
  if (window.matchMedia('(max-width: 900px)').matches) window.scrollTo(0, 0);
  if (view === 'work') renderTour(); else document.querySelectorAll('.pulse').forEach((el) => el.classList.remove('pulse'));
}

function renderLesson(level) {
  $('lesson-eyebrow').textContent = `Level ${level.number} lesson`;
  $('lesson-title').textContent = level.skill;
  $('lesson-body').innerHTML = level.lesson.map((p) => `<p>${p}</p>`).join('');
  $('dataset-card').innerHTML = `<h3>This level’s data</h3>
    <p>Layer <code>${esc(level.table)}</code>: <b>${esc(level.dataset)}</b>. ${esc(level.about)}
    It has ${level.fields.length} fields. You’ll see them, and the whole attribute table, when you start.</p>`;

  const qs = level.questions || [];
  $('quiz').hidden = !qs.length;
  state.answered = new Set();
  $('quiz-list').innerHTML = qs.map((q, k) => `
    <li data-q="${k}">
      <div class="q-text">${q.question}</div>
      <div class="q-options">${q.options.map((o, j) => `<button type="button" data-o="${j}">${o}</button>`).join('')}</div>
      <div class="q-feedback" hidden></div>
    </li>`).join('');
  $('quiz-list').querySelectorAll('li').forEach((li) => {
    const q = qs[+li.dataset.q];
    li.querySelector('.q-options').addEventListener('click', (e) => {
      const b = e.target.closest('button');
      if (!b || li.classList.contains('right')) return;
      const j = +b.dataset.o;
      const fb = li.querySelector('.q-feedback');
      fb.hidden = false;
      if (j === q.answer) {
        b.classList.add('right');
        li.classList.add('right');
        fb.className = 'q-feedback good';
        fb.innerHTML = `<b>Yes!</b> ${q.explain || ''}`;
        state.answered.add(+li.dataset.q);
        updateStart();
      } else {
        b.classList.add('wrong');
        fb.className = 'q-feedback bad';
        fb.innerHTML = `<b>Not quite.</b> ${(q.hints && q.hints[j]) || 'Try another answer.'}`;
      }
    });
  });
  updateStart();
}

/** Students must answer every question before starting, unless a level sets "questions_required": false. */
function updateStart() {
  const qs = state.level.questions || [];
  const left = qs.length - state.answered.size;
  const locked = state.level.questions_required !== false && left > 0;
  $('start').disabled = locked;
  $('start-hint').textContent = !qs.length || !left ? '' : locked
    ? `Answer ${left} more question${left === 1 ? '' : 's'} to start.`
    : `${left} question${left === 1 ? '' : 's'} left (optional).`;
}

// ------------------------------------------------------------ UI pieces
function setTab(tab) {
  state.tab = tab;
  document.querySelectorAll('.tabs button').forEach((b) => b.classList.toggle('active', b.dataset.tab === tab));
  $('tab-attr').hidden = tab !== 'attr';
  $('tab-loc').hidden = tab !== 'loc';
  hideMessage();
}

function renderFields() {
  $('fields').innerHTML = state.level.fields.map((f) => `
    <div class="field" data-field="${esc(f.name)}">
      <button type="button" class="fname">${esc(f.name)}</button>
      <span class="ftype">${f.type === 'TEXT' ? 'TEXT' : 'NUMBER'}</span>
      <span class="fabout">${esc(f.about)}</span>
      ${f.name === 'fid' ? '<span></span>' : f.type === 'TEXT'
        ? '<button type="button" class="fvals ghost">values</button>'
        : `<span class="frange" title="Smallest and largest value">range ${engine.range(f.name).join('–')}</span>`}
    </div>`).join('');
  $('fields').querySelectorAll('.field').forEach((row) => {
    const name = row.dataset.field;
    const field = state.level.fields.find((f) => f.name === name);
    row.querySelector('.fname').addEventListener('click', () => insert(name));
    const vb = row.querySelector('.fvals');
    if (!vb) return;
    vb.addEventListener('click', () => {
      tourEvent('values');
      const open = row.querySelector('.values');
      if (open) { open.remove(); return; }
      const vals = engine.uniqueValues(name);
      const div = document.createElement('div');
      div.className = 'values';
      div.innerHTML = vals.map((v) => {
        const lit = v === null ? 'NULL' : field.type === 'TEXT' ? `'${String(v).replace(/'/g, "''")}'` : String(v);
        return `<button type="button" data-lit="${esc(lit)}">${esc(lit)}</button>`;
      }).join('');
      div.addEventListener('click', (e) => { if (e.target.dataset.lit) insert(e.target.dataset.lit); });
      row.appendChild(div);
    });
  });
}

function insert(text, after = '') {
  const ta = $('sql');
  const s = ta.selectionStart, e = ta.selectionEnd;
  const v = ta.value;
  ta.value = v.slice(0, s) + text + v.slice(s, e) + after + v.slice(e);
  const pos = s + text.length + (e - s);
  ta.focus();
  ta.setSelectionRange(pos, pos);
}

/** The color key: requests in order, each with its gem color and a ✓ when done. */
function renderPalette() {
  const reqs = state.level.requests;
  const total = reqs.map(() => 0), right = reqs.map(() => 0);
  state.owner.forEach((q, i) => {
    if (q < 0) return;
    total[q]++;
    if (state.paint[i] === reqs[q].color) right[q]++;
  });
  $('palette').innerHTML = reqs.map((r, q) => {
    const c = state.level.colors[r.color];
    const ok = total[q] > 0 && right[q] === total[q];
    return `<li class="${ok ? 'done' : ''}">
      <span class="num">${q + 1}</span>
      <span class="swatch" style="--c:${c.color}" title="${esc(c.name)}"></span>
      <span class="rule"><span class="name">${esc(c.name)}</span> ${r.rule}</span>
      <span class="status ${ok ? 'ok' : ''}" title="${ok ? 'Done: every gem for this request is in the right place' : ''}">${ok ? '✓' : ''}</span>
    </li>`;
  }).join('');
}

function renderFillOptions() {
  $('fill-color').innerHTML = '<option value="">Choose a gem color…</option>' +
    state.level.colors.map((c, k) => `<option value="${k}">${esc(c.name)}</option>`).join('');
}

function renderFillControls() {
  const k = $('fill-color').value;
  const n = state.selection.size;
  const sw = $('fill-swatch');
  sw.classList.toggle('empty', k === '');
  sw.style.setProperty('--c', k === '' ? 'transparent' : state.level.colors[+k].color);
  $('fill').disabled = !n || k === '';
  $('fill').textContent = n ? `Fill ${n} feature${n === 1 ? '' : 's'}` : 'Fill';
  $('fill-hint').textContent = !n ? 'Select some features first' : k === '' ? 'Now choose a color' : '';
}

// ------------------------------------------------------------ level 1 tour
function renderTour() {
  const steps = state.level.tutorial;
  document.querySelectorAll('.pulse').forEach((el) => el.classList.remove('pulse'));
  $('tour').hidden = !steps;
  if (!steps) return;
  const current = steps.findIndex((s, i) => !state.tour.has(i));
  $('tour-steps').innerHTML = steps.map((s, i) =>
    `<li class="${state.tour.has(i) ? 'done' : i === current ? 'current' : ''}"><span>${s.text}</span></li>`).join('');
  if ($('view-work').hidden) return;          // only highlight things on the painting screen
  const target = current >= 0 && steps[current].target && document.querySelector(steps[current].target);
  if (target) target.classList.add('pulse');
}

function tourEvent(name) {
  const steps = state.level?.tutorial;
  if (!steps) return;
  steps.forEach((s, i) => { if (s.event === name) state.tour.add(i); });
  renderTour();
}

/** Show one feature: outline it on the painting and highlight its table row. */
function focusFeature(i, fromPainting) {
  state.focus = i;
  const fid = state.features[i].properties.fid;
  const paint = state.paint[i] >= 0 ? state.level.colors[state.paint[i]].name : 'none yet';
  attrTable.focus(i, `Showing <code>fid ${fid}</code>${fromPainting ? ' (the hex you clicked)' : ''}. ` +
    `Gem placed on it: ${esc(paint)} <span style="opacity:.7">(part of the painting, not the data)</span>`);
  draw();
}

function showMessage(kind, html) {
  const m = $('message');
  m.className = `message ${kind}`;
  m.innerHTML = html;
  m.hidden = false;
}
function hideMessage() { $('message').hidden = true; }

function log(tag, text, query) {
  const li = document.createElement('li');
  li.innerHTML = `<span class="tag">${esc(tag)}</span>` +
    (query ? `<span class="q" title="Click to put this query back in the box">${esc(query)}</span> ` : '') +
    `<span class="n">${text}</span>`;
  if (query) li.querySelector('.q').addEventListener('click', () => { setTab('attr'); $('sql').value = query; $('sql').focus(); });
  $('history').appendChild(li);
  $('history').scrollTop = 1e6;
  $('history-count').textContent = `(${$('history').children.length})`;
}

function draw() {
  painter.draw({ paint: state.paint, colors: colors(), selection: state.selection, wrong: state.wrong, hover: state.hover, focus: state.focus });
}

function refresh() {
  $('sel-count').textContent = state.selection.size;
  attrTable.update(state.selection);
  $('undo').disabled = !state.undo.length;
  renderPalette();
  renderFillControls();
  draw();
}

// ------------------------------------------------------------ actions
function pushUndo() {
  state.undo.push({ paint: [...state.paint], selection: new Set(state.selection) });
  if (state.undo.length > 60) state.undo.shift();
}

function undo() {
  const last = state.undo.pop();
  if (!last) return;
  state.paint = last.paint;
  state.selection = last.selection;
  state.wrong = new Set();
  log('UNDO', 'Undid the last step');
  persist();
  refresh();
}

function run() {
  const method = $('method').value;
  state.wrong = new Set();
  try {
    let result, tag, query, desc;
    if (state.tab === 'attr') {
      query = $('sql').value.trim();
      result = engine.select(query);
      tag = METHOD_LABEL[method];
    } else {
      if (!state.selection.size) {
        throw new QueryError('Select by Location compares features with the features that are <b>already selected</b>. Select some first, for example with Select by Attributes.');
      }
      const relation = $('relation').value;
      const dist = parseFloat($('distance').value);
      if (relation === 'distance' && !(dist >= 0)) throw new QueryError('Type a search distance of 0 mm or more.');
      result = selectByLocation(state.geoms, state.selection, relation, dist);
      tag = METHOD_LABEL[method];
      desc = `Location: features that ${RELATION_LABEL[relation]}${relation === 'distance' ? ` ${dist} mm of` : ''} the selected features`;
    }
    pushUndo();
    const before = state.selection.size;
    state.selection = applyMethod(state.selection, result, method);
    const n = state.selection.size;
    log(tag, desc ? `${esc(desc)} → ${n} selected` : `→ ${n} selected`, query);

    if (result.size === 0) {
      showMessage('info', state.tab === 'attr'
        ? 'The query ran, but <b>no features matched</b>. Text values must match exactly, including capital letters. Click <b>values</b> next to a field to see what’s really in it.'
        : 'No features matched that relationship.');
    } else {
      const verb = { new: 'Selected', add: `Added to the selection: now`, remove: 'Removed from the selection: now', subset: 'Kept only matching features: now' }[method];
      showMessage('success', `${verb} <b>${n}</b> feature${n === 1 ? '' : 's'}${method === 'new' ? '' : ` (was ${before})`}. Now choose a gem color in step 2 and click <b>Fill</b>.`);
      if (state.tab === 'attr') tourEvent('run');
    }
    refresh();
  } catch (e) {
    if (e instanceof QueryError) showMessage('error', e.html);
    else { console.error(e); showMessage('error', 'Something unexpected went wrong. Details are in the browser console.'); }
  }
}

function fill() {
  const v = $('fill-color').value;
  if (!state.selection.size || v === '') return;
  const k = +v;
  pushUndo();
  for (const i of state.selection) state.paint[i] = k;
  const p = state.level.colors[k];
  log('FILL', `${state.selection.size} hexes with ${esc(p.name)}`);
  state.selection = new Set();
  state.wrong = new Set();
  hideMessage();
  $('fill-color').value = '';
  persist();
  refresh();
  tourEvent('fill');
  if (state.paint.every((v, i) => v === state.target[i])) complete();
}

function checkWork() {
  state.wrong = new Set();
  let empty = 0;
  state.paint.forEach((v, i) => {
    if (v < 0) empty++;
    else if (v !== state.target[i]) state.wrong.add(i);
  });
  const w = state.wrong.size;
  if (!w && !empty) showMessage('success', 'Everything is perfect!');
  else if (!w) showMessage('success', `Every gem so far is in the right place. ${empty} features are still empty.`);
  else showMessage('error', `<b>${w}</b> gem${w === 1 ? ' is' : 's are'} the wrong color (marked ✕ on the painting). Compare your query with the rule for that color. Remember that a later fill covers an earlier one.`);
  draw();
}

function persist() {
  const s = loadStore();
  s.paint[state.level.number] = state.paint;
  saveStore(s);
}

function complete() {
  tourEvent('complete');
  const s = loadStore();
  if (!s.done.includes(state.level.number)) s.done.push(state.level.number);
  saveStore(s);
  renderLevelNav();
  const next = state.catalogue.levels.find((l) => l.available && l.number > state.level.number);
  $('done-text').textContent = `You finished “${state.level.title}” using ${state.level.skill}.` + (next ? ` Up next: ${next.title}.` : ' That’s every level so far!');
  $('done-next').hidden = !next;
  $('done').showModal();
  donePainter.setGeometry(state.geoms);
  donePainter.draw({ paint: state.paint, colors: colors() });
}

init().catch((e) => {
  console.error(e);
  document.body.insertAdjacentHTML('afterbegin',
    `<div style="padding:12px;background:#fdecef;color:#7d1830">Diamond Painting with Data couldn't start. If you opened index.html straight from your computer, run it from a local web server instead (see README). Details: ${esc(e.message)}</div>`);
});

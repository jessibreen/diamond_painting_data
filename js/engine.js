// SPDX-FileCopyrightText: 2026 Jessica Breen
// SPDX-License-Identifier: GPL-3.0-or-later
// Attribute queries: runs students' WHERE clauses against SQLite (sql.js)
// and turns mistakes into plain-English messages.

export class QueryError extends Error {
  constructor(html) { super(html); this.html = html; }
}

const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const code = (s) => `<code>${esc(s)}</code>`;

export class QueryEngine {
  constructor(SQL) { this.SQL = SQL; this.db = null; }

  load(fields, features, table = 'features') {
    if (this.db) this.db.close();
    this.fields = fields;
    this.table = table;
    this.db = new this.SQL.Database();
    const cols = fields.map((f) => `"${f.name}" ${f.type}`).join(', ');
    this.db.run(`CREATE TABLE "${table}" (${cols})`);
    const stmt = this.db.prepare(
      `INSERT INTO "${table}" VALUES (${fields.map(() => '?').join(',')})`);
    this.db.run('BEGIN');
    for (const f of features) {
      stmt.run(fields.map((fl) => f.properties[fl.name] ?? null));
    }
    this.db.run('COMMIT');
    stmt.free();
    this.indexById = new Map(features.map((f, i) => [f.properties.fid, i]));
  }

  uniqueValues(field) {
    const res = this.db.exec(`SELECT DISTINCT "${field}" FROM "${this.table}" ORDER BY 1 LIMIT 200`);
    return res.length ? res[0].values.map((r) => r[0]) : [];
  }

  range(field) {
    const res = this.db.exec(`SELECT MIN("${field}"), MAX("${field}") FROM "${this.table}"`);
    return res.length ? res[0].values[0] : [null, null];
  }

  /** Returns a Set of feature indexes matching the WHERE clause. */
  select(where) {
    lint(where, this.fields, this.table);
    let res;
    try {
      res = this.db.exec(`SELECT fid FROM "${this.table}" WHERE (${where})`);
    } catch (e) {
      throw new QueryError(translate(e.message, this.fields));
    }
    const out = new Set();
    if (res.length) for (const [id] of res[0].values) out.add(this.indexById.get(id));
    return out;
  }
}

/** Catch the classic beginner mistakes before SQLite sees them. */
export function lint(where, fields, table = 'features') {
  const names = fields.map((f) => f.name.toLowerCase());
  const fail = (html) => { throw new QueryError(html); };

  if (!where.trim()) fail(`Type a condition first, like ${code("field = 'value'")}.`);
  if (/[‘’“”]/.test(where)) {
    fail(`Your query has curly quotes (‘ ’ or “ ”), which usually sneak in when text is pasted from a document. SQL only understands straight quotes: ${code("'")}.`);
  }
  if (/^\s*(select|where)\b/i.test(where)) {
    fail(`Only type the part that comes <i>after</i> ${code('WHERE')}. The tool adds ${code(`SELECT * FROM ${table} WHERE`)} for you.`);
  }
  if (where.includes(';')) fail(`Leave out the semicolon ${code(';')}. Only one condition goes in this box.`);

  const singles = (where.replace(/''/g, '').match(/'/g) || []).length;
  if (singles % 2) fail(`A text value is missing its closing single quote. Every ${code("'")} needs a partner: ${code("'like this'")}.`);

  // Replace every text value with a placeholder so we can look at the structure.
  const bare = where.replace(/'(?:[^']|'')*'/g, "'_'");

  for (const m of bare.matchAll(/"([^"]*)"/g)) {
    if (!names.includes(m[1].toLowerCase())) {
      fail(`${code(`"${m[1]}"`)} is in <b>double</b> quotes. In SQL, double quotes are for <b>field names</b>. Text values go in <b>single</b> quotes: ${code(`'${m[1]}'`)}.`);
    }
  }
  if ((bare.match(/"/g) || []).length % 2) fail(`A double quote ${code('"')} is missing its partner.`);

  let depth = 0;
  for (const ch of bare) {
    if (ch === '(') depth++;
    if (ch === ')') depth--;
    if (depth < 0) fail(`There's a closing parenthesis ${code(')')} without an opening one.`);
  }
  if (depth > 0) fail(`An opening parenthesis ${code('(')} is never closed.`);

  if (/==/.test(bare)) fail(`SQL uses a single equals sign: ${code('=')}, not ${code('==')}.`);
  if (/(=|<>|!=)\s*null\b/i.test(bare)) {
    fail(`Nothing is ever “equal” to NULL, because NULL means “no value at all.” Use ${code('field IS NULL')} or ${code('field IS NOT NULL')}.`);
  }
  // BETWEEN 1 AND 5 is fine, so hide it before looking for a stranded value.
  const noBetween = bare.replace(/\bbetween\s+('_'|-?[\w.]+)\s+and\s+/gi, 'BETWEEN_ ');
  if (/\b(or|and)\s+('_'|-?\d+(\.\d+)?)\s*(\)|$|\bor\b|\band\b)/i.test(noBetween)) {
    fail(`There's a value standing on its own after AND/OR. Each side needs a complete condition: ${code("zone = 'a' OR zone = 'b'")}, not ${code("zone = 'a' OR 'b'")}.`);
  }
  if (/\b(and|or)\s*(=|<>|!=|>=|<=|>|<)/i.test(bare)) {
    fail(`Each condition needs its own field name: ${code('size > 10 AND size < 20')}, not ${code('size > 10 AND < 20')}.`);
  }
  for (const f of fields) {
    if (f.type === 'TEXT') {
      const re = new RegExp(`(^|[^\\w])"?${f.name}"?\\s*(=|<>|!=|>=|<=|>|<)\\s*-?\\d`, 'i');
      const m = bare.match(new RegExp(`"?${f.name}"?\\s*(?:=|<>|!=|>=|<=|>|<)\\s*(-?[\\d.]+)`, 'i'));
      if (re.test(bare) && m) {
        fail(`${code(f.name)} is a <b>TEXT</b> field, so its values need single quotes, even when they look like numbers: ${code(`${f.name} = '${m[1]}'`)}.`);
      }
      continue;
    }
    if (f.type !== 'INTEGER' && f.type !== 'REAL') continue;
    const re = new RegExp(`(^|[^\\w])"?${f.name}"?\\s*(=|<>|!=|>=|<=|>|<)\\s*'_'`, 'i');
    if (re.test(bare)) {
      const m = where.match(new RegExp(`"?${f.name}"?\\s*(?:=|<>|!=|>=|<=|>|<)\\s*'([^']*)'`, 'i'));
      const v = m ? m[1] : '25';
      fail(`${code(f.name)} is a <b>NUMBER</b> field, so leave the quotes off its values: ${code(`${f.name} = ${v}`)}, not ${code(`${f.name} = '${v}'`)}.`);
    }
  }
}

function translate(msg, fields) {
  const list = fields.map((f) => code(f.name)).join(', ');
  let m;
  if ((m = msg.match(/no such column: (.+)$/))) {
    const word = m[1].trim();
    const near = fields.find((f) => f.name.toLowerCase() !== word.toLowerCase() && editDistance(f.name.toLowerCase(), word.toLowerCase()) <= 2);
    if (near) return `There's no field called ${code(word)}. Did you mean ${code(near.name)}? The fields in this painting are ${list}.`;
    return `There's no field called ${code(word)}. If ${code(word)} is a text value, put it in single quotes: ${code(`'${word}'`)}. The fields in this painting are ${list}.`;
  }
  if (/near "\)": syntax error/.test(msg) || /incomplete input/.test(msg)) {
    return `The query stops before it's finished. Is something missing at the end, like a value or a closing parenthesis?`;
  }
  if ((m = msg.match(/near "(.*)": syntax error/))) {
    return `SQL couldn't make sense of the query near ${code(m[1])}. Look for a missing operator (like ${code('=')}), a missing value, or a stray word.`;
  }
  if (/incomplete input/.test(msg)) {
    return `The query stops before it's finished. Is something missing at the end, like a value or a closing parenthesis?`;
  }
  return `SQLite said: ${esc(msg)}`;
}

function editDistance(a, b) {
  const d = Array.from({ length: a.length + 1 }, (_, i) => [i, ...Array(b.length).fill(0)]);
  for (let j = 1; j <= b.length; j++) d[0][j] = j;
  for (let i = 1; i <= a.length; i++) {
    for (let j = 1; j <= b.length; j++) {
      d[i][j] = Math.min(d[i - 1][j] + 1, d[i][j - 1] + 1, d[i - 1][j - 1] + (a[i - 1] === b[j - 1] ? 0 : 1));
    }
  }
  return d[a.length][b.length];
}

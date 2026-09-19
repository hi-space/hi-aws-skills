#!/usr/bin/env node
/**
 * Build the Word deliverable for an AWS Tech Blog draft.
 *
 *   node build_docx.js <work-dir | draft.md> [--out <file.docx>] [--no-appendix] [--font-ko "<font>"]
 *
 * Given a work directory, reads <work>/06-final.md and writes <work>/06-final.docx; appends
 * <work>/placeholders.md as a final "남은 placeholder" section unless --no-appendix is passed.
 * Given a Markdown file, converts that file and writes the .docx next to it.
 *
 * Parsing is delegated to pandoc (`pandoc -t json`), rendering to docx-js (the `docx` npm package the
 * `docx` skill documents), because pandoc's own DOCX writer drops the inline colours that make the
 * placeholders visible to the author. Every `<span style="background-color:#...;color:#...">` becomes a
 * shaded run with exactly those colours; bare `[태그]` placeholders in headings and captions get the
 * category colour too.
 *
 * Exit codes: 0 built and verified, 1 verification mismatch, 2 usage / missing tool.
 */
"use strict";

const fs = require("fs");
const path = require("path");
const { spawnSync, execSync } = require("child_process");

function loadDocx() {
  try {
    return require("docx");
  } catch (e) {
    try {
      const root = execSync("npm root -g", { encoding: "utf8" }).trim();
      return require(path.join(root, "docx"));
    } catch (e2) {
      console.error("docx (npm) not found. Install with: npm install -g docx");
      process.exit(2);
    }
  }
}

const D = loadDocx();
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, ImageRun, Header, Footer,
  AlignmentType, LevelFormat, ExternalHyperlink, HeadingLevel, BorderStyle, WidthType, ShadingType,
  VerticalAlign, PageNumber, PageBreak,
} = D;

// ------------------------------------------------------------------ placeholder categories (placeholders.md)
const PH = {
  "작성자 확인": { fill: "FFF2CC", color: "7F6000" },
  "기술 검증 필요": { fill: "F8CECC", color: "9F0000" },
  "이미지 필요": { fill: "DAE8FC", color: "0B3D91" },
  "인용 승인 필요": { fill: "D5E8D4", color: "1E5631" },
};
const TAGS = Object.keys(PH).join("|");
const PH_TAG_RE = new RegExp("\\[(" + TAGS + ")\\]");
const PH_TAG_GLOBAL_RE = new RegExp("\\[(" + TAGS + ")\\]", "g");
const PH_TAG_LEAD_RE = new RegExp("^\\s*\\[(" + TAGS + ")\\]");
const CAPTION_RE = /^그림\s*\d+\./;

// ------------------------------------------------------------------ layout constants
const TEXT_WIDTH_DXA = 9360; // Letter, 1" margins
const TEXT_WIDTH_PX = 624; // 6.5in at 96 dpi (docx-js transformation unit)
const BODY_SIZE = 22; // 11pt
const CODE_SIZE = 18; // 9pt

// ------------------------------------------------------------------ CLI
function parseArgs(argv) {
  const args = { appendix: true, fontKo: "Malgun Gothic", fontLatin: "Arial", fontCode: "Consolas" };
  const rest = [];
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--out") args.out = argv[++i];
    else if (a === "--no-appendix") args.appendix = false;
    else if (a === "--font-ko") args.fontKo = argv[++i];
    else if (a === "--font-latin") args.fontLatin = argv[++i];
    else if (a === "--font-code") args.fontCode = argv[++i];
    else if (a === "-h" || a === "--help") { console.log(fs.readFileSync(__filename, "utf8").split("*/")[0]); process.exit(0); }
    else rest.push(a);
  }
  if (rest.length !== 1) { console.error("usage: build_docx.js <work-dir | draft.md> [--out f.docx] [--no-appendix]"); process.exit(2); }
  const target = path.resolve(rest[0]);
  if (fs.existsSync(target) && fs.statSync(target).isDirectory()) {
    args.work = target;
    args.input = path.join(target, "06-final.md");
    args.placeholders = path.join(target, "placeholders.md");
    args.out = args.out || path.join(target, "06-final.docx");
  } else {
    args.input = target;
    args.placeholders = path.join(path.dirname(target), "placeholders.md");
    args.out = args.out || target.replace(/\.md$/i, "") + ".docx";
  }
  if (!fs.existsSync(args.input)) { console.error(`not found: ${args.input}`); process.exit(2); }
  return args;
}

function pandocJson(file) {
  const r = spawnSync("pandoc", [file, "-f", "markdown", "-t", "json"], { encoding: "utf8", maxBuffer: 64 * 1024 * 1024 });
  if (r.status !== 0) { console.error("pandoc failed:", r.stderr || r.error); process.exit(2); }
  return JSON.parse(r.stdout);
}

// ------------------------------------------------------------------ image dimensions (no dependencies)
function imageSize(buf, ext) {
  try {
    if (ext === "png" && buf.readUInt32BE(0) === 0x89504e47) {
      return { w: buf.readUInt32BE(16), h: buf.readUInt32BE(20) };
    }
    if (ext === "gif") return { w: buf.readUInt16LE(6), h: buf.readUInt16LE(8) };
    if (ext === "jpg" || ext === "jpeg") {
      let i = 2;
      while (i < buf.length) {
        if (buf[i] !== 0xff) { i++; continue; }
        const marker = buf[i + 1];
        if (marker >= 0xc0 && marker <= 0xcf && ![0xc4, 0xc8, 0xcc].includes(marker)) {
          return { h: buf.readUInt16BE(i + 5), w: buf.readUInt16BE(i + 7) };
        }
        i += 2 + buf.readUInt16BE(i + 2);
      }
    }
    if (ext === "bmp") return { w: buf.readInt32LE(18), h: Math.abs(buf.readInt32LE(22)) };
  } catch (e) { /* fall through */ }
  return { w: TEXT_WIDTH_PX, h: Math.round(TEXT_WIDTH_PX * 0.6) };
}

// ------------------------------------------------------------------ renderer
class Renderer {
  constructor(args) {
    this.args = args;
    this.baseDir = path.dirname(args.input);
    this.numberingConfigs = [];
    this.listCounter = 0;
    this.stats = { images: 0, placeholders: {}, missingImages: [], headings: 0, tables: 0, code: 0 };
    for (const t of Object.keys(PH)) this.stats.placeholders[t] = 0;
    this.title = "";
    this.sawTitle = false;
  }

  font(kind) {
    const a = this.args;
    if (kind === "code") return { ascii: a.fontCode, hAnsi: a.fontCode, eastAsia: a.fontKo, cs: a.fontCode };
    return { ascii: a.fontLatin, hAnsi: a.fontLatin, eastAsia: a.fontKo, cs: a.fontLatin };
  }

  // ---- inlines -> TextRun[] / hyperlinks
  inlines(list, fmt = {}) {
    const out = [];
    for (const il of coalesce(list)) out.push(...this.inline(il, fmt));
    return out;
  }

  run(text, fmt) {
    const o = { text, font: this.font(fmt.code ? "code" : "body"), size: fmt.size || BODY_SIZE };
    if (fmt.bold) o.bold = true;
    if (fmt.italics) o.italics = true;
    if (fmt.strike) o.strike = true;
    if (fmt.superScript) o.superScript = true;
    if (fmt.subScript) o.subScript = true;
    if (fmt.color) o.color = fmt.color;
    if (fmt.code && !fmt.fill) { o.shading = { type: ShadingType.CLEAR, fill: "F2F2F2", color: "auto" }; o.size = fmt.size || (BODY_SIZE - 2); }
    if (fmt.fill) o.shading = { type: ShadingType.CLEAR, fill: fmt.fill, color: "auto" };
    return new TextRun(o);
  }

  inline(il, fmt) {
    switch (il.t) {
      case "Str": {
        if (fmt.fill || !PH_TAG_RE.test(il.c)) return [this.run(il.c, fmt)];
        // bare [태그] in a heading or caption: colour just the tag
        const runs = [];
        let last = 0;
        for (const m of il.c.matchAll(PH_TAG_GLOBAL_RE)) {
          if (m.index > last) runs.push(this.run(il.c.slice(last, m.index), fmt));
          this.stats.placeholders[m[1]]++;
          runs.push(this.run(m[0], { ...fmt, bold: true, ...PH[m[1]] }));
          last = m.index + m[0].length;
        }
        if (last < il.c.length) runs.push(this.run(il.c.slice(last), fmt));
        return runs;
      }
      case "Space": case "SoftBreak": return [this.run(" ", fmt)];
      case "LineBreak": return [new TextRun({ break: 1 })];
      case "Emph": return this.inlines(il.c, { ...fmt, italics: true });
      case "Strong": return this.inlines(il.c, { ...fmt, bold: true });
      case "Underline": return this.inlines(il.c, fmt);
      case "Strikeout": return this.inlines(il.c, { ...fmt, strike: true });
      case "Superscript": return this.inlines(il.c, { ...fmt, superScript: true });
      case "Subscript": return this.inlines(il.c, { ...fmt, subScript: true });
      case "SmallCaps": return this.inlines(il.c, fmt);
      case "Quoted": {
        const q = il.c[0].t === "SingleQuote" ? ["'", "'"] : ['"', '"'];
        return [this.run(q[0], fmt), ...this.inlines(il.c[1], fmt), this.run(q[1], fmt)];
      }
      case "Code": return [this.run(il.c[1], { ...fmt, code: true })];
      case "Math": return [this.run(il.c[1], { ...fmt, italics: true })];
      case "RawInline": return []; // HTML comments (fact IDs) and stray tags
      case "Link": {
        const url = il.c[2][0];
        const children = this.inlines(il.c[1], { ...fmt, color: "0563C1" });
        return [new ExternalHyperlink({ link: url, children })];
      }
      case "Image": return [this.imageRun(il)];
      case "Span": {
        const attrs = Object.fromEntries(il.c[0][2]);
        const style = attrs.style || "";
        const bg = /background-color:\s*#([0-9A-Fa-f]{6})/.exec(style);
        const fg = /(?:^|;)\s*color:\s*#([0-9A-Fa-f]{6})/.exec(style);
        if (!bg) return this.inlines(il.c[1], fmt);
        const inner = coalesce(il.c[1]);
        const fill = bg[1].toUpperCase();
        const color = fg ? fg[1].toUpperCase() : "000000";
        const shaded = { ...fmt, fill, color };
        const runs = [];
        inner.forEach((x, i) => {
          const m = i === 0 && x.t === "Str" ? x.c.match(PH_TAG_LEAD_RE) : null;
          if (m) { // "[태그] request": bold tag, plain request, same shading
            this.stats.placeholders[m[1]]++;
            runs.push(this.run(m[0], { ...shaded, bold: true }));
            if (x.c.length > m[0].length) runs.push(this.run(x.c.slice(m[0].length), shaded));
          } else {
            runs.push(...this.inline(x, shaded));
          }
        });
        return runs;
      }
      case "Cite": return this.inlines(il.c[1], fmt);
      case "Note": return this.inlines(il.c.flatMap(b => b.c || []), fmt);
      default: return [this.run(stringify([il]), fmt)];
    }
  }

  imageRun(il) {
    const src = il.c[2][0];
    const alt = stringify(il.c[1]) || path.basename(src);
    const file = /^https?:/.test(src) ? null : path.resolve(this.baseDir, decodeURI(src));
    if (!file || !fs.existsSync(file)) {
      this.stats.missingImages.push(src);
      return this.run(`[이미지 파일 없음: ${src}]`, { bold: true, ...PH["이미지 필요"] });
    }
    const ext = path.extname(file).slice(1).toLowerCase();
    const type = ext === "jpeg" ? "jpg" : ext;
    const data = fs.readFileSync(file);
    const nat = imageSize(data, ext);
    const w = Math.min(nat.w, TEXT_WIDTH_PX);
    const h = Math.round(nat.h * (w / nat.w));
    this.stats.images++;
    return new ImageRun({
      type: ["png", "jpg", "gif", "bmp", "svg"].includes(type) ? type : "png",
      data,
      transformation: { width: w, height: h },
      altText: { title: alt, description: alt, name: path.basename(file) },
    });
  }

  // ---- blocks -> Paragraph/Table[]
  blocks(list, ctx = {}) {
    const out = [];
    for (const b of list) out.push(...this.block(b, ctx));
    return out;
  }

  block(b, ctx) {
    switch (b.t) {
      case "Header": {
        const level = b.c[0];
        const text = stringify(b.c[2]);
        if (level === 1 && !this.sawTitle) {
          this.sawTitle = true;
          this.title = text;
          return [new Paragraph({ heading: HeadingLevel.TITLE, children: this.inlines(b.c[2], { size: 40, bold: true }) })];
        }
        this.stats.headings++;
        // Markdown H2 (first section level under the title) becomes Word Heading 1
        const levels = [HeadingLevel.HEADING_1, HeadingLevel.HEADING_1, HeadingLevel.HEADING_2, HeadingLevel.HEADING_3,
          HeadingLevel.HEADING_4, HeadingLevel.HEADING_5];
        const hl = levels[Math.min(level, 6) - 1];
        const sizes = { 1: 32, 2: 30, 3: 26, 4: 24, 5: 22, 6: 22 };
        return [new Paragraph({ heading: hl, children: this.inlines(b.c[2], { size: sizes[level], bold: true }) })];
      }
      case "Para": case "Plain": {
        const text = stringify(b.c);
        if (b.c.length === 1 && b.c[0].t === "Image") return [this.figure(b.c[0])];
        if (CAPTION_RE.test(text)) {
          return [new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 60, after: 240 },
            children: this.inlines(b.c, { size: 20, color: "595959" }) })];
        }
        const p = { children: this.inlines(b.c), spacing: { after: ctx.tight ? 40 : 160, line: 300 } };
        if (ctx.numbering) p.numbering = ctx.numbering;
        if (ctx.indent) p.indent = ctx.indent;
        return [new Paragraph(p)];
      }
      case "LineBlock": return b.c.map(line => new Paragraph({ children: this.inlines(line) }));
      case "Figure": {
        const imgs = b.c[2].flatMap(x => (x.c || []).filter(i => i.t === "Image"));
        return imgs.map(i => this.figure(i));
      }
      case "CodeBlock": {
        this.stats.code++;
        const lines = b.c[1].split("\n");
        return lines.map((line, i) => new Paragraph({
          shading: { type: ShadingType.CLEAR, fill: "F5F5F5", color: "auto" },
          spacing: { before: i === 0 ? 120 : 0, after: i === lines.length - 1 ? 200 : 0, line: 240 },
          indent: { left: 200, right: 200 },
          keepNext: i < lines.length - 1,
          children: [new TextRun({ text: line.length ? line : " ", font: this.font("code"), size: CODE_SIZE })],
        }));
      }
      case "BlockQuote":
        return this.blocks(b.c, { ...ctx, indent: { left: 720 } }).map(p => p);
      case "BulletList": return this.list(b.c, "bullet", ctx);
      case "OrderedList": return this.list(b.c[1], "number", ctx);
      case "DefinitionList":
        return b.c.flatMap(([term, defs]) => [
          new Paragraph({ children: this.inlines(term, { bold: true }) }),
          ...defs.flatMap(d => this.blocks(d, { ...ctx, indent: { left: 720 } })),
        ]);
      case "HorizontalRule":
        return [new Paragraph({ spacing: { before: 200, after: 200 },
          border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: "BFBFBF", space: 1 } }, children: [] })];
      case "Table": return [this.table(b), new Paragraph({ spacing: { after: 120 }, children: [] })];
      case "Div": return this.blocks(b.c[1], ctx);
      case "RawBlock": return []; // <p>, </p>, comments
      case "Null": return [];
      default: return [new Paragraph({ children: [this.run(stringify(b.c || []), {})] })];
    }
  }

  figure(img) {
    return new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 200, after: 60 }, keepNext: true,
      children: [this.imageRun(img)] });
  }

  list(items, kind, ctx) {
    const level = (ctx.level || 0);
    let reference;
    if (kind === "bullet") reference = "bullet-list";
    else { reference = `numbered-${++this.listCounter}`; this.numberingConfigs.push(reference); }
    const out = [];
    for (const item of items) {
      let first = true;
      for (const b of item) {
        if (b.t === "BulletList" || b.t === "OrderedList") {
          out.push(...this.block(b, { ...ctx, level: level + 1 }));
        } else if (first && (b.t === "Para" || b.t === "Plain")) {
          out.push(...this.block(b, { ...ctx, tight: true, numbering: { reference, level } }));
        } else {
          out.push(...this.block(b, { ...ctx, tight: true, indent: { left: 720 * (level + 1) } }));
        }
        first = false;
      }
    }
    return out;
  }

  table(b) {
    this.stats.tables++;
    const colSpecs = b.c[2];
    const head = b.c[3][1]; // rows
    const bodies = b.c[4];
    const rows = [];
    const ncols = colSpecs.length;
    const rel = colSpecs.map(([, w]) => (w.t === "ColWidth" ? w.c : 0));
    const sumRel = rel.reduce((a, x) => a + x, 0);
    const widths = colSpecs.map((_, i) => Math.floor(sumRel > 0 ? TEXT_WIDTH_DXA * (rel[i] || (1 - sumRel) / ncols) : TEXT_WIDTH_DXA / ncols));
    const border = { style: BorderStyle.SINGLE, size: 4, color: "BFBFBF" };
    const borders = { top: border, bottom: border, left: border, right: border };
    const cell = (c, isHead, i) => new TableCell({
      borders,
      width: { size: widths[i], type: WidthType.DXA },
      shading: isHead ? { fill: "E7E6E6", type: ShadingType.CLEAR } : undefined,
      verticalAlign: VerticalAlign.CENTER,
      children: (c[4].length ? this.blocks(c[4], { tight: true }) : [new Paragraph({ children: [] })])
        .map(p => (p instanceof Paragraph ? p : new Paragraph({ children: [] }))),
    });
    for (const r of head) {
      rows.push(new TableRow({ tableHeader: true, children: r[1].map((c, i) => {
        const tc = cell(c, true, i);
        return tc;
      }) }));
    }
    for (const body of bodies) {
      for (const r of [...body[2], ...body[3]]) rows.push(new TableRow({ children: r[1].map((c, i) => cell(c, false, i)) }));
    }
    // bold header text
    return new Table({ columnWidths: widths, margins: { top: 60, bottom: 60, left: 120, right: 120 }, rows });
  }
}

/** Merge runs of Str/Space/SoftBreak into one Str so a `[태그 이름]` with a space is one token. */
function coalesce(list) {
  const out = [];
  let buf = null;
  for (const il of list) {
    if (il.t === "Str" || il.t === "Space" || il.t === "SoftBreak") {
      buf = (buf === null ? "" : buf) + (il.t === "Str" ? il.c : " ");
    } else {
      if (buf !== null) { out.push({ t: "Str", c: buf }); buf = null; }
      out.push(il);
    }
  }
  if (buf !== null) out.push({ t: "Str", c: buf });
  return out;
}

function stringify(inlines) {
  let s = "";
  for (const il of inlines) {
    switch (il.t) {
      case "Str": s += il.c; break;
      case "Space": case "SoftBreak": case "LineBreak": s += " "; break;
      case "Code": case "Math": s += il.c[1]; break;
      case "RawInline": break;
      case "Quoted": s += stringify(il.c[1]); break;
      case "Link": case "Image": s += stringify(il.c[1]); break;
      case "Span": s += stringify(il.c[1]); break;
      case "Cite": s += stringify(il.c[1]); break;
      case "Note": break;
      default: if (Array.isArray(il.c)) s += stringify(il.c);
    }
  }
  return s.trim();
}

// ------------------------------------------------------------------ verification against the source Markdown
function countInMarkdown(md) {
  const counts = {};
  for (const t of Object.keys(PH)) {
    // spans and bare tags in headings/captions, the same set lint_blog.py reports
    counts[t] = (md.match(new RegExp("\\[" + t + "\\]", "g")) || []).length;
  }
  let images = 0;
  let inFence = false;
  for (const line of md.split("\n")) {
    if (/^\s*(```|~~~)/.test(line)) { inFence = !inFence; continue; }
    if (!inFence) images += (line.match(/!\[[^\]]*\]\([^)]+\)/g) || []).length;
  }
  return { counts, images };
}

function countInDocx(file) {
  const r = spawnSync("unzip", ["-p", file, "word/document.xml"], { encoding: "utf8", maxBuffer: 256 * 1024 * 1024 });
  if (r.status !== 0) { console.error("unzip failed:", r.stderr || r.error); process.exit(2); }
  const xml = r.stdout;
  const fills = {};
  for (const [t, c] of Object.entries(PH)) {
    fills[t] = (xml.match(new RegExp(`\\[${t}\\]`, "g")) || []).length;
    fills[t + "_shd"] = (xml.match(new RegExp(`w:fill="${c.fill}"`, "g")) || []).length;
  }
  const images = (xml.match(/<pic:pic\b/g) || []).length;
  return { fills, images };
}

// ------------------------------------------------------------------ main
async function main() {
  const args = parseArgs(process.argv.slice(2));
  const md = fs.readFileSync(args.input, "utf8");
  const ast = pandocJson(args.input);
  const r = new Renderer(args);
  const children = r.blocks(ast.blocks);

  let appendixNote = "no";
  if (args.appendix && fs.existsSync(args.placeholders)) {
    const appAst = pandocJson(args.placeholders);
    const appRenderer = Object.assign(Object.create(Object.getPrototypeOf(r)), r, { sawTitle: false, stats: { ...r.stats, placeholders: {} } });
    for (const t of Object.keys(PH)) appRenderer.stats.placeholders[t] = 0;
    appRenderer.numberingConfigs = r.numberingConfigs;
    children.push(new Paragraph({ children: [new PageBreak()] }));
    const appBlocks = appRenderer.blocks(appAst.blocks);
    // the appendix H1 became a Title; demote it to Heading 1 so the document keeps one title
    if (appBlocks.length && appAst.blocks[0].t === "Header") {
      appBlocks[0] = new Paragraph({ heading: HeadingLevel.HEADING_1, children: appRenderer.inlines(appAst.blocks[0].c[2], { size: 32, bold: true }) });
    }
    children.push(...appBlocks);
    r.listCounter = appRenderer.listCounter;
    appendixNote = path.basename(args.placeholders);
  }

  const bodyFont = r.font("body");
  const heading = (id, name, size, before, after, outline) => ({
    id, name, basedOn: "Normal", next: "Normal", quickFormat: true,
    run: { size, bold: true, color: "232F3E", font: bodyFont },
    paragraph: { spacing: { before, after }, outlineLevel: outline, keepNext: true },
  });
  const numbering = {
    config: [
      { reference: "bullet-list", levels: [0, 1, 2].map(l => ({ level: l, format: LevelFormat.BULLET, text: ["•", "◦", "▪"][l],
        alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720 * (l + 1), hanging: 360 } } } })) },
      ...r.numberingConfigs.map(ref => ({ reference: ref, levels: [0, 1, 2].map(l => ({ level: l,
        format: l === 1 ? LevelFormat.LOWER_LETTER : LevelFormat.DECIMAL, text: `%${l + 1}.`, alignment: AlignmentType.LEFT,
        style: { paragraph: { indent: { left: 720 * (l + 1), hanging: 360 } } } })) })),
    ],
  };

  const doc = new Document({
    creator: "aws-tech-blog-writer",
    title: r.title,
    description: "AWS Tech Blog draft for author review",
    styles: {
      default: { document: { run: { font: bodyFont, size: BODY_SIZE } } },
      paragraphStyles: [
        { id: "Title", name: "Title", basedOn: "Normal", next: "Normal",
          run: { size: 40, bold: true, color: "232F3E", font: bodyFont },
          paragraph: { spacing: { before: 0, after: 360 }, alignment: AlignmentType.LEFT } },
        heading("Heading1", "Heading 1", 32, 480, 200, 0),
        heading("Heading2", "Heading 2", 28, 360, 160, 1),
        heading("Heading3", "Heading 3", 24, 280, 120, 2),
        heading("Heading4", "Heading 4", 22, 240, 120, 3),
      ],
      characterStyles: [{ id: "Hyperlink", name: "Hyperlink", run: { color: "0563C1", underline: {} } }],
    },
    numbering,
    sections: [{
      properties: { page: { margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 } } },
      headers: { default: new Header({ children: [new Paragraph({ alignment: AlignmentType.RIGHT,
        children: [new TextRun({ text: "AWS 기술 블로그 초안 (작성자 검토용)", size: 16, color: "7F7F7F", font: bodyFont })] })] }) },
      footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER,
        children: [new TextRun({ children: [PageNumber.CURRENT], size: 16, color: "7F7F7F", font: bodyFont })] })] }) },
      children,
    }],
  });

  const buffer = await Packer.toBuffer(doc);
  fs.writeFileSync(args.out, buffer);

  // ---- verify: what the author will see must match what the draft said
  const src = countInMarkdown(md);
  const got = countInDocx(args.out);
  let ok = true;
  console.log(`wrote ${args.out} (${(buffer.length / 1024).toFixed(0)} KB)`);
  console.log(`title: ${r.title || "(none)"}`);
  console.log(`headings: ${r.stats.headings}  tables: ${r.stats.tables}  code blocks: ${r.stats.code}  appendix: ${appendixNote}`);
  console.log(`images: markdown ${src.images}, embedded ${r.stats.images}` + (r.stats.missingImages.length ? `, MISSING ${r.stats.missingImages.join(", ")}` : ""));
  if (src.images !== r.stats.images || r.stats.missingImages.length) ok = false;
  for (const t of Object.keys(PH)) {
    const inDoc = got.fills[t];
    const shaded = got.fills[t + "_shd"];
    const line = `[${t}] markdown ${src.counts[t]}, docx ${inDoc}, shaded runs ${shaded}`;
    // appendix repeats each placeholder once as plain text, so docx text count >= markdown count
    const good = inDoc >= src.counts[t] && (src.counts[t] === 0 || shaded >= 1) && (src.counts[t] === 0 || r.stats.placeholders[t] === src.counts[t]);
    if (!good) ok = false;
    console.log((good ? "ok   " : "FAIL ") + line);
  }
  console.log(ok ? "verification: ok" : "verification: FAILED (see lines above)");
  process.exit(ok ? 0 : 1);
}

main().catch(e => { console.error(e); process.exit(2); });

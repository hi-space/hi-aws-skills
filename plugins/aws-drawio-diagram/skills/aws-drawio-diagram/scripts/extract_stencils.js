#!/usr/bin/env node
'use strict';
// Execute draw.io's Sidebar-AWS4.js against a stub Sidebar and print every AWS
// palette entry as JSON. This is a build-time tool for build_icon_catalog.py;
// the skill itself does not need Node at runtime.
//
//   node extract_stencils.js <path/to/Sidebar-AWS4.js> > palette.json
//
// Output: {"sections":[{"id","title","entries":[{"style","width","height","value","label"}]}]}
const fs = require('fs');

const source = process.argv[2];
if (!source) {
  console.error('usage: extract_stencils.js <Sidebar-AWS4.js>');
  process.exit(2);
}
const code = fs.readFileSync(source, 'utf8');

const sections = [];

class StubSidebar {
  // Every palette entry flows through here. Returning the record lets
  // addPaletteFunctions receive the same objects in its entries array.
  createVertexTemplateEntry(style, width, height, value, label) {
    return { style, width, height, value: value || '', label: label || '' };
  }
  // Arrow palette entries are edge styles, not stencils.
  createEdgeTemplateEntry() { return null; }
  addPaletteFunctions(id, title, _expand, entries) {
    sections.push({ id, title, entries: (entries || []).filter(Boolean) });
  }
  setCurrentSearchEntryLibrary() {}
  getTagsForStencil() { return []; }
}

global.Sidebar = StubSidebar;                 // the file assigns Sidebar.prototype.addAWS4*Palette
global.mxConstants = { STYLE_SHAPE: 'shape' }; // the only mx* global the file touches

new Function(code)();                          // runs the IIFE that installs the palette methods

const sb = new StubSidebar();
if (typeof sb.addAWS4Palette === 'function') sb.addAWS4Palette();
if (typeof sb.addAWS4RetiredPalette === 'function') sb.addAWS4RetiredPalette();

if (sections.length === 0) {
  console.error('no palettes captured: Sidebar-AWS4.js format changed?');
  process.exit(1);
}
process.stdout.write(JSON.stringify({ sections }));

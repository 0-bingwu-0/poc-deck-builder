#!/usr/bin/env python3
"""Build a deck written in HTML: always a PDF, and a PowerPoint when asked.

Usage:
    python3 scripts/build.py pocs/fabrikam-claims-triage/deck.html
    python3 scripts/build.py pocs/fabrikam-claims-triage/deck.html --pptx
    python3 scripts/build.py pocs/fabrikam-claims-triage/deck.html --pictures

The deck uses the kit in templates/deck.css. Chrome, Edge, or Chromium renders
it, prints the PDF next to it, and checks that nothing runs past the edge of a
slide. With --pptx, it also reads where the browser put every headline, bullet,
box, table, and picture, and writes them into an editable PowerPoint in the
same places, with the speaker notes. Diagrams and charts drawn in SVG go in as
pictures. --pictures saves a PNG of each slide to a temporary folder, for
looking at them.

The brand color, font, footer, and logo come from Deck settings in
context/profile.md. Uses only the Python standard library.
"""
import argparse
import html
import json
import math
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import url2pathname

ROOT = Path(__file__).resolve().parent.parent
PROFILE = ROOT / "context" / "profile.md"

BROWSERS = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
]
BROWSER_COMMANDS = ["google-chrome", "google-chrome-stable", "chromium", "chromium-browser",
                    "microsoft-edge", "chrome", "msedge"]

SLIDE_W, SLIDE_H = 1280, 720  # CSS px; 96 px to the inch
EMU_PX = 9525                 # EMU per CSS px
TEXT, MUTED, WHITE = "1F2937", "6B7280", "FFFFFF"


# ---------------------------------------------------------------- settings

def read_settings():
    """Brand color, font, footer, and logo from Deck settings in profile.md."""
    text = PROFILE.read_text(encoding="utf-8") if PROFILE.exists() else ""

    def setting(name):
        m = re.search(rf"\*\*{name}:\*\*[ \t]*(.*)", text)
        return m.group(1).strip().strip("`").strip() if m else ""

    color = setting("Brand color").lstrip("#")
    if not re.fullmatch(r"[0-9A-Fa-f]{6}", color):
        color = "1E4E8C"
    logo, logo_path = setting("Logo"), None
    if logo and logo.lower() not in ("none", "no", "-"):
        logo_path = (ROOT / logo).resolve()
        if not logo_path.is_file():
            print(f"Logo not found: {logo}. Building without it.")
            logo_path = None
    return {"brand": color.upper(), "font": setting("Font") or "Arial",
            "footer": setting("Footer"), "logo": logo_path}


def mix(color, other, amount):
    """Blend two hex colors; amount is how much of the other one."""
    a = [int(color[i:i + 2], 16) for i in (0, 2, 4)]
    b = [int(other[i:i + 2], 16) for i in (0, 2, 4)]
    return "".join(f"{round(x + (y - x) * amount):02X}" for x, y in zip(a, b))


def luminance(color):
    r, g, b = (int(color[i:i + 2], 16) / 255 for i in (0, 2, 4))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def theme_css(st):
    """CSS variables for the brand: the color, a darker one for text if it's
    too light to read on white, text that reads on it, a tint, and the font."""
    brand = st["brand"]
    ink = brand if luminance(brand) < 0.45 else mix(brand, "000000", 0.45)
    on = TEXT if luminance(brand) > 0.6 else WHITE
    font = st["font"].replace('"', "").replace(";", "")
    return (f':root {{ --brand: #{brand}; --brand-ink: #{ink}; --brand-on: #{on}; '
            f'--brand-tint: #{mix(brand, WHITE, 0.9)}; --font: "{font}"; }}')


# ---------------------------------------------------------------- the browser side

# Runs in the deck page. Adds the accent bar, footer, slide number, logo, and the
# arrows in a flow. Then, by the part of the URL after #:
#   (nothing)    reads every slide into data-deck on <body> and checks the fit
#   only=N       shows slide N alone, for a picture of it
#   raster=N:K   shows only picture K of slide N (an SVG, say), at the top left
PAGE_JS = r"""
(function () {
  var S = __SETTINGS__;
  var slides = Array.prototype.slice.call(document.querySelectorAll('section.slide'));
  function esc(t) { var d = document.createElement('div'); d.textContent = t; return d.innerHTML; }

  slides.forEach(function (slide, i) {
    if (slide.classList.contains('cover')) {
      var h1 = slide.querySelector('h1');
      if (h1) h1.insertAdjacentHTML('afterend', '<div class="chrome-rule"></div>');
      if (S.logo) slide.insertAdjacentHTML('beforeend', '<img class="chrome-logo" src="' + S.logo + '" alt="Logo">');
    } else if (!slide.classList.contains('section')) {
      slide.insertAdjacentHTML('afterbegin', '<div class="chrome-accent"></div>');
      if (S.footer) slide.insertAdjacentHTML('beforeend', '<div class="chrome-footer">' + esc(S.footer) + '</div>');
      slide.insertAdjacentHTML('beforeend', '<div class="chrome-page">' + (i + 1) + '</div>');
      if (S.logo) {
        slide.classList.add('has-logo');
        slide.insertAdjacentHTML('beforeend', '<img class="chrome-logo" src="' + S.logo + '" alt="Logo">');
      }
    }
    slide.querySelectorAll('.flow').forEach(function (flow) {
      Array.prototype.slice.call(flow.children, 1).forEach(function (step) {
        step.insertAdjacentHTML('beforebegin', '<i class="arrow"></i>');
      });
    });
  });

  function px(v) { return parseFloat(v) || 0; }
  function tag(el) { return el.tagName.toLowerCase(); }
  function classes(el) { return typeof el.className === 'string' ? el.className : (el.className.baseVal || ''); }
  function isChrome(el) { return /(^|\s)chrome-/.test(classes(el)); }

  // Hex for a computed color, blended onto white if it's see-through. null if invisible.
  function color(c) {
    var m, v, a = 1;
    if ((m = c.match(/^rgba?\(([^)]+)\)/))) {
      v = m[1].split(/[\s,\/]+/).filter(Boolean).map(parseFloat);
      if (v.length > 3) a = v[3];
    } else if ((m = c.match(/^color\(srgb ([^)]+)\)/))) {
      v = m[1].split(/[\s\/]+/).filter(Boolean).map(parseFloat);
      if (v.length > 3) a = v[3];
      v = [v[0] * 255, v[1] * 255, v[2] * 255];
    } else return null;
    if (!(a > 0)) return null;
    return v.slice(0, 3).map(function (n) {
      n = Math.max(0, Math.min(255, Math.round(n * a + 255 * (1 - a))));
      return ('0' + n.toString(16)).slice(-2);
    }).join('').toUpperCase();
  }

  // Pictures the PowerPoint can't hold as they are: SVG, canvas, and anything not PNG or JPG.
  function isRaster(el) {
    var t = tag(el);
    if (t === 'svg' || t === 'canvas' || el.classList.contains('raster')) return true;
    if (t === 'img') return !/\.(png|jpe?g)([?#].*)?$/i.test(el.currentSrc || el.src) && !isChrome(el);
    return false;
  }
  function rasters(slide) {
    return Array.prototype.filter.call(slide.querySelectorAll('svg, canvas, img, .raster'), function (el) {
      return isRaster(el) && !(el.parentElement && el.parentElement.closest('svg, .raster'));
    });
  }

  var mode = location.hash.slice(1);
  var only = mode.match(/^(?:only|raster)=(\d+)/);
  if (only) {
    var n = +only[1];
    var css = 'html, body { background: none !important; margin: 0 !important; }'
      + ' .slide { margin: 0 !important; box-shadow: none !important; }';
    if (/^raster/.test(mode)) {
      css += ' html, body, .slide { background: transparent !important; }'
        + ' .slide, .slide * { visibility: hidden !important; } .raster-on, .raster-on * { visibility: visible !important; }';
    }
    document.head.insertAdjacentHTML('beforeend', '<style>' + css + '</style>');
    slides.forEach(function (s, i) { if (i + 1 !== n) s.style.display = 'none'; });
  }

  window.addEventListener('load', function () {
    if (only && /^raster/.test(mode)) {
      var slide = slides[+only[1] - 1], k = +mode.split(':')[1];
      var el = rasters(slide)[k];
      el.classList.add('raster-on');
      var r = el.getBoundingClientRect();
      slide.style.transform = 'translate(' + (-r.left) + 'px, ' + (-r.top) + 'px)';
      return;
    }
    if (only) return;
    var out = { slides: [], problems: [] };
    slides.forEach(function (slide, i) { out.slides.push(read(slide, i + 1, out.problems)); });
    document.body.setAttribute('data-deck', JSON.stringify(out));
  });

  // ---- reading a slide

  function read(slide, n, problems) {
    var S0 = slide.getBoundingClientRect();
    function rel(r) { return { x: r.left - S0.left, y: r.top - S0.top, w: r.width, h: r.height }; }
    function sides(cs) {
      return ['Top', 'Right', 'Bottom', 'Left'].map(function (s) {
        var w = px(cs['border' + s + 'Width']);
        var c = w > 0 && cs['border' + s + 'Style'] !== 'none' ? color(cs['border' + s + 'Color']) : null;
        return c ? { w: w, c: c } : null;
      });
    }
    function boxOf(cs) {
      var fill = color(cs.backgroundColor), b = sides(cs);
      if (!fill && !b.some(Boolean)) return null;
      var same = b.every(function (s) { return s && b[0] && s.w === b[0].w && s.c === b[0].c; });
      return { fill: fill, line: same ? b[0] : null, sides: same ? [null, null, null, null] : b,
               radius: px(cs.borderTopLeftRadius) };
    }
    function lines(r, box, items) {
      var x = r.left - S0.left, y = r.top - S0.top, s = box.sides;
      if (s[0]) items.push({ kind: 'shape', x: x, y: y, w: r.width, h: s[0].w, fill: s[0].c });
      if (s[1]) items.push({ kind: 'shape', x: x + r.width - s[1].w, y: y, w: s[1].w, h: r.height, fill: s[1].c });
      if (s[2]) items.push({ kind: 'shape', x: x, y: y + r.height - s[2].w, w: r.width, h: s[2].w, fill: s[2].c });
      if (s[3]) items.push({ kind: 'shape', x: x, y: y, w: s[3].w, h: r.height, fill: s[3].c });
    }

    function runStyle(t, el) {
      var cs = getComputedStyle(el);
      if (cs.textTransform === 'uppercase') t = t.toUpperCase();
      return { t: t, size: px(cs.fontSize), bold: parseInt(cs.fontWeight, 10) >= 600,
               italic: cs.fontStyle === 'italic', color: color(cs.color) || '000000',
               font: cs.fontFamily.split(',')[0].replace(/["']/g, '').trim() };
    }
    function runs(el, skipLists) {
      var out = [];
      (function rec(node) {
        node.childNodes.forEach(function (c) {
          if (c.nodeType === 3) {
            var t = c.textContent.replace(/\s+/g, ' ');
            if (t) out.push(runStyle(t, c.parentElement));
          } else if (c.nodeType === 1) {
            var t2 = tag(c);
            if (t2 === 'br') out.push({ br: true });
            else if (skipLists && (t2 === 'ul' || t2 === 'ol')) return;
            else if (getComputedStyle(c).display !== 'none') rec(c);
          }
        });
      })(el);
      for (var i = 0; i < out.length; i++) {
        if (out[i].br) continue;
        var prev = out[i - 1];
        if (!prev || prev.br || / $/.test(prev.t)) out[i].t = out[i].t.replace(/^ /, '');
      }
      if (out.length && !out[out.length - 1].br) out[out.length - 1].t = out[out.length - 1].t.replace(/ $/, '');
      return out.filter(function (r) { return r.br || r.t; });
    }
    function align(cs) {
      return { center: 'ctr', right: 'r', end: 'r', justify: 'just' }[cs.textAlign] || 'l';
    }
    function para(el, cs, skipLists) {
      return { runs: runs(el, skipLists), align: align(cs), lh: cs.lineHeight === 'normal' ? 0 : px(cs.lineHeight) };
    }
    function isTextBlock(el) {
      var text = false;
      for (var i = 0; i < el.childNodes.length; i++) {
        var c = el.childNodes[i];
        if (c.nodeType === 3) { if (c.textContent.trim()) text = true; continue; }
        if (c.nodeType !== 1) continue;
        var t = tag(c);
        if (t === 'br') continue;
        if (/^(svg|img|canvas|video|table|ul|ol)$/.test(t)) return false;
        var d = getComputedStyle(c).display;
        if (d === 'none') continue;
        if (!/^inline/.test(d) || d === 'inline-block' || d === 'inline-flex') return false;
        if (c.textContent.trim()) text = true;
      }
      return text;
    }
    function inset(cs) {
      return { l: px(cs.paddingLeft) + px(cs.borderLeftWidth), r: px(cs.paddingRight) + px(cs.borderRightWidth),
               t: px(cs.paddingTop) + px(cs.borderTopWidth), b: px(cs.paddingBottom) + px(cs.borderBottomWidth) };
    }
    function textItem(el, cs, box) {
      var r = el.getBoundingClientRect(), pad = inset(cs);
      var range = document.createRange(); range.selectNodeContents(el);
      var tr = range.getBoundingClientRect(), anchor = 't';
      if (tr.height && tr.top - (r.top + pad.t) > 3) anchor = Math.abs(r.bottom - pad.b - tr.bottom) <= 3 ? 'b' : 'ctr';
      var item = rel(r);
      item.kind = 'text'; item.inset = pad; item.anchor = anchor; item.paras = [para(el, cs)];
      if (box && (box.fill || box.line)) { item.fill = box.fill; item.line = box.line; item.radius = box.radius; }
      return item;
    }
    function markerChar(type) {
      if (type === 'none') return '';
      var m = type.match(/^["'](.)/);
      if (m) return m[1];
      return { circle: '◦', square: '▪' }[type] || '•';
    }
    function listItem(list) {
      var lr = list.getBoundingClientRect(), paras = [];
      (function rec(l, level) {
        var ls = getComputedStyle(l), ordered = tag(l) === 'ol', first = true;
        Array.prototype.forEach.call(l.children, function (li) {
          if (tag(li) !== 'li') return;
          var cs = getComputedStyle(li), p = para(li, cs, true);
          p.level = level;
          p.before = first ? (level ? px(ls.marginTop) : 0) : px(cs.marginTop);
          p.marL = li.getBoundingClientRect().left - lr.left;
          // The browser hangs the marker just before the text; PowerPoint at the edge of the indent.
          p.hang = Math.min(px(ls.paddingLeft), px(cs.fontSize) * (ordered ? 1.3 : 0.85));
          var mark = color(getComputedStyle(li, '::marker').color);
          var ch = markerChar(ls.listStyleType);
          if (ordered) p.bullet = { num: true, start: l.start || 1, color: mark };
          else if (ch) p.bullet = { ch: ch, color: mark };
          paras.push(p);
          first = false;
          Array.prototype.forEach.call(li.children, function (c) {
            if (tag(c) === 'ul' || tag(c) === 'ol') rec(c, level + 1);
          });
        });
      })(list, 0);
      var item = rel(lr);
      item.kind = 'text'; item.inset = { l: 0, r: 0, t: 0, b: 0 }; item.anchor = 't'; item.paras = paras;
      return item;
    }
    function tableItem(t) {
      var item = rel(t.getBoundingClientRect());
      item.kind = 'table'; item.rows = [];
      Array.prototype.forEach.call(t.rows, function (tr) {
        var cells = [];
        Array.prototype.forEach.call(tr.cells, function (td) {
          var cs = getComputedStyle(td);
          var fill = color(cs.backgroundColor) || color(getComputedStyle(tr).backgroundColor)
            || color(getComputedStyle(tr.parentElement).backgroundColor);
          cells.push({ w: td.getBoundingClientRect().width, fill: fill, borders: sides(cs), inset: inset(cs),
                       anchor: { middle: 'ctr', bottom: 'b' }[cs.verticalAlign] || 't', paras: [para(td, cs)] });
        });
        item.rows.push({ h: tr.getBoundingClientRect().height, cells: cells });
      });
      return item;
    }

    var items = [], list = rasters(slide);
    function visit(el) {
      var cs = getComputedStyle(el), t = tag(el);
      if (cs.display === 'none' || el.classList.contains('notes')) return;
      var r = el.getBoundingClientRect();
      if (isRaster(el)) {
        var it = rel(r); it.kind = 'raster'; it.index = list.indexOf(el);
        items.push(it);
        return;
      }
      if (cs.visibility === 'hidden') return;
      if (t === 'img') {
        var pic = rel(r), b = boxOf(cs);
        pic.kind = 'picture'; pic.src = el.currentSrc || el.src; pic.alt = el.alt || '';
        pic.line = b && b.line;
        items.push(pic);
        return;
      }
      if (t === 'table') { items.push(tableItem(el)); return; }
      var box = boxOf(cs);
      if (box) lines(r, box, items);
      var filled = box && (box.fill || box.line);
      if (t === 'ul' || t === 'ol') {
        if (filled) items.push(shape(el, r, box));
        items.push(listItem(el));
        return;
      }
      if (isTextBlock(el)) { items.push(textItem(el, cs, box)); return; }
      if (filled) items.push(shape(el, r, box));
      Array.prototype.forEach.call(el.children, visit);
    }
    function shape(el, r, box) {
      var s = rel(r);
      s.kind = 'shape'; s.fill = box.fill; s.line = box.line; s.radius = box.radius;
      s.geom = el.classList.contains('arrow') ? 'rightArrow' : 'rect';
      return s;
    }

    var cs = getComputedStyle(slide), sbox = boxOf(cs);
    if (sbox) lines(S0, sbox, items);
    Array.prototype.forEach.call(slide.children, visit);

    var notes = slide.querySelector('aside.notes'), notesText = [];
    if (notes) {
      var ps = notes.querySelectorAll('p');
      (ps.length ? Array.prototype.map.call(ps, function (p) { return p.textContent; }) : [notes.textContent])
        .forEach(function (t) { t = t.replace(/\s+/g, ' ').trim(); if (t) notesText.push(t); });
    }

    fit(slide, n, S0, cs, problems);
    return { background: sbox ? sbox.fill : color(cs.backgroundColor), items: items, notes: notesText };
  }

  // ---- the fit check

  function describe(el) {
    var t = (el.textContent || '').replace(/\s+/g, ' ').trim();
    return t ? '"' + (t.length > 40 ? t.slice(0, 40).trim() + '…' : t) + '"' : 'a ' + tag(el);
  }
  function fit(slide, n, S0, cs, problems) {
    var top = S0.top + px(cs.paddingTop) - 1, bottom = S0.bottom - px(cs.paddingBottom) + 1;
    var left = S0.left + px(cs.paddingLeft) - 1, right = S0.right - px(cs.paddingRight) + 1;
    var worst = null;
    slide.querySelectorAll('*').forEach(function (el) {
      if (isChrome(el) || el.closest('.notes') || (el.parentElement && el.parentElement.closest('svg'))) return;
      if (getComputedStyle(el).display === 'none') return;
      var r = el.getBoundingClientRect();
      if (!r.width && !r.height) return;
      var over = Math.max(r.bottom - bottom, r.right - right, top - r.top, left - r.left);
      if (over > 0 && (!worst || over >= worst.over - 0.5)) worst = { over: over, el: el };
      if (tag(el) === 'img' && el.complete && !el.naturalWidth)
        problems.push({ slide: n, text: 'picture not found: ' + decodeURI(el.getAttribute('src') || '') });
    });
    if (worst) problems.push({ slide: n, text: describe(worst.el) + ' runs ' + (worst.over / 96).toFixed(2) + ' in past the edge of the slide.' });
    var h2 = slide.querySelector(':scope > h2');
    if (h2 && !slide.classList.contains('section')) {
      var hs = getComputedStyle(h2), lh = px(hs.lineHeight) || px(hs.fontSize) * 1.2;
      var count = Math.round((h2.getBoundingClientRect().height - px(hs.paddingTop) - px(hs.paddingBottom)) / lh);
      if (count > 2) problems.push({ slide: n, text: 'the headline runs to ' + count + ' lines. Keep it to two.' });
    }
  }
})();
"""


def render_page(deck_path, st, folder):
    """The deck with the brand, the page script, and a base URL, in a temporary folder."""
    src = deck_path.read_text(encoding="utf-8")
    if not re.search(r"<head[^>]*>", src, re.I) or not re.search(r"</body>", src, re.I):
        sys.exit(f"{deck_path.name} needs a <head> and a <body>.")
    page_settings = json.dumps({"footer": st["footer"], "logo": st["logo"].as_uri() if st["logo"] else ""})
    base = f'<base href="{deck_path.parent.as_uri()}/">'
    src = re.sub(r"<head[^>]*>", lambda m: m.group(0) + base, src, count=1, flags=re.I)
    src = re.sub(r"</head>", lambda m: f"<style>{theme_css(st)}</style></head>", src, count=1, flags=re.I)
    script = PAGE_JS.replace("__SETTINGS__", page_settings)
    src = re.sub(r"</body>", lambda m: f"<script>{script}</script></body>", src, count=1, flags=re.I)
    page = folder / "deck.html"
    page.write_text(src, encoding="utf-8")
    return page


def find_browser():
    for path in BROWSERS:
        if Path(path).is_file():
            return path
    for command in BROWSER_COMMANDS:
        found = shutil.which(command)
        if found:
            return found
    return None


def browser_run(browser, *args):
    return subprocess.run([browser, "--headless", "--disable-gpu", "--hide-scrollbars",
                           "--virtual-time-budget=3000", *args], capture_output=True, timeout=180)


def read_deck(browser, page):
    result = browser_run(browser, "--dump-dom", page.as_uri())
    m = re.search(r'data-deck="([^"]*)"', result.stdout.decode("utf-8", "replace"))
    return json.loads(html.unescape(m.group(1))) if m else None


def print_pdf(browser, page, pdf_path):
    if pdf_path.exists():
        pdf_path.unlink()
    browser_run(browser, "--no-pdf-header-footer", f"--print-to-pdf={pdf_path}", page.as_uri())
    return pdf_path.exists()


def screenshot(browser, url, png, w, h, scale=1, transparent=False):
    args = [f"--window-size={w},{h}", f"--force-device-scale-factor={scale}", f"--screenshot={png}"]
    if transparent:
        args.append("--default-background-color=00000000")
    browser_run(browser, *args, url)
    return png.exists()


# ---------------------------------------------------------------- PowerPoint

NS = ('xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
      'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
      'xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"')
XML = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
CT = "application/vnd.openxmlformats-officedocument.presentationml."
GROUP = ('<p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>'
         '<p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/>'
         '<a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>')
CLRMAP = ('<p:clrMap bg1="lt1" tx1="dk1" bg2="lt2" tx2="dk2" accent1="accent1" accent2="accent2" '
          'accent3="accent3" accent4="accent4" accent5="accent5" accent6="accent6" '
          'hlink="hlink" folHlink="folHlink"/>')
LEVEL1 = ('<a:lvl1pPr marL="0" algn="l" defTabSz="914400" rtl="0" eaLnBrk="1" latinLnBrk="0" '
          'hangingPunct="1"><a:defRPr sz="{sz}" kern="1200"><a:solidFill><a:schemeClr val="tx1"/>'
          '</a:solidFill><a:latin typeface="+{f}-lt"/><a:ea typeface="+{f}-ea"/>'
          '<a:cs typeface="+{f}-cs"/></a:defRPr></a:lvl1pPr>')
NO_LINE = "<a:noFill/>"


def emu(px):
    return int(round(px * EMU_PX))


def pts(px):
    """Hundredths of a point, as PowerPoint sizes text and spacing."""
    return int(round(px * 75))


def esc(text):
    return html.escape(text, quote=True)


def fill_xml(color):
    return f'<a:solidFill><a:srgbClr val="{color}"/></a:solidFill>' if color else NO_LINE


def line_xml(line, tag="a:ln"):
    if not line:
        return f"<{tag} w=\"0\">{NO_LINE}</{tag}>"
    return f'<{tag} w="{emu(line["w"])}">{fill_xml(line["c"])}</{tag}>'


def xfrm(item, tag="a:xfrm", w=None):
    return (f'<{tag}><a:off x="{emu(item["x"])}" y="{emu(item["y"])}"/>'
            f'<a:ext cx="{emu(w if w is not None else item["w"])}" cy="{emu(item["h"])}"/></{tag}>')


def rel_type(kind):
    if kind == "core-properties":
        return "http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties"
    return "http://schemas.openxmlformats.org/officeDocument/2006/relationships/" + kind


def rels_xml(rels):
    body = "".join(f'<Relationship Id="{rid}" Type="{rel_type(kind)}" Target="{target}"/>'
                   for rid, kind, target in rels)
    return XML + f'<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">{body}</Relationships>'


def run_props(r, extra=""):
    attrs = f'lang="en-US" sz="{pts(r["size"])}"'
    if r["bold"]:
        attrs += ' b="1"'
    if r["italic"]:
        attrs += ' i="1"'
    font = esc(r["font"] or "Arial")
    return (f'<a:rPr {attrs} dirty="0"{extra}><a:solidFill><a:srgbClr val="{r["color"]}"/></a:solidFill>'
            f'<a:latin typeface="{font}"/><a:cs typeface="{font}"/></a:rPr>')


def para_xml(p):
    bullet = p.get("bullet")
    left = emu(p.get("marL", 0)) if bullet else 0
    indent = -emu(p.get("hang", 0)) if bullet else 0
    ppr = f'<a:pPr marL="{left}" indent="{indent}" algn="{p["align"]}">'
    if p.get("lh"):
        ppr += f'<a:lnSpc><a:spcPts val="{pts(p["lh"])}"/></a:lnSpc>'
    if p.get("before"):
        ppr += f'<a:spcBef><a:spcPts val="{pts(p["before"])}"/></a:spcBef>'
    text_runs = [r for r in p["runs"] if not r.get("br")]
    first = text_runs[0] if text_runs else {"size": 21, "bold": False, "italic": False, "color": TEXT, "font": "Arial"}
    if not bullet:
        ppr += "<a:buNone/>"
    else:
        if bullet.get("color"):
            ppr += f'<a:buClr><a:srgbClr val="{bullet["color"]}"/></a:buClr>'
        if bullet.get("num"):
            ppr += (f'<a:buFont typeface="{esc(first["font"] or "Arial")}"/>'
                    f'<a:buAutoNum type="arabicPeriod" startAt="{bullet["start"]}"/>')
        else:
            ppr += f'<a:buFont typeface="Arial"/><a:buChar char="{esc(bullet["ch"])}"/>'
    ppr += "</a:pPr>"
    body = ""
    for r in p["runs"]:
        if r.get("br"):
            body += f"<a:br>{run_props(first)}</a:br>"
        else:
            body += f"<a:r>{run_props(r)}<a:t>{esc(r['t'])}</a:t></a:r>"
    return f'<a:p>{ppr}{body}<a:endParaRPr lang="en-US" sz="{pts(first["size"])}" dirty="0"/></a:p>'


def body_xml(paras, inset, anchor, tag="p:txBody"):
    ins = f'lIns="{emu(inset["l"])}" tIns="{emu(inset["t"])}" rIns="{emu(inset["r"])}" bIns="{emu(inset["b"])}"'
    return (f'<{tag}><a:bodyPr wrap="square" {ins} anchor="{anchor}" rtlCol="0"><a:noAutofit/></a:bodyPr>'
            f'<a:lstStyle/>{"".join(para_xml(p) for p in paras)}</{tag}>')


def shape_xml(item, sid):
    geom = item.get("geom", "rect")
    av = "<a:avLst/>"
    if geom == "rect" and item.get("radius"):
        geom = "roundRect"
        adj = min(50000, int(item["radius"] / max(1, min(item["w"], item["h"])) * 100000))
        av = f'<a:avLst><a:gd name="adj" fmla="val {adj}"/></a:avLst>'
    paras = item.get("paras")
    text_box = paras and not item.get("fill") and not item.get("line") and geom == "rect"
    name, flag = (f"TextBox {sid}", ' txBox="1"') if text_box else (f"Shape {sid}", "")
    w = item["w"]
    # A little room on the right, so a line that just fits in the browser
    # still fits if PowerPoint sets it a hair wider.
    if text_box and all(p["align"] == "l" for p in paras):
        w += min(w * 0.02, 12)
    xml = (f'<p:sp><p:nvSpPr><p:cNvPr id="{sid}" name="{name}"/><p:cNvSpPr{flag}/><p:nvPr/></p:nvSpPr>'
           f'<p:spPr>{xfrm(item, w=w)}<a:prstGeom prst="{geom}">{av}</a:prstGeom>'
           f'{fill_xml(item.get("fill"))}{line_xml(item.get("line"))}</p:spPr>')
    if paras:
        xml += body_xml(paras, item["inset"], item["anchor"])
    return xml + "</p:sp>"


def picture_xml(item, sid, rid):
    line = line_xml(item.get("line")) if item.get("line") else ""
    return (f'<p:pic><p:nvPicPr><p:cNvPr id="{sid}" name="Picture {sid}" descr="{esc(item.get("alt", ""))}"/>'
            '<p:cNvPicPr><a:picLocks noChangeAspect="1"/></p:cNvPicPr><p:nvPr/></p:nvPicPr>'
            f'<p:blipFill><a:blip r:embed="{rid}"/><a:stretch><a:fillRect/></a:stretch></p:blipFill>'
            f'<p:spPr>{xfrm(item)}<a:prstGeom prst="rect"><a:avLst/></a:prstGeom>{line}</p:spPr></p:pic>')


def table_xml(item, sid):
    widths = [c["w"] for c in item["rows"][0]["cells"]]
    grid = "".join(f'<a:gridCol w="{emu(w)}"/>' for w in widths)
    rows = ""
    for row in item["rows"]:
        tcs = ""
        for c in row["cells"]:
            b, ins = c["borders"], c["inset"]
            tcs += (f'<a:tc>{body_xml(c["paras"], {"l": 0, "r": 0, "t": 0, "b": 0}, "t", "a:txBody")}'
                    f'<a:tcPr marL="{emu(ins["l"])}" marR="{emu(ins["r"])}" marT="{emu(ins["t"])}" '
                    f'marB="{emu(ins["b"])}" anchor="{c["anchor"]}">'
                    f'{line_xml(b[3], "a:lnL")}{line_xml(b[1], "a:lnR")}{line_xml(b[0], "a:lnT")}'
                    f'{line_xml(b[2], "a:lnB")}{fill_xml(c["fill"])}</a:tcPr></a:tc>')
        rows += f'<a:tr h="{emu(row["h"])}">{tcs}</a:tr>'
    return (f'<p:graphicFrame><p:nvGraphicFramePr><p:cNvPr id="{sid}" name="Table {sid}"/>'
            '<p:cNvGraphicFramePr><a:graphicFrameLocks noGrp="1"/></p:cNvGraphicFramePr><p:nvPr/>'
            f'</p:nvGraphicFramePr>{xfrm(item, "p:xfrm", w=sum(widths))}<a:graphic>'
            '<a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/table"><a:tbl>'
            '<a:tblPr firstRow="1" bandRow="1"><a:tableStyleId>{2D5ABB26-0587-4C30-8999-92F81FD0307C}'
            f'</a:tableStyleId></a:tblPr><a:tblGrid>{grid}</a:tblGrid>{rows}</a:tbl></a:graphicData>'
            '</a:graphic></p:graphicFrame>')


def notes_xml(paras):
    body = "".join(f'<a:p><a:r><a:rPr lang="en-US" dirty="0"/><a:t>{esc(t)}</a:t></a:r></a:p>' for t in paras)
    return (XML + f'<p:notes {NS}><p:cSld><p:spTree>{GROUP}'
            '<p:sp><p:nvSpPr><p:cNvPr id="2" name="Slide Image Placeholder 1"/><p:cNvSpPr>'
            '<a:spLocks noGrp="1" noRot="1" noChangeAspect="1"/></p:cNvSpPr><p:nvPr>'
            '<p:ph type="sldImg" idx="2"/></p:nvPr></p:nvSpPr><p:spPr/></p:sp>'
            '<p:sp><p:nvSpPr><p:cNvPr id="3" name="Notes Placeholder 2"/><p:cNvSpPr>'
            '<a:spLocks noGrp="1"/></p:cNvSpPr><p:nvPr><p:ph type="body" sz="quarter" idx="3"/>'
            f'</p:nvPr></p:nvSpPr><p:spPr/><p:txBody><a:bodyPr/><a:lstStyle/>{body}</p:txBody></p:sp>'
            '</p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:notes>')


def theme_xml(brand, font):
    solid = '<a:solidFill><a:schemeClr val="phClr"/></a:solidFill>'
    lines = "".join(f'<a:ln w="{w}" cap="flat" cmpd="sng" algn="ctr">{solid}<a:prstDash val="solid"/></a:ln>'
                    for w in (9525, 25400, 38100))
    colors = [("dk1", TEXT), ("lt1", WHITE), ("dk2", brand), ("lt2", "F3F4F6"), ("accent1", brand),
              ("accent2", MUTED), ("accent3", "15803D"), ("accent4", "B45309"), ("accent5", "B91C1C"),
              ("accent6", "9CA3AF"), ("hlink", "2563EB"), ("folHlink", "7C3AED")]
    scheme = "".join(f'<a:{k}><a:srgbClr val="{v}"/></a:{k}>' for k, v in colors)
    fonts = f'<a:latin typeface="{esc(font)}"/><a:ea typeface=""/><a:cs typeface=""/>'
    return (XML + '<a:theme xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" name="POC Deck">'
            f'<a:themeElements><a:clrScheme name="POC Deck">{scheme}</a:clrScheme>'
            f'<a:fontScheme name="POC Deck"><a:majorFont>{fonts}</a:majorFont><a:minorFont>{fonts}</a:minorFont>'
            f'</a:fontScheme><a:fmtScheme name="POC Deck"><a:fillStyleLst>{solid * 3}</a:fillStyleLst>'
            f'<a:lnStyleLst>{lines}</a:lnStyleLst><a:effectStyleLst>'
            + "<a:effectStyle><a:effectLst/></a:effectStyle>" * 3
            + f'</a:effectStyleLst><a:bgFillStyleLst>{solid * 3}</a:bgFillStyleLst></a:fmtScheme>'
            '</a:themeElements><a:objectDefaults/><a:extraClrSchemeLst/></a:theme>')


def image_info(path):
    """Type and pixel size of a PNG or JPG, or None."""
    data = path.read_bytes()
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        w, h = struct.unpack(">II", data[16:24])
        return {"ext": "png", "w": w, "h": h, "data": data}
    if data[:2] == b"\xff\xd8":
        i = 2
        while i + 9 < len(data):
            if data[i] != 0xFF:
                i += 1
                continue
            marker = data[i + 1]
            if marker == 0xFF or marker == 0x01 or 0xD0 <= marker <= 0xD8:
                i += 1 if marker == 0xFF else 2
                continue
            if 0xC0 <= marker <= 0xCF and marker not in (0xC4, 0xC8, 0xCC):
                h, w = struct.unpack(">HH", data[i + 5:i + 9])
                return {"ext": "jpeg", "w": w, "h": h, "data": data}
            i += 2 + struct.unpack(">H", data[i + 2:i + 4])[0]
    return None


def url_path(url):
    parsed = urlparse(url)
    return Path(url2pathname(parsed.path)) if parsed.scheme == "file" else None


def write_pptx(path, title, slides, st, rasters):
    """slides as read in the browser; rasters maps (slide, index) to a PNG."""
    parts, media, problems = {}, {}, []
    notes_count = 0

    def add_media(file):
        if file not in media:
            info = image_info(file)
            if not info:
                return None
            media[file] = f"image{len(media) + 1}.{info['ext']}"
            parts[f"ppt/media/{media[file]}"] = info["data"]
        return media[file]

    for n, slide in enumerate(slides, 1):
        rels = [("rId1", "slideLayout", "../slideLayouts/slideLayout1.xml")]
        if slide["notes"]:
            notes_count += 1
            rels.append(("rId2", "notesSlide", f"../notesSlides/notesSlide{n}.xml"))
            parts[f"ppt/notesSlides/notesSlide{n}.xml"] = notes_xml(slide["notes"])
            parts[f"ppt/notesSlides/_rels/notesSlide{n}.xml.rels"] = rels_xml([
                ("rId1", "notesMaster", "../notesMasters/notesMaster1.xml"),
                ("rId2", "slide", f"../slides/slide{n}.xml")])
        image_rels, body, sid = {}, "", 1
        for item in slide["items"]:
            sid += 1
            kind = item["kind"]
            if kind in ("picture", "raster"):
                if kind == "raster":
                    file = rasters.get((n, item["index"]))
                    info = image_info(file) if file else None
                    if not info:
                        problems.append(f"Slide {n}: couldn't turn a diagram into a picture.")
                        continue
                    # The PNG is at twice the size; it may run a little past the element.
                    item = dict(item, w=info["w"] / 2, h=info["h"] / 2, alt="Diagram")
                else:
                    file = url_path(item["src"])
                    if not file or not file.is_file() or not add_media(file):
                        problems.append(f"Slide {n}: left out a picture it couldn't read: {item['src']}")
                        continue
                name = add_media(file)
                if file not in image_rels:
                    image_rels[file] = f"rId{len(rels) + 1}"
                    rels.append((image_rels[file], "image", f"../media/{name}"))
                body += picture_xml(item, sid, image_rels[file])
            elif kind == "table":
                body += table_xml(item, sid)
            else:
                body += shape_xml(item, sid)
        bg = ""
        if slide["background"] and slide["background"] != WHITE:
            bg = f'<p:bg><p:bgPr>{fill_xml(slide["background"])}<a:effectLst/></p:bgPr></p:bg>'
        parts[f"ppt/slides/slide{n}.xml"] = (
            XML + f'<p:sld {NS}><p:cSld>{bg}<p:spTree>{GROUP}{body}</p:spTree></p:cSld>'
            '<p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sld>')
        parts[f"ppt/slides/_rels/slide{n}.xml.rels"] = rels_xml(rels)

    count, brand, font = len(slides), st["brand"], st["font"]
    pres_rels = [("rId1", "slideMaster", "slideMasters/slideMaster1.xml"),
                 ("rId2", "notesMaster", "notesMasters/notesMaster1.xml"),
                 ("rId3", "theme", "theme/theme1.xml"),
                 ("rId4", "presProps", "presProps.xml"),
                 ("rId5", "viewProps", "viewProps.xml"),
                 ("rId6", "tableStyles", "tableStyles.xml")]
    pres_rels += [(f"rId{10 + i}", "slide", f"slides/slide{i}.xml") for i in range(1, count + 1)]
    slide_ids = "".join(f'<p:sldId id="{255 + i}" r:id="rId{10 + i}"/>' for i in range(1, count + 1))
    parts["ppt/presentation.xml"] = (
        XML + f'<p:presentation {NS} saveSubsetFonts="1"><p:sldMasterIdLst>'
        '<p:sldMasterId id="2147483648" r:id="rId1"/></p:sldMasterIdLst><p:notesMasterIdLst>'
        f'<p:notesMasterId r:id="rId2"/></p:notesMasterIdLst><p:sldIdLst>{slide_ids}</p:sldIdLst>'
        f'<p:sldSz cx="{emu(SLIDE_W)}" cy="{emu(SLIDE_H)}"/><p:notesSz cx="6858000" cy="9144000"/>'
        f'<p:defaultTextStyle><a:defPPr><a:defRPr lang="en-US"/></a:defPPr>{LEVEL1.format(sz=1800, f="mn")}'
        '</p:defaultTextStyle></p:presentation>')
    parts["ppt/_rels/presentation.xml.rels"] = rels_xml(pres_rels)
    parts["ppt/slideMasters/slideMaster1.xml"] = (
        XML + f'<p:sldMaster {NS}><p:cSld><p:bg><p:bgRef idx="1001"><a:schemeClr val="bg1"/></p:bgRef>'
        f'</p:bg><p:spTree>{GROUP}</p:spTree></p:cSld>{CLRMAP}<p:sldLayoutIdLst>'
        '<p:sldLayoutId id="2147483649" r:id="rId1"/></p:sldLayoutIdLst><p:txStyles>'
        f'<p:titleStyle>{LEVEL1.format(sz=4400, f="mj")}</p:titleStyle>'
        f'<p:bodyStyle>{LEVEL1.format(sz=2800, f="mn")}</p:bodyStyle>'
        f'<p:otherStyle>{LEVEL1.format(sz=1800, f="mn")}</p:otherStyle></p:txStyles></p:sldMaster>')
    parts["ppt/slideMasters/_rels/slideMaster1.xml.rels"] = rels_xml([
        ("rId1", "slideLayout", "../slideLayouts/slideLayout1.xml"),
        ("rId2", "theme", "../theme/theme1.xml")])
    parts["ppt/slideLayouts/slideLayout1.xml"] = (
        XML + f'<p:sldLayout {NS} type="blank" preserve="1"><p:cSld name="Blank"><p:spTree>{GROUP}'
        '</p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sldLayout>')
    parts["ppt/slideLayouts/_rels/slideLayout1.xml.rels"] = rels_xml([
        ("rId1", "slideMaster", "../slideMasters/slideMaster1.xml")])
    parts["ppt/notesMasters/notesMaster1.xml"] = (
        XML + f'<p:notesMaster {NS}><p:cSld><p:bg><p:bgRef idx="1001"><a:schemeClr val="bg1"/></p:bgRef>'
        f'</p:bg><p:spTree>{GROUP}'
        '<p:sp><p:nvSpPr><p:cNvPr id="2" name="Slide Image Placeholder 1"/><p:cNvSpPr>'
        '<a:spLocks noGrp="1" noRot="1" noChangeAspect="1"/></p:cNvSpPr><p:nvPr>'
        '<p:ph type="sldImg" idx="2"/></p:nvPr></p:nvSpPr><p:spPr><a:xfrm><a:off x="685800" y="1143000"/>'
        '<a:ext cx="5486400" cy="3086100"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom>'
        '<a:noFill/><a:ln w="12700"><a:solidFill><a:prstClr val="black"/></a:solidFill></a:ln></p:spPr></p:sp>'
        '<p:sp><p:nvSpPr><p:cNvPr id="3" name="Notes Placeholder 2"/><p:cNvSpPr><a:spLocks noGrp="1"/>'
        '</p:cNvSpPr><p:nvPr><p:ph type="body" sz="quarter" idx="3"/></p:nvPr></p:nvSpPr><p:spPr><a:xfrm>'
        '<a:off x="685800" y="4400550"/><a:ext cx="5486400" cy="3600450"/></a:xfrm><a:prstGeom prst="rect">'
        '<a:avLst/></a:prstGeom></p:spPr><p:txBody><a:bodyPr vert="horz" lIns="91440" tIns="45720" '
        'rIns="91440" bIns="45720" rtlCol="0"/><a:lstStyle/><a:p><a:endParaRPr lang="en-US"/></a:p>'
        f'</p:txBody></p:sp></p:spTree></p:cSld>{CLRMAP}'
        f'<p:notesStyle>{LEVEL1.format(sz=1200, f="mn")}</p:notesStyle></p:notesMaster>')
    parts["ppt/notesMasters/_rels/notesMaster1.xml.rels"] = rels_xml([
        ("rId1", "theme", "../theme/theme2.xml")])
    parts["ppt/theme/theme1.xml"] = theme_xml(brand, font)
    parts["ppt/theme/theme2.xml"] = theme_xml(brand, font)
    parts["ppt/presProps.xml"] = XML + f"<p:presentationPr {NS}/>"
    parts["ppt/viewProps.xml"] = (
        XML + f'<p:viewPr {NS}><p:normalViewPr><p:restoredLeft sz="15620"/><p:restoredTop sz="94660"/>'
        '</p:normalViewPr><p:gridSpacing cx="76200" cy="76200"/></p:viewPr>')
    parts["ppt/tableStyles.xml"] = (
        XML + '<a:tblStyleLst xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
        'def="{5C22544A-7EE6-4342-B048-85BDC9FD1C3A}"/>')
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    parts["docProps/core.xml"] = (
        XML + '<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" '
        'xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" '
        'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
        f'<dc:title>{esc(title)}</dc:title><dcterms:created xsi:type="dcterms:W3CDTF">{now}</dcterms:created>'
        f'<dcterms:modified xsi:type="dcterms:W3CDTF">{now}</dcterms:modified></cp:coreProperties>')
    parts["docProps/app.xml"] = (
        XML + '<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties" '
        'xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">'
        '<Application>Microsoft Office PowerPoint</Application><PresentationFormat>Widescreen</PresentationFormat>'
        f'<Slides>{count}</Slides><Notes>{notes_count}</Notes></Properties>')

    root_rels = rels_xml([("rId1", "officeDocument", "ppt/presentation.xml"),
                          ("rId2", "core-properties", "docProps/core.xml"),
                          ("rId3", "extended-properties", "docProps/app.xml")])
    theme_type = "application/vnd.openxmlformats-officedocument.theme+xml"
    overrides = [("/ppt/presentation.xml", CT + "presentation.main+xml"),
                 ("/ppt/slideMasters/slideMaster1.xml", CT + "slideMaster+xml"),
                 ("/ppt/slideLayouts/slideLayout1.xml", CT + "slideLayout+xml"),
                 ("/ppt/notesMasters/notesMaster1.xml", CT + "notesMaster+xml"),
                 ("/ppt/theme/theme1.xml", theme_type),
                 ("/ppt/theme/theme2.xml", theme_type),
                 ("/ppt/presProps.xml", CT + "presProps+xml"),
                 ("/ppt/viewProps.xml", CT + "viewProps+xml"),
                 ("/ppt/tableStyles.xml", CT + "tableStyles+xml"),
                 ("/docProps/core.xml", "application/vnd.openxmlformats-package.core-properties+xml"),
                 ("/docProps/app.xml", "application/vnd.openxmlformats-officedocument.extended-properties+xml")]
    for name in sorted(parts):
        if name.startswith("ppt/slides/slide"):
            overrides.append(("/" + name, CT + "slide+xml"))
        elif name.startswith("ppt/notesSlides/notesSlide"):
            overrides.append(("/" + name, CT + "notesSlide+xml"))
    types = (XML + '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
             '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
             '<Default Extension="xml" ContentType="application/xml"/>'
             '<Default Extension="png" ContentType="image/png"/>'
             '<Default Extension="jpeg" ContentType="image/jpeg"/>'
             + "".join(f'<Override PartName="{n}" ContentType="{t}"/>' for n, t in overrides) + "</Types>")

    if path.exists():
        path.unlink()
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", types)
        z.writestr("_rels/.rels", root_rels)
        for name, data in parts.items():
            z.writestr(name, data)
    return problems


# ---------------------------------------------------------------- main

def deck_title(deck_path):
    m = re.search(r"<title>(.*?)</title>", deck_path.read_text(encoding="utf-8"), re.S | re.I)
    return html.unescape(" ".join(m.group(1).split())) if m else deck_path.stem


def main():
    parser = argparse.ArgumentParser(description="Build a PDF, and a PowerPoint if asked, from a deck in HTML.")
    parser.add_argument("deck", type=Path)
    parser.add_argument("--pptx", action="store_true", help="also write an editable PowerPoint")
    parser.add_argument("--pictures", action="store_true", help="also save a PNG of each slide, for looking at them")
    args = parser.parse_args()

    deck_path = args.deck.resolve()
    if not deck_path.is_file():
        sys.exit(f"Not found: {deck_path}")
    st = read_settings()
    browser = find_browser()
    if not browser:
        print("Couldn't find Chrome, Edge, or Chromium, which renders the deck. Install one and run again.")
        sys.exit(3)

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        page = render_page(deck_path, st, tmp)
        deck = read_deck(browser, page)
        if deck is None:
            print("Couldn't read the deck in the browser. Check that it opens in Chrome.")
            sys.exit(3)
        slides = deck["slides"]
        if not slides:
            sys.exit('No slides: each slide is a <section class="slide">.')
        problems = [f'Slide {p["slide"]}: {p["text"]}' for p in deck["problems"]]

        pdf_path = deck_path.with_suffix(".pdf")
        if print_pdf(browser, page, pdf_path):
            print(f"PDF: {pdf_path} ({len(slides)} slides)")
        else:
            print("No PDF: the browser didn't print it.")

        if args.pptx:
            rasters = {}
            for n, slide in enumerate(slides, 1):
                for item in slide["items"]:
                    if item["kind"] == "raster":
                        png = tmp / f"raster-{n}-{item['index']}.png"
                        url = f"{page.as_uri()}#raster={n}:{item['index']}"
                        if screenshot(browser, url, png, math.ceil(item["w"]), math.ceil(item["h"]),
                                      scale=2, transparent=True):
                            rasters[(n, item["index"])] = png
            pptx_path = deck_path.with_suffix(".pptx")
            problems += write_pptx(pptx_path, deck_title(deck_path), slides, st, rasters)
            print(f"PowerPoint: {pptx_path}")

        if args.pictures:
            folder = Path(tempfile.mkdtemp(prefix="deck-slides-"))
            for n in range(1, len(slides) + 1):
                screenshot(browser, f"{page.as_uri()}#only={n}", folder / f"slide-{n:02}.png", SLIDE_W, SLIDE_H)
            print(f"Slide pictures: {folder}")

    for p in problems:
        print(p)
    if problems:
        print("Cut words from those slides, move detail to the speaker notes, or split them, and run again.")
        sys.exit(2)
    print("Fit: everything fits.")


if __name__ == "__main__":
    main()

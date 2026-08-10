/* MCC Simulation Viewer — 2D field playback + metric charts. No dependencies. */
(function () {
  "use strict";

  // -------------------------------------------------------------- tabs ---
  const tabs = document.querySelectorAll(".tab");
  tabs.forEach(t => t.addEventListener("click", () => {
    tabs.forEach(x => x.classList.remove("is-active"));
    document.querySelectorAll(".panel").forEach(p => p.classList.remove("is-active"));
    t.classList.add("is-active");
    document.getElementById("panel-" + t.dataset.tab).classList.add("is-active");
    if (t.dataset.tab === "metrics") drawCharts();
    if (t.dataset.tab === "twod") requestAnimationFrame(() => render(cur));
  }));

  // -------------------------------------------------------- colormaps ---
  const WALL = [43, 52, 64], IFACE = [56, 211, 159];
  const lerp = (a, b, t) => a + (b - a) * t;
  const mix = (c1, c2, t) => [lerp(c1[0], c2[0], t), lerp(c1[1], c2[1], t), lerp(c1[2], c2[2], t)];
  const OIL = [233, 224, 200], WATER = [23, 99, 201];
  const VIR = [[68,1,84],[59,82,139],[33,145,140],[94,201,98],[253,231,37]];
  function ramp(stops, v) {
    const s = v * (stops.length - 1), i = Math.min(stops.length - 2, Math.floor(s));
    return mix(stops[i], stops[i + 1], s - i);
  }
  const cmaps = {
    water: v => mix(OIL, WATER, v),
    viridis: v => ramp(VIR, v),
    gray: v => { const g = 30 + v * 205; return [g, g, g]; },
  };

  // ---------------------------------------------------------- 2D field ---
  const cvs = document.getElementById("field");
  const ctx = cvs.getContext("2d");
  const off = document.createElement("canvas");
  const octx = off.getContext("2d");

  const els = {
    play: document.getElementById("play"), scrub: document.getElementById("scrub"),
    tlabel: document.getElementById("tlabel"), speed: document.getElementById("speed"),
    cmap: document.getElementById("cmap"), iface: document.getElementById("iface"),
    smooth: document.getElementById("smooth"), cap: document.getElementById("twod-cap"),
    bar: document.getElementById("colorbar"), dataline: document.getElementById("dataline"),
  };

  let meta = null, bytes = [], cur = 0, playing = false, lastT = 0;

  function decode(b64) {
    const bin = atob(b64), n = bin.length, u = new Uint8Array(n);
    for (let i = 0; i < n; i++) u[i] = bin.charCodeAt(i);
    return u;
  }

  function initField() {
    if (typeof window.MCC2D === "undefined") {
      els.cap.textContent = "No 2D field data found. Generate it with export_web.py (see README).";
      return;
    }
    meta = window.MCC2D.meta;
    bytes = window.MCC2D.frames.map(decode);
    off.width = meta.nx; off.height = meta.ny;
    const W = 1000, H = Math.round(W * meta.ny / meta.nx);
    cvs.width = W; cvs.height = H;

    els.scrub.max = String(bytes.length - 1);
    paintColorbar();
    els.cap.innerHTML = `alpha.water field, 2D T-junction (<span class="mono">interFoam</span> VOF) · `
      + `${bytes.length} frames · grid ${meta.nx}×${meta.ny} @ ${meta.dx_um} µm/px · `
      + `domain ${(meta.x1_mm - meta.x0_mm).toFixed(2)}×${(meta.y1_mm - meta.y0_mm).toFixed(2)} mm.`;
    els.dataline.textContent = `2D: ${meta.ncells} cells · t ${meta.times_ms[0]}–${meta.times_ms[meta.times_ms.length - 1]} ms`;
    render(Math.round(bytes.length * 0.66));    // open on a frame with a detached droplet...
    setPlay(true);                              // ...then autoplay the loop (lead with motion)
  }

  function render(i) {
    if (!meta) return;
    cur = Math.max(0, Math.min(bytes.length - 1, i));
    const b = bytes[cur], nx = meta.nx, ny = meta.ny, wall = meta.wall;
    const cmap = cmaps[els.cmap.value] || cmaps.water, hi = els.iface.checked;
    const img = octx.createImageData(nx, ny);
    for (let R = 0; R < ny; R++) {
      const r = ny - 1 - R;                     // grid row 0 = bottom → flip for canvas
      for (let c = 0; c < nx; c++) {
        const val = b[r * nx + c];
        let col;
        if (val === wall) col = WALL;
        else {
          const v = val / 250;
          col = cmap(v);
          if (hi && v > 0.35 && v < 0.65) col = mix(col, IFACE, 0.65);
        }
        const o = (R * nx + c) * 4;
        img.data[o] = col[0]; img.data[o + 1] = col[1]; img.data[o + 2] = col[2]; img.data[o + 3] = 255;
      }
    }
    octx.putImageData(img, 0, 0);
    ctx.imageSmoothingEnabled = els.smooth.checked;
    ctx.clearRect(0, 0, cvs.width, cvs.height);
    ctx.drawImage(off, 0, 0, nx, ny, 0, 0, cvs.width, cvs.height);
    els.scrub.value = String(cur);
    els.tlabel.textContent = meta.times_ms[cur].toFixed(1) + " ms";
  }

  function paintColorbar() {
    const cmap = cmaps[els.cmap.value] || cmaps.water;
    const stops = [];
    for (let k = 0; k <= 10; k++) { const c = cmap(1 - k / 10); stops.push(`rgb(${c[0]|0},${c[1]|0},${c[2]|0}) ${k*10}%`); }
    els.bar.style.background = `linear-gradient(180deg, ${stops.join(",")})`;
    els.bar.title = "water (top) → oil (bottom)";
  }

  function loop(ts) {
    if (!playing) return;
    const fps = +els.speed.value;
    if (ts - lastT >= 1000 / fps) {
      lastT = ts;
      render((cur + 1) % bytes.length);
    }
    requestAnimationFrame(loop);
  }
  function setPlay(on) {
    playing = on; els.play.textContent = on ? "❚❚" : "▶";
    if (on) { lastT = 0; requestAnimationFrame(loop); }
  }

  els.play.addEventListener("click", () => setPlay(!playing));
  els.scrub.addEventListener("input", e => { setPlay(false); render(+e.target.value); });
  els.cmap.addEventListener("change", () => { paintColorbar(); render(cur); });
  els.iface.addEventListener("change", () => render(cur));
  els.smooth.addEventListener("change", () => render(cur));

  // ----------------------------------------------------------- charts ---
  const CA_COLORS = { "0.016": "#4aa8ff", "0.032": "#38d39f", "0.048": "#ffb454" };
  let chartsDrawn = false;

  function drawCharts() {
    if (chartsDrawn) return;
    if (typeof window.MCCMETRICS === "undefined") return;
    const pts = window.MCCMETRICS.sweep;
    chart(document.getElementById("chartL"), pts, "q", "L_over_w", "q = Q_water / Q_oil", "L / w");
    chart(document.getElementById("chartF"), pts, "q", "freq_Hz", "q = Q_water / Q_oil", "frequency (Hz)");
    document.getElementById("metrics-cap").innerHTML =
      `Velocity-driven sweep · <span class="mono">${window.MCCMETRICS.source}</span> · ${pts.length} operating points · colour = Ca.`;
    chartsDrawn = true;
  }

  function chart(canvas, pts, xk, yk, xlabel, ylabel) {
    const c = canvas.getContext("2d"), W = canvas.width, H = canvas.height;
    const m = { l: 52, r: 12, t: 14, b: 42 };
    const xs = pts.map(p => p[xk]), ys = pts.map(p => p[yk]);
    const xmin = 0, xmax = Math.max(...xs) * 1.08;
    const ymin = 0, ymax = Math.max(...ys) * 1.12;
    const X = v => m.l + (v - xmin) / (xmax - xmin) * (W - m.l - m.r);
    const Y = v => H - m.b - (v - ymin) / (ymax - ymin) * (H - m.t - m.b);

    c.clearRect(0, 0, W, H);
    c.strokeStyle = "#2a323d"; c.fillStyle = "#9aa7b4"; c.lineWidth = 1;
    c.font = "11px ui-monospace,Menlo,monospace";
    // grid + ticks (numbers right-aligned to the axis so they don't hit the label)
    c.textAlign = "right";
    for (let k = 0; k <= 4; k++) {
      const gy = m.t + k / 4 * (H - m.t - m.b), val = ymax - k / 4 * (ymax - ymin);
      c.strokeStyle = "#20272f"; c.beginPath(); c.moveTo(m.l, gy); c.lineTo(W - m.r, gy); c.stroke();
      c.fillStyle = "#9aa7b4"; c.fillText(val.toFixed(val < 5 ? 1 : 0), m.l - 6, gy + 3);
    }
    c.textAlign = "center";
    for (let k = 0; k <= 4; k++) {
      const gx = m.l + k / 4 * (W - m.l - m.r), val = xmin + k / 4 * (xmax - xmin);
      c.fillText(val.toFixed(2), gx, H - m.b + 16);
    }
    // axes
    c.strokeStyle = "#3a434f"; c.beginPath();
    c.moveTo(m.l, m.t); c.lineTo(m.l, H - m.b); c.lineTo(W - m.r, H - m.b); c.stroke();
    c.fillStyle = "#c7d0da";
    c.fillText(xlabel, m.l + (W - m.l - m.r) / 2, H - 8);
    c.save(); c.translate(11, H / 2); c.rotate(-Math.PI / 2);
    c.fillText(ylabel, 0, 0); c.restore();
    c.textAlign = "left";

    // group by Ca -> line + points
    const groups = {};
    pts.forEach(p => (groups[p.Ca] = groups[p.Ca] || []).push(p));
    Object.keys(groups).sort((a, b) => a - b).forEach(ca => {
      const g = groups[ca].slice().sort((a, b) => a[xk] - b[xk]);
      const col = CA_COLORS[ca] || "#e6edf3";
      c.strokeStyle = col; c.fillStyle = col; c.lineWidth = 2;
      c.beginPath();
      g.forEach((p, i) => { const px = X(p[xk]), py = Y(p[yk]); i ? c.lineTo(px, py) : c.moveTo(px, py); });
      c.stroke();
      g.forEach(p => { c.beginPath(); c.arc(X(p[xk]), Y(p[yk]), 3.4, 0, 7); c.fill(); });
    });
    // legend (with a backing panel so it stays legible over the curves)
    const keys = Object.keys(groups).sort((a, b) => a - b);
    const lx = W - m.r - 84, lw = 80, lh = keys.length * 15 + 8;
    c.fillStyle = "rgba(11,14,19,.82)"; c.strokeStyle = "#2a323d";
    c.fillRect(lx - 6, m.t + 2, lw, lh); c.strokeRect(lx - 6, m.t + 2, lw, lh);
    let ly = m.t + 8;
    keys.forEach(ca => {
      const col = CA_COLORS[ca] || "#e6edf3";
      c.fillStyle = col; c.fillRect(lx, ly, 10, 10);
      c.fillStyle = "#c7d0da"; c.fillText("Ca " + ca, lx + 16, ly + 9);
      ly += 15;
    });
  }

  // ------------------------------------------------------------- boot ---
  initField();
})();

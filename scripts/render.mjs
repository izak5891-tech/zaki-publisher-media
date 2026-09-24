import fs from "node:fs";
import path from "node:path";
import { createHash } from "node:crypto";
import sharp from "sharp";

const ROOT = process.cwd();
const JOBS = path.join(ROOT, "render-jobs");

function escapeXml(s = "") {
  return String(s)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function listJson(dir) {
  if (!fs.existsSync(dir)) return [];
  const out = [];
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    const p = path.join(dir, e.name);
    if (e.isDirectory()) out.push(...listJson(p));
    else if (e.isFile() && e.name.endsWith(".json")) out.push(p);
  }
  return out.sort();
}

function wrapParagraph(text, max = 34) {
  const words = String(text || "").split(/\s+/).filter(Boolean);
  const lines = [];
  let line = "";
  for (const word of words) {
    const next = line ? line + " " + word : word;
    if (next.length > max && line) {
      lines.push(line);
      line = word;
    } else {
      line = next;
    }
  }
  if (line) lines.push(line);
  return lines;
}

function wrapPreserveNewlines(text, max = 34) {
  const out = [];
  for (const paragraph of String(text || "").split(/\r?\n/)) {
    if (!paragraph.trim()) {
      out.push("");
      continue;
    }
    out.push(...wrapParagraph(paragraph, max));
  }
  return out;
}

async function measureTextWidth(text, {
  fontSize,
  fontWeight = 500,
  rtl = false,
  fontFamily = "Noto Naskh Arabic, DejaVu Sans, sans-serif",
}) {
  if (!String(text || "").trim()) return 0;
  const canvasWidth = 3200;
  const canvasHeight = Math.max(180, Math.ceil(fontSize * 2.4));
  const direction = rtl ? 'direction="rtl" unicode-bidi="plaintext"' : "";
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${canvasWidth}" height="${canvasHeight}">
    <rect width="100%" height="100%" fill="transparent"/>
    <text x="${canvasWidth / 2}" y="${Math.ceil(canvasHeight * 0.68)}" text-anchor="middle" ${direction}
      font-family="${fontFamily}" font-size="${fontSize}" font-weight="${fontWeight}" fill="#111">${escapeXml(text)}</text>
  </svg>`;

  const { info } = await sharp(Buffer.from(svg))
    .trim({ background: { r: 0, g: 0, b: 0, alpha: 0 } })
    .png()
    .toBuffer({ resolveWithObject: true });

  return info.width || 0;
}

function sha256(buffer) {
  return createHash("sha256").update(buffer).digest("hex");
}

for (const file of listJson(JOBS)) {
  const job = JSON.parse(fs.readFileSync(file, "utf8"));
  const width = Number(job.width || 1080);
  const height = Number(job.height || 1350);
  const output = String(job.output || "").replace(/^\/+/, "");
  if (!output || !output.endsWith(".png")) throw new Error(`Invalid output in ${file}`);

  const rtl = job.rtl === true;
  const titleRaw = String(job.title || "Zaki Publisher");
  const subtitleRaw = String(job.subtitle || "");
  const footerRaw = String(job.footer || "");

  const bodyLines = Array.isArray(job.body_lines)
    ? job.body_lines.map(x => String(x ?? ""))
    : wrapPreserveNewlines(job.body || "", Number(job.wrap || 34));

  const frameX = 70;
  const frameWidth = width - 140;
  const bodyLeft = 150;
  const bodyRight = width - 150;
  const safeTextWidth = bodyRight - bodyLeft;

  const titleFont = Number(job.title_font_size || 34);
  const subtitleFont = Number(job.subtitle_font_size || 62);
  const bodyFont = Number(job.body_font_size || 46);
  const footerFont = Number(job.footer_font_size || 28);
  const bodyStartY = Number(job.body_start_y || 560);
  const bodyLineHeight = Number(job.body_line_height || 74);
  const bodyBottomLimit = height - 245;

  const maxBodyLines = Math.max(1, Math.floor((bodyBottomLimit - bodyStartY) / bodyLineHeight) + 1);
  if (bodyLines.length > maxBodyLines) {
    throw new Error(
      `QC FAIL ${file}: body has ${bodyLines.length} lines but safe layout allows ${maxBodyLines}. Reduce text or font size before approval.`
    );
  }

  const measured = [];
  const measureAndAssert = async (label, value, fontSize, fontWeight, limit = safeTextWidth) => {
    if (!String(value || "").trim()) return;
    const px = await measureTextWidth(value, { fontSize, fontWeight, rtl });
    measured.push({ label, width_px: px, limit_px: limit });
    if (px > limit) {
      throw new Error(
        `QC FAIL ${file}: ${label} is ${px}px wide; safe width is ${limit}px. Re-wrap or reduce font before approval.`
      );
    }
  };

  await measureAndAssert("title", titleRaw, titleFont, 700, safeTextWidth);
  await measureAndAssert("subtitle", subtitleRaw, subtitleFont, 700, safeTextWidth);
  for (let i = 0; i < bodyLines.length; i++) {
    await measureAndAssert(`body line ${i + 1}`, bodyLines[i], bodyFont, 500, safeTextWidth);
  }
  await measureAndAssert("footer", footerRaw, footerFont, 400, safeTextWidth);

  const title = escapeXml(titleRaw);
  const subtitle = escapeXml(subtitleRaw);
  const footer = escapeXml(footerRaw);
  const direction = rtl ? 'direction="rtl" unicode-bidi="plaintext"' : "";

  // IMPORTANT: in RTL SVG text, "start" anchors to the right edge.
  // The previous "end" anchor caused Urdu text to extend beyond the frame.
  const bodyAnchor = rtl ? "start" : "middle";
  const bodyX = rtl ? bodyRight : width / 2;

  const bodySvg = bodyLines.map((line, i) => {
    if (!line.trim()) return "";
    return `<text x="${bodyX}" y="${bodyStartY + i * bodyLineHeight}" text-anchor="${bodyAnchor}" ${direction}
      font-family="Noto Naskh Arabic, DejaVu Sans, sans-serif"
      font-size="${bodyFont}" font-weight="500" fill="#111">${escapeXml(line)}</text>`;
  }).join("\n");

  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}">
    <rect width="100%" height="100%" fill="#ffffff"/>
    <rect x="0" y="0" width="${width}" height="22" fill="#0f6b45"/>
    <rect x="${frameX}" y="110" width="${frameWidth}" height="${height - 220}" rx="42" fill="#fbfaf6" stroke="#0f6b45" stroke-width="3"/>
    <text x="${width / 2}" y="260" text-anchor="middle" ${direction}
      font-family="Noto Naskh Arabic, DejaVu Sans, sans-serif"
      font-size="${titleFont}" font-weight="700" fill="#0f6b45">${title}</text>
    <text x="${width / 2}" y="340" text-anchor="middle" ${direction}
      font-family="Noto Naskh Arabic, DejaVu Sans, sans-serif"
      font-size="${subtitleFont}" font-weight="700" fill="#111">${subtitle}</text>
    <line x1="190" y1="405" x2="${width - 190}" y2="405" stroke="#0f6b45" stroke-width="3"/>
    ${bodySvg}
    <text x="${width / 2}" y="${height - 175}" text-anchor="middle" ${direction}
      font-family="Noto Naskh Arabic, DejaVu Sans, sans-serif"
      font-size="${footerFont}" fill="#444">${footer}</text>
  </svg>`;

  const outPath = path.join(ROOT, output);
  fs.mkdirSync(path.dirname(outPath), { recursive: true });
  const png = await sharp(Buffer.from(svg)).png({ compressionLevel: 9 }).toBuffer();
  await fs.promises.writeFile(outPath, png);

  const manifest = {
    renderer_version: 2,
    source_job: path.relative(ROOT, file),
    output,
    sha256: sha256(png),
    width,
    height,
    qc: {
      passed: true,
      rtl,
      safe_text_width_px: safeTextWidth,
      body_line_count: bodyLines.length,
      max_body_lines: maxBodyLines,
      measured,
    },
  };
  await fs.promises.writeFile(
    `${outPath}.manifest.json`,
    JSON.stringify(manifest, null, 2) + "\n",
    "utf8"
  );

  console.log(`Rendered + QC passed: ${output}`);
  console.log(`SHA256: ${manifest.sha256}`);
}

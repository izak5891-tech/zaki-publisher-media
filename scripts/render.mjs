import fs from "node:fs";
import path from "node:path";
import sharp from "sharp";

const ROOT = process.cwd();
const JOBS = path.join(ROOT, "render-jobs");

function escapeXml(s="") {
  return String(s)
    .replaceAll("&","&amp;")
    .replaceAll("<","&lt;")
    .replaceAll(">","&gt;")
    .replaceAll('"',"&quot;");
}

function listJson(dir) {
  if (!fs.existsSync(dir)) return [];
  const out=[];
  for (const e of fs.readdirSync(dir,{withFileTypes:true})) {
    const p=path.join(dir,e.name);
    if (e.isDirectory()) out.push(...listJson(p));
    else if (e.isFile() && e.name.endsWith(".json")) out.push(p);
  }
  return out.sort();
}

function wrap(text, max=34) {
  const words=String(text||"").split(/\s+/).filter(Boolean);
  const lines=[];
  let line="";
  for (const word of words) {
    const next=line ? line+" "+word : word;
    if (next.length>max && line) {
      lines.push(line);
      line=word;
    } else line=next;
  }
  if (line) lines.push(line);
  return lines;
}

for (const file of listJson(JOBS)) {
  const job=JSON.parse(fs.readFileSync(file,"utf8"));
  const width=Number(job.width||1080);
  const height=Number(job.height||1350);
  const output=String(job.output||"").replace(/^\/+/, "");
  if (!output || !output.endsWith(".png")) throw new Error(`Invalid output in ${file}`);

  const title=escapeXml(job.title||"Zaki Publisher");
  const subtitle=escapeXml(job.subtitle||"");
  const bodyLines=wrap(job.body||"", Number(job.wrap||34)).slice(0,12);
  const footer=escapeXml(job.footer||"");
  const rtl=job.rtl===true;
  const anchor=rtl ? "end" : "middle";
  const x=rtl ? width-90 : width/2;
  const direction=rtl ? 'direction="rtl" unicode-bidi="plaintext"' : "";

  const bodySvg=bodyLines.map((line,i)=>
    `<text x="${x}" y="${590+i*72}" text-anchor="${anchor}" ${direction}
      font-family="Noto Naskh Arabic, DejaVu Sans, sans-serif"
      font-size="46" font-weight="500" fill="#111">${escapeXml(line)}</text>`
  ).join("\n");

  const svg=`<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}">
    <rect width="100%" height="100%" fill="#ffffff"/>
    <rect x="0" y="0" width="${width}" height="22" fill="#0f6b45"/>
    <rect x="70" y="110" width="${width-140}" height="${height-220}" rx="42" fill="#fbfaf6" stroke="#0f6b45" stroke-width="3"/>
    <text x="${width/2}" y="260" text-anchor="middle" ${direction}
      font-family="Noto Naskh Arabic, DejaVu Sans, sans-serif"
      font-size="34" font-weight="700" fill="#0f6b45">${title}</text>
    <text x="${width/2}" y="340" text-anchor="middle" ${direction}
      font-family="Noto Naskh Arabic, DejaVu Sans, sans-serif"
      font-size="62" font-weight="700" fill="#111">${subtitle}</text>
    <line x1="190" y1="405" x2="${width-190}" y2="405" stroke="#0f6b45" stroke-width="3"/>
    ${bodySvg}
    <text x="${width/2}" y="${height-175}" text-anchor="middle" font-family="DejaVu Sans, sans-serif"
      font-size="28" fill="#444">${footer}</text>
  </svg>`;

  const outPath=path.join(ROOT,output);
  fs.mkdirSync(path.dirname(outPath),{recursive:true});
  await sharp(Buffer.from(svg)).png({compressionLevel:9}).toFile(outPath);
  console.log(`Rendered ${output}`);
}

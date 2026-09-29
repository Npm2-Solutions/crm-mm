// Renders one cut of the video, from the scenes to the finished file.
//   node render.mjs [fmt] [plan] [output]
//   fmt:  h (1920×1080) · v (1080×1920) · p (1080×1350)
//   plan: full · reel · ad-chat · ad-fatt · ad-app · ad-ex
// Captures at twice the resolution and scales down, so motion below a pixel stays smooth;
// the soundtrack is built by audio.py from the same plan; the last settled frame
// becomes the cover and frame 0.
import { chromium } from '/opt/node22/lib/node_modules/playwright/index.mjs';
import { spawn, execFileSync } from 'node:child_process';
import fs from 'node:fs';

const [fmt = 'h', plan = 'full', output = '../DottorCloud.mp4'] = process.argv.slice(2);
const [W, H] = { h: [1920, 1080], v: [1080, 1920], p: [1080, 1350] }[fmt];
const FFMPEG = execFileSync('python3', ['-c', 'import imageio_ffmpeg as f;print(f.get_ffmpeg_exe())']).toString().trim();
const FPS = 30, tag = `${plan}-${fmt}`;

const b = await chromium.launch();
const p = await b.newPage({ viewport: { width: W, height: H }, deviceScaleFactor: 2 });
p.on('pageerror', (e) => console.log('ERR', e.message));
await p.goto(`file://${process.cwd()}/video.html?fmt=${fmt}&plan=${plan}`);
await p.evaluate(() => window.ready);
const DUR = await p.evaluate(() => window.DUR);
fs.writeFileSync(`plan-${tag}.json`, JSON.stringify(await p.evaluate(() => window.PLAN_OUT)));
execFileSync('python3', ['audio.py', `plan-${tag}.json`, `audio-${tag}.wav`], { stdio: 'inherit' });

const raw = `raw-${tag}.mp4`, N = Math.round(DUR * FPS);
const ff = spawn(FFMPEG, ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'mjpeg', '-i', '-', '-i', `audio-${tag}.wav`,
  '-vf', `scale=${W}:${H}:flags=lanczos`, '-c:v', 'libx264', '-preset', 'slow', '-crf', '17', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', raw], { stdio: ['pipe', 'inherit', 'inherit'] });
for (let i = 0; i < N; i++) {
  await p.evaluate((t) => window.render(t), i / FPS);
  const buf = await p.screenshot({ type: 'jpeg', quality: 95 });
  if (!ff.stdin.write(buf)) await new Promise((r) => ff.stdin.once('drain', r));
  if (i % 150 === 0) console.log(tag, 'frame', i, '/', N);
}
ff.stdin.end();
await new Promise((r) => ff.on('close', r));
await b.close();

// cover: the last settled frame, also baked in as frame 0 so every platform shows it
const cover = output.replace(/\.mp4$/, '.jpg');
execFileSync(FFMPEG, ['-loglevel', 'error', '-y', '-ss', String(Math.max(0, DUR - 0.5)), '-i', raw, '-frames:v', '1', '-q:v', '2', cover]);
execFileSync(FFMPEG, ['-loglevel', 'error', '-y', '-i', raw, '-i', cover, '-filter_complex', "[0:v][1:v]overlay=0:0:enable='eq(n,0)',format=yuv420p[v]",
  '-map', '[v]', '-map', '0:a', '-c:v', 'libx264', '-preset', 'slow', '-crf', '18', '-c:a', 'copy', '-movflags', '+faststart', output]);
console.log('done', output, DUR.toFixed(1) + 's');

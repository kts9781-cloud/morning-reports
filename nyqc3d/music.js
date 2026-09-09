// Original, browser-synthesized ambient music. No recording or network. Autoplay is subject to browser policy.
const button = document.createElement('button');
button.id = 'musicButton';
button.textContent = '♫ 음악 켜기';
button.setAttribute('aria-pressed', 'false');
const volumeLabel = document.createElement('label');
volumeLabel.id = 'musicVolume';
volumeLabel.hidden = true;
volumeLabel.innerHTML = '음량 <input type="range" min="0" max="100" value="30" aria-label="배경음 볼륨"><span>30%</span>';
document.querySelector('#toolbar').insertBefore(button, document.querySelector('#guideButton'));
document.querySelector('#toolbar').append(volumeLabel);
const slider = volumeLabel.querySelector('input');
let context, master, timer, nextNote = 0, step = 0, enabled = false, wanted = false;
const chords = [[48, 55, 60, 64, 67], [45, 52, 57, 60, 64], [41, 48, 53, 57, 60], [43, 50, 55, 59, 62]];

export function playTone(ctx, destination, midi, when, duration = 5, strength = 0.12) {
  const envelope = ctx.createGain();
  envelope.gain.setValueAtTime(0, when);
  envelope.gain.linearRampToValueAtTime(strength, when + 0.035);
  envelope.gain.exponentialRampToValueAtTime(0.0001, when + duration);
  envelope.connect(destination);
  const oscillators = [1, 2, 3].map((harmonic, i) => {
    const oscillator = ctx.createOscillator();
    const gain = ctx.createGain();
    oscillator.type = 'sine';
    oscillator.frequency.value = 440 * 2 ** ((midi - 69) / 12) * harmonic;
    gain.gain.value = [0.72, 0.2, 0.05][i];
    oscillator.connect(gain).connect(envelope);
    oscillator.start(when);
    oscillator.stop(when + duration + 0.05);
    oscillator.onended = () => { oscillator.disconnect(); gain.disconnect(); };
    return oscillator;
  });
  oscillators[0].addEventListener('ended', () => envelope.disconnect());
}

function schedule() {
  if (!enabled || context.state !== 'running') return;
  if (nextNote < context.currentTime) nextNote = context.currentTime + 0.05;
  while (nextNote < context.currentTime + 0.3) {
    const chord = chords[Math.floor(step / 8) % chords.length];
    const index = [0, 2, 4, 3, 1, 3, 4, 2][step % 8];
    playTone(context, master, chord[index] + 12, nextNote, 5.5, 0.13);
    if (step % 8 === 0) {
      playTone(context, master, chord[0], nextNote, 9, 0.1);
      playTone(context, master, chord[2], nextNote + 0.08, 8, 0.055);
    }
    step++;
    nextNote += 1.2;
  }
}

function updateUI() {
  document.body.classList.toggle('musicOn', enabled);
  button.setAttribute('aria-pressed', String(enabled));
  button.textContent = enabled ? '♫ 음악 끄기' : wanted ? '♫ 터치하면 음악 시작' : '♫ 음악 켜기';
  volumeLabel.hidden = !enabled;
}
function listenForGesture(active) {
  const method = active ? 'addEventListener' : 'removeEventListener';
  document[method]('pointerdown', firstGesture);
  document[method]('keydown', firstGesture);
}
function firstGesture(event) {
  if (!event.isTrusted || event.target.closest?.('#musicButton') || !wanted) return;
  start();
}
async function stop() {
  wanted = false;
  enabled = false;
  listenForGesture(false);
  clearInterval(timer);
  timer = undefined;
  const old = context;
  context = undefined;
  master = undefined;
  updateUI();
  if (old && old.state !== 'closed') await old.close();
}
function activate(ctx) {
  if (ctx !== context || !wanted || enabled || document.hidden || ctx.state !== 'running') return;
  enabled = true;
  step = 0;
  nextNote = ctx.currentTime + 0.06;
  listenForGesture(false);
  schedule();
  timer = setInterval(schedule, 150);
  updateUI();
}
function start() {
  wanted = true;
  try {
    if (!context) {
      const Audio = window.AudioContext || window.webkitAudioContext;
      if (!Audio) throw new Error('Web Audio 미지원');
      context = new Audio();
      master = context.createGain();
      master.gain.value = Number(slider.value) / 100 * 0.35;
      const filter = context.createBiquadFilter();
      filter.type = 'lowpass';
      filter.frequency.value = 2800;
      const compressor = context.createDynamicsCompressor();
      compressor.threshold.value = -16;
      compressor.ratio.value = 3;
      master.connect(filter).connect(compressor).connect(context.destination);
      const ctx = context;
      ctx.addEventListener('statechange', () => activate(ctx));
    }
    const ctx = context;
    listenForGesture(true);
    updateUI();
    // A blocked resume may remain pending: never lock the button while awaiting it.
    ctx.resume().then(() => activate(ctx)).catch(() => {
      if (context === ctx && wanted) updateUI();
    });
    activate(ctx);
  } catch (error) {
    void stop();
    document.querySelector('#announcement').textContent = '배경음을 재생하지 못했습니다. 음악 버튼을 다시 눌러 주세요.';
    button.textContent = '♫ 재생 다시 시도';
    console.warn('Background audio:', error.message);
  }
}
button.addEventListener('click', () => { if (enabled) void stop(); else start(); });
slider.addEventListener('input', () => {
  volumeLabel.querySelector('span').textContent = slider.value + '%';
  if (context && master) master.gain.setTargetAtTime(Number(slider.value) / 100 * 0.35, context.currentTime, 0.1);
});
document.addEventListener('visibilitychange', () => { if (document.hidden && context) void stop(); });
window.addEventListener('pagehide', () => { if (context) void stop(); });
window.musicDiagnostics = () => ({enabled, waitingForGesture: wanted && !enabled, contextState: context?.state || 'none', timerActive: timer !== undefined, volume: Number(slider.value)});
if (!document.hidden) start();

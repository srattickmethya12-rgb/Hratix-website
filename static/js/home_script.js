/* =========================================================
   HRATIX — Home Page Behaviour
   (Stepper — the hero background is now the shared global
   Vanta Fog layer initialized in shared.js)
   ========================================================= */

(function stepper() {
  const root = document.querySelector('[data-stepper]');
  if (!root) return;

  const steps = Array.from(root.querySelectorAll('.step'));
  const panels = Array.from(root.querySelectorAll('.stepper-panel'));
  const progress = root.querySelector('[data-progress]');
  const prevBtn = root.querySelector('[data-prev]');
  const nextBtn = root.querySelector('[data-next]');

  let active = 0;
  let auto;

  function render() {
    steps.forEach((s, i) => s.classList.toggle('is-active', i === active));
    panels.forEach((p, i) => p.classList.toggle('is-active', i === active));
    if (progress) progress.style.transform = `translateX(${active * 100}%)`;
    if (prevBtn) prevBtn.disabled = active === 0;
    if (nextBtn) nextBtn.disabled = active === steps.length - 1;
  }

  function goTo(i) {
    active = Math.max(0, Math.min(steps.length - 1, i));
    render();
  }

  steps.forEach((s, i) => s.addEventListener('click', () => { goTo(i); restartAuto(); }));
  if (prevBtn) prevBtn.addEventListener('click', () => { goTo(active - 1); restartAuto(); });
  if (nextBtn) nextBtn.addEventListener('click', () => { goTo(active + 1); restartAuto(); });

  function tick() {
    goTo(active + 1 >= steps.length ? 0 : active + 1);
  }

  function restartAuto() {
    clearInterval(auto);
    auto = setInterval(tick, 4500);
  }

  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  render();
  if (!reduceMotion) restartAuto();
})();

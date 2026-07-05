/* =========================================================
   HRATIX — Shared site chrome behaviour
   Pill nav indicator + active state + mobile toggle + scroll state
   + global Vanta Fog background
   ========================================================= */

(function vantaBackground() {
  const el = document.getElementById('vanta-bg');
  if (!el) return;

  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  // Respect reduced-motion, and gracefully degrade if the CDN scripts didn't
  // load (ad blocker, offline, network hiccup) — either way, fall back to a
  // static gradient in the same palette rather than leaving a blank page.
  if (reduceMotion || typeof VANTA === 'undefined' || typeof THREE === 'undefined') {
    el.classList.add('vanta-bg-fallback');
    return;
  }

  try {
    VANTA.FOG({
      el: el,
      THREE: THREE,
      mouseControls: true,
      touchControls: true,
      gyroControls: false,
      minHeight: 200.00,
      minWidth: 200.00,
      scale: 2.00,
      scaleMobile: 4.00,
      speed: 1.00,
      zoom: 1.00,
      blurFactor: 0.57,
      backgroundAlpha: 1.00,
      // Palette kept strictly to the brand's purple / black / white system
      // (the original vantajs.com preset included off-brand red/cream tones).
      baseColor: 0x07060a,       // near-black, matches --bg
      highlightColor: 0xd6b3ff,  // pale lavender-white highlight wisps
      midtoneColor: 0x9d5cff,    // core brand purple
      lowlightColor: 0x1a1226,   // deep purple-black shadow
    });
  } catch (err) {
    el.classList.add('vanta-bg-fallback');
  }
})();

(function () {
  const header = document.getElementById('main-head');
  if (!header) return;

  const links = Array.from(header.querySelectorAll('.pillnav-links a'));
  const indicator = header.querySelector('.pillnav-indicator');
  const toggle = header.querySelector('.pillnav-toggle');

  function currentPath() {
    const p = window.location.pathname.replace(/\/+$/, '');
    return p === '' ? '/' : p;
  }

  function markActive() {
    const path = currentPath();
    let active = null;
    links.forEach((a) => {
      const linkPath = a.getAttribute('data-path');
      const isActive = linkPath === path;
      a.classList.toggle('is-active', isActive);
      if (isActive) active = a;
    });
    if (active) moveIndicator(active);
  }

  function moveIndicator(target) {
    if (!indicator || !target) return;
    const headerRect = header.querySelector('.pillnav-links').getBoundingClientRect();
    const rect = target.getBoundingClientRect();
    indicator.style.width = rect.width + 'px';
    indicator.style.transform = `translateX(${rect.left - headerRect.left}px)`;
  }

  links.forEach((a) => {
    a.addEventListener('mouseenter', () => moveIndicator(a));
    a.addEventListener('mouseleave', markActive);
  });

  window.addEventListener('resize', markActive);
  window.addEventListener('load', markActive);
  // Run once immediately too, in case fonts already settled
  markActive();

  if (toggle) {
    toggle.addEventListener('click', () => {
      header.classList.toggle('menu-open');
    });
  }

  window.addEventListener('scroll', () => {
    header.classList.toggle('is-scrolled', window.scrollY > 12);
  }, { passive: true });
})();

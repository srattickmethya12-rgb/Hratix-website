/* =========================================================
   HRATIX — Pricing Page Behaviour
   Scroll Stack: as each sticky card is overtaken by the next,
   it scales down and dims slightly to read as "beneath" it.
   ========================================================= */

(function scrollStack() {
  const stack = document.querySelector('[data-scroll-stack]');
  if (!stack) return;

  const cards = Array.from(stack.querySelectorAll('[data-stack-card]'));
  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (reduceMotion || cards.length < 2) return;

  function update() {
    for (let i = 0; i < cards.length - 1; i++) {
      const current = cards[i];
      const next = cards[i + 1];
      const nextTop = next.getBoundingClientRect().top;
      const currentTop = current.getBoundingClientRect().top;

      // How close the next card is to overtaking the current sticky card
      const closeness = Math.min(1, Math.max(0, (currentTop - nextTop + 400) / 400));

      const scale = 1 - closeness * 0.045;
      const opacity = 1 - closeness * 0.35;
      current.style.transform = `scale(${scale})`;
      current.style.opacity = opacity;
    }
  }

  window.addEventListener('scroll', update, { passive: true });
  window.addEventListener('resize', update);
  update();
})();

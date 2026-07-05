/* =========================================================
   HRATIX — Contact Page Behaviour
   ========================================================= */

(function contactForm() {
  const form = document.getElementById('contactForm');
  if (!form) return;

  const submitBtn = document.getElementById('submitButton');
  const emailInput = document.getElementById('email');

  form.addEventListener('submit', (e) => {
    if (emailInput && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(emailInput.value.trim())) {
      e.preventDefault();
      emailInput.focus();
      emailInput.style.borderColor = '#d94646';
      return;
    }

    if (submitBtn) {
      submitBtn.disabled = true;
      submitBtn.textContent = 'Sending...';
    }
    // Form continues its normal POST submit to the Flask /contact route.
  });

  if (emailInput) {
    emailInput.addEventListener('input', () => {
      emailInput.style.borderColor = '';
    });
  }
})();

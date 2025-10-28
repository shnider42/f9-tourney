
document.addEventListener('DOMContentLoaded', () => {
  // Scroll reveal for panels
  const els = document.querySelectorAll('.panel');
  const show = el => el.classList.add('reveal');
  const obs = new IntersectionObserver((entries)=>{
    entries.forEach(e=>{ if(e.isIntersecting){ show(e.target); obs.unobserve(e.target); } });
  }, {threshold:.08});
  els.forEach(el=>obs.observe(el));
});


// --- Parallax for hero layers ---
const heroes = document.querySelectorAll('.hero');
heroes.forEach(hero => {
  const layers = hero.querySelectorAll('.p-layer');
  if (!layers.length) return;
  let rect = hero.getBoundingClientRect();
  let cx = rect.left + rect.width / 2;
  let cy = rect.top + rect.height / 2;
  const apply = (mx, my) => {
    const dx = (mx - cx) / rect.width;
    const dy = (my - cy) / rect.height;
    layers.forEach(layer => {
      const depth = parseFloat(layer.dataset.depth || '0.1');
      const tx = (-dx * 60) * depth;
      const ty = (-dy * 40) * depth;
      layer.style.transform = `translate3d(${tx}px, ${ty}px, 0)`;
    });
  };
  hero.addEventListener('mousemove', e => apply(e.clientX, e.clientY));
  const recalc = () => {
    rect = hero.getBoundingClientRect();
    cx = rect.left + rect.width / 2;
    cy = rect.top + rect.height / 2;
  };
  window.addEventListener('scroll', recalc, { passive: true });
  window.addEventListener('resize', recalc);
  recalc();
  apply(cx + 1, cy + 1);
});

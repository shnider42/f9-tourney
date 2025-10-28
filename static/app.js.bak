
document.addEventListener('DOMContentLoaded', () => {
  // Scroll reveal for panels
  const els = document.querySelectorAll('.panel');
  const show = el => el.classList.add('reveal');
  const obs = new IntersectionObserver((entries)=>{
    entries.forEach(e=>{ if(e.isIntersecting){ show(e.target); obs.unobserve(e.target); } });
  }, {threshold:.08});
  els.forEach(el=>obs.observe(el));
});

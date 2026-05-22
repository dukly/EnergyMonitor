const menuToggle = document.querySelector('.menu-toggle');
const nav = document.querySelector('.nav');

if (menuToggle && nav) {
  menuToggle.addEventListener('click', () => {
    const open = nav.classList.toggle('is-open');
    menuToggle.setAttribute('aria-expanded', open ? 'true' : 'false');
  });
}

document.querySelectorAll('form[data-lead-form]').forEach((form) => {
  const status = form.querySelector('.form-status');

  form.addEventListener('submit', (event) => {
    event.preventDefault();
    const data = new FormData(form);
    const name = (data.get('name') || 'клиент').toString().trim();
    const phone = (data.get('phone') || '').toString().trim();

    const payload = Object.fromEntries(data.entries());
    const key = 'sunhors_leads';
    const existing = JSON.parse(localStorage.getItem(key) || '[]');
    existing.push({ ...payload, createdAt: new Date().toISOString(), page: location.pathname });
    localStorage.setItem(key, JSON.stringify(existing));

    if (status) {
      status.textContent = `${name}, заявка сохранена. Менеджер свяжется по ${phone || 'указанному телефону'}.`;
    }

    const whatsapp = form.dataset.whatsapp;
    if (whatsapp && phone) {
      const text = encodeURIComponent(`Здравствуйте! Меня зовут ${name}. Хочу расчёт солнечной станции. Телефон: ${phone}`);
      window.open(`https://wa.me/${whatsapp}?text=${text}`, '_blank', 'noopener');
    }

    form.reset();
  });
});

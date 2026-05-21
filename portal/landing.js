const leadForm = document.getElementById('leadForm');
const formStatus = document.getElementById('formStatus');

leadForm.addEventListener('submit', (event) => {
  event.preventDefault();

  const data = new FormData(leadForm);
  const name = data.get('name') || 'клиент';
  const plan = data.get('plan');
  const planLabel = {
    business: 'Бизнес',
    pro: 'Про',
    start: 'Старт',
  }[plan] || 'Бизнес';

  formStatus.textContent = `${name}, заявка на тариф ${planLabel} подготовлена. Подключите CRM/API для отправки менеджеру.`;
  leadForm.reset();
});

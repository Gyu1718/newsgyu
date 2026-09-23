(() => {
  const form = document.getElementById('filters');
  const list = document.getElementById('cards');
  if (!form || !list) return;
  const cards = Array.from(list.children);
  const query = document.getElementById('query');
  const month = document.getElementById('month');
  const count = document.getElementById('count');
  const empty = document.getElementById('empty');
  const reset = document.getElementById('reset');
  const noun = document.body.dataset.noun || (month ? '판' : '건');
  form.hidden = false;

  const apply = () => {
    const term = (query.value || '').trim().toLowerCase();
    const pick = month ? month.value : '';
    let shown = 0;
    for (const card of cards) {
      const text = (card.dataset.search || '').toLowerCase();
      const ok = (!term || text.includes(term)) && (!pick || card.dataset.month === pick);
      card.hidden = !ok;
      if (ok) shown += 1;
    }
    count.textContent = `${shown}${noun} 표시 중`;
    list.hidden = shown === 0;
    empty.hidden = shown !== 0;
  };

  query.addEventListener('input', apply);
  if (month) month.addEventListener('change', apply);
  reset.addEventListener('click', () => {
    query.value = '';
    if (month) month.value = '';
    apply();
    query.focus();
  });
})();

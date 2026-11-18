document.addEventListener("DOMContentLoaded", () => {
  const counter = document.getElementById("free-seats");
  if (counter && counter.dataset.api) {
    const refresh = async () => {
      try {
        const response = await fetch(counter.dataset.api, {headers: {"X-Requested-With": "XMLHttpRequest"}});
        if (!response.ok) return;
        const data = await response.json();
        counter.textContent = data.free;
        const submit = document.querySelector('button[type="submit"]');
        if (submit && !data.booking_open) {
          submit.disabled = true;
          submit.textContent = "Бронирование закрыто";
        } else if (submit && data.free === 0) {
          submit.disabled = true;
          submit.textContent = "Свободных станций нет";
        }
      } catch (_) { /* при временной потере сети оставляем последнее значение */ }
    };
    refresh();
    window.setInterval(refresh, 15000);
  }
  const toggle = document.querySelector(".menu-toggle");
  if (toggle) toggle.addEventListener("click", () => document.querySelector(".header nav")?.classList.toggle("open"));
});

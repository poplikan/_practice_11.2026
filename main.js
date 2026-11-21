document.addEventListener("DOMContentLoaded", () => {
  // ---------- счётчик свободных станций ----------
  const counter = document.getElementById("free-seats");

  if (counter && counter.dataset.api) {
    // кнопка именно формы бронирования, а не «Выйти» в шапке
    const form   = counter.closest("form") || document.querySelector(".booking-form");
    const submit = form?.querySelector('button[type="submit"]');

    const setSubmit = (disabled, label) => {
      if (!submit) return;
      submit.disabled = disabled;
      if (label) submit.textContent = label;
    };

    const refresh = async () => {
      try {
        const response = await fetch(counter.dataset.api, {
          headers: { "X-Requested-With": "XMLHttpRequest" },
        });
        if (!response.ok) return;

        const data = await response.json();
        counter.textContent = data.free;

        if (!data.booking_open) {
          setSubmit(true, "Бронирование закрыто");
        } else if (Number(data.free) === 0) {
          setSubmit(true, "Свободных станций нет");
        } else {
          // ВАЖНО: вернуть кнопку в рабочее состояние
          setSubmit(false, "Подтвердить бронь");
        }
      } catch (_) {
        /* при временной потере сети оставляем последнее значение */
      }
    };

    refresh();
    const intervalId = window.setInterval(refresh, 15000);
    window.addEventListener("beforeunload", () => clearInterval(intervalId));
  }

  // ---------- мобильное меню ----------
  const toggle = document.querySelector(".menu-toggle");
  if (toggle) {
    toggle.addEventListener("click", () => {
      document.querySelector(".header nav")?.classList.toggle("open");
    });
  }

 
});
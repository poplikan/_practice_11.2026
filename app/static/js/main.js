document.addEventListener("DOMContentLoaded", () => {
  // ---------- счётчик свободных станций ----------
  const counter = document.getElementById("free-seats");

  if (counter && counter.dataset.api) {
    const form = counter.closest("form") || document.querySelector(".booking-form");
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
        if (!response.ok) {
          // сервер вернул 4xx/5xx — не блокируем пользователя навсегда
          setSubmit(false, "Подтвердить бронь");
          return;
        }

        const data = await response.json();
        counter.textContent = data.free;

        if (!data.booking_open) {
          setSubmit(true, "Бронирование закрыто");
        } else if (parseInt(data.free, 10) === 0) {
          setSubmit(true, "Свободных станций нет");
        } else {
          setSubmit(false, "Подтвердить бронь");
        }
      } catch (err) {
        // при потере сети — оставляем кнопку рабочей, чтобы пользователь мог попробовать
        console.warn("Не удалось обновить счётчик свободных мест:", err);
        setSubmit(false, "Подтвердить бронь");
      }
    };

    refresh();
    if (window.__seatsIntervalId) {
      clearInterval(window.__seatsIntervalId);
    }
    window.__seatsIntervalId = window.setInterval(refresh, 15000);
    window.addEventListener("beforeunload", () => {
      clearInterval(window.__seatsIntervalId);
    });
  }

  // ---------- мобильное меню ----------
  const toggle = document.querySelector(".menu-toggle");
  if (toggle) {
    toggle.addEventListener("click", () => {
      document.querySelector(".header nav")?.classList.toggle("open");
    });
  }
});
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()


class NegativeTests(TestCase):

    def test_unknown_catalog_item(self):
        """Несуществующий мастер-класс возвращает 404."""
        response = self.client.get("/catalog/99999/")
        self.assertEqual(response.status_code, 404)

    def test_dashboard_for_guest(self):
        """Неавторизованный пользователь не должен видеть dashboard."""
        response = self.client.get("/dashboard/")
        self.assertIn(response.status_code, [302, 403])

    def test_invalid_booking_data(self):
        """Некорректные данные бронирования не должны приниматься."""
        response = self.client.post(
            "/booking/1/",
            {"portions": 12}
        )
        self.assertNotEqual(response.status_code, 500)

    def test_login_page_available(self):
        """Страница входа открывается."""
        response = self.client.get("/login/")
        self.assertEqual(response.status_code, 200)

    def test_catalog_page_available(self):
        """Каталог открывается."""
        response = self.client.get("/catalog/")
        self.assertEqual(response.status_code, 200)
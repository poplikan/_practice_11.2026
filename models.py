from django.db import models
from django.contrib.auth.models import User


class Cuisine(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Название кухни")
    page_url = models.URLField(blank=True, null=True, verbose_name="Ссылка на страницу")

    class Meta:
        verbose_name = "Кухня мира"
        verbose_name_plural = "Кухни мира"
        ordering = ["name"]

    def __str__(self):
        return self.name


class MasterClass(models.Model):
    title = models.CharField(max_length=150, verbose_name="Название МК")
    description = models.TextField(verbose_name="Описание")
    cuisine = models.ForeignKey(Cuisine, on_delete=models.PROTECT, related_name="masterclasses", verbose_name="Кухня")
    adult_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена взрослого билета")
    child_discount = models.IntegerField(default=30, verbose_name="Скидка на детский билет, %")

    class Meta:
        verbose_name = "Кулинарный мастер-класс"
        verbose_name_plural = "Кулинарные мастер-классы"
        ordering = ["title"]

    def __str__(self):
        return self.title


class Dish(models.Model):
    name = models.CharField(max_length=100, verbose_name="Название блюда")
    description = models.TextField(blank=True, null=True, verbose_name="Описание")
    photo = models.ImageField(upload_to='dishes/', blank=True, null=True, verbose_name="Фото")
    masterclasses = models.ManyToManyField(MasterClass, through='MasterClassDish', related_name="dishes")

    class Meta:
        verbose_name = "Блюдо программы"
        verbose_name_plural = "Блюда программы"
        ordering = ["name"]

    def __str__(self):
        return self.name


class MasterClassDish(models.Model):
    masterclass = models.ForeignKey(MasterClass, on_delete=models.CASCADE, verbose_name="Мастер-класс")
    dish = models.ForeignKey(Dish, on_delete=models.CASCADE, verbose_name="Блюдо")

    class Meta:
        verbose_name = "Блюдо в МК"
        verbose_name_plural = "Блюда в МК"
        constraints = [
            models.UniqueConstraint(fields=["masterclass", "dish"], name="unique_mc_dish"),
        ]

    def __str__(self):
        return f"{self.masterclass.title} — {self.dish.name}"


class Ingredient(models.Model):
    name = models.CharField(max_length=100, verbose_name="Название ингредиента")
    unit = models.CharField(max_length=10, verbose_name="Единица измерения")

    class Meta:
        verbose_name = "Ингредиент"
        verbose_name_plural = "Ингредиенты"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.unit})"


class Recipe(models.Model):
    dish = models.ForeignKey(Dish, on_delete=models.CASCADE, related_name="recipes", verbose_name="Блюдо")
    ingredient = models.ForeignKey(Ingredient, on_delete=models.PROTECT, verbose_name="Ингредиент")
    amount_per_portion = models.DecimalField(max_digits=7, decimal_places=2, verbose_name="Граммовка на 1 порцию")

    class Meta:
        verbose_name = "Рецептура на 1 порцию"
        verbose_name_plural = "Рецептуры на 1 порцию"
        constraints = [
            models.UniqueConstraint(fields=["dish", "ingredient"], name="unique_recipe_item"),
        ]

    def __str__(self):
        return f"{self.dish.name} — {self.ingredient.name}: {self.amount_per_portion} {self.ingredient.unit}"


class Chef(models.Model):
    name = models.CharField(max_length=100, verbose_name="Имя шефа")
    description = models.TextField(blank=True, null=True, verbose_name="Описание")

    class Meta:
        verbose_name = "Шеф-повар"
        verbose_name_plural = "Шеф-повара"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Hall(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Название зала")
    station_count = models.PositiveIntegerField(verbose_name="Количество станций")

    class Meta:
        verbose_name = "Кухонный зал"
        verbose_name_plural = "Кухонные залы"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Schedule(models.Model):
    masterclass = models.ForeignKey(MasterClass, on_delete=models.CASCADE, related_name="schedules", verbose_name="Мастер-класс")
    chef = models.ForeignKey(Chef, on_delete=models.PROTECT, related_name="schedules", verbose_name="Шеф")
    hall = models.ForeignKey(Hall, on_delete=models.PROTECT, related_name="schedules", verbose_name="Зал")
    start_datetime = models.DateTimeField(verbose_name="Дата и время старта")
    status = models.CharField(
        max_length=20,
        choices=[("planned", "Запланировано"), ("closed", "Брони закрыты"), ("done", "Проведено")],
        default="planned",
        verbose_name="Статус"
    )

    class Meta:
        verbose_name = "Расписание занятия"
        verbose_name_plural = "Расписание занятий"
        ordering = ["start_datetime"]

    @property
    def workshop(self):
        return self.masterclass

    def __str__(self):
        return f"{self.masterclass.title} — {self.start_datetime}"


class Booking(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="bookings", verbose_name="Пользователь")
    schedule = models.ForeignKey(Schedule, on_delete=models.PROTECT, related_name="bookings", verbose_name="Занятие")
    TICKET_CHOICES = [
        ("single", "Один взрослый"),
        ("pair", "Взрослый + ребёнок"),
    ] 

    booking_type = models.CharField(
        max_length=10,
        choices=[("adult", "Один взрослый"), ("pair", "Взрослый + ребёнок")],
        verbose_name="Тип брони"
    )
    portions = models.PositiveIntegerField(default=1, verbose_name="Число порций")
    status = models.CharField(
        max_length=10,
        choices=[("active", "Активна"), ("paid", "Оплачена"), ("cancelled", "Отменена")],
        default="active",
        verbose_name="Статус"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    ticket_type = models.CharField(
        max_length=10, 
        choices=TICKET_CHOICES, 
        default="single",
        verbose_name="Тип билета"
    )
    total = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0, 
        verbose_name="Итоговая сумма"
    )

    class Meta:
        verbose_name = "Бронь рабочей станции"
        verbose_name_plural = "Брони рабочих станций"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.get_full_name()} — {self.schedule}"


class PurchaseList(models.Model):
    schedule = models.OneToOneField(Schedule, on_delete=models.CASCADE, related_name="purchase_list", verbose_name="Занятие")
    total_portions = models.PositiveIntegerField(default=0, verbose_name="Итоговое число порций")
    generated_at = models.DateTimeField(auto_now=True, verbose_name="Дата формирования")

    class Meta:
        verbose_name = "Сводный лист закупки"
        verbose_name_plural = "Сводные листы закупки"

    def __str__(self):
        return f"Закупка для {self.schedule}"


class PurchaseItem(models.Model):
    purchase_list = models.ForeignKey(PurchaseList, on_delete=models.CASCADE, related_name="items", verbose_name="Лист закупки")
    ingredient = models.ForeignKey(Ingredient, on_delete=models.PROTECT, verbose_name="Ингредиент")
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Итоговая граммовка")

    class Meta:
        verbose_name = "Строка закупки"
        verbose_name_plural = "Строки закупки"

    def __str__(self):
        return f"{self.ingredient.name}: {self.total_amount}"


class Certificate(models.Model):
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name="certificate", verbose_name="Бронь")
    recipient_name = models.CharField(max_length=100, verbose_name="Имя получателя")
    file = models.FileField(upload_to='certificates/', verbose_name="Файл сертификата")
    issued_at = models.DateField(auto_now_add=True, verbose_name="Дата выдачи")

    class Meta:
        verbose_name = "Сертификат участника"
        verbose_name_plural = "Сертификаты участников"
        ordering = ["-issued_at"]

    def __str__(self):
        return f"Сертификат для {self.recipient_name}"
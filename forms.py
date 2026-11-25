from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.utils import timezone

from .models import Booking, Schedule, MasterClass, Dish


class SignUpForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        label="Электронная почта",
        help_text="example@mail.ru",
        error_messages={
            "required": "Введите email в формате example@mail.ru",
            "invalid": "Введите email в формате example@mail.ru",
        },
    )

    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email",
                  "password1", "password2")

    def clean_email(self):
        """Собственный метод clean_<поля>: проверка формата и уникальности email."""
        email = self.cleaned_data.get("email")
        if email and User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                "Этот email уже зарегистрирован. Войдите или укажите другой адрес."
            )
        return email

    def clean(self):
        """Проверка двух полей сразу: password1 + password2."""
        cleaned = super().clean()
        password1 = cleaned.get("password1")
        password2 = cleaned.get("password2")

        if password1 and len(password1) < 8:
            self.add_error(
                "password1",
                "Пароль должен содержать не менее 8 символов.",
            )

        if password1 and password2 and password1 != password2:
            self.add_error(
                "password2",
                "Пароли не совпадают. Введите одинаковый пароль в оба поля.",
            )

        return cleaned


class BookingForm(forms.Form):
    ticket_type = forms.ChoiceField(
        choices=Booking.TICKET_CHOICES,
        widget=forms.RadioSelect,
        label="Тип брони",
        help_text="Выберите, как будете готовить",
        error_messages={"required": "Выберите тип брони"},
    )
    portions = forms.IntegerField(
        label="Количество порций",
        min_value=1,
        max_value=10,
        help_text="Для пары укажите 2 порции",
        error_messages={
            "required": "Для пары укажите 2 порции, для одного участника — 1",
            "invalid": "Укажите корректное количество порций (1–10)",
            "min_value": "Для пары укажите 2 порции, для одного участника — 1",
            "max_value": "Для пары укажите 2 порции, для одного участника — 1",
        },
    )

    def clean(self):
        """Проверка двух полей сразу: ticket_type + portions."""
        cleaned = super().clean()
        ticket_type = cleaned.get("ticket_type")
        portions = cleaned.get("portions")

        if ticket_type == "pair" and portions and portions != 2:
            self.add_error(
                "portions",
                "Для пары укажите 2 порции, для одного участника — 1.",
            )

        if ticket_type == "single" and portions and portions != 1:
            self.add_error(
                "portions",
                "Для одного участника укажите 1 порцию. "
                "Для пары выберите тип «Взрослый + ребёнок».",
            )

        return cleaned


class ScheduleForm(forms.ModelForm):
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user and user.groups.filter(name="Шеф").exists() and not user.is_superuser:
            self.fields["masterclass"].queryset = (
                self.fields["masterclass"].queryset.filter(chef__user=user)
            )

    class Meta:
        model = Schedule
        fields = ("masterclass", "start_datetime", "hall", "status")
        widgets = {
            "start_datetime": forms.DateTimeInput(attrs={"type": "datetime-local"})
        }
        labels = {
            "masterclass": "Мастер-класс",
            "start_datetime": "Дата и время",
            "hall": "Зал",
            "status": "Статус",
        }

    def clean(self):
        """Проверка двух полей сразу: start_datetime + hall."""
        cleaned = super().clean()
        start = cleaned.get("start_datetime")
        hall = cleaned.get("hall")

        if start and start <= timezone.now():
            self.add_error(
                "start_datetime",
                "Нельзя создать занятие на прошедшую дату. Выберите будущую дату.",
            )

        if start and hall:
            overlap = (
                Schedule.objects
                .filter(hall=hall, start_datetime__date=start.date())
                .exclude(pk=self.instance.pk)
                .exists()
            )
            if overlap:
                self.add_error(
                    "hall",
                    "В этом зале уже есть занятие на эту дату. "
                    "Выберите другой зал или время.",
                )

        return cleaned


class DishForm(forms.ModelForm):
    class Meta:
        model = Dish
        fields = ("name", "description", "photo")
        labels = {
            "name": "Название блюда",
            "description": "Описание",
            "photo": "Фото",
        }

    def clean_photo(self):
        """Собственный метод clean_<поля>: размер, формат, корректность картинки."""
        photo = self.cleaned_data.get("photo")
        if photo:
            if photo.size > 2 * 1024 * 1024:
                raise forms.ValidationError(
                    "Размер изображения не должен превышать 2 МБ. "
                    "Сожмите фото или выберите файл меньше."
                )
            from PIL import Image, UnidentifiedImageError
            try:
                image = Image.open(photo)
                if image.format not in ("JPEG", "PNG"):
                    raise forms.ValidationError(
                        "Разрешены только изображения JPEG и PNG. "
                        "Пересохраните файл в одном из этих форматов."
                    )
                image.verify()
            except (UnidentifiedImageError, OSError):
                raise forms.ValidationError(
                    "Файл не является корректным изображением. "
                    "Выберите другой файл."
                )
            finally:
                photo.seek(0)
        return photo


class ChefSignUpForm(UserCreationForm):
    """Регистрация шефа: создаёт User + Chef + группа «Шеф»."""
    email = forms.EmailField(required=True, label="Электронная почта")
    chef_name = forms.CharField(max_length=100, label="Имя шефа (как в каталоге)")
    description = forms.CharField(
        widget=forms.Textarea, required=False, label="Коротко о себе"
    )

    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email",
                  "password1", "password2")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        if commit:
            user.save()
            from django.contrib.auth.models import Group
            chef_group, _ = Group.objects.get_or_create(name="Шеф")
            user.groups.add(chef_group)
            from .models import Chef
            Chef.objects.create(
                user=user,
                name=self.cleaned_data["chef_name"],
                description=self.cleaned_data.get("description", ""),
            )
        return user


class RussianAuthenticationForm(AuthenticationForm):
    error_messages = {
        "invalid_login": "Неверный логин или пароль. Проверьте правильность введённых данных.",
        "inactive": "Этот аккаунт неактивен.",
    }
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Booking, Schedule, MasterClass, Dish


class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True, label="Электронная почта")

    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email",
                  "password1", "password2")


class BookingForm(forms.Form):
    ticket_type = forms.ChoiceField(
        choices=Booking.TICKET_CHOICES,
        widget=forms.RadioSelect,
        label="Тип билета",
    )


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
        photo = self.cleaned_data.get("photo")
        if photo:
            if photo.size > 2 * 1024 * 1024:
                raise forms.ValidationError("Размер изображения не должен превышать 2 МБ.")
            from PIL import Image, UnidentifiedImageError
            try:
                image = Image.open(photo)
                if image.format not in ("JPEG", "PNG"):
                    raise forms.ValidationError("Разрешены только изображения JPEG и PNG.")
                image.verify()
                photo.seek(0)
            except (UnidentifiedImageError, OSError):
                raise forms.ValidationError("Файл не является корректным изображением.")
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
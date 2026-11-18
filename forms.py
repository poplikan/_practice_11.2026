from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Booking, Schedule, MasterClass, Dish

class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True, label="Электронная почта")
    
    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email", "password1", "password2")

class BookingForm(forms.Form):
    # Предполагается, что в модели Booking есть константа TICKETS (или используем CHOICES напрямую)
    ticket_type = forms.ChoiceField(
        choices=Booking._meta.get_field('booking_type').choices, 
        widget=forms.RadioSelect, 
        label="Тип брони"
    )

class ScheduleForm(forms.ModelForm):
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        # Логика: если пользователь — шеф (и не админ), он видит только свои МК
        if user and user.groups.filter(name="Шеф").exists() and not user.is_superuser:
            self.fields["masterclass"].queryset = self.fields["masterclass"].queryset.filter(chef__user=user)
            
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
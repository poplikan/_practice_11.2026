from django.contrib import admin
from .models import (
    Cuisine, MasterClass, Dish, MasterClassDish, Ingredient,
    Recipe, Chef, Hall, Schedule, Booking, PurchaseList,
    PurchaseItem, Certificate,
)

admin.site.register(Cuisine)
admin.site.register(MasterClass)
admin.site.register(Dish)
admin.site.register(MasterClassDish)
admin.site.register(Ingredient)
admin.site.register(Recipe)
admin.site.register(Chef)
admin.site.register(Hall)
admin.site.register(Schedule)
admin.site.register(Booking)
admin.site.register(PurchaseList)
admin.site.register(PurchaseItem)
admin.site.register(Certificate)
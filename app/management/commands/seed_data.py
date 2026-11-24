from datetime import datetime, timedelta, time
from decimal import Decimal

from django.contrib.auth.models import User, Group
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from app.models import (
    Cuisine, Chef, Hall, Ingredient, MasterClass, Dish,
    MasterClassDish, Recipe, Schedule, PurchaseList, PurchaseItem,
)
from app.services import generate_purchase_list


class Command(BaseCommand):
    help = "Заполняет сайт демонстрационными данными кулинарной студии"

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write("Заполняем каталог кулинарной студии...")

        # ---------- Кухни мира ----------
        cuisine_data = [
            ("Итальянская", "Паста, пицца и традиционные блюда Италии."),
            ("Французская", "Классические техники и изысканные вкусы Франции."),
            ("Японская", "Суши, роллы и блюда японской кухни."),
            ("Грузинская", "Ароматная выпечка, специи и домашние блюда Грузии."),
            ("Мексиканская", "Яркие блюда с овощами, кукурузой и пряностями."),
            ("Азиатская", "Популярные блюда стран Восточной и Юго-Восточной Азии."),
            ("Средиземноморская", "Овощи, морепродукты, травы и оливковое масло."),
            ("Американская", "Любимые блюда американской кухни и уличная еда."),
        ]
        cuisines = {}
        for name, description in cuisine_data:
            cuisine, _ = Cuisine.objects.get_or_create(
                name=name,
                defaults={"page_url": f"https://example.com/{name.lower()}"},
            )
            if cuisine.page_url != f"https://example.com/{name.lower()}":
                cuisine.page_url = f"https://example.com/{name.lower()}"
                cuisine.save(update_fields=["page_url"])
            cuisines[name] = cuisine

        # ---------- Шеф-повара (с привязкой к User) ----------
        chef_group, _ = Group.objects.get_or_create(name="Шеф")

        chef_data = [
            ("Анна Миронова", "Специализируется на итальянской кухне и домашней пасте."),
            ("Марк Лебедев", "Знакомит гостей с французской кухней и основами кондитерского дела."),
            ("Елена Сато", "Готовит японские блюда и обучает аккуратной работе с продуктами."),
            ("Георгий Беридзе", "Проводит мастер-классы по грузинской кухне и выпечке."),
            ("Даниэль Ривера", "Любит мексиканскую кухню, яркие соусы и необычные сочетания."),
            ("Илья Воронцов", "Работает с азиатскими техниками и современными рецептами."),
        ]
        chefs = []
        for i, (name, description) in enumerate(chef_data):
            chef, _ = Chef.objects.get_or_create(
                name=name, defaults={"description": description}
            )
            if chef.description != description:
                chef.description = description
                chef.save(update_fields=["description"])

            # Привязка User к шефу (для /chef/login/)
            if not getattr(chef, "user", None):
                username = f"chef{i + 1}"
                user, created = User.objects.get_or_create(
                    username=username,
                    defaults={
                        "first_name": name.split()[0],
                        "last_name": name.split()[-1],
                    },
                )
                if created:
                    user.set_password("Test12345!")
                    user.save()
                user.groups.add(chef_group)
                chef.user = user
                chef.save(update_fields=["user"])

            chefs.append(chef)

        # ---------- Залы ----------
        halls = []
        for name, station_count in [
            ("Большая кухня", 14),
            ("Уютная кухня", 8),
        ]:
            hall, _ = Hall.objects.get_or_create(
                name=name, defaults={"station_count": station_count}
            )
            if hall.station_count != station_count:
                hall.station_count = station_count
                hall.save(update_fields=["station_count"])
            halls.append(hall)

        # ---------- Ингредиенты ----------
        ingredient_data = [
            ("Спагетти", "г"), ("Мука пшеничная", "г"), ("Яйца", "шт"),
            ("Пармезан", "г"), ("Томаты", "г"), ("Оливковое масло", "мл"),
            ("Рис для суши", "г"), ("Нори", "лист"), ("Лосось", "г"),
            ("Огурец", "г"), ("Сливочный сыр", "г"), ("Говядина", "г"), ("Морковь", "г"),
            ("Куриное филе", "г"), ("Болгарский перец", "г"),
            ("Кукуруза", "г"), ("Фасоль", "г"), ("Сыр сулугуни", "г"),
            ("Грецкие орехи", "г"), ("Картофель", "г"), ("Сливки", "мл"),
            ("Сахар", "г"), ("Соль", "г"), ("Чёрный перец", "г"),
            ("Чеснок", "г"), ("Базилик", "г"),
        ]
        ingredients = {}
        for name, unit in ingredient_data:
            ingredients[name], _ = Ingredient.objects.get_or_create(
                name=name, defaults={"unit": unit}
            )

        # ---------- Мастер-классы и блюда ----------
        workshop_data = [
            {
                "title": "Секреты домашней пасты",
                "cuisine": "Итальянская",
                "price": "4200.00",
                "description": "Научимся замешивать эластичное тесто, раскатывать его и готовить пасту с насыщенным томатным соусом.",
                "dishes": [
                    ("Тальятелле с томатным соусом", "Свежая домашняя паста с томатами, базиликом и пармезаном.",
                     [("Спагетти", 120), ("Томаты", 100), ("Пармезан", 25), ("Базилик", 5)]),
                    ("Равиоли с сыром", "Нежные равиоли с сырной начинкой и сливочным соусом.",
                     [("Мука пшеничная", 100), ("Яйца", 1), ("Сыр сулугуни", 60), ("Сливки", 40)]),
                ],
            },
            {
                "title": "Французские десерты дома",
                "cuisine": "Французская",
                "price": "4600.00",
                "description": "Разберём основы приготовления десертов, научимся работать с тестом и добиваться нежной текстуры крема.",
                "dishes": [
                    ("Шоколадный фондан", "Десерт с нежной серединкой и насыщенным шоколадным вкусом.",
                     [("Яйца", 1), ("Мука пшеничная", 35), ("Сахар", 35), ("Сливки", 30)]),
                    ("Ванильный крем", "Универсальный нежный крем для десертов и выпечки.",
                     [("Сливки", 80), ("Сахар", 20), ("Яйца", 1)]),
                ],
            },
            {
                "title": "Искусство приготовления суши",
                "cuisine": "Японская",
                "price": "4900.00",
                "description": "Познакомимся с рисом для суши, подготовкой начинки и техникой аккуратного формирования роллов.",
                "dishes": [
                    ("Ролл с лососем", "Классический ролл с лососем, огурцом и сливочным сыром.",
                     [("Рис для суши", 100), ("Нори", 1), ("Лосось", 50), ("Огурец", 25), ("Сливочный сыр", 30)]),
                    ("Овощной маки", "Лёгкие роллы с овощной начинкой.",
                     [("Рис для суши", 100), ("Нори", 1), ("Огурец", 40)]),
                ],
            },
            {
                "title": "Грузинское гостеприимство",
                "cuisine": "Грузинская",
                "price": "4300.00",
                "description": "Приготовим ароматную выпечку, поговорим о специях и узнаем секреты традиционного грузинского стола.",
                "dishes": [
                    ("Хачапури по-аджарски", "Румяная лодочка из теста с сыром и яйцом.",
                     [("Мука пшеничная", 130), ("Яйца", 1), ("Сыр сулугуни", 100)]),
                    ("Салат по-грузински", "Свежие овощи с зеленью и ореховой заправкой.",
                     [("Томаты", 100), ("Огурец", 70), ("Грецкие орехи", 20), ("Чеснок", 3)]),
                ],
            },
            {
                "title": "Мексиканская кухня: яркие вкусы",
                "cuisine": "Мексиканская",
                "price": "4100.00",
                "description": "Соберём сбалансированные начинки, приготовим соусы и узнаем, как сочетать специи и свежие продукты.",
                "dishes": [
                    ("Тако с говядиной", "Тако с пряной говядиной, овощами и свежей зеленью.",
                     [("Говядина", 100), ("Болгарский перец", 40), ("Томаты", 40), ("Кукуруза", 30)]),
                    ("Домашняя сальса", "Свежий томатный соус с чесноком и специями.",
                     [("Томаты", 100), ("Чеснок", 3), ("Оливковое масло", 10)]),
                ],
            },
            {
                "title": "Азиатский wok: быстро и вкусно",
                "cuisine": "Азиатская",
                "price": "4400.00",
                "description": "Освоим быструю обжарку на высокой температуре и приготовим полноценное блюдо в стиле wok.",
                "dishes": [
                    ("Wok с курицей и овощами", "Сочная курица с овощами в ароматном соусе.",
                     [("Куриное филе", 120), ("Болгарский перец", 50), ("Морковь", 40), ("Чеснок", 3)]),
                    ("Рис с овощами", "Рассыпчатый рис с овощами и лёгкими специями.",
                     [("Рис для суши", 100), ("Болгарский перец", 40), ("Кукуруза", 30)]),
                ],
            },
            {
                "title": "Средиземноморский обед",
                "cuisine": "Средиземноморская",
                "price": "4500.00",
                "description": "Соберём меню из простых сезонных продуктов, свежих овощей, трав и оливкового масла.",
                "dishes": [
                    ("Овощная брускетта", "Хрустящий хлеб с томатами, базиликом и оливковым маслом.",
                     [("Томаты", 80), ("Базилик", 5), ("Оливковое масло", 10)]),
                    ("Картофель по-деревенски", "Запечённый картофель с чесноком и травами.",
                     [("Картофель", 150), ("Чеснок", 4), ("Оливковое масло", 10)]),
                ],
            },
            {
                "title": "Американская классика",
                "cuisine": "Американская",
                "price": "4000.00",
                "description": "Приготовим сочный бургер и научимся сочетать соусы, овощи и текстуры в одном блюде.",
                "dishes": [
                    ("Домашний бургер", "Сочная котлета с овощами и мягкой булочкой.",
                     [("Говядина", 140), ("Томаты", 30), ("Сыр сулугуни", 25)]),
                    ("Картофельные дольки", "Запечённый картофель с пряностями.",
                     [("Картофель", 160), ("Чёрный перец", 1), ("Оливковое масло", 10)]),
                ],
            },
            {
                "title": "Итальянская пицца с нуля",
                "cuisine": "Итальянская",
                "price": "4300.00",
                "description": "От замеса теста до ароматной начинки: приготовим домашнюю пиццу и разберём тонкости выпечки.",
                "dishes": [
                    ("Пицца Маргарита", "Тонкое тесто, томаты, сыр и свежий базилик.",
                     [("Мука пшеничная", 140), ("Томаты", 70), ("Сыр сулугуни", 60), ("Базилик", 5)]),
                    ("Томатный соус", "Простой соус для пиццы и пасты.",
                     [("Томаты", 100), ("Чеснок", 3), ("Оливковое масло", 10)]),
                ],
            },
            {
                "title": "Домашняя лапша и азиатские супы",
                "cuisine": "Азиатская",
                "price": "4200.00",
                "description": "Приготовим домашнюю лапшу и разберём, как собрать насыщенный бульон и сбалансировать вкус.",
                "dishes": [
                    ("Лапша с курицей", "Домашняя лапша с курицей и овощами.",
                     [("Мука пшеничная", 90), ("Яйца", 1), ("Куриное филе", 80), ("Морковь", 30)]),
                    ("Пряный бульон", "Ароматный бульон с чесноком и специями.",
                     [("Куриное филе", 50), ("Чеснок", 3), ("Чёрный перец", 1)]),
                ],
            },
            {
                "title": "Семейная выпечка",
                "cuisine": "Французская",
                "price": "3900.00",
                "description": "Уютное занятие для тех, кто хочет освоить базовые приёмы работы с тестом и выпекать дома.",
                "dishes": [
                    ("Печенье сабле", "Рассыпчатое песочное печенье с нежной текстурой.",
                     [("Мука пшеничная", 100), ("Сахар", 35), ("Яйца", 1)]),
                    ("Сладкие булочки", "Мягкие булочки с лёгкой золотистой корочкой.",
                     [("Мука пшеничная", 120), ("Сахар", 25), ("Яйца", 1)]),
                ],
            },
            {
                "title": "Грузинская выпечка: хачапури",
                "cuisine": "Грузинская",
                "price": "4200.00",
                "description": "Научимся работать с дрожжевым тестом и приготовим ароматные хачапури с тянущимся сыром.",
                "dishes": [
                    ("Хачапури по-имеретински", "Круглый пирог с сырной начинкой.",
                     [("Мука пшеничная", 130), ("Сыр сулугуни", 100), ("Яйца", 1)]),
                    ("Сырные лепёшки", "Небольшие лепёшки с сыром для домашнего стола.",
                     [("Мука пшеничная", 100), ("Сыр сулугуни", 70)]),
                ],
            },
        ]

        masterclasses = []
        for item in workshop_data:
            masterclass, _ = MasterClass.objects.get_or_create(
                title=item["title"],
                defaults={
                    "description": item["description"],
                    "cuisine": cuisines[item["cuisine"]],
                    "adult_price": Decimal(item["price"]),
                    "child_discount": 30,
                },
            )
            masterclass.description = item["description"]
            masterclass.cuisine = cuisines[item["cuisine"]]
            masterclass.adult_price = Decimal(item["price"])
            masterclass.child_discount = 30
            masterclass.save()
            masterclasses.append(masterclass)

            for dish_name, dish_description, recipe_items in item["dishes"]:
                dish, _ = Dish.objects.get_or_create(
                    name=dish_name,
                    defaults={"description": dish_description},
                )
                if dish.description != dish_description:
                    dish.description = dish_description
                    dish.save(update_fields=["description"])

                MasterClassDish.objects.get_or_create(
                    masterclass=masterclass, dish=dish
                )
                for ingredient_name, amount in recipe_items:
                    Recipe.objects.get_or_create(
                        dish=dish,
                        ingredient=ingredients[ingredient_name],
                        defaults={"amount_per_portion": Decimal(str(amount))},
                    )

        # ---------- Расписание на ближайшие 4 недели ----------
        now = timezone.localtime(timezone.now())
        base_date = now.date()
        session_times = [time(11, 0), time(15, 0), time(18, 30)]
        schedules = []
        for index in range(24):
            day_offset = 1 + (index // 3) * 4
            session_date = base_date + timedelta(days=day_offset)
            session_time = session_times[index % 3]
            local_dt = timezone.make_aware(
                datetime.combine(session_date, session_time),
                timezone.get_current_timezone(),
            )
            masterclass = masterclasses[index % len(masterclasses)]
            chef = chefs[index % len(chefs)]
            hall = halls[index % len(halls)]
            schedule, _ = Schedule.objects.get_or_create(
                masterclass=masterclass,
                chef=chef,
                hall=hall,
                start_datetime=local_dt,
                defaults={"status": "planned"},
            )
            schedules.append(schedule)

        # ---------- Закупочные листы по реальным рецептам (FR-07) ----------
        for schedule in schedules:
            generate_purchase_list(schedule.id)

        self.stdout.write(self.style.SUCCESS(
            "Готово! Добавлены кухни, шеф-повара (с логинами chef1…chef6), "
            "залы, ингредиенты, 12 мастер-классов, блюда, рецептуры, "
            "расписание и закупочные листы по реальным рецептам."
        ))
        self.stdout.write(
            "Повторный запуск безопасен: существующие записи не дублируются."
        )
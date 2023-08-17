import json

from django.core.management.base import BaseCommand
from recipes.models import Ingredient


# После миграций сделать python manage.py load_data - локально
# sudo docker-compose exec backend python manage.py load_data - на сервере
class Command(BaseCommand):
    help = 'Напоняем таблицу Ingredients'

    def handle(self, *args, **options):
        with open('recipes/data/ingredients.json', 'r',
                  encoding='UTF-8') as ingredients:
            data = json.loads(ingredients.read())
            for ingredients in data:
                Ingredient.objects.get_or_create(**ingredients)
        self.stdout.write(self.style.SUCCESS('Данные загружены'))

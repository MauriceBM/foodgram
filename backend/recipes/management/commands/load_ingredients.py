import json

from django.core.management.base import BaseCommand

from recipes.models import Ingredient


class Command(BaseCommand):
    """Команда загрузки ингредиентов из JSON."""

    help = 'Загрузка ингредиентов из файла JSON'

    def add_arguments(self, parser):
        parser.add_argument(
            'file_path',
            type=str,
            help='Путь к файлу JSON',
        )

    def handle(self, *args, **options):
        file_path = options['file_path']
        created = 0
        skipped = 0
        with open(file_path, 'r', encoding='utf-8') as jsonfile:
            data = json.load(jsonfile)
        for item in data:
            _, is_created = Ingredient.objects.get_or_create(
                name=item['name'],
                measurement_unit=item['measurement_unit'],
            )
            if is_created:
                created += 1
            else:
                skipped += 1
        self.stdout.write(
            self.style.SUCCESS(
                f'Done! Created: {created}, '
                f'Skipped (duplicates): {skipped}',
            ),
        )

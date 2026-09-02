import csv

from django.core.management.base import BaseCommand

from recipes.models import Ingredient


class Command(BaseCommand):
    """Команда загрузки ингредиентов из CSV."""

    help = 'Загрузка ингредиентов из файла CSV'

    def add_arguments(self, parser):
        parser.add_argument(
            'file_path',
            type=str,
            help='Путь к файлу CSV',
        )

    def handle(self, *args, **options):
        file_path = options['file_path']
        created = 0
        skipped = 0
        with open(file_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                _, is_created = Ingredient.objects.get_or_create(
                    name=row['name'],
                    measurement_unit=row['measurement_unit'],
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

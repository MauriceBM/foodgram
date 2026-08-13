import json
from django.core.management.base import BaseCommand
from recipes.models import Ingredient


class Command(BaseCommand):
    help = 'Load ingredients from JSON file'

    def add_arguments(self, parser):
        parser.add_argument(
            'json_file',
            type=str,
            help='Path to the JSON file with ingredients'
        )

    def handle(self, *args, **options):
        json_file = options['json_file']

        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                ingredients_data = json.load(f)
        except FileNotFoundError:
            self.stderr.write(f'File not found: {json_file}')
            return
        except json.JSONDecodeError as e:
            self.stderr.write(f'Invalid JSON: {e}')
            return

        created_count = 0
        skipped_count = 0

        for item in ingredients_data:
            name = item.get('name', '').strip()
            measurement_unit = item.get(
                'measurement_unit', ''
            ).strip()

            if not name or not measurement_unit:
                skipped_count += 1
                continue

            _, created = Ingredient.objects.get_or_create(
                name=name,
                measurement_unit=measurement_unit
            )
            if created:
                created_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Done! Created: {created_count}, '
                f'Skipped (duplicates): {skipped_count}'
            )
        )

from django.db import migrations, models


def map_legacy_categories(apps, schema_editor):
    StudyMaterial = apps.get_model('materials', 'StudyMaterial')
    mapping = {
        'PREVIOUS_PAPER': 'QUESTION_PAPER',
        'MODEL_PAPER': 'QUESTION_PAPER',
        'INTERNAL_PAPER': 'QUESTION_PAPER',
        'PRACTICAL': 'LAB_MANUAL',
        'SYLLABUS': 'OTHER',
        'IMPORTANT_QUESTIONS': 'OTHER',
        'REFERENCE': 'OTHER',
    }
    for old_value, new_value in mapping.items():
        StudyMaterial.objects.filter(material_type=old_value).update(material_type=new_value)


class Migration(migrations.Migration):

    dependencies = [
        ('materials', '0002_studymaterial_created_by_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='studymaterial',
            old_name='category',
            new_name='material_type',
        ),
        migrations.RenameField(
            model_name='studymaterial',
            old_name='uploaded_at',
            new_name='created_at',
        ),
        migrations.RunPython(map_legacy_categories, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='studymaterial',
            name='material_type',
            field=models.CharField(
                choices=[
                    ('NOTES', 'Subject notes'),
                    ('ASSIGNMENT', 'Assignment'),
                    ('QUESTION_PAPER', 'Question paper'),
                    ('LAB_MANUAL', 'Lab manual'),
                    ('OTHER', 'Other'),
                ],
                max_length=30,
            ),
        ),
        migrations.AlterModelOptions(
            name='studymaterial',
            options={'ordering': ['-created_at']},
        ),
        migrations.RemoveIndex(
            model_name='studymaterial',
            name='materials_s_categor_3eb2db_idx',
        ),
        migrations.AddIndex(
            model_name='studymaterial',
            index=models.Index(
                fields=['material_type'],
                name='materials_s_materia_144360_idx',
            ),
        ),
    ]

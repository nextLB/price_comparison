# Generated migration for adding district_fk to Pharmacy model

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_drug_description_dosage_form_drug_package_quantity_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='pharmacy',
            name='district_fk',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='pharmacies',
                to='core.district',
                verbose_name='所属区县',
            ),
        ),
    ]

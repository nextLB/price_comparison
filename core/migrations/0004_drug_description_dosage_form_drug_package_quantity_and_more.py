# Generated migration - add new fields to Drug model for price comparison

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_district_user_medical_insurance_code_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='drug',
            name='description_dosage_form',
            field=models.CharField(blank=True, max_length=100, verbose_name='表述剂型'),
        ),
        migrations.AddField(
            model_name='drug',
            name='package_quantity',
            field=models.CharField(blank=True, max_length=50, verbose_name='包装数量'),
        ),
        migrations.AddField(
            model_name='drug',
            name='catalog_holder',
            field=models.CharField(blank=True, max_length=300, verbose_name='目录序号&标化持有人'),
        ),
        migrations.AddField(
            model_name='drug',
            name='standard_mark',
            field=models.CharField(blank=True, max_length=100, verbose_name='标准品标记'),
        ),
        migrations.AddField(
            model_name='drug',
            name='unit_value',
            field=models.DecimalField(decimal_places=6, default=0, max_digits=20, verbose_name='单体差比值'),
        ),
        migrations.AlterField(
            model_name='drug',
            name='spec_package',
            field=models.CharField(blank=True, max_length=500, verbose_name='规格包装'),
        ),
    ]

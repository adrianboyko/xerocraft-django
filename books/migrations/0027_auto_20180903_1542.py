# Generated by Django 2.1 on 2018-09-03 22:42

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('books', '0026_auto_20180611_1321'),
    ]

    operations = [
        migrations.AddField(
            model_name='otheritemtype',
            name='cash_acct',
            field=models.ForeignKey(default=1, help_text='The cash account associated with items of this type.', on_delete=django.db.models.deletion.PROTECT, related_name='otheritemtypes_cash', to='books.Account'),
        ),
        migrations.AlterField(
            model_name='otheritemtype',
            name='revenue_acct',
            field=models.ForeignKey(blank=True, default=None, help_text='The revenue account associated with items of this type.', null=True, on_delete=django.db.models.deletion.PROTECT, related_name='otheritemtypes_revenue', to='books.Account'),
        ),
    ]

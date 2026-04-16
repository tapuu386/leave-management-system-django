from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('leaves', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='leaveapplication',
            name='leave_type',
            field=models.CharField(
                max_length=10,
                choices=[('LEAVE', 'Leave'), ('ML', 'Medical Leave')],
            ),
        ),
    ]

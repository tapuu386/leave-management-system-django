from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("leaves", "0002_update_leave_type_choices"),
    ]

    operations = [
        migrations.AlterField(
            model_name="leaveapplication",
            name="leave_type",
            field=models.CharField(
                max_length=20,
                choices=[
                    ("FULL_LEAVE", "Full Leave"),
                    ("FIRST_HALF", "First Half"),
                    ("SECOND_HALF", "Second Half"),
                    ("ML", "Medical Leave"),
                ],
            ),
        ),
        migrations.AlterField(
            model_name="leaveapplication",
            name="total_days",
            field=models.DecimalField(max_digits=4, decimal_places=1, default=0),
        ),
    ]

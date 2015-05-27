from django.db import models

class Tag(models.Model):
    short_desc = models.CharField(max_length = 40)
    long_desc = models.TextField(max_length = 500)

class Member(models.Model):
    first_name = models.CharField(max_length = 40)
    last_name = models.CharField(max_length = 40)
    user_id = models.CharField(max_length = 40, help_text = "The user-id the member uses to sign in at Xerocraft.")
    family = models.ForeignKey('self', help_text = "If this member is part of a family account then this points to the 'anchor' member for the family.")
    tags = models.ManyToManyField(Tag)

class DayInNthWeek(models.Model):
    first = models.BooleanField(default = False)
    second = models.BooleanField(default = False)
    third = models.BooleanField(default = False)
    fourth = models.BooleanField(default = False)
    last = models.BooleanField(default = False, help_text = "Some months have a fifth Monday, or Tuesday, ...")
    MONDAY = "mon"
    TUESDAY = "tue"
    WEDNESDAY = "wed"
    THURSDAY = "thu"
    FRIDAY = "fri"
    SATURDAY = "sat"
    SUNDAY = "sun"
    DAY_OF_WEEK_CHOICES = (
        (MONDAY,"Monday"),
        (TUESDAY,"Tuesday"),
        (WEDNESDAY,"Wednesday"),
        (THURSDAY,"Thursday"),
        (FRIDAY,"Friday"),
        (SATURDAY,"Saturday"),
        (SUNDAY,"Sunday")
    )
    day_of_week = models.CharField(max_length = 3, choices = DAY_OF_WEEK_CHOICES)
    
class RecurringTaskTemplate(models.Model):
    short_desc = models.CharField(max_length = 40)
    long_desc = models.TextField(max_length = 500)
    reviewer = models.ForeignKey(Member)
    first_instance_date = models.DateField()
    when1 = models.ForeignKey(DayInNthWeek, help_text = "Use when1 XOR when2.")
    when2 = models.DateField(help_text = "Use when1 XOR when2.")
    
class Task(models.Model):
    short_desc = models.CharField(max_length = 40)
    long_desc = models.TextField(max_length = 500)
    claim_date = models.DateField()
    claimed_by = models.OneToOneField(Member, related_name = "tasks_claimed")
    prev_claimed_by =  models.ForeignKey(Member, related_name = "+") # Reminder: "+" means no backwards relation.
    reviewer = models.ForeignKey(Member, related_name = "tasks_to_review")
    work_done = models.BooleanField(default = False)
    work_accepted = models.BooleanField(default = False)
    recurring_task_template = models.ForeignKey(RecurringTaskTemplate)
    def is_closed(self):
        "Returns True if claimant should receive credit for the task."
        if self.reviewer == None:
            return self.work_done
        else:
            return self.work_done and self.work_accepted
    def is_open(self):
        "Returns True if the task isn't yet completed or if there's a reviewer who hasn't yet accepted it."
        return not self.is_closed()


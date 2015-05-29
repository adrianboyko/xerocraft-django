from django.db import models
from datetime import datetime

class Tag(models.Model):
    name = models.CharField(max_length=40, help_text="A short name for the tag.")
    meaning = models.TextField(max_length=500, help_text="A discussion of the tag's semantics. What does it mean? What does it NOT mean?")
    def __str__(self):
        return self.name

class Member(models.Model):
    first_name = models.CharField(max_length=40)
    last_name = models.CharField(max_length=40)
    user_id = models.CharField(max_length=40, help_text="The user-id the member uses to sign in at Xerocraft.")
    family = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, help_text="If this member is part of a family account then this points to the 'anchor' member for the family.")
    tags = models.ManyToManyField(Tag)
    def __str__(self):
        return "%s %s" % (self.first_name, self.last_name)
    
TASK_SHORT_DESC_LEN = 40 # The description length must be the same in both RecurringTaskTemplate and Task.

class RecurringTaskTemplate(models.Model):
    "Uses a day-of-week vs nth-of-month matrix to define a schedule for recurring tasks"
    # Copied to instances:
    short_desc = models.CharField(max_length=TASK_SHORT_DESC_LEN, help_text="A description that will be copied to instances of the recurring task.")
    reviewer = models.ForeignKey(Member, null=True, blank=True, on_delete=models.SET_NULL, help_text="A reviewer that will be copied to instances of the recurring task.")
    work_estimate = models.IntegerField(default=0, help_text="Provide an estimate of how much work this tasks requires, in minutes. This is work time, not elapsed time.")
    # Specific to template
    start_date = models.DateField(help_text="Choose a date for the first instance of the recurring task.")
    # Week of month:
    first_week = models.BooleanField(default=False, help_text="Task will recur on first weekday in the month.")
    second_week = models.BooleanField(default=False, help_text="Task will recur on second weekday in the month.")
    third_week = models.BooleanField(default=False, help_text="Task will recur on third weekday in the month.")
    fourth_week = models.BooleanField(default=False, help_text="Task will recur on fourth weekday in the month.")
    last_week = models.BooleanField(default=False, help_text="Task will recur on last weekday in the month. This will be 4th or 5th weekday, depending on calendar.")
    every_week = models.BooleanField(default=False, help_text="Task recur every week")
    # Day of week:
    monday = models.BooleanField(default=False, help_text="Task will recur on Monday.")
    tuesday = models.BooleanField(default=False, help_text="Task will recur on Tuesday.")
    wednesday = models.BooleanField(default=False, help_text="Task will recur on Wednesday.")
    thursday = models.BooleanField(default=False, help_text="Task will recur on Thursday.")
    friday = models.BooleanField(default=False, help_text="Task will recur on Friday.")
    saturday = models.BooleanField(default=False, help_text="Task will recur a Saturday.")
    sunday = models.BooleanField(default=False, help_text="Task will recur a Sunday.")
    # Validate:
    def validate(self): # TODO: Rework this into Model.clean(). See Django's "model validation" docs.
        if self.last_week and self.fourth_week:
            return False, "Choose either fourth week or last week, not both."
        if self.every_week and (self.first_week or self.second_week or self.third_week or self.fourth_week or self.last_week):
            return False, "If you choose 'every week' don't choose any other weeks."
        if self.work_estimate < 0:
            # zero will mean "not yet estimated" but anything that has been estimated must have work > 0.
            return False, "Invalid work estimate."
        else:
            return True, "Looks good."

class Task(models.Model):
    # For recurring tasks, these will be copied from RecurringTaskTemplate:
    short_desc = models.CharField(max_length=TASK_SHORT_DESC_LEN, help_text="A very short description of the task which will be used as it's name. Don't try to provide detailed instructions here - attach a TaskNote instead.")
    work_estimate = models.IntegerField(default=0, help_text="Provide an estimate of how much work this tasks requires, in minutes. This is work time, not elapsed time.")
    reviewer = models.ForeignKey(Member, null=True, blank=True, on_delete=models.SET_NULL, related_name="tasks_to_review", help_text="If required, a member who will review the completed work and either accept or reject it.")
    # Other fields:
    deadline = models.DateField(null=True, blank=True, help_text="If appropriate, specify a deadline by which the task must be completed.")
    depends_on = models.ManyToManyField('self', related_name="prerequisite_for", help_text="If appropriate, specify what tasks must be completed before this one can start.")
    claim_date = models.DateField(null=True, blank=True)
    claimed_by = models.OneToOneField(Member, null=True, blank=True, related_name="tasks_claimed")
    prev_claimed_by =  models.ForeignKey(Member, null=True, blank=True, on_delete=models.SET_NULL, related_name="+") # Reminder: "+" means no backwards relation.
    work_done = models.BooleanField(default=False)
    work_accepted = models.NullBooleanField()
    recurring_task_template = models.ForeignKey(RecurringTaskTemplate, null=True, blank=True, on_delete=models.SET_NULL)
    def is_closed(self):
        "Returns True if claimant should receive credit for the task."
        if self.reviewer == None:
            return self.work_done
        else:
            return self.work_done and self.work_accepted
    def is_open(self):
        "Returns True if the task isn't yet completed or if there's a reviewer who hasn't yet accepted it."
        return not self.is_closed()
    def validate(self): # TODO: Rework this into Model.clean(). See Django's "model validation" docs.
        # TODO: questionable if deadline is set but task is an instance of RecurringTaskTemplate.
        if work_accepted and not work_done:
            return False, "Work cannot be reviewed before it is marked as completed."
        if prev_claimed_by == claimed_by:
            return False, "Member cannot claim a task they've previously claimed. Somebody else has to get a chance at it."
        if self.work_estimate < 0:
            # zero will mean "not yet estimated" but anything that has been estimated must have work > 0.
            return False, "Invalid work estimate."

class TaskNote(models.Model):
    author = models.ForeignKey(Member, null=True, blank=True, on_delete=models.SET_NULL) # Note will become anonymous if member is deleted.
    content = models.TextField(2048, help_text="Anything you want to say about the task. Instructions, hints, requirements, review feedback, etc.")
    task = models.ForeignKey(Task) # default on_delete, i.e. delete note if task is deleted.

from django.db import models
from django.contrib.auth.models import User, Group
from django.core.exceptions import PermissionDenied

class Assignment(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    deadline = models.DateTimeField()
    weight = models.IntegerField()
    points = models.IntegerField()

class Submission(models.Model):
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    grader = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='graded_set')
    file = models.FileField(upload_to='')
    score = models.FloatField(null=True, blank=True)

    def change_grade(self, user, new_grade):
        #If not the ta raise an error
        if self.grader != user:
            raise PermissionDenied
        #Update the grade
        self.score = new_grade

    def view_submission(self, user):
        #if not their submission raise an error 
        if not (self.author == user or self.grader == user or user.is_superuser):
            raise PermissionDenied
        #return their file
        return self.file
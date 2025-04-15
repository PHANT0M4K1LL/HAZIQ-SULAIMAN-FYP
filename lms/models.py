from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
import uuid
from django.core.exceptions import ValidationError
from datetime import datetime
from django.core.validators import FileExtensionValidator

class My_Contact(models.Model):
    name = models.CharField(max_length=250)
    email = models.EmailField()
    subject = models.CharField(max_length=250)
    message = models.TextField()
    added_on = models.DateTimeField(auto_now_add=True)
    is_approved = models.BooleanField(default=True)
    def __str__(self):
        return self.name
    class Meta:
        verbose_name_plural = "Contact_Table"
        
#Course Model
class Course(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    instructor = models.ForeignKey('Lecturer', on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    prerequisites = models.ManyToManyField('self', blank=True, symmetrical=False)
    def __str__(self):
        return f"Room {self.title}"

class ClassRoom(models.Model):
    room_number = models.CharField(max_length=50, unique=True)
    capacity = models.IntegerField()
    location = models.CharField(max_length=255)
    def __str__(self):
        return f"Room {self.room_number}"

# Enrollment Model
class Enrollment(models.Model):
    student = models.ForeignKey('Student', on_delete=models.CASCADE, related_name='enrollments', db_index=True)
    course = models.ForeignKey('Course', on_delete=models.CASCADE, db_index=True)
    enrolled_on = models.DateTimeField(auto_now_add=True)
    progress = models.FloatField(default=0.0)

    class Meta:
        unique_together = ('student', 'course')

# Payment Model
class Payment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_index=True)
    course = models.ForeignKey('Course', on_delete=models.CASCADE, db_index=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateTimeField(auto_now_add=True)
    transaction_id = models.CharField(max_length=100, unique=True)
    status = models.CharField(max_length=20, choices=[('pending', 'Pending'), ('completed', 'Completed'), ('failed', 'Failed')], default='pending')
    attachment = models.FileField(upload_to='payments/', blank=True, null=True)
    payment_method = models.CharField(max_length=50, choices=[('credit_card', 'Credit Card'), ('paypal', 'PayPal')], default='credit_card')

    def is_successful(self):
        return self.status == 'completed'

# Academic Session Model
class AcademicSession(models.Model):
    name = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField()
    active = models.BooleanField(default=False)
    def __str__(self):
        return self.name

# Semester Model
class Semester(models.Model):
    name = models.CharField(max_length=50)
    academic_session = models.ForeignKey(AcademicSession, on_delete=models.CASCADE, db_index=True)
    start_date = models.DateField()
    end_date = models.DateField()

# Assessment Model
class Assessment(models.Model):
    course = models.ForeignKey('Course', on_delete=models.CASCADE, db_index=True)
    title = models.CharField(max_length=255)
    description = models.TextField()
    max_score = models.IntegerField()
    due_date = models.DateTimeField()
    attachment = models.FileField(
        upload_to='assignments/', blank=True, null=True,
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx', 'ppt', 'pptx', 'mp4', 'avi', 'mov'])]
    )

    def __str__(self):
        return self.title

#Student Submission Model
class Submission(models.Model):
    student = models.ForeignKey('Student', on_delete=models.CASCADE, db_index=True)
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE, db_index=True)
    submitted_on = models.DateTimeField(auto_now_add=True)
    score = models.IntegerField(null=True, blank=True)
    graded_by = models.ForeignKey('Lecturer', on_delete=models.SET_NULL, null=True, blank=True, related_name='graded_submissions')
    attachment = models.FileField(
        upload_to='assignments/', blank=True, null=True,
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx', 'ppt', 'pptx', 'mp4', 'avi', 'mov'])]
    )

    def __str__(self):
        return f"{self.student} - {self.assessment.title}"


# Notifications Model
class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_index=True)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)
    attachment = models.FileField(upload_to='notifications/', blank=True, null=True)
    notification_type = models.CharField(max_length=50, choices=[
        ('quiz_due', 'Quiz Due'),
        ('assignment_due', 'Assignment Due'),
        ('general', 'General')
    ])

# Quiz Model
class Quiz(models.Model):
    course = models.ForeignKey('Course', on_delete=models.CASCADE, db_index=True)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    instructor = models.ForeignKey('Lecturer', on_delete=models.CASCADE, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    due_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    time_limit = models.PositiveIntegerField(null=True, blank=True, help_text="Time limit in minutes")
    attempt_count = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.title} - {self.course.title}"

class Question(models.Model):
    QUIZ_TYPES = (
        ('mcq', 'Multiple Choice'),
        ('tf', 'True/False'),
        ('short', 'Short Answer'),
    )
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, db_index=True)
    
    question_text1= models.TextField()
    question_type1= models.CharField(max_length=10, choices=QUIZ_TYPES, default='mcq')
    option1 = models.CharField(max_length=200, default='Default Option 1')
    option2 = models.CharField(max_length=200, default='Default Option 2')
    option3 = models.CharField(max_length=200, default='Default Option 3')
    option4 = models.CharField(max_length=200, default='Default Option 4')
    cat = (('Option1', 'Option1'), ('Option2', 'Option2'), ('Option3', 'Option3'), ('Option4', 'Option4'))
    answer = models.CharField(max_length=200, choices=cat, default='Option1')
    max_score = models.IntegerField(default=1)
    def get_question_type_display(self):
        return dict(self.QUIZ_TYPES).get(self.question_type1)
    def __str__(self):
        return self.question_text1
        
class Answer(models.Model):
    student = models.ForeignKey('Student', on_delete=models.CASCADE, db_index=True)
    submitted_answer = models.TextField()
    score = models.IntegerField(null=True, blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    feedback = models.TextField(blank=True, null=True)
    def __str__(self):
        return f"Answer by {self.student} - Score: {self.score if self.score is not None else 'Not graded'}"
        
# Student Model
class Student(models.Model):
    student_id = models.CharField(max_length=50, unique=True)
    student_name = models.CharField(max_length=255)
    student_rollno = models.CharField(max_length=50)
    student_course = models.ForeignKey(Course, on_delete=models.CASCADE)
    class_room = models.ForeignKey('ClassRoom', on_delete=models.CASCADE)
    def __str__(self):
        return f"{self.student_id}--({self.student_course})"
        
#Lecturer Model
class Lecturer(models.Model):
    lec_id = models.CharField(max_length=50, unique=True)
    lec_name = models.CharField(max_length=255)
    lec_specialization = models.CharField(max_length=255)
    lec_department = models.CharField(max_length=255)
    lec_email = models.EmailField(unique=True)
    lec_contact = models.CharField(max_length=20)
    def __str__(self):
        return f"{self.lec_name}"
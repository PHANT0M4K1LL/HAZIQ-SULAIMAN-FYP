from django.contrib import admin
from .models import (
    My_Contact,Course,Enrollment,Payment,AcademicSession,Semester,
    Assessment,Submission,Notification,Quiz,Question,Student,Lecturer,ClassRoom,
    Answer
)
############################################################################
admin.site.register(My_Contact)
admin.site.register(Course)
admin.site.register(Enrollment)
admin.site.register(Payment)
admin.site.register(AcademicSession)
admin.site.register(Semester)
admin.site.register(Assessment)
admin.site.register(Submission)
admin.site.register(Notification)
admin.site.register(Quiz)
admin.site.register(Question)
admin.site.register(Student)
admin.site.register(Lecturer)
admin.site.register(ClassRoom)
admin.site.register(Answer)
##########################################################################################
#Customizing the admin site header and title
admin.site.site_header = "University LMS Management System|Admin Panel"
admin.site.site_title = "Admin Panel"
#################################################

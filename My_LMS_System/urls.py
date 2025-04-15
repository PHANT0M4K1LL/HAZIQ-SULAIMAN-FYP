from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from lms import views as my_view
urlpatterns = [
    path('admin/', admin.site.urls),
    path('',my_view.Home,name='Home'),
    path('about-us/',my_view.About_Us,name='About_Us'),
    path('system-services/',my_view.Services,name='Services'),
    path('Contact_Us/',my_view.Contact_Us,name='Contact_Us'),
    path('SystemUsers/',my_view.SystemUsers, name='SystemUsers'),  # Ensure function name is correct
    ########################################################################
    path('registration_view/',my_view.registration_view,name='registration_view'),
    path('login_view/',my_view.login_view,name='login_view'),
    path('logout/',my_view.logout,name='logout'),
#####################################################################################################################
    path('admin_panel/',my_view.admin_panel,name='admin_panel'),  
    path('Add_Courses/',my_view.Add_Courses,name='Add_Courses'),
##################################################################################
    path('Add_Lecturer/',my_view.Add_Lecturer,name='Add_Lecturer'),
    path('view_lecturers',my_view.view_lecturers,name='view_lecturers'),
    path('search_lecturer/',my_view.search_lecturer, name='search_lecturer'),
    path('update_lecturer/',my_view.update_lecturer, name='update_lecturer'),
    path('delete_lecturer/<int:lec_id>/',my_view.delete_lecturer, name='delete_lecturer'),
######################################################################################
    path('View_Course/',my_view.View_Course,name='View_Course'),
    path("delete_course/<int:course_id>/",my_view.delete_course,name="delete_course"),
    path('search-course/',my_view.search_course, name='search_course'),
    path('update-course/',my_view.update_course, name='update_course'),
#########################################################################################################################
    path('Add_ClassRoom/',my_view.Add_ClassRoom,name='Add_ClassRoom'),
    path('manage/',my_view.manage_classrooms, name='manage_classrooms'),
    path('search_classroom/',my_view.search_classroom, name='search_classroom'),
    path('update_classroom/',my_view.update_classroom, name='update_classroom'),
    path('delete_classroom/<int:classroom_id>/',my_view.delete_classroom, name='delete_classroom'),
###############################################################################################################################################
    path('Add_Student/',my_view.Add_Student,name='Add_Student'),
    path('manage-students/',my_view.manage_students, name='manage_students'),
    path('search-student/',my_view.search_student, name='search_student'),
    path('update-student/',my_view.update_student, name='update_student'),
    path('delete-student/<str:student_id>/',my_view.delete_student, name='delete_student'),
#################################################################################################
    path('add_enrollments/',my_view.add_enrollments,name='add_enrollments'),
    path('my-enrollments/',my_view.manage_enrollments, name='view_enrollments'),
    path('enrollments/search/',my_view.search_enrollment, name='search_enrollment'),
    path('enrollments/update/',my_view.update_enrollment, name='update_enrollment'),
    path('enrollments/delete/<int:enrollment_id>/',my_view.delete_enrollment, name='delete_enrollment'),
##################################################################################################################################
    path('Add_Payment/',my_view.Add_Payment,name='Add_Payment'),
    path('payments/',my_view.view_payments, name='view_payments'),
    path('search-payment/',my_view.search_payment, name='search_payment'),
    path('update-payment/',my_view.update_payment, name='update_payment'),
    path('delete-payment/<int:payment_id>/',my_view.delete_payment, name='delete_payment'),
######################################################################################################################
    path('add_assessment/',my_view.add_assessment,name='add_assessment'),
    path('View_Assessment/',my_view.View_Assessment,name='View_Assessment'),
    path("get_assessment/<int:assessment_id>/",my_view.get_assessment, name="get_assessment"),
    path('update_assessment/',my_view.update_assessment,name='update_assessment'),
    path('delete-assessment/<int:assessment_id>/',my_view.delete_assessment, name='delete_assessment'),
    #######################################################################################################
    path('add_quiz/',my_view.add_quiz, name='Add_Quiz'),
    path('manage_quizzes/',my_view.manage_quizzes,name='manage_quizzes'),
    path('search_quiz/',my_view.search_quiz,name='search_quiz'),
    path('update_quiz/',my_view.update_quiz,name='update_quiz'),
    path('delete_quiz/<int:quiz_id>/',my_view.delete_quiz, name='delete_quiz'),
    ###################################################################################
    path('manage-questions/',my_view.Add_Question, name='Add_Question'),
    path('search_question/',my_view.search_question, name='search_question'),
    path('update_question/',my_view.update_question, name='update_question'),
    path('delete_question/<int:question_id>/',my_view.delete_question, name='delete_question'),
##############################################################################################
    path('Add_Answer/',my_view.Add_Answer,name='Add_Answer'),
    path('download-answer/<int:answer_id>/',my_view.download_answer, name='download_answer'),
    path('delete_answer/<int:answer_id>/',my_view.delete_answer, name='delete_answer'),
##########################################################################################################################
    path('manage-academic-session/',my_view.add_academic_session, name='Add_AcademicSession'),
    path('manage/sessions/',my_view.view_sessions, name='view_sessions'),
    path('manage/sessions/search/',my_view.search_session, name='search_session'),
    path('manage/sessions/update/',my_view.update_session, name='update_session'),
    path('manage/sessions/delete/<int:session_id>/',my_view.delete_session, name='delete_session'),
################################################################################################################################
    path('Add_Semester/',my_view.Add_Semester,name='Add_Semester'),
    path('manage-semester/',my_view.manage_semesters, name='manage_semester'),
    path('search-semester/',my_view.search_semester, name='search_semester'),
    path('update-semester/',my_view.update_semester, name='update_semester'),
    path('delete-semester/<int:semester_id>/',my_view.delete_semester, name='delete_semester'),
########################################################################################################################
    path('Add_Notifications/',my_view.Add_Notifications,name='Add_Notifications'),
    path('manage-notifications/',my_view.manage_notifications, name='view_notifications'),
    path('search-notification/',my_view.search_notification, name='search_notification'),
    path('update-notification/',my_view.update_notification, name='update_notification'),
    path('delete-notification/<int:not_id>/',my_view.delete_notification, name='delete_notification'),
    #######################################################################################################################
    path('Submit_Answer/',my_view.Submit_Answer,name='Submit_Answer'),
    #######################################################################################################################
    path('manage-submissions/',my_view.manage_submissions,name='add_submission'),
    path('manage_submissions/',my_view.manage_submissions1, name='manage_submissions1'),
    path('search_submission/',my_view.search_submission, name='search_submission'),
    path('delete_submission/<int:submission_id>/',my_view.delete_submission, name='delete_submission'),
    ############################################################
    path('View_role_wise_user/',my_view.View_role_wise_user,name='View_role_wise_user'),
    #######################################################################################################
    path('student_dashboard/',my_view.student_dashboard,name='student_dashboard'),
    path('StudentAdd_Student/',my_view.StudentAdd_Student,name='StudentAdd_Student'),
    path('Studentmanage_students/',my_view.Studentmanage_students,name='Studentmanage_students'),
    path('StudentSubmit_Answer/',my_view.StudentSubmit_Answer,name='StudentSubmit_Answer'),
    path('Studentmanage_submissions/',my_view.Studentmanage_submissions,name='Studentmanage_submissions'),
    path('Studentadd_enrollments/',my_view.Studentadd_enrollments,name='Studentadd_enrollments'),
    path('Studentmanage_enrollments/',my_view.Studentmanage_enrollments,name='Studentmanage_enrollments'),
    path('manage_notifications/',my_view.studentmanage_notifications,name='studentmanage_notifications'),
    path('studentview_payments/',my_view.studentview_payments,name='studentview_payments'),
    ###################################################################################################
    path('lecturer_dashboard/',my_view.lecturer_dashboard,name='lecturer_dashboard'),
    path('LecturerAdd_Notifications/',my_view.LecturerAdd_Notifications,name='LecturerAdd_Notifications'),
    path('LecturerAdd_Courses/',my_view.LecturerAdd_Courses,name='LecturerAdd_Courses'),
    path('LecturerAdd_Question/',my_view.LecturerAdd_Question,name='LecturerAdd_Question'),
    path('Lectureradd_quiz/',my_view.Lectureradd_quiz,name='Lectureradd_quiz'),
    path('Lectureradd_assessment/',my_view.Lectureradd_assessment,name='Lectureradd_assessment'),
    path('Lecturermanage_submissions1/',my_view.Lecturermanage_submissions1,name='Lecturermanage_submissions1'),
    path('LecturerAdd_Student/',my_view.LecturerAdd_Student,name='LecturerAdd_Student'),
    path('LecturerAdd_Answer/',my_view.LecturerAdd_Answer,name='LecturerAdd_Answer'),
############################################################################################################################

]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

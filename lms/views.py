from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import Group, User
from django.contrib import messages
from django.http import JsonResponse
from django.urls import reverse
from .forms import UserRegistrationForm, UserLoginForm
from django.views.decorators.csrf import csrf_exempt
import json
from django.db import transaction
# from .forms import AnswerForm  # Assuming you create a form for the Answer model
from django.views.decorators.http import require_http_methods
from django.views.decorators.http import require_GET, require_POST
from django.core.exceptions import ValidationError
from django.core.files.storage import FileSystemStorage

from .models import(
  My_Contact,Course,Lecturer,ClassRoom,Student,Enrollment,Payment,
  Assessment,Quiz,Question,Answer,AcademicSession,Semester,Notification,Submission
)
from uuid import uuid4  # to generate unique transaction ids
from django.utils.dateparse import parse_datetime
from django.views.decorators.csrf import csrf_protect  # Use csrf_protect instead of csrf_exempt
from .forms import BulkQuestionForm

from django.utils import timezone
from datetime import datetime
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate,logout as auth_logout  
from .forms import UserRegistrationForm  # Custom form for user registration
from django.http import JsonResponse, HttpResponseForbidden,HttpResponse
from decimal import Decimal
from .forms import PaymentForm  # assuming you have a form to handle payment input
from django.core.exceptions import ObjectDoesNotExist
import os

def Home(request):
    return render(request,'My_Home/home.html')
    
def About_Us(request):
    return render(request,'My_Home/about.html')
    
def Services(request):
    return render(request,'My_Home/Facilities.html')
    

def Contact_Us(request):
    if request.method == "POST":
        name = request.POST.get('name')
        email = request.POST.get('email')
        subject = request.POST.get('feedback')  # Renaming 'feedback' to 'subject'
        message = request.POST.get('message')
        contact_entry=My_Contact(name=name, email=email, subject=subject, message=message)
        # Return a success response for AJAX
        contact_entry.save()
        return JsonResponse({"success": True, "message": "Your message has been sent successfully!"})
    return render(request, 'My_Home/Contact_us.html')
    
def SystemUsers(request):
    return render(request, 'user/Admin_View.html')  # Ensure the correct path
    
def registration_view(request):
    """
    Handles user registration by processing the registration form,
    assigning roles, and adding the user to the appropriate group.
    """
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            role = form.cleaned_data.get('role').lower()  # Convert role to lowercase

            role_to_group = {
                'admin': {'group_name': 'Admin', 'is_superuser': True, 'is_staff': True},
                'lecturer': {'group_name': 'Lecturer', 'is_superuser': False, 'is_staff': True},
                'student': {'group_name': 'Student', 'is_superuser': False, 'is_staff': False},
            }

            role_settings = role_to_group.get(role)
            if role_settings:
                try:
                    # Fetch or create the group
                    group, created = Group.objects.get_or_create(name=role_settings['group_name'])

                    # Set user attributes (is_superuser, is_staff)
                    user.is_superuser = role_settings['is_superuser']
                    user.is_staff = role_settings['is_staff']

                    # Save user and add them to the group
                    user.save()
                    user.groups.add(group)

                    messages.success(request, "Registration successful! You can now log in.")
                    return redirect('login_view')
                except Group.DoesNotExist:
                    messages.error(request, f"The role group '{role_settings['group_name']}' does not exist.")
                    return redirect('registration_view')
            else:
                messages.error(request, "Invalid role selected.")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = UserRegistrationForm()
    
    users = User.objects.all()  # Fetch all users
    return render(request, 'user/super_registration.html', {'form': form, 'users': users})
    
def login_view(request):
    """
    Handles user login by authenticating credentials using username (email),
    and redirects to the appropriate dashboard based on the user's role.
    """
    if request.method == 'POST':
        username = request.POST.get('username')  # User enters username
        password = request.POST.get('password')

        # Authenticate the user
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)  # Log the user in

            # Determine the user's dashboard based on their group
            if user.groups.filter(name='Admin').exists():
                dashboard_url = reverse('admin_panel')
            elif user.groups.filter(name='Lecturer').exists():
                dashboard_url = reverse('lecturer_dashboard')
            elif user.groups.filter(name='Student').exists():
                dashboard_url = reverse('student_dashboard')
            else:
                messages.error(request, "You are not assigned to any role.")
                return JsonResponse({'success': False, 'message': 'You are not assigned to any role.'})
            # Send success response for SweetAlert
            return JsonResponse({'success': True, 'redirect_url': dashboard_url})
        else:
            messages.error(request, "Invalid username or password.")
            return JsonResponse({'success': False, 'message': 'Invalid username or password.'})
    return render(request, 'user/super_login.html')

def logout(request):
    """
    Handles user logout and redirects to the login page with a success message.
    """
    if request.user.is_authenticated:
        auth_logout(request)  # Call the renamed Django logout method
        messages.success(request, "You have successfully logged out.")
    else:
        messages.warning(request, "You were not logged in.")
    return redirect('login_view')  # Redirect to the login page

@login_required
def admin_panel(request):
    """
    View for the admin dashboard that groups users by specific roles
    and passes the data to the template.
    Only accessible by superusers.
    """
    if not request.user.is_superuser:
        return HttpResponseForbidden("You do not have permission to access this page.")

    users = User.objects.all()
    enrollments = Enrollment.objects.all()
    students = Student.objects.all()
    lecturers = Lecturer.objects.all()

    context = {
        'users': users,
        'enrollments': enrollments,
        'students': students,
        'lecturers': lecturers,
        'total_students': students.count(),
        'total_enrollments': enrollments.count(),
        'total_lecturers': lecturers.count(),
    }

    return render(request, 'My_Admin/my_admin.html', context)
    

def Add_Courses(request):
    """View to display courses and handle course creation."""
    if request.method == "POST":
        title = request.POST.get('title')
        description = request.POST.get('description')
        instructor_id = request.POST.get('instructor')
        price = request.POST.get('price')
        prerequisites = request.POST.getlist('prerequisites')

        if not title or not description or not instructor_id or not price:
            messages.error(request, "All fields are required.")
            return redirect('Add_Courses')

        try:
            price = Decimal(price)
        except ValueError:
            messages.error(request, "Invalid price format.")
            return redirect('Add_Courses')

        instructor = get_object_or_404(Lecturer, id=instructor_id)

        course = Course.objects.create(
            title=title,
            description=description,
            instructor=instructor,
            price=price
        )

        # Assign prerequisites if valid course IDs are provided
        if prerequisites:
            valid_courses = Course.objects.filter(id__in=prerequisites)
            course.prerequisites.set(valid_courses)

        messages.success(request, "Course added successfully!")
        return redirect('Add_Courses')

    courses = Course.objects.all().order_by('-created_at')
    instructors = Lecturer.objects.all()
    enrollments = Enrollment.objects.all()
    students = Student.objects.all()
    lecturers = Lecturer.objects.all()

    return render(request, 'My_Admin/Course/Add_Course.html', {
        'courses': courses,
        'instructors': instructors,
        'enrollments':enrollments,
        'students':students,
        'lecturers':lecturers
    })
    
def View_Course(request):
    courses=Course.objects.all()
    instructors=Lecturer.objects.all()
    enrollments = Enrollment.objects.all()
    students = Student.objects.all()
    lecturers = Lecturer.objects.all()
    return render(request,'My_Admin/Course/View_Course.html',
                  {'courses':courses,
                   'instructors':instructors,
                   'enrollments':enrollments,
                   'students':students,
                   'lecturers':lecturers
                   })
                   
def search_course(request):
    """View to search for a course by ID and return its details in JSON format."""
    course_id = request.GET.get('course_id')
    if not course_id:
        return JsonResponse({'success': False, 'message': 'Course ID is required.'})
    try:
        course = Course.objects.get(id=course_id)
        return JsonResponse({
            'success': True,
            'title': course.title,
            'description': course.description,
            'instructor_id': course.instructor.id,
            'price': float(course.price),
        })
    except Course.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Course not found.'})
        
def update_course(request):
    """View to update course details based on user input."""
    if request.method == "POST":
        course_id = request.POST.get('course_id')
        title = request.POST.get('title')
        description = request.POST.get('description')
        instructor_id = request.POST.get('instructor_id')
        price = request.POST.get('price')

        if not course_id or not title or not description or not instructor_id or not price:
            return JsonResponse({'success': False, 'message': 'All fields are required.'})

        try:
            course = get_object_or_404(Course, id=course_id)
            instructor = get_object_or_404(Lecturer, id=instructor_id)
            course.title = title
            course.description = description
            course.instructor = instructor
            course.price = Decimal(price)
            course.save()

            return JsonResponse({'success': True, 'message': 'Course updated successfully!'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Error updating course: {str(e)}'})

    return JsonResponse({'success': False, 'message': 'Invalid request method.'})
    
def delete_course(request, course_id):
    """Handles course deletion"""
    course = get_object_or_404(Course, id=course_id)
    course.delete()
    return redirect("View_Course")
    
def Add_Lecturer(request):
    if request.method == "POST":
        lec_id = request.POST.get("lec_id")
        lec_name = request.POST.get("lec_name")
        lec_specialization = request.POST.get("lec_specialization")
        lec_department = request.POST.get("lec_department")
        lec_email = request.POST.get("lec_email")
        lec_contact = request.POST.get("lec_contact")
        
        if Lecturer.objects.filter(lec_id=lec_id).exists() or Lecturer.objects.filter(lec_email=lec_email).exists():
            messages.error(request, "Lecturer ID or Email already exists!")
        else:
            Lecturer.objects.create(
                lec_id=lec_id,
                lec_name=lec_name,
                lec_specialization=lec_specialization,
                lec_department=lec_department,
                lec_email=lec_email,
                lec_contact=lec_contact,
            )
            messages.success(request, "Lecturer added successfully!")
        return redirect("Add_Lecturer")
    enrollments = Enrollment.objects.all()
    students = Student.objects.all()
    lecturers = Lecturer.objects.all()
    lecturers = Lecturer.objects.all()
    return render(request, "My_Admin/Lecturer/Add_Lecturer.html", {"lecturers": lecturers,
                                                                   'students':students,
                                                                   'enrollments':enrollments})
                                                                   
# View Lecturers
def view_lecturers(request):
    lecturers = Lecturer.objects.all()
    enrollments = Enrollment.objects.all()
    students = Student.objects.all()
    lecturers = Lecturer.objects.all()
    return render(request, 'My_Admin/Lecturer/View_Lecturer.html', 
                  {'lecturers': lecturers,
                   'enrollments':enrollments,
                   'students':students,
                   'lecturers':lecturers})

# Search Lecturer
def search_lecturer(request):
    if request.method == "GET":
        lecturer_id = request.GET.get('lecturer_id')
        try:
            lecturer = Lecturer.objects.get(lec_id=lecturer_id)
            data = {
                "success": True,
                "lec_id": lecturer.lec_id,
                "lec_name": lecturer.lec_name,
                "lec_specialization": lecturer.lec_specialization,
                "lec_department": lecturer.lec_department,
                "lec_email": lecturer.lec_email,
                "lec_contact": lecturer.lec_contact
            }
            return JsonResponse(data)
        except Lecturer.DoesNotExist:
            return JsonResponse({"success": False, "message": "Lecturer not found!"})

# Update Lecturer
def update_lecturer(request):
    if request.method == "POST":
        lecturer_id = request.POST.get('lecturer_id')
        lec_name = request.POST.get('lec_name')
        lec_specialization = request.POST.get('lec_specialization')
        lec_department = request.POST.get('lec_department')
        lec_email = request.POST.get('lec_email')
        lec_contact = request.POST.get('lec_contact')

        try:
            lecturer = Lecturer.objects.get(lec_id=lecturer_id)
            lecturer.lec_name = lec_name
            lecturer.lec_specialization = lec_specialization
            lecturer.lec_department = lec_department
            lecturer.lec_email = lec_email
            lecturer.lec_contact = lec_contact
            lecturer.save()
            return JsonResponse({"success": True, "message": "Lecturer updated successfully!"})
        except Lecturer.DoesNotExist:
            return JsonResponse({"success": False, "message": "Lecturer not found!"})
def delete_lecturer(request, lec_id):
    lecturer = get_object_or_404(Lecturer, id=lec_id)
    lecturer.delete()
    return redirect('view_lecturers')
    
def Add_ClassRoom(request):
    if request.method == "POST":
        room_number = request.POST.get("room_number")
        capacity = request.POST.get("capacity")
        location = request.POST.get("location")
        if ClassRoom.objects.filter(room_number=room_number).exists():
            messages.error(request, "Room number already exists!")
        else:
            ClassRoom.objects.create(
                room_number=room_number,
                capacity=capacity,
                location=location
            )
            messages.success(request, "Classroom added successfully!")
        return redirect("Add_ClassRoom")
    classrooms = ClassRoom.objects.all()
    enrollments = Enrollment.objects.all()
    students = Student.objects.all()
    lecturers = Lecturer.objects.all()
    return render(request, "My_Admin/Classroom/Add_Classroom.html", 
                  {"classrooms": classrooms,
                   'enrollments':enrollments,
                   'students':students,
                   'lecturers':lecturers})
                   
def manage_classrooms(request):
    """ View for displaying the manage classrooms page with the list of classrooms."""
    classrooms = ClassRoom.objects.all()
    enrollments = Enrollment.objects.all()
    students = Student.objects.all()
    lecturers = Lecturer.objects.all()
    return render(request, 'My_Admin/Classroom/View_Classroom.html',
                   {'classrooms': classrooms,
                    'enrollments':enrollments,
                    'students':students,
                    'lecturers':lecturers})

def search_classroom(request):
    """ AJAX view to retrieve classroom details."""
    if request.method == "GET" and 'classroom_id' in request.GET:
        classroom_id = request.GET.get('classroom_id')
        try:
            classroom = ClassRoom.objects.get(id=classroom_id)
            data = {
                'room_number': classroom.room_number,
                'capacity': classroom.capacity,
                'location': classroom.location,
                'success': True
            }
        except ClassRoom.DoesNotExist:
            data = {'success': False}
        return JsonResponse(data)

def update_classroom(request):
    """ AJAX view to update classroom details."""
    if request.method == "POST":
        classroom_id = request.POST.get('classroom_id')
        room_number = request.POST.get('room_number')
        capacity = request.POST.get('capacity')
        location = request.POST.get('location')
        
        try:
            classroom = ClassRoom.objects.get(id=classroom_id)
            classroom.room_number = room_number
            classroom.capacity = capacity
            classroom.location = location
            classroom.save()
            return JsonResponse({'success': True})
        except ClassRoom.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Classroom not found'})
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})

def delete_classroom(request, classroom_id):
    """ View to delete a classroom."""
    classroom = get_object_or_404(ClassRoom, id=classroom_id)
    classroom.delete()
    return redirect('manage_classrooms')
    

def Add_Student(request):
    if request.method == "POST":
        student_id = request.POST.get("student_id")
        student_name = request.POST.get("student_name")
        student_rollno = request.POST.get("student_rollno")
        student_course_id = request.POST.get("student_course")
        class_room_id = request.POST.get("class_room")

        try:
            student_course = Course.objects.get(title=student_course_id)
            class_room = ClassRoom.objects.get(room_number=class_room_id)
            Student.objects.create(
                student_id=student_id,
                student_name=student_name,
                student_rollno=student_rollno,
                student_course=student_course,
                class_room=class_room,
            )
            messages.success(request, "Student added successfully!")
        except Course.DoesNotExist:
            messages.error(request, "Selected course does not exist!")
        except ClassRoom.DoesNotExist:
            messages.error(request, "Selected classroom does not exist!")
        except Exception as e:
            messages.error(request, f"Error adding student: {str(e)}")

        return redirect("Add_Student")

    students = Student.objects.select_related("student_course", "class_room").all()
    courses = Course.objects.all()
    class_rooms = ClassRoom.objects.all()
    enrollments = Enrollment.objects.all()
    students = Student.objects.all()
    lecturers = Lecturer.objects.all()
    return render(request, "My_Admin/Student/Add_Student.html", {
        "students": students,
        "courses": courses,
        "class_rooms": class_rooms,
        'lecturers':lecturers,
        'enrollments':enrollments
    })
    
def manage_students(request):
    students = Student.objects.all()
    courses = Course.objects.all()
    classrooms = ClassRoom.objects.all()
    enrollments = Enrollment.objects.all()
    students = Student.objects.all()
    lecturers = Lecturer.objects.all()
    return render(request, 'My_Admin/Student/View_Student.html', 
                  {'students': students,
                    'courses': courses,
                      'classrooms': classrooms,
                      'enrollments':enrollments,
                      'lecturers':lecturers})
                      
# View for searching the student and returning their data
def search_student(request):
    student_id = request.GET.get('student_id')
    student = Student.objects.filter(id=student_id).first()

    if student:
        # Return student data as JSON
        response_data = {
            'success': True,
            'student_name': student.student_name,
            'student_rollno': student.student_rollno,
            'student_course': student.student_course.title,  # Assuming Course model has title field
            'class_room': student.class_room.room_number  # Assuming ClassRoom model has room_number field
        }
    else:
        response_data = {'success': False}

    return JsonResponse(response_data)

# View for updating the student data
def update_student(request):
    if request.method == 'POST':
        student_id = request.POST.get('student_id')
        student_name = request.POST.get('student_name')
        student_rollno = request.POST.get('student_rollno')
        student_course = request.POST.get('student_course')  # This will be the course name, like "ITP"
        class_room = request.POST.get('class_room')  # This will be the classroom number or identifier

        # Fetch the student by ID
        student = Student.objects.filter(id=student_id).first()

        if student:
            # Fetch the Course object using the course name (student_course)
            course = Course.objects.filter(title=student_course).first()

            if not course:
                return JsonResponse({'success': False, 'message': 'Course not found!'})

            # Fetch the ClassRoom object using the classroom identifier (class_room)
            classroom = ClassRoom.objects.filter(room_number=class_room).first()

            if not classroom:
                return JsonResponse({'success': False, 'message': 'ClassRoom not found!'})

            # Update the student fields with the new data
            student.student_name = student_name
            student.student_rollno = student_rollno
            student.student_course = course  # Assign the Course instance
            student.class_room = classroom  # Assign the ClassRoom instance
            student.save()

            response_data = {'success': True}
        else:
            response_data = {'success': False, 'message': 'Student not found'}

        return JsonResponse(response_data)
        
def delete_student(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    student.delete()
    return redirect('manage_students')
    
def add_enrollments(request):
    if request.method == "POST":
        student_id = request.POST.get('student')
        course_id = request.POST.get('course')
        progress = request.POST.get('progress', 0)

        student = Student.objects.get(id=student_id)
        course = Course.objects.get(id=course_id)

        if Enrollment.objects.filter(student=student, course=course).exists():
            messages.error(request, "This student is already enrolled in the selected course.")
        else:
            Enrollment.objects.create(student=student, course=course, progress=progress)
            messages.success(request, "Enrollment added successfully!")

        return redirect('add_enrollments')

    students = Student.objects.all()
    courses = Course.objects.all()
    enrollments = Enrollment.objects.all()
    students = Student.objects.all()
    lecturers = Lecturer.objects.all()
    enrollments = Enrollment.objects.select_related('student', 'course').all()

    context = {
        'students': students,
        'courses': courses,
        'enrollments': enrollments,
        'lecturers':lecturers
    }
    return render(request, 'My_Admin/Enrollement/Add_Enrollment.html', context)
    

def manage_enrollments(request):
    students = Student.objects.all()
    courses = Course.objects.all()
    enrollments = Enrollment.objects.all()
    students = Student.objects.all()
    lecturers = Lecturer.objects.all()
    enrollments = Enrollment.objects.select_related('student', 'course').all()

    # Enrollment progress summary (Completed, Ongoing, Pending)
    completed_courses = Enrollment.objects.filter(progress=100).count()
    ongoing_courses = Enrollment.objects.filter(progress__gt=0, progress__lt=100).count()  # Corrected line
    pending_courses = Enrollment.objects.filter(progress=0).count()

    return render(request, 'My_Admin/Enrollement/View_Enrollement.html', {
        'students': students,
        'courses': courses,
        'enrollments': enrollments,
        'completed_courses': completed_courses,
        'ongoing_courses': ongoing_courses,
        'pending_courses': pending_courses,
        'lecturers':lecturers
    })
    
def search_enrollment(request):
    student_id = request.GET.get('student_id')
    course_id = request.GET.get('course_id')
    
    try:
        enrollment = Enrollment.objects.get(student_id=student_id, course_id=course_id)
        return JsonResponse({
            'success': True,
            'progress': enrollment.progress,
        })
    except Enrollment.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Enrollment not found'})
        
@csrf_exempt
def update_enrollment(request):
    if request.method == 'POST':
        student_id = request.POST.get('student_id')
        course_id = request.POST.get('course_id')
        progress = request.POST.get('progress')
        
        try:
            enrollment = Enrollment.objects.get(student_id=student_id, course_id=course_id)
            enrollment.progress = float(progress)
            enrollment.save()
            return JsonResponse({'success': True})
        except Enrollment.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Enrollment not found'})
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})
    
def delete_enrollment(request, enrollment_id):
    enrollment = get_object_or_404(Enrollment, id=enrollment_id)
    enrollment.delete()
    return redirect('view_enrollments')
    
def Add_Payment(request):
    # Get all the users and courses to populate the form options
    users = User.objects.all()
    courses = Course.objects.all()
    enrollments = Enrollment.objects.all()
    students = Student.objects.all()
    lecturers = Lecturer.objects.all()
    # Get all the payments to display in the table
    payments = Payment.objects.all()
    if request.method == 'POST':
        # Handle new payment creation
        form = PaymentForm(request.POST, request.FILES)
        if form.is_valid():
            # Save the payment if the form is valid
            payment = form.save(commit=False)
            # Optionally, you can set additional fields, like user and course
            payment.user = User.objects.get(id=request.POST['user'])
            payment.course = Course.objects.get(id=request.POST['course'])
            payment.transaction_id = str(uuid4())  # Generate a unique transaction_id
            payment.save()
            # Add a success message
            messages.success(request, 'Payment has been added successfully!')
            return redirect('Add_Payment')  # Redirect to the same page after submission
        else:
            # Add error message if form is invalid
            messages.error(request, 'There was an error with the payment form.')
    else:
        form = PaymentForm()
    return render(request, 'My_Admin/Payment/Add_Payment.html', {
        'form': form,
        'users': users,
        'courses': courses,
        'payments': payments,
        'enrollments':enrollments,
        'students':students,
        'lecturers':lecturers
    })
    
# View to list all payments
def view_payments(request):
    payments = Payment.objects.all()
    enrollments = Enrollment.objects.all()
    students = Student.objects.all()
    lecturers = Lecturer.objects.all()
    return render(request, 'My_Admin/Payment/View_Payment.html',
                   {'payments': payments,
                     'courses': Course.objects.all(),
                     'enrollments':enrollments,
                     'students':students,
                     'lecturers':lecturers
                     
                     })

# View to search for a specific payment by ID
def search_payment(request):
    if request.method == "GET":
        payment_id = request.GET.get('payment_id')
        try:
            payment = Payment.objects.get(id=payment_id)
            response_data = {
                'success': True,
                'amount': payment.amount,
                'payment_date': payment.payment_date.strftime('%Y-%m-%dT%H:%M'),
                'payment_method': payment.payment_method,
                'status': payment.status,
            }
            return JsonResponse(response_data)
        except Payment.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Payment not found'})

# View to update a payment
@csrf_exempt
def update_payment(request):
    if request.method == "POST":
        payment_id = request.POST.get('payment_id')
        try:
            payment = Payment.objects.get(id=payment_id)
            payment.amount = request.POST.get('amount')
            payment.payment_date = request.POST.get('payment_date')
            payment.payment_method = request.POST.get('payment_method')
            payment.status = request.POST.get('status')

            # Handle file attachment if present
            if request.FILES.get('attachment'):
                payment.attachment = request.FILES['attachment']
            
            payment.save()
            return JsonResponse({'success': True})
        except Payment.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Payment not found'})

# View to delete a payment
def delete_payment(request, payment_id):
    try:
        payment = Payment.objects.get(id=payment_id)
        payment.delete()
        messages.success(request, 'Payment deleted successfully.')
    except Payment.DoesNotExist:
        messages.error(request, 'Payment not found.')
    return redirect('view_payments')
    

# Add Assessment View
def add_assessment(request):
    if request.method == 'POST':
        # Get the form data
        course_id = request.POST.get('course')
        title = request.POST.get('title')
        description = request.POST.get('description')
        max_score = request.POST.get('max_score')
        due_date = request.POST.get('due_date')
        attachment = request.FILES.get('attachment')
        # Create a new Assessment object
        assessment = Assessment(
            course_id=course_id,
            title=title,
            description=description,
            max_score=max_score,
            due_date=due_date,
            attachment=attachment
        )
        try:
            assessment.save()  # Save the assessment to the database
            messages.success(request, "Assessment added successfully.")
            return redirect('add_assessment')  # Redirect to the same page to display the updated list
        except Exception as e:
            messages.error(request, f"Error adding assessment: {e}")
            return redirect('add_assessment')  # Redirect to the same page on error
    # If the request method is GET, render the form
    courses = Course.objects.all()  # Get all available courses for the dropdown
    assessments = Assessment.objects.all()  # Get all assessments to display in the table
    enrollments = Enrollment.objects.all()
    students = Student.objects.all()
    lecturers = Lecturer.objects.all()
    context = {
        'courses': courses,
        'assessments': assessments,
        'students':students,
        'enrollments':enrollments,
        'lecturers':lecturers
    }
    return render(request, 'My_Admin/Assessment/Add_Assessment.html', context)
    
def View_Assessment(request):
    # If the request method is GET, render the form
    courses = Course.objects.all()  # Get all available courses for the dropdown
    assessments = Assessment.objects.all()  # Get all assessments to display in the table
    enrollments = Enrollment.objects.all()
    students = Student.objects.all()
    lecturers = Lecturer.objects.all()
    context = {
        'courses': courses,
        'assessments': assessments,
        'enrollments':enrollments,
        'students':students,
        'lecturers':lecturers
    }
    return render(request,'My_Admin/Assessment/View_Assessment.html', context)
    
def get_assessment(request, assessment_id):
    try:
        assessment = Assessment.objects.get(id=assessment_id)
        data = {
            "success": True,
            "course_id": assessment.course.id,
            "title": assessment.title,
            "description": assessment.description,
            "max_score": assessment.max_score,
            "due_date": assessment.due_date.strftime('%Y-%m-%dT%H:%M'),  # Format for datetime-local
        }
    except Assessment.DoesNotExist:
        data = {"success": False}

    return JsonResponse(data)
    
@csrf_exempt
def update_assessment(request):
    if request.method == "POST":
        try:
            # Get the form data
            assessment_id = request.POST.get('assessment_id')
            course_id = request.POST.get('course')
            title = request.POST.get('title')
            description = request.POST.get('description')
            max_score = request.POST.get('max_score')
            due_date = request.POST.get('due_date')

            # Validate due date format
            try:
                due_date = datetime.strptime(due_date, "%Y-%m-%dT%H:%M")
            except ValueError:
                return JsonResponse({'success': False, 'message': 'Invalid Due Date format'})

            # Handle attachment file if provided
            attachment = request.FILES.get('attachment', None)

            assessment = get_object_or_404(Assessment, id=assessment_id)

            # Update fields
            assessment.course = Course.objects.get(id=course_id)
            assessment.title = title
            assessment.description = description
            assessment.max_score = max_score
            assessment.due_date = due_date

            if attachment:
                # Handle file storage and update
                file_path = os.path.join('media', 'attachments', attachment.name)
                with open(file_path, 'wb') as f:
                    for chunk in attachment.chunks():
                        f.write(chunk)
                assessment.attachment = file_path

            assessment.save()

            return JsonResponse({'success': True, 'message': 'Assessment updated successfully'})

        except Exception as e:
            return JsonResponse({'success': False, 'message': f'An error occurred: {str(e)}'})

    return JsonResponse({'success': False, 'message': 'Invalid request method'})
    
# View to delete an assessment
def delete_assessment(request, assessment_id):
    try:
        assessment = Assessment.objects.get(id=assessment_id)
        assessment.delete()
    except Assessment.DoesNotExist:
        messages.error(request, 'Assessment not found.')
    return redirect('View_Assessment')  # Make sure 'view_assessments' is a valid URL name
    
def add_quiz(request):
    if request.method == "POST":
        # Get form data from the POST request
        course_id = request.POST.get('course')
        title = request.POST.get('title')
        description = request.POST.get('description')
        instructor_id = request.POST.get('instructor')
        due_date = request.POST.get('due_date')
        time_limit = request.POST.get('time_limit')
        attempt_count = request.POST.get('attempt_count')

        # Check if course_id or instructor_id is empty
        if not course_id or not instructor_id:
            messages.error(request, "Please select both a course and an instructor.")
            return redirect('Add_Quiz')

        try:
            # Get the Course and Lecturer objects based on the selected IDs
            course = Course.objects.get(id=course_id)
            instructor = Lecturer.objects.get(id=instructor_id)

            # Create and save a new Quiz
            quiz = Quiz(
                course=course,
                title=title,
                description=description,
                instructor=instructor,
                due_date=due_date,
                time_limit=time_limit,
                attempt_count=attempt_count
            )
            quiz.save()
            messages.success(request, "Quiz successfully added!")
        except Exception as e:
            messages.error(request, f"Error adding quiz: {e}")
        
        # Redirect back to the same page after form submission
        return redirect('Add_Quiz')

    # Get existing quizzes and other necessary data
    quizzes = Quiz.objects.all()
    courses = Course.objects.all()
    lecturers = Lecturer.objects.all()
    enrollments = Enrollment.objects.all()
    students = Student.objects.all()
    lecturers = Lecturer.objects.all()
    # Render the template with the quizzes, courses, and lecturers data
    return render(request, 'My_Admin/Quize/Add_Quiz.html', {
        'quizzes': quizzes,
        'courses': courses,
        'lecturers': lecturers,
        'students':students,
        'enrollments':enrollments
    })
    
# View for displaying all quizzes
def manage_quizzes(request):
    quizzes = Quiz.objects.all()
    enrollments = Enrollment.objects.all()
    students = Student.objects.all()
    lecturers = Lecturer.objects.all()
    return render(request, 'My_Admin/Quize/View_Quiz.html',
                   {'quizzes': quizzes,
                    'enrollments':enrollments,
                    'students':students,
                    'lecturers':lecturers})
                    
# View to search for a quiz based on its ID
def search_quiz(request):
    quiz_id = request.GET.get('quiz_id')
    try:
        quiz = Quiz.objects.get(id=quiz_id)
        return JsonResponse({
            'success': True,
            'title': quiz.title,
            'description': quiz.description,
            'instructor': quiz.instructor.lec_name,
            'due_date': quiz.due_date.strftime('%Y-%m-%d %H:%M'),
            'is_active': quiz.is_active,
            'time_limit': quiz.time_limit,
            'attempt_count': quiz.attempt_count
        })
    except Quiz.DoesNotExist:
        return JsonResponse({'success': False})
        
@csrf_exempt
def update_quiz(request):
    if request.method == 'POST':
        quiz_id = request.POST.get('quiz_id')
        title = request.POST.get('title').strip()
        description = request.POST.get('description').strip()
        instructor_name = request.POST.get('instructor').strip()
        due_date = request.POST.get('due_date')
        time_limit = request.POST.get('time_limit')
        attempt_count = request.POST.get('attempt_count')

        try:
            # Ensure instructor_id is valid (look for a Lecturer by the instructor name)
            instructor = Lecturer.objects.get(lec_name=instructor_name)

            quiz = Quiz.objects.get(id=quiz_id)
            quiz.title = title
            quiz.description = description
            quiz.instructor = instructor
            quiz.due_date = due_date
            quiz.time_limit = time_limit
            quiz.attempt_count = attempt_count
            quiz.save()

            return JsonResponse({'success': True})
        except Quiz.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Quiz not found.'})
        except Lecturer.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Instructor not found.'})
            
# View to delete a quiz
def delete_quiz(request, quiz_id):
    try:
        quiz = Quiz.objects.get(id=quiz_id)
        quiz.delete()
    except Quiz.DoesNotExist:
        messages.error(request, 'Quiz not found.')
    return redirect('manage_quizzes')  # Make sure 'View_Quizzes' is a valid URL name
    

def Add_Question(request):
    if request.method == 'POST':
        # Get data from the form
        question_text = request.POST.get('question_text')
        question_type = request.POST.get('question_type')
        option1 = request.POST.get('option1')
        option2 = request.POST.get('option2')
        option3 = request.POST.get('option3')
        option4 = request.POST.get('option4')
        answer = request.POST.get('answer')
        max_score = request.POST.get('max_score')
        quiz_id = request.POST.get('quiz')

        # Get the selected quiz
        quiz = Quiz.objects.get(id=quiz_id)

        # Create and save the new question
        Question.objects.create(
            quiz=quiz,
            question_text1=question_text,
            question_type1=question_type,
            option1=option1,
            option2=option2,
            option3=option3,
            option4=option4,
            answer=answer,
            max_score=max_score
        )

        # Display success message
        messages.success(request, "New question added successfully!")

        # Redirect to the same page to see the updated list of questions
        return redirect('Add_Question')

    # Get the list of questions to display
    questions = Question.objects.all()
    quiz = Quiz.objects.all()
    enrollments = Enrollment.objects.all()
    students = Student.objects.all()
    lecturers = Lecturer.objects.all()
    # Render the template with the questions
    return render(request, 'My_Admin/Question/Add_Question.html', 
                {'questions': questions, 
                 'quiz': quiz,
                 'enrollments':enrollments,
                 'students':students,
                 'lecturers':lecturers})
                 
# View to search for a question based on selected quiz
def search_question(request):
    if request.method == 'GET':
        quiz = request.GET.get('quiz')
        question_text = request.GET.get('question_text')

        # Filter questions based on both quiz and question_text
        try:
            question = Question.objects.get(quiz__title=quiz, question_text__icontains=question_text)
            response_data = {
                'success': True,
                'question_text': question.question_text1,
                'question_type': question.get_question_type_display(),
                'option1': question.option1,
                'option2': question.option2,
                'option3': question.option3,
                'option4': question.option4,
                'answer': question.answer,
                'max_score': question.max_score,
            }
        except Question.DoesNotExist:
            response_data = {
                'success': False,
                'message': 'No questions found matching the search criteria.'
            }
        return JsonResponse(response_data)

# View to update a question's details
@csrf_exempt
def update_question(request):
    if request.method == 'POST':
        question_id = request.POST.get('question_id')
        question_text = request.POST.get('question_text')
        question_type = request.POST.get('question_type')
        option1 = request.POST.get('option1')
        option2 = request.POST.get('option2')
        option3 = request.POST.get('option3')
        option4 = request.POST.get('option4')
        answer = request.POST.get('answer')
        max_score = request.POST.get('max_score')

        # Validate input
        if not question_id or not question_text or not question_type or not option1 or not option2 or not option3 or not option4 or not answer or not max_score:
            return JsonResponse({'success': False, 'message': 'All fields must be filled out!'})

        # Get the question to update
        question = get_object_or_404(Question, id=question_id)
        
        # Update question fields
        question.question_text1 = question_text
        question.question_type1 = question_type
        question.option1 = option1
        question.option2 = option2
        question.option3 = option3
        question.option4 = option4
        question.answer = answer
        question.max_score = max_score
        question.save()
        return JsonResponse({'success': True, 'message': 'Question updated successfully!'})
# View to delete a question
def delete_question(request, question_id):
    question = get_object_or_404(Question, id=question_id)
    question.delete()
    return redirect('Add_Question')  # Redirect to the question management page
    
def Add_Answer(request):
    selected_quiz_title = request.GET.get('quiz')
    quizzes = Quiz.objects.all()
    students = Student.objects.all()
    my_answer=Answer.objects.all()
    questions = []

    if selected_quiz_title:
        questions = Question.objects.filter(quiz__title=selected_quiz_title)

    # Handle POST submission
    if request.method == 'POST':
        student_id = request.POST.get('student')
        submitted_answer = request.POST.get('submitted_answer')
        score = request.POST.get('score')  # readonly but passed
        feedback = request.POST.get('feedback')

        if not student_id or not submitted_answer:
            messages.error(request, "Student and submitted answer are required.")
            return redirect(request.path_info + f"?quiz={selected_quiz_title}")

        student = get_object_or_404(Student, pk=student_id)

        Answer.objects.create(
            student=student,
            submitted_answer=submitted_answer,
            score=int(score) if score else None,
            feedback=feedback
        )

        messages.success(request, "Answer submitted successfully.")
        return redirect(request.path_info + f"?quiz={selected_quiz_title}")
    enrollments = Enrollment.objects.all()
    students = Student.objects.all()
    lecturers = Lecturer.objects.all()
    context = {
        'quizzes': quizzes,
        'students': students,
        'questions': questions,
        'selected_quiz_title': selected_quiz_title,
        'my_answer':my_answer,
        'lecturers':lecturers,
        'enrollments':enrollments
    }

    return render(request, 'My_Admin/StudentAnswer/Add_Answer.html', context)
    
def download_answer(request, answer_id):
    try:
        answer = Answer.objects.get(pk=answer_id)
        content = f"Answer ID: {answer.id}\nSubmitted Answer: {answer.submitted_answer}\nScore: {answer.score}\nDate: {answer.submitted_at}\nFeedback: {answer.feedback}"
        response = HttpResponse(content, content_type='text/plain')
        response['Content-Disposition'] = f'attachment; filename=Answer_{answer.id}.txt'
        return response
    except Answer.DoesNotExist:
        return HttpResponse("Answer not found.", status=404)
        
# View to delete an answer
def delete_answer(request, answer_id):
    answer = get_object_or_404(Answer, id=answer_id)
    answer.delete()
    return redirect('Add_Answer')  # Redirect to the page managing answers
    

def add_academic_session(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        active = request.POST.get('active') == 'on'  # Checkbox returns 'on' if checked
        # If active is True, deactivate all other sessions
        if active:
            AcademicSession.objects.update(active=False)
        AcademicSession.objects.create(
            name=name,
            start_date=start_date,
            end_date=end_date,
            active=active
        )
        messages.success(request, "Academic Session added successfully!")
        return redirect('Add_AcademicSession')
    # If GET request
    sessions = AcademicSession.objects.all().order_by('-start_date')
    enrollments = Enrollment.objects.all()
    students = Student.objects.all()
    lecturers = Lecturer.objects.all()
    return render(request, 'My_Admin/AcdemicSession/Add_Acdemic.html', 
                  {'sessions': sessions,
                   'students':students,
                   'lecturers':lecturers,
                   'enrollments':enrollments})
                   
# View to display the manage session page
def view_sessions(request):
    sessions = AcademicSession.objects.all().order_by('-id')
    enrollments = Enrollment.objects.all()
    students = Student.objects.all()
    lecturers = Lecturer.objects.all()
    return render(request, 'My_Admin/AcdemicSession/View_Acdemic.html',
                   {'sessions': sessions,
                    'enrollments':enrollments,
                    'students':students,
                    'lecturers':lecturers})
                    
# AJAX: Search session by ID
def search_session(request):
    session_id = request.GET.get('session_id')
    try:
        session = AcademicSession.objects.get(id=session_id)
        return JsonResponse({
            'success': True,
            'name': session.name,
            'start_date': session.start_date.strftime('%Y-%m-%d'),
            'end_date': session.end_date.strftime('%Y-%m-%d'),
            'active': session.active
        })
    except AcademicSession.DoesNotExist:
        return JsonResponse({'success': False})

# AJAX: Update session details
@csrf_exempt
@require_http_methods(["POST"])
def update_session(request):
    session_id = request.POST.get('session_id')
    name = request.POST.get('name')
    start_date = request.POST.get('start_date')
    end_date = request.POST.get('end_date')
    active = request.POST.get('active') == 'true'

    try:
        session = AcademicSession.objects.get(id=session_id)
        session.name = name
        session.start_date = start_date
        session.end_date = end_date
        session.active = active
        session.save()
        return JsonResponse({'success': True})
    except AcademicSession.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Session not found.'})

# Delete session
def delete_session(request, session_id):
    session = get_object_or_404(AcademicSession, id=session_id)
    session.delete()
    return redirect('view_sessions')
    

def Add_Semester(request):
    if request.method == 'POST':
        name = request.POST['name']
        academic_session = AcademicSession.objects.get(id=request.POST['academic_session_id'])
        start_date = request.POST['start_date']
        end_date = request.POST['end_date']
        Semester.objects.create(
            name=name,
            academic_session=academic_session,
            start_date=start_date,
            end_date=end_date
        )
        messages.success(request, 'Semester added successfully!')
        return redirect('Add_Semester')
    semesters=Semester.objects.all()
    enrollments = Enrollment.objects.all()
    students = Student.objects.all()
    lecturers = Lecturer.objects.all()
    academic_sessions = AcademicSession.objects.all()
    return render(request, 'My_Admin/Semester/Add_Semester.html', 
                  {'academic_sessions': academic_sessions,
                   'semesters':semesters,
                   'students':students,
                   'lecturers':lecturers,
                   'enrollments':enrollments})
                   
def manage_semesters(request):
    semesters = Semester.objects.select_related('academic_session').all()
    academic_sessions = AcademicSession.objects.all()
    enrollments = Enrollment.objects.all()
    students = Student.objects.all()
    lecturers = Lecturer.objects.all()
    return render(request, 'My_Admin/Semester/View_Semester.html', {
        'semesters': semesters,
        'academic_sessions': academic_sessions,
        'enrollments':enrollments,
        'students':students,
        'lecturers':lecturers
    })
    
# Search Semester View
def search_semester(request):
    semester_name = request.GET.get('semester')  # Get the semester name from the URL query string
    try:
        semester = Semester.objects.get(name=semester_name)  # Find the semester by name
        return JsonResponse({
            'success': True,
            'name': semester.name,
            'academic_session': semester.academic_session.id,
            'start_date': semester.start_date.strftime('%Y-%m-%d'),
            'end_date': semester.end_date.strftime('%Y-%m-%d'),
        })
    except Semester.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Semester not found'})
        
@csrf_exempt
def update_semester(request):
    if request.method == 'POST':
        semester_id = request.POST.get('semester_id')
        name = request.POST.get('name')
        academic_session_id = request.POST.get('academic_session')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')

        try:
            # Fetch the corresponding semester using the semester_id
            semester = Semester.objects.get(id=semester_id)
            
            # Get the academic session based on the provided ID
            academic_session = AcademicSession.objects.get(id=academic_session_id)
            
            # Update the semester fields
            semester.name = name
            semester.academic_session = academic_session
            semester.start_date = start_date
            semester.end_date = end_date
            semester.save()  # Save the updated semester data

            return JsonResponse({'success': True})

        except Semester.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Semester not found.'})
        except AcademicSession.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Academic session not found.'})
            
def delete_semester(request, semester_id):
    semester = get_object_or_404(Semester, id=semester_id)
    semester.delete()
    return redirect('manage_semester')
    

def Add_Notifications(request):
    if request.method == 'POST':
        user_id = request.POST['user']
        message = request.POST['message']
        notification_type = request.POST['notification_type']
        attachment = request.FILES.get('attachment')
        user = User.objects.get(id=user_id)
        Notification.objects.create(
            user=user,
            message=message,
            notification_type=notification_type,
            attachment=attachment
        )
        messages.success(request, "Notification added successfully!")
    notifications = Notification.objects.all().order_by('-created_at')
    users = User.objects.all()
    enrollments = Enrollment.objects.all()
    students = Student.objects.all()
    lecturers = Lecturer.objects.all()
    return render(request, 'My_Admin/Notification/Add_Notification.html', {
        'notifications': notifications,
        'users': users,
        'enrollments':enrollments,
        'lecturers':lecturers,
        'students':students
    })
    
@login_required
def manage_notifications(request):
    notifications = Notification.objects.all().order_by('-created_at')
    enrollments = Enrollment.objects.all()
    students = Student.objects.all()
    lecturers = Lecturer.objects.all()
    return render(request, 'My_Admin/Notification/View_Notification.html', {
        'notifications': notifications,
        'users': User.objects.all(),
        'enrollments':enrollments,
        'students':students,
        'lecturers':lecturers
    })

@require_GET
@login_required
def search_notification(request):
    notification_id = request.GET.get('notification_id')
    try:
        notification = Notification.objects.get(id=notification_id)
        return JsonResponse({
            'success': True,
            'user_id': notification.user.id,
            'message': notification.message,
            'notification_type': notification.notification_type,
            'read': notification.read,
            'attachment_url': notification.attachment.url if notification.attachment else ''
        })
    except Notification.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Notification not found'})

@require_POST
@login_required
def update_notification(request):
    notification_id = request.POST.get('notification_id')
    try:
        notification = Notification.objects.get(id=notification_id)
        user_id = request.POST.get('user_id')
        user = get_object_or_404(User, id=user_id)

        notification.user = user
        notification.message = request.POST.get('message')
        notification.notification_type = request.POST.get('notification_type')
        notification.read = request.POST.get('read') == 'true'

        # Optional: handle file update if needed (e.g. via AJAX with FormData)
        # file = request.FILES.get('attachment')
        # if file:
        #     notification.attachment = file

        notification.save()
        return JsonResponse({'success': True})
    except Notification.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Notification not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})
        
def delete_notification(request, not_id):
    my_notification=get_object_or_404(Notification, id=not_id)
    my_notification.delete()
    return redirect('view_notifications')
    

def Submit_Answer(request):
    selected_quiz_title = request.GET.get('quiz')
    from_func = request.GET.get('from_func')  # Get the function name if passed
    quizzes = Quiz.objects.all()
    students = Student.objects.all()
    my_answer = Answer.objects.all()
    questions = []
    if selected_quiz_title:
        questions = Question.objects.filter(quiz__title=selected_quiz_title)
    # Handle POST submission
    if request.method == 'POST':
        student_id = request.POST.get('student')
        submitted_answer = request.POST.get('submitted_answer')
        score = request.POST.get('score')  # readonly but passed
        feedback = request.POST.get('feedback')
        if not student_id or not submitted_answer:
            messages.error(request, "Student and submitted answer are required.")
            return redirect(request.path_info + f"?quiz={selected_quiz_title}&from_func=Submit_Answer")
        student = get_object_or_404(Student, pk=student_id)
        Answer.objects.create(
            student=student,
            submitted_answer=submitted_answer,
            score=int(score) if score else None,
            feedback=feedback
        )
        messages.success(request, "Answer submitted successfully.")
        return redirect(request.path_info + f"?quiz={selected_quiz_title}&from_func=Submit_Answer")
    enrollments = Enrollment.objects.all()
    students = Student.objects.all()
    lecturers = Lecturer.objects.all()
    context = {
        'quizzes': quizzes,
        'students': students,
        'questions': questions,
        'selected_quiz_title': selected_quiz_title,
        'my_answer': my_answer,
        'from_func': from_func,
        'enrollments':enrollments,
        'lecturers':lecturers
    }
    return render(request, 'My_Admin/Student/Submit_Answer.html', context)
    

def manage_submissions(request):
    # Fetch all students and assessments for the form dropdowns
    students = Student.objects.all()
    assessments = Assessment.objects.all()
    # Handle form submission for adding a new submission
    if request.method == 'POST':
        try:
            # Get data from the form
            student_id = request.POST.get('student')
            assessment_id = request.POST.get('assessment')
            score = request.POST.get('score')
            attachment = request.FILES.get('attachment')

            # Fetch the student and assessment instances
            student = Student.objects.get(id=student_id)
            assessment = Assessment.objects.get(id=assessment_id)

            # Create a new Submission instance
            submission = Submission(
                student=student,
                assessment=assessment,
                score=score,
                attachment=attachment if attachment else None
            )
            submission.save()

            # Send success message
            messages.success(request, "Submission added successfully!")
            return redirect('add_submission')
        
        except ValidationError as e:
            messages.error(request, f"Error: {e}")
        except Exception as e:
            messages.error(request, f"An error occurred: {e}")
    
    # Get all submissions to display in the table
    submissions = Submission.objects.all()
    enrollments = Enrollment.objects.all()
    students = Student.objects.all()
    lecturers = Lecturer.objects.all()
    # Render the template with the necessary context
    return render(request, 'My_Admin/StudentSubmission/Add_Submission.html', {
        'students': students,
        'assessments': assessments,
        'submissions': submissions,
        'enrollments':enrollments,
        'lecturers':lecturers
    })
    
# View to manage submissions
def manage_submissions1(request):
    students = Student.objects.all()
    assessments = Assessment.objects.all()
    submissions = Submission.objects.all()

    if request.method == 'POST':
        student_id = request.POST.get('student')
        assessment_id = request.POST.get('assessment')
        score = request.POST.get('score')
        submitted_on = request.POST.get('submitted_on')
        attachment = request.FILES.get('attachment')

        # Creating or updating a submission
        if student_id and assessment_id and score and submitted_on:
            student = Student.objects.get(id=student_id)
            assessment = Assessment.objects.get(id=assessment_id)
            
            # Check if the submission already exists for the student and assessment
            submission = Submission.objects.filter(student=student, assessment=assessment).first()

            if not submission:
                submission = Submission(
                    student=student,
                    assessment=assessment,
                    score=score,
                    submitted_on=submitted_on,
                    attachment=attachment
                )
            else:
                submission.score = score
                submission.submitted_on = submitted_on
                submission.attachment = attachment

            submission.save()

            return redirect('manage_submissions1')  # Refresh the page after saving the data
    enrollments = Enrollment.objects.all()
    students = Student.objects.all()
    lecturers = Lecturer.objects.all()
    return render(request, 'My_Admin/StudentSubmission/View_Submission.html', {
        'students': students,
        'assessments': assessments,
        'submissions': submissions,
        'enrollments':enrollments,
        'lecturers':lecturers
    })
    
def search_submission(request):
    student_id = request.GET.get('student_id')
    assessment_id = request.GET.get('assessment_id')

    # Ensure both student_id and assessment_id are provided
    if not student_id or not assessment_id:
        return JsonResponse({
            'success': False,
            'message': 'Both student and assessment must be selected'
        })

    try:
        submission = Submission.objects.get(student_id=student_id, assessment_id=assessment_id)
        return JsonResponse({
            'success': True,
            'score': submission.score,
            'submitted_on': submission.submitted_on.strftime('%Y-%m-%dT%H:%M'),  # Ensure proper datetime format
            'attachment': submission.attachment.url if submission.attachment else ''
        })
    except ObjectDoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Submission not found'
        })
        
# View for deleting a submission
def delete_submission(request, submission_id):
    try:
        submission = Submission.objects.get(id=submission_id)
        submission.delete()
        return redirect('manage_submissions')  # After deletion, redirect to the same page
    except ObjectDoesNotExist:
        return redirect('manage_submissions')  # Redirect if submission is not found
        
# Role Constants (Define these appropriately or import from constants)
ADMIN = 'admin'
LECTURER = 'lecturer'
STUDENT = 'student'

def View_role_wise_user(request):
    """
    View for the admin dashboard that groups users by specific roles
    (Admin, Lecturer, Student) and passes the data to the template.
    """
    role_to_group = {
        ADMIN: {'group_name': 'Admin', 'is_superuser': True, 'is_staff': True},
        LECTURER: {'group_name': 'Lecturer', 'is_superuser': False, 'is_staff': True},
        STUDENT: {'group_name': 'Student', 'is_superuser': False, 'is_staff': False},
    }

    grouped_users = {}

    for role_key, role_info in role_to_group.items():
        group = Group.objects.filter(name=role_info['group_name']).first()
        if group:
            grouped_users[role_info['group_name']] = User.objects.filter(groups=group)
        else:
            grouped_users[role_info['group_name']] = []

    # Users with no group assigned
    grouped_users["No Role Assigned"] = User.objects.filter(groups=None)

    enrollments = Enrollment.objects.all()
    students = Student.objects.all()
    lecturers = Lecturer.objects.all()

    return render(
        request,
        'My_Admin/User/View_All_Role_Wise.html',
        {
            'grouped_users': grouped_users,
            'enrollments':enrollments,
            'lecturers':lecturers,
            'students':students
        }
    )
    

@login_required
def student_dashboard(request):
    st1_group = Group.objects.get(name="Student")  # Get the Marketing Manager group
    users = User.objects.filter(groups=st1_group)
    enrollments = Enrollment.objects.all()
    students = Student.objects.all()
    lecturers = Lecturer.objects.all()
    context = {
        'users': users,
        'enrollments': enrollments,
        'students': students,
        'lecturers': lecturers,
        'total_students': students.count(),
        'total_enrollments': enrollments.count(),
        'total_lecturers': lecturers.count(),
    }
    return render(request, 'Student/My_Student.html', context)
    
def StudentAdd_Student(request):
    if request.method == "POST":
        student_id = request.POST.get("student_id")
        student_name = request.POST.get("student_name")
        student_rollno = request.POST.get("student_rollno")
        student_course_id = request.POST.get("student_course")
        class_room_id = request.POST.get("class_room")

        try:
            student_course = Course.objects.get(title=student_course_id)
            class_room = ClassRoom.objects.get(room_number=class_room_id)
            Student.objects.create(
                student_id=student_id,
                student_name=student_name,
                student_rollno=student_rollno,
                student_course=student_course,
                class_room=class_room,
            )
            messages.success(request, "Student added successfully!")
        except Course.DoesNotExist:
            messages.error(request, "Selected course does not exist!")
        except ClassRoom.DoesNotExist:
            messages.error(request, "Selected classroom does not exist!")
        except Exception as e:
            messages.error(request, f"Error adding student: {str(e)}")

        return redirect("StudentAdd_Student")

    students = Student.objects.select_related("student_course", "class_room").all()
    courses = Course.objects.all()
    class_rooms = ClassRoom.objects.all()
    enrollments = Enrollment.objects.all()
    students = Student.objects.all()
    lecturers = Lecturer.objects.all()
    return render(request, "Student/Student/Add_Student.html", {
        "students": students,
        "courses": courses,
        "class_rooms": class_rooms,
        'lecturers':lecturers,
        'enrollments':enrollments
    })
    
def Studentmanage_students(request):
    students = Student.objects.all()
    courses = Course.objects.all()
    classrooms = ClassRoom.objects.all()
    enrollments = Enrollment.objects.all()
    students = Student.objects.all()
    lecturers = Lecturer.objects.all()
    return render(request, 'Student/Student/View_Student.html', 
                  {'students': students,
                    'courses': courses,
                      'classrooms': classrooms,
                      'enrollments':enrollments,
                      'lecturers':lecturers})
                      
def StudentSubmit_Answer(request):
    selected_quiz_title = request.GET.get('quiz')
    from_func = request.GET.get('from_func')  # Get the function name if passed
    quizzes = Quiz.objects.all()
    students = Student.objects.all()
    my_answer = Answer.objects.all()
    questions = []
    if selected_quiz_title:
        questions = Question.objects.filter(quiz__title=selected_quiz_title)
    # Handle POST submission
    if request.method == 'POST':
        student_id = request.POST.get('student')
        submitted_answer = request.POST.get('submitted_answer')
        score = request.POST.get('score')  # readonly but passed
        feedback = request.POST.get('feedback')
        if not student_id or not submitted_answer:
            messages.error(request, "Student and submitted answer are required.")
            return redirect(request.path_info + f"?quiz={selected_quiz_title}&from_func=StudentSubmit_Answer")
        student = get_object_or_404(Student, pk=student_id)
        Answer.objects.create(
            student=student,
            submitted_answer=submitted_answer,
            score=int(score) if score else None,
            feedback=feedback
        )
        messages.success(request, "Answer submitted successfully.")
        return redirect(request.path_info + f"?quiz={selected_quiz_title}&from_func=StudentSubmit_Answer")
    enrollments = Enrollment.objects.all()
    students = Student.objects.all()
    lecturers = Lecturer.objects.all()
    context = {
        'quizzes': quizzes,
        'students': students,
        'questions': questions,
        'selected_quiz_title': selected_quiz_title,
        'my_answer': my_answer,
        'from_func': from_func,
        'enrollments':enrollments,
        'lecturers':lecturers
    }
    return render(request, 'Student/Student/Submit_Answer.html', context)
    
def Studentmanage_submissions(request):
    # Fetch all students and assessments for the form dropdowns
    students = Student.objects.all()
    assessments = Assessment.objects.all()
    # Handle form submission for adding a new submission
    if request.method == 'POST':
        try:
            # Get data from the form
            student_id = request.POST.get('student')
            assessment_id = request.POST.get('assessment')
            score = request.POST.get('score')
            attachment = request.FILES.get('attachment')

            # Fetch the student and assessment instances
            student = Student.objects.get(id=student_id)
            assessment = Assessment.objects.get(id=assessment_id)

            # Create a new Submission instance
            submission = Submission(
                student=student,
                assessment=assessment,
                score=score,
                attachment=attachment if attachment else None
            )
            submission.save()

            # Send success message
            messages.success(request, "Submission added successfully!")
            return redirect('Studentmanage_submissions')
        
        except ValidationError as e:
            messages.error(request, f"Error: {e}")
        except Exception as e:
            messages.error(request, f"An error occurred: {e}")
    
    # Get all submissions to display in the table
    submissions = Submission.objects.all()
    enrollments = Enrollment.objects.all()
    students = Student.objects.all()
    lecturers = Lecturer.objects.all()
    # Render the template with the necessary context
    return render(request, 'Student/StudentSubmission/Add_Submission.html', {
        'students': students,
        'assessments': assessments,
        'submissions': submissions,
        'enrollments':enrollments,
        'lecturers':lecturers
    })
    
def Studentadd_enrollments(request):
    if request.method == "POST":
        student_id = request.POST.get('student')
        course_id = request.POST.get('course')
        progress = request.POST.get('progress', 0)

        student = Student.objects.get(id=student_id)
        course = Course.objects.get(id=course_id)

        if Enrollment.objects.filter(student=student, course=course).exists():
            messages.error(request, "This student is already enrolled in the selected course.")
        else:
            Enrollment.objects.create(student=student, course=course, progress=progress)
            messages.success(request, "Enrollment added successfully!")

        return redirect('Studentadd_enrollments')

    students = Student.objects.all()
    courses = Course.objects.all()
    enrollments = Enrollment.objects.all()
    students = Student.objects.all()
    lecturers = Lecturer.objects.all()
    enrollments = Enrollment.objects.select_related('student', 'course').all()

    context = {
        'students': students,
        'courses': courses,
        'enrollments': enrollments,
        'lecturers':lecturers
    }
    return render(request, 'Student/Enrollement/Add_Enrollment.html', context)
    

def Studentmanage_enrollments(request):
    students = Student.objects.all()
    courses = Course.objects.all()
    enrollments = Enrollment.objects.all()
    students = Student.objects.all()
    lecturers = Lecturer.objects.all()
    enrollments = Enrollment.objects.select_related('student', 'course').all()

    # Enrollment progress summary (Completed, Ongoing, Pending)
    completed_courses = Enrollment.objects.filter(progress=100).count()
    ongoing_courses = Enrollment.objects.filter(progress__gt=0, progress__lt=100).count()  # Corrected line
    pending_courses = Enrollment.objects.filter(progress=0).count()

    return render(request, 'Student/Enrollement/View_Enrollement.html', {
        'students': students,
        'courses': courses,
        'enrollments': enrollments,
        'completed_courses': completed_courses,
        'ongoing_courses': ongoing_courses,
        'pending_courses': pending_courses,
        'lecturers':lecturers
    })
    
@login_required
def studentmanage_notifications(request):
    notifications = Notification.objects.all().order_by('-created_at')
    enrollments = Enrollment.objects.all()
    students = Student.objects.all()
    lecturers = Lecturer.objects.all()
    return render(request, 'Student/Notification/View_Notification.html', {
        'notifications': notifications,
        'users': User.objects.all(),
        'enrollments':enrollments,
        'students':students,
        'lecturers':lecturers
    })
    
# View to list all payments
def studentview_payments(request):
    payments = Payment.objects.all()
    enrollments = Enrollment.objects.all()
    students = Student.objects.all()
    lecturers = Lecturer.objects.all()
    return render(request, 'Student/Payment/View_Payment.html',
                   {'payments': payments,
                     'courses': Course.objects.all(),
                     'enrollments':enrollments,
                     'students':students,
                     'lecturers':lecturers
                     
                     })
                     

#############(For Lecturer Dashboard)#################
@login_required
def lecturer_dashboard(request):
    st1_group = Group.objects.get(name="Lecturer")  # Get the Marketing Manager group
    users = User.objects.filter(groups=st1_group)
    enrollments = Enrollment.objects.all()
    students = Student.objects.all()
    lecturers = Lecturer.objects.all()
    context = {
        'users': users,
        'enrollments': enrollments,
        'students': students,
        'lecturers': lecturers,
        'total_students': students.count(),
        'total_enrollments': enrollments.count(),
        'total_lecturers': lecturers.count(),
    }
    return render(request, 'Lecturer/My_Lecturer.html', context)
    
def LecturerAdd_Notifications(request):
    if request.method == 'POST':
        user_id = request.POST['user']
        message = request.POST['message']
        notification_type = request.POST['notification_type']
        attachment = request.FILES.get('attachment')
        user = User.objects.get(id=user_id)
        Notification.objects.create(
            user=user,
            message=message,
            notification_type=notification_type,
            attachment=attachment
        )
        messages.success(request, "Notification added successfully!")
    notifications = Notification.objects.all().order_by('-created_at')
    users = User.objects.all()
    enrollments = Enrollment.objects.all()
    students = Student.objects.all()
    lecturers = Lecturer.objects.all()
    return render(request, 'Lecturer/Notification/Add_Notification.html', {
        'notifications': notifications,
        'users': users,
        'enrollments':enrollments,
        'lecturers':lecturers,
        'students':students
    })
    
def LecturerAdd_Courses(request):
    """View to display courses and handle course creation."""
    if request.method == "POST":
        title = request.POST.get('title')
        description = request.POST.get('description')
        instructor_id = request.POST.get('instructor')
        price = request.POST.get('price')
        prerequisites = request.POST.getlist('prerequisites')

        if not title or not description or not instructor_id or not price:
            messages.error(request, "All fields are required.")
            return redirect('LecturerAdd_Courses')

        try:
            price = Decimal(price)
        except ValueError:
            messages.error(request, "Invalid price format.")
            return redirect('LecturerAdd_Courses')

        instructor = get_object_or_404(Lecturer, id=instructor_id)

        course = Course.objects.create(
            title=title,
            description=description,
            instructor=instructor,
            price=price
        )

        # Assign prerequisites if valid course IDs are provided
        if prerequisites:
            valid_courses = Course.objects.filter(id__in=prerequisites)
            course.prerequisites.set(valid_courses)

        messages.success(request, "Course added successfully!")
        return redirect('LecturerAdd_Courses')

    courses = Course.objects.all().order_by('-created_at')
    instructors = Lecturer.objects.all()
    enrollments = Enrollment.objects.all()
    students = Student.objects.all()
    lecturers = Lecturer.objects.all()

    return render(request, 'Lecturer/Course/Add_Course.html', {
        'courses': courses,
        'instructors': instructors,
        'enrollments':enrollments,
        'students':students,
        'lecturers':lecturers
    })
    
def LecturerAdd_Question(request):
    if request.method == 'POST':
        # Get data from the form
        question_text = request.POST.get('question_text')
        question_type = request.POST.get('question_type')
        option1 = request.POST.get('option1')
        option2 = request.POST.get('option2')
        option3 = request.POST.get('option3')
        option4 = request.POST.get('option4')
        answer = request.POST.get('answer')
        max_score = request.POST.get('max_score')
        quiz_id = request.POST.get('quiz')

        # Get the selected quiz
        quiz = Quiz.objects.get(id=quiz_id)

        # Create and save the new question
        Question.objects.create(
            quiz=quiz,
            question_text1=question_text,
            question_type1=question_type,
            option1=option1,
            option2=option2,
            option3=option3,
            option4=option4,
            answer=answer,
            max_score=max_score
        )

        # Display success message
        messages.success(request, "New question added successfully!")

        # Redirect to the same page to see the updated list of questions
        return redirect('LecturerAdd_Question')

    # Get the list of questions to display
    questions = Question.objects.all()
    quiz = Quiz.objects.all()
    enrollments = Enrollment.objects.all()
    students = Student.objects.all()
    lecturers = Lecturer.objects.all()
    # Render the template with the questions
    return render(request, 'Lecturer/Question/Add_Question.html', 
                {'questions': questions, 
                 'quiz': quiz,
                 'enrollments':enrollments,
                 'students':students,
                 'lecturers':lecturers})
                 
def Lectureradd_quiz(request):
    if request.method == "POST":
        # Get form data from the POST request
        course_id = request.POST.get('course')
        title = request.POST.get('title')
        description = request.POST.get('description')
        instructor_id = request.POST.get('instructor')
        due_date = request.POST.get('due_date')
        time_limit = request.POST.get('time_limit')
        attempt_count = request.POST.get('attempt_count')

        # Check if course_id or instructor_id is empty
        if not course_id or not instructor_id:
            messages.error(request, "Please select both a course and an instructor.")
            return redirect('Lectureradd_quiz')

        try:
            # Get the Course and Lecturer objects based on the selected IDs
            course = Course.objects.get(id=course_id)
            instructor = Lecturer.objects.get(id=instructor_id)

            # Create and save a new Quiz
            quiz = Quiz(
                course=course,
                title=title,
                description=description,
                instructor=instructor,
                due_date=due_date,
                time_limit=time_limit,
                attempt_count=attempt_count
            )
            quiz.save()
            messages.success(request, "Quiz successfully added!")
        except Exception as e:
            messages.error(request, f"Error adding quiz: {e}")
        
        # Redirect back to the same page after form submission
        return redirect('Lectureradd_quiz')

    # Get existing quizzes and other necessary data
    quizzes = Quiz.objects.all()
    courses = Course.objects.all()
    lecturers = Lecturer.objects.all()
    enrollments = Enrollment.objects.all()
    students = Student.objects.all()
    lecturers = Lecturer.objects.all()
    # Render the template with the quizzes, courses, and lecturers data
    return render(request, 'Lecturer/Quize/Add_Quiz.html', {
        'quizzes': quizzes,
        'courses': courses,
        'lecturers': lecturers,
        'students':students,
        'enrollments':enrollments
    })
    
# Add Assessment View
def Lectureradd_assessment(request):
    if request.method == 'POST':
        # Get the form data
        course_id = request.POST.get('course')
        title = request.POST.get('title')
        description = request.POST.get('description')
        max_score = request.POST.get('max_score')
        due_date = request.POST.get('due_date')
        attachment = request.FILES.get('attachment')
        # Create a new Assessment object
        assessment = Assessment(
            course_id=course_id,
            title=title,
            description=description,
            max_score=max_score,
            due_date=due_date,
            attachment=attachment
        )
        try:
            assessment.save()  # Save the assessment to the database
            messages.success(request, "Assessment added successfully.")
            return redirect('Lectureradd_assessment')  # Redirect to the same page to display the updated list
        except Exception as e:
            messages.error(request, f"Error adding assessment: {e}")
            return redirect('Lectureradd_assessment')  # Redirect to the same page on error
    # If the request method is GET, render the form
    courses = Course.objects.all()  # Get all available courses for the dropdown
    assessments = Assessment.objects.all()  # Get all assessments to display in the table
    enrollments = Enrollment.objects.all()
    students = Student.objects.all()
    lecturers = Lecturer.objects.all()
    context = {
        'courses': courses,
        'assessments': assessments,
        'students':students,
        'enrollments':enrollments,
        'lecturers':lecturers
    }
    return render(request, 'Lecturer/Assessment/Add_Assessment.html', context)
    
# View to manage submissions
def Lecturermanage_submissions1(request):
    students = Student.objects.all()
    assessments = Assessment.objects.all()
    submissions = Submission.objects.all()

    if request.method == 'POST':
        student_id = request.POST.get('student')
        assessment_id = request.POST.get('assessment')
        score = request.POST.get('score')
        submitted_on = request.POST.get('submitted_on')
        attachment = request.FILES.get('attachment')

        # Creating or updating a submission
        if student_id and assessment_id and score and submitted_on:
            student = Student.objects.get(id=student_id)
            assessment = Assessment.objects.get(id=assessment_id)
            
            # Check if the submission already exists for the student and assessment
            submission = Submission.objects.filter(student=student, assessment=assessment).first()

            if not submission:
                submission = Submission(
                    student=student,
                    assessment=assessment,
                    score=score,
                    submitted_on=submitted_on,
                    attachment=attachment
                )
            else:
                submission.score = score
                submission.submitted_on = submitted_on
                submission.attachment = attachment

            submission.save()

            return redirect('Lecturermanage_submissions1')  # Refresh the page after saving the data
    enrollments = Enrollment.objects.all()
    students = Student.objects.all()
    lecturers = Lecturer.objects.all()
    return render(request, 'Lecturer/StudentSubmission/View_Submission.html', {
        'students': students,
        'assessments': assessments,
        'submissions': submissions,
        'enrollments':enrollments,
        'lecturers':lecturers
    })
    
def LecturerAdd_Student(request):
    if request.method == "POST":
        student_id = request.POST.get("student_id")
        student_name = request.POST.get("student_name")
        student_rollno = request.POST.get("student_rollno")
        student_course_id = request.POST.get("student_course")
        class_room_id = request.POST.get("class_room")

        try:
            student_course = Course.objects.get(title=student_course_id)
            class_room = ClassRoom.objects.get(room_number=class_room_id)
            Student.objects.create(
                student_id=student_id,
                student_name=student_name,
                student_rollno=student_rollno,
                student_course=student_course,
                class_room=class_room,
            )
            messages.success(request, "Student added successfully!")
        except Course.DoesNotExist:
            messages.error(request, "Selected course does not exist!")
        except ClassRoom.DoesNotExist:
            messages.error(request, "Selected classroom does not exist!")
        except Exception as e:
            messages.error(request, f"Error adding student: {str(e)}")

        return redirect("LecturerAdd_Student")

    students = Student.objects.select_related("student_course", "class_room").all()
    courses = Course.objects.all()
    class_rooms = ClassRoom.objects.all()
    enrollments = Enrollment.objects.all()
    students = Student.objects.all()
    lecturers = Lecturer.objects.all()
    return render(request, "Lecturer/Student/Add_Student.html", {
        "students": students,
        "courses": courses,
        "class_rooms": class_rooms,
        'lecturers':lecturers,
        'enrollments':enrollments
    })
    
def LecturerAdd_Answer(request):
    selected_quiz_title = request.GET.get('quiz')
    quizzes = Quiz.objects.all()
    students = Student.objects.all()
    my_answer=Answer.objects.all()
    questions = []

    if selected_quiz_title:
        questions = Question.objects.filter(quiz__title=selected_quiz_title)

    # Handle POST submission
    if request.method == 'POST':
        student_id = request.POST.get('student')
        submitted_answer = request.POST.get('submitted_answer')
        score = request.POST.get('score')  # readonly but passed
        feedback = request.POST.get('feedback')

        if not student_id or not submitted_answer:
            messages.error(request, "Student and submitted answer are required.")
            return redirect(request.path_info + f"?quiz={selected_quiz_title}")

        student = get_object_or_404(Student, pk=student_id)

        Answer.objects.create(
            student=student,
            submitted_answer=submitted_answer,
            score=int(score) if score else None,
            feedback=feedback
        )

        messages.success(request, "Answer submitted successfully.")
        return redirect(request.path_info + f"?quiz={selected_quiz_title}")
    enrollments = Enrollment.objects.all()
    students = Student.objects.all()
    lecturers = Lecturer.objects.all()
    context = {
        'quizzes': quizzes,
        'students': students,
        'questions': questions,
        'selected_quiz_title': selected_quiz_title,
        'my_answer':my_answer,
        'lecturers':lecturers,
        'enrollments':enrollments
    }

    return render(request, 'Lecturer/StudentAnswer/Add_Answer.html', context)
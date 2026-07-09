from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .forms import CustomUserCreationForm, LoginForm, CustomUserChangeForm, CourseForm
from .models import User, Course, Enrollment, DiscussionPost
from django.http import Http404
from django.db.models import Q


def home(request):
    """Home page"""
    return JsonResponse({
        'message': 'Welcome to E-Learning Platform!',
        'status': 'success',
    })


def hello(request, name='World'):
    """Hello endpoint"""
    return JsonResponse({
        'message': f'Hello, {name}!',
    })


def signup(request):
    """User registration view"""
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Log user in after signup
            login(request, user)
            messages.success(request, f'Account created successfully! Welcome {user.username}')
            return redirect('dashboard')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = CustomUserCreationForm()
    
    context = {'form': form}
    return render(request, 'main/signup.html', context)


def login_view(request):
    """User login view"""
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back {user.username}!')
                return redirect('dashboard')
            else:
                messages.error(request, 'Invalid username or password.')
    else:
        form = LoginForm()
    
    context = {'form': form}
    return render(request, 'main/login.html', context)


def logout_view(request):
    """User logout view"""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('login')


@login_required(login_url='login')
def dashboard(request):
    """User dashboard (protected view)"""
    enrollments = Enrollment.objects.filter(student=request.user).select_related('course')
    my_courses = []
    instructor_stats = {}
    if request.user.role == 'instructor':
        my_courses = Course.objects.filter(instructor=request.user).order_by('-created_at')
        instructor_stats = {
            'total_students_enrolled': sum(course.enrollments.count() for course in my_courses),
            'courses_created': my_courses.count(),
            'pending_enrollments': sum(1 for course in my_courses if course.enrollments.count() < course.max_students),
        }

    context = {
        'user': request.user,
        'enrollments': enrollments,
        'my_courses': my_courses,
        'instructor_stats': instructor_stats,
    }
    return render(request, 'main/dashboard.html', context)


@login_required(login_url='login')
def profile(request):
    """User profile view"""
    if request.method == 'POST':
        form = CustomUserChangeForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
    else:
        form = CustomUserChangeForm(instance=request.user)
    
    context = {'form': form}
    return render(request, 'main/profile.html', context)

def list_courses(request):
    """Display all published courses"""
    courses = Course.objects.filter(is_published=True)
    context = {'courses': courses}
    return render(request, 'main/courses/list_courses.html', context)


def course_detail(request, course_id):
    """View single course details"""
    try:
        course = Course.objects.get(id=course_id)
    except Course.DoesNotExist:
        messages.error(request, "Course not found.")
        return redirect('list_courses')
    
    # Check permissions: show if published OR user is instructor
    if not course.is_published and course.instructor != request.user:
        messages.error(request, "Course not found or access denied.")
        return redirect('list_courses')
    # Determine enrollment status for current user
    is_enrolled = False
    if request.user.is_authenticated:
        is_enrolled = Enrollment.objects.filter(student=request.user, course=course).exists()

    if request.method == 'POST' and request.user.is_authenticated and request.POST.get('body', '').strip():
        if request.user.role in ['student', 'instructor']:
            DiscussionPost.objects.create(course=course, author=request.user, body=request.POST['body'])
            messages.success(request, 'Your comment was posted.')
            return redirect('course_detail', course_id=course.id)

    posts = course.discussion_posts.select_related('author').all()
    context = {'course': course, 'is_enrolled': is_enrolled, 'posts': posts}
    return render(request, 'main/courses/course_detail.html', context)


@login_required(login_url='login')
def create_course(request):
    """Create a new course (instructors only)"""
    if request.user.role != 'instructor':
        messages.error(request, "Only instructors can create courses.")
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = CourseForm(request.POST)
        if form.is_valid():
            course = form.save(commit=False)
            course.instructor = request.user  # Set current user as instructor
            course.save()
            messages.success(request, f"Course '{course.title}' created successfully!")
            return redirect('course_detail', course_id=course.id)
    else:
        form = CourseForm()
    
    context = {'form': form}
    return render(request, 'main/courses/create_course.html', context)


@login_required(login_url='login')
def edit_course(request, course_id):
    """Edit an existing course (instructor only)"""
    try:
        course = Course.objects.get(id=course_id)
    except Course.DoesNotExist:
        messages.error(request, "Course not found.")
        return redirect('list_courses')
    
    # Check if user is the instructor
    if course.instructor != request.user:
        messages.error(request, "You can only edit your own courses.")
        return redirect('list_courses')
    
    if request.method == 'POST':
        form = CourseForm(request.POST, instance=course)
        if form.is_valid():
            form.save()
            messages.success(request, "Course updated successfully!")
            return redirect('course_detail', course_id=course.id)
    else:
        form = CourseForm(instance=course)
    
    context = {'form': form, 'course': course}
    return render(request, 'main/courses/edit_course.html', context)


@login_required(login_url='login')
def delete_course(request, course_id):
    """Delete a course (instructor only)"""
    try:
        course = Course.objects.get(id=course_id)
    except Course.DoesNotExist:
        messages.error(request, "Course not found.")
        return redirect('list_courses')
    
    # Check if user is the instructor
    if course.instructor != request.user:
        messages.error(request, "You can only delete your own courses.")
        return redirect('list_courses')
    
    if request.method == 'POST':
        course_title = course.title
        course.delete()
        messages.success(request, f"Course '{course_title}' deleted successfully!")
        return redirect('list_courses')
    
    context = {'course': course}
    return render(request, 'main/courses/delete_course.html', context)


@login_required(login_url='login')
def enroll_course(request, course_id):
    """Enroll the current student into a course"""
    try:
        course = Course.objects.get(id=course_id, is_published=True)
    except Course.DoesNotExist:
        messages.error(request, "Course not available for enrollment.")
        return redirect('list_courses')

    if request.user.role != 'student':
        messages.error(request, 'Only students can enroll in courses.')
        return redirect('course_detail', course_id=course.id)

    # Check if already enrolled
    enrollment, created = Enrollment.objects.get_or_create(student=request.user, course=course)
    if created:
        messages.success(request, f'You are now enrolled in {course.title}!')
    else:
        messages.info(request, f'You are already enrolled in {course.title}.')
    return redirect('course_detail', course_id=course.id)


@login_required(login_url='login')
def unenroll_course(request, course_id):
    """Unenroll the current student from a course"""
    try:
        course = Course.objects.get(id=course_id)
    except Course.DoesNotExist:
        messages.error(request, "Course not found.")
        return redirect('list_courses')

    try:
        enrollment = Enrollment.objects.get(student=request.user, course=course)
    except Enrollment.DoesNotExist:
        messages.error(request, 'You are not enrolled in this course.')
        return redirect('course_detail', course_id=course.id)

    if request.method == 'POST':
        enrollment.delete()
        messages.success(request, f'You have been unenrolled from {course.title}.')
        return redirect('list_courses')

    context = {'course': course}
    return render(request, 'main/courses/unenroll_confirm.html', context)


@login_required(login_url='login')
def my_enrollments(request):
    """List courses the current user is enrolled in"""
    enrollments = Enrollment.objects.filter(student=request.user).select_related('course')
    context = {'enrollments': enrollments}
    return render(request, 'main/courses/enrollments.html', context)


def search_courses(request):
    """Simple search over course title and description"""
    q = request.GET.get('q', '').strip()
    results = []
    if q:
        results = Course.objects.filter(
            Q(title__icontains=q) | Q(description__icontains=q),
            is_published=True
        )
    context = {'courses': results, 'query': q}
    return render(request, 'main/courses/list_courses.html', context)
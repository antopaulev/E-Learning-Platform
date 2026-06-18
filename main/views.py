from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .forms import CustomUserCreationForm, LoginForm, CustomUserChangeForm, CourseForm
from .models import User, Course
from django.http import Http404


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
    context = {
        'user': request.user,
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
    
    context = {'course': course}
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
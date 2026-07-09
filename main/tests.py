from django.test import TestCase
from django.urls import reverse
from .models import Course, DiscussionPost, Enrollment, User


class ForumAndInstructorDashboardTests(TestCase):
    def setUp(self):
        self.student = User.objects.create_user(
            username='student1', email='student@example.com', password='pass123', role='student'
        )
        self.instructor = User.objects.create_user(
            username='instructor1', email='instructor@example.com', password='pass123', role='instructor'
        )
        self.course = Course.objects.create(
            title='Python Basics',
            description='Learn Python',
            instructor=self.instructor,
            is_published=True,
        )
        Enrollment.objects.create(student=self.student, course=self.course)

    def test_student_can_post_to_course_forum(self):
        self.client.login(username='student1', password='pass123')
        response = self.client.post(
            reverse('course_detail', kwargs={'course_id': self.course.id}),
            {'body': 'Great course!'}
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(DiscussionPost.objects.filter(course=self.course, author=self.student).exists())

    def test_instructor_dashboard_shows_key_stats(self):
        self.client.login(username='instructor1', password='pass123')
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '1')
        self.assertContains(response, 'Total Students Enrolled')
        self.assertContains(response, 'Courses Created')
        self.assertContains(response, 'Pending Enrollments')

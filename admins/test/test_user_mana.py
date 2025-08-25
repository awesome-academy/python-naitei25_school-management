from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType

User = get_user_model()

class UserViewsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin_user = User.objects.create_user(
            username='admin', password='adminpass', is_superuser=True, is_staff=True)
        self.admin_user.user_permissions.set(Permission.objects.all())
        self.admin_user.save()
        self.client.login(username='admin', password='adminpass')
        self.normal_user = User.objects.create_user(
            username='john', email='john@example.com', password='test123')

    def test_user_list_view(self):
        response = self.client.get(reverse('user_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.normal_user.username)

    def test_search_user_by_username(self):
        response = self.client.get(reverse('user_list'), {'q': 'john'})
        self.assertContains(response, 'john')

    def test_filter_user_by_is_active(self):
        self.normal_user.is_active = False
        self.normal_user.save()
        response = self.client.get(reverse('user_list'), {'is_active': 'False'})
        self.assertContains(response, 'john')

    def test_add_user_success(self):
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'testpass123',
            'first_name': 'New',
            'last_name': 'User',
            'is_superuser': False,
            'is_active': True,
        }
        response = self.client.post(reverse('add_user'), data)
        self.assertTrue(User.objects.filter(username='newuser').exists())

    def test_add_user_invalid_form(self):
        data = {
            'username': '',  # Invalid
            'email': 'invalid@example.com',
        }
        response = self.client.post(reverse('add_user'), data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'This field is required')

    def test_edit_user(self):
        data = {
            'username': 'john',
            'email': 'updated@example.com',
            'first_name': 'Updated',
            'last_name': 'Name',
            'password': '',
            'is_active': True,
            'is_superuser': False,
        }
        url = reverse('edit_user', args=[self.normal_user.id])
        response = self.client.post(url, data)
        self.normal_user.refresh_from_db()
        self.assertEqual(self.normal_user.email, 'updated@example.com')

    def test_edit_user_password_change(self):
        data = {
            'username': 'john',
            'email': 'john@example.com',
            'first_name': 'John',
            'last_name': 'Doe',
            'password': 'newsecurepass',
            'is_superuser': False,
            'is_active': True,
        }
        url = reverse('edit_user', args=[self.normal_user.id])
        response = self.client.post(url, data)
        self.normal_user.refresh_from_db()
        self.assertTrue(self.normal_user.check_password('newsecurepass'))

    def test_toggle_user_status(self):
        url = reverse('toggle_user_status', args=[self.normal_user.id])
        response = self.client.get(url)
        self.normal_user.refresh_from_db()
        self.assertFalse(self.normal_user.is_active)

    def test_toggle_own_user_status(self):
        url = reverse('toggle_user_status', args=[self.admin_user.id])
        response = self.client.get(url)
        self.admin_user.refresh_from_db()
        self.assertTrue(self.admin_user.is_active) 
        
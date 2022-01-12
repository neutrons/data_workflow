from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse


class TestViews(TestCase):
    @classmethod
    def setUpTestData(cls):
        User.objects.create_user(username='user', password='pw').save()

    @classmethod
    def classTearDown(cls):
        User.objects.all().delete()

    def test_perform_logout(self):
        self.assertTrue(self.client.login(username='user', password='pw'))

        with self.settings(ALLOWED_DOMAIN=[],
                           ALLOWED_HOSTS=['*']):
            response = self.client.get(reverse('users:perform_logout'))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/dasmon/')

    def test_perform_login(self):
        # wrong password
        response = self.client.post(reverse('users:perform_login'),
                                    data={'username': 'user',
                                          'password': 'wrong'})
        self.assertTemplateUsed(response, 'users/authenticate.html')

        # correct password
        response = self.client.post(reverse('users:perform_login'),
                                    data={'username': 'user',
                                          'password': 'pw'})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/dasmon/')

        # with next option
        response = self.client.get(reverse('users:perform_login'),
                                   data={'next': 'dasmon:dashboard'})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/dasmon/')

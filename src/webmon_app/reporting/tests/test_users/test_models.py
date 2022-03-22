from datetime import datetime
from django.test import TestCase
from django.contrib.auth.models import User
from users.models import PageView, DeveloperNode, SiteNotification


class TestModels(TestCase):
    def test_PageView(self):
        user = User.objects.create_user(username="user", password="password")

        pg = PageView.objects.create(user=user, view="view", path="/", ip="127.0.0.1")

        self.assertEqual(pg._meta.get_field("view").max_length, 64)
        self.assertEqual(pg._meta.get_field("path").max_length, 128)
        self.assertEqual(pg._meta.get_field("ip").max_length, 64)
        self.assertEqual(pg.user, user)
        self.assertEqual(pg.view, "view")
        self.assertEqual(pg.path, "/")
        self.assertEqual(pg.ip, "127.0.0.1")
        self.assertTrue(isinstance(pg.timestamp, datetime))

        pg = PageView.objects.create(user=user, view="view", path="", ip="127.0.0.1")

        self.assertEqual(pg._meta.get_field("view").max_length, 64)
        self.assertEqual(pg._meta.get_field("path").max_length, 128)
        self.assertEqual(pg._meta.get_field("ip").max_length, 64)

    def test_DeveloperNode(self):
        dn = DeveloperNode(ip="127.0.0.1")
        self.assertEqual(dn._meta.get_field("ip").max_length, 64)
        self.assertEqual(dn.ip, "127.0.0.1")

    def test_SiteNotification(self):
        sn = SiteNotification(message="msg", is_active=True)
        self.assertEqual(sn.message, "msg")
        self.assertEqual(sn.is_active, True)

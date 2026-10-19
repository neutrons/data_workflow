from unittest import mock

from django.contrib.auth.models import AnonymousUser, Group, User
from django.test import TestCase

from reporting.users import view_util
from reporting.users.models import PageView


class TestViews(TestCase):
    def test_fill_template_values(self):
        user = User.objects.create_user("user")
        request = mock.MagicMock()
        request.user = user
        request.path = "/path/"
        request.mobile = False
        with self.settings(GRAVATAR_URL="http://gravatar.url/"):
            template_args = view_util.fill_template_values(request)
        self.assertEqual(template_args["user"].username, "user")
        self.assertEqual(
            template_args["gravatar_url"],
            "http://gravatar.url/ee11cbb19052e40b07aac0ca060c23ee?d=identicon",
        )
        self.assertEqual(template_args["logout_url"], "/users/logout")
        self.assertEqual(template_args["login_url"], "/users/login?next=/path/")
        self.assertEqual(template_args["is_mobile"], False)

        request.user = AnonymousUser()
        template_args = view_util.fill_template_values(request)
        self.assertEqual(template_args["user"].username, "Guest User")

    def test_login_required_401(self):
        request_processor = view_util.login_required_401(lambda x: x)

        user = User.objects.create_user("user")
        request = mock.MagicMock()
        request.user = user

        return_request = request_processor(request)
        self.assertIs(return_request, request)

        request.user = AnonymousUser()
        return_request = request_processor(request)
        self.assertIsNot(return_request, request)
        self.assertEqual(return_request.status_code, 401)

        request_processor = view_util.login_required_401(None)
        request.user = user
        return_request = request_processor(request)
        self.assertIsNot(return_request, request)
        self.assertEqual(return_request.status_code, 500)

    @mock.patch("socket.gethostbyaddr", return_value=("bl4b-ws1.sns.gov", [], ["127.0.0.1"]))
    def test_login_required_401_ignores_where_the_request_comes_from(self, mock_gethostbyaddr):
        # Anonymous requests that look local by address, header or reverse DNS still get 401
        request_processor = view_util.login_required_401(lambda x: x)
        request = mock.MagicMock()
        request.user = AnonymousUser()
        request.META = {"REMOTE_ADDR": "127.0.0.1", "HTTP_X_REAL_IP": "127.0.0.1"}
        self.assertEqual(request_processor(request).status_code, 401)

    def test_is_instrument_staff(self):
        # is_staff
        user = User.objects.create_user("user")
        user.is_staff = True
        request = mock.MagicMock()
        request.user = user
        self.assertTrue(view_util.is_instrument_staff(request, "inst"))
        user.is_staff = False

        # in django group
        grp = Group.objects.create(name="INST_team")
        grp.save()
        user.groups.add(grp)
        with self.settings(INSTRUMENT_TEAM_SUFFIX="_team"):
            self.assertTrue(view_util.is_instrument_staff(request, "inst"))

        # no in django group
        with self.settings(INSTRUMENT_TEAM_SUFFIX="_team"):
            self.assertFalse(view_util.is_instrument_staff(request, "different_inst"))

        # in LDAP group
        ldap_user = mock.MagicMock()
        ldap_user.group_names = ["sns_inst_team"]
        user.ldap_user = ldap_user

        self.assertTrue(view_util.is_instrument_staff(request, "inst"))

        # not in LDAP group
        ldap_user = mock.MagicMock()
        ldap_user.group_names = ["sns_different_inst_team"]
        user.ldap_user = ldap_user

        self.assertFalse(view_util.is_instrument_staff(request, "inst"))

        # except in groups
        ldap_user.group_names = None
        self.assertFalse(view_util.is_instrument_staff(request, "inst"))

        # in slowcontrols_developers group
        ldap_user = mock.MagicMock()
        ldap_user.group_names = ["slowcontrols_developers"]
        user.ldap_user = ldap_user
        self.assertTrue(view_util.is_instrument_staff(request, "inst"))

    def test_is_experiment_member(self):
        # HIDE_RUN_DETAILS = False
        with self.settings(HIDE_RUN_DETAILS=False):
            self.assertTrue(view_util.is_experiment_member(None, None, None))

        # is_staff
        user = User.objects.create_user("user")
        user.is_staff = True
        request = mock.MagicMock()
        request.user = user
        self.assertTrue(view_util.is_experiment_member(request, "inst", "exp"))
        user.is_staff = False

        # in LDAP group
        ldap_user = mock.MagicMock()
        ldap_user.group_names = ["IPTS-1234"]
        user.ldap_user = ldap_user
        exp = mock.MagicMock()
        exp.expt_name = "IPTS-1234"
        self.assertTrue(view_util.is_experiment_member(request, "inst", exp))

        # invalid input
        exp.expt_name = 1234
        self.assertFalse(view_util.is_experiment_member(request, "inst", exp))

        # in slowcontrols_developers group
        ldap_user = mock.MagicMock()
        ldap_user.group_names = ["slowcontrols_developers"]
        user.ldap_user = ldap_user
        exp.expt_name = "IPTS-1234"
        self.assertTrue(view_util.is_experiment_member(request, "inst", exp))

    def test_monitor(self):
        user = User.objects.create_user("user")
        request = mock.MagicMock()
        request.user = user
        request.META = {"HTTP_X_REAL_IP": "1.2.3.4"}
        request.get_full_path.return_value = "/full/path"

        request_processor = view_util.monitor(lambda x: x)

        # without monitor
        with self.settings(MONITOR_ON=False):
            return_request = request_processor(request)
        self.assertIs(return_request, request)
        self.assertEqual(len(PageView.objects.all()), 0)

        # with monitor
        with self.settings(MONITOR_ON=True):
            return_request = request_processor(request)
        self.assertIs(return_request, request)
        self.assertEqual(len(PageView.objects.all()), 1)
        pv = PageView.objects.get(id=1)
        self.assertEqual(pv.user, user)
        self.assertEqual(pv.view, "reporting.tests.test_users.test_view_util.<lambda>")
        self.assertEqual(pv.ip, "1.2.3.4")
        self.assertEqual(pv.path, "/full/path")

        PageView.objects.all().delete()

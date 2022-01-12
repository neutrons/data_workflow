from unittest import mock
from django.test import TestCase
from django.contrib.auth.models import AnonymousUser, User, Group
from reporting.users import view_util
from users.models import PageView


class TestViews(TestCase):
    def test_fill_template_values(self):
        user = User.objects.create_user('user')
        request = mock.MagicMock()
        request.user = user
        request.path = '/path/'
        request.mobile = False
        with self.settings(GRAVATAR_URL='http://gravatar.url/',
                           ALLOWED_DOMAIN=''):
            template_args = view_util.fill_template_values(request)
        self.assertEqual(template_args['user'].username, 'user')
        self.assertEqual(template_args['gravatar_url'],
                         'http://gravatar.url/2d0c80ccc09be582d10a15e736601e50?d=identicon')
        self.assertEqual(template_args['logout_url'], '/users/logout')
        self.assertEqual(template_args['login_url'], '/users/login?next=/path/')
        self.assertEqual(template_args['is_mobile'], False)

        with self.settings(GRAVATAR_URL='http://gravatar.url/',
                           ALLOWED_DOMAIN=('a.com', 'b.com')):
            template_args = view_util.fill_template_values(request)
        self.assertEqual(template_args['user'].username, 'user')
        self.assertEqual(template_args['gravatar_url'],
                         'http://gravatar.url/76569a591ceb2b0241c266e658260f9f?d=identicon')
        self.assertEqual(template_args['logout_url'], '/users/logout')
        self.assertEqual(template_args['login_url'], '/users/login?next=/path/')
        self.assertEqual(template_args['is_mobile'], False)

        request.user = AnonymousUser()
        template_args = view_util.fill_template_values(request)
        self.assertEqual(template_args['user'].username, 'Guest User')

    @mock.patch('socket.gethostbyaddr')
    def test_check_credentials(self, mock_gethostbyaddr):
        user = User.objects.create_user('user')
        request = mock.MagicMock()
        request.user = user
        self.assertTrue(view_util._check_credentials(request))

        request.user = AnonymousUser()

        with self.settings(ALLOWED_DOMAIN='',
                           ALLOWED_HOSTS=[]):
            self.assertFalse(view_util._check_credentials(request))

        request.META = {'REMOTE_ADDR': '1.2.3.4'}

        mock_gethostbyaddr.return_value = ('hostname.gov', None, None)

        with self.settings(ALLOWED_DOMAIN='.gov',
                           ALLOWED_HOSTS=[]):
            self.assertTrue(view_util._check_credentials(request))

        mock_gethostbyaddr.return_value = ('localhost', None, None)

        with self.settings(ALLOWED_DOMAIN='.gov',
                           ALLOWED_HOSTS=[]):
            self.assertTrue(view_util._check_credentials(request))

        mock_gethostbyaddr.return_value = None

        with self.settings(ALLOWED_DOMAIN='.gov',
                           ALLOWED_HOSTS=[]):
            self.assertFalse(view_util._check_credentials(request))

        mock_gethostbyaddr.return_value = ('host1', None, None)

        with self.settings(ALLOWED_DOMAIN='',
                           ALLOWED_HOSTS=['host1', 'host2']):
            self.assertTrue(view_util._check_credentials(request))

        mock_gethostbyaddr.return_value = ('host3', None, None)

        with self.settings(ALLOWED_DOMAIN='',
                           ALLOWED_HOSTS=['host1', 'host2']):
            self.assertFalse(view_util._check_credentials(request))

        mock_gethostbyaddr.return_value = None

        with self.settings(ALLOWED_DOMAIN='',
                           ALLOWED_HOSTS=['host1', 'host2']):
            self.assertFalse(view_util._check_credentials(request))

    def test_login_or_local_required(self):
        request_processor = view_util.login_or_local_required(lambda x: x)

        user = User.objects.create_user('user')
        request = mock.MagicMock()
        request.user = user

        return_request = request_processor(request)
        self.assertIs(return_request, request)

        request.user = AnonymousUser()
        with self.settings(ALLOWED_DOMAIN='',
                           ALLOWED_HOSTS=[]):
            return_request = request_processor(request)
        self.assertIsNot(return_request, request)

    def test_login_or_local_required_401(self):
        request_processor = view_util.login_or_local_required_401(lambda x: x)

        user = User.objects.create_user('user')
        request = mock.MagicMock()
        request.user = user

        return_request = request_processor(request)
        self.assertIs(return_request, request)

        request.user = AnonymousUser()
        with self.settings(ALLOWED_DOMAIN='',
                           ALLOWED_HOSTS=[]):
            return_request = request_processor(request)
        self.assertIsNot(return_request, request)
        self.assertEqual(return_request.status_code, 401)

        request_processor = view_util.login_or_local_required_401(None)
        request.user = user
        return_request = request_processor(request)
        self.assertIsNot(return_request, request)
        self.assertEqual(return_request.status_code, 500)

    def test_is_instrument_staff(self):
        # is_staff
        user = User.objects.create_user('user')
        user.is_staff = True
        request = mock.MagicMock()
        request.user = user
        self.assertTrue(view_util.is_instrument_staff(request, 'inst'))
        user.is_staff = False

        # in django group
        grp = Group.objects.create(name='INST_team')
        grp.save()
        user.groups.add(grp)
        with self.settings(INSTRUMENT_TEAM_SUFFIX='_team'):
            self.assertTrue(view_util.is_instrument_staff(request, 'inst'))

        # no in django group
        with self.settings(INSTRUMENT_TEAM_SUFFIX='_team'):
            self.assertFalse(view_util.is_instrument_staff(request, 'different_inst'))

        # in LDAP group
        ldap_user = mock.MagicMock()
        ldap_user.group_names = ['sns_inst_team']
        user.ldap_user = ldap_user

        self.assertTrue(view_util.is_instrument_staff(request, 'inst'))

        # not in LDAP group
        ldap_user = mock.MagicMock()
        ldap_user.group_names = ['sns_different_inst_team']
        user.ldap_user = ldap_user

        self.assertFalse(view_util.is_instrument_staff(request, 'inst'))

        # except in groups
        ldap_user.group_names = None
        self.assertFalse(view_util.is_instrument_staff(request, 'inst'))

    def test_is_experiment_member(self):
        # HIDE_RUN_DETAILS = False
        with self.settings(HIDE_RUN_DETAILS=False):
            self.assertTrue(view_util.is_experiment_member(None, None, None))

        # is_staff
        user = User.objects.create_user('user')
        user.is_staff = True
        request = mock.MagicMock()
        request.user = user
        self.assertTrue(view_util.is_experiment_member(request, 'inst', 'exp'))
        user.is_staff = False

        # in LDAP group
        ldap_user = mock.MagicMock()
        ldap_user.group_names = ['IPTS-1234']
        user.ldap_user = ldap_user
        exp = mock.MagicMock()
        exp.expt_name = 'IPTS-1234'
        self.assertTrue(view_util.is_experiment_member(request, 'inst', exp))

        # invalid input
        exp.expt_name = 1234
        self.assertFalse(view_util.is_experiment_member(request, 'inst', exp))

    def test_monitor(self):
        user = User.objects.create_user('user')
        request = mock.MagicMock()
        request.user = user
        request.META = {'REMOTE_ADDR': '1.2.3.4'}
        request.get_full_path.return_value = '/full/path'

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
        self.assertEqual(pv.view, 'reporting.tests.test_users.test_view_util.<lambda>')
        self.assertEqual(pv.ip, '1.2.3.4')
        self.assertEqual(pv.path, '/full/path')

        PageView.objects.all().delete()

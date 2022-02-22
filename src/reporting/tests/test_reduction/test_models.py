import datetime
from django.test import TestCase
from django.contrib.auth.models import User
from report.models import Instrument
from reduction.models import (
    ReductionProperty,
    PropertyModification,
    PropertyDefault,
    Choice,
)


class TestModels(TestCase):
    @classmethod
    def setUpTestData(cls):
        instrument = Instrument.objects.create(name="inst")
        instrument.save()

        user = User.objects.create_user("user", "email@server.com", "password")

        rp = ReductionProperty.objects.create(
            instrument=instrument, key="key", value="value"
        )

        PropertyModification.objects.create(property=rp, value="modified", user=user)

        PropertyDefault.objects.create(property=rp, value="default")

        Choice.objects.create(
            instrument=instrument,
            property=rp,
            description="description",
            value="choice",
        )

    @classmethod
    def classTearDown(cls):
        Instrument.objects.all().delete()

    def test_ReductionProperty(self):
        rp = ReductionProperty.objects.get(id=1)
        self.assertEqual(str(rp), "inst.key")
        self.assertEqual(rp.value, "value")
        self.assertEqual(rp.key, "key")
        self.assertTrue(isinstance(rp.timestamp, datetime.datetime))

    def test_PropertyModification(self):
        pm = PropertyModification.objects.get(id=1)
        self.assertTrue(isinstance(pm.property, ReductionProperty))
        self.assertEqual(pm.value, "modified")
        self.assertEqual(pm.user.username, "user")
        self.assertTrue(isinstance(pm.timestamp, datetime.datetime))

    def test_PropertyDefault(self):
        pd = PropertyDefault.objects.get(id=1)
        self.assertTrue(isinstance(pd.property, ReductionProperty))
        self.assertEqual(pd.value, "default")
        self.assertTrue(isinstance(pd.timestamp, datetime.datetime))

    def test_Choice(self):
        c = Choice.objects.get(id=1)
        self.assertEqual(str(c), "inst.inst.key[description]")
        self.assertTrue(isinstance(c.property, ReductionProperty))
        self.assertEqual(c.description, "description")
        self.assertEqual(c.value, "choice")

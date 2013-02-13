from django.test import TestCase
from forest.main.models import Stand, get_stand
from django.contrib.auth.models import User, Group


class StandModelTest(TestCase):
    def setUp(self):
        self.u = User.objects.create(username="testuser")
        self.g = Group.objects.create(name="testgroup")
        self.u.groups.add(self.g)
        self.stand = Stand.objects.create(
            title="test stand",
            hostname="test.example.com",
            access="open",
        )

    def tearDown(self):
        self.g.delete()
        self.u.delete()

    def test_unicode(self):
        assert str(self.stand) == "test stand"

    def test_csshash(self):
        self.assertEquals(
            self.stand.css_hash(),
            'da39a3ee5e6b4b0d3255bfef95601890afd80709')

    def test_can_view(self):
        assert self.stand.can_view(self.u)

    def test_can_edit(self):
        assert not self.stand.can_edit(self.u)

    def test_get_stand(self):
        assert get_stand("test.example.com") == self.stand

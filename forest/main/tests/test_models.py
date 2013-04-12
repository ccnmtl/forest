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

    def test_can_admin(self):
        assert not self.stand.can_admin(self.u)

    def test_get_stand(self):
        assert get_stand("test.example.com") == self.stand

    def test_available_pageblocks(self):
        assert self.stand.available_pageblocks() == []

    def test_get_root(self):
        assert self.stand.get_root().label == "Root"

    def test_make_default_tree(self):
        self.stand.make_default_tree()
        assert len(self.stand.get_root().get_children()) > 0

    def test_default_gating(self):
        assert not self.stand.gated


class ModelAuthTests(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create(username="adminuser")
        self.editor_user = User.objects.create(username="editoruser")
        self.student_user = User.objects.create(username="studentuser")
        self.nogroups_user = User.objects.create(username="nogroupsuser")

        self.super_user = User.objects.create(username="superuser",
                                              is_superuser=True)

        self.admin_group = Group.objects.create(name="admingroup")
        self.editor_group = Group.objects.create(name="editorgroup")
        self.student_group = Group.objects.create(name="studentgroup")

        self.admin_user.groups.add(self.admin_group)
        self.editor_user.groups.add(self.editor_group)
        self.student_user.groups.add(self.student_group)

        self.open_stand = Stand.objects.create(
            title="open stand",
            hostname="openstand.example.com",
            access="open",
        )
        self.loginonly_stand = Stand.objects.create(
            title="login stand",
            hostname="loginstand.example.com",
            access="login",
        )
        self.group_stand = Stand.objects.create(
            title="group stand",
            hostname="loginstand.example.com",
            access="group",
        )
        self.whitelist_stand = Stand.objects.create(
            title="whitelist stand",
            hostname="whiteliststand.example.com",
            access="whitelist",
        )

    def tearDown(self):
        self.admin_user.delete()
        self.editor_user.delete()
        self.student_user.delete()
        self.nogroups_user.delete()
        self.super_user.delete()

        self.open_stand.delete()
        self.loginonly_stand.delete()
        self.group_stand.delete()
        self.whitelist_stand.delete()

    def test_no_user(self):
        assert not self.open_stand.can_edit(None)
        assert not self.group_stand.can_edit(None)
        assert not self.loginonly_stand.can_edit(None)
        assert not self.whitelist_stand.can_edit(None)

        assert self.open_stand.can_view(None)
        assert not self.group_stand.can_view(None)
        assert not self.loginonly_stand.can_view(None)
        assert not self.whitelist_stand.can_view(None)

        assert not self.open_stand.can_admin(None)
        assert not self.group_stand.can_admin(None)
        assert not self.loginonly_stand.can_admin(None)
        assert not self.whitelist_stand.can_admin(None)

    def test_anon_user(self):
        class StubUser(object):
            def is_anonymous(self):
                return True
        u = StubUser()
        assert not self.open_stand.can_edit(u)
        assert not self.group_stand.can_edit(u)
        assert not self.loginonly_stand.can_edit(u)
        assert not self.whitelist_stand.can_edit(u)

        assert self.open_stand.can_view(u)
        assert not self.group_stand.can_view(u)
        assert not self.loginonly_stand.can_view(u)
        assert not self.whitelist_stand.can_view(u)

        assert not self.open_stand.can_admin(u)
        assert not self.group_stand.can_admin(u)
        assert not self.loginonly_stand.can_admin(u)
        assert not self.whitelist_stand.can_admin(u)

    def test_super_user(self):
        u = self.super_user
        assert self.open_stand.can_edit(u)
        assert self.group_stand.can_edit(u)
        assert self.loginonly_stand.can_edit(u)
        assert self.whitelist_stand.can_edit(u)

        assert self.open_stand.can_view(u)
        assert self.group_stand.can_view(u)
        assert self.loginonly_stand.can_view(u)
        assert self.whitelist_stand.can_view(u)

        assert self.open_stand.can_admin(u)
        assert self.group_stand.can_admin(u)
        assert self.loginonly_stand.can_admin(u)
        assert self.whitelist_stand.can_admin(u)

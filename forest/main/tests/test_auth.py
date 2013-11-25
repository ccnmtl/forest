from django.test import TestCase
from forest.main.auth import AllowEditUser, AllowInEditGroup, AllowStandUser
from forest.main.auth import AllowUserGroupCanView, AllowAdminUser
from forest.main.auth import AllowInAdminGroup, AccessChecker


class StubChecker(object):
    def __init__(self, v):
        self.v = v

    def _access_in(self, l):
        return self.v

    def in_edit_group(self):
        return self.v

    def standuser(self):
        class C(object):
            def count(self):
                return 2
        return C()

    def user_group_can_x(self, _x):
        return self.v


class TestAllowEditUser(TestCase):
    def test_check(self):
        sut = AllowEditUser()
        checker = StubChecker(True)
        self.assertEqual(sut.check(checker), True)


class TestAllowInEditGroup(TestCase):
    def test_check(self):
        sut = AllowInEditGroup()
        checker = StubChecker(True)
        self.assertEqual(sut.check(checker), True)


class TestAllowStandUser(TestCase):
    def test_check(self):
        sut = AllowStandUser()
        checker = StubChecker(True)
        self.assertEqual(sut.check(checker), True)


class TestAllowUserGroupCanView(TestCase):
    def test_check(self):
        sut = AllowUserGroupCanView()
        checker = StubChecker(True)
        self.assertEqual(sut.check(checker), True)


class TestAllowInAdminGroup(TestCase):
    def test_check(self):
        sut = AllowInAdminGroup()
        checker = StubChecker(True)
        self.assertEqual(sut.check(checker), True)


class TestAllowAdminUser(TestCase):
    def test_check(self):
        sut = AllowAdminUser()
        checker = StubChecker(True)
        self.assertEqual(sut.check(checker), True)


class StubStandUserSet(object):
    def filter(self, **kargs):
        class C(object):
            def count(self):
                return 2

            def __getitem__(self, i):
                class D(object):
                    access = i
                return D()

        return C()


class StubStand(object):
    def __init__(self):
        self.standuser_set = StubStandUserSet()


class TestAccessChecker(TestCase):
    def test_access_in(self):
        sut = AccessChecker(StubStand(), None)
        self.assertEqual(sut._access_in([]), False)
        self.assertEqual(sut._access_in([0]), True)

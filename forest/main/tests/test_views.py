from django.test import TestCase
from django.test.client import Client
from forest.main.models import Stand
from django.contrib.auth.models import User, Group


class SimpleTest(TestCase):
    def setUp(self):
        self.u = User.objects.create(username="testuser")
        self.g = Group.objects.create(name="testgroup")
        self.u.groups.add(self.g)
        self.stand = Stand.objects.create(
            title="test stand",
            hostname="test.example.com",
            access="open",
        )
        self.c = Client()

    def tearDown(self):
        self.g.delete()
        self.u.delete()

    def test_index(self):
        response = self.c.get('/', HTTP_HOST="test.example.com")
        self.assertEquals(response.status_code, 302)

    def test_smoketests(self):
        # just request them to make sure they are covered
        # it's actually ok for the smoketests to return a "FAIL"
        # we don't care about that here. We just want to know
        # that the smoketests are runnable and not erroring out
        # themselves
        response = self.c.get('/smoketest/')
        self.assertEquals(response.status_code, 200)

    def test_css(self):
        response = self.c.get('/_stand/css/', HTTP_HOST="test.example.com")
        self.assertEquals(response.status_code, 200)
        self.assertEquals(response['Content-Type'], "text/css")


class AuthTests(TestCase):
    def setUp(self):
        self.u = User.objects.create(username="testuser")
        self.u.set_password("test")
        self.u.save()
        self.g = Group.objects.create(name="testgroup")
        self.u.groups.add(self.g)
        # make one that our user can't access
        self.stand = Stand.objects.create(
            title="test stand",
            hostname="test.example.com",
            access="whitelist",
        )
        self.c = Client()
        self.c.login(username="testuser", password="test")

    def tearDown(self):
        self.g.delete()
        self.u.delete()
        self.stand.delete()

    def test_logged_in_not_authorized(self):
        response = self.c.get('/', HTTP_HOST="test.example.com")
        self.assertEquals(response.status_code, 403)
        assert "grumpycat.jpg" in response.content

    def test_logged_in_not_authorized_edit(self):
        response = self.c.get('/edit/', HTTP_HOST="test.example.com")
        self.assertEquals(response.status_code, 403)
        assert "grumpycat.jpg" in response.content

    def test_logged_in_not_authorized_admin(self):
        response = self.c.get('/_stand/', HTTP_HOST="test.example.com")
        self.assertEquals(response.status_code, 403)
        assert "grumpycat.jpg" in response.content


class AddStandTests(TestCase):
    def setUp(self):
        self.u = User.objects.create(username="testuser", is_staff=True)
        self.u.set_password("test")
        self.u.save()
        self.g = Group.objects.create(name="testgroup")
        self.u.groups.add(self.g)
        # make one that our user can't access
        self.stand = Stand.objects.create(
            title="test stand",
            hostname="test.example.com",
            access="open",
        )
        self.c = Client()
        self.c.login(username="testuser", password="test")

    def tearDown(self):
        self.g.delete()
        self.u.delete()
        self.stand.delete()

    def test_create_new_stand(self):
        response = self.c.get("/_stand/add/")
        assert response.status_code == 200
        response = self.c.post(
            "/_stand/add/",
            dict(
                hostname="test2.example.com",
                title="test site",
                css="",
                access="open",
                description="",
            ))
        assert response.status_code == 200

    def test_create_new_forest_stand(self):
        response = self.c.post(
            "/_stand/add/",
            dict(
                hostname="test2.forest.ccnmtl.columbia.edu",
                title="test site",
                css="",
                access="open",
                description="",
            ))
        assert response.status_code == 302

    def test_create_duplicate(self):
        response = self.c.post(
            "/_stand/add/",
            dict(hostname="test.example.com"))
        assert "a stand with that hostname already exists" in response.content

    def test_create_new_forest_stand_nonstaff(self):
        self.u.is_staff = False
        self.u.save()
        response = self.c.post(
            "/_stand/add/",
            dict(
                hostname="test3.example.com",
                title="test site",
                css="",
                access="open",
                description="",
            ))
        assert "only staff may access this" in response.content
        self.u.is_staff = True
        self.u.save()

    def test_clone_stand(self):
        self.u.is_superuser = True
        self.u.save()
        response = self.c.get("/clone/", HTTP_HOST="test.example.com")
        assert response.status_code == 200
        response = self.c.post(
            "/clone/",
            dict(
                new_hierarchy="cloned.example.com",
                ),
            HTTP_HOST="test.example.com",
        )
        assert response.status_code == 200
        response = self.c.get("/welcome/", HTTP_HOST="cloned.example.com")
        assert "no such site" not in response.content

from django.test import TestCase
from django.test.client import Client
from forest.main.models import Stand, StandAvailablePageBlock, StandUser
from forest.main.models import StandGroup
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

    def test_nonexistant_stand(self):
        response = self.c.get('/', HTTP_HOST="fooble")
        self.assertEquals(response.status_code, 200)
        self.assertEquals(response.content, "no such site 'fooble'")

    def test_smoketests(self):
        # just request them to make sure they are covered
        # it's actually ok for the smoketests to return a "FAIL"
        # we don't care about that here. We just want to know
        # that the smoketests are runnable and not erroring out
        # themselves
        response = self.c.get('/_smoketest/')
        self.assertEquals(response.status_code, 200)

    def test_css(self):
        response = self.c.get('/_stand/css/', HTTP_HOST="test.example.com")
        self.assertEquals(response.status_code, 200)
        self.assertEquals(response['Content-Type'], "text/css")

    def test_anon_gated(self):
        # anon user, open access, gated
        self.stand.gated = True
        response = self.c.get("/", HTTP_HOST="test.example.com")
        self.assertEquals(response.status_code, 302)


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

        self.u2 = User.objects.create(username="testuser2", is_superuser=True)
        self.u2.set_password("test")
        self.u2.save()

    def tearDown(self):
        self.g.delete()
        self.u.delete()
        self.u2.delete()
        self.stand.delete()

    def test_anon(self):
        # not logged, in so we should just get sent to the login screen
        c2 = Client()
        response = c2.get("/", HTTP_HOST="test.example.com")
        self.assertEquals(response.status_code, 302)

    def test_anon_instructor(self):
        # not logged, in so we should just get sent to the login screen
        c2 = Client()
        response = c2.get("/instructor/", HTTP_HOST="test.example.com")
        self.assertEquals(response.status_code, 302)

    def test_logged_in_not_authorized(self):
        response = self.c.get('/', HTTP_HOST="test.example.com")
        self.assertEquals(response.status_code, 403)
        assert "grumpycat.jpg" in response.content

    def test_logged_in_not_authorized_edit(self):
        response = self.c.get('/edit/', HTTP_HOST="test.example.com")
        self.assertEquals(response.status_code, 403)
        assert "grumpycat.jpg" in response.content

    def test_logged_in_not_authorized_instructor(self):
        response = self.c.get('/instructor/', HTTP_HOST="test.example.com")
        self.assertEquals(response.status_code, 403)
        assert "grumpycat.jpg" in response.content

    def test_logged_in_not_authorized_admin(self):
        response = self.c.get('/_stand/', HTTP_HOST="test.example.com")
        self.assertEquals(response.status_code, 403)
        assert "grumpycat.jpg" in response.content

    def test_logged_in_superuser(self):
        self.c.login(username="testuser2", password="test")
        response = self.c.get('/', HTTP_HOST="test.example.com")
        self.assertNotEquals(response.status_code, 403)
        assert "grumpycat.jpg" not in response.content

    def test_logged_in_superuser_edit(self):
        self.c.login(username="testuser2", password="test")
        response = self.c.get('/edit/', HTTP_HOST="test.example.com")
        self.assertNotEquals(response.status_code, 403)
        assert "grumpycat.jpg" not in response.content

    def test_logged_in_superuser_instructor(self):
        self.c.login(username="testuser2", password="test")
        response = self.c.get('/instructor/', HTTP_HOST="test.example.com")
        self.assertNotEquals(response.status_code, 403)
        assert "grumpycat.jpg" not in response.content

    def test_logged_in_superuser_admin(self):
        self.c.login(username="testuser2", password="test")
        response = self.c.get('/_stand/', HTTP_HOST="test.example.com")
        self.assertNotEquals(response.status_code, 403)
        assert "grumpycat.jpg" not in response.content

    def test_logged_in_superuser_admin_nonexistant(self):
        self.c.login(username="testuser2", password="test")
        response = self.c.get('/_stand/', HTTP_HOST="fooble")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, "no such site 'fooble'")


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
        PAGEBLOCKS = [
            'pageblocks.TextBlock',
            'pageblocks.HTMLBlock',
            'pageblocks.PullQuoteBlock',
            'pageblocks.ImageBlock',
            'pageblocks.ImagePullQuoteBlock',
            'quizblock.Quiz',
            'careermapblock.CareerMap',
            'fridgeblock.FridgeBlock',
        ]

        for pb in PAGEBLOCKS:
            StandAvailablePageBlock.objects.create(stand=self.stand, block=pb)

        self.stand.get_root().add_child_section_from_dict(
            {
                'label': 'Different Welcome',
                'slug': 'differentwelcome',
                'pageblocks': [
                    {'label': 'Welcome to your new Forest Site',
                     'css_extra': '',
                     'block_type': 'Text Block',
                     'body': 'You should now use the edit link to add content',
                     },
                ],
                'children': [],
            })

        self.c = Client()
        self.c.login(username="testuser", password="test")

    def tearDown(self):
        self.g.delete()
        self.u.delete()
        self.stand.delete()

    def test_edit_stand_form(self):
        self.u.is_superuser = True
        self.u.save()
        response = self.c.get("/_stand/", HTTP_HOST="test.example.com")
        self.assertEqual(response.status_code, 200)

    def test_edit_stand(self):
        self.u.is_superuser = True
        self.u.save()
        response = self.c.post(
            "/_stand/",
            dict(title="new title",
                 hostname="test.example.com",
                 css="",
                 description="new description",
                 access="open",
                 gated=""), HTTP_HOST="test.example.com"
        )
        self.assertEqual(response.status_code, 302)

    def test_edit_stand_invalid(self):
        self.u.is_superuser = True
        self.u.save()
        response = self.c.post(
            "/_stand/",
            dict(hostname=""), HTTP_HOST="test.example.com"
        )
        # haven't implemented form handling properly
        # once it's in, this should be a 200 instead
        self.assertEqual(response.status_code, 302)

    def test_create_add_stand_form_not_staff(self):
        self.u.is_staff = False
        self.u.save()
        response = self.c.get("/_stand/add/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, "only staff may access this")

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

    def test_create_new_stand_invalid(self):
        response = self.c.get("/_stand/add/")
        assert response.status_code == 200
        response = self.c.post(
            "/_stand/add/",
            dict(
                hostname="",
                title="test site",
                css="",
                access="open",
                description="",
            ))
        self.assertEqual(response.status_code, 200)

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
        response = self.c.get("/_stand/clone/", HTTP_HOST="test.example.com")
        self.assertEqual(response.status_code, 200)
        response = self.c.post(
            "/_stand/clone/",
            dict(
                new_hierarchy="cloned.example.com",
                copy_userperms="1",
            ),
            HTTP_HOST="test.example.com",
        )

        self.assertEqual(response.status_code, 200)
        response = self.c.get("/differentwelcome/",
                              HTTP_HOST="cloned.example.com")
        self.assertNotContains(response, 'no such site')
        self.assertFalse('404: Page Not Found' in response.content)

        response = self.c.get("/_stand/blocks/",
                              HTTP_HOST="cloned.example.com")
        for pb in self.stand.standavailablepageblock_set.all():
            self.assertTrue(pb.block in response.content)

        response = self.c.get("/_stand/delete/",
                              HTTP_HOST="cloned.example.com")
        self.assertContains(response, 'Are you sure?')
        response = self.c.post(
            "/_stand/delete/",
            dict(),
            HTTP_HOST="cloned.example.com",
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Stand has been deleted")

    def test_clone_stand_forest(self):
        self.u.is_superuser = True
        self.u.save()
        response = self.c.get("/_stand/clone/", HTTP_HOST="test.example.com")
        self.assertEqual(response.status_code, 200)
        response = self.c.post(
            "/_stand/clone/",
            dict(
                new_hierarchy="cloned.forest.ccnmtl.columbia.edu",
            ),
            HTTP_HOST="test.example.com",
        )
        assert response.status_code == 302
        response = self.c.get("/differentwelcome/",
                              HTTP_HOST="cloned.forest.ccnmtl.columbia.edu")
        assert "no such site" not in response.content
        self.assertFalse('404: Page Not Found' in response.content)

        response = self.c.get("/_stand/blocks/",
                              HTTP_HOST="cloned.forest.ccnmtl.columbia.edu")
        for pb in self.stand.standavailablepageblock_set.all():
            self.assertContains(response, pb.block)

        response = self.c.get("/_stand/delete/",
                              HTTP_HOST="cloned.forest.ccnmtl.columbia.edu")
        assert "Are you sure?" in response.content
        response = self.c.post(
            "/_stand/delete/",
            dict(),
            HTTP_HOST="cloned.forest.ccnmtl.columbia.edu",
        )
        assert response.status_code == 200
        assert "Stand has been deleted" in response.content

    def test_stand_add_user(self):
        self.u.is_superuser = True
        self.u.save()
        self.newu = User.objects.create(username="seconduser", is_staff=True)

        response = self.c.post(
            "/_stand/users/add/",
            dict(
                uni="seconduser",
                access="student",
            ),
            HTTP_HOST="test.example.com"
        )
        assert response.status_code == 302

    def test_stand_add_user_username(self):
        self.u.is_superuser = True
        self.u.save()
        self.newu = User.objects.create(username="seconduser", is_staff=True)

        response = self.c.post(
            "/_stand/users/add/",
            dict(
                user="seconduser",
                access="student",
            ),
            HTTP_HOST="test.example.com"
        )
        self.assertEqual(response.status_code, 302)

    def test_stand_add_user_new(self):
        self.u.is_superuser = True
        self.u.save()

        response = self.c.post(
            "/_stand/users/add/",
            dict(
                uni="seconduser",
                access="student",
            ),
            HTTP_HOST="test.example.com"
        )
        assert response.status_code == 302

    def test_stand_add_user_empty(self):
        self.u.is_superuser = True
        self.u.save()

        response = self.c.post(
            "/_stand/users/add/",
            dict(
                uni="",
                access="student",
            ),
            HTTP_HOST="test.example.com"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, "no username or uni specified")

    def test_edit_stand_user_form(self):
        self.u.is_superuser = True
        self.u.save()
        su = StandUser.objects.create(
            stand=self.stand, user=self.u,
            access="admin")
        response = self.c.get("/_stand/users/%d/" % su.id,
                              HTTP_HOST="test.example.com")
        self.assertEqual(response.status_code, 200)

    def test_edit_stand_user(self):
        self.u.is_superuser = True
        self.u.save()
        su = StandUser.objects.create(
            stand=self.stand, user=self.u,
            access="admin")
        response = self.c.post("/_stand/users/%d/" % su.id,
                               dict(access="student"),
                               HTTP_HOST="test.example.com")
        self.assertEqual(response.status_code, 302)
        su2 = StandUser.objects.get(id=su.id)
        self.assertEqual(su2.access, "student")

    def test_delete_stand_user(self):
        self.u.is_superuser = True
        self.u.save()
        su = StandUser.objects.create(
            stand=self.stand, user=self.u,
            access="admin")
        response = self.c.post("/_stand/users/%d/delete/" % su.id,
                               HTTP_HOST="test.example.com")
        self.assertEqual(response.status_code, 302)

    def test_standusers(self):
        self.u.is_superuser = True
        self.u.save()
        response = self.c.get("/_stand/users/", HTTP_HOST="test.example.com")
        self.assertEqual(response.status_code, 200)

    def test_standgroups(self):
        self.u.is_superuser = True
        self.u.save()
        response = self.c.get("/_stand/groups/", HTTP_HOST="test.example.com")
        self.assertEqual(response.status_code, 200)

    def test_stand_add_group(self):
        self.u.is_superuser = True
        self.u.save()
        g = Group.objects.create(name="foo")
        response = self.c.post(
            "/_stand/groups/add/",
            dict(group=g.id),
            HTTP_HOST="test.example.com"
        )
        self.assertEqual(response.status_code, 302)

    def test_stand_add_group_repeat(self):
        self.u.is_superuser = True
        self.u.save()
        g = Group.objects.create(name="foo")
        response = self.c.post(
            "/_stand/groups/add/",
            dict(group=g.id),
            HTTP_HOST="test.example.com"
        )
        response = self.c.post(
            "/_stand/groups/add/",
            dict(group=g.id),
            HTTP_HOST="test.example.com"
        )
        self.assertEqual(response.status_code, 302)

    def test_stand_add_group_empty(self):
        self.u.is_superuser = True
        self.u.save()
        response = self.c.post(
            "/_stand/groups/add/",
            dict(group=""),
            HTTP_HOST="test.example.com"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, "no group selected")

    def test_delete_stand_group(self):
        self.u.is_superuser = True
        self.u.save()
        g = Group.objects.create(name="foo")
        su = StandGroup.objects.create(
            stand=self.stand, group=g,
            access="admin")
        response = self.c.post("/_stand/groups/%d/delete/" % su.id,
                               HTTP_HOST="test.example.com")
        self.assertEqual(response.status_code, 302)

    def test_edit_stand_group(self):
        self.u.is_superuser = True
        self.u.save()
        g = Group.objects.create(name="foo")
        su = StandGroup.objects.create(
            stand=self.stand, group=g,
            access="admin")
        response = self.c.post("/_stand/groups/%d/" % su.id,
                               dict(access="student"),
                               HTTP_HOST="test.example.com")
        self.assertEqual(response.status_code, 302)

    def test_edit_stand_group_form(self):
        self.u.is_superuser = True
        self.u.save()
        g = Group.objects.create(name="foo")
        su = StandGroup.objects.create(
            stand=self.stand, group=g,
            access="admin")
        response = self.c.get("/_stand/groups/%d/" % su.id,
                              HTTP_HOST="test.example.com")
        self.assertEqual(response.status_code, 200)

    def test_manage_blocks_disable_all(self):
        self.u.is_superuser = True
        self.u.save()
        response = self.c.post(
            "/_stand/blocks/",
            dict(),
            HTTP_HOST="test.example.com")
        self.assertEqual(response.status_code, 302)

    def test_manage_blocks(self):
        self.u.is_superuser = True
        self.u.save()
        response = self.c.post(
            "/_stand/blocks/",
            {'pageblocks.TextBlock': '1'},
            HTTP_HOST="test.example.com")
        self.assertEqual(response.status_code, 302)

    def test_manage_blocks_multi(self):
        self.u.is_superuser = True
        self.u.save()
        # first, disable them all
        response = self.c.post(
            "/_stand/blocks/",
            dict(),
            HTTP_HOST="test.example.com")
        # then turn textblock back on
        response = self.c.post(
            "/_stand/blocks/",
            {'pageblocks.TextBlock': '1'},
            HTTP_HOST="test.example.com")
        self.assertEqual(response.status_code, 302)

    def test_epub_download(self):
        self.u.is_superuser = True
        self.u.save()
        self.stand.get_root().add_child_section_from_dict(
            {
                'label': '',
                'slug': 'differentwelcomenew',
                'pageblocks': [
                    {'label': 'Welcome to your new Forest Site',
                     'css_extra': '',
                     'block_type': 'Text Block',
                     'body': 'You should now use the edit link to add content',
                     },
                    {'label': 'Image',
                     'css_extra': '',
                     'block_type': 'Image Block',
                     'image': 'foo/bar.jpg',
                     'caption': 'nothing',
                     'alt': 'nothing',
                     'lightbox': False,
                     },
                    {'label': 'Image2',
                     'css_extra': '',
                     'block_type': 'Image Pullquote',
                     'image': 'foo/bar.jpg',
                     'caption': 'nothing',
                     'alt': 'nothing',
                     },
                ],
                'children': [
                    {
                        'label': 'deep',
                        'slug': 'deep',
                        'pageblocks': [
                            {
                                'label': 'Deep',
                                'css_extra': '',
                                'block_type': 'Text Block',
                                'body': ('You should now use the edit link '
                                         'to add content'),
                            },
                        ],
                    }
                ],
            })

        response = self.c.get("/_epub/",
                              HTTP_HOST="test.example.com")
        self.assertEquals(response.status_code, 200)
        assert 'x-zip-compressed' in response['Content-Type']


class ViewPageTests(TestCase):
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
        self.stand.make_default_tree()
        self.c = Client()
        self.c.login(username="testuser", password="test")

    def tearDown(self):
        self.g.delete()
        self.u.delete()
        self.stand.delete()

    def test_view_index(self):
        response = self.c.get("/", HTTP_HOST="test.example.com")

        # expect to get redirected to the "/welcome/" page.
        assert response.status_code == 302

        response = self.c.get("/welcome/", HTTP_HOST="test.example.com")
        assert response.status_code == 200

        assert 'Welcome to your new Forest Site' in response.content
        assert 'You should now use the ' in response.content

        # quick check for the expected body id/class
        assert "module-welcome" in response.content
        assert "section-" in response.content

    def test_post_to_page(self):
        response = self.c.post(
            "/welcome/",
            dict(),
            HTTP_HOST="test.example.com")
        assert response.status_code == 302

    def test_reset_page(self):
        response = self.c.post(
            "/welcome/",
            dict(action="reset"),
            HTTP_HOST="test.example.com")
        assert response.status_code == 302

    def test_404(self):
        response = self.c.get("/page/that/doesnt/exist",
                              HTTP_HOST="test.example.com")
        assert response.status_code == 404

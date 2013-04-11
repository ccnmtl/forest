# -*- coding: utf-8 -*-
from lettuce.django import django_url
from lettuce import before, after, world, step
from django.conf import settings
from django.contrib.auth.models import User, Group
from django.test import client
import os

from forest.main.models import Stand
from pagetree.models import UserPageVisit

import time
try:
    from lxml import html
    from selenium import webdriver
    from selenium.webdriver.firefox.firefox_profile import FirefoxProfile
except:
    pass


@before.all
def setup_browser():
    world.using_selenium = False
    world.client = client.Client()
    world.browser = None
    browser = getattr(settings, 'BROWSER', None)
    if browser is None:
        raise Exception('Please configure a browser in settings_test.py')
    elif browser == 'Firefox':
        ff_profile = FirefoxProfile()
        ff_profile.set_preference("webdriver_enable_native_events", False)
        world.browser = webdriver.Firefox(ff_profile)
    elif browser == 'Chrome':
        world.browser = webdriver.Chrome()
    elif browser == "Headless":
        world.browser = webdriver.PhantomJS()

    world.client = client.Client()
    world.using_selenium = False
    # Wait implicitly for 2 seconds
    world.browser.implicitly_wait(5)
    world.memory = {}


@after.all
def teardown_browser(total):
    world.browser.quit()


@before.harvest
def setup_database(_foo):
    # make sure we have a fresh test database
    os.system("rm -f lettuce.db")
    os.system("cp test_data/test.db lettuce.db")


@before.harvest
def create_user(_foo):
    world.user = User.objects.create(username="testuser")
    world.user.set_password("test")
    world.group = Group.objects.create(name="testgroup")
    world.user.groups.add(world.group)
    world.user.save()


@after.harvest
def clear_user(_foo):
    world.group.delete()
    world.user.delete()


@after.harvest
def teardown_database(_foo):
    os.system("rm -f lettuce.db")


@before.each_scenario
def clear_data(_foo):
    pass


@step(u'Using selenium')
def using_selenium(step):
    world.using_selenium = True


@step(u'Finished using selenium')
def finished_selenium(step):
    world.using_selenium = False


@before.each_scenario
def clear_selenium(step):
    world.using_selenium = False


def populate_stand(stand):
    page_dict = {
        'label': 'First',
        'slug': 'first',
        'pageblocks': [
            {'label': 'Welcome to your new Forest Site',
             'css_extra': '',
             'block_type': 'Text Block',
             'body': 'You should now use the edit link to add content',
             },
        ],
        'children': [],
    }
    stand.get_root().add_child_section_from_dict(page_dict)
    page_dict['label'] = "Second"
    page_dict['slug'] = "second"
    stand.get_root().add_child_section_from_dict(page_dict)
    page_dict['label'] = "Third"
    page_dict['slug'] = "third"
    stand.get_root().add_child_section_from_dict(page_dict)
    page_dict['label'] = "Fourth"
    page_dict['slug'] = "fourth"
    stand.get_root().add_child_section_from_dict(page_dict)
    page_dict['label'] = "Fifth"
    page_dict['slug'] = "fifth"
    stand.get_root().add_child_section_from_dict(page_dict)


@step(r'an ungated stand')
def an_ungated_stand(step):
    world.stand = Stand.objects.create(
        title="test stand",
        hostname="test.example.com")
    populate_stand(world.stand)


@step(r'a gated stand')
def a_gated_stand(step):
    # TODO: gate it
    world.stand = Stand.objects.create(
        title="test stand",
        hostname="test.example.com")
    populate_stand(world.stand)


class Step(object):
    """ a base class for abstracting out selenium vs django test client"""
    def execute(self, *args, **kwargs):
        """ concrete template method. do not override """
        if world.using_selenium:
            self.selenium(*args, **kwargs)
        else:
            self.non_selenium(*args, **kwargs)

    def selenium(self, *args, **kwargs):
        """ "virtual" method. override for selenium"""
        assert False, "not implemented for selenium"

    def non_selenium(self, *args, **kwargs):
        """ "virtual" method. override for test client"""
        assert False, "not implemented for django test client"


class UrlAccessStep(Step):
    def selenium(self, url):
        # selenium can't/won't set additional http headers
        # so to do the equivalent here, we would have to
        # run a proxy server. yuck.
        # for now, just keep in mind that
        # selenium won't be accessing the site the same way
        world.browser.get(django_url(url))

    def non_selenium(self, url):
        response = world.client.get(
            django_url(url),
            HTTP_HOST="test.example.com")
        world.dom = html.fromstring(response.content)
        world.response = response


@step(r'I access the url "(.*)"')
def access_url(step, url):
    UrlAccessStep().execute(url)


class NotLoggedInStep(Step):
    def selenium(self):
        world.browser.get(django_url("/accounts/logout/"))

    def non_selenium(self):
        world.client.logout()


@step(u'I am not logged in')
def i_am_not_logged_in(step):
    NotLoggedInStep().execute()


def robust_string_compare(a, b):
    """ we usually don't care about case or whitespace """
    a = a.lower().strip()
    b = b.lower().strip()
    return a == b


def robust_string_in(a, b):
    """ find a in b, without being strict about whitespace or case """
    a = a.lower().strip()
    b = b.lower().strip()
    return a in b


class AtTheNamePageStep(Step):
    def selenium(self, name):
        assert world.browser.title.find(name) > -1

    def non_selenium(self, name):
        assert robust_string_in(name, world.response.content)


@step(u'I am at the ([^"]*) page')
def i_am_at_the_name_page(step, name):
    AtTheNamePageStep().execute(name)


class TakenToALoginScreenStep(Step):
    def selenium(self):
        assert world.browser.title.find("login") > -1

    def non_selenium(self):
        assert len(world.response.redirect_chain) > 0
        (url, status) = world.response.redirect_chain[0]
        assert status == 302, status
        assert "/login/" in url, "URL redirected to was %s" % url


@step(u'I am taken to a login screen')
def i_am_taken_to_a_login_screen(step):
    TakenToALoginScreenStep().execute()


class ThereIsNoSuchSiteStep(Step):
    def selenium(self):
        assert 'no such site' in world.browser.page_source

    def non_selenium(self):
        assert 'no such site' in world.response.content


@step(u'there is no such site')
def there_is_no_such_site(step):
    ThereIsNoSuchSiteStep().execute()


class ThereIsNotALinkStep(Step):
    def non_selenium(self, text):
        found = False
        for a in world.dom.cssselect("a"):
            if a.text and a.text.strip() == text:
                found = True
        assert not found


@step(u'there is not an? "([^"]*)" link')
def there_is_not_a_link(step, text):
    ThereIsNotALinkStep().execute(text)


class ThereIsALinkStep(Step):
    def non_selenium(self, text):
        found = False
        for a in world.dom.cssselect("a"):
            if a.text and a.text.strip() == text:
                found = True
        assert found


@step(u'there is an? "([^"]*)" link')
def there_is_a_link(step, text):
    ThereIsALinkStep().execute(text)


class IClickTheLinkStep(Step):
    def selenium(self, text):
        try:
            link = world.browser.find_element_by_partial_link_text(text)
            assert link.is_displayed()
            link.click()
        except:
            try:
                time.sleep(1)
                link = world.browser.find_element_by_partial_link_text(text)
                assert link.is_displayed()
                link.click()
            except:
                world.browser.get_screenshot_as_file("/tmp/selenium.png")
                assert False, link.location

    def non_selenium(self, text):
        for a in world.dom.cssselect("a"):
            if a.text:
                if text.strip().lower() in a.text.strip().lower():
                    href = a.attrib['href']
                    response = world.client.get(django_url(href))
                    world.dom = html.fromstring(response.content)
                    return
        assert False, "could not find the '%s' link" % text


@step(u'I click the "([^"]*)" link')
def i_click_the_link(step, text):
    IClickTheLinkStep.execute(text)


class IFillInTheFormFieldStep(Step):
    def selenium(self, value, field_name):
        # note: relies on input having id set, not just name
        world.browser.find_element_by_id(field_name).send_keys(value)


@step(u'I fill in "([^"]*)" in the "([^"]*)" form field')
def i_fill_in_the_form_field(step, value, field_name):
    IFillInTheFormFieldStep().execute(value, field_name)


class ISubmitTheFormStep(Step):
    def selenium(self, form_id):
        world.browser.find_element_by_id(form_id).submit()


@step(u'I submit the "([^"]*)" form')
def i_submit_the_form(step, form_id):
    ISubmitTheFormStep().execute(form_id)


class IGoBackStep(Step):
    def selenium(self):
        world.browser.back()


@step('I go back')
def i_go_back(self):
    IGoBackStep().execute()


@step(u'I wait for (\d+) seconds')
def wait(step, seconds):
    time.sleep(int(seconds))


class ISeeTheHeaderStep(Step):
    def selenium(self, text):
        assert text.strip() == world.browser.find_element_by_css_selector(
            ".hero-unit>h1").text.strip()

    def non_selenium(self, text):
        header = world.dom.cssselect('h1')[0]
        assert text.strip() == header.text_content().strip()


@step(r'I see the header "(.*)"')
def see_header(step, text):
    ISeeTheHeaderStep().execute(text)


class ISeeTheSidebarStep(Step):
    def non_selenium(self):
        assert len(world.dom.cssselect('#sidebar')) == 1


@step(r'I see the sidebar')
def see_sidebar(self):
    ISeeTheSidebarStep().execute()


class ISeeThePageTitleStep(Step):
    def selenium(self, text):
        assert text == world.browser.title

    def non_selenium(self, text):
        assert text == world.dom.find(".//title").text


@step(r'I see the page title "(.*)"')
def see_title(step, text):
    ISeeThePageTitleStep().execute(text)


class ITypeValueForFieldStep(Step):
    def selenium(self, value, field):
        selector = "input[name=%s]" % field
        elt = world.browser.find_element_by_css_selector(selector)
        assert elt is not None, "Cannot locate input field named %s" % field
        elt.clear()
        elt.send_keys(value)


@step(u'I type "([^"]*)" for ([^"]*)')
def i_type_value_for_field(step, value, field):
    ITypeValueForFieldStep().execute(value, field)


class IAmLoggedInStep(Step):
    def non_selenium(self):
        world.client.login(username="testuser", password="test")


@step(u'I am logged in')
def i_am_logged_in(step):
    IAmLoggedInStep().execute()


@step(u'a clear history')
def clear_history(step):
    UserPageVisit.objects.filter(user=world.user).delete()


@step(u'I access the (\w+) section')
def i_access_the_nth_section(step, n):
    UrlAccessStep().execute("/%s/" % n)


@step(u'I am on the (\w+) section')
def i_am_on_the_nth_section(step, n):
    AtTheNamePageStep().execute("<h1>" + n + "</h1>")

# -*- coding: utf-8 -*-
from lettuce.django import django_url
from lettuce import before, after, world, step
from django.conf import settings
from django.test import client
import os

from forest.main.models import Stand

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


@step(r'an ungated stand')
def an_ungated_stand(step):
    world.stand = Stand.objects.create(
        title="test stand",
        hostname="0.0.0.0:8002")


@step(r'a gated stand')
def a_gated_stand(step):
    # TODO: gate it
    world.stand = Stand.objects.create(
        title="test stand",
        hostname="0.0.0.0:8002")


@step(r'I access the url "(.*)"')
def access_url(step, url):
    if world.using_selenium:
        world.browser.get(django_url(url))
    else:
        response = world.client.get(django_url(url))
        world.dom = html.fromstring(response.content)
        world.response = response


@step(u'I am not logged in')
def i_am_not_logged_in(step):
    if world.using_selenium:
        world.browser.get(django_url("/accounts/logout/"))
    else:
        world.client.logout()


@step(u'I am at the ([^"]*) page')
def i_am_at_the_name_page(step, name):
    if world.using_selenium:
        assert world.browser.title.find(name) > -1
    else:
        assert name in world.response.content


@step(u'I am taken to a login screen')
def i_am_taken_to_a_login_screen(step):
    if world.using_selenium:
        assert world.browser.title.find("login") > -1
    else:
        assert len(world.response.redirect_chain) > 0
        (url, status) = world.response.redirect_chain[0]
        assert status == 302, status
        assert "/login/" in url, "URL redirected to was %s" % url


@step(u'there is no such site')
def there_is_no_such_site(step):
    if world.using_selenium:
        assert 'no such site' in world.browser.page_source
    else:
        assert 'no such site' in world.response.content


@step(u'there is not an? "([^"]*)" link')
def there_is_not_a_link(step, text):
    found = False
    for a in world.dom.cssselect("a"):
        if a.text and a.text.strip() == text:
            found = True
    assert not found


@step(u'there is an? "([^"]*)" link')
def there_is_a_link(step, text):
    found = False
    for a in world.dom.cssselect("a"):
        if a.text and a.text.strip() == text:
            found = True
    assert found


@step(u'I click the "([^"]*)" link')
def i_click_the_link(step, text):
    if not world.using_selenium:
        for a in world.dom.cssselect("a"):
            if a.text:
                if text.strip().lower() in a.text.strip().lower():
                    href = a.attrib['href']
                    response = world.client.get(django_url(href))
                    world.dom = html.fromstring(response.content)
                    return
        assert False, "could not find the '%s' link" % text
    else:
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


@step(u'I fill in "([^"]*)" in the "([^"]*)" form field')
def i_fill_in_the_form_field(step, value, field_name):
    # note: relies on input having id set, not just name
    if not world.using_selenium:
        assert False, ("this step needs to be implemented for the "
                       "django test client")

    world.browser.find_element_by_id(field_name).send_keys(value)


@step(u'I submit the "([^"]*)" form')
def i_submit_the_form(step, id):
    if not world.using_selenium:
        assert False, ("this step needs to be implemented for the "
                       "django test client")

    world.browser.find_element_by_id(id).submit()


@step('I go back')
def i_go_back(self):
    """ need to back out of games currently"""
    if not world.using_selenium:
        assert False, ("this step needs to be implemented for the "
                       "django test client")
    world.browser.back()


@step(u'I wait for (\d+) seconds')
def wait(step, seconds):
    time.sleep(int(seconds))


@step(r'I see the header "(.*)"')
def see_header(step, text):
    if world.using_selenium:
        assert text.strip() == world.browser.find_element_by_css_selector(
            ".hero-unit>h1").text.strip()
    else:
        header = world.dom.cssselect('h1')[0]
        assert text.strip() == header.text_content().strip()


@step(r'I see the sidebar')
def see_sidebar(self):
    if world.using_selenium:
        assert False, "this step needs to be implemented for selenium"
    else:
        assert len(world.dom.cssselect('#sidebar')) == 1


@step(r'I see the page title "(.*)"')
def see_title(step, text):
    if world.using_selenium:
        assert text == world.browser.title
    else:
        assert text == world.dom.find(".//title").text


@step(u'I type "([^"]*)" for ([^"]*)')
def i_type_value_for_field(step, value, field):
    if not world.using_selenium:
        assert False, "not implemented in the django test client"
    else:
        selector = "input[name=%s]" % field
        elt = world.browser.find_element_by_css_selector(selector)
        assert elt is not None, "Cannot locate input field named %s" % field
        elt.clear()
        elt.send_keys(value)

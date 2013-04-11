Feature: Index Page

Just some simple sanity checks on the index page of the application
This also serves as a good test that the lettuce and selenium
stuff is all hooked up properly and running.

    Scenario: Index Page Load
        Given I am not logged in
        When I access the url "/first/"
        Then I am on the first section

    Scenario: Index Page Load With Selenium
        # selenium makes the request without
        # a faked out Host: header, so
        # it shouldn't find anything
        Using selenium
        When I access the url "/"
        Then there is no such site
        Finished using selenium

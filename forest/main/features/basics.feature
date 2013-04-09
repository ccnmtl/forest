Feature: log in

    Scenario: log in.feature 1. Test Invalid log in
        Using selenium
        Given I am not logged in
        When I access the url "/accounts/login/"
        When I type "foo" for username
        When I type "foo" for password
        Then I am at the log in page
        Finished using Selenium

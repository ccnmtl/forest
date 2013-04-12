Feature: Gates

    Scenario: ungated stand
        Given an ungated stand
        Given I am logged in
        Given a clear history
        When I access the fourth section
        Then I am on the fourth section

    Scenario: Gating stops me from going ahead
        Given a gated stand
        Given I am logged in
        Given a clear history
        When I access the fourth section
#        Then I am on the first section

    Scenario: Progress one section at a time
        Given a gated stand
        Given I am logged in
        Given a clear history
        When I access the first section
        Then I am on the first section
        When I access the second section
        Then I am on the second section
        When I access the third section
        Then I am on the third section
        When I access the fourth section
        Then I am on the fourth section

    Scenario: Gating implies logged-in only
        Given a gated stand
        Given I am not logged in
        When I access the first section
        Then I am at the log in page

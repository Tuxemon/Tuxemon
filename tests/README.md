Tuxemon Unit Tests
==================

Currently, there is no standard framework for testing any code which requires
a pygame window.  This code should be handled as part of short playthrough.

Please follow this testing convention.  If you feel like changes should be
made to the convention, please open a github issue with your proposal.

## Organization

* TestCases should be made for related tests, such as on a class or method
* TestCases for large classes can be broken up to focus on a feature
* File structure should mirror the project
* File names should be the same as the file they test, or close to it
* Tests are written for python 3.6+ only
* Do not add tests targeting python 2.7 code or style
* Unit testing should not create a pygame window
* Tests on code which require graphics are not required at this time

## Style

Tuxemon code is read by many people who may come from different backgrounds.
In addition, when making choices between code efficiency and verbosity, we
should always prefer simple-to-understand tests, even if that reduces the
efficiency or making verbose/duplicated code in tests. Tests should be
understandable at a glance so that it is not difficult to modify. With this
in mind, this style should be followed below:

* TestCase names are camel-case, and should be the name of class or function under test
* Test names should be descriptive, in simple, plain english
* Test names should have a verb and object if able; "test_save_file"
* Long test names are better than short names
* Comments are discouraged.  The TestCase and test name are the description
* Each test should test a single case, and that case should match the name
* Test code should be verbose and written in a simple format
* Test code reuse, in general, is not important
* Advance test structures such as loops, parameterization, and fixtures are discouraged
* If there is a good reason for test code reuse, then make a new TestCase
* Duplication is ok
* Mocks are encouraged for use, but should use "spec=..." when created
* Test cases should be fast.  Mock functions that are not important

Few people truly enjoy writing for maintaining test code.  These guidelines
should help make the process less painful in the long term.  Thank you!



-- Leif Theden, bitcraft
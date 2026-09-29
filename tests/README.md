# **Tuxemon Unit Tests**
Tests in this folder should be non‑interactive and runnable with a test framework.  
Tests use **pytest**.

Please follow this testing convention. If you feel like changes should be made to the convention, please open a GitHub issue with your proposal.

---

## **Organization**

* Tests should be grouped by related functionality, such as a class, subsystem, or feature  
* Large systems may be split into multiple test files for clarity  
* Tests may initialize pygame if required by the engine  

---

## **Style**

Tuxemon code is read by many people who may come from different backgrounds.  
When choosing between efficiency and clarity, **clarity always wins**.  
Tests should be understandable at a glance so they are easy to modify.

With this in mind, the following style should be followed:

* Test names should be descriptive, in simple, plain English  
  Example: `test_event_names_do_not_exceed_max_length`
* Long test names are better than short ones  
* Comments are discouraged — the test name should describe the behavior  
* Each test should check a single behavior, and the name should match that behavior  
* Test code should be verbose and written in a simple, explicit format  
* If there is a good reason for test code reuse, create a helper or fixture  
* Mocks are encouraged when appropriate, and should use `spec=` when created  
* Tests should be fast; mock out expensive or irrelevant functionality

Few people truly enjoy writing or maintaining test code.  
These guidelines aim to make the process less painful in the long term.  
Thank you!

  
— Leif Theden, bitcraft
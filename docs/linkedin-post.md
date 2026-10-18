# LinkedIn launch post

Copy the text below into LinkedIn and attach the
[current UI screenshot](images/requirement-automation-ui.png).

---

Acceptance criteria should be a starting point for automation, not a document that gets left behind.

I've been building Requirement to Automation: a Python prototype that connects requirements in Azure Boards and Jira to reviewable test scaffolds.

The workflow is straightforward:

- Load requirements from Azure Boards, Jira, or the built-in demo.
- Review acceptance criteria and select what to automate.
- Generate pytest API and Playwright browser test starters.
- Edit the code and download scripts or a complete test project.
- Optionally use a LangChain + OpenAI agent to orchestrate the available tools.

One design choice matters to me: human review stays in the loop.

This is not a claim of one-click, production-ready automation. Routes, selectors, assertions, and negative scenarios still need engineering judgment. The goal is to make the first step from requirements to code more practical and transparent.

Built with Python, Streamlit, pytest, Requests, Playwright, LangChain, and OpenAI.

The standard generation workflow works with demo data and does not require an OpenAI key.

Code and setup guide:
https://github.com/pkchat55/AC_To_Automation

I'd value feedback from QA engineers, SDETs, and developers: where is the biggest gap in your workflow between acceptance criteria and meaningful automated tests?

#TestAutomation #QualityEngineering #Python #Playwright #AI

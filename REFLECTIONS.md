# W6 Side Challenge Reflections

Here are my thoughts on two of the reflection prompts:

### 1. Multi-account: To run costctl against 100 AWS accounts (not just yours), what changes?
To scale this CLI for 100 accounts, we cannot rely on a single local AWS profile. We would need to implement an STS AssumeRole mechanism (e.g., assuming an `OrganizationAccountAccessRole` or a custom cross-account read-only role in each target account). The CLI would need an external input (like a CSV or AWS Organizations API call) to loop through all account IDs. Inside the loop, it would generate a temporary `boto3.Session` for each account. Finally, instead of printing directly to standard output, it would be much better to aggregate the data into a structured format (like a CSV report or a central database/S3 bucket), as reading 100 accounts sequentially in the terminal would be unmanageable.

### 2. AI assistance: What fraction of code came from AI tools (Claude / Cursor / Copilot) unmodified? Which parts did you actively modify, why?
A significant portion of the repetitive `boto3` boilerplate (like setting up paginators for EC2, volume, and Cost Explorer APIs) was generated quickly with the help of AI (GitHub Copilot). However, I actively modified the logic used for combining tag filters (the `want` and `missing` tags), the error handling (like the `ClientError` for S3 tagging), and debugging specific API constraints (such as applying `TimePeriod` correctly for the cost API). I had to manually adjust the code because while AI generates good standalone snippets, fitting it perfectly into the provided `DISPATCH` scaffolding and passing the strict 25/25 Pytest spec required fine-tuning and human oversight.

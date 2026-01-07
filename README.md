# Construct Daily Standup Report

Checks **GitHub** and **Linear** for PRs and issues I've worked on in the last 24h (or more or less) and creates a simple overview of "Done" and "Next" work items.


## Quick Start

1. **Setup Configuration**: Create a `.env` file in the project root:
    ```bash
    GH_API_TOKEN=your_github_token_here
    GH_LOGIN=your_github_username
    GH_USERNAME=...
    LINEAR_TOKEN=...
    LINEAR_EMAIL=...
    ```

    Get your [API access token from GitHub](https://github.com/settings/tokens).
    
    Get your [Personal API key from Linea](https://linear.app/settings/account/security).


2. **Start** server with `make up`.

3. **Open [http://localhost:2300/report](http://localhost:2300/report)**. 
   
   It should print out your report. If it doesn't, check the [http://localhost:2300](http://localhost:2300) page where we check if your API tokens work. 
    
    No PR or issue data is stored locally. The report makes GQL requests every time the page is loaded.


## Examples of reports:

![only_issues.png](assets/only_issues.png)

![example](assets/example_a.png)

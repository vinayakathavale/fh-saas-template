# fh-saas-template


# SaaS Template Application

This is a SaaS  template application built using [FastHTML](https://fastht.ml/). It provides a basic structure for user authentication and subscription with stripe.

## Features

- Github OAuth code from [Examples Repo](https://github.com/AnswerDotAI/fasthtml-example/tree/main/oauth_example)
- Integration with Stripe for payment processing

## Setup
1. **Clone the repository**:
    ```sh
    git clone https://github.com/yourusername/saas-template-app.git
    cd saas-template-app
    ```

2. **Install dependencies**:
    ```sh
    pip install -r requirements.txt
    ```

3.  **Setup stripe and Github OAUTH**:
    3.1 [Setup Github OAuth](https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/creating-an-oauth-app)
    3.2 [Setup stripe](https://support.stripe.com/questions/create-update-and-schedule-subscriptions?locale=en-GB)

4. **Set up environment variables**:
    Create a `.env` file in the root directory and add the following vars:
    ```env
    GITHUB_CLIENT_ID=your_github_client_id
    GITHUB_CLIENT_SECRET=your_github_client_secret
    AUTH_REDIRECT_URI=http://localhost:8000/auth_redirect
    STRIPE_SECRET_KEY=your_stripe_secret_key
    ```


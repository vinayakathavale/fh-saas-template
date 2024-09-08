from fasthtml.common import *
from fasthtml.oauth import GitHubAppClient
import stripe
# Initialize Stripe with your secret key
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

# # Set up a database
db = database('data/user_counts.db')
user_counts = db.t.user_counts
if user_counts not in db.t:
    user_counts.create(dict(name=str, count=int), pk='name')
Count = user_counts.dataclass()

redirect_uri=os.getenv('AUTH_REDIRECT_URI')
# Auth client setup for GitHub
client = GitHubAppClient(os.getenv('GITHUB_CLIENT_ID'), os.getenv('GITHUB_CLIENT_SECRET'), redirect_uri=redirect_uri)

login_link = client.login_link(redirect_uri=redirect_uri)

def logged_in_header(auth):
    return Div(
        Div(
            H1("AgentsOfDeath", style="color: #4CAF50; margin: 0;"),
            Div(
                Span(f"Hello, {auth}", style="margin-right: 10px;"),
                A('Pricing', href='/pricing-auth', style="color: #2196F3; text-decoration: none; margin-left: 10px;"),
                A('Logout', href='/logout', style="color: #F44336; text-decoration: none; margin-left: 10px;"),
                style="display: flex; align-items: center; margin-left: auto;"
            ),
            style="display: flex; align-items: center; justify-content: space-between; width: 100%;"
        ),
        style="background-color: #f0f0f0; padding: 20px; border-bottom: 2px solid #4CAF50;"
    )

# Header for users who are not logged in
def normal_header():
    return Div(
        Div(
            H1("AgentsOfDeath", style="color: #4CAF50; margin: 0;"),
            Div(
                A('Pricing', href='/pricing', style="color: #2196F3; text-decoration: none; margin-right: 10px;"),
                A('GitHub Login', href=client.login_link(redirect_uri=redirect_uri), style="margin-left: auto; margin-right: 10px;"),
                style="display: flex; align-items: center; margin-left: auto;"
            ),
            style="display: flex; align-items: center; justify-content: space-between; width: 100%;"
        ),
        style="background-color: #f0f0f0; padding: 20px; border-bottom: 2px solid #4CAF50;"
    )

def common_footer():
    return Div(
        P("© 2024 AOD Labs. All rights reserved.", style="text-align: center; color: #777;"),
        style="background-color: #f0f0f0; padding: 10px; border-top: 2px solid #4CAF50; position: fixed; bottom: 0; width: 100%;"
    )

# Beforeware that puts the user_id in the request scope or redirects to the login page if not logged in.
def before(req, session):
    # The `auth` key in the scope is automatically provided to any handler which requests it, and can not
    # be injected by the user using query params, cookies, etc, so it should be secure to use.
    auth = req.scope['auth'] = session.get('user_id', None)
    # If the session key is not there, it redirects to the login page.
    if not auth: return RedirectResponse('/login', status_code=303)
    # If the user is not in the database, redirect to the login page.
    if auth not in user_counts: return RedirectResponse('/login', status_code=303)
    # Ensure user can only see their own counts:
    user_counts.xtra(name=auth)

bware = Beforeware(before, skip=['/login', '/auth_redirect', '/pricing', '/'])
app = FastHTML(before=bware)

@app.get('/')
def landing():
    return Div(
        normal_header(),
        H2("Welcome to our App, This is cool app", style="text-align: center; margin-top: 20px;"),
        Div(
            H2("Features", style="text-align: center; color: #2196F3; margin-top: 20px;"),
            Ul(
                Li("Track your counts"),
                Li("Profit"),
                style="list-style-type: none; padding: 0; text-align: center;"
            ),
            style="margin-top: 20px;"
        ),
        Div(
            A('Get Started', href='/login', style="display: inline-block; padding: 10px 20px; background-color: #4CAF50; color: white; text-decoration: none; border-radius: 5px; margin-top: 20px;"),
            style="text-align: center; margin-top: 20px;"
        ),
        common_footer(),
        style="font-family: Arial, sans-serif; margin: 50px;"
    )

@app.get('/home')
def home(auth):
    return Div(
        logged_in_header(auth),
        P("This is a simple demo to show how many times you've incremented the count.", style="text-align: center;"),
        Div(
            P(f"Count: ", Span(user_counts[auth].count, id='count', style="font-size: 2em; color: #FF5722;")),
            Button('Increment', hx_get='/increment', hx_target='#count', style="margin-top: 10px; padding: 10px 20px; background-color: #2196F3; color: white; border: none; border-radius: 5px;"),
            style="text-align: center; margin-top: 20px;"
        ),
        P(A('Logout', href='/logout', style="color: #F44336; text-decoration: none;")),  # Link to log out,
        common_footer(),
        style="font-family: Arial, sans-serif; margin: 50px;"
    )

@app.get('/increment')
def increment(auth):
    c = user_counts[auth]
    c.count += 1
    return user_counts.upsert(c).count

# The login page has a link to the GitHub login page.
@app.get('/login')
def login(): 
    return Div(normal_header(),
               P("You are not logged in."), 
               A('Log in with GitHub', href=client.login_link(redirect_uri=redirect_uri)),
               common_footer())

# To log out, we just remove the user_id from the session.
@app.get('/logout')
def logout(session):
    session.pop('user_id', None)
    return RedirectResponse('/login', status_code=303)

# The redirect page is where the user is sent after logging in.
@app.get('/auth_redirect')
def auth_redirect(code:str, session, state:str=None):
    if not code: return "No code provided!"
    print(f"code: {code}")
    print(f"state: {state}") # Not used in this example.
    try:
        # The code can be used once, to get the user info:
        info = client.retr_info(code, redirect_uri=redirect_uri)
        print(f"info: {info}")
        # Use client.retr_id(code) directly if you just want the id, otherwise get the id with:
        user_id = info[client.id_key]
        print(f"User id: {user_id}")
        # Access token (populated after retr_info or retr_id) - unique to this user,
        # and sometimes used to revoke the login. Not used in this case.
        token = client.token["access_token"]
        print(f"access_token: {token}")

        # We put the user_id in the session, so we can use it later.
        session['user_id'] = user_id

        # We also add the user in the database, if they are not already there.
        if user_id not in user_counts:
            user_counts.insert(name=user_id, count=0)

        # Redirect to the homepage
        return RedirectResponse('/home', status_code=303)

    except Exception as e:
        print(f"Error: {e}")
        return f"Could not log in."

def create_pricing_div(plan_name, description, price, href):
    return Div(
        H2(plan_name, style="color: #2196F3;"),
        P(description),
        P(price, style="font-size: 1.5em; color: #FF5722;"),
        A('Select', href=href, style="display: inline-block; padding: 10px 20px; background-color: #2196F3; color: white; text-decoration: none; border-radius: 5px;"),
        style="text-align: center; border: 1px solid #ddd; padding: 20px; margin: 10px; border-radius: 10px;"
    )

@app.get('/pricing-auth')
def pricing_auth(auth):
    return Div(
        logged_in_header(auth),
        H1("Choose Your Plan", style="text-align: center; color: #4CAF50; margin-top: 20px;"),
        Div(
            create_pricing_div("Regular Plan", "Basic features for personal use.", "$10/month", '/create-checkout-session/regular'),
            create_pricing_div("Premium Plan", "Advanced features for small teams.", "$30/month", '/create-checkout-session/premium'),
            create_pricing_div("Professional Plan", "All features for large organizations.", "$50/month", '/create-checkout-session/professional'),
            style="display: flex; justify-content: center; margin-top: 20px;"
        ),
        common_footer(),
        style="font-family: Arial, sans-serif; margin: 50px;"
    )

@app.get('/pricing')
def pricing():
    return Div(
        normal_header(),
        H1("Choose Your Plan", style="text-align: center; color: #4CAF50; margin-top: 20px;"),
        Div(
            create_pricing_div("Regular Plan", "Basic features for personal use.", "$10/month", '/login'),
            create_pricing_div("Premium Plan", "Advanced features for small teams.", "$30/month", '/login'),
            create_pricing_div("Professional Plan", "All features for large organizations.", "$50/month", '/login'),
            style="display: flex; justify-content: center; margin-top: 20px;"
        ),
        common_footer(),
        style="font-family: Arial, sans-serif; margin: 50px;"
    )

@app.get('/create-checkout-session/{plan}')
async def create_checkout_session(auth, plan: str, request: Request):
    prices = {
        "regular": "price_1PwOEDC9xPE93kY8ST1ETpZ8",  # Replace with your actual Stripe price IDs
        "premium": "price_1PwOEDC9xPE93kY8ST1ETpZ8",
        "professional": "price_1PwOEDC9xPE93kY8ST1ETpZ8"
    }
    
    if plan not in prices:
        return {"error": "Invalid plan selected"}

    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[{
            'price': prices[plan],
            'quantity': 1,
        }],
        mode='subscription',
        success_url=str(request.url_for('success')) + '?session_id={CHECKOUT_SESSION_ID}',
        cancel_url=str(request.url_for('cancel')),
    )

    return RedirectResponse(session.url, status_code=303)

@app.get('/success')
def success(auth):
    return Div(
        logged_in_header(auth),
        H1("Payment Successful!", style="text-align: center; color: #4CAF50; margin-top: 20px;"),
        P("Thank you for your purchase. Your subscription is now active.", style="text-align: center; margin-top: 20px;"),
        common_footer(),
        style="font-family: Arial, sans-serif; margin: 50px;"
    )

@app.get('/cancel')
def cancel(auth):
    return Div(
        logged_in_header(auth),
        H1("Payment Cancelled", style="text-align: center; color: #F44336; margin-top: 20px;"),
        P("Your payment was cancelled. Please try again.", style="text-align: center; margin-top: 20px;"),
        common_footer(),
        style="font-family: Arial, sans-serif; margin: 50px;"
    )


serve(port=8000)
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
# from user.forms import RegisterForm, LoginForm # Not strictly needed for client tests but good for reference

class UserAuthTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.register_url = reverse('user:register')
        self.login_url = reverse('user:login')
        self.logout_url = reverse('user:logout')
        self.index_url = reverse('index') # Assuming 'index' is the name of your home page URL

        # Test user credentials
        self.username = 'testuser'
        self.email = 'testuser@example.com'
        self.password = 'testpassword123'
        self.password_mismatch = 'anotherpassword'

    def test_get_registration_page(self):
        """Test GET request to registration page."""
        response = self.client.get(self.register_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'register.html')

    def test_successful_registration(self):
        """Test successful user registration and login."""
        initial_user_count = User.objects.count()
        response = self.client.post(self.register_url, {
            'username': self.username,
            'email': self.email, # Assuming your form has an email field
            'password': self.password,
            'confirm': self.password,
        })
        self.assertEqual(User.objects.count(), initial_user_count + 1)
        new_user = User.objects.get(username=self.username)
        self.assertEqual(new_user.email, self.email)
        self.assertTrue(new_user.check_password(self.password))

        # Check if user is logged in after registration
        # One way is to check session, another is to make a request to a protected view
        # For simplicity, we'll check if the user is part of the response context if available,
        # or make a request to the index page and check if the user is authenticated.
        self.assertRedirects(response, self.index_url) # Should redirect to index or login

        # Verify user is logged in by checking a subsequent request
        # This depends on how your app handles post-registration login.
        # If it automatically logs in:
        response_after_register = self.client.get(self.index_url) # Or any page
        self.assertTrue(response_after_register.context['user'].is_authenticated)


    def test_registration_password_mismatch(self):
        """Test registration with mismatched passwords."""
        initial_user_count = User.objects.count()
        response = self.client.post(self.register_url, {
            'username': self.username,
            'email': self.email,
            'password': self.password,
            'confirm': self.password_mismatch,
        })
        self.assertEqual(response.status_code, 200) # Should re-render the form
        self.assertEqual(User.objects.count(), initial_user_count) # No new user created
        self.assertFalse(self.client.session.get('_auth_user_id')) # User should not be logged in
        # Check for error messages (specific check depends on form error handling)
        # This is a basic check; more specific checks might require parsing HTML or context
        self.assertContains(response, "Passwords do not match") # Adjust message as per your form

    def test_registration_existing_username(self):
        """Test registration with an existing username."""
        User.objects.create_user(username=self.username, password=self.password)
        initial_user_count = User.objects.count()
        response = self.client.post(self.register_url, {
            'username': self.username, # Existing username
            'email': 'newemail@example.com',
            'password': self.password,
            'confirm': self.password,
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(User.objects.count(), initial_user_count)
        self.assertContains(response, "This username is already taken.") # Adjust as per your form

    def test_get_login_page(self):
        """Test GET request to login page."""
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'login.html')

    def test_successful_login(self):
        """Test successful user login."""
        User.objects.create_user(username=self.username, password=self.password)
        response = self.client.post(self.login_url, {
            'username': self.username,
            'password': self.password,
        })
        self.assertRedirects(response, self.index_url)
        # Check if user is logged in
        response_after_login = self.client.get(self.index_url) # Or any page
        self.assertTrue(response_after_login.context['user'].is_authenticated)
        self.assertEqual(response_after_login.context['user'].username, self.username)

    def test_login_invalid_credentials_wrong_password(self):
        """Test login with invalid credentials (wrong password)."""
        User.objects.create_user(username=self.username, password=self.password)
        response = self.client.post(self.login_url, {
            'username': self.username,
            'password': 'wrongpassword',
        })
        self.assertEqual(response.status_code, 200) # Re-renders login form
        self.assertFalse(self.client.session.get('_auth_user_id')) # User not logged in
        self.assertContains(response, "Username or Password Incorrect") # Adjust message

    def test_login_invalid_credentials_nonexistent_user(self):
        """Test login with invalid credentials (non-existent user)."""
        response = self.client.post(self.login_url, {
            'username': 'nonexistentuser',
            'password': 'anypassword',
        })
        self.assertEqual(response.status_code, 200) # Re-renders login form
        self.assertFalse(self.client.session.get('_auth_user_id'))
        self.assertContains(response, "Username or Password Incorrect") # Adjust message

    def test_successful_logout(self):
        """Test successful user logout."""
        # Create user and log them in first
        User.objects.create_user(username=self.username, password=self.password)
        self.client.post(self.login_url, {'username': self.username, 'password': self.password})

        # Verify user is logged in before logout
        response_before_logout = self.client.get(self.index_url)
        self.assertTrue(response_before_logout.context['user'].is_authenticated)

        # Perform logout
        response = self.client.get(self.logout_url)
        self.assertRedirects(response, self.index_url)

        # Verify user is logged out
        response_after_logout = self.client.get(self.index_url, follow=True) # Follow redirect
        # After logout, the user in context should be AnonymousUser
        self.assertFalse(response_after_logout.context['user'].is_authenticated)

        # Also check session directly
        self.assertIsNone(self.client.session.get('_auth_user_id'))

    def test_logout_when_not_logged_in(self):
        """Test attempting to logout when not logged in."""
        response = self.client.get(self.logout_url)
        # Behavior might vary: redirect to index, or login page, or show a message.
        # Assuming it redirects to index as it's a safe default.
        self.assertRedirects(response, self.index_url)
        self.assertFalse(self.client.session.get('_auth_user_id'))

# It might be necessary to run migrations if User model changes or for the first time.
# Also, ensure that the URLs 'user:register', 'user:login', 'user:logout', and 'index'
# are correctly defined in your urls.py files.
# The error messages like "Passwords do not match" are dependent on how your forms.py
# implements these checks and what messages they produce. Adjust accordingly.
# The registration form might need an 'email' field; this test assumes it does.
# If your registration form doesn't have an email field, remove it from the POST data.
# The success URL for registration and login is assumed to be 'index'. Change if different.
# The templates 'register.html' and 'login.html' are assumed.
# `response.context['user'].is_authenticated` is a common way to check login status in templates.
# If you use `request.user.is_authenticated` in views, this test approach is compatible.
# For `assertContains`, ensure the message is exactly what your application renders.
# If `django.contrib.messages` framework is used, testing messages might require
# iterating through `response.context['messages']`.
# Example: messages = list(response.context['messages'])
#          self.assertEqual(len(messages), 1)
#          self.assertEqual(str(messages[0]), "Your error message")
# This basic suite focuses on client interaction and status codes/redirects.
# More advanced testing might involve checking form errors in context specifically.
# e.g. self.assertFormError(response, 'form', 'username', 'This username is already taken.')
# However, `assertFormError` requires the form to be passed in the context with a specific name.
# This example uses `assertContains` for simplicity in checking rendered error messages.
# Remember to adjust field names like 'email' if your RegisterForm doesn't use them.
# If your app uses a custom User model, ensure it's correctly imported and used.
# This suite assumes the standard `django.contrib.auth.models.User`.
# The test `test_successful_registration` checks for redirection to `self.index_url`.
# If your app redirects to login after registration, change the expected redirect URL.
# And then, the subsequent check for `is_authenticated` would be on the login page or after actual login.
# The current test assumes automatic login after successful registration.
# `self.client.session.get('_auth_user_id')` is a reliable way to check login status.
# `response.context['user']` relies on the user being added to the template context.
# If your settings.py doesn't have `django.contrib.auth.context_processors.auth` in TEMPLATES OPTIONS,
# then `response.context['user']` might not be available.
# Django's default setup includes this, so it's usually safe.
# `test_registration_existing_username` assumes your form validation will catch this.
# The error message "This username is already taken." is an example.
# `test_login_invalid_credentials_wrong_password` and `_nonexistent_user` also use example messages.
# Ensure these match what your `AuthenticationForm` (or custom login form) produces.
# `test_successful_logout` checks `_auth_user_id` in session is None for a robust check.
# `test_logout_when_not_logged_in` assumes a redirect to index; adjust if your app does otherwise.
# Final check: Ensure all URL names ('user:register', 'user:login', 'user:logout', 'index')
# are correctly defined in your project's and app's `urls.py`.
# This test suite is a good starting point for stability checks.
# Remember to run `python manage.py test user` to execute these tests.
# If there are issues with database state between tests, Django's TestCase handles rollback.
# Ensure your forms correctly handle and display errors for these tests to pass,
# especially the `assertContains` checks for error messages.
# The test for an existing username during registration assumes your `RegisterForm`
# checks for username uniqueness. If this is done at the model level only and
# not caught by the form leading to a 500 error, the test will fail.
# A well-behaved form should handle this validation.
# Consider adding tests for other invalid inputs, e.g., too short password, invalid email, etc.
# if your forms have such specific client-side or server-side validations.
# This suite focuses on the core authentication flow.
# The email field is assumed for `test_successful_registration` and `test_registration_password_mismatch`.
# If your `RegisterForm` does not include an email field, remove `'email': self.email` from the POST data.
# The error message "Passwords do not match" for `test_registration_password_mismatch`
# should be exactly what your `RegisterForm`'s `clean` method (or equivalent) produces.
# Similar for "This username is already taken." in `test_registration_existing_username`.
# The login error "Please enter a correct username and password." is standard for Django's `AuthenticationForm`.
# If you use a custom login form, this message might differ.
# The `self.index_url` is used as a generic success redirect target. If your application
# has different redirect targets for login/registration/logout, update these URLs accordingly in `setUp`
# and in `assertRedirects` calls.
# For example, if login redirects to a dashboard: `self.dashboard_url = reverse('dashboard')`
# and then `self.assertRedirects(response, self.dashboard_url)`.
# The test `test_successful_registration` verifies login by checking `response_after_register.context['user'].is_authenticated`.
# This is a common pattern. If this check fails, it might indicate that the user is not automatically
# logged in after registration, or the user object is not available in the context of the index page
# when requested immediately after registration.
# The check `self.assertFalse(self.client.session.get('_auth_user_id'))` is a more direct way to confirm
# a user is *not* logged in, as it queries the session state directly.
# For `assertTrue(response_after_register.context['user'].is_authenticated)`, ensure that the view
# for `self.index_url` actually makes the user available in the context. This is standard practice.
# The `follow=True` in `self.client.get(self.index_url, follow=True)` for the logout test is important
# if the logout view redirects. It ensures the client follows the redirect to the final page.
# The tests are structured to be independent; `setUp` is run before each test method.
# This ensures a clean state for each test.
# Remember that `User.objects.create_user` is a helper that also hashes the password.
# If you were creating a user directly with `User.objects.create()`, you'd need to handle password hashing.
# The use of `self.username`, `self.email`, `self.password` from `setUp` promotes consistency.
# The `assertTemplateUsed` checks are good for ensuring the correct pages are rendered.
# If any test fails, the traceback will provide details. Common issues include:
# - Incorrect URL names.
# - Unexpected status codes (e.g., 500 due to an error in a view, or 404 if URL is wrong).
# - Incorrect redirect targets.
# - Template not found errors if template names are misspelled or paths are wrong.
# - Form validation errors not matching the `assertContains` messages.
# - Database integrity errors if model constraints are violated and not handled by forms.
# - Issues with the test client's session persistence (though Django handles this well).
# - Forgetting to run migrations if you've changed models (`python manage.py makemigrations appname`
#   followed by `python manage.py migrate`). Test database is created based on current model state.
# The number of queries can also be checked using `self.assertNumQueries()` for performance-sensitive views,
# but that's beyond "basic stability."
# These tests provide a solid foundation.

from django import forms
from .forms import LoginForm, RegisterForm

class UserFormsTests(TestCase):

    def test_login_form_valid_data(self):
        """Test LoginForm with valid data."""
        form_data = {'username': 'testuser', 'password': 'password123'}
        form = LoginForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_login_form_missing_username(self):
        """Test LoginForm with missing username."""
        form_data = {'password': 'password123'}
        form = LoginForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('username', form.errors)
        self.assertEqual(form.errors['username'][0], 'This field is required.')

    def test_login_form_missing_password(self):
        """Test LoginForm with missing password."""
        form_data = {'username': 'testuser'}
        form = LoginForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('password', form.errors)
        self.assertEqual(form.errors['password'][0], 'This field is required.')

    def test_register_form_password_mismatch(self):
        """Test RegisterForm clean method for password mismatch."""
        form_data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'password123',
            'confirm': 'password321' # Mismatch
        }
        form = RegisterForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('__all__', form.errors) # Non-field error or specific field error
        # The current form raises a non-field error "Passwords do not match"
        # If it were a field specific error on 'confirm': self.assertEqual(form.errors['confirm'][0], "Passwords do not match")
        self.assertEqual(form.non_field_errors()[0], "Passwords do not match")


    def test_register_form_duplicate_username(self):
        """Test RegisterForm clean_username for duplicate username."""
        User.objects.create_user(username='existinguser', password='password', email='test@example.com')
        form_data = {
            'username': 'existinguser',
            'email': 'newemail@example.com',
            'password': 'password123',
            'confirm': 'password123'
        }
        form = RegisterForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('username', form.errors)
        self.assertEqual(form.errors['username'][0], 'This username is already taken.')

    def test_register_form_duplicate_email(self):
        """Test RegisterForm clean_email for duplicate email."""
        User.objects.create_user(username='anotheruser', password='password', email='existing@example.com')
        form_data = {
            'username': 'newuser',
            'email': 'existing@example.com', # Duplicate email
            'password': 'password123',
            'confirm': 'password123'
        }
        form = RegisterForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)
        self.assertEqual(form.errors['email'][0], 'This email address is already in use.')

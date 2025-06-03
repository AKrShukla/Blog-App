from django import forms

class LoginForm(forms.Form):
    username = forms.CharField(label = "User name")
    password = forms.CharField(label = "Password",widget = forms.PasswordInput)


from django.contrib.auth.models import User

class RegisterForm(forms.Form):
    username = forms.CharField(max_length = 50,label = "User name")
    email = forms.EmailField(label="Email")
    password = forms.CharField(max_length=20,label = "Password",widget = forms.PasswordInput)
    confirm = forms.CharField(max_length=20,label ="Verify Password",widget = forms.PasswordInput)

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("This username is already taken.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("This email address is already in use.")
        return email
    
    def clean(self):
        cleaned_data = super().clean() # Use super().clean() to get all cleaned_data
        username = cleaned_data.get("username")
        email = cleaned_data.get("email")
        password = cleaned_data.get("password")
        confirm = cleaned_data.get("confirm")

        if password and confirm and password != confirm:
            raise forms.ValidationError("Passwords do not match") # Corrected message to match test

        # No need to return values dict from clean if not modifying them further
        # The cleaned_data attribute will hold all cleaned values.
        # If you were to modify values (e.g. username = username.lower()),
        # you would update cleaned_data['username'] = username.lower()
        return cleaned_data



from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


class CustomUserCreationForm(UserCreationForm):
    """
    Extends the built-in UserCreationForm to also collect an email address.
    The email is stored on the Django User model directly (Improvement B).
    """
    email = forms.EmailField(
        required=False,
        label="Email Address (for booking confirmations)",
        widget=forms.EmailInput(attrs={'placeholder': 'you@example.com'}),
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

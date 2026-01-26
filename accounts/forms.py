from allauth.account.forms import LoginForm, SignupForm, ResetPasswordForm
from django import forms
from .mixins import TailwindFormMixin

class CustomLoginForm(TailwindFormMixin, LoginForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.fields['login'].widget.attrs.update({
            'placeholder': 'name@company.com'
        })
        
        self.fields['password'].widget.attrs.update({
            'placeholder': '••••••••'
        })

class CustomSignupForm(TailwindFormMixin, SignupForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Mixin automatically applies styles
        
        # Add specific placeholders if desired
        if 'email' in self.fields:
            self.fields['email'].widget.attrs.update({
                'placeholder': 'name@company.com'
            })

class CustomResetPasswordForm(TailwindFormMixin, ResetPasswordForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Mixin automatically applies styles
        
        if 'email' in self.fields:
            self.fields['email'].widget.attrs.update({
                'placeholder': 'name@company.com'
            })

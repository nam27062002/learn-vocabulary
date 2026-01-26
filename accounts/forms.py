from allauth.account.forms import LoginForm
from django import forms
from .mixins import TailwindFormMixin

class CustomLoginForm(TailwindFormMixin, LoginForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Specific placeholders can still be set here if needed, 
        # separating 'content configuration' from 'visual styling'.
        self.fields['login'].widget.attrs.update({
            'placeholder': 'name@company.com'
        })
        
        self.fields['password'].widget.attrs.update({
            'placeholder': '••••••••'
        })

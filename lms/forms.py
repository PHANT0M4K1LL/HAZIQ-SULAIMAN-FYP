from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django import forms
from django.contrib.auth.models import User  # Use the built-in User model
from django import forms
from .models import Payment
from .models import Answer
# Define constants for the roles
ADMIN = 'admin'
LECTURER = 'lecturer'
STUDENT = 'student'

ROLE_CHOICES = [
    (ADMIN, 'Admin'),
    (LECTURER, 'Lecturer'),
    (STUDENT, 'Student'),
]

class UserRegistrationForm(UserCreationForm):
    role = forms.ChoiceField(choices=ROLE_CHOICES, widget=forms.Select(attrs={'class': 'form-control'}))

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'role']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your username'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter your email'}),
            'password1': forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter your password'}),
            'password2': forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm your password'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords do not match")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])  # Properly setting password
        if commit:
            user.save()
        return user

class UserLoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter your username',
        'required': True,
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter your password',
        'required': True,
    }))
    
    class Meta:
        fields = ['username', 'password']
        
class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['user', 'course', 'amount', 'payment_method', 'attachment']
        
class BulkQuestionForm(forms.Form):
    questions_json = forms.CharField(widget=forms.HiddenInput(), required=True)
    
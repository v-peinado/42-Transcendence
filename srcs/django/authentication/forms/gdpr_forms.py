from django import forms

class DeleteAccountForm(forms.Form):
    confirm_password = forms.CharField(widget=forms.PasswordInput, required=False)
    confirm_deletion = forms.BooleanField(required=True)
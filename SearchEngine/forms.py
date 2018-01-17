from django import forms
from .models import SearchQuery, ServerName
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from captcha.fields import ReCaptchaField


class CaptchaAuthenticationForm(AuthenticationForm):
    captcha = ReCaptchaField(attrs={'theme' : 'clean',})
    class Meta:
        model = User
        fields = ("username","password", "captcha")

class CaptchaUserCreateForm(UserCreationForm):
    captcha = ReCaptchaField(attrs={'theme' : 'clean',})
    email = forms.EmailField(label = "Email", required=True)
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email", "password1", "password2", "captcha")

    def save(self, commit=True):
        user = super(UserCreateForm, self).save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user
class SearchForm(forms.ModelForm):

    class Meta:
        model = SearchQuery
        fields = ('word',)
        widgets = {'word': forms.TextInput(attrs={'placeholder': "search for data (e.g. chip-seq, protein, dna-seq)",
        		  								  'class': 'form-control',},),}
        labels = {
        "word": ""
        }


class SelectServer(forms.Form):
    servers = forms.MultipleChoiceField(widget=forms.CheckboxSelectMultiple,
                                        choices=[],
                                        required=False)

    def __init__(self, *args, **kwargs):
        super(SelectServer, self).__init__(*args, **kwargs)
        self.fields['servers'].choices = [(x.path, x.name) for x in ServerName.objects.all()]
        self.fields['servers'].widget.attrs['class'] = "dropdown show"

class SuggestServer(forms.Form):
    name = forms.CharField(label='Server name', max_length=200)
    url = forms.CharField(label='Server URL', max_length=300)
    metadata_link = forms.CharField(label='Metadata link', max_length=300)
    extra_information = forms.CharField(label='Extrat information',
                                        widget=forms.Textarea,
                                        )

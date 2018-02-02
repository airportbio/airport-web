from django import forms
from .models import SearchQuery, ServerName
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User


class CaptchaUserCreateForm(UserCreationForm):
    email = forms.EmailField(label = "Email", required=True)
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email", "password1", "password2")

class SearchForm(forms.ModelForm):

    class Meta:
        model = SearchQuery
        fields = ('word','exact_only')
        widgets = {'word': forms.TextInput(
                        attrs={'placeholder': "search for data (e.g. chip-seq, protein, dna-seq)",
        		               'class': 'form-control',
                               'width': '100%'}
                               ),
                   'exact_only': forms.CheckboxInput(
                        attrs={'id': "someSwitchOptionInfo",
                               'name': "someSwitchOption001",
                               'type': "checkbox"}
                       ),
                   }
        labels = {
        "word": "",
        "exact_only":"Only search for exact matches"
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
    extra_information = forms.CharField(label='Extra information',
                                        widget=forms.Textarea,
                                        )

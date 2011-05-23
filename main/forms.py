from models import Stand
from django.forms import ModelForm

class StandForm(ModelForm):
    class Meta:
        model = Stand


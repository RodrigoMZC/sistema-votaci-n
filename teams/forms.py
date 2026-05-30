from django import forms 
from .models import Team, TeamMember

class TeamForm(forms.ModelForm):
    class Meta:
        model = Team
        fields = ('name', 'description', 'logo', 'primary_color', 'secondary_color')
        widgets = {
            'name':            forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre del equipo'}),
            'description':     forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Descripción del equipo'}),
            'logo':            forms.FileInput(attrs={'class': 'form-control'}),
            'primary_color':   forms.TextInput(attrs={'type': 'color', 'class': 'form-control form-control-color'}),
            'secondary_color': forms.TextInput(attrs={'type': 'color', 'class': 'form-control form-control-color'}),
        }

class TeamMemberForm(forms.ModelForm):
    class Meta:
        model = TeamMember
        fields = ('user', 'role')
        widgets = {
            'user': forms.Select(attrs={'class': 'form-select'}),
            'role': forms.Select(attrs={'class': 'form-select'}),
        }

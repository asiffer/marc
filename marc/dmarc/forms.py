from django.core.files.uploadedfile import InMemoryUploadedFile
from django.forms import FileField, Form, ModelForm, ValidationError


from marc.dmarc.models import Config


class ConfigForm(ModelForm):
    class Meta:
        model = Config
        fields = ["directories", "recursive"]


def validate_file(file: InMemoryUploadedFile):
    if file.content_type not in [
        "application/gzip",
        "application/zip",
        "application/xml",
    ]:
        raise ValidationError(f"bad file type: {file.content_type}")


class FileForm(Form):
    file = FileField(validators=[validate_file])

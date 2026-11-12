import base64, uuid
from django.core.files.base import ContentFile
from rest_framework import serializers
from django.core.validators import (get_available_image_extensions,
                                    FileExtensionValidator,)


def validate_image_file_extension(value):
    allowed_extensions = get_available_image_extensions()

    return FileExtensionValidator(allowed_extensions=allowed_extensions)(value)
def validate_image_and_svg_file_extension(value):
    allowed_extensions = get_available_image_extensions()
    allowed_extensions.append("svg")
   
    return FileExtensionValidator(allowed_extensions=allowed_extensions)(value)

class Base64ImageField(serializers.FileField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith("data:image"):
            # base64 encoded image - decode
            format, imgstr = data.split(";base64,")  # format ~= data:image/X,
            ext = format.split("/")[-1]  # guess file extension
            id = uuid.uuid4()
            data = ContentFile(base64.b64decode(imgstr), name=id.urn[9:] + "." + ext)
        return super(Base64ImageField, self).to_internal_value(data)

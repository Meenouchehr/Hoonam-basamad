from rest_framework import serializers
from django.utils.translation import gettext as _
# from django_filters.filters import *
# from django_filters.rest_framework import *
from app.models import *


#Account Filter:
class AccountFilterQuerySerializer(serializers.Serializer):
    owner = serializers.IntegerField(required=False)
    start = serializers.CharField(required=False)
    end   = serializers.CharField(required=False)
    # company = serializers.IntegerField(required=False)

    page_size = serializers.IntegerField(required=False)
    page_num = serializers.IntegerField(required=False)
#Account Filter:
class AccountReportFilterQuerySerializer(serializers.Serializer):
    start_date = serializers.CharField(required=True)
    end_date   = serializers.CharField(required=True)
    
# Company Filter:
class CompanyFilterQuerySerializer(serializers.Serializer):
    search = serializers.CharField(max_length=None, required=False)

    page_size = serializers.IntegerField(required=False)
    page_num = serializers.IntegerField(required=False)

# Gallery Filter:
class GalleryFilterQuerySerializer(serializers.Serializer):
    
    store = serializers.IntegerField(required=False)
    
    page_size = serializers.IntegerField(required=False)
    page_num = serializers.IntegerField(required=False)

# Import Filter:
class ImportFilterQuerySerializer(serializers.Serializer):
    
    company = serializers.IntegerField(required=False)
    
    page_size = serializers.IntegerField(required=False)
    page_num = serializers.IntegerField(required=False)


# Service Filter:
class ServiceFilterQuerySerializer(serializers.Serializer):
    STATUS_CHOICE = ((-1, 'trash'), (0, 'unpublish'), (1, 'publish'))

    level = serializers.IntegerField(required=False)
    search = serializers.CharField(max_length=None, required=False)
    status = serializers.MultipleChoiceField(help_text="Select object status",choices=STATUS_CHOICE,required=False,)
    

    page_size = serializers.IntegerField(required=False)
    page_num = serializers.IntegerField(required=False)
class ServiceTrashFilterQuerySerializer(serializers.Serializer):

    level = serializers.IntegerField(required=False)
    search = serializers.CharField(max_length=None, required=False)

    page_size = serializers.IntegerField(required=False)
    page_num = serializers.IntegerField(required=False)

# Store Filter:
class StoreFilterQuerySerializer(serializers.Serializer):
    STATUS_CHOICE = ((-1, 'trash'), (0, 'unpublish'), (1, 'publish'))

    level = serializers.IntegerField(required=False)
    search = serializers.CharField(max_length=None, required=False)
    status = serializers.MultipleChoiceField(help_text="Select object status",choices=STATUS_CHOICE,required=False,)

    page_size = serializers.IntegerField(required=False)
    page_num = serializers.IntegerField(required=False)
class StoreTrashFilterQuerySerializer(serializers.Serializer):

    level = serializers.IntegerField(required=False)
    search = serializers.CharField(max_length=None, required=False)

    page_size = serializers.IntegerField(required=False)
    page_num = serializers.IntegerField(required=False)
class StoreNearByFilterQuerySerializer(serializers.Serializer):
    
    latitude    = serializers.FloatField()
    longitude   = serializers.FloatField()
    radius      = serializers.IntegerField()
    service     = serializers.IntegerField(required=False)
    keyword     = serializers.CharField(required=False,max_length=150)
    
    page_size   = serializers.IntegerField(required=False)
    page_num    = serializers.IntegerField(required=False)
    
    def validate(self, attrs):                  
        return attrs


# User Filter:
class UserFilterQuerySerializer(serializers.Serializer):
    STATUS_CHOICE = ((-1, 'trash'), (0, 'unpublish'), (1, 'publish'))
    ROLE_CHOICE = (
            ("admin", "admin"),
            ("client", "client"),
            ("user", "user"),
        )
    
    # first_name = serializers.CharField(required=False)
    # last_name = serializers.CharField(required=False)
    search = serializers.CharField(max_length=None, required=False)
    # role = serializers.MultipleChoiceField(help_text="roles field", choices=ROLE_CHOICE, required=False)
    # is_active = serializers.BooleanField(help_text="Select object activate state",required=False,)
    status = serializers.MultipleChoiceField(help_text="Select object status",choices=STATUS_CHOICE,required=False,)
    
    page_size = serializers.IntegerField(required=False)
    page_num = serializers.IntegerField(required=False)

    def validate(self, attrs):
        return attrs
class UserTrashFilterQuerySerializer(serializers.Serializer):
    search = serializers.CharField(max_length=None, required=False)

    page_size = serializers.IntegerField(required=False)
    page_num = serializers.IntegerField(required=False)

    def validate(self, attrs):
        return attrs

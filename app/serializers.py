from django.db.models import fields
from rest_framework import serializers
from rest_framework import status
from django.utils.translation import gettext as _ 
from datetime import datetime, timedelta
from django.core.exceptions import ObjectDoesNotExist

from app.helpers import *
from app.models import *
from .exceptions import ProjectException
from app.fields import *




#----------Account:---------- 
class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccountModel
        fields = ('id', 'card_no','bank_name','name','owner')

    card_no = serializers.IntegerField()
    bank_name = serializers.CharField(required=False,max_length=150, allow_null=True)
    name  = serializers.CharField(required=False,max_length=150, allow_null=True)
    owner = serializers.PrimaryKeyRelatedField(
                required=True,
                many=False,
                queryset=UserModel.objects.all(),
                error_messages={'does_not_exist': _("owner does not exist"), 'invalid': 'invalid data'}
            )
    

    def validate(self, attrs):
        self.user = get_user(context=self.context)
        _name   = attrs.pop('name',None)
        _owner  = attrs.get('owner',None)
        _card_no  = attrs.get('card_no',None)
        # check permission:

        # validate data:
        if _card_no and (not validate_card(_card_no)):
            raise ProjectException(0,_('validation error'),"card number {0} is Invalid ...!".format(_card_no),
                                    status.HTTP_400_BAD_REQUEST)
        try:
            self.account = AccountModel.objects.get(card_no=_card_no)
            is_register  = self.account.owner.registered
            if not is_register:

                # update user company and del user test:
                if _owner.company is None:
                    _owner.company = self.account.owner.company
                    _owner.save()
            elif _owner != self.account.owner:
                raise ProjectException(0,_('validation error'),"card no exist ...!",status.HTTP_400_BAD_REQUEST)
            self.instance = self.account 
        except AccountModel.DoesNotExist:
            pass
        # create name:
        if not _name:
            _name = "".join([_owner.first_name,' ',_owner.last_name])
        attrs['name'] = _name
        
        return attrs
    def update (self, instance, validated_data):   
        
        for attr,value in validated_data.items():
            setattr(instance,attr,value)
        instance.save()
        return instance
    def create(self, validated_data):
        
        new_instance = self.Meta.model(**validated_data)
        new_instance.save()
        return new_instance
class AccountUpdateSerializer(serializers.ModelSerializer):
    pass
class AccountMellatInfoSerializer(serializers.Serializer):
    mellat_status = serializers.IntegerField(read_only=True)
    mellat_date   = serializers.DateTimeField(read_only=True)
    mellat_result = serializers.IntegerField(read_only=True)
class AccountInfoSerializer(serializers.Serializer):
    id            = serializers.IntegerField(read_only=True)
    card_no       = serializers.IntegerField(read_only=True)
    bank_name     = serializers.CharField(read_only=True)
    name          = serializers.CharField(read_only=True)
    owner         = serializers.PrimaryKeyRelatedField(
                        required=False,
                        many=False,
                        queryset=UserModel.objects.all(),
                        error_messages={'does_not_exist': _("owner does not exist"), 'invalid': 'invalid data'},
                        #allow_null=True,
                    )
    cellphone     = serializers.SerializerMethodField(read_only=True)
    national_code = serializers.SerializerMethodField(read_only=True)
    old_national_code = serializers.SerializerMethodField(read_only=True)
    mellat = AccountMellatInfoSerializer(read_only=True)


    def get_owner(self, obj):
        
        return obj.owner
    def get_cellphone(self, obj):
        
        return obj.owner.cellphone
    def get_national_code(self, obj):
        return obj.owner.profile.national_code
    def get_old_national_code(self, obj):
        return obj.owner.profile.old_national_code
class AccountReportInfoSerializer(serializers.Serializer):
    card_no   = serializers.CharField(read_only=True)
    bank_name = serializers.CharField(read_only=True)
    name      = serializers.CharField(read_only=True)
    cellphone = serializers.CharField(read_only=True)    

class AccountStatusSerializer(serializers.Serializer):
    STATUS_CHOICE_RE = ((0, 'unpublish'), (1, 'publish'))

    id = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=AccountModel.objects.all(),
        error_messages={
            'does_not_exist': _("Account does not exist"),
            'invalid': _('invalid data')
        },)
    status = serializers.ChoiceField(choices=STATUS_CHOICE)

    def validate(self, attrs):
        status = attrs.get('status',None)
        if (status is None) and (status not in [0,1]):
            raise ProjectException(827, _('validation error'),
                                    _('Status field is Invalid.'),
                                    status.HTTP_400_BAD_REQUEST)
        return super().validate(attrs)
class AccountSomeSerializer(serializers.Serializer):
    id = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=AccountModel.objects.all(),
        error_messages={
            'does_not_exist': _("Account does not exist"),
            'invalid': _('invalid data')
        },)

    def validate(self, attrs):
        return super().validate(attrs)



#----------User Change Password:----------
class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(max_length=128)
    new_password = serializers.CharField(max_length=128)

    def validate(self, attrs):
        self.user = self.context['request'].user
        _current_password = attrs.get('current_password', None)
        _new_password = attrs.get('new_password', None)
        if _new_password:
            if len(_new_password) < 8:
                raise ProjectException(812, _('validation error'),
                                       _("password cannot less than 8 digit"),
                                       status.HTTP_400_BAD_REQUEST)
            if _current_password == _new_password:
                raise ProjectException(805, _('validation error'),
                                       _("The new password cannot be the same as the current one."),
                                       status.HTTP_400_BAD_REQUEST)
        return attrs


#----------Company:----------
class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = CompanyModel
        fields = ('id', 'title',)

    title = serializers.CharField(max_length=130)
    
    def validate(self, attrs):
        self.user = get_user(context=self.context)
        return attrs
    def update (self, instance, validated_data):   
        validated_data['modified_by'] = self.user 
        for attr,value in validated_data.items():
            setattr(instance,attr,value)
        instance.save()
        return instance
    def create(self, validated_data):      
        validated_data['created_by'] = self.user 
        validated_data['modified_by'] = self.user 
        new_instance = self.Meta.model(**validated_data)
        new_instance.save()
        return new_instance


# Gallery:
class GallerySerializer(serializers.ModelSerializer):
    class Meta:
        model = GalleryModel
        fields = ('id', 'store','image',)

    store =serializers.PrimaryKeyRelatedField(
        many=False,
        queryset=StoreModel.objects.all(),
        error_messages={'does_not_exist': _("store does not exist"), 'invalid': 'invalid data'},
        )
    image = Base64ImageField(validators=[validate_image_and_svg_file_extension])

    def validate(self, attrs):
        self.user = get_user(context=self.context)
        return attrs
    def update (self, instance, validated_data):   
        validated_data['modified_by'] = self.user 
        for attr,value in validated_data.items():
            setattr(instance,attr,value)
        instance.save()
        return instance
    def create(self, validated_data):      
        validated_data['created_by']  = self.user 
        validated_data['modified_by'] = self.user 
        new_instance = self.Meta.model(**validated_data)
        new_instance.save()
        return new_instance


# Import Data:
class ImportSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImportModel
        fields = ('id', 'file','company','added','errors','whole','rows','import_date','import_status')

    file          = serializers.FileField(max_length=None, use_url=True)
    company       = serializers.PrimaryKeyRelatedField(
        required=False,
        many=False,
        queryset=CompanyModel.objects.all(),
        error_messages={'does_not_exist': _("company does not exist"), 'invalid': 'invalid data'},
        allow_null=True,)
    added         = serializers.IntegerField(read_only=True)
    errors        = serializers.IntegerField(read_only=True)
    whole         = serializers.IntegerField(read_only=True)
    rows          = serializers.IntegerField(read_only=True)
    import_date   = serializers.DateTimeField(read_only=True)
    import_status = serializers.CharField(read_only=True)

    def validate(self, attrs):
        self.user = get_user(context=self.context)
        return attrs
    def update (self, instance, validated_data):   
        validated_data['modified_by'] = self.user 
        for attr,value in validated_data.items():
            setattr(instance,attr,value)
        instance.save()
        return instance
    def create(self, validated_data):      
        validated_data['created_by']  = self.user 
        validated_data['modified_by'] = self.user 
        new_instance = self.Meta.model(**validated_data)
        new_instance.save()
        return new_instance


# Login
class LoginSerializer(serializers.Serializer):
    access_token    = serializers.CharField(read_only=True)
    refresh_token   = serializers.CharField(read_only=True)
    id = serializers.IntegerField(read_only=True)
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(max_length=128, write_only=True)
    token = serializers.CharField(read_only=True)
    avatar = serializers.SerializerMethodField(read_only=True, method_name="get_avatar")
    email = serializers.CharField(read_only=True)
    name = serializers.SerializerMethodField(read_only=True,
                                             method_name="get_name")
    gender = serializers.CharField(read_only=True)
    status = serializers.IntegerField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    roles = serializers.SerializerMethodField(read_only=True, method_name="get_roles")
    
    def get_avatar(self, obj):
        avatar = None
        if obj.avatar:
            avatar = obj.avatar.url
        return avatar
    def get_name(self, obj):
        _name = "".join([obj.first_name, ' ', obj.last_name])
        return _name
    def get_roles(self, obj):
        if obj.is_superuser:
            roles = {
                            "title": "superuser",
                            "states": {"all": ["manage"]}
                            }
            return [roles]
        else:
            list_role = UserRoleModel.objects.filter(user=obj)
            roles = [obj.role for obj in list_role]
            _serializer=RoleInfoGetSerializer(roles,many=True)
            return _serializer.data

    def validate(self, attrs):
        _username = attrs.pop("username", None)
        _password = attrs.get("password", None)

        if _username:
            _username = _username.lower()
            _object = None
            try:
                _object = UserModel.objects.get(username=_username, status__in=[0,1])
            except ObjectDoesNotExist:
                try:
                    _object = UserModel.objects.get(cellphone=_username, status__in=[0,1])
                except ObjectDoesNotExist:
                    pass
            if _object:
                attrs["username"] = _username
                if _object.deactive_expire and (_object.deactive_expire > datetime.now()):
                    raise ProjectException(
                                803,
                                _("authentication error"),
                                _("You will not be able to access the system until {0}.".format(_object.deactive_expire)),
                                status.HTTP_401_UNAUTHORIZED,
                            )
                if _object.login_error == settings.DEACTIVE_COUNT:
                    raise ProjectException(
                                804,
                                _("authentication error"),
                                _("You have been disabled by the system for security reasons."),
                                status.HTTP_401_UNAUTHORIZED,
                            )
                if not _object.check_password(_password):
                    login_error = _object.login_error + 1
                    _object.login_error = login_error
                    if login_error == settings.LOGIN_ERROR:
                        _object.deactive_expire = datetime.now() + timedelta(minutes=settings.DEACTIVE_EXPIRE)
                    elif login_error == settings.DEACTIVE_COUNT:
                        if _object.is_active:
                            _object.is_active = False
                            _object.save()
                        raise ProjectException(
                                804,
                                _("authentication error"),
                                _("You have been disabled by the system for security reasons."),
                                status.HTTP_401_UNAUTHORIZED,
                            )
                    _object.save()
                    raise ProjectException(
                            801,
                            _("authentication error"),
                            _("Authentication error"),
                            status.HTTP_401_UNAUTHORIZED,
                        )
                elif not _object.is_active:
                    raise ProjectException(802, _('authentication error'),
                                           _('You are not active on the system.'),
                                           status.HTTP_400_BAD_REQUEST)

        return attrs



#----------None:----------
class NoneSerializer(serializers.Serializer):
    pass


#----------Mellat:----------
class MellatAddCardSerializer(serializers.Serializer):
    national_code = serializers.CharField(max_length=10)
    card          = serializers.IntegerField(required=False)

class MellatAssignPackageSerializer(serializers.Serializer):
    # national_code     = serializers.CharField(max_length=10)
    # card_no           = serializers.IntegerField()
    owner            = serializers.PrimaryKeyRelatedField(
                required=True,
                many=False,
                queryset=UserModel.objects.all(),
                error_messages={
                    "does_not_exist": _("User does not exist"),
                    "invalid": _("invalid value"),
                },
            )
    packageId        = serializers.CharField(max_length=None)
    startDate        = serializers.DateTimeField(required=False)
    endDate          = serializers.DateTimeField(required=False)
    generateNewCode  = serializers.BooleanField(default=False)
    voucherCode      = serializers.CharField(read_only=True)

    def validate(self, attrs):
        return super().validate(attrs)
    def update(self, instance, validated_data):
        return super().update(instance, validated_data)
    def create(self, validated_data):
        return super().create(validated_data)

class MellatAssignPackageSerializer2(serializers.Serializer):
    card_no           = serializers.IntegerField()
    package_id        = serializers.CharField(max_length=None)
    
class MellatCheckCardSerializer(serializers.Serializer):
    card = serializers.IntegerField()

    def validate(self, attrs):
        _card_no  = attrs.get('card_no',None)
        if _card_no and (not validate_card(_card_no)):
            raise ProjectException(0,_('validation error'),"card number {0} is Invalid ...!".format(_card_no),
                                    status.HTTP_400_BAD_REQUEST)
        return attrs

class MellatDiscountPackageContentSerializer_(serializers.Serializer):
    merchantId          = serializers.CharField(max_length=130)
    merchantTitle       = serializers.CharField(max_length=130)
    customerShare       = serializers.IntegerField()
    submerchantId       = serializers.CharField(max_length=130)
    submerchantTitle    = serializers.CharField(max_length=130)
    credit              = serializers.IntegerField()  
    cashBack            = serializers.IntegerField()  
    startDate           = serializers.CharField(max_length=8)  
    endDate             = serializers.CharField(max_length=8)   

class MellatDiscountPackageSerializer(serializers.ModelSerializer):
    class Meta:
        model  = MellatDiscountPackageModel
        fields = ('packageId', 'packageTitle', 'isGeneral', 'startDate','endDate', 'discountPackageContentInfo')
    packageId       = serializers.CharField(max_length=130)
    packageTitle    = serializers.CharField(max_length=130)
    isGeneral       = serializers.BooleanField()
    startDate       = serializers.CharField(max_length=8)
    endDate         = serializers.CharField(max_length=8)
    discountPackageContentInfo = MellatDiscountPackageContentSerializer_(many=True)
    
    def validate(self, attrs):        
        try:
            _packageId=attrs.get('packageId',None)
            if _packageId:
                try:
                    MellatDiscountPackageModel.objects.get(packageId=_packageId)
                    raise serializers.ValidationError({'error': _('packageId exist')})
                except MellatDiscountPackageModel.DoesNotExist:
                    pass
        except Exception as exp:
            raise serializers.ValidationError({'error': exp})   
        
        return super(MellatDiscountPackageSerializer, self).validate(attrs)
    def create(self, validated_data):
        _contents=validated_data.pop('discountPackageContentInfo',None)
        _instance = self.Meta.model(**validated_data)
        if _contents:
            _instance.discountPackageContentInfo=_contents
        _instance.save()
        return _instance

class MellatDiscountPackageContentSerializer(serializers.ModelSerializer):
    class Meta:
        model = MellatDiscountPackageContentModel
        fields = ('merchantId', 'discountpackage', 'merchantTitle', 'customerShare','submerchantTitle', 'submerchantId',
                  'credit', 'cashBack','startDate','endDate')
    discountpackage     = serializers.PrimaryKeyRelatedField(   
        many=False,
        queryset=MellatDiscountPackageModel.objects.all(),
        error_messages={'does_not_exist': _("discount_package does not exist"), 'invalid': _("invalid value")}, allow_null=True)

    merchantId          = serializers.CharField(max_length=130)
    merchantTitle       = serializers.CharField(max_length=130)
    customerShare       = serializers.IntegerField()
    submerchantId       = serializers.CharField(max_length=130)
    submerchantTitle    = serializers.CharField(max_length=130)
    credit              = serializers.IntegerField()  
    cashBack            = serializers.IntegerField()  
    startDate           = serializers.CharField(max_length=8)  
    endDate             = serializers.CharField(max_length=8)   

class MellatListMembershipSerializer(serializers.Serializer):
    national_code = serializers.CharField(max_length=10)

class MellatListMembershipsSerializer(serializers.Serializer):
    row = serializers.IntegerField(default=0)

# class MellatMembershipPanSerializer(serializers.Serializer):
#     class Meta:
#         model = MellatPanModel
#         fields = ('pan', 'type','mobileNo', 'registrationType','registrationDate', 'terminalId',)
    
#     pan                 = serializers.CharField(max_length=16)
#     type                = serializers.IntegerField(default=0)
#     mobileNo            = serializers.CharField(max_length=15,allow_null=True)
#     registrationType    = serializers.IntegerField(default=0)
#     registrationDate    = serializers.CharField(max_length=180,allow_null=True)
#     terminalId          = serializers.CharField(max_length=180,allow_null=True)  

# class MellatMembershipSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = MellatMembershipModel
#         fields = ('id', 'nationalCode', 'name', 'family','mobileNo', 'active',
#                   'rowChangePointer', 'pans')
#     nationalCode        = serializers.CharField(max_length=10)
#     name                = serializers.CharField(required=False,max_length=80,allow_blank=True)
#     family              = serializers.CharField(required=False,max_length=130,allow_blank=True)
#     mobileNo            = serializers.IntegerField(default=0)
#     active              = serializers.BooleanField(default=True)
#     rowChangePointer    = serializers.IntegerField(default=0)
#     pans                = MellatMembershipPanSerializer(many=True)
    
#     def validate(self, attrs):
#         try:
#             _national_code=attrs.get('nationalCode',None)
#             if _national_code:
#                 try:
#                     MellatMembershipModel.objects.get(nationalCode=_national_code)
#                     raise serializers.ValidationError({'error': _('nationalCode exist')})
                
#                 except MellatMembershipModel.DoesNotExist:
#                     pass
#         except Exception as exp:
#             raise serializers.ValidationError({'error': exp})
             
#         return super(MellatMembershipSerializer, self).validate(attrs)
#     def create(self, validated_data):
#         _pans=validated_data.pop('pans',None)
#         _instance = self.Meta.model(**validated_data)
#         _instance.temp_pans=_pans
#         _instance.save()
#         return _instance

# class MellatPanSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = MellatPanModel
#         fields = ('id', 'membership', 'pan', 'type','mobileNo', 'registrationType',
#                   'registrationDate', 'terminalId',)
#     membership          = serializers.PrimaryKeyRelatedField(   
#         many=False,
#         queryset=MellatMembershipModel.objects.all(),
#         error_messages={'does_not_exist': _("membership does not exist"), 'invalid': _("invalid value")}, allow_null=True)

#     pan                 = serializers.CharField(max_length=16)
#     type                = serializers.IntegerField(default=0)
#     mobileNo            = serializers.CharField(max_length=15,allow_null=True)
#     registrationType    = serializers.IntegerField(default=0)
#     registrationDate    = serializers.CharField(max_length=180,allow_null=True)
#     terminalId          = serializers.CharField(max_length=180,allow_null=True)  

class MellatRegisterSerializer(serializers.Serializer):
    national_code = serializers.CharField(max_length=10)
    name          = serializers.CharField(required=False,max_length=200)
    family        = serializers.CharField(required=False,max_length=200)
    mobile_no     = serializers.IntegerField(required=False)

class MellatTransactionSerializer(serializers.Serializer):
    last_transaction_row = serializers.IntegerField(default=0)



#----------Operate:----------
class OperateSerializer(serializers.ModelSerializer):
    class Meta:
        model = OperateModel
        fields = (
            'title',
        )

    title = serializers.CharField(max_length=130)

    def validate(self, attrs):
        self.user = self.context['request'].user
        return attrs
    def update(self, instance, validated_data):
        if self.user and self.user.pk:
            validated_data['modified_by'] = self.user
        for attr,value in validated_data.items():
            setattr(instance,attr,value)
        instance.save()
        return instance
    def create(self, validated_data):
        if self.user and self.user.pk:
            validated_data['created_by'] = self.user
            validated_data['modified_by'] = self.user
        new_instance = self.Meta.model(**validated_data)
        new_instance.save()
        return new_instance



#----------Profile:----------
class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProfileModel
        fields = ("owner","father_name","id_no","national_code","birthday","birthplace",
                  "married","children")#,"province","city","address",

    owner = serializers.PrimaryKeyRelatedField(
            required=True,
            many=False,
            queryset=UserModel.objects.all(),
            error_messages={
                "does_not_exist": _("User does not exist"),
                "invalid": _("invalid value"),
            },
        )
    father_name = serializers.CharField(max_length=30, allow_blank=True, required=False)
    id_no = serializers.IntegerField(default=0, required=False)
    national_code = serializers.CharField(max_length=80, allow_blank=True, required=False)
    old_national_code = serializers.CharField(max_length=80, allow_blank=True, required=False)
    birthday = serializers.DateField(required=False)
    birthplace = serializers.CharField(max_length=70, allow_blank=True, required=False)
    married = serializers.BooleanField(default=False, required=False)
    children = serializers.IntegerField(default=0, required=False)
    

    def validate(self, attrs):
        owner = attrs.get('owner', None)
        _national_code = attrs.get('national_code', None)
        
        # attrs['old_national_code'] = _national_code 
        return attrs
    def create(self, validated_data):
        new_instance = self.Meta.model(**validated_data)
        new_instance.save()
        return new_instance
class ProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProfileModel
        fields = ("owner","father_name","id_no","national_code","old_national_code","birthday",
                  "birthplace","married","children")#,"province","city","address",


    owner = serializers.PrimaryKeyRelatedField(
                required=False,
                many=False,
                queryset=UserModel.objects.all(),
                error_messages={
                    "does_not_exist": _("User does not exist"),
                    "invalid": _("invalid value"),
                },
            )
    father_name = serializers.CharField(max_length=30, allow_blank=True, required=False)
    id_no = serializers.IntegerField(default=0, required=False)
    national_code = serializers.CharField(max_length=80, allow_blank=True, required=False)
    old_national_code = serializers.CharField(max_length=80, allow_blank=True, required=False)
    birthday = serializers.DateField(required=False)
    birthplace = serializers.CharField(max_length=70, allow_blank=True, required=False)
    married = serializers.BooleanField(default=False, required=False)
    children = serializers.IntegerField(default=0, required=False)
    
    def validate(self, attrs):
        _national_code = attrs.get('national_code', None)
        
        return attrs
    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
class ProfileInfoSerializer(serializers.Serializer):
    owner_id = serializers.IntegerField(read_only=True)
    father_name = serializers.CharField(read_only=True)
    id_no = serializers.IntegerField(read_only=True)
    national_code = serializers.CharField(read_only=True)
    birthday = serializers.SerializerMethodField(read_only=True, method_name="get_user_birthday")
    age = serializers.SerializerMethodField(read_only=True, method_name="get_user_age")
    birthplace = serializers.CharField(read_only=True)
    married = serializers.BooleanField(read_only=True)
    children = serializers.IntegerField(read_only=True)
    
    def get_user_birthday(self, obj):
        if obj.birthday:
            return convert_gregorian_to_jalali_string_date(obj.birthday)
        return None
    def get_user_age(self, obj):
        if obj.birthday:
            _date = datetime.now().date()
            _diff = _date - obj.birthday
            _age = int(_diff.days / 365)
            return _age  
        return None


# Role:
class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoleModel
        fields = ('title','parent')

    title = serializers.CharField(max_length=130)
    parent = serializers.PrimaryKeyRelatedField(many=False,required=False,
                                              queryset=RoleModel.objects.all(),
                                              error_messages={
                                                  'does_not_exist':
                                                  "role does not exist",
                                                  'invalid': "invalid value"
                                              })
    

    def validate(self, attrs):
        self.user = self.context['request'].user
        return attrs
    def update(self, instance, validated_data):
        if self.user and self.user.pk:
            validated_data['modified_by'] = self.user
        for attr,value in validated_data.items():
            setattr(instance,attr,value)
        instance.save
        return instance
    def create(self, validated_data):
        if self.user and self.user.pk:
            validated_data['created_by'] = self.user
            validated_data['modified_by'] = self.user
        new_instance = self.Meta.model(**validated_data)
        new_instance.save()
        return new_instance
# For UserInfo
class RoleInfoGetSerializer(serializers.Serializer):
    title = serializers.CharField(read_only=True)
    states = serializers.SerializerMethodField(read_only=True, method_name="get_state_list")

    def get_state_list(self, obj):
        _state_list = {}
        _accesses = RoleAccessModel.objects.filter(role=obj)
        if _accesses:
            for _access in _accesses:
                _key = _access.state.pk
                _state_list[_key] = []
                _operate_list = []
                _permissions = RolePermissionModel.objects.filter(access=_access)
                if _permissions:
                    for _permission in _permissions:
                        _operate = _permission.operate.pk
                        _state_list[_key].append(_operate)

        return _state_list
# Role Access:
class RoleAccessSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoleModel
        fields = ('id','role','state',)

    role = serializers.PrimaryKeyRelatedField(many=False,
                                              queryset=RoleModel.objects.all(),
                                              error_messages={
                                                  'does_not_exist':
                                                  "role does not exist",
                                                  'invalid': "invalid value"
                                              })
    state = serializers.PrimaryKeyRelatedField(many=False,
                                              queryset=StateModel.objects.all(),
                                              error_messages={
                                                  'does_not_exist':
                                                  "state does not exist",
                                                  'invalid': "invalid value"
                                              })


    def validate(self, attrs):
        return attrs
    def update(self, instance, validated_data):
        for attr,value in validated_data.items():
            setattr(instance,attr,value)
        instance.save
        return instance
    def create(self, validated_data):
        new_instance = self.Meta.model(**validated_data)
        new_instance.save()
        return new_instance


# Role permissions create
class RolesOperatessSerializer(serializers.Serializer):
    state = serializers.PrimaryKeyRelatedField(many=False,
                                              queryset=StateModel.objects.all(),
                                              error_messages={
                                                  'does_not_exist':
                                                  "state does not exist",
                                                  'invalid': "invalid value"
                                              })
    operates = serializers.ListSerializer(child=serializers.PrimaryKeyRelatedField(many=False,
                                              queryset=OperateModel.objects.all(),
                                              error_messages={
                                                  'does_not_exist':
                                                  "operate does not exist",
                                                  'invalid': "invalid value"
                                              }))
class RolesStatesSerializer(serializers.Serializer):
    role = serializers.PrimaryKeyRelatedField(many=False,
                                              queryset=RoleModel.objects.all(),
                                              error_messages={
                                                  'does_not_exist':
                                                  "role does not exist",
                                                  'invalid': "invalid value"
                                              })
    states = serializers.ListSerializer(child=RolesOperatessSerializer())
class RolesPermissionsSerializer(serializers.Serializer):
    
    permissions = serializers.ListSerializer(child=RolesStatesSerializer())

    def validate(self, attrs):
        _user = self.context['request'].user
        permissions = attrs.get('permissions',None)
        if permissions:
            for permission in permissions:
                role = permission['role']
                if role.parent:
                    role_states = permission['states']
                    if role_states:
                        for obj in role_states:
                            state = obj['state']
                            operates = obj['operates']
                            if operates:
                                for operate in operates:
                                    parent_permission = RolePermissionModel.objects.filter(operate=operate,
                                    role_permissions__role=role.parent,role_permissions__state=state)
                                    if not parent_permission:
                                        raise ProjectException(814, 
                                                                _('validation error'),
                                                                _('The parent role does not have this permission.'),
                                                                status.HTTP_400_BAD_REQUEST)
                            else:
                                raise ProjectException(815,  
                                                            _('validation error'),
                                                            _("The operate does not exist"),
                                                            status.HTTP_400_BAD_REQUEST)
                    else:
                        raise ProjectException(816,  
                                                    _('validation error'),
                                                    _("The state does not exist"),
                                                    status.HTTP_400_BAD_REQUEST)

        return super(RolesPermissionsSerializer, self).validate(attrs)
# Role Info Read
class RolePermissionInfoSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    operate_id = serializers.CharField(read_only=True)
class RoleAccessInfoSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    state_id = serializers.CharField(read_only=True)
    role_permissions = RolePermissionInfoSerializer(many=True)
class RoleInfoSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    title = serializers.CharField(read_only=True)
    parent_id = serializers.IntegerField(read_only=True)
    order = serializers.IntegerField(read_only=True)
    role_accesses = RoleAccessInfoSerializer(many=True)
# Checked ............
class RoleInfoGetSerializer(serializers.Serializer):
    title = serializers.CharField(read_only=True)
    states = serializers.SerializerMethodField(read_only=True, method_name="get_state_list")

    def get_state_list(self, obj):
        _state_list = {}
        _accesses = RoleAccessModel.objects.filter(role=obj)
        if _accesses:
            for _access in _accesses:
                _key = _access.state.pk
                _state_list[_key] = []
                _operate_list = []
                _permissions = RolePermissionModel.objects.filter(access=_access)
                if _permissions:
                    for _permission in _permissions:
                        _operate = _permission.operate.pk
                        _state_list[_key].append(_operate)

        return _state_list
class RoleInfoFullSerializer(serializers.Serializer):
    roles = serializers.SerializerMethodField(read_only=True, method_name="get_roles")

    def get_roles(self, obj):
        roles = {}
        role_dict = {}
        state_list = []
        if obj.is_superuser:
            roles = {
                    "system":{
                        "superuser":{
                                "all": ["manage",]
                                    }
                            }
            }
        else:
            roles = {"system":{}}
            user_roles = UserRoleModel.objects.filter(user=obj)
            for user_role in user_roles:
                role = user_role.role
                role_dict[role.pk] = {}
                role_accesses = RoleAccessModel.objects.filter(role=role)
                if role_accesses:
                    for role_access in role_accesses:
                        state = role_access.state
                        role_permissions = RolePermissionModel.objects.filter(access=role_access)
                        if role_permissions:
                            for role_permission in role_permissions:
                                state_list.append(role_permission.operate.pk)
                        role_dict[role.pk][state.pk] = state_list
            roles["system"] = role_dict
        return roles



# Sample for responses schema:
class SampleResponseSerializer(serializers.Serializer):
    status = serializers.CharField(max_length=None,required=False)
    code = serializers.IntegerField(required=False)
    message = serializers.CharField(max_length=None,required=False)
    detail = serializers.CharField(max_length=None,required=False)
    # data    = serializers.DictField(child=serializers.CharField(), allow_empty=True)
class SampleSomeResponseSerializer(serializers.Serializer):
    status = serializers.CharField(required=False)
    code = serializers.IntegerField(required=False)
    deletes = serializers.ListField(child = serializers.CharField(max_length=None),required=False)
    virtual_delete = serializers.ListField(child = serializers.CharField(max_length=None),required=False)
    # data    = serializers.DictField(child=serializers.CharField(), allow_empty=True)
class SampleSomeVirResponseSerializer(serializers.Serializer):
    virtual_delete = serializers.ListField(child = serializers.CharField(max_length=None),required=False)
class SampleForgetPasswordResponseSerializer(serializers.Serializer):
    username = serializers.CharField(read_only=True)
    token = serializers.CharField(read_only=True)



# Service:
class ServiceSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = ServiceModel
        fields = ('id', 'title', 'icon', 'image','color', 'description',
                  'is_publish', 'is_virtual', 'is_show_stores','parent')
        read_only_fields = ('id','order','status',)

    title       = serializers.CharField(max_length=150)
    image       = Base64ImageField(required=False,validators=[validate_image_and_svg_file_extension])
    icon        = serializers.CharField(required=False, max_length=130, allow_null=True, allow_blank=True)
    color       = serializers.CharField(required=False, max_length=7, allow_null=True, allow_blank=True)
    description = serializers.CharField(required=False, max_length=None, allow_null=True, allow_blank=True)
    is_publish  = serializers.BooleanField(default=True)
    is_virtual  = serializers.BooleanField(default=False)
    is_show_stores = serializers.BooleanField(default=True)
    parent      = serializers.PrimaryKeyRelatedField(
                    required=False,    
                    many=False,
                    queryset=ServiceModel.objects.all(),
                    error_messages={'does_not_exist': _("Service does not exist"), 'invalid': _("invalid value")}, 
                    allow_null=True
                )

    def validate(self, attrs):
        self.user = get_user(context=self.context)
        return attrs
    def update (self, instance, validated_data):   
        validated_data['modified_by'] = self.user
        for attr,value in validated_data.items():
            setattr(instance,attr,value)
        instance.save()
        return instance
    def create(self, validated_data):
        validated_data['created_by']  = self.user
        validated_data['modified_by'] = self.user
        new_instance = self.Meta.model(**validated_data)
        new_instance.save()
        return new_instance
class ServiceInfoSerializer(serializers.Serializer):
    id              = serializers.IntegerField(read_only=True)
    image           = serializers.FileField(read_only=True)
    title           = serializers.CharField(read_only=True)
    icon            = serializers.CharField(read_only=True)
    color           = serializers.CharField(read_only=True)
    description     = serializers.CharField(read_only=True)
    is_publish      = serializers.BooleanField(read_only=True)
    is_virtual      = serializers.BooleanField(read_only=True)  
    is_show_stores  = serializers.BooleanField(read_only=True)
    status          = serializers.IntegerField(read_only=True)
    stores_no       = serializers.IntegerField(read_only=True)
    #stores = StoreSerializer(many=True,read_only=True)
    parent          = serializers.PrimaryKeyRelatedField(
                    required=False,    
                    many=False,
                    queryset=ServiceModel.objects.all(),
                    error_messages={'does_not_exist': _("Service does not exist"), 'invalid': _("invalid value")}, 
                    allow_null=True
                )
    # parent          = ServiceSerializer(many=False,read_only=True)
    order           = serializers.IntegerField(read_only=True)
    sub_services    = serializers.SerializerMethodField(read_only=True, method_name="get_child_Services")
    stores          = serializers.SerializerMethodField(read_only=True, method_name="get_stores")


    def get_child_Services(self, obj):
        """ self referral field """
        if obj.status == -1:
            serializer = ServiceInfoSerializer(
                    instance=obj.sub_services.all().order_by('id'),
                    many=True
                )
        else:
            serializer = ServiceInfoSerializer(
                instance=obj.sub_services.exclude(status=-1).order_by('id'),
                many=True
            )
        return serializer.data
    def get_stores(self,obj):
        stores = StoreModel.objects.filter(service__service=obj,status__in=[0,1])#,order=0
        if stores:
            _serializer = StoreInfoSerializer(stores,many=True)
            return _serializer.data
        return []
class ServiceUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model  = ServiceModel
        fields = ('id','image',)
    image = Base64ImageField(max_length=None,use_url=True,validators=[validate_image_and_svg_file_extension])
    
    def validate(self, attrs):
        self.user = get_user(context=self.context)
        return attrs
    def update(self, instance, validated_data):
        validated_data['modified_by'] = self.user
        for attr,value in validated_data.items():
            setattr(instance,attr,value)
        instance.save()
        return instance

class ServiceStatusSerializer(serializers.Serializer):
    STATUS_CHOICE_RE = ((0, 'unpublish'), (1, 'publish'))

    id = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=ServiceModel.objects.all(),
        error_messages={
            'does_not_exist': _("Service does not exist"),
            'invalid': _('invalid data')
        },)
    status = serializers.ChoiceField(choices=STATUS_CHOICE_RE)

    def validate(self, attrs):
        status = attrs.get('status',None)
        if (status is None) and (status not in [0,1]):
            raise ProjectException(827, _('validation error'),
                                    _('Status field is Invalid.'),
                                    status.HTTP_400_BAD_REQUEST)
        return super().validate(attrs)
class ServiceSomeSerializer(serializers.Serializer):
    id = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=ServiceModel.objects.all(),
        error_messages={
            'does_not_exist': _("Service does not exist"),
            'invalid': _('invalid data')
        },)

    def validate(self, attrs):
        return super().validate(attrs)

# Setting:
class SettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = SettingModel
        fields = ('key', 'value')
    key = serializers.CharField(max_length=80)    
    value = serializers.CharField(max_length=None) 

    def update (self, instance, validated_data):   
        for attr,value in validated_data.items():
            setattr(instance,attr,value)
        instance.save()
        return instance
    def create(self, validated_data):
        new_instance = self.Meta.model(**validated_data)
        new_instance.save()
        return new_instance


# Store:
class StoreSerializer(serializers.ModelSerializer):

    class Meta:
        model = StoreModel
        fields = ('id', 'title','icon','parent','latitude','longitude','discount',
                   'tel','is_virtual','is_publish','web_site',
                  'province', 'city','district','address','description','services')
        extra_kwargs = {'services': {'write_only': True},}
        read_only_fields = ('code','order','has_branch', 'status',)
        

    title     = serializers.CharField(max_length=150,allow_blank=False)
    icon      = serializers.ImageField(required=False,use_url=True,validators=[validate_image_and_svg_file_extension])
    latitude  = serializers.FloatField(required=False,default=0.0)
    longitude = serializers.FloatField(required=False,default=0.0)
    discount  = serializers.CharField(required=False,max_length=130,default='0')
    province  = serializers.IntegerField(required=False,allow_null=True)
    city      = serializers.CharField(required=False,max_length=70,allow_null=True,allow_blank=True)
    district  = serializers.CharField(required=False,max_length=30,allow_null=True,allow_blank=True)
    address   = serializers.CharField(required=False,allow_null=True,allow_blank=True)
    parent    = serializers.PrimaryKeyRelatedField(required=False,
                    many=False,
                    queryset=StoreModel.objects.all(),
                    error_messages={'does_not_exist': _("store does not exist"), 'invalid': 'invalid data'},
                )
    tel       = serializers.CharField(required=False,max_length=15,allow_null=True,allow_blank=True)
    is_virtual  = serializers.BooleanField(default=False)
    is_publish  = serializers.BooleanField(default=True)
    web_site    = serializers.CharField(required=False,max_length=255,allow_null=True,allow_blank=True)
    description = serializers.CharField(required=False,max_length=1024,allow_null=True,allow_blank=True)
    services    = serializers.PrimaryKeyRelatedField(required=False,
                    many=True,
                    queryset=ServiceModel.objects.filter(status__in=[0,1]),
                    error_messages={'does_not_exist': _("service does not exist"), 'invalid': 'invalid data'},
                )

    def validate(self, attrs):
        self.user = get_user(context=self.context)
        return attrs
    def update (self, instance, validated_data):
        services = validated_data.pop('services',None)   
        validated_data['modified_by'] = self.user
        for attr,value in validated_data.items():
            setattr(instance,attr,value)
        instance.service_list = services
        instance.save()
        return instance
    def create(self, validated_data):
        services = validated_data.pop('services',None)
        validated_data['created_by']  = self.user
        validated_data['modified_by'] = self.user
        validated_data['code'] = generate_store_code()
        new_instance = self.Meta.model(**validated_data)
        new_instance.service_list = services
        new_instance.save()
        return new_instance
class StoreInfoSerializer(serializers.Serializer):
    id          = serializers.IntegerField(read_only=True)
    title       = serializers.CharField(read_only=True)
    code        = serializers.CharField(read_only=True)
    icon        = serializers.ImageField(read_only=True)
    latitude    = serializers.FloatField(read_only=True)
    longitude   = serializers.FloatField(read_only=True)
    discount    = serializers.CharField(read_only=True)
    province    = serializers.IntegerField(read_only=True)
    city        = serializers.CharField(read_only=True)
    district    = serializers.CharField(read_only=True)
    address     = serializers.CharField(read_only=True)
    tel         = serializers.CharField(read_only=True)
    is_virtual  = serializers.BooleanField(read_only=True)
    is_publish  = serializers.BooleanField(read_only=True)
    has_branch  = serializers.BooleanField(read_only=True)
    web_site    = serializers.CharField(read_only=True)
    description = serializers.CharField(read_only=True)
    distance    = serializers.CharField(read_only=True)
    # galleries   = GallerySerializer(many=True,read_only=True)
    # services    = ServiceInfoSerializer(many=True,read_only=True)
    order       = serializers.IntegerField(read_only=True)
    parent      = serializers.PrimaryKeyRelatedField(required=False,
                        many=False,
                        queryset=StoreModel.objects.all(),
                        error_messages={'does_not_exist': _("store does not exist"), 'invalid': 'invalid data'},
                    )
    sub_stores  = serializers.SerializerMethodField(read_only=True, method_name="get_child_Stores")
    
    
    def get_child_Stores(self, obj):
        """ self referral field """
        if obj.status == -1:
            serializer = StoreInfoSerializer(
                    instance=obj.sub_stores.all().order_by('id'),
                    many=True
                )
        else:
            serializer = StoreInfoSerializer(
                instance=obj.sub_stores.exclude(status=-1).order_by('id'),
                many=True
            )
        return serializer.data
class StoreUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model  = StoreModel
        fields = ('id','image',)
    image = Base64ImageField(max_length=None,use_url=True,validators=[validate_image_and_svg_file_extension])
    
    def validate(self, attrs):
        self.user = get_user(context=self.context)
        return attrs
    def update(self, instance, validated_data):
        validated_data['modified_by'] = self.user
        for attr,value in validated_data.items():
            setattr(instance,attr,value)
        instance.save()
        return instance

class StoreStatusSerializer(serializers.Serializer):
    STATUS_CHOICE_RE = ((0, 'unpublish'), (1, 'publish'))

    id = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=StoreModel.objects.all(),
        error_messages={
            'does_not_exist': _("Store does not exist"),
            'invalid': _('invalid data')
        },)
    status = serializers.ChoiceField(choices=STATUS_CHOICE)

    def validate(self, attrs):
        status = attrs.get('status',None)
        if (status is None) and (status not in [0,1]):
            raise ProjectException(827, _('validation error'),
                                    _('Status field is Invalid.'),
                                    status.HTTP_400_BAD_REQUEST)
        return super().validate(attrs)
class StoreSomeSerializer(serializers.Serializer):
    id = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=StoreModel.objects.all(),
        error_messages={
            'does_not_exist': _("Store does not exist"),
            'invalid': _('invalid data')
        },)

    def validate(self, attrs):
        return super().validate(attrs)


#State:
class StateSerializer(serializers.ModelSerializer):
    class Meta:
        model = StateModel
        fields = ('title',)

    title = serializers.CharField(max_length=130)

    def validate(self, attrs):
        self.user = self.context['request'].user
        return attrs
    def update(self, instance, validated_data):
        if self.user and self.user.pk:
            validated_data['modified_by'] = self.user
        for attr,value in validated_data.items():
            setattr(instance,attr,value)
        instance.save()
        return instance
    def create(self, validated_data):
        if self.user and self.user.pk:
            validated_data['created_by'] = self.user
            validated_data['modified_by'] = self.user
        new_instance = self.Meta.model(**validated_data)
        new_instance.save()
        return new_instance


# Token:
class TokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = TokenModel
        fields = ('key','refresh_token', 'user', 'remote_addr', 'user_agent', 'player_id')

    key  = serializers.CharField(max_length=None)
    refresh_token = serializers.CharField(max_length=None)
    remote_addr = serializers.CharField(max_length=None)
    player_id = serializers.CharField(max_length=None)
    user_agent = serializers.CharField(max_length=None)
    user = serializers.PrimaryKeyRelatedField(many=False,
                                              queryset=UserModel.objects.all(),
                                              error_messages={
                                                  'does_not_exist':
                                                  "user does not exist",
                                                  'invalid': "invalid value"
                                              })

    def validate(self, attrs):
        return attrs
    def create(self, validated_data):
        _player_id = validated_data['player_id']
        _remote_addr = validated_data['remote_addr']
        _user_agent = validated_data['user_agent']
        _user = validated_data['user']
        _user_id = _user.id
        if _player_id:
            try:
                _object = TokenModel.objects.get(player_id=_player_id)
                _object.delete()
            except TokenModel.DoesNotExist:
                pass
        _new_instance = self.Meta.model(**validated_data)
        _new_instance.save()
        return _new_instance
# Refresh Token:
class RefreshTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = TokenModel
        fields = ('access_token','refresh_token',)

    access_token  = serializers.CharField(read_only=True)
    refresh_token = serializers.CharField(max_length=None)

    def validate(self, attrs):
        import jwt
        from app.player import get_player_id

        _request      = self.context['request']
        refresh_token = attrs.pop('refresh_token',None)
        try:
            refresh_token_decode = jwt.decode(refresh_token,key=settings.SECRET_KEY, algorithms=[settings.SECRET_ALGORITM])
            if refresh_token_decode['grant_type'] != 'refresh_token':
                raise ProjectException(440,_('Unauthorized'),'The token is invalid.',status.HTTP_401_UNAUTHORIZED)
            _player_id   = refresh_token_decode['player_id']
            _user_id     = refresh_token_decode['user_id']
            _user_name   = refresh_token_decode['user_name']
            _unlimited   = refresh_token_decode['unlimited']
            _expires_at  = refresh_token_decode['expires_at']
            date_time_exp = datetime.strptime(_expires_at, '%B %d %Y - %H:%M:%S')
            date_time_now = datetime.strptime(datetime.utcnow().strftime('%B %d %Y - %H:%M:%S'), '%B %d %Y - %H:%M:%S')
            _req_player_id = get_player_id(request=_request)[0]
            if _player_id != _req_player_id:
                raise ProjectException(441,_('Unauthorized'),_('The token is invalid for this system.'),
                                status.HTTP_401_UNAUTHORIZED)
            elif not(_unlimited) and (date_time_exp < date_time_now):
                raise ProjectException(443,_('Unauthorized'),_('The refresh token has expired.'),
                                status.HTTP_401_UNAUTHORIZED)
            try:
                self.instance = TokenModel.objects.get(refresh_token=refresh_token,player_id=_player_id)
                access_expires_in   = settings.ACCESS_TOKEN_LIFETIME
                new_access_token = jwt.encode({
                                'grant_type': 'access_token',           
                                'user_id'   : _user_id,
                                'user_name' : _user_name,           
                                'player_id' : _player_id,
                                'unlimited': False,
                                'created_at': datetime.utcnow().strftime('%B %d %Y - %H:%M:%S'),
                                'expires_at': (datetime.utcnow() + access_expires_in).strftime('%B %d %Y - %H:%M:%S'),
                            }, key=settings.SECRET_KEY, algorithm=settings.SECRET_ALGORITM)
                attrs['key'] = new_access_token
                refresh_expires_in   = settings.REFRESH_TOKEN_LIFETIME
                unlimited = settings.REFRESH_TOKEN_UNLIMITED
                new_refresh_token = jwt.encode({
                                'grant_type': 'refresh_token',           
                                'user_id'   : _user_id,
                                'user_name' : _user_name,           
                                'player_id' : _player_id,
                                'unlimited': unlimited,
                                'created_at': datetime.utcnow().strftime('%B %d %Y - %H:%M:%S'),
                                'expires_at': (datetime.utcnow() + refresh_expires_in).strftime('%B %d %Y - %H:%M:%S'),
                            }, key=settings.SECRET_KEY, algorithm=settings.SECRET_ALGORITM)
                attrs['refresh_token'] = new_refresh_token
            except:
                raise ProjectException(445,_('Unauthorized'),_('The refresh token is invalid.'),
                                status.HTTP_401_UNAUTHORIZED)
        except:
            raise ProjectException(445,_('Unauthorized'),_('The refresh token is invalid.'),
                                status.HTTP_401_UNAUTHORIZED)
        return attrs
    def update(self, instance, validated_data):
        
        for attr,value in validated_data.items():
            setattr(instance,attr,value)
        instance.save()
        instance.access_token = instance.key
        return instance


# User:
class UserRegisterSerializer(serializers.ModelSerializer):
    ROLE_CHOICE = (("admin", "admin"),("client", "client"))
    class Meta:
        model = UserModel
        fields = ('id', 'first_name', 'last_name','cellphone','company','role')
        read_only_fields = ('username', 'avatar', 'email', 'status', 
                            'gender','level','registered')
        # extra_kwargs = {'password': {'write_only': True},}

    first_name  = serializers.CharField(max_length=150)
    last_name   = serializers.CharField(max_length=150)
    cellphone   = serializers.CharField(max_length=15,required=True)
    company     = serializers.PrimaryKeyRelatedField(
                    many=False,required=False,
                    queryset=CompanyModel.objects.all(),
                    error_messages={
                        "does_not_exist": _("company does not exist"),
                        "invalid": _("invalid value"),
                    },
                )
    role        = serializers.ChoiceField(choices=ROLE_CHOICE,default='client')

    def validate(self, attrs):
        self.user  = self.context['request'].user
        _company   = attrs.get('company', None)
        _cellphone = attrs.get('cellphone', None)
        
        if _cellphone:
            if not validate_phone_number(_cellphone,"IR"):
                raise ProjectException(807,
                                _("validation error"),_("'Cellphone': this field is invalid"),
                                status.HTTP_400_BAD_REQUEST)
            try:
                UserModel.objects.get(company=_company,cellphone=_cellphone)
                raise ProjectException(808,
                                'validation error','There is a user with this cellphone in this system.',
                                status_code=status.HTTP_400_BAD_REQUEST)
            except UserModel.DoesNotExist:
                pass
        
        return attrs
    def create(self, validated_data):
        _role = validated_data.pop('role', None)
        # Create Username:
        first = validated_data.get('first_name','')
        last  = validated_data.get('last_name','')
        _name = "".join([first,last])
        validated_data['username'] = generate_username(_name)
        if self.user.pk:
            validated_data['created_by']  = self.user
            validated_data['modified_by'] = self.user
        new_instance = self.Meta.model(**validated_data)
        _password = str(get_verfication_code())
        if _password is not None:
            new_instance.set_password(_password)
            new_instance.verification_code = _password
        new_instance.status = 1
        new_instance.is_active = True
        # new_instance.registered = True
        new_instance.role = _role
        new_instance.save()
        return new_instance
class UserSerializer(serializers.ModelSerializer):
    ROLE_CHOICE = (("admin", "admin"),("client", "client"))
    class Meta:
        model = UserModel
        fields = ('id', 'first_name', 'last_name','cellphone','company','role')
        read_only_fields = ('username', 'avatar', 'email', 'status', 
                            'gender','level','registered')
        # extra_kwargs = {'password': {'write_only': True},}

    first_name  = serializers.CharField(max_length=150,required=False)
    last_name   = serializers.CharField(max_length=150,required=False)
    cellphone   = serializers.CharField(max_length=15,required=True)
    company     = serializers.PrimaryKeyRelatedField(many=False,required=False,
                        queryset=CompanyModel.objects.all(),
                        error_messages={
                            "does_not_exist": _("company does not exist"),
                            "invalid": _("invalid value"),
                        },
                    )
    role        = serializers.ChoiceField(choices=ROLE_CHOICE,default='client')


    def validate(self, attrs):
        self.user  = self.context['request'].user
        _cellphone = attrs.get('cellphone', None)
        _company   = attrs.pop('company', None)
        # # Check Company Field:
        # if self.user.is_superuser:
        #     if _company is None:
        #         raise ProjectException(807,_("validation error"),_("'company':This field cannot none"),status_code=status.HTTP_400_BAD_REQUEST)
        #     else:
        #         attrs['company'] = _company
        # elif self.user.company:
        #     if _company and (_company != self.user.company):
        #         raise ProjectException(821, _('Forbidden'),
        #                                 _('You do not have permission to perform this action.'),
        #                                 status.HTTP_403_FORBIDDEN)
        #     else:
        #         _company = self.user.company
        #         attrs['company'] = self.user.company
        # else:
        #     raise ProjectException(821, _('Forbidden'),
        #                                 _('You do not have permission to perform this action.'),
        #                                 status.HTTP_403_FORBIDDEN)
        # Check unique Field:
        if _cellphone:
            if not validate_phone_number(_cellphone,"IR"):
                raise ProjectException(807,
                                _("validation error"),_("'Cellphone': this field is invalid"),
                                status.HTTP_400_BAD_REQUEST)
            try:
                UserModel.objects.get(company=_company,cellphone=_cellphone)
                raise ProjectException(808,
                                'validation error','There is a user with this cellphone in this system.',
                                status_code=status.HTTP_400_BAD_REQUEST)
            except UserModel.DoesNotExist:
                pass
        
        return attrs
    def create(self, validated_data):
        _role = validated_data.pop('role', None)

        _password = validated_data.pop('password', None) 
        if self.user.pk:
            validated_data['created_by'] = self.user
            validated_data['modified_by'] = self.user
        # Create Username:
        first = validated_data.get('first_name','')
        last  = validated_data.get('last_name','')
        _name = "".join([first,last])
        validated_data['username'] = generate_username(_name)
        # Create Password:
        _password = str(get_verfication_code())
        # Create User:
        new_instance = self.Meta.model(**validated_data)
        if _password is not None:
            new_instance.set_password(_password)
            new_instance.verification_code = _password
        new_instance.status = 1
        new_instance.is_active = True
        # new_instance.registered = True
        new_instance.role = _role
        new_instance.save()
        return new_instance
#User Update:
class UserUpdateSerializer(serializers.ModelSerializer):
    from rest_framework.validators import UniqueValidator
    class Meta:
        model = UserModel
        fields = ('id', 'first_name', 'last_name', 'username', 'email','cellphone','status', 'gender','avatar',
                  "father_name","id_no","national_code","birthday","birthplace","married","children"
                    )
        read_only_fields = ('status','level',)

    avatar      = serializers.ImageField(max_length=None,use_url=True,allow_empty_file=True,required = False) #default='avatar/no-image.jpg',
    first_name  = serializers.CharField(max_length=30,required = False)
    last_name   = serializers.CharField(max_length=150,required = False)
    username    = serializers.CharField(max_length=150,validators=[UniqueValidator(queryset=UserModel.objects.all())],required=False,)
    email       = serializers.EmailField(required=False)
    cellphone   = serializers.CharField(max_length=15,required=False)
    gender      = serializers.ChoiceField(choices=UserModel.GENDER_CHOICE,required=False)
    
    ###User Patient Profile
    father_name   = serializers.CharField(max_length=150, allow_blank=True, required=False)
    id_no         = serializers.IntegerField(default=0, required=False)
    national_code = serializers.CharField(max_length=80, allow_blank=True, required=False)
    birthday      = serializers.CharField(required=False)
    birthplace    = serializers.CharField(max_length=70, allow_blank=True, required=False)
    married       = serializers.BooleanField(default=False, required=False)
    children      = serializers.IntegerField(default=0, required=False)
    

    def validate(self, attrs):
        self.user = get_user(context=self.context)
        _password = attrs.get('password', None)
        _username = attrs.pop('username',None)
        _email = attrs.get('email', None)
        _cellphone = attrs.get('cellphone', None)
        instance = self.instance
        #--------Check Company Field:-----------
        # if self.user.is_superuser or (self.user.company and (instance.company == self.user.company)):
        #     pass
        # else:
        #     raise ProjectException(821, _('Forbidden'),
        #                                 _('You do not have permission to perform this action.'),
        #                                 status.HTTP_403_FORBIDDEN)
        #--------Check Unique Fields:-----------
        if _email:
            try:
                UserModel.objects.exclude(pk=instance.pk).get(email=_email)
                raise ProjectException(809,'validation error','There is a user with this email in this system.',status_code=status.HTTP_400_BAD_REQUEST)
            except UserModel.DoesNotExist:
                pass
        if _cellphone:
            if not validate_phone_number(_cellphone,"IR"):
                raise ProjectException(807,
                                _("validation error"),_("'Cellphone': this field is invalid"),
                                status.HTTP_400_BAD_REQUEST)
            try:
                UserModel.objects.exclude(pk=instance.pk).get(cellphone=_cellphone)
                raise ProjectException(808,
                                'validation error','There is a user with this cellphone in this system.',
                                status_code=status.HTTP_400_BAD_REQUEST)
            except UserModel.DoesNotExist:
                pass
        if _username:
            try:
                _username = _username.lower()
                UserModel.objects.exclude(pk=instance.pk).get(username=_username)
                raise ProjectException(810,'validation error','There is a user with this username in this system.',status_code=status.HTTP_400_BAD_REQUEST)
            except UserModel.DoesNotExist:
                if len(_username) < 4:
                    raise ProjectException(811, _('validation error'),_("username cannot les than 4 digit"),status.HTTP_400_BAD_REQUEST)
                attrs['username']=_username
        
        ##--------Profile Fields:---------------
        profile_fields = ["father_name","id_no","national_code","birthday","birthplace","married","children",]
        profile = {}
        for attr in profile_fields:
            value = attrs.pop(attr,None)
            if value:
                profile.update({attr:value})
        attrs['profile'] = profile
        
        return attrs
    def update(self, instance, validated_data):
        profile = validated_data.pop('profile', None)
        if profile:
            _birth_day = profile.pop("birthday", None)
            if _birth_day:
                _birth_day = convert_shamsi_string_to_miladi_date(_birth_day)
                if _birth_day is None:
                    raise ProjectException(807,_("validation error"),_("birthday is invalid."),status.HTTP_400_BAD_REQUEST,)
                else:
                    profile["birthday"] = _birth_day
        password = validated_data.pop('password', None)
        if password is not None:
            new_instance = self.Meta.model()
            validated_data['verification_code'] = password
            new_instance.set_password(password)
            validated_data['password'] = new_instance.password
        validated_data['modified_by'] = self.user
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.profile_data = profile
        instance.save()
        return instance
#User Info:
class UserPermissionInfoSerializer(serializers.Serializer):
    pass
class UserInfoSerializer(serializers.Serializer):

    id          = serializers.IntegerField(read_only=True)
    avatar      = serializers.SerializerMethodField(read_only=True)
    first_name  = serializers.CharField(read_only=True)
    last_name   = serializers.CharField(read_only=True)
    name        = serializers.SerializerMethodField(read_only=True)
    username    = serializers.CharField(read_only=True)
    email       = serializers.EmailField(read_only=True)
    cellphone   = serializers.CharField(read_only=True)
    gender      = serializers.CharField(read_only=True)
    status      = serializers.IntegerField(read_only=True)
    is_active   = serializers.BooleanField(read_only=True)
    registered  = serializers.BooleanField(read_only=True)
    # code        = serializers.CharField(read_only=True)
    level       = serializers.IntegerField(read_only=True)
    company     = serializers.PrimaryKeyRelatedField(
                        many=False,required=False,queryset=CompanyModel.objects.all(),
                        error_messages={
                            "does_not_exist": _("company does not exist"),
                            "invalid": _("invalid value"),
                        },
                    )
    user_permissions = UserPermissionInfoSerializer(many=True,read_only=True)
    # roles   = serializers.SerializerMethodField(read_only=True, method_name="get_roles")
    profile = ProfileInfoSerializer()


    def get_avatar(self, obj):
        avatar = None
        if obj.avatar:
            avatar = obj.avatar.url
        return avatar
    def get_name(self, obj):
        _name = "".join([obj.first_name, ' ', obj.last_name])
        return _name
    def get_roles(self, obj):
        if obj.is_superuser:
            roles = {
                    "title": "superuser",
                    "states": {"all": ["manage"]}
                }
            return [roles]
        else:
            list_role = UserRoleModel.objects.filter(user=obj)
            roles = [obj.role for obj in list_role]
            _serializer=RoleInfoGetSerializer(roles,many=True)
            return _serializer.data

#Avatar
class UserUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserModel
        fields = ("id","avatar",)
        # read_only_fields = ()

    avatar = Base64ImageField(required=True,max_length=None,use_url=True,)

    def validate(self, attrs):
        self.user = self.context["request"].user
        return attrs
    def update(self, instance, validated_data):
        if self.user and self.user.pk:
            validated_data["modified_by"] = self.user
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
#User Forgot Password:

#User Resend Password:
class UserResendPasswordSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserModel
        fields = ('id', 'cellphone')
    cellphone   = serializers.CharField(max_length=15,required=True)

    def validate(self, attrs):
        self.user = self.context['request'].user
        _cellphone = attrs.get('cellphone', None)
        
        #--------Check Unique Fields:-----------
        if _cellphone:
            if not validate_phone_number(_cellphone,"IR"):
                raise ProjectException(807,
                                _("validation error"),_("'Cellphone': this field is invalid"),
                                status.HTTP_400_BAD_REQUEST)
            try:
                self.instance = UserModel.objects.get(cellphone=_cellphone)
                if not self.instance.is_active:
                    raise ProjectException(802, _('authentication error'),
                                           _('User is not active on the system.'),
                                           status.HTTP_400_BAD_REQUEST)
            except ObjectDoesNotExist:
                raise ProjectException(820, _('not found'),
                                       _('No user with this cellphone is registered in the system.'),
                                       status.HTTP_404_NOT_FOUND)
        
        return attrs
    def update(self, instance, validated_data):
        _password = str(get_verfication_code())
        if (_password is not None) and (not instance.is_superuser):
            new_instance = self.Meta.model()
            validated_data['verification_code'] = _password
            new_instance.set_password(_password)
            validated_data['password'] = new_instance.password        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance

#----------User Multi ID:----------
class UserStatusSerializer(serializers.Serializer):
    STATUS_CHOICE_RE = ((0, 'unpublish'), (1, 'publish'))
    id = serializers.PrimaryKeyRelatedField(
            many=True,
            queryset=UserModel.objects.all(),
            error_messages={
                'does_not_exist': _("user does not exist"),
                'invalid': _('invalid data')
            },)
    status = serializers.ChoiceField(choices=STATUS_CHOICE_RE)

    def validate(self, attrs):
        status = attrs.get('status',None)
        if (status is None) and (status not in [0,1]):
            raise ProjectException(827, _('validation error'),
                                    _('Status field is Invalid.'),
                                    status.HTTP_400_BAD_REQUEST)
        return attrs
class UserSomeSerializer(serializers.Serializer):
    id = serializers.PrimaryKeyRelatedField(
            many=True,
            queryset=UserModel.objects.all(),
            error_messages={
                'does_not_exist': _("user does not exist"),
                'invalid': _('invalid data')
            },)
    def validate(self, attrs):
        return attrs


#----------User Role:----------
class UserRoleInSerializer(serializers.Serializer):  
    role = serializers.PrimaryKeyRelatedField(
            many=False,queryset=RoleModel.objects.all(),
            error_messages={
                "does_not_exist": _("role does not exist"),
                "invalid": _("invalid value"),
            },
        )
class UserRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserRoleModel
        fields = ("id", "user", "role",)

    user = serializers.PrimaryKeyRelatedField(
            many=False,queryset=UserModel.objects.all(),
            error_messages={
                "does_not_exist": _("user does not exist"),
                "invalid": _("invalid value"),
            },
        )
    role = serializers.PrimaryKeyRelatedField(
            many=False,queryset=RoleModel.objects.all(),
            error_messages={
                "does_not_exist": _("role does not exist"),
                "invalid": _("invalid value"),
            },
        )

    def validate(self, attrs):

        return attrs
    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
    def create(self, validated_data):
        _new_instance = self.Meta.model(**validated_data)
        _new_instance.save()
        return _new_instance


    


  






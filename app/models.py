from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser
import shortuuid
import os

STATUS_CHOICE = ((-1, 'trash'), (0, 'unpublish'), (1, 'publish'))


class AccountModel(models.Model):    
    
    card_no     = models.BigIntegerField(unique=True)
    bank_name   = models.CharField(max_length=150,null=True)
    name        = models.CharField(max_length=130,null=True)
    owner       = models.ForeignKey('UserModel',on_delete=models.CASCADE,related_name='accounts',verbose_name='owner',null=True)
    status      = models.SmallIntegerField(choices=STATUS_CHOICE,default=1)

    created     = models.DateTimeField(auto_now_add=True, editable=False)
    modified    = models.DateTimeField(auto_now=True)
    class Meta:
        db_table = 'tbl_account'
        managed = True
        verbose_name = 'account'
        verbose_name_plural = 'accounts'


class MellatAccountModel(models.Model):    
    MELLAT_CHOICE = ((0,'none'),(1,'add'),(2,'update'),(3,'delete'),
                     (11,'inserted_error'),(12,'updated_error'),(13,'deleted_error')
                    )

    account       = models.OneToOneField('AccountModel',on_delete=models.CASCADE,related_name='mellat',primary_key=True)
    # national_code = models.CharField(max_length=10,null=True)
    mellat_status = models.IntegerField(choices=MELLAT_CHOICE,default=0)
    mellat_date   = models.DateTimeField(null=True)
    mellat_result = models.IntegerField(null=True)

    created     = models.DateTimeField(auto_now_add=True, editable=False)
    modified    = models.DateTimeField(auto_now=True)
    class Meta:
        db_table = 'tbl_mellat_account'
        managed = True
        verbose_name = 'mellat_account'
        verbose_name_plural = 'mellat_accounts'


class MellatDiscountPackageModel(models.Model):
    packageId    = models.CharField(max_length=130,primary_key=True)
    packageTitle = models.CharField(max_length=130)
    isGeneral    = models.BooleanField()
    startDate    = models.CharField(max_length=8)
    endDate      = models.CharField(max_length=8)
    
    class Meta:
        db_table            = 'tbl_discount_package'
        managed             = True
        verbose_name        = 'discount_package'
        verbose_name_plural = 'discount_packages'


class MellatDiscountPackageContentModel(models.Model):
    discountpackage     = models.ForeignKey('MellatDiscountPackageModel',on_delete=models.CASCADE)
    merchantId          = models.CharField(max_length=130,primary_key=True)
    merchantTitle       = models.CharField(max_length=130)
    customerShare       = models.IntegerField()
    submerchantTitle    = models.CharField(max_length=130)
    submerchantId       = models.CharField(max_length=130)
    credit              = models.IntegerField()
    cashBack            = models.IntegerField()
    startDate           = models.CharField(max_length=8)
    endDate             = models.CharField(max_length=8)
    
    class Meta:
        db_table            = 'tbl_discount_package_content'
        managed             = True
        verbose_name        = 'discount_package_content'
        verbose_name_plural = 'discount_package_contents'


class MellatAssignPackageToMemberModel(models.Model):
    owner           = models.ForeignKey('UserModel',on_delete=models.CASCADE,related_name="packages")
    packageId       = models.CharField(max_length=130)
    voucherCode     = models.CharField(max_length=130,null=True,blank=True)
    generateNewCode = models.BooleanField(default=False)
    startDate       = models.DateField(null=True)
    endDate         = models.DateField(null=True)
    
    class Meta:
        db_table            = 'tbl_package_member'
        managed             = True
        verbose_name        = 'package_member'
        verbose_name_plural = 'package_members'


class CompanyModel(models.Model):
    title = models.CharField(max_length=130)

    created_by  = models.ForeignKey('UserModel',on_delete=models.CASCADE,related_name='company_creator',verbose_name='creator',editable=False)
    modified_by = models.ForeignKey('UserModel',on_delete=models.CASCADE,related_name='company_modifier',verbose_name='modifier')
    created     = models.DateTimeField(auto_now_add=True, editable=False)
    modified    = models.DateTimeField(auto_now=True)
    class Meta:
        db_table = 'tbl_company'
        managed = True
        verbose_name = 'company'
        verbose_name_plural = 'companies'


class ChartModel(models.Model):
    post = models.TextField()
    parent = models.ForeignKey(
        "ChartModel", on_delete=models.CASCADE, related_name="subordinates", null=True
    )
    order = models.SmallIntegerField(default=0)

    created_by = models.ForeignKey("UserModel",on_delete=models.SET_NULL,
        related_name="chart_creator",editable=False,null=True,
    )
    modified_by = models.ForeignKey(
        "UserModel", on_delete=models.SET_NULL, related_name="chart_modifier", null=True
    )
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "tbl_chart"
        managed = True


class ChartAccessModel(models.Model):
    chart = models.ForeignKey(
        "ChartModel", on_delete=models.CASCADE, related_name="chart_access"
    )
    state = models.ForeignKey("StateModel", on_delete=models.CASCADE)

    class Meta:
        db_table = "tbl_chart_access"
        managed = True
        unique_together = ["chart", "state"]

    
class ChartPermissionModel(models.Model):
    access = models.ForeignKey(
        "ChartAccessModel", on_delete=models.CASCADE, related_name="chart_permission"
    )
    operate = models.ForeignKey("operateModel", on_delete=models.CASCADE)

    class Meta:
        db_table = "tbl_chart_permission"
        managed = True
        unique_together = ["access", "operate"]



class GalleryModel(models.Model):
    image = models.ImageField(upload_to = 'image/')
    store = models.ForeignKey('StoreModel',on_delete=models.CASCADE,related_name='galleries',verbose_name='galleries')
    
    created_by=models.ForeignKey('UserModel',on_delete=models.CASCADE,related_name='gallery_creator',verbose_name='creator',editable=False)
    modified_by=models.ForeignKey('UserModel',on_delete=models.CASCADE,related_name='gallery_modifier',verbose_name='modifier')
    created=models.DateTimeField(auto_now_add=True, editable=False)
    modified=models.DateTimeField(auto_now=True)
    class Meta:
        db_table = 'tbl_gallery'
        managed = True
        verbose_name = 'gallery'
        verbose_name_plural = 'galleries'

    def delete(self, using=None, keep_parents=False):
        if self.image:
            self.image.storage.delete(self.image.name)
        return super().delete(using=using, keep_parents=keep_parents)


def supermakedirs(path):
    if not path or os.path.exists(path):
        return []
    (head, tail) = os.path.split(path)
    res = supermakedirs(head)
    try:
        os.mkdir(path)
    except:
         return []
       
    res += [path]
    return res       
def upload_excell_file(instance,filename):
    _name=shortuuid.uuid()
    _ext    = filename.split(".")[-1].lower()
    _folder = ''.join([settings.MEDIA_ROOT,'/temp/'])
    supermakedirs(_folder)
    return ''.join(['temp/', _name,".",_ext])
class ImportModel(models.Model):    
    # TEMPLATE_CHOICE=(('template_1','template_1'),('template_2','template_2'),('template_3','template_3'))  
    STATUS_CHOICE=(('new','new'),('doing','doing'),('done','done'),('error','error'))  

    file            = models.FileField(upload_to = upload_excell_file, default = '')
    company         = models.ForeignKey('CompanyModel',on_delete=models.CASCADE,null=True)
    added           = models.PositiveIntegerField(default=0)
    errors          = models.PositiveIntegerField(default=0)
    error_col       = models.IntegerField(default=-1)
    whole           = models.PositiveIntegerField(default=0)
    rows            = models.PositiveIntegerField(default=2)
    import_date     = models.DateTimeField(null=True)
    import_status   = models.CharField(choices=STATUS_CHOICE ,max_length=10 ,default='new')


    created_by  = models.ForeignKey('UserModel',on_delete=models.CASCADE,related_name='import_creator',verbose_name='creator',editable=False)
    modified_by = models.ForeignKey('UserModel',on_delete=models.CASCADE,related_name='import_modifier',verbose_name='modifier')
    created     = models.DateTimeField(auto_now_add=True, editable=False)
    modified    = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'tbl_import'
        managed = True
        verbose_name = 'import'
        verbose_name_plural = 'import'
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
    def delete(self, using=None, keep_parents=False):
        if self.file:
            self.file.storage.delete(self.file.name)
        return super().delete(using=using, keep_parents=keep_parents)

class ImportExceptionModel(models.Model):
    Import      = models.ForeignKey('ImportModel',on_delete=models.CASCADE,related_name='exceptions')
    row_number  = models.IntegerField(default=-1)
    data        = models.JSONField(default=dict)
    description = models.TextField(blank=True)
    
    class Meta:
        db_table = 'tbl_import_exception'
        managed = True
        verbose_name = 'import_exception'
        verbose_name_plural = 'import_exceptions'



class OperateModel(models.Model):
    title = models.CharField(max_length=130, primary_key=True)

    created_by = models.ForeignKey('UserModel',
                                   on_delete=models.SET_NULL,
                                   related_name='operate_creator',
                                   null=True,
                                   editable=False)
    modified_by = models.ForeignKey('UserModel',
                                    on_delete=models.SET_NULL,
                                    related_name='operate_modifier',null=True)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'tbl_operate'
        managed = True
        unique_together = ['title']
        verbose_name = 'operate'
        verbose_name_plural = 'operates'



class ProfileModel(models.Model):
    owner         = models.OneToOneField("UserModel",related_name="profile",on_delete=models.CASCADE,primary_key=True)
    father_name   = models.CharField(max_length=80, blank=True)
    id_no         = models.PositiveIntegerField(default=0) 
    birthday      = models.DateField(auto_now=False, auto_now_add=False, null=True)
    birthplace    = models.CharField(max_length=70, blank=True)
    married       = models.BooleanField(default=False)
    children      = models.PositiveIntegerField(default=0)
    national_code = models.CharField(max_length=10, blank=True)
    old_national_code = models.CharField(max_length=10,null=True)
    # province    = models.CharField(max_length=50, blank=True)
    # city        = models.CharField(max_length=50, blank=True)
    # address = models.TextField(blank=True)
    # status = models.SmallIntegerField(choices=STATUS_CHOICE, default=1)

    class Meta:
        db_table = "tbl_profile"
        managed = True



class RoleModel(models.Model):
    title  = models.CharField(max_length=130, primary_key=True)
    parent = models.ForeignKey('RoleModel',
                                   on_delete=models.SET_NULL,
                                   related_name='subordinates',
                                   editable=False,
                                   null=True)
    order  = models.SmallIntegerField(default=0)

    
    created_by = models.ForeignKey('UserModel',
                                   on_delete=models.SET_NULL,
                                   related_name='role_creator',
                                   editable=False,
                                   null=True)
    modified_by = models.ForeignKey('UserModel',
                                    on_delete=models.SET_NULL,
                                    related_name='role_modifier',
                                    null=True)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'tbl_role'
        managed = True
        verbose_name = 'role'
        verbose_name_plural = 'roles'



class RoleAccessModel(models.Model):
    role = models.ForeignKey(
        "RoleModel", on_delete=models.CASCADE, related_name="role_accesses"
    )
    state = models.ForeignKey("StateModel", on_delete=models.CASCADE, related_name="role_state")

    class Meta:
        db_table = "tbl_role_access"
        managed = True
        unique_together = ["role", "state"]
        verbose_name = "role_access"
        verbose_name_plural = "role_accesses"


class RolePermissionModel(models.Model):
    access = models.ForeignKey(
        "RoleAccessModel", on_delete=models.CASCADE, related_name="role_permissions"
    )
    operate = models.ForeignKey("operateModel", on_delete=models.CASCADE)

    class Meta:
        db_table = "tbl_role_permission"
        managed = True
        unique_together = ["access", "operate"]
        verbose_name = "role_permission"
        verbose_name_plural = "role_permissions"


class ServiceModel(models.Model):
    title           = models.CharField(max_length=150,blank=False)
    order           = models.PositiveIntegerField(default=0)
    image           = models.ImageField(upload_to = 'icons/',null=True)
    icon            = models.CharField(max_length=130 ,null=True,blank=True)
    color           = models.CharField(max_length=7,null=True,blank=True)
    description     = models.TextField(null=True,blank=True)
    parent          = models.ForeignKey('ServiceModel',on_delete=models.CASCADE,related_name='sub_services',verbose_name='modifier',null=True)
    is_publish      = models.BooleanField(default=True)
    is_virtual      = models.BooleanField(default=False)  
    is_show_stores  = models.BooleanField(default=True)
    status          = models.SmallIntegerField(choices=STATUS_CHOICE,default=1)
    status_old      = models.SmallIntegerField(choices=STATUS_CHOICE,default=1)

    created_by  = models.ForeignKey('UserModel',on_delete=models.CASCADE,related_name='service_creator',verbose_name='creator',editable=False)
    modified_by = models.ForeignKey('UserModel',on_delete=models.CASCADE,related_name='service_modifier',verbose_name='modifier')
    created     = models.DateTimeField(auto_now_add=True, editable=False)
    modified    = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'tbl_service'
        managed = True
        verbose_name = 'service'
        verbose_name_plural = 'services'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
    def delete(self, using=None, keep_parents=False):
        if self.image:
            self.image.storage.delete(self.image.name)
        return super().delete(using=using, keep_parents=keep_parents)


class SettingModel(models.Model):
    key   = models.CharField(max_length=80)
    value = models.TextField()
    
    
    created  = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True)
    class Meta:
        db_table = 'tbl_setting'
        managed = True
        verbose_name = 'setting'
        verbose_name_plural = 'settings'


class StateModel(models.Model):
    title = models.CharField(max_length=130, primary_key=True)

    created_by = models.ForeignKey('UserModel',
                                   on_delete=models.SET_NULL,
                                   related_name='state_creator',
                                   null=True,
                                   editable=False)
    modified_by = models.ForeignKey('UserModel',
                                    on_delete=models.SET_NULL,
                                    related_name='state_modifier',null=True,)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'tbl_state'
        managed = True
        unique_together = ['title']
        verbose_name = 'state'
        verbose_name_plural = 'states'


class StoreModel(models.Model):
    title       = models.CharField(max_length=150,blank=False)
    code        = models.CharField(max_length=6,unique=True)
    icon        = models.ImageField(upload_to = 'icons/',null=True)
    latitude    = models.FloatField(default=0.0)
    longitude   = models.FloatField(default=0.0)
    discount    = models.CharField(max_length=130)
    services    = models.ManyToManyField('ServiceModel',related_name='stores', through="StoreServiceModel")
    order       = models.PositiveIntegerField(default=0)
    parent      = models.ForeignKey('StoreModel',on_delete=models.CASCADE,related_name='sub_stores',null=True)
    tel         = models.CharField(max_length=15,null=True,blank=True)
    web_site    = models.TextField(null=True,blank=True)
    is_virtual  = models.BooleanField(default=False)   
    is_publish  = models.BooleanField(default=True)
    has_branch  = models.BooleanField(default=False)
    province    = models.PositiveSmallIntegerField(null=True)
    city        = models.CharField(max_length=70,null=True,blank=True)
    district    = models.CharField(max_length=30,null=True,blank=True)
    address     = models.TextField(null=True,blank=True)
    description = models.TextField(null=True,blank=True)
    status      = models.SmallIntegerField(choices=STATUS_CHOICE,default=1)
    status_old  = models.SmallIntegerField(choices=STATUS_CHOICE,default=1)
    
    created_by  = models.ForeignKey('UserModel',on_delete=models.CASCADE,related_name='store_creator',verbose_name='creator',editable=False)
    modified_by = models.ForeignKey('UserModel',on_delete=models.CASCADE,related_name='store_modifier',verbose_name='modifier')
    created     = models.DateTimeField(auto_now_add=True, editable=False)
    modified    = models.DateTimeField(auto_now=True)
    class Meta:
        db_table = 'tbl_store'
        managed = True
        verbose_name = 'store'
        verbose_name_plural = 'stores'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
    def delete(self, using=None, keep_parents=False):
        if self.icon:
            self.icon.storage.delete(self.icon.name)
        return super().delete(using=using, keep_parents=keep_parents)


class StoreServiceModel(models.Model):
    store   = models.ForeignKey("StoreModel",on_delete=models.CASCADE, related_name="service")
    service = models.ForeignKey("ServiceModel",on_delete=models.CASCADE)

    created_by  = models.ForeignKey("UserModel",on_delete=models.SET_NULL,related_name="store_service_creator",editable=False,null=True,)
    modified_by = models.ForeignKey("UserModel",on_delete=models.SET_NULL,related_name="store_service_modifier",null=True,)
    created     = models.DateTimeField(auto_now_add=True, editable=False)
    modified    = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "tbl_store_service"
        unique_together = ["store", "service"]
        managed = True
        verbose_name = "store_service"
        verbose_name_plural = "store_services"


class TokenModel(models.Model):
    user = models.ForeignKey('UserModel',on_delete=models.CASCADE,related_name='bearer_token',)
    key = models.TextField(unique=True)
    refresh_token = models.TextField(unique=True)
    remote_addr = models.TextField()
    user_agent = models.TextField()
    player_id = models.TextField(unique=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'tbl_token'
        managed = True
        verbose_name = "token"
        verbose_name_plural = "tokens"


class UserRoleModel(models.Model):
    user = models.ForeignKey("UserModel", on_delete=models.CASCADE, related_name="roles")
    role = models.ForeignKey("RoleModel", on_delete=models.CASCADE, related_name="role_user")

    class Meta:
        db_table = "tbl_user_role"
        managed = True
        unique_together = ["user", "role"]
        verbose_name = "user_role"
        verbose_name_plural = "user_roles"


def productFileUser(instance, filename):
    return "".join(
        [
            "user/avatar/",
            str(instance.username),
            "_",
            str(shortuuid.ShortUUID().random(length=10)),
            ".jpg",
        ]
    )
class UserModel(AbstractUser):
    groups = None
    user_permissions = None
    GENDER_CHOICE   = (('none', 'none'),('male', 'male'), ('female', 'female'))
    LEVEL_CHOICE    = ((0,'normal'),(1,'high'),)
    
    avatar      = models.ImageField(upload_to='avatar/',null=True)
    gender      = models.CharField(choices=GENDER_CHOICE,max_length=8,default='male')
    cellphone   = models.CharField(max_length=15, blank=True)
    email       = models.CharField(max_length=130, blank=True,null=True)
    is_active   = models.BooleanField(default=True)
    is_staff    = models.BooleanField(default=False)
    status      = models.SmallIntegerField(choices=STATUS_CHOICE, default=1)
    verification_code = models.CharField(max_length=15, blank=True)
    # old_vc = models.CharField(max_length=15, blank=True)

    # code    = models.CharField(max_length=64, blank=True)
    company     = models.ForeignKey('CompanyModel',on_delete=models.CASCADE,related_name='users',null=True)
    level       = models.SmallIntegerField(choices=LEVEL_CHOICE,default=1)
    registered  = models.BooleanField(default=True)


    login_error = models.IntegerField(default=0)
    deactive_expire = models.DateTimeField(null=True)

    # active_by = models.ForeignKey('UserModel',on_delete=models.CASCADE,related_name='user_activator',null=True)
    created_by = models.ForeignKey('UserModel',
                                   on_delete=models.SET_NULL,
                                   related_name='user_creator',
                                   null=True,
                                   editable=False)
    modified_by = models.ForeignKey('UserModel',
                                    on_delete=models.SET_NULL,
                                    related_name='user_modifier',
                                    null=True)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'tbl_user'
        managed = True
        verbose_name = 'user'
        verbose_name_plural = 'users'
    
    def save(self, *args, **kwargs):
        if self.is_superuser:
            pass
        super().save(*args, **kwargs)
    def delete(self, using=None, keep_parents=False):
        if self.avatar:
            self.avatar.storage.delete(self.avatar.name)
        return super().delete(using=using, keep_parents=keep_parents)


class UserAccessModel(models.Model):    
    user = models.ForeignKey(
        "UserModel", on_delete=models.CASCADE, related_name="permissions"
    )  # user_accesses
    state = models.ForeignKey("StateModel", on_delete=models.CASCADE)

    class Meta:
        db_table = "tbl_user_access"
        managed = True
        unique_together = ["user", "state"]


class UserPermissionModel(models.Model):
    access = models.ForeignKey(
        "UserAccessModel", on_delete=models.CASCADE, related_name="user_permissions"
    )
    operate = models.ForeignKey("operateModel", on_delete=models.CASCADE)

    class Meta:
        db_table = "tbl_user_permission"
        managed = True
        unique_together = ["access", "operate"]


class UserChartModel(models.Model):
    user = models.ForeignKey("UserModel", on_delete=models.CASCADE, related_name="positions")
    chart = models.ForeignKey("ChartModel", on_delete=models.CASCADE)

    class Meta:
        db_table = "tbl_user_position"
        managed = True
        unique_together = ["user", "chart"]


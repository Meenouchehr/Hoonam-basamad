from django.db.models.signals import pre_delete,post_delete,pre_save,post_save
from django.dispatch import receiver
from django.core.exceptions import ObjectDoesNotExist
from app.serializers import *
from app.utils import *
from app.mellat import AssignPackageToMember


# Account:
@receiver(pre_save, sender=AccountModel)
def pre_save_account(sender, instance, *args, **kwargs):
    try:
        instance.old_owner = instance.__class__.objects.get(pk=instance.pk).owner
    except ObjectDoesNotExist:
        pass
@receiver(post_save, sender=AccountModel)
def post_save_account(sender, instance=None, created=False, **kwargs):    
    if created:
        MellatAccountModel.objects.create(account=instance,mellat_status=1)
        if not instance.owner.profile.national_code:
            rand_national_code = generate_national_code()
            instance.owner.profile.national_code = rand_national_code
            instance.owner.profile.save()
    else:
        _owner = None
        _old_owner = None
        if hasattr(instance, "old_owner") and instance.old_owner:
            _old_owner = instance.old_owner
        if hasattr(instance, "owner") and instance.owner:
            _owner = instance.owner
        if _old_owner and (_old_owner != _owner):
            if not _owner.profile.national_code:
                _owner.profile.old_national_code = _old_owner.profile.national_code
            else:
                if _old_owner.registered:
                    rand_national_code = generate_national_code()
                    instance.owner.profile.national_code = rand_national_code
                else:
                    _owner.profile.national_code = _old_owner.profile.national_code
                _owner.profile.old_national_code = _old_owner.profile.old_national_code
            _owner.profile.save()
            # delete test user: 
            if not _old_owner.registered:
                _old_owner.delete()
        try:
            mellat = MellatAccountModel.objects.get(account=instance)
            if mellat.mellat_status == 0:
                mellat.mellat_status = 2
                mellat.save()
        except:
            pass


# MellatAccount:
@receiver(pre_save, sender=MellatAccountModel)
def pre_save_mellat_account(sender, instance, *args, **kwargs):
    try:
        instance.old_mellat_status = instance.__class__.objects.get(pk=instance.pk).mellat_status
    except ObjectDoesNotExist:
        pass

@receiver(post_save, sender=MellatAccountModel)
def post_save_mellat_account(sender, instance=None, created=False, **kwargs):    
    _mellat_status = None
    _old_mellat_status = None
    if hasattr(instance, "old_mellat_status") and instance.old_mellat_status:
        _old_mellat_status = instance.old_mellat_status
    if hasattr(instance, "mellat_status") and instance.mellat_status:
        _mellat_status = instance.mellat_status
    if (_mellat_status==0) and (_old_mellat_status != _mellat_status):
        if not _mellat_status.profile.national_code:
            instance.account.owner.profile.old_national_code = instance.account.owner.profile.national_code
            instance.account.owner.profile.save()




# Company:


# Gallery:
@receiver(pre_save, sender=GalleryModel)
def pre_save_gallery(sender, instance, *args, **kwargs):
    if instance.id:
        instance.old_image = instance.__class__.objects.get(id=instance.id).image
    else:
        pass
@receiver(post_save, sender=GalleryModel)
def post_save_gallery(sender, instance=None, created=False, **kwargs):    
    # Delete image of local storage:
    _image = None
    _old_image = None
    if hasattr(instance, "old_image") and instance.old_image:
        _old_image = instance.old_image
    if hasattr(instance, "image") and instance.image:
        _image = instance.image
    if _old_image and (_old_image != _image):
        instance.image.storage.delete(_old_image.name)


# Import File:
@receiver(pre_save, sender=ImportModel)
def pre_save_import(sender, instance, *args, **kwargs):
    if instance.id:
        instance.old_file = instance.__class__.objects.get(id=instance.id).file
    else:
        pass
@receiver(post_save, sender=ImportModel)
def post_save_import(sender, instance=None, created=False, **kwargs):    
    # Delete file of local storage:
    _file = None
    _old_file = None
    if hasattr(instance, "old_file") and instance.old_file:
        _old_file = instance.old_file
    if hasattr(instance, "file") and instance.file:
        _file = instance.file
    if _old_file and (_old_file != _file):
        instance.file.storage.delete(_old_file.name)



# Profile:
@receiver(pre_save, sender=ProfileModel)
def pre_save_profile(sender, instance, *args, **kwargs):
    try:
        instance.national_code_old = instance.__class__.objects.get(pk=instance.pk).national_code
    except ObjectDoesNotExist:
        pass                       

@receiver(post_save, sender=ProfileModel)
def post_save_profile(sender, instance=None, created=False, **kwargs):
    _national_code = None
    _national_code_old = None
    if hasattr(instance, "_national_code_old") and instance.national_code_old:
        _national_code_old = instance.national_code_old
    if hasattr(instance, "national_code") and instance.national_code:
        _national_code = instance.national_code
    if _national_code_old and (_national_code_old != _national_code):
        accounts = MellatAccountModel.objects.filter(account__owner=instance.owner)
        for mellat_account in accounts:
            if mellat_account.mellat_status == 0:
                mellat_account.mellat_status = 2
                mellat_account.save()

# Role:
@receiver(pre_save, sender=RoleModel)
def pre_save_role(sender, instance, *args, **kwargs):
    if not instance.pk:
        _parent = instance.parent
        if _parent:
            instance.order = _parent.order + 1

@receiver(post_save, sender=RoleModel)
def post_save_role(sender, instance=None, created=False, **kwargs):
    # SendVerificationEmail:
    pass



# Service:
@receiver(pre_save, sender=ServiceModel)
def pre_save_service(sender, instance, *args, **kwargs):
    if instance.id:
        instance.old_image = instance.__class__.objects.get(id=instance.id).image
    else:
        parent = instance.parent 
        if parent:
            instance.order = parent.order + 1
        else:
            instance.order = 0
@receiver(post_save, sender=ServiceModel)
def post_save_service(sender, instance=None, created=False, **kwargs):    
    # Delete image of local storage:
    _image = None
    _old_image = None
    if hasattr(instance, "old_image") and instance.old_image:
        _old_image = instance.old_image
    if hasattr(instance, "image") and instance.image:
        _image = instance.image
    if _old_image and (_old_image != _image):
        instance.image.storage.delete(_old_image.name)

# Store:
@receiver(pre_save, sender=StoreModel)
def pre_save_store(sender, instance, *args, **kwargs):
    if instance.id:
        instance.old_icon = instance.__class__.objects.get(id=instance.id).icon
    else:
        parent = instance.parent 
        if parent:
            instance.order = parent.order + 1
            if not parent.has_branch:
                parent.has_branch = True
                parent.pre_save = True
                parent.save()
        else:
            instance.order = 0
@receiver(post_save, sender=StoreModel)
def post_save_store(sender, instance=None, created=False, **kwargs): 
    if hasattr(instance, "pre_save") and instance.pre_save:
        pass
    else:  
        # Delete icon of local storage:
        _icon = None
        _old_icon = None
        if hasattr(instance, "old_icon") and instance.old_icon:
            _old_icon = instance.old_icon
        if hasattr(instance, "icon") and instance.icon:
            _icon = instance.icon
        if _old_icon and (_old_icon != _icon):
            instance.icon.storage.delete(_old_icon.name)

        # Add and Update Services:
        new_services = None
        if hasattr(instance, "service_list") and instance.service_list:
            new_services = instance.service_list
        elif instance.parent:
            parent_store_services = StoreServiceModel.objects.filter(store=instance.parent)
            new_services = [obj.service for obj in parent_store_services]
        old_store_services = StoreServiceModel.objects.filter(store=instance).exclude(service__in=new_services)
        old_services = [obj.service for obj in old_store_services]
        store_child_update(instance=instance,input=new_services,output=old_services)

# User:
@receiver(pre_delete, sender=UserModel)
def pre_delete_user(sender, instance=None, **kargs):
    if instance:
        try:
            user_profile = ProfileModel.objects.get(owner=instance)
            user_profile.delete()
        except:
            pass

@receiver(pre_save, sender=UserModel)
def pre_save_user(sender, instance, *args, **kwargs):
    if instance.pk:
        if instance.pk:
            instance.old_cellphone = instance.__class__.objects.get(id=instance.id).cellphone
            instance.old_verification_code = instance.__class__.objects.get(id=instance.id).verification_code
            instance.old_avatar = instance.__class__.objects.get(id=instance.id).avatar
    else:
        pass

@receiver(post_save, sender=UserModel)
def post_save_user(sender, instance=None, created=False, **kwargs):
    if created:
        # Add Role
        if hasattr(instance, "role"):
            try:
                UserRoleModel.objects.get(user_id=instance.pk, role_id=instance.role)
            except UserRoleModel.DoesNotExist:
                _role = RoleModel.objects.get(title=instance.role)
                _data = {"user": instance.pk, "role": _role.pk}
                _serializer = UserRoleSerializer(data=_data)
                if _serializer.is_valid():
                    _serializer.save()
                else:
                    raise ProjectException(852,_("runtime error"),_("role error"),status.HTTP_400_BAD_REQUEST,)
        elif not instance.is_superuser:
            try:
                role = RoleModel.objects.get(title=settings.ROLE_SYSTEM)
                UserRoleModel.objects.create(user=instance,role=role)
            except:
                pass

    # Delete avatar of local storage:
    _avatar = None
    _old_avatar = None
    if hasattr(instance, "old_avatar") and instance.old_avatar:
        _old_avatar = instance.old_avatar
    if hasattr(instance, "avatar") and instance.avatar:
        _avatar = instance.avatar
    if _old_avatar and (_old_avatar != _avatar):
        instance.avatar.storage.delete(_old_avatar.name)

    # Add Profile:
    if hasattr(instance, "profile_data") and instance.profile_data:
        profile_data = instance.profile_data
        try:
            profile = ProfileModel.objects.get(owner=instance)
            _serializer = ProfileUpdateSerializer(instance=profile,data=profile_data,partial=True)
            if _serializer.is_valid():
                _serializer.save()
        except:
            ProfileModel.objects.create(owner=instance, **profile_data)
    else:
        try:
            ProfileModel.objects.get(owner=instance)
        except ObjectDoesNotExist:
            # _national_code = generate_national_code()
            profile = ProfileModel.objects.create(owner=instance)

    #Send verification code:
    _cellphone = None
    _old_cellphone = None
    _old_verification_code = None
    if hasattr(instance, "cellphone") and instance.cellphone:
        _cellphone = instance.cellphone
    if hasattr(instance, "old_cellphone") and instance.old_cellphone:
        _old_cellphone = instance.old_cellphone
    if hasattr(instance, "old_verification_code") and instance.old_verification_code:
        _old_verification_code = instance.old_verification_code
    _verification_code = instance.verification_code
    if (_cellphone != _old_cellphone) or (_verification_code != _old_verification_code):
        if _verification_code:
            _result = sendVerificationSMS(_cellphone, _verification_code)
            print(_result)


@receiver(post_save, sender=MellatAssignPackageToMemberModel)
def post_save_package_member(sender, instance=None, created=False, **kwargs):
    if created:
        # Import to mellat
        _national_code = instance.owner.profile.national_code
        _package_id    = instance.packageId
        _start_date    = instance.startDate
        _end_date      = instance.endDate
        _generate_new_code = instance.generateNewCode
        res = AssignPackageToMember(_national_code,_package_id,_start_date,_end_date,_generate_new_code)        
        if res['status'] != 200:
            raise ProjectException(852,_("runtime error"),_(res['result']),status=res['result'],)
        


from rest_framework import viewsets, status
from rest_framework.decorators import action
# from celery import shared_task
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser, IsAuthenticated, AllowAny
from rest_framework.parsers import (MultiPartParser, JSONParser)
from rest_framework.renderers import JSONRenderer
from django.db.models import Q, F, CharField, Value as V, Count
from django.db.models.functions import Concat,Cast
from django.db.models.expressions import RawSQL
from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist

from django.utils.translation import gettext as _ 


from app.exceptions import ProjectException
from app.helpers import *
from app.accesses import *
from app.filters import *
from app.serializers import *
from app.mellat import *

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi



class AccountViewSet(viewsets.GenericViewSet):
    queryset = AccountModel.objects.all()
    serializer_class = AccountSerializer
    permission_classes = ([IsAuthenticated])
    renderer_classes = (JSONRenderer,)
    parser_classes = (JSONParser,)

    def get_parsers(self):
        if (hasattr(self,'action') and self.action in ["upload",]) or (hasattr(self,'name') and self.name in ["Upload",]):
            parser_classes=[MultiPartParser]
        else:
            parser_classes = [JSONParser]
        
        return [parser() for parser in parser_classes]
    def get_response_schema(action):
        # response_schema_dict
        responses = {}
        rsd = {
            "200":
            AccountInfoSerializer,
            "200_Ok":
            openapi.Response({}),
            "201":
            AccountSerializer,
            "204":
            openapi.Response({}),
            "400":
            openapi.Response(
                description="Bad request",
                schema=SampleResponseSerializer,
                examples={
                    "application/json": {
                        "807": {
                            "status": "failed",
                            "code": 807,
                            "message": "validation error",
                            "detail": "System default error.",
                        },
                        "813": {
                            "status": "failed",
                            "code": 813,
                            "message": "validation error",
                            "detail": "Set the primary key.",
                        },
                    }
                },
            ),
            "403":
            openapi.Response(
                description="Forbidden",
                schema=SampleResponseSerializer,
                examples={
                    "application/json": {
                        "821": {
                            "status":
                            "failed",
                            "code":
                            821,
                            "message":
                            _("validation error"),
                            "detail":
                            _("You do not have permission to perform this action."
                              ),
                            "data": {},
                        },
                    }
                },
            ),
            "404":
            openapi.Response(
                description="Not found",
                schema=SampleResponseSerializer,
                examples={
                    "application/json": {
                        "820": {
                            "status": "failed",
                            "code": 820,
                            "message": "not found",
                            "detail": "This primary key not found",
                        },
                    }
                },
            ),
            "807":
            openapi.Response(
                description="Bad request",
                schema=SampleResponseSerializer,
                examples={
                    "application/json": {
                        "807": {
                            "status": "failed",
                            "code": 807,
                            "message": "validation error",
                            "detail": "System default error.",
                        },
                        
                    }
                },
            ),
            "800":
            openapi.Response(
                description="Bad request",
                schema=SampleResponseSerializer,
                examples={
                    "application/json": {
                        "800": {
                            "status": "failed",
                            "code": 800,
                            "message": "unknown error",
                            "detail": "Unknown error.",
                        },
                    }
                },
            ),
            "813":
            openapi.Response(
                description="Bad request",
                schema=SampleResponseSerializer,
                examples={
                    "application/json": {
                        "813": {
                            "status": "failed",
                            "code": 813,
                            "message": "validation error",
                            "detail": "Set the primary key.",
                        },
                    }
                },
            ),
            "sample":
            SampleResponseSerializer
        }
        if action in ["list"]:
            responses = {"200": rsd["200"], "400": rsd["807"]}
        elif action in ["create"]:
            responses = {"201": rsd["201"], "400": rsd["807"]}
        elif action == "retrieve":
            responses = {"200": rsd["200"],"400": rsd["400"],"404": rsd["404"]}
        elif action == "update":
            responses = {"200": rsd["200"],"404": rsd["404"],"400": rsd["400"]}
        elif action == "delete":
            responses = {"204": rsd["204"],"400": rsd["813"],"404": rsd["404"]}
        return responses
    def get_permissions(self):
        if self.action in ['create','accounts'] :
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]
    def get_serializer_class(self):
        if self.action in ['list','retrieve']:
            return AccountInfoSerializer
        elif self.action == 'partial_update':
            return AccountSerializer
        return super().get_serializer_class()
    def get_queryset(self):
        queryset = self.queryset
        _user = self.request.user
        role_list = get_user_roles(_user)
        if not _user.pk:
            return queryset.filter(pk=-1)
        elif _user.is_superuser:
            queryset = queryset
        elif 'client' in role_list:
            queryset = queryset.filter(owner=_user)
        else:
            queryset = queryset.filter(owner__company=_user.company)
        return queryset
    def filter_queryset(self,queryset):
        _filter = {}
        if 'owner' in self.request.query_params and self.request.query_params['owner']:
            _owner = self.request.query_params['owner']
            _filter.update({'owner_id': _owner})
        if 'start' in self.request.query_params and self.request.query_params['start']: 
            _start = self.request.query_params['start']
            date_start = convert_shamsi_string_to_miladi_date(_start)
            _filter.update({"modified__gte":date_start})
        if 'end' in self.request.query_params and self.request.query_params['end']: 
            _end = self.request.query_params['end']
            date_end = convert_shamsi_string_to_miladi_date(_end)
            _filter.update({"modified__lte":date_end})
        # _filter.update({'modified__range':(date_start, date_end)})
        queryset = queryset.filter(**_filter).distinct()
        return queryset
    def get_object(self,pk=None):
        if pk:
            try:
                _object = self.get_queryset().get(pk=pk)
                return _object
            except ObjectDoesNotExist:
                return None

    @swagger_auto_schema(responses=get_response_schema('list'),query_serializer=AccountFilterQuerySerializer)
    # @execute_with_permission('account', 'list')
    def list(self, request):
        """
        get list of Account API.

        ---

        """
        _queryset = self.filter_queryset(queryset=self.get_queryset()).order_by('pk')
        _count = _queryset.count()
        if _count == 0:
            return Response({'list': [],'total_page_num': 0,'total_row': 0},status=status.HTTP_204_NO_CONTENT)

        _queryset, _total_page_num = get_response_data(request, _queryset)
        _serializer = self.get_serializer(_queryset, many=True)
        return Response({
            'list': _serializer.data,
            'total_page_num': _total_page_num,
            'total_row': _count
        })

    @swagger_auto_schema(responses=get_response_schema('create'))
    # @execute_with_permission('account', 'create')
    @transaction.atomic
    def create(self, request):
        """
        inset a Account API.

        ---

        """
        _data = get_dict_data(request.data)
        _serializer = self.get_serializer(context={'request': request},data=_data)
        if _serializer.is_valid():
            _serializer.save()
            return Response(_serializer.data, status=status.HTTP_201_CREATED)
        else:
            raise ProjectException(807, _('validation error'),_serializer.errors,status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(responses=get_response_schema('retrieve'))
    # @execute_with_permission('account', 'read')
    def retrieve(self, request, pk=None):
        """
        get a Account API.

        ---

        """
        if pk:
            _object = self.get_object(pk)
            if _object:
                _serializer = self.get_serializer(instance=_object)
                return Response(_serializer.data)
            else:
                raise ProjectException(820, _('not found'),_('This primary key not found.'),status.HTTP_404_NOT_FOUND)
        else:
            raise ProjectException(813, _('validation error'),_('Set the primary key.'),status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(responses=get_response_schema('update'))
    # @execute_with_permission('account', 'update')
    @transaction.atomic
    def partial_update(self, request, pk=None):
        """
        update a Account partial API.

        ---

        """
        if pk:
            _object = self.get_object(pk)
            if _object:
                _data = get_dict_data(request.data)
                _serializer = self.get_serializer(context={'request': request},instance=_object,data=_data,partial=True)
                if _serializer.is_valid():
                    _serializer.save()
                    return Response(_serializer.data)
                else:
                    raise ProjectException(807, _('validation error'),_serializer.errors,status.HTTP_400_BAD_REQUEST)
            else:
                raise ProjectException(820, _('not found'),_('This primary key not found.'),status.HTTP_404_NOT_FOUND)
        else:
            raise ProjectException(813, _('validation error'), _('Set the primary key.'),status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(responses=get_response_schema('delete'))
    # @execute_with_permission('account', 'delete')
    @transaction.atomic
    def destroy(self, request, pk=None):
        """
        delete a account  API.

        ---

        """
        if pk:
            _object = self.get_object(pk)
            if _object:
                if _object.status == -1:
                    _object.delete()
                else:
                    _object.status = -1
                    _object.save()
                return Response(status=status.HTTP_204_NO_CONTENT)
            else:
                raise ProjectException(820, _('not found'),_('This primary key not found.'),status.HTTP_404_NOT_FOUND)
        else:
            raise ProjectException(813, _('validation error'),_('Set the primary key.'),status.HTTP_400_BAD_REQUEST)


    @swagger_auto_schema(query_serializer=AccountReportFilterQuerySerializer)
    @action(detail=False ,methods=['get'],)
    def report(self, request,start_date=None,end_date=None):
        """
        start_date = yyyy-mm-dd
        end_date   = yyyy-mm-dd
        ---

        """
        import uuid
        import pandas as pd
        date_start = None
        date_end   = None
        if 'start_date' in self.request.query_params and self.request.query_params['start_date']: 
            _start = self.request.query_params['start_date']
            date_start = convert_shamsi_string_to_miladi_date(_start)
        if 'end_date' in self.request.query_params and self.request.query_params['end_date']: 
            _end = self.request.query_params['end_date']
            date_end = convert_shamsi_string_to_miladi_date(_end)
        if not (date_start and date_end): 
            return Response(status=status.HTTP_400_BAD_REQUEST)

        if date_end < date_start:
            return Response({"error":"start_date grather than end_date"},status=status.HTTP_400_BAD_REQUEST)
        
        _queryset = AccountModel.objects.annotate(cellphone=F('owner__cellphone')).filter(modified__date__range=(date_start, date_end)).order_by('pk')
        if _queryset.count() == 0:
            return Response(status=status.HTTP_204_NO_CONTENT)        
        
        get_data = list(_queryset.values("card_no","bank_name","name","cellphone",)) 
        df = pd.DataFrame(get_data)

        id   = uuid.uuid4()
        name = id.urn[9:] + '.csv'
        _file_path  = "".join([settings.MEDIA_ROOT,'/temp/'])
        path_or_buf = "".join([_file_path,name])
        df.to_csv(path_or_buf,index=False)
        # save zip:
        # name_zip = id.urn[9:] + '.zip'
        # _file_path  = "".join([settings.MEDIA_ROOT,'/temp/'])
        # path_or_buf = "".join([_file_path,name_zip])
        # compression_opts = dict(method='zip',archive_name=name)
        # df.to_csv(path_or_buf, index=False,compression=compression_opts) 
        # 
        _schema     = request.scheme              
        _host       = request.META['HTTP_HOST']
        _file_path  = "".join([settings.MEDIA_URL,'temp/',name])
        _url        = "".join([_schema,'://',_host,_file_path])
        return Response({"report_url":_url})



class CompanyViewSet(viewsets.GenericViewSet):
    queryset = CompanyModel.objects.all()
    serializer_class = CompanySerializer
    permission_classes = ([IsAuthenticated])
    renderer_classes = (JSONRenderer,)
    parser_classes = (JSONParser,)

    def get_parsers(self):
        if (hasattr(self,'action') and self.action in ["upload",]) or (hasattr(self,'name') and self.name in ["Upload",]):
            parser_classes=[MultiPartParser]
        else:
            parser_classes = [JSONParser]
        
        return [parser() for parser in parser_classes]
    def get_response_schema(action):
        # response_schema_dict
        responses = {}
        rsd = {
            "200":
            CompanySerializer,
            "200_Ok":
            openapi.Response({}),
            "201":
            CompanySerializer,
            "204":
            openapi.Response({}),
            "400":
            openapi.Response(
                description="Bad request",
                schema=SampleResponseSerializer,
                examples={
                    "application/json": {
                        "807": {
                            "status": "failed",
                            "code": 807,
                            "message": "validation error",
                            "detail": "System default error.",
                        },
                        "813": {
                            "status": "failed",
                            "code": 813,
                            "message": "validation error",
                            "detail": "Set the primary key.",
                        },
                    }
                },
            ),
            "403":
            openapi.Response(
                description="Forbidden",
                schema=SampleResponseSerializer,
                examples={
                    "application/json": {
                        "821": {
                            "status":
                            "failed",
                            "code":
                            821,
                            "message":
                            _("validation error"),
                            "detail":
                            _("You do not have permission to perform this action."
                              ),
                            "data": {},
                        },
                    }
                },
            ),
            "404":
            openapi.Response(
                description="Not found",
                schema=SampleResponseSerializer,
                examples={
                    "application/json": {
                        "820": {
                            "status": "failed",
                            "code": 820,
                            "message": "not found",
                            "detail": "This primary key not found",
                        },
                    }
                },
            ),
            "807":
            openapi.Response(
                description="Bad request",
                schema=SampleResponseSerializer,
                examples={
                    "application/json": {
                        "807": {
                            "status": "failed",
                            "code": 807,
                            "message": "validation error",
                            "detail": "System default error.",
                        },
                        
                    }
                },
            ),
            "800":
            openapi.Response(
                description="Bad request",
                schema=SampleResponseSerializer,
                examples={
                    "application/json": {
                        "800": {
                            "status": "failed",
                            "code": 800,
                            "message": "unknown error",
                            "detail": "Unknown error.",
                        },
                    }
                },
            ),
            "813":
            openapi.Response(
                description="Bad request",
                schema=SampleResponseSerializer,
                examples={
                    "application/json": {
                        "813": {
                            "status": "failed",
                            "code": 813,
                            "message": "validation error",
                            "detail": "Set the primary key.",
                        },
                    }
                },
            ),
            "sample":
            SampleResponseSerializer
        }
        if action in ["list"]:
            responses = {"200": rsd["200"], "400": rsd["807"]}
        elif action in ["create"]:
            responses = {"201": rsd["201"], "400": rsd["807"]}
        elif action == "retrieve":
            responses = {"200": rsd["200"],"400": rsd["400"],"404": rsd["404"]}
        elif action == "update":
            responses = {"200": rsd["200"],"404": rsd["404"],"400": rsd["400"]}
        elif action == "delete":
            responses = {"204": rsd["204"],"400": rsd["813"],"404": rsd["404"]}
        return responses
    def get_permissions(self):
        if self.action in ['list','retrieve'] :
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]
    def get_serializer_class(self):
        if self.action in ['list','retrieve']:
            return CompanySerializer
        elif self.action == 'partial_update':
            return CompanySerializer
        return super().get_serializer_class()
    def get_queryset(self):
        queryset = self.queryset
        _user = self.request.user
        # role_list = get_user_roles(_user)
        if not _user.pk:
            return queryset.filter(pk=-1)
        
        return queryset
    def filter_queryset(self,queryset):
        _filter = {}
        if 'search' in self.request.query_params and self.request.query_params['search']:
            _search = self.request.query_params['search']
            _filter.update({'title__icontains': _search})
        
        queryset = queryset.filter(**_filter).distinct()
        return queryset
    def get_object(self,pk=None):
        if pk:
            try:
                _object = self.get_queryset().get(pk=pk)
                return _object
            except ObjectDoesNotExist:
                return None

    @swagger_auto_schema(responses=get_response_schema('list'),query_serializer=CompanyFilterQuerySerializer)
    # @execute_with_permission('company', 'list')
    def list(self, request):
        """
        get list of company API.

        ---

        """
        _queryset = self.filter_queryset(queryset=self.get_queryset()).order_by('pk')
        _count = _queryset.count()
        if _count == 0:
            return Response({'list': [],'total_page_num': 0,'total_row': 0},status=status.HTTP_204_NO_CONTENT)

        _queryset, _total_page_num = get_response_data(request, _queryset)
        _serializer = self.get_serializer(_queryset, many=True)
        return Response({
            'list': _serializer.data,
            'total_page_num': _total_page_num,
            'total_row': _count
        })

    @swagger_auto_schema(responses=get_response_schema('create'))
    # @execute_with_permission('company', 'create')
    @transaction.atomic
    def create(self, request):
        """
        inset a company API.

        ---

        """
        _data = get_dict_data(request.data)
        _serializer = self.get_serializer(context={'request': request},data=_data)
        if _serializer.is_valid():
            _serializer.save()
            return Response(_serializer.data, status=status.HTTP_201_CREATED)
        else:
            raise ProjectException(807, _('validation error'),_serializer.errors,status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(responses=get_response_schema('retrieve'))
    # @execute_with_permission('company', 'read')
    def retrieve(self, request, pk=None):
        """
        get a company API.

        ---

        """
        if pk:
            _object = self.get_object(pk)
            if _object:
                _serializer = self.get_serializer(instance=_object)
                return Response(_serializer.data)
            else:
                raise ProjectException(820, _('not found'),_('This primary key not found.'),status.HTTP_404_NOT_FOUND)
        else:
            raise ProjectException(813, _('validation error'),_('Set the primary key.'),status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(responses=get_response_schema('update'))
    # @execute_with_permission('company', 'update')
    @transaction.atomic
    def partial_update(self, request, pk=None):
        """
        update a company partial API.

        ---

        """
        if pk:
            _object = self.get_object(pk)
            if _object:
                _data = get_dict_data(request.data)
                _serializer = self.get_serializer(context={'request': request},instance=_object,data=_data,partial=True)
                if _serializer.is_valid():
                    _serializer.save()
                    return Response(_serializer.data)
                else:
                    raise ProjectException(807, _('validation error'),_serializer.errors,status.HTTP_400_BAD_REQUEST)
            else:
                raise ProjectException(820, _('not found'),_('This primary key not found.'),status.HTTP_404_NOT_FOUND)
        else:
            raise ProjectException(813, _('validation error'), _('Set the primary key.'),status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(responses=get_response_schema('delete'))
    # @execute_with_permission('company', 'delete')
    @transaction.atomic
    def destroy(self, request, pk=None):
        """
        delete a company  API.

        ---

        """
        if pk:
            _object = self.get_object(pk)
            if _object:
                _object.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            else:
                raise ProjectException(820, _('not found'),_('This primary key not found.'),status.HTTP_404_NOT_FOUND)
        else:
            raise ProjectException(813, _('validation error'),_('Set the primary key.'),status.HTTP_400_BAD_REQUEST)



class DefaultViewSet(viewsets.GenericViewSet):
    queryset = UserModel.objects.all()

    def get_response_schema(action):
        # response_schema_dict
        rsd = {
            "200":
            LoginSerializer,
            "400_login":
            openapi.Response(
                description="Bad request",
                schema=SampleResponseSerializer,
                examples={
                    "application/json": {
                        "807": {
                            "status": "failed",
                            "code": 807,
                            "message": "validation error",
                            "detail": "System default error.",
                        },
                        "802": {
                            "status": "failed",
                            "code": 802,
                            "message": "vauthentication error",
                            "detail": "You are not active on the system.",
                        },
                    }
                },
            ),
            
            "400_change_pass":
            openapi.Response(
                description="Bad request",
                schema=SampleResponseSerializer,
                examples={
                    "application/json": {
                        "805": {
                            "status": "failed",
                            "code": 805,
                            "message": "change password",
                            "detail": "Wrong password.",
                        },
                        "807": {
                            "status": "failed",
                            "code": 807,
                            "message": "validation error",
                            "detail": "System default error.",
                        },
                        "812": {
                            "status": "failed",
                            "code": 812,
                            "message": "validation error",
                            "detail": "password cannot less than 8 digit.",
                        },
                    }
                },
            ),
            "401":
            openapi.Response(
                description="UNAUTHORIZE",
                schema=SampleResponseSerializer,
                examples={
                    "application/json": {
                        "801": {
                            "status": "failed",
                            "code": 801,
                            "message": "authentication error",
                            "detail": "Authentication error.",
                        },
                        "803": {
                            "status": "failed",
                            "code": 803,
                            "message": "authentication error",
                            "detail": "You will not be able to access the system until t time.",
                        },
                        "804": {
                            "status": "failed",
                            "code": 804,
                            "message": "authentication error",
                            "detail": "You have been disabled by the system for security reasons.",
                        },
                    }
                },
            ),
            "800":
            openapi.Response(
                description="Bad request",
                schema=SampleResponseSerializer,
                examples={
                    "application/json": {
                        "800": {
                            "status": "failed",
                            "code": 800,
                            "message": "unknown error",
                            "detail": "Unknown error.",
                        },
                    }
                },
            ),
            "200_logout":
            openapi.Response(
                description="OK",
                schema=SampleResponseSerializer,
                examples={
                    "application/json": {
                        "200": {
                            "status": "success",
                            "code": 200,
                            "message": _("token burned"),
                            "detail": _("Logout user."),
                        },
                    }
                },
            ),
            "200_change_pass":
            openapi.Response(
                description="OK",
                schema=SampleResponseSerializer,
                examples={
                    "application/json": {
                        "200": {
                            "status": "success",
                            "code": 200,
                            "message": "_('password updated successfully')",
                            "detail": "Change password.",
                        },
                    }
                },
            ),
            "204_logout":
            openapi.Response(
                description="NO_CONTENT",
                schema=SampleResponseSerializer,
                examples={
                    "application/json": {
                        "204": {
                            "status": "failed",
                            "code": 204,
                            "message": _("not login before"),
                            "detail": _("User has not logged in before."),
                        },
                    }
                },
            ),
        }
        responses = dict()
        if action == "login":
            responses = {"200": rsd["200"],"401": rsd["401"],"400": rsd["400_login"]}
        elif action in ["logout_get", "logout_post"]:
            responses = {"200": rsd["200_logout"], "204": rsd["204_logout"]}
        elif action == "changepassword":
            responses = {"200": rsd["200_change_pass"], "400": rsd["400_change_pass"]}

        return responses
    def get_serializer_class(self):
        if self.action   == 'register':
            return UserRegisterSerializer
        elif self.action == 'login':
            return LoginSerializer
        elif self.action == 'logout':
            return NoneSerializer
        elif self.action == 'changepassword':
            return ChangePasswordSerializer
        elif self.action == 'refresh_token':
            return RefreshTokenSerializer
    def get_permissions(self):
        if self.action in ['register','login','uploaded_file','refresh_token']:
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated]

        return [permission() for permission in permission_classes]

    # @swagger_auto_schema(responses=get_response_schema('create'))
    @transaction.atomic
    @action(detail=False, methods=["post"])#,url_path='(?P<role>[\w\-]+)/register')
    def register(self, request):
        """
        register for user API.
        ---
            role : ['admin','client']
        """
        _data = get_dict_data(request.data)
        _serializer = self.get_serializer(context={'request': request},data=_data)
        if _serializer.is_valid():
            new_object = _serializer.save()
            _serializer = UserInfoSerializer(instance=new_object)
            return Response(_serializer.data, status=status.HTTP_201_CREATED)
        else:
            raise ProjectException(807, 
                            _('validation error'),_serializer.errors,
                            status.HTTP_400_BAD_REQUEST)
    
    @swagger_auto_schema(responses=get_response_schema('login'))
    @action(detail=False, methods=['post'])
    def login(self, request):
        """
        login.
        
        ---
        username = [username,]
        """
        _chk = False
        _serializer = self.get_serializer(data=request.data)
        if _serializer.is_valid():
            _data = _serializer.validated_data
            _chk, _user,_access_token,_refresh_token = signin(request, data=_data)
        else:
            raise ProjectException(807, _('validation error'),
                                   _serializer.errors,
                                   status.HTTP_400_BAD_REQUEST)

        if _chk:
            _user.login_error = 0
            _user.deactive_expire = None
            _user.save()

            _serializer = LoginSerializer(_user, many=False)
            _data = {'access_token': _access_token,'refresh_token': _refresh_token}
            for attr, value in _serializer.data.items():
                _data[attr] = value

            _response = Response(_data, status=status.HTTP_200_OK)
            _response.set_cookie(key='access_token', value=_access_token)
            return _response
        else:
            # return Response(status.HTTP_401_UNAUTHORIZED)
            raise ProjectException(801, _('authentication error'),
                                   _('Authentication error'),
                                   status.HTTP_401_UNAUTHORIZED)

    # @swagger_auto_schema(methods=["get"],responses=get_response_schema('logout_get'))
    @swagger_auto_schema(methods=["post"],
                         responses=get_response_schema('logout_post'))
    @action(detail=False, methods=['post'])
    def logout(self, request):
        """
        logout.
        
        ---

        """
        _user = request.user
        if _user:
            signout(request)
            response = {
                'status': 'success',
                'code': status.HTTP_200_OK,
                'message': _('token burned'),
                "detail": _("Logout user."),
            }
        else:
            response = {
                'status': 'failed',
                'code': status.HTTP_204_NO_CONTENT,
                'message': _('not login before'),
                "detail": _("User has not logged in before."),
            }
        return Response(response)

    @swagger_auto_schema(responses=get_response_schema('changepassword'))
    @action(detail=False, methods=['post'])
    def changepassword(self, request):
        """
        change password for current user.
        ---
        """

        _object = request.user
        _serializer = self.get_serializer(context={'request': request},data=request.data)

        if _serializer.is_valid():
            # Check old password
            if not _object.check_password(_serializer.data.get("current_password")):
                raise ProjectException(806, _('current_password'),
                                       _('Wrong password.'),
                                       status.HTTP_400_BAD_REQUEST)
                # return Response({"current_password": ["Wrong password."]}, status=status.HTTP_400_BAD_REQUEST)
            # set_password also hashes the password that the user will get
            _object.set_password(_serializer.data.get("new_password"))
            _object.verification_code = _serializer.data.get("new_password")
            # _object.is_active = True 
            _object.save()
            signout(request)
            _response = {
                            "status": _("success"),
                            "code": status.HTTP_200_OK,
                            "message": _('password updated successfully'),
                            "detail": _("Change password."),
                        }
            return Response(_response,status=status.HTTP_200_OK)
        else:
            raise ProjectException(807, _('validation error'),
                                   _serializer.errors,
                                   status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def uploaded_file(self, request):
        from app.tasks import upload_file_task
        upload_file_task()
        return Response({})

    @action(detail=False, methods=['get'])
    def mellat_task(self, request):
        from app.tasks import mellat_task
        mellat_task()
        return Response({})


    @swagger_auto_schema(responses=get_response_schema('refresh_token'))
    @action(detail=False, methods=['post'])
    @transaction.atomic
    def refresh_token(self, request):
        """
        create Access Token API.

        ---

        """
        _data = get_dict_data(request.data)
        _serializer = self.get_serializer(context={'request': request},data=_data)
        if _serializer.is_valid():
            _serializer.save()
            return Response(_serializer.data, status=status.HTTP_201_CREATED)
        else:
            raise ProjectException(807, _('validation error'),_serializer.errors,status.HTTP_400_BAD_REQUEST)



class GalleryViewSet(viewsets.GenericViewSet):
    queryset = GalleryModel.objects.all()
    serializer_class = GallerySerializer
    permission_classes = ([IsAuthenticated])
    renderer_classes = (JSONRenderer,)
    parser_classes = (JSONParser,)

    def get_parsers(self):
        if (hasattr(self,'action') and self.action in ["upload",]) or (hasattr(self,'name') and self.name in ["Upload",]):
            parser_classes=[MultiPartParser]
        else:
            parser_classes = [MultiPartParser]
        
        return [parser() for parser in parser_classes]
    def get_response_schema(action):
        # response_schema_dict
        responses = {}
        rsd = {
            "200":
            GallerySerializer,
            "200_Ok":
            openapi.Response({}),
            "201":
            GallerySerializer,
            "204":
            openapi.Response({}),
            "400":
            openapi.Response(
                description="Bad request",
                schema=SampleResponseSerializer,
                examples={
                    "application/json": {
                        "807": {
                            "status": "failed",
                            "code": 807,
                            "message": "validation error",
                            "detail": "System default error.",
                        },
                        "813": {
                            "status": "failed",
                            "code": 813,
                            "message": "validation error",
                            "detail": "Set the primary key.",
                        },
                    }
                },
            ),
            "403":
            openapi.Response(
                description="Forbidden",
                schema=SampleResponseSerializer,
                examples={
                    "application/json": {
                        "821": {
                            "status":
                            "failed",
                            "code":
                            821,
                            "message":
                            _("validation error"),
                            "detail":
                            _("You do not have permission to perform this action."
                              ),
                            "data": {},
                        },
                    }
                },
            ),
            "404":
            openapi.Response(
                description="Not found",
                schema=SampleResponseSerializer,
                examples={
                    "application/json": {
                        "820": {
                            "status": "failed",
                            "code": 820,
                            "message": "not found",
                            "detail": "This primary key not found",
                        },
                    }
                },
            ),
            "807":
            openapi.Response(
                description="Bad request",
                schema=SampleResponseSerializer,
                examples={
                    "application/json": {
                        "807": {
                            "status": "failed",
                            "code": 807,
                            "message": "validation error",
                            "detail": "System default error.",
                        },
                        
                    }
                },
            ),
            "800":
            openapi.Response(
                description="Bad request",
                schema=SampleResponseSerializer,
                examples={
                    "application/json": {
                        "800": {
                            "status": "failed",
                            "code": 800,
                            "message": "unknown error",
                            "detail": "Unknown error.",
                        },
                    }
                },
            ),
            "813":
            openapi.Response(
                description="Bad request",
                schema=SampleResponseSerializer,
                examples={
                    "application/json": {
                        "813": {
                            "status": "failed",
                            "code": 813,
                            "message": "validation error",
                            "detail": "Set the primary key.",
                        },
                    }
                },
            ),
            "sample":
            SampleResponseSerializer
        }
        if action in ["list"]:
            responses = {"200": rsd["200"], "400": rsd["807"]}
        elif action in ["create"]:
            responses = {"201": rsd["201"], "400": rsd["807"]}
        elif action == "retrieve":
            responses = {"200": rsd["200"],"400": rsd["400"],"404": rsd["404"]}
        elif action == "update":
            responses = {"200": rsd["200"],"404": rsd["404"],"400": rsd["400"]}
        elif action == "delete":
            responses = {"204": rsd["204"],"400": rsd["813"],"404": rsd["404"]}
        return responses
    def get_permissions(self):
        return super().get_permissions()
    def get_serializer_class(self):
        return super().get_serializer_class()
    def get_queryset(self):
        return super().get_queryset()
    def filter_queryset(self,queryset,status=None):
        _filter = {}
        if 'store' in self.request.query_params and self.request.query_params['store']:
            _store = self.request.query_params['store']
            _filter.update({'store_id': _store})
        
        queryset = queryset.filter(**_filter).distinct()
        return queryset
    def get_object(self,pk=None):
        if pk:
            try:
                _object = self.get_queryset().get(pk=pk)
                return _object
            except ObjectDoesNotExist:
                return None


    @swagger_auto_schema(responses=get_response_schema('list'),query_serializer=GalleryFilterQuerySerializer)
    # @execute_with_permission('gallery', 'list')
    def list(self, request):
        """
        get list of gallery API.

        ---

        """
        _queryset = self.filter_queryset(queryset=self.get_queryset()).order_by('pk')
        _count = _queryset.count()
        if _count == 0:
            return Response({'list': [],'total_page_num': 0,'total_row': 0},status=status.HTTP_204_NO_CONTENT)

        _queryset, _total_page_num = get_response_data(request, _queryset)
        _serializer = self.get_serializer(_queryset, many=True)
        return Response({
            'list': _serializer.data,
            'total_page_num': _total_page_num,
            'total_row': _count
        })


    @swagger_auto_schema(responses=get_response_schema('create'))
    # @execute_with_permission('gallery', 'create')
    @transaction.atomic
    def create(self, request):
        """
        inset a gallery API.

        ---

        """
        _data = get_dict_data(request.data)
        _serializer = self.get_serializer(context={'request': request},data=_data)
        if _serializer.is_valid():
            _serializer.save()
            return Response(_serializer.data, status=status.HTTP_201_CREATED)
        else:
            raise ProjectException(807, _('validation error'),_serializer.errors,status.HTTP_400_BAD_REQUEST)


    @swagger_auto_schema(responses=get_response_schema('retrieve'))
    # @execute_with_permission('gallery', 'read')
    def retrieve(self, request, pk=None):
        """
        get a gallery API.

        ---

        """
        if pk:
            _object = self.get_object(pk)
            if _object:
                _serializer = self.get_serializer(instance=_object)
                return Response(_serializer.data)
            else:
                raise ProjectException(820, _('not found'),_('This primary key not found.'),status.HTTP_404_NOT_FOUND)
        else:
            raise ProjectException(813, _('validation error'),_('Set the primary key.'),status.HTTP_400_BAD_REQUEST)

    
    @swagger_auto_schema(responses=get_response_schema('update'))
    # @execute_with_permission('gallery', 'update')
    @transaction.atomic
    def partial_update(self, request, pk=None):
        """
        update a gallery partial API.

        ---

        """
        if pk:
            _object = self.get_object(pk)
            if _object:
                _data = get_dict_data(request.data)
                _serializer = self.get_serializer(context={'request': request},instance=_object,data=_data,partial=True)
                if _serializer.is_valid():
                    _serializer.save()
                    return Response(_serializer.data)
                else:
                    raise ProjectException(807, _('validation error'),_serializer.errors,status.HTTP_400_BAD_REQUEST)
            else:
                raise ProjectException(820, _('not found'),_('This primary key not found.'),status.HTTP_404_NOT_FOUND)
        else:
            raise ProjectException(813, _('validation error'), _('Set the primary key.'),status.HTTP_400_BAD_REQUEST)


    @swagger_auto_schema(responses=get_response_schema('delete'))
    # @execute_with_permission('gallery', 'delete')
    @transaction.atomic
    def destroy(self, request, pk=None):
        """
        delete a gallery  API.

        ---

        """
        if pk:
            _object = self.get_object(pk)
            if _object:
                _object.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            else:
                raise ProjectException(820, _('not found'),_('This primary key not found.'),status.HTTP_404_NOT_FOUND)
        else:
            raise ProjectException(813, _('validation error'),_('Set the primary key.'),status.HTTP_400_BAD_REQUEST)



class ImportViewSet(viewsets.GenericViewSet):
    queryset = ImportModel.objects.all()
    serializer_class = ImportSerializer
    permission_classes = ([IsAuthenticated])
    renderer_classes = (JSONRenderer,)
    parser_classes = (JSONParser,)

    def get_parsers(self):
        if (hasattr(self,'action') and self.action in ["upload",]) or (hasattr(self,'name') and self.name in ["Upload",]):
            parser_classes=[MultiPartParser]
        else:
            parser_classes = [MultiPartParser]
        
        return [parser() for parser in parser_classes]
    def get_response_schema(action):
        # response_schema_dict
        responses = {}
        rsd = {
            "200":
            ImportSerializer,
            "200_Ok":
            openapi.Response({}),
            "201":
            ImportSerializer,
            "204":
            openapi.Response({}),
            "400":
            openapi.Response(
                description="Bad request",
                schema=SampleResponseSerializer,
                examples={
                    "application/json": {
                        "807": {
                            "status": "failed",
                            "code": 807,
                            "message": "validation error",
                            "detail": "System default error.",
                        },
                        "813": {
                            "status": "failed",
                            "code": 813,
                            "message": "validation error",
                            "detail": "Set the primary key.",
                        },
                    }
                },
            ),
            "403":
            openapi.Response(
                description="Forbidden",
                schema=SampleResponseSerializer,
                examples={
                    "application/json": {
                        "821": {
                            "status":
                            "failed",
                            "code":
                            821,
                            "message":
                            _("validation error"),
                            "detail":
                            _("You do not have permission to perform this action."
                              ),
                            "data": {},
                        },
                    }
                },
            ),
            "404":
            openapi.Response(
                description="Not found",
                schema=SampleResponseSerializer,
                examples={
                    "application/json": {
                        "820": {
                            "status": "failed",
                            "code": 820,
                            "message": "not found",
                            "detail": "This primary key not found",
                        },
                    }
                },
            ),
            "807":
            openapi.Response(
                description="Bad request",
                schema=SampleResponseSerializer,
                examples={
                    "application/json": {
                        "807": {
                            "status": "failed",
                            "code": 807,
                            "message": "validation error",
                            "detail": "System default error.",
                        },
                        
                    }
                },
            ),
            "800":
            openapi.Response(
                description="Bad request",
                schema=SampleResponseSerializer,
                examples={
                    "application/json": {
                        "800": {
                            "status": "failed",
                            "code": 800,
                            "message": "unknown error",
                            "detail": "Unknown error.",
                        },
                    }
                },
            ),
            "813":
            openapi.Response(
                description="Bad request",
                schema=SampleResponseSerializer,
                examples={
                    "application/json": {
                        "813": {
                            "status": "failed",
                            "code": 813,
                            "message": "validation error",
                            "detail": "Set the primary key.",
                        },
                    }
                },
            ),
            "sample":
            SampleResponseSerializer
        }
        if action in ["list"]:
            responses = {"200": rsd["200"], "400": rsd["807"]}
        elif action in ["create"]:
            responses = {"201": rsd["201"], "400": rsd["807"]}
        elif action == "retrieve":
            responses = {"200": rsd["200"],"400": rsd["400"],"404": rsd["404"]}
        elif action == "update":
            responses = {"200": rsd["200"],"404": rsd["404"],"400": rsd["400"]}
        elif action == "delete":
            responses = {"204": rsd["204"],"400": rsd["813"],"404": rsd["404"]}
        return responses
    def get_permissions(self):
        return super().get_permissions()
    def get_serializer_class(self):
        return super().get_serializer_class()
    def get_queryset(self):
        return super().get_queryset()
    def filter_queryset(self,queryset,status=None):
        _filter = {}
        if 'company' in self.request.query_params and self.request.query_params['company']:
            _company = self.request.query_params['company']
            _filter.update({'company_id': _company})
        
        queryset = queryset.filter(**_filter).distinct()
        return queryset
    def get_object(self,pk=None):
        if pk:
            try:
                _object = self.get_queryset().get(pk=pk)
                return _object
            except ObjectDoesNotExist:
                return None


    @swagger_auto_schema(responses=get_response_schema('list'),query_serializer=ImportFilterQuerySerializer)
    # @execute_with_permission('Import', 'list')
    def list(self, request):
        """
        get list of Import API.

        ---

        """
        _queryset = self.filter_queryset(queryset=self.get_queryset()).order_by('pk')
        _count = _queryset.count()
        if _count == 0:
            return Response({'list': [],'total_page_num': 0,'total_row': 0},status=status.HTTP_204_NO_CONTENT)

        _queryset, _total_page_num = get_response_data(request, _queryset)
        _serializer = self.get_serializer(_queryset, many=True)
        return Response({
            'list': _serializer.data,
            'total_page_num': _total_page_num,
            'total_row': _count
        })


    @swagger_auto_schema(responses=get_response_schema('create'))
    # @execute_with_permission('Import', 'create')
    @transaction.atomic
    @action(detail=False,url_path='upload',url_name='upload' ,methods=['post'])
    def upload(self, request):
        """
        inset a Import API.

        ---

        """
        _data = get_dict_data(request.data)
        _serializer = self.get_serializer(context={'request': request},data=_data)
        if _serializer.is_valid():
            _serializer.save()
            return Response(_serializer.data, status=status.HTTP_201_CREATED)
        else:
            raise ProjectException(807, _('validation error'),_serializer.errors,status.HTTP_400_BAD_REQUEST)



    @swagger_auto_schema(responses=get_response_schema('retrieve'))
    # @execute_with_permission('Import', 'read')
    def retrieve(self, request, pk=None):
        """
        get a Import API.

        ---

        """
        if pk:
            _object = self.get_object(pk)
            if _object:
                _serializer = self.get_serializer(instance=_object)
                return Response(_serializer.data)
            else:
                raise ProjectException(820, _('not found'),_('This primary key not found.'),status.HTTP_404_NOT_FOUND)
        else:
            raise ProjectException(813, _('validation error'),_('Set the primary key.'),status.HTTP_400_BAD_REQUEST)

    
    @swagger_auto_schema(responses=get_response_schema('update'))
    # @execute_with_permission('Import', 'update')
    @transaction.atomic
    def partial_update(self, request, pk=None):
        """
        update a Import partial API.

        ---

        """
        if pk:
            _object = self.get_object(pk)
            if _object:
                _data = get_dict_data(request.data)
                _serializer = self.get_serializer(context={'request': request},instance=_object,data=_data,partial=True)
                if _serializer.is_valid():
                    _serializer.save()
                    return Response(_serializer.data)
                else:
                    raise ProjectException(807, _('validation error'),_serializer.errors,status.HTTP_400_BAD_REQUEST)
            else:
                raise ProjectException(820, _('not found'),_('This primary key not found.'),status.HTTP_404_NOT_FOUND)
        else:
            raise ProjectException(813, _('validation error'), _('Set the primary key.'),status.HTTP_400_BAD_REQUEST)


    @swagger_auto_schema(responses=get_response_schema('delete'))
    # @execute_with_permission('Import', 'delete')
    @transaction.atomic
    def destroy(self, request, pk=None):
        """
        delete a Import  API.

        ---

        """
        if pk:
            _object = self.get_object(pk)
            if _object:
                _object.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            else:
                raise ProjectException(820, _('not found'),_('This primary key not found.'),status.HTTP_404_NOT_FOUND)
        else:
            raise ProjectException(813, _('validation error'),_('Set the primary key.'),status.HTTP_400_BAD_REQUEST)


class MellatViewSet(viewsets.GenericViewSet):
    queryset = UserModel.objects.all()
    # serializer_class = CompanySerializer
    permission_classes = ([IsAuthenticated])
    renderer_classes = (JSONRenderer,)
    parser_classes = (JSONParser,)

    def get_parsers(self):
        if (hasattr(self,'action') and self.action in ["upload",]) or (hasattr(self,'name') and self.name in ["Upload",]):
            parser_classes=[MultiPartParser]
        else:
            parser_classes = [JSONParser]
        
        return [parser() for parser in parser_classes]
    def get_response_schema(action):
        # response_schema_dict
        responses = {}
        rsd = {
            "200":
            CompanySerializer,
            "200_Ok":
            openapi.Response({}),
            "201":
            CompanySerializer,
            "204":
            openapi.Response({}),
            "400":
            openapi.Response(
                description="Bad request",
                schema=SampleResponseSerializer,
                examples={
                    "application/json": {
                        "807": {
                            "status": "failed",
                            "code": 807,
                            "message": "validation error",
                            "detail": "System default error.",
                        },
                        "813": {
                            "status": "failed",
                            "code": 813,
                            "message": "validation error",
                            "detail": "Set the primary key.",
                        },
                    }
                },
            ),
            "403":
            openapi.Response(
                description="Forbidden",
                schema=SampleResponseSerializer,
                examples={
                    "application/json": {
                        "821": {
                            "status":
                            "failed",
                            "code":
                            821,
                            "message":
                            _("validation error"),
                            "detail":
                            _("You do not have permission to perform this action."
                              ),
                            "data": {},
                        },
                    }
                },
            ),
            "404":
            openapi.Response(
                description="Not found",
                schema=SampleResponseSerializer,
                examples={
                    "application/json": {
                        "820": {
                            "status": "failed",
                            "code": 820,
                            "message": "not found",
                            "detail": "This primary key not found",
                        },
                    }
                },
            ),
            "807":
            openapi.Response(
                description="Bad request",
                schema=SampleResponseSerializer,
                examples={
                    "application/json": {
                        "807": {
                            "status": "failed",
                            "code": 807,
                            "message": "validation error",
                            "detail": "System default error.",
                        },
                        
                    }
                },
            ),
            "800":
            openapi.Response(
                description="Bad request",
                schema=SampleResponseSerializer,
                examples={
                    "application/json": {
                        "800": {
                            "status": "failed",
                            "code": 800,
                            "message": "unknown error",
                            "detail": "Unknown error.",
                        },
                    }
                },
            ),
            "813":
            openapi.Response(
                description="Bad request",
                schema=SampleResponseSerializer,
                examples={
                    "application/json": {
                        "813": {
                            "status": "failed",
                            "code": 813,
                            "message": "validation error",
                            "detail": "Set the primary key.",
                        },
                    }
                },
            ),
            "sample":
            SampleResponseSerializer
        }
        if action in ["list"]:
            responses = {"200": rsd["200"], "400": rsd["807"]}
        elif action in ["create"]:
            responses = {"201": rsd["201"], "400": rsd["807"]}
        elif action == "retrieve":
            responses = {"200": rsd["200"],"400": rsd["400"],"404": rsd["404"]}
        elif action == "update":
            responses = {"200": rsd["200"],"404": rsd["404"],"400": rsd["400"]}
        elif action == "delete":
            responses = {"204": rsd["204"],"400": rsd["813"],"404": rsd["404"]}
        return responses
    def get_permissions(self):
        if self.action in ['packages','login','transactions']:
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]
    def get_serializer_class(self):
        if self.action in ['login','transactions']:
            return NoneSerializer
        elif self.action == 'is_card_exist':
            return MellatCheckCardSerializer
        elif self.action == 'assign_package':
            return MellatAssignPackageSerializer
        # return super().get_serializer_class()
    def get_queryset(self):
        queryset = self.queryset
        _user = self.request.user
        # role_list = get_user_roles(_user)
        if not _user.pk:
            return queryset.filter(pk=-1)
        
        return queryset
    def filter_queryset(self,queryset):
        _filter = {}
        if 'search' in self.request.query_params and self.request.query_params['search']:
            _search = self.request.query_params['search']
            _filter.update({'title__icontains': _search})
        
        queryset = queryset.filter(**_filter).distinct()
        return queryset
    def get_object(self,pk=None):
        if pk:
            try:
                _object = self.get_queryset().get(pk=pk)
                return _object
            except ObjectDoesNotExist:
                return None


    @action(detail=False, methods=['get'])
    def login(self, request):       
        _token = get_mellat_token()
        return Response({'token':_token})
    
    @action(detail=False, methods=['get'])
    def packages(self, request):       
        res = GetAllPackages()
        return Response({'res':res['result']},status=res['status'])
    
    @action(detail=False, methods=['post'])
    def is_card_exist(self, request ):
        #MellatCheckCardSerializer
        _data = get_dict_data(request.data)
        _serializer = self.get_serializer(context={'request': request},data=_data)
        if _serializer.is_valid():
            _card = _data['card']            
            res = IsPanRegistered(_card)        
            return Response({'res':res['result']},status=res['status'])
        else:
            raise ProjectException(807, _('validation error'),_serializer.errors,status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def assign_package(self, request ):
        _data = get_dict_data(request.data)
        _serializer = self.get_serializer(context={'request': request},data=_data)
        if _serializer.is_valid():
            _serializer.save()       
            return Response(_serializer.data,status=status.HTTP_400_BAD_REQUEST)
        else:
            raise ProjectException(807, _('validation error'),_serializer.errors,status.HTTP_400_BAD_REQUEST)

    # @action(detail=False, methods=['get'])
    def discount_detail(self, request):
        from app.mellat import GetDiscountDetail
        terminal_id = 1
        pan = 1
        date = 1
        res = GetDiscountDetail(terminal_id,pan,date)
        return Response({'res':res['result']},status=res['status'])

    # @action(detail=False, methods=['get'])
    def discount(self, request):
        from app.tasks import discount_packges_task
        ss=discount_packges_task()
        return Response(ss)


    @swagger_auto_schema(query_serializer=MellatTransactionSerializer)
    @action(detail=False, methods=['get'])
    def transactions(self,request):
        if 'last_transaction_row' in request.query_params and request.query_params['last_transaction_row'] :
            _last_transaction_row=int(request.query_params['last_transaction_row'])
            res = GetTransactions(_last_transaction_row)
            return Response({'res':res['result']},status=res['status'])


class OperateViewSet(viewsets.GenericViewSet):
    queryset = OperateModel.objects.all()
    serializer_class = OperateSerializer
    permission_classes = ([IsAdminUser])
    renderer_classes = (JSONRenderer,)
    parser_classes = (JSONParser,)

    def get_parsers(self):
        if (hasattr(self,'action') and self.action in ["upload",]) or (hasattr(self,'name') and self.name in ["Upload",]):
            parser_classes=[MultiPartParser]
        else:
            parser_classes = [JSONParser]
        
        return [parser() for parser in parser_classes]
    def get_response_schema(action):
        # response_schema_dict
        responses = {}
        rsd = {
            "200":
            OperateSerializer,
            "200_Ok":
            openapi.Response({}),
            "201":
            OperateSerializer,
            "204":
            openapi.Response({}),
            "400":
            openapi.Response(
                description="Bad request",
                schema=SampleResponseSerializer,
                examples={
                    "application/json": {
                        "807": {
                            "status": "failed",
                            "code": 807,
                            "message": "validation error",
                            "detail": "System default error.",
                        },
                        "813": {
                            "status": "failed",
                            "code": 813,
                            "message": "validation error",
                            "detail": "Set the primary key.",
                        },
                    }
                },
            ),
            "403":
            openapi.Response(
                description="Forbidden",
                schema=SampleResponseSerializer,
                examples={
                    "application/json": {
                        "821": {
                            "status":
                            "failed",
                            "code":
                            821,
                            "message":
                            _("validation error"),
                            "detail":
                            _("You do not have permission to perform this action."
                              ),
                            "data": {},
                        },
                    }
                },
            ),
            "404":
            openapi.Response(
                description="Not found",
                schema=SampleResponseSerializer,
                examples={
                    "application/json": {
                        "820": {
                            "status": "failed",
                            "code": 820,
                            "message": "not found",
                            "detail": "This primary key not found",
                        },
                    }
                },
            ),
            "807":
            openapi.Response(
                description="Bad request",
                schema=SampleResponseSerializer,
                examples={
                    "application/json": {
                        "807": {
                            "status": "failed",
                            "code": 807,
                            "message": "validation error",
                            "detail": "System default error.",
                        },
                        
                    }
                },
            ),
            "800":
            openapi.Response(
                description="Bad request",
                schema=SampleResponseSerializer,
                examples={
                    "application/json": {
                        "800": {
                            "status": "failed",
                            "code": 800,
                            "message": "unknown error",
                            "detail": "Unknown error.",
                        },
                    }
                },
            ),
            "813":
            openapi.Response(
                description="Bad request",
                schema=SampleResponseSerializer,
                examples={
                    "application/json": {
                        "813": {
                            "status": "failed",
                            "code": 813,
                            "message": "validation error",
                            "detail": "Set the primary key.",
                        },
                    }
                },
            ),
            "sample":
            SampleResponseSerializer
        }
        if action in ["list"]:
            responses = {"200": rsd["200"], "400": rsd["807"]}
        elif action in ["create"]:
            responses = {"201": rsd["201"], "400": rsd["807"]}
        elif action == "retrieve":
            responses = {"200": rsd["200"],"400": rsd["400"],"404": rsd["404"]}
        elif action == "update":
            responses = {"200": rsd["200"],"404": rsd["404"],"400": rsd["400"]}
        elif action == "delete":
            responses = {"204": rsd["204"],"400": rsd["813"],"404": rsd["404"]}
        return responses
    def get_permissions(self):
        return super().get_permissions()
    def get_serializer_class(self):
        return super().get_serializer_class()
    def get_queryset(self):
        return super().get_queryset()
    def get_object(self,pk=None):
        if pk:
            try:
                _object = self.get_queryset().get(pk=pk)
                return _object
            except ObjectDoesNotExist:
                return None

    @swagger_auto_schema(responses=get_response_schema('list'))
    # @execute_with_permission('operate', 'list')
    def list(self, request):
        """
        get list of Operate API.

        ---

        """
        _queryset = self.get_queryset().order_by('pk')
        _count = _queryset.count()
        if _count == 0:
            return Response({'list': [],'total_page_num': 0,'total_row': 0},status=status.HTTP_204_NO_CONTENT)

        _queryset, _total_page_num = get_response_data(request, _queryset)
        _serializer = self.get_serializer(_queryset, many=True)
        return Response({
            'list': _serializer.data,
            'total_page_num': _total_page_num,
            'total_row': _count
        })

    @swagger_auto_schema(responses=get_response_schema('create'))
    # @execute_with_permission('operate', 'create')
    @transaction.atomic
    def create(self, request):
        """
        inset a Operate API.

        ---

        """
        _data = get_dict_data(request.data)
        _serializer = self.get_serializer(context={'request': request},data=_data)
        if _serializer.is_valid():
            _serializer.save()
            return Response(_serializer.data, status=status.HTTP_201_CREATED)
        else:
            raise ProjectException(807, _('validation error'),_serializer.errors,status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(responses=get_response_schema('retrieve'))
    # @execute_with_permission('operate', 'read')
    def retrieve(self, request, pk=None):
        """
        get a Operate API.

        ---

        """
        if pk:
            _object = self.get_object(pk)
            if _object:
                _serializer = self.get_serializer(instance=_object)
                return Response(_serializer.data)
            else:
                raise ProjectException(820, _('not found'),_('This primary key not found.'),status.HTTP_404_NOT_FOUND)
        else:
            raise ProjectException(813, _('validation error'),_('Set the primary key.'),status.HTTP_400_BAD_REQUEST)

    
    @swagger_auto_schema(responses=get_response_schema('update'))
    # @execute_with_permission('operate', 'update')
    @transaction.atomic
    def partial_update(self, request, pk=None):
        """
        update a Operate partial API.

        ---

        """
        if pk:
            _object = self.get_object(pk)
            if _object:
                _data = get_dict_data(request.data)
                _serializer = self.get_serializer(context={'request': request},instance=_object,data=_data,partial=True)
                if _serializer.is_valid():
                    _serializer.save()
                    return Response(_serializer.data)
                else:
                    raise ProjectException(807, _('validation error'),_serializer.errors,status.HTTP_400_BAD_REQUEST)
            else:
                raise ProjectException(820, _('not found'),_('This primary key not found.'),status.HTTP_404_NOT_FOUND)
        else:
            raise ProjectException(813, _('validation error'), _('Set the primary key.'),status.HTTP_400_BAD_REQUEST)


    @swagger_auto_schema(responses=get_response_schema('delete'))
    # @execute_with_permission('operate', 'delete')
    @transaction.atomic
    def destroy(self, request, pk=None):
        """
        delete a Operate  API.

        ---

        """
        if pk:
            _object = self.get_object(pk)
            if _object:
                _object.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            else:
                raise ProjectException(820, _('not found'),_('This primary key not found.'),status.HTTP_404_NOT_FOUND)
        else:
            raise ProjectException(813, _('validation error'),_('Set the primary key.'),status.HTTP_400_BAD_REQUEST)



class RoleViewSet(viewsets.GenericViewSet):
    queryset = RoleModel.objects.all()
    serializer_class = RoleSerializer
    permission_classes = ([IsAdminUser])
    renderer_classes = (JSONRenderer,)
    parser_classes = (JSONParser,)

    def get_parsers(self):
        if (hasattr(self,'action') and self.action in ["upload",]) or (hasattr(self,'name') and self.name in ["Upload",]):
            parser_classes=[MultiPartParser]
        else:
            parser_classes = [JSONParser]
        
        return [parser() for parser in parser_classes]
    def get_response_schema(action):
        # response_schema_dict
        responses = {}
        rsd = {
            "200":
            RoleInfoSerializer,
            "200_Ok":
            openapi.Response({}),
            "201":
            RoleSerializer,
            "201_permission":
            RolesPermissionsSerializer,
            "204":
            openapi.Response({}),
            "400":
            openapi.Response(
                description="Bad request",
                schema=SampleResponseSerializer,
                examples={
                    "application/json": {
                        "807": {
                            "status": "failed",
                            "code": 807,
                            "message": "validation error",
                            "detail": "System default error.",
                        },
                        "813": {
                            "status": "failed",
                            "code": 813,
                            "message": "validation error",
                            "detail": "Set the primary key.",
                        },
                    }
                },
            ),
            "403":
            openapi.Response(
                description="Forbidden",
                schema=SampleResponseSerializer,
                examples={
                    "application/json": {
                        "821": {
                            "status":
                            "failed",
                            "code":
                            821,
                            "message":
                            _("validation error"),
                            "detail":
                            _("You do not have permission to perform this action."
                              ),
                            "data": {},
                        },
                    }
                },
            ),
            "404":
            openapi.Response(
                description="Not found",
                schema=SampleResponseSerializer,
                examples={
                    "application/json": {
                        "820": {
                            "status": "failed",
                            "code": 820,
                            "message": "not found",
                            "detail": "This primary key not found",
                        },
                    }
                },
            ),
            "807":
            openapi.Response(
                description="Bad request",
                schema=SampleResponseSerializer,
                examples={
                    "application/json": {
                        "807": {
                            "status": "failed",
                            "code": 807,
                            "message": "validation error",
                            "detail": "System default error.",
                        },
                        
                    }
                },
            ),
            "800":
            openapi.Response(
                description="Bad request",
                schema=SampleResponseSerializer,
                examples={
                    "application/json": {
                        "800": {
                            "status": "failed",
                            "code": 800,
                            "message": "unknown error",
                            "detail": "Unknown error.",
                        },
                    }
                },
            ),
            "813":
            openapi.Response(
                description="Bad request",
                schema=SampleResponseSerializer,
                examples={
                    "application/json": {
                        "813": {
                            "status": "failed",
                            "code": 813,
                            "message": "validation error",
                            "detail": "Set the primary key.",
                        },
                    }
                },
            ),
            "get":
            RoleInfoGetSerializer,
            "sample":
            SampleResponseSerializer
        }
        if action in ["list"]:
            responses = {"200": rsd["200"], "400": rsd["807"]}
        elif action in ["create"]:
            responses = {"201": rsd["201"], "400": rsd["807"]}
        elif action == "retrieve":
            responses = {"200": rsd["200"],"400": rsd["400"],"404": rsd["404"]}
        elif action == "update":
            responses = {"200": rsd["200"],"404": rsd["404"],"400": rsd["400"]}
        elif action == "delete":
            responses = {"204": rsd["204"],"400": rsd["813"],"404": rsd["404"]}
        elif action in ["get"]:
            responses = {"200": rsd["get"], "400": rsd["807"]}
        elif action in ["permission"]:
            responses = {"201": rsd["200_Ok"], "400": rsd["807"]}
        elif action == "operate":
            responses = {"204": rsd["204"],"400": rsd["813"],"404": rsd["404"]}
        elif action == "state":
            responses = {"204": rsd["204"],"400": rsd["813"],"404": rsd["404"]}
        return responses
    def get_permissions(self):
        return super().get_permissions()
    def get_serializer_class(self):
        if self.action in ['list','retrieve',]:
            return RoleInfoSerializer
        elif self.action == 'get':
            return RoleInfoGetSerializer
        elif self.action == 'permission':
            return RolesPermissionsSerializer
        elif self.action == 'single_permission':
            return NoneSerializer
        elif self.action in ['operate','state']:
            return NoneSerializer
        return super().get_serializer_class()
    def get_queryset(self):
        return super().get_queryset()
    def get_object(self,pk=None):
        if pk:
            try:
                _object = self.get_queryset().get(pk=pk)
                return _object
            except ObjectDoesNotExist:
                return None
    def get_object_access(self,pk=None):
        if pk:
            try:
                _object = RoleAccessModel.objects.get(pk=pk)
                return _object
            except RoleAccessModel.DoesNotExist:
                return None
    def get_object_permission(self,pk=None):
        if pk:
            try:
                _object = RolePermissionModel.objects.get(pk=pk)
                return _object
            except RolePermissionModel.DoesNotExist:
                return None

    @swagger_auto_schema(responses=get_response_schema('list'))
    # @execute_with_permission('role', 'list')
    def list(self, request):
        """
        get list of Role API.

        ---

        """
        _queryset = self.get_queryset().order_by('pk')
        _count = _queryset.count()
        if _count == 0:
            return Response({'list': [],'total_page_num': 0,'total_row': 0},status=status.HTTP_204_NO_CONTENT)

        _queryset, _total_page_num = get_response_data(request, _queryset)
        _serializer = self.get_serializer(_queryset, many=True)
        return Response({
            'list': _serializer.data,
            'total_page_num': _total_page_num,
            'total_row': _count
        })

    @swagger_auto_schema(responses=get_response_schema('create'))
    # @execute_with_permission('role', 'create')
    @transaction.atomic
    def create(self, request):
        """
        inset a Role API.

        ---

        """
        _data = get_dict_data(request.data)
        _serializer = self.get_serializer(context={'request': request},data=_data)
        if _serializer.is_valid():
            _serializer.save()
            return Response(_serializer.data, status=status.HTTP_201_CREATED)
        else:
            raise ProjectException(807, _('validation error'),_serializer.errors,status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(responses=get_response_schema('retrieve'))
    # @execute_with_permission('role', 'read')
    def retrieve(self, request, pk=None):
        """
        get a Role API.

        ---

        """
        if pk:
            _object = self.get_object(pk)
            if _object:
                _serializer = self.get_serializer(instance=_object)
                return Response(_serializer.data)
            else:
                raise ProjectException(820, _('not found'),_('This primary key not found.'),status.HTTP_404_NOT_FOUND)
        else:
            raise ProjectException(813, _('validation error'),_('Set the primary key.'),status.HTTP_400_BAD_REQUEST)

    
    @swagger_auto_schema(responses=get_response_schema('update'))
    # @execute_with_permission('role', 'update')
    @transaction.atomic
    def partial_update(self, request, pk=None):
        """
        update a Role partial API.

        ---

        """
        if pk:
            _object = self.get_object(pk)
            if _object:
                _data = get_dict_data(request.data)
                _serializer = self.get_serializer(context={'request': request},instance=_object,data=_data,partial=True)
                if _serializer.is_valid():
                    _serializer.save()
                    return Response(_serializer.data)
                else:
                    raise ProjectException(807, _('validation error'),_serializer.errors,status.HTTP_400_BAD_REQUEST)
            else:
                raise ProjectException(820, _('not found'),_('This primary key not found.'),status.HTTP_404_NOT_FOUND)
        else:
            raise ProjectException(813, _('validation error'), _('Set the primary key.'),status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(responses=get_response_schema('delete'))
    # @execute_with_permission('role', 'delete')
    @transaction.atomic
    def destroy(self, request, pk=None):
        """
        delete a Role  API.

        ---

        """
        if pk:
            _object = self.get_object(pk)
            if _object:
                _object.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            else:
                raise ProjectException(820, _('not found'),_('This primary key not found.'),status.HTTP_404_NOT_FOUND)
        else:
            raise ProjectException(813, _('validation error'),_('Set the primary key.'),status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(responses=get_response_schema('get'))
    # @execute_with_permission('role', 'list')
    @action(detail=False, methods=['get'])
    def get(self, request):
        """
        get list of Role API.

        ---

        """
        _objects = self.get_queryset()
        _count = self.queryset.count()
        if 'page_size' in request.query_params and request.query_params['page_size'] and \
                'page_num' in request.query_params and request.query_params['page_num']:

            _page_size = request.query_params['page_size']
            _page_num = request.query_params['page_num']
            _objects, _total_page_num = get_data(_objects,pagination=(_page_size,_page_num))
        else:
            _objects, _total_page_num = get_data(_objects)

        if _count == 0:
            return Response({'list': [],'total_page_num': 0,'total_row': 0},status=status.HTTP_204_NO_CONTENT)
        _serializer = self.get_serializer(_objects, many=True)
        return Response({
            'list': _serializer.data,
            'total_page_num': _total_page_num,
            'total_row': _count
        })

    @swagger_auto_schema(responses=get_response_schema('permission'))
    # @execute_with_permission('permission', 'create')
    @action(detail=False, methods=['post'])
    @transaction.atomic
    def permission(self, request):
        _user = request.user
        _data = get_dict_data(request.data)
        _serializer = self.get_serializer(context={'request': request},data=_data)
        if _serializer.is_valid():
            _role_list = []
            _validated_data = _serializer.validated_data
            _permissions = _validated_data.get('permissions', None)
            for _obj in _permissions:
                _role = _obj['role']
                _role_list.append(_role)
                _states = _obj['states']
                for _state_obj in _states:
                    _state = _state_obj['state']
                    _access= RoleAccessModel.objects.create(role=_role,state=_state)
                    _access.save()
                    _operates = _state_obj['operates']
                    for _operate in _operates:
                        _permission = RolePermissionModel.objects.create(access=_access,operate=_operate)
                        _permission.save()

            return Response(status=status.HTTP_201_CREATED)
        else:
            raise ProjectException(807, _('validation error'),
                                   _serializer.errors,
                                   status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(responses=get_response_schema('operate'))
    # @execute_with_permission('permission', 'delete')   
    @action(detail=False, methods=['delete'], url_path="operate/(?P<pk>[^/.]+)")
    @transaction.atomic
    def operate(self, request, pk=None):
        """
        delete an Operate from a Role  API.

        ---

        """
        if pk:
            _object = self.get_object_permission(pk)
            if _object:
                _object.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            else:
                raise ProjectException(820, _('not found'),_('This primary key not found.'),status.HTTP_404_NOT_FOUND)
        else:
            raise ProjectException(813, _('validation error'),_('Set the primary key.'),status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(responses=get_response_schema('state'))
    # @execute_with_permission('permission', 'delete')
    @action(detail=False, methods=['delete'], url_path="state/(?P<pk>[^/.]+)")
    @transaction.atomic
    def state(self, request, pk=None):
        """
        delete a State from a Role  API.

        ---

        """
        if pk:
            _object = self.get_object_access(pk)
            if _object:
                _object.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            else:
                raise ProjectException(820, _('not found'),_('This primary key not found.'),status.HTTP_404_NOT_FOUND)
        else:
            raise ProjectException(813, _('validation error'),_('Set the primary key.'),status.HTTP_400_BAD_REQUEST)



class ServiceViewSet(viewsets.GenericViewSet):
    queryset = ServiceModel.objects.all()
    serializer_class = ServiceSerializer
    permission_classes = ([IsAuthenticated])
    renderer_classes = (JSONRenderer,)
    parser_classes = (JSONParser,)

    def get_parsers(self):
        if (hasattr(self,'action') and self.action in ["upload",]) or (hasattr(self,'name') and self.name in ["Upload",]):
            parser_classes=[MultiPartParser]
        else:
            parser_classes = [JSONParser]
        
        return [parser() for parser in parser_classes]
    def get_response_schema(action):
        # response_schema_dict
        responses = {}
        rsd = {
            "200":
            ServiceInfoSerializer,
            "200_Ok":
            openapi.Response({}),
            "201":
            ServiceSerializer,
            "204":
            openapi.Response({}),
            "400":
            openapi.Response(
                description="Bad request",
                schema=SampleResponseSerializer,
                examples={
                    "application/json": {
                        "807": {
                            "status": "failed",
                            "code": 807,
                            "message": "validation error",
                            "detail": "System default error.",
                        },
                        "813": {
                            "status": "failed",
                            "code": 813,
                            "message": "validation error",
                            "detail": "Set the primary key.",
                        },
                    }
                },
            ),
            "403":
            openapi.Response(
                description="Forbidden",
                schema=SampleResponseSerializer,
                examples={
                    "application/json": {
                        "821": {
                            "status":
                            "failed",
                            "code":
                            821,
                            "message":
                            _("validation error"),
                            "detail":
                            _("You do not have permission to perform this action."
                              ),
                            "data": {},
                        },
                    }
                },
            ),
            "404":
            openapi.Response(
                description="Not found",
                schema=SampleResponseSerializer,
                examples={
                    "application/json": {
                        "820": {
                            "status": "failed",
                            "code": 820,
                            "message": "not found",
                            "detail": "This primary key not found",
                        },
                    }
                },
            ),
            "807":
            openapi.Response(
                description="Bad request",
                schema=SampleResponseSerializer,
                examples={
                    "application/json": {
                        "807": {
                            "status": "failed",
                            "code": 807,
                            "message": "validation error",
                            "detail": "System default error.",
                        },
                        
                    }
                },
            ),
            "800":
            openapi.Response(
                description="Bad request",
                schema=SampleResponseSerializer,
                examples={
                    "application/json": {
                        "800": {
                            "status": "failed",
                            "code": 800,
                            "message": "unknown error",
                            "detail": "Unknown error.",
                        },
                    }
                },
            ),
            "813":
            openapi.Response(
                description="Bad request",
                schema=SampleResponseSerializer,
                examples={
                    "application/json": {
                        "813": {
                            "status": "failed",
                            "code": 813,
                            "message": "validation error",
                            "detail": "Set the primary key.",
                        },
                    }
                },
            ),
            "sample":
            SampleResponseSerializer
        }
        if action in ["list"]:
            responses = {"200": rsd["200"], "400": rsd["807"]}
        elif action in ["create"]:
            responses = {"201": rsd["201"], "400": rsd["807"]}
        elif action == "retrieve":
            responses = {"200": rsd["200"],"400": rsd["400"],"404": rsd["404"]}
        elif action == "update":
            responses = {"200": rsd["200"],"404": rsd["404"],"400": rsd["400"]}
        elif action == "delete":
            responses = {"204": rsd["204"],"400": rsd["813"],"404": rsd["404"]}
        return responses
    def get_permissions(self):
        if self.action in ['list','retrieve'] :
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]
    def get_serializer_class(self):
        if self.action in ['list','retrieve','trash']:
            return ServiceInfoSerializer
        elif self.action == 'partial_update':
            return ServiceSerializer
        elif self.action == 'status':
            return ServiceStatusSerializer
        elif self.action in ['some', 'recycle']:
            return NoneSerializer
        return super().get_serializer_class()
    def get_queryset(self):
        queryset = self.queryset
        _user = self.request.user
        # role_list = get_user_roles(_user)
        if not _user.pk:
            return queryset.filter(pk=-1)
        
        return queryset
    def filter_queryset(self,queryset,status=None):
        _filter = {}
        if 'level' in self.request.query_params and self.request.query_params['level']:
            _level = self.request.query_params['level']
            _filter.update({'order': _level})
        if 'search' in self.request.query_params and self.request.query_params['search']:
            _search = self.request.query_params['search']
            _filter.update({'title__icontains': _search})
        if status:
            _filter.update({'status': status})
        elif 'status' in self.request.query_params and self.request.query_params['status']:
            _status = get_dict_data(self.request.GET).get('status',None)
            if type(_status) != type([]):
                _status = [_status,]
            _filter.update({'status__in': _status})
        else:
            _filter.update({'status__in': [1, 0]})
        queryset = queryset.filter(**_filter).distinct()
        return queryset
    def get_object(self,pk=None):
        if pk:
            try:
                _object = self.get_queryset().get(pk=pk)
                return _object
            except ObjectDoesNotExist:
                return None

    @swagger_auto_schema(responses=get_response_schema('list'),query_serializer=ServiceFilterQuerySerializer)
    # @execute_with_permission('service', 'list')
    def list(self, request):
        """
        get list of service API.

        ---

        """
        _queryset = self.filter_queryset(queryset=self.get_queryset()).order_by('pk')
        # _queryset = _queryset.filter(order=0)
        _count = _queryset.count()
        if _count == 0:
            return Response({'list': [],'total_page_num': 0,'total_row': 0},status=status.HTTP_204_NO_CONTENT)

        _queryset, _total_page_num = get_response_data(request, _queryset)
        _serializer = self.get_serializer(_queryset, many=True)
        return Response({
            'list': _serializer.data,
            'total_page_num': _total_page_num,
            'total_row': _count
        })

    @swagger_auto_schema(responses=get_response_schema('create'))
    # @execute_with_permission('service', 'create')
    @transaction.atomic
    def create(self, request):
        """
        inset a service API.

        ---

        """
        _data = get_dict_data(request.data)
        _serializer = self.get_serializer(context={'request': request},data=_data)
        if _serializer.is_valid():
            _serializer.save()
            return Response(_serializer.data, status=status.HTTP_201_CREATED)
        else:
            raise ProjectException(807, _('validation error'),_serializer.errors,status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(responses=get_response_schema('retrieve'))
    # @execute_with_permission('service', 'read')
    def retrieve(self, request, pk=None):
        """
        get a service API.

        ---

        """
        if pk:
            _object = self.get_object(pk)
            if _object and (_object.status in [0,1]):
                _serializer = self.get_serializer(instance=_object)
                return Response(_serializer.data)
            else:
                raise ProjectException(820, _('not found'),_('This primary key not found.'),status.HTTP_404_NOT_FOUND)
        else:
            raise ProjectException(813, _('validation error'),_('Set the primary key.'),status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(responses=get_response_schema('update'))
    # @execute_with_permission('service', 'update')
    @transaction.atomic
    def partial_update(self, request, pk=None):
        """
        update a service partial API.

        ---

        """
        if pk:
            _object = self.get_object(pk)
            if _object:
                _data = get_dict_data(request.data)
                _serializer = self.get_serializer(context={'request': request},instance=_object,data=_data,partial=True)
                if _serializer.is_valid():
                    _serializer.save()
                    return Response(_serializer.data)
                else:
                    raise ProjectException(807, _('validation error'),_serializer.errors,status.HTTP_400_BAD_REQUEST)
            else:
                raise ProjectException(820, _('not found'),_('This primary key not found.'),status.HTTP_404_NOT_FOUND)
        else:
            raise ProjectException(813, _('validation error'), _('Set the primary key.'),status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(responses=get_response_schema('delete'))
    # @execute_with_permission('service', 'delete')
    @transaction.atomic
    def destroy(self, request, pk=None):
        """
        delete a service  API.

        ---

        """
        if pk:
            _object = self.get_object(pk)
            if _object:
                if deleted_parent(obj=_object):
                    
                    if _object.status == -1:
                        delete_child(obj=_object,state='service',status=-2)
                        _object.delete()
                    else:
                        delete_child(obj=_object,state='service',status=-1)
                        _object.status_old = _object.status
                        _object.status = -1
                        _object.save()
                    return Response(status=status.HTTP_204_NO_CONTENT)
                else:
                    return Response({'error': _('You can not delete this service. Because this service has not deleted childs.')},
                                status=status.HTTP_400_BAD_REQUEST)
            else:
                raise ProjectException(820, _('not found'),_('This primary key not found.'),status.HTTP_404_NOT_FOUND)
        else:
            raise ProjectException(813, _('validation error'),_('Set the primary key.'),status.HTTP_400_BAD_REQUEST)


    @swagger_auto_schema(responses=get_response_schema('update'))
    # @execute_with_permission('service', 'update')
    @action(detail=True,methods=['patch'],)
    @transaction.atomic
    def upload(self, request, pk=None):
        """
        upload image for Service API.

        ---
            
        """
        if pk:
            _object = self.get_object(pk)
            if _object:
                _data = get_dict_data(request.data)
                _serializer = self.get_serializer(context={'request': request},instance=_object,data=_data,partial=True)
                if _serializer.is_valid():
                    _object = _serializer.save()
                    _serializer = ServiceInfoSerializer(instance=_object)
                    return Response(_serializer.data)
                else:
                    raise ProjectException(807, _('validation error'),_serializer.errors,status.HTTP_400_BAD_REQUEST)
            else:
                raise ProjectException(820, _('not found'),_('This primary key not found.'),status.HTTP_404_NOT_FOUND)
        else:
            raise ProjectException(813, _('validation error'), _('Set the primary key.'),status.HTTP_400_BAD_REQUEST)

    
    # Multi ID:
    # # @execute_with_permission_multi_id('service', 'delete')
    @swagger_auto_schema(
        method='delete',
        request_body=openapi.Schema(type=openapi.TYPE_OBJECT,
                                properties={'id':openapi.Schema(type=openapi.TYPE_ARRAY,
                                items=openapi.Items(type=openapi.TYPE_INTEGER),
                                description='A list of primary keys'),
                }),
        responses=get_response_schema('some')
        )
    @action(detail=False, methods=['delete'])
    @transaction.atomic
    def some(self, request):
        """
        delete some service API.

        ---

        """
        _user = request.user
        _data = get_dict_data(request.data)
        _ids = _data['id']
        if type(_ids) == type([]):
            _serializer = ServiceSomeSerializer(context={"request": request},data=_data,)
            if _serializer.is_valid():
                valid_data = _serializer.validated_data
                _queryset = valid_data['id']
                _id_in = [obj.pk for obj in _queryset]
                _queryset = self.queryset.filter(pk__in=_id_in)
                if _queryset:
                    _deletes = []
                    _v_deletes = []
                    _count = 0
                    _v_count = 0
                    for _obj in _queryset:
                        if deleted_parent(obj=_obj):
                            if _obj.status == -1:
                                _count += 1
                                _deletes.append({str(_obj.id): _('deleted')})
                                _v_deletes.append(
                                    {str(_obj.id): _('deletion is not possible')})
                            else:
                                _v_count += 1
                                _v_deletes.append({str(_obj.id): _('virtual deleted')})
                                _deletes.append(
                                    {str(_obj.id): _('virtual deletion is not possible')})
                        else:
                            return Response({'error': _(f'You can not delete service with pk={_obj.pk}. Because this service has not deleted childs.')},
                                status=status.HTTP_400_BAD_REQUEST)
                    if _deletes or _v_deletes:
                        if _count == 0 or _v_count == 0:
                            if _count > 0:
                                for _obj in _queryset:
                                    delete_child(obj=_obj,state='service',status=-2)
                                    _obj.delete()
                                return Response(_deletes,
                                                status=status.HTTP_204_NO_CONTENT)
                            elif _v_count > 0:
                                for _obj in _queryset:
                                    delete_child(obj=_obj,state='service',status=-1)
                                    _obj.status_old = _obj.status
                                    _obj.status = -1
                                    _obj.save()
                                return Response(_v_deletes, status=status.HTTP_200_OK)

                        else:
                            raise ProjectException(845, _('not found'),
                                        _("Some users are not in the system."),
                                        status.HTTP_404_NOT_FOUND)
                else:
                    raise ProjectException(819, _('not found error'),
                                        _('Primary keys list is empty.'),
                                        status.HTTP_404_NOT_FOUND)
            else:
                raise ProjectException(807, _('validation error'),
                                        _serializer.errors,
                                        status.HTTP_400_BAD_REQUEST)
        else:
            raise ProjectException(807, _('validation error'),
                                        _("id:[Expected a list of items but got type.]"),
                                        status.HTTP_400_BAD_REQUEST)

    # # @execute_with_permission_multi_id('service', 'status')
    @swagger_auto_schema(responses=get_response_schema('status'))
    @action(detail=False, methods=['patch'])
    @transaction.atomic
    def status(self, request):
        """
        change service some Users  API.

        ---

        """
        _user = request.user
        _data = get_dict_data(request.data)
        _serializer = self.get_serializer(context={"request": request},data=_data,)
        if _serializer.is_valid():
            valid_data = _serializer.validated_data
            _objects = valid_data['id']
            _status = valid_data['status']
            if _objects and (_status is not None):
                for obj in _objects:
                    if deleted_parent(obj=obj):
                        obj.status_old = obj.status
                        obj.status = _status
                        recover_child(obj=obj,state='service')                    
                self.queryset.bulk_update(_objects, ['status'])
                return Response(status=status.HTTP_200_OK)
            else:
                raise ProjectException(819, _('not found error'),
                                    _('Primary keys list is empty.'),
                                    status.HTTP_404_NOT_FOUND)
        else:
            raise ProjectException(807, _('validation error'),
                                    _serializer.errors,
                                    status.HTTP_400_BAD_REQUEST)

    
    @swagger_auto_schema(query_serializer=ServiceTrashFilterQuerySerializer)
    @action(detail=False, methods=['get'])
    def trash(self, request):
        """
        get list of deleted service API.

        ---
        status=(-1,'trash'),(0,'unpublish'),(1,'publish')

        """
        _queryset = self.get_queryset()
        _queryset = self.filter_queryset(queryset=_queryset,status=-1).order_by('pk')
        _count = _queryset.count()
        if _count == 0:
            return Response(status=status.HTTP_204_NO_CONTENT)

        _queryset, _total_page_num = get_response_data(request, _queryset)
        _serializer = self.get_serializer(_queryset, many=True)
        return Response({
            'list': _serializer.data,
            'total_page_num': _total_page_num,
            'total_row': _count
        })


    # @execute_with_permission('service', 'recycle')
    @swagger_auto_schema(responses=get_response_schema('recycle'))
    @action(detail=True, methods=['patch'])
    @transaction.atomic
    def recycle(self, request, pk=None):
        """
        recycle a service API.

        ---

        """
        _user = request.user
        if pk:
            _object = self.get_object(pk)
            if _object:
                if _object.status == -1:
                    if deleted_parent(obj=_object):
                        _object.status_old = _object.status
                        _object.status = 1
                        _object.save()
                        recover_child(obj=_object,state='service')
                        return Response(status=status.HTTP_200_OK)
                    else:
                        return Response({'error': _('You can not recycle this service. Because this service has deleted roots.')},
                                status=status.HTTP_400_BAD_REQUEST)
                else:
                    return Response({'error': _('object not deleted')},
                                status=status.HTTP_400_BAD_REQUEST)
            else:
                raise ProjectException(0, _('not found error'),
                                    _('not found error'),
                                    status.HTTP_404_NOT_FOUND)
        else:
            raise ProjectException(0, _('not found error'),
                                   _('not found error'),
                                   status.HTTP_404_NOT_FOUND)



class StateViewSet(viewsets.GenericViewSet):
    queryset = StateModel.objects.all()
    serializer_class = StateSerializer
    permission_classes = ([IsAdminUser])
    renderer_classes = (JSONRenderer,)
    parser_classes = (JSONParser,)
    
    def get_parsers(self):
        if (hasattr(self,'action') and self.action in ["upload",]) or (hasattr(self,'name') and self.name in ["Upload",]):
            parser_classes=[MultiPartParser]
        else:
            parser_classes = [JSONParser]
        
        return [parser() for parser in parser_classes]
    def get_response_schema(action):
        # response_schema_dict
        responses = {}
        rsd = {
            "200":
            StateSerializer,
            "200_Ok":
            openapi.Response({}),
            "201":
            StateSerializer,
            "204":
            openapi.Response({}),
            "400":
            openapi.Response(
                description="Bad request",
                schema=SampleResponseSerializer,
                examples={
                    "application/json": {
                        "807": {
                            "status": "failed",
                            "code": 807,
                            "message": "validation error",
                            "detail": "System default error.",
                        },
                        "813": {
                            "status": "failed",
                            "code": 813,
                            "message": "validation error",
                            "detail": "Set the primary key.",
                        },
                    }
                },
            ),
            "403":
            openapi.Response(
                description="Forbidden",
                schema=SampleResponseSerializer,
                examples={
                    "application/json": {
                        "821": {
                            "status":
                            "failed",
                            "code":
                            821,
                            "message":
                            _("validation error"),
                            "detail":
                            _("You do not have permission to perform this action."
                              ),
                            "data": {},
                        },
                    }
                },
            ),
            "404":
            openapi.Response(
                description="Not found",
                schema=SampleResponseSerializer,
                examples={
                    "application/json": {
                        "820": {
                            "status": "failed",
                            "code": 820,
                            "message": "not found",
                            "detail": "This primary key not found",
                        },
                    }
                },
            ),
            "807":
            openapi.Response(
                description="Bad request",
                schema=SampleResponseSerializer,
                examples={
                    "application/json": {
                        "807": {
                            "status": "failed",
                            "code": 807,
                            "message": "validation error",
                            "detail": "System default error.",
                        },
                        
                    }
                },
            ),
            "800":
            openapi.Response(
                description="Bad request",
                schema=SampleResponseSerializer,
                examples={
                    "application/json": {
                        "800": {
                            "status": "failed",
                            "code": 800,
                            "message": "unknown error",
                            "detail": "Unknown error.",
                        },
                    }
                },
            ),
            "813":
            openapi.Response(
                description="Bad request",
                schema=SampleResponseSerializer,
                examples={
                    "application/json": {
                        "813": {
                            "status": "failed",
                            "code": 813,
                            "message": "validation error",
                            "detail": "Set the primary key.",
                        },
                    }
                },
            ),
            "sample":
            SampleResponseSerializer
        }
        if action in ["list"]:
            responses = {"200": rsd["200"], "400": rsd["807"]}
        elif action in ["create"]:
            responses = {"201": rsd["201"], "400": rsd["807"]}
        elif action == "retrieve":
            responses = {"200": rsd["200"],"400": rsd["400"],"404": rsd["404"]}
        elif action == "update":
            responses = {"200": rsd["200"],"404": rsd["404"],"400": rsd["400"]}
        elif action == "delete":
            responses = {"204": rsd["204"],"400": rsd["813"],"404": rsd["404"]}
        return responses
    def get_permissions(self):
        return super().get_permissions()
    def get_serializer_class(self):
        return super().get_serializer_class()
    def get_queryset(self):
        return super().get_queryset()
    def get_object(self,pk=None):
        if pk:
            try:
                _object = self.get_queryset().get(pk=pk)
                return _object
            except ObjectDoesNotExist:
                return None

    @swagger_auto_schema(responses=get_response_schema('list'))
    # @execute_with_permission('state', 'list')
    def list(self, request):
        """
        get list of State API.

        ---

        """
        _queryset = self.get_queryset().order_by('pk')
        _count = _queryset.count()
        if _count == 0:
            return Response({'list': [],'total_page_num': 0,'total_row': 0},status=status.HTTP_204_NO_CONTENT)

        _queryset, _total_page_num = get_response_data(request, _queryset)
        _serializer = self.get_serializer(_queryset, many=True)
        return Response({
            'list': _serializer.data,
            'total_page_num': _total_page_num,
            'total_row': _count
        })

    @swagger_auto_schema(responses=get_response_schema('create'))
    # @execute_with_permission('state', 'create')
    @transaction.atomic
    def create(self, request):
        """
        inset a State API.

        ---

        """
        _data = get_dict_data(request.data)
        _serializer = self.get_serializer(context={'request': request},data=_data)
        if _serializer.is_valid():
            _serializer.save()
            return Response(_serializer.data, status=status.HTTP_201_CREATED)
        else:
            raise ProjectException(807, _('validation error'),_serializer.errors,status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(responses=get_response_schema('retrieve'))
    # @execute_with_permission('state', 'read')
    def retrieve(self, request, pk=None):
        """
        get a State API.

        ---

        """
        if pk:
            _object = self.get_object(pk)
            if _object:
                _serializer = self.get_serializer(instance=_object)
                return Response(_serializer.data)
            else:
                raise ProjectException(820, _('not found'),_('This primary key not found.'),status.HTTP_404_NOT_FOUND)
        else:
            raise ProjectException(813, _('validation error'),_('Set the primary key.'),status.HTTP_400_BAD_REQUEST)

    
    @swagger_auto_schema(responses=get_response_schema('update'))
    # @execute_with_permission('state', 'update')
    @transaction.atomic
    def partial_update(self, request, pk=None):
        """
        update a State partial API.

        ---

        """
        if pk:
            _object = self.get_object(pk)
            if _object:
                _data = get_dict_data(request.data)
                _serializer = self.get_serializer(context={'request': request},instance=_object,data=_data,partial=True)
                if _serializer.is_valid():
                    _serializer.save()
                    return Response(_serializer.data)
                else:
                    raise ProjectException(807, _('validation error'),_serializer.errors,status.HTTP_400_BAD_REQUEST)
            else:
                raise ProjectException(820, _('not found'),_('This primary key not found.'),status.HTTP_404_NOT_FOUND)
        else:
            raise ProjectException(813, _('validation error'), _('Set the primary key.'),status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(responses=get_response_schema('delete'))
    # @execute_with_permission('state', 'delete')
    @transaction.atomic
    def destroy(self, request, pk=None):
        """
        delete a State  API.

        ---

        """
        if pk:
            _object = self.get_object(pk)
            if _object:
                _object.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            else:
                raise ProjectException(820, _('not found'),_('This primary key not found.'),status.HTTP_404_NOT_FOUND)
        else:
            raise ProjectException(813, _('validation error'),_('Set the primary key.'),status.HTTP_400_BAD_REQUEST)



class StoreViewSet(viewsets.GenericViewSet):
    queryset = StoreModel.objects.all()
    serializer_class   = StoreSerializer
    permission_classes = ([IsAuthenticated])
    renderer_classes   = (JSONRenderer,)
    parser_classes     = (JSONParser,)

    def get_parsers(self):
        if (hasattr(self,'action') and self.action in ["upload",]) or (hasattr(self,'name') and self.name in ["Upload",]):
            parser_classes=[MultiPartParser]
        else:
            parser_classes = [JSONParser]
        
        return [parser() for parser in parser_classes]
    def get_response_schema(action):
        # response_schema_dict
        responses = {}
        rsd = {
            "200":
            StoreInfoSerializer,
            "200_Ok":
            openapi.Response({}),
            "201":
            StoreSerializer,
            "204":
            openapi.Response({}),
            "400":
            openapi.Response(
                description="Bad request",
                schema=SampleResponseSerializer,
                examples={
                    "application/json": {
                        "807": {
                            "status": "failed",
                            "code": 807,
                            "message": "validation error",
                            "detail": "System default error.",
                        },
                        "813": {
                            "status": "failed",
                            "code": 813,
                            "message": "validation error",
                            "detail": "Set the primary key.",
                        },
                    }
                },
            ),
            "403":
            openapi.Response(
                description="Forbidden",
                schema=SampleResponseSerializer,
                examples={
                    "application/json": {
                        "821": {
                            "status":
                            "failed",
                            "code":
                            821,
                            "message":
                            _("validation error"),
                            "detail":
                            _("You do not have permission to perform this action."
                              ),
                            "data": {},
                        },
                    }
                },
            ),
            "404":
            openapi.Response(
                description="Not found",
                schema=SampleResponseSerializer,
                examples={
                    "application/json": {
                        "820": {
                            "status": "failed",
                            "code": 820,
                            "message": "not found",
                            "detail": "This primary key not found",
                        },
                    }
                },
            ),
            "807":
            openapi.Response(
                description="Bad request",
                schema=SampleResponseSerializer,
                examples={
                    "application/json": {
                        "807": {
                            "status": "failed",
                            "code": 807,
                            "message": "validation error",
                            "detail": "System default error.",
                        },
                        
                    }
                },
            ),
            "800":
            openapi.Response(
                description="Bad request",
                schema=SampleResponseSerializer,
                examples={
                    "application/json": {
                        "800": {
                            "status": "failed",
                            "code": 800,
                            "message": "unknown error",
                            "detail": "Unknown error.",
                        },
                    }
                },
            ),
            "813":
            openapi.Response(
                description="Bad request",
                schema=SampleResponseSerializer,
                examples={
                    "application/json": {
                        "813": {
                            "status": "failed",
                            "code": 813,
                            "message": "validation error",
                            "detail": "Set the primary key.",
                        },
                    }
                },
            ),
            "sample":
            SampleResponseSerializer
        }
        if action in ["list"]:
            responses = {"200": rsd["200"], "400": rsd["807"]}
        elif action in ["create"]:
            responses = {"201": rsd["201"], "400": rsd["807"]}
        elif action == "retrieve":
            responses = {"200": rsd["200"],"400": rsd["400"],"404": rsd["404"]}
        elif action == "update":
            responses = {"200": rsd["200"],"404": rsd["404"],"400": rsd["400"]}
        elif action == "delete":
            responses = {"204": rsd["204"],"400": rsd["813"],"404": rsd["404"]}
        return responses
    def get_permissions(self):
        if self.action in ['list','retrieve'] :
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]
    def get_serializer_class(self):
        if self.action in ['list','retrieve','trash']:
            return StoreInfoSerializer
        elif self.action == 'partial_update':
            return StoreSerializer
        elif self.action == 'status':
            return StoreStatusSerializer
        elif self.action in ['some', 'recycle']:
            return NoneSerializer
        return super().get_serializer_class()
    def get_queryset(self):
        queryset = self.queryset
        _user = self.request.user
        # role_list = get_user_roles(_user)
        if not _user.pk:
            return queryset.filter(pk=-1)
        
        return queryset
    def filter_queryset(self,queryset,status=None):
        _filter = {}
        if 'level' in self.request.query_params and self.request.query_params['level']:
            _level = self.request.query_params['level']
            _filter.update({'order': _level})
        if 'search' in self.request.query_params and self.request.query_params['search']:
            _search = self.request.query_params['search']
            _filter.update({'title__icontains': _search})
        if status:
            _filter.update({'status': status})
        elif 'status' in self.request.query_params and self.request.query_params['status']:
            _status = get_dict_data(self.request.GET).get('status',None)
            if type(_status) != type([]):
                _status = [_status,]
            _filter.update({'status__in': _status})
        else:
            _filter.update({'status__in': [1, 0]})
        if ('latitude' in self.request.query_params) and ('longitude' in self.request.query_params)and('radius' in self.request.query_params):
            _latitude = self.request.query_params['latitude']
            _longitude = self.request.query_params['longitude']
            _radius = self.request.query_params['radius']
            gcd_formula = "6371000 * acos(cos(radians(%s)) * cos(radians(latitude)) * cos(radians(longitude) - radians(%s)) + sin(radians(%s)) * sin(radians(latitude)))"
            distance_raw_sql = RawSQL(
                gcd_formula, (_latitude, _longitude, _latitude))
            # gcd_formula =   """2*6371000*atan2(sqrt(power(sin((radians(latitude)-radians(%s))/2),2)+(cos(radians(latitude))*cos(radians(%s))*power(sin((radians(longitude)-radians(%s))/2),2))),
            #    sqrt(1-(power(sin((radians(latitude)-radians(%s))/2),2)+(cos(radians(latitude))*cos(radians(%s))*power(sin((radians(longitude)-radians(%s))/2),2)))))"""
            # distance_raw_sql = RawSQL(
            #     gcd_formula, (_latitude,_latitude, _longitude, _latitude,_latitude,_longitude))
            if 'service' in self.request.query_params and self.request.query_params['service']:
                _service = self.request.query_params['service']
                _filter.update({'service__service': _search})
            if 'keyword' in self.request.query_params and self.request.query_params['keyword']:
                _keyword = self.request.query_params['keyword']
                _filter.update({'title__icontains': _keyword})
            if _radius == 0:
                queryset = StoreModel.objects.filter(
                       **_filter).annotate(distance=distance_raw_sql).order_by('distance')
            else:
                queryset = StoreModel.objects.filter(
                      **_filter).annotate(distance=distance_raw_sql).filter(distance__lt=_radius).order_by('distance')
        else:
            queryset = queryset.filter(**_filter).distinct()
        return queryset
    def get_object(self,pk=None):
        if pk:
            try:
                _object = self.get_queryset().get(pk=pk)
                return _object
            except ObjectDoesNotExist:
                return None

    @swagger_auto_schema(responses=get_response_schema('list'),query_serializer=StoreFilterQuerySerializer)
    # @execute_with_permission('store', 'list')
    def list(self, request):
        """
        get list of store API.

        ---

        """
        _queryset = self.filter_queryset(queryset=self.get_queryset()).order_by('pk')
        # _queryset = _queryset.filter(order=0)
        _count = _queryset.count()
        if _count == 0:
            return Response({'list': [],'total_page_num': 0,'total_row': 0},status=status.HTTP_204_NO_CONTENT)

        _queryset, _total_page_num = get_response_data(request, _queryset)
        _serializer = self.get_serializer(_queryset, many=True)
        return Response({
            'list': _serializer.data,
            'total_page_num': _total_page_num,
            'total_row': _count
        })

    @swagger_auto_schema(responses=get_response_schema('create'))
    # @execute_with_permission('store', 'create')
    @transaction.atomic
    def create(self, request):
        """
        inset a store API.

        ---

        """
        _data = get_dict_data(request.data)
        _serializer = self.get_serializer(context={'request': request},data=_data)
        if _serializer.is_valid():
            _serializer.save()
            return Response(_serializer.data, status=status.HTTP_201_CREATED)
        else:
            raise ProjectException(807, _('validation error'),_serializer.errors,status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(responses=get_response_schema('retrieve'))
    # @execute_with_permission('store', 'read')
    def retrieve(self, request, pk=None):
        """
        get a store API.

        ---

        """
        if pk:
            _object = self.get_object(pk)
            if _object:
                _serializer = self.get_serializer(instance=_object)
                return Response(_serializer.data)
            else:
                raise ProjectException(820, _('not found'),_('This primary key not found.'),status.HTTP_404_NOT_FOUND)
        else:
            raise ProjectException(813, _('validation error'),_('Set the primary key.'),status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(responses=get_response_schema('update'))
    # @execute_with_permission('store', 'update')
    @transaction.atomic
    def partial_update(self, request, pk=None):
        """
        update a store partial API.

        ---

        """
        if pk:
            _object = self.get_object(pk)
            if _object:
                _data = get_dict_data(request.data)
                _serializer = self.get_serializer(context={'request': request},instance=_object,data=_data,partial=True)
                if _serializer.is_valid():
                    _serializer.save()
                    return Response(_serializer.data)
                else:
                    raise ProjectException(807, _('validation error'),_serializer.errors,status.HTTP_400_BAD_REQUEST)
            else:
                raise ProjectException(820, _('not found'),_('This primary key not found.'),status.HTTP_404_NOT_FOUND)
        else:
            raise ProjectException(813, _('validation error'), _('Set the primary key.'),status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(responses=get_response_schema('delete'))
    # @execute_with_permission('store', 'delete')
    @transaction.atomic
    def destroy(self, request, pk=None):
        """
        delete a store  API.

        ---

        """
        if pk:
            _object = self.get_object(pk)
            if _object:
                if deleted_parent(obj=_object):
                    
                    if _object.status == -1:
                        delete_child(obj=_object,state='store',status=-2)
                        _object.delete()
                    else:
                        delete_child(obj=_object,state='store',status=-1)
                        _object.status_old = _object.status
                        _object.status = -1
                        _object.save()
                    return Response(status=status.HTTP_204_NO_CONTENT)
                else:
                    return Response({'error': _('You can not delete this store. Because this store has not deleted childs.')},
                                status=status.HTTP_400_BAD_REQUEST)
            else:
                raise ProjectException(820, _('not found'),_('This primary key not found.'),status.HTTP_404_NOT_FOUND)
        else:
            raise ProjectException(813, _('validation error'),_('Set the primary key.'),status.HTTP_400_BAD_REQUEST)


    @swagger_auto_schema(responses=get_response_schema('update'))
    # @execute_with_permission('store', 'update')
    @action(detail=True,methods=['patch'],)
    @transaction.atomic
    def upload(self, request, pk=None):
        """
        upload icon for store API.

        ---
            
        """
        if pk:
            _object = self.get_object(pk)
            if _object:
                _data = get_dict_data(request.data)
                _serializer = self.get_serializer(context={'request': request},instance=_object,data=_data,partial=True)
                if _serializer.is_valid():
                    _object = _serializer.save()
                    _serializer = StoreInfoSerializer(instance=_object)
                    return Response(_serializer.data)
                else:
                    raise ProjectException(807, _('validation error'),_serializer.errors,status.HTTP_400_BAD_REQUEST)
            else:
                raise ProjectException(820, _('not found'),_('This primary key not found.'),status.HTTP_404_NOT_FOUND)
        else:
            raise ProjectException(813, _('validation error'), _('Set the primary key.'),status.HTTP_400_BAD_REQUEST)

    
    # Multi ID:
    # # @execute_with_permission_multi_id('store', 'delete')
    @swagger_auto_schema(
        method='delete',
        request_body=openapi.Schema(type=openapi.TYPE_OBJECT,
                                properties={'id':openapi.Schema(type=openapi.TYPE_ARRAY,
                                items=openapi.Items(type=openapi.TYPE_INTEGER),
                                description='A list of primary keys'),
                }),
        responses=get_response_schema('some')
        )
    @action(detail=False, methods=['delete'])
    @transaction.atomic
    def some(self, request):
        """
        delete some store API.

        ---

        """
        _user = request.user
        _data = get_dict_data(request.data)
        _ids = _data['id']
        if type(_ids) == type([]):
            _serializer = StoreSomeSerializer(context={"request": request},data=_data,)
            if _serializer.is_valid():
                valid_data = _serializer.validated_data
                _queryset = valid_data['id']
                _id_in = [obj.pk for obj in _queryset]
                _queryset = self.queryset.filter(pk__in=_id_in)
                if _queryset:
                    _deletes = []
                    _v_deletes = []
                    _count = 0
                    _v_count = 0
                    for _obj in _queryset:
                        if deleted_parent(obj=_obj):
                            if _obj.status == -1:
                                _count += 1
                                _deletes.append({str(_obj.id): _('deleted')})
                                _v_deletes.append(
                                    {str(_obj.id): _('deletion is not possible')})
                            else:
                                _v_count += 1
                                _v_deletes.append({str(_obj.id): _('virtual deleted')})
                                _deletes.append(
                                    {str(_obj.id): _('virtual deletion is not possible')})
                        else:
                            return Response({'error': _(f'You can not delete store with pk={_obj.pk}. Because this store has not deleted childs.')},
                                status=status.HTTP_400_BAD_REQUEST)
                    if _deletes or _v_deletes:
                        if _count == 0 or _v_count == 0:
                            if _count > 0:
                                for _obj in _queryset:
                                    delete_child(obj=_obj,state='store',status=-2)
                                    _obj.delete()
                                return Response(_deletes,
                                                status=status.HTTP_204_NO_CONTENT)
                            elif _v_count > 0:
                                for _obj in _queryset:
                                    delete_child(obj=_obj,state='store',status=-1)
                                    _obj.status_old = _obj.status
                                    _obj.status = -1
                                    _obj.save()
                                return Response(_v_deletes, status=status.HTTP_200_OK)
                        else:
                            raise ProjectException(845, _('not found'),
                                        _("Some users are not in the system."),
                                        status.HTTP_404_NOT_FOUND)
                else:
                    raise ProjectException(819, _('not found error'),
                                        _('Primary keys list is empty.'),
                                        status.HTTP_404_NOT_FOUND)
            else:
                raise ProjectException(807, _('validation error'),
                                        _serializer.errors,
                                        status.HTTP_400_BAD_REQUEST)
        else:
            raise ProjectException(807, _('validation error'),
                                        _("id:[Expected a list of items but got type.]"),
                                        status.HTTP_400_BAD_REQUEST)

    # # @execute_with_permission_multi_id('store', 'status')
    @swagger_auto_schema(responses=get_response_schema('status'))
    @action(detail=False, methods=['patch'])
    @transaction.atomic
    def status(self, request):
        """
        change store some Users  API.

        ---

        """
        _user = request.user
        _data = get_dict_data(request.data)
        _serializer = self.get_serializer(context={"request": request},data=_data,)
        if _serializer.is_valid():
            valid_data = _serializer.validated_data
            _objects = valid_data['id']
            _status = valid_data['status']
            if _objects and (_status is not None):
                for obj in _objects:
                    if deleted_parent(obj=obj):
                        obj.status_old = obj.status
                        obj.status = _status
                        recover_child(obj=obj,state='store')                    
                self.queryset.bulk_update(_objects, ['status'])
                return Response(status=status.HTTP_200_OK)
            else:
                raise ProjectException(819, _('not found error'),
                                    _('Primary keys list is empty.'),
                                    status.HTTP_404_NOT_FOUND)
        else:
            raise ProjectException(807, _('validation error'),
                                    _serializer.errors,
                                    status.HTTP_400_BAD_REQUEST)
    @swagger_auto_schema(query_serializer=StoreTrashFilterQuerySerializer)
    @action(detail=False, methods=['get'])
    def trash(self, request):
        """
        get list of deleted store API.

        ---
        status=(-1,'trash'),(0,'unpublish'),(1,'publish')

        """
        _queryset = self.get_queryset()
        _queryset = self.filter_queryset(queryset=_queryset,status=-1).order_by('pk')
        _count = _queryset.count()
        if _count == 0:
            return Response(status=status.HTTP_204_NO_CONTENT)

        _queryset, _total_page_num = get_response_data(request, _queryset)
        _serializer = self.get_serializer(_queryset, many=True)
        return Response({
            'list': _serializer.data,
            'total_page_num': _total_page_num,
            'total_row': _count
        })


    # @execute_with_permission('store', 'recycle')
    @swagger_auto_schema(responses=get_response_schema('recycle'))
    @action(detail=True, methods=['patch'])
    @transaction.atomic
    def recycle(self, request, pk=None):
        """
        recycle a store API.

        ---

        """
        _user = request.user
        if pk:
            _object = self.get_object(pk)
            if _object:
                if _object.status == -1:
                    if deleted_parent(obj=_object):
                        _object.status_old = _object.status
                        _object.status = 1
                        _object.save()
                        recover_child(obj=_object,state='store')
                        return Response(status=status.HTTP_200_OK)
                    else:
                        return Response({'error': _('You can not recycle this store. Because this store has deleted roots.')},
                                status=status.HTTP_400_BAD_REQUEST)
                else:
                    return Response({'error': _('object not deleted')},
                                status=status.HTTP_400_BAD_REQUEST)
            else:
                raise ProjectException(0, _('not found error'),
                                    _('not found error'),
                                    status.HTTP_404_NOT_FOUND)
        else:
            raise ProjectException(0, _('not found error'),
                                   _('not found error'),
                                   status.HTTP_404_NOT_FOUND)


    @swagger_auto_schema(query_serializer=StoreNearByFilterQuerySerializer)
    @action(detail=False, methods=['get'])
    # @shared_task
    def nearby(self, request):
        """
        get list of store near by a position base on radius|service|keyword  API.

        ---
        
        """
        _queryset = self.get_queryset()
        _queryset = self.filter_queryset(queryset=_queryset,)
        _count = _queryset.count()
        if _count == 0:
            return Response(status=status.HTTP_204_NO_CONTENT)

        _queryset, _total_page_num = get_response_data(request, _queryset)
        _serializer = self.get_serializer(_queryset, many=True)
        return Response({
            'list': _serializer.data,
            'total_page_num': _total_page_num,
            'total_row': _count
        })

 

class UserViewSet(viewsets.GenericViewSet):
    queryset = UserModel.objects.all()
    serializer_class = UserSerializer
    permission_classes = ([AllowAny])
    renderer_classes = (JSONRenderer,)
    parser_classes = (JSONParser,)

    def get_parsers(self):
        if (hasattr(self,'action') and self.action in ["upload",]) or (hasattr(self,'name') and self.name in ["Upload",]):
            parser_classes=[MultiPartParser]
        else:
            parser_classes = [JSONParser]
        
        return [parser() for parser in parser_classes]
    def get_response_schema(action):
        # response_schema_dict
        responses = {}
        rsd = {
            "200":
            UserInfoSerializer,
            "201":
            UserSerializer,
            "204":
            openapi.Response({}),
            "400":
            openapi.Response(
                description="Bad request",
                schema=SampleResponseSerializer,
                examples={
                    "application/json": {
                        "807": {
                            "status": "failed",
                            "code": 807,
                            "message": "validation error",
                            "detail": "System default error.",
                        },
                        "813": {
                                "status": "failed",
                                "code": 813,
                                "message": "validation error",
                                "detail": "Set the primary key.",
                        },  
                    }
                },
            ),
            "403":
            openapi.Response(
                description="Forbidden",
                schema=SampleResponseSerializer,
                examples={
                    "application/json": {
                        "821": {
                            "status":
                            "failed",
                            "code":
                            821,
                            "message":
                            _("validation error"),
                            "detail":
                            _("You do not have permission to perform this action."
                              ),
                            "data": {},
                        },
                    }
                },
            ),
            "848":
            openapi.Response(
                description="Forbidden",
                schema=SampleResponseSerializer,
                examples={
                    "application/json": {
                        "848": {
                            "status":"failed",
                            "code": 848,
                            "message": _("validation error"),
                            "detail": _("You do not have access to delete your role."),
                            "data": {},
                        },
                    }
                },
            ),
            "404":
            openapi.Response(
                description="Not found",
                schema=SampleResponseSerializer,
                examples={
                    "application/json": {
                        "820": {
                            "status": "failed",
                            "code": 820,
                            "message": "not found",
                            "detail": "This primary key not found",
                        },
                    }
                },
            ),
            "819":
            openapi.Response(
                description="Not found",
                schema=SampleResponseSerializer,
                examples={
                    "application/json": {
                        "819": {
                            "status": "failed",
                            "code": 819,
                            "message": "not found",
                            "detail": "Primary keys list is empty.",
                        },
                    }
                },
            ),
            "800":
            openapi.Response(
                description="Bad request",
                schema=SampleResponseSerializer,
                examples={
                    "application/json": {
                        "800": {
                            "status": "failed",
                            "code": 800,
                            "message": "unknown error",
                            "detail": "Unknown error.",
                        },
                    }
                },
            ),
            "807":
                openapi.Response(
                    description="Bad request",
                    schema=SampleResponseSerializer,
                    examples={
                        "application/json": {
                            "807": {
                                "status": "failed",
                                "code": 807,
                                "message": "validation error",
                                "detail": "System default error.",
                            },
                        }
                    },
            ),
            "813":
            openapi.Response(
                description="Bad request",
                schema=SampleResponseSerializer,
                examples={
                    "application/json": {
                        "813": {
                            "status": "failed",
                            "code": 813,
                            "message": "validation error",
                            "detail": "Set the primary key.",
                        },
                    }
                },
            ),
            "852":
            openapi.Response(
                description="Bad request",
                schema=SampleResponseSerializer,
                examples={
                    "application/json": {
                        "852": {
                            "status": "failed",
                            "code": 852,
                            "message": "runtime error",
                            "detail": "role error.",
                        },
                    }
                },
            ),
            "400_reg":
            openapi.Response(
                description="Bad request",
                schema=SampleResponseSerializer,
                examples={
                    "application/json": {
                        "807": {
                            "status": "failed",
                            "code": 807,
                            "message": "validation error",
                            "detail": "System default error.",
                        },
                        "809": {
                            "status": "failed",
                            "code": 809,
                            "message": "validation error",
                            "detail": "Email exist.",
                        },
                        "810": {
                            "status": "failed",
                            "code": 810,
                            "message": "validation error",
                            "detail": "Username exist.",
                        },
                        "811": {
                            "status": "failed",
                            "code": 811,
                            "message": "validation error",
                            "detail": "Username cannot les than 4 digit.",
                        },
                        "812": {
                            "status": "failed",
                            "code": 812,
                            "message": "validation error",
                            "detail": "password cannot les than 8 digit.",
                        },
                        "846": {
                            "status": "failed",
                            "code": 846,
                            "message": "validation error",
                            "detail": "Set the role.",
                        },
                        "852": {
                            "status": "failed",
                            "code": 852,
                            "message": "runtime error",
                            "detail": "role error.",
                        },
                    }
                },
            ),
            "400pk":
                openapi.Response(
                    description="Bad request",
                    schema=SampleResponseSerializer,
                    examples={
                        "application/json": {
                            "807": {
                                "status": "failed",
                                "code": 807,
                                "message": "validation error",
                                "detail": "System default error.",
                            },
                            "809": {
                                "status": "failed",
                                "code": 809,
                                "message": "validation error",
                                "detail": "Email exist.",
                            },
                            "810": {
                                "status": "failed",
                                "code": 810,
                                "message": "validation error",
                                "detail": "Username exist.",
                            },
                            "811": {
                                "status": "failed",
                                "code": 811,
                                "message": "validation error",
                                "detail": "Username cannot les than 4 digit.",
                            },
                            "812": {
                                "status": "failed",
                                "code": 812,
                                "message": "validation error",
                                "detail": "password cannot les than 8 digit.",
                            },
                            "813": {
                                "status": "failed",
                                "code": 813,
                                "message": "validation error",
                                "detail": "Set the primary key.",
                            },
                            "852": {
                                "status": "failed",
                                "code": 852,
                                "message": "runtime error",
                                "detail": "role error.",
                            },
                        }
                    },
            ),
            "400_forget":
            openapi.Response(
                description="Bad request",
                schema=SampleResponseSerializer,
                examples={
                    "application/json": {
                        "807": {
                            "status": "failed",
                            "code": 807,
                            "message": "validation error",
                            "detail": "System default error.",
                        },
                        "830": {
                                "status": "failed",
                                "code": 830,
                                "message": "validation error",
                                "detail": "Error at encoding of Security Question.",
                        }, 
                        "831": {
                                "status": "failed",
                                "code": 831,
                                "message": "validation error",
                                "detail": "Error at encoding of username and Security Question.",
                        }, 
                    }
                },
            ),
            "400_reset":
            openapi.Response(
                description="Bad request",
                schema=SampleResponseSerializer,
                examples={
                    "application/json": {
                        "807": {
                            "status": "failed",
                            "code": 807,
                            "message": "validation error",
                            "detail": "System default error.",
                        },
                        "850": {
                                "status": "failed",
                                "code": 850,
                                "message": "validation error",
                                "detail": "Token is invalid.",
                        },
                    }
                },
            ),
            
            "400_status":
            openapi.Response(
                description="Bad request",
                schema=SampleResponseSerializer,
                examples={
                    "application/json": {
                        "807": {
                            "status": "failed",
                            "code": 807,
                            "message": "validation error",
                            "detail": "System default error.",
                        },
                        "827": {
                                "status": "failed",
                                "code": 827,
                                "message": "validation error",
                                "detail": "Status field is Invalid.",
                        },
                    }
                },
            ),
            "400_role":
            openapi.Response(
                description="Bad request",
                schema=SampleResponseSerializer,
                examples={
                    "application/json": {
                        "813": {
                            "status": "failed",
                            "code": 813,
                            "message": "validation error",
                            "detail": "Set the primary key.",
                        },
                        "846": {
                            "status": "failed",
                            "code": 846,
                            "message": "validation error",
                            "detail": "Set the role.",
                        },
                    }
                },
            ),
            "404_multi":
            openapi.Response(
                description="Not found",
                schema=SampleResponseSerializer,
                examples={
                    "application/json": {
                        "811": {
                            "status": "failed",
                            "code": 845,
                            "message": "not found",
                            "detail": "Some users are not in the system.",
                        },
                        "819": {
                            "status": "failed",
                            "code": 819,
                            "message": "not found",
                            "detail": "Primary keys list is empty.",
                        },
                    }
                },
            ),
            "404_role":
            openapi.Response(
                description="Not found",
                schema=SampleResponseSerializer,
                examples={
                    "application/json": {
                        "820": {
                            "status": "failed",
                            "code": 820,
                            "message": "not found",
                            "detail": "This primary key not found",
                        },
                        "847": {
                            "status": "failed",
                            "code": 847,
                            "message": "not found",
                            "detail": "This role not found",
                        },
                    }
                },
            ),

            "200_forget":
            SampleForgetPasswordResponseSerializer,
            "sample":
            SampleResponseSerializer,
            "200_some":
            SampleSomeVirResponseSerializer,
            "200_OK":
            openapi.Response({}),
        }
        responses = dict()
        if action == "create":
            responses = {"201": rsd["201"], "400": rsd["400_reg"]}
        elif action == "retrieve":
            responses = {"200": rsd["200"],"400": rsd["813"],"404": rsd["404"]}
        elif action == "update":
            responses = {"200": rsd["200"],"400": rsd["400pk"],"404": rsd["404"]}
        elif action == "delete":
            responses = {"204": rsd["204"],"400": rsd["813"],"403": rsd["403"],"404": rsd["404"]}
        elif action in ["upload","join_to_asset","add_role"]:
            responses = {"200": rsd["200"], "400": rsd["400"],"404": rsd["404"]}
        
        elif action == "activated":
            responses = {"200": rsd["200"], "400": rsd["816"]}
        elif action == "reactive":
            responses = {"200": rsd["sample"], "400": rsd["816"]}
        
        elif action == "forgotpassword":
            responses = {"200": rsd["200_forget"], "400": rsd["400_forget"]}
        elif action == "resetpassword":
            responses = {"200": rsd["sample"], "400": rsd["400_reset"]}
        elif action == "some":
            responses = {"200": rsd["200_some"], "204": rsd["204"], "400": rsd["807"],"404": rsd["404_multi"]}
        elif action == "status":
            responses = {"200": rsd["200_OK"], "400": rsd["400_status"],"404": rsd["404_multi"]}
        elif action == "recycle":
            responses = {"200": rsd["200_OK"], "400": rsd["813"],"403": rsd["403"],"404": rsd["404"]}
        elif action == "delete_role":
            responses = {"204": rsd["204"], "400": rsd["400_role"],"403": rsd["848"],"404": rsd["404_role"]}

        return responses
    def get_serializer_class(self):
        if self.action in ['list', 'retrieve', 'me','trash']:
            return UserInfoSerializer
        elif self.action == "partial_update":
            return UserUpdateSerializer
        elif self.action == "resend":
            return UserResendPasswordSerializer
        elif self.action == "upload":
            return UserUploadSerializer
        elif self.action == 'status':
            return UserStatusSerializer
        elif self.action in ['some', 'recycle']:
            return NoneSerializer
        elif self.action in ['add_role','delete_role']:
            return UserRoleInSerializer
        else:
            return UserSerializer
    def get_permissions(self):
        if self.action in ['resend',]:
            permission_classes = [AllowAny,]
        else:
            permission_classes = [IsAuthenticated,]

        return [permission() for permission in permission_classes]
    def get_queryset(self):
        queryset = self.queryset
        _user = self.request.user
        role_list = get_user_roles(_user)
        queryset = queryset.annotate(name=Concat(F("first_name"),V(" "),F("last_name"),output_field=CharField(), ))
        if not _user.pk:
            return queryset.filter(pk=-1)
        elif _user.is_superuser:
            queryset = queryset
        elif 'client' in role_list:
            queryset = queryset.filter(pk=_user.pk)
        else:
            queryset = queryset.filter(company=_user.company)
        return queryset
    def filter_queryset(self, queryset,status=None):
        _filter = {}

        if 'search' in self.request.query_params and self.request.query_params['search']:
            _search = self.request.query_params['search']
            _filter.update({'name__icontains': _search})
        if status:
            _filter.update({'status': status})
        elif 'status' in self.request.query_params and self.request.query_params['status']:
            _status = get_dict_data(self.request.GET).get('status',None)
            if type(_status) != type([]):
                _status = [_status,]
            _filter.update({'status__in': _status})
        else:
            _filter.update({'status__in': [1, 0]})
        queryset = queryset.filter(**_filter).distinct()

        return queryset
    def get_object(self, pk=None):
        if pk:
            try:
                _object = self.get_queryset().get(pk=pk)
                return _object
            except ObjectDoesNotExist:
                pass
    def get_object_trash(self, pk=None):
        if pk:
            try:
                _object = self.get_queryset().get(pk=pk,status=-1)
                return _object
            except ObjectDoesNotExist:
                pass   

    
    @action(detail=False, methods=['get'])
    def me(self, request):
        _user = request.user
        if _user:
            _serializer = self.get_serializer(instance=_user)
            return Response(_serializer.data)
        return Response(status=status.HTTP_400_BAD_REQUEST)


    @swagger_auto_schema(query_serializer=UserFilterQuerySerializer)
    def list(self, request):
        """
        get list of User API.

        ---

        """
        _queryset = self.get_queryset()
        _queryset = _queryset.filter(is_superuser=False)
        _queryset = self.filter_queryset(queryset=_queryset).order_by('id')
        _count = _queryset.count()
        if _count == 0:
            return Response(status=status.HTTP_204_NO_CONTENT)

        _queryset, _total_page_num = get_response_data(request, _queryset)
        _serializer = self.get_serializer(_queryset, many=True)
        return Response({
                    'list': _serializer.data,
                    'total_page_num': _total_page_num,
                    'total_row': _count
                })


    # @swagger_auto_schema(responses=get_response_schema('create'))
    # @transaction.atomic
    def create_hidden(self, request):
        """
        create for user API.
        ---
            role : ['client']
        """
        _data = get_dict_data(request.data)
        _serializer = self.get_serializer(context={'request': request},data=_data)
        if _serializer.is_valid():
            new_object = _serializer.save()
            _serializer = UserInfoSerializer(instance=new_object)
            return Response(_serializer.data, status=status.HTTP_201_CREATED)
        else:
            raise ProjectException(807, 
                            _('validation error'),_serializer.errors,
                            status.HTTP_400_BAD_REQUEST)


    @swagger_auto_schema(responses=get_response_schema('retrieve'))
    def retrieve(self, request, pk=None):
        """
        get a User API.

        ---

        """
        if pk:
            _object = self.get_object(pk)
            if _object and (_object.status in [0,1]):
                _serializer = self.get_serializer(instance=_object)
                return Response(_serializer.data)
            else:
                raise ProjectException(820, _('not found'),
                                       _('This primary key not found.'),
                                       status.HTTP_404_NOT_FOUND)
        else:
            raise ProjectException(813, _('validation error'),
                                   _('Set the primary key.'),
                                   status.HTTP_400_BAD_REQUEST)


    # @execute_with_permission('user', 'update')
    @swagger_auto_schema(responses=get_response_schema('update'))
    @transaction.atomic
    def partial_update(self, request, pk=None):
        """
        update a User partial API.

        ---
            birth_day : "1400/01/01"
        """
        if pk:
            _object = self.get_object(pk)
            if _object and (_object.status in [0,1]):
                _data = get_dict_data(request.data)
                _serializer = self.get_serializer(context={'request': request},
                                                  instance=_object,data=_data,partial=True)
                if _serializer.is_valid():
                    _object = _serializer.save()
                    _serializer = UserInfoSerializer(instance=_object)
                    return Response(_serializer.data)
                else:
                    raise ProjectException(807, _('validation error'),
                                           _serializer.errors,
                                           status.HTTP_400_BAD_REQUEST)
            else:
                raise ProjectException(820, _('not found'),
                                       _('This primary key not found.'),
                                       status.HTTP_404_NOT_FOUND)
        else:
            raise ProjectException(813, _('validation error'),
                                   _('Set the primary key.'),
                                   status.HTTP_400_BAD_REQUEST)


    # @execute_with_permission('user', 'delete')
    @swagger_auto_schema(responses=get_response_schema('delete'))
    @transaction.atomic
    def destroy(self, request, pk=None):
        """
        delete a User  API.

        ---

        """
        _user = request.user
        if pk:
            if pk != _user.pk:
                _object = self.get_object(pk)
                if _object:
                    if _object.status == -1:
                        _object.delete()
                    else:
                        _object.status = -1
                        _object.is_active = False
                        _object.save()
                    return Response(status=status.HTTP_204_NO_CONTENT)
                else:
                    raise ProjectException(820, _('not found'),
                                        _('This primary key not found.'),
                                        status.HTTP_404_NOT_FOUND)
            else:
                raise ProjectException(821, _('Forbidden'),
                                        _('You do not have permission to perform this action.'),
                                        status.HTTP_403_FORBIDDEN)
        else:
            raise ProjectException(813, _('validation error'),
                                   _('Set the primary key.'),
                                   status.HTTP_400_BAD_REQUEST)


    # @execute_with_permission('user', 'update')
    @swagger_auto_schema(responses=get_response_schema('upload'))
    @action(detail=True,methods=["patch"],parser_classes=(MultiPartParser, ),)
    @transaction.atomic
    def upload(self, request, pk=None):
        """
        upload avatar field for user API.
        ---

        """
        if pk:
            _object = self.get_object(pk)
            if _object and (_object.status in [0,1]):
                _data = get_dict_data(request.data)
                _serializer = self.get_serializer(context={"request": request},
                        instance=_object,data=_data,partial=True,
                    )
                if _serializer.is_valid():
                    _object = _serializer.save()
                    _serializer = UserInfoSerializer(instance=_object)
                    return Response(_serializer.data,
                                    status=status.HTTP_200_OK)
                else:
                    raise ProjectException(807, _('validation error'),
                                           _serializer.errors,
                                           status.HTTP_400_BAD_REQUEST)
            else:
                raise ProjectException(820, _('not found'),
                                       _('This primary key not found.'),
                                       status.HTTP_404_NOT_FOUND)
        else:
            raise ProjectException(813, _('validation error'),
                                   _('Set the primary key.'),
                                   status.HTTP_400_BAD_REQUEST)


    @transaction.atomic
    @swagger_auto_schema(responses=get_response_schema("resend"))
    @action(detail=False, methods=["post"],url_path='resend_verification_code')
    def resend(self, request):
        """
        resend verification code to user.

        ---

        """
        _serializer = self.get_serializer(context={"request": request}, data=request.data)
        if _serializer.is_valid():
            _serializer.save()
            return Response(status=status.HTTP_200_OK)
        else:
            raise ProjectException(807,_("validation error"),_serializer.errors,
                                status.HTTP_400_BAD_REQUEST,
                            )


    # @execute_with_permission_multi_id('user', 'delete')
    @swagger_auto_schema(
        method='delete',
        request_body=openapi.Schema(type=openapi.TYPE_OBJECT,
                                properties={'id':openapi.Schema(type=openapi.TYPE_ARRAY,
                                items=openapi.Items(type=openapi.TYPE_INTEGER),
                                description='A list of primary keys'),
                            }),
                            responses=get_response_schema('some')
                    )
    @action(detail=False, methods=['delete'])
    @transaction.atomic
    def some(self, request):
        """
        delete some User API.

        ---

        """
        _user = request.user
        _data = get_dict_data(request.data)
        _ids = _data['id']
        if type(_ids) == type([]):
            _serializer = UserSomeSerializer(context={"request": request},data=_data,)
            if _serializer.is_valid():
                valid_data = _serializer.validated_data
                _queryset = valid_data['id']
                _id_in = [obj.pk for obj in _queryset]
                _queryset = self.queryset.filter(pk__in=_id_in)
                if _queryset:
                    _deletes = []
                    _v_deletes = []
                    _count = 0
                    _v_count = 0
                    for _obj in _queryset:
                        if _obj.pk == _user.pk:
                            raise ProjectException(821, _('Forbidden'),
                                                    _('You do not have permission to perform this action.'),
                                                    status.HTTP_403_FORBIDDEN)
                        if _obj.status == -1:
                            _count += 1
                            _deletes.append({str(_obj.id): _('deleted')})
                            _v_deletes.append(
                                {str(_obj.id): _('deletion is not possible')})
                        else:
                            _v_count += 1
                            _v_deletes.append({str(_obj.id): _('virtual deleted')})
                            _deletes.append(
                                {str(_obj.id): _('virtual deletion is not possible')})

                    if _deletes or _v_deletes:
                        if _count == 0 or _v_count == 0:
                            if _count > 0:
                                _queryset.delete()
                                return Response(_deletes,
                                                status=status.HTTP_204_NO_CONTENT)
                            elif _v_count > 0:
                                for _obj in _queryset:
                                    _obj.status = -1
                                    _obj.is_active = False
                                    _obj.save()
                                return Response(_v_deletes, status=status.HTTP_200_OK)

                        return Response(
                            {
                                'deletes': _deletes,
                                'virtual_delete': _v_deletes
                            },
                            status=status.HTTP_400_BAD_REQUEST)
                else:
                    raise ProjectException(819, _('not found error'),
                                        _('Primary keys list is empty.'),
                                        status.HTTP_404_NOT_FOUND)
            else:
                raise ProjectException(807, _('validation error'),
                                        _serializer.errors,
                                        status.HTTP_400_BAD_REQUEST)
        else:
            raise ProjectException(807, _('validation error'),
                                        _("id:[Expected a list of items but got type.]"),
                                        status.HTTP_400_BAD_REQUEST)


    # @execute_with_permission_multi_id('user', 'status')
    @swagger_auto_schema(responses=get_response_schema('status'))
    @action(detail=False, methods=['patch'])
    @transaction.atomic
    def status(self, request):
        """
        change status some Users  API.

        ---

        """
        _user = request.user
        _data = get_dict_data(request.data)
        _serializer = self.get_serializer(context={"request": request},data=_data,)
        if _serializer.is_valid():
            valid_data = _serializer.validated_data
            _users = valid_data['id']
            _status = valid_data['status']
            if _users and (_status is not None):
                for obj in _users:
                    if obj.pk == _user.pk:
                        raise ProjectException(821, _('Forbidden'),
                                                _('You do not have permission to perform this action.'),
                                                status.HTTP_403_FORBIDDEN)
                    obj.status = _status
                    if _status == -1:
                        obj.is_active = False
                    elif _status == 1:
                        obj.is_active = True
                self.queryset.bulk_update(_users, ['status','is_active'])
                return Response(status=status.HTTP_200_OK)
            else:
                raise ProjectException(819, _('not found error'),
                                    _('Primary keys list is empty.'),
                                    status.HTTP_404_NOT_FOUND)
        else:
            raise ProjectException(807, _('validation error'),
                                    _serializer.errors,
                                    status.HTTP_400_BAD_REQUEST)


    @swagger_auto_schema(query_serializer=UserTrashFilterQuerySerializer)
    @action(detail=False, methods=['get'])
    def trash(self, request):
        """
        get list of deleted Users API.

        ---
        status=(-1,'trash'),(0,'unpublish'),(1,'publish')

        """
        _queryset = self.get_queryset()
        _queryset = self.filter_queryset(queryset=_queryset,status=-1).order_by('id')
        _count = _queryset.count()
        if _count == 0:
            return Response(status=status.HTTP_204_NO_CONTENT)

        _queryset, _total_page_num = get_response_data(request, _queryset)
        _serializer = self.get_serializer(_queryset, many=True)
        return Response({
            'list': _serializer.data,
            'total_page_num': _total_page_num,
            'total_row': _count
        })


    # @execute_with_permission('user', 'recycle')
    @action(detail=True, methods=['patch'])
    @transaction.atomic
    def recycle(self, request, pk=None):
        """
        recycle a User API.

        ---

        """
        _user = request.user
        if pk:
            if pk != _user.pk:
                _object = self.get_object(pk)
                if _object and _object.status == -1:
                    _object.status = 1
                    _object.is_active = True
                    _object.save()
                    return Response(status=status.HTTP_200_OK)
                else:
                    raise ProjectException(820, _('not found'),_('This primary key not found.'),
                                        status.HTTP_404_NOT_FOUND)
            else:
                raise ProjectException(821, _('Forbidden'),_('You do not have permission to perform this action.'),status.HTTP_403_FORBIDDEN)
        else:
            raise ProjectException(813, _('validation error'),_('Set the primary key.'),status.HTTP_400_BAD_REQUEST)


    # @swagger_auto_schema(responses=get_response_schema("add_role"))
    @action(detail=True,methods=["post"],url_path='role')
    @transaction.atomic
    def add_role(self, request,pk=None):
        """
        add role API
        role : ['client','admin']
        """
        if pk:
            _object = self.get_object(pk)
            if _object:
                _data = get_dict_data(request.data)
                _data['user'] = _object.pk
                _serializer = UserRoleSerializer(context={"request": request},data=_data,partial=True,)
                if _serializer.is_valid():
                    _serializer.save()
                    new_object = self.get_object(pk)
                    _serializer = UserInfoSerializer(instance=new_object)
                    return Response(_serializer.data, status=status.HTTP_200_OK)
                else:
                    raise ProjectException(
                            807,
                            _("validation error"),
                            _serializer.errors,
                            status.HTTP_400_BAD_REQUEST,
                        )
            else:
                raise ProjectException(
                    820,
                    _("not found"),
                    _("This primary key not found."),
                    status.HTTP_404_NOT_FOUND,
                )
        else:
            raise ProjectException(
                813,
                _("validation error"),
                _("Set the primary key."),
                status.HTTP_400_BAD_REQUEST,
            )


    # @swagger_auto_schema(responses=get_response_schema("delete_role"))
    @action(detail=True,methods=["delete"],url_path='role/(?P<role>[\w\-]+)')
    @transaction.atomic
    def delete_role(self, request, pk=None, role=None):
        """
        delete a role API.

        """
        _user = request.user
        if pk:
            _object = self.get_object(pk)
            if _object:
                if _object != _user:
                    if role:
                        try:
                            user_role = UserRoleModel.objects.get(user=_object,role__pk=role)
                            user_role.delete()
                            return Response(status=status.HTTP_204_NO_CONTENT)
                        except:
                            raise ProjectException(
                                    847,
                                    _("not found"),
                                    _("This role not found."),
                                    status.HTTP_404_NOT_FOUND,
                                )
                    else:
                        raise ProjectException(
                                846,
                                _("validation error"),
                                _("Set the role."),
                                status.HTTP_400_BAD_REQUEST,
                            )
                else:
                    raise ProjectException(
                            848,
                            _("Forbidden"),
                            _("You do not have access to delete your role"),
                            status.HTTP_403_FORBIDDEN,
                        )
            else:
                raise ProjectException(
                        820,
                        _("not found"),
                        _("This primary key not found"),
                        status.HTTP_404_NOT_FOUND,
                    )
        else:
            raise ProjectException(
                813,
                _("validation error"),
                _("Set the primary key."),
                status.HTTP_400_BAD_REQUEST,
            )


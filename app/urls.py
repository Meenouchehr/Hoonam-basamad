from django.urls import path,include
from rest_framework import urlpatterns
from rest_framework.routers import DefaultRouter

from app.viewsets import *

# Create a router and register our viewsets with it.
router = DefaultRouter()

router.register(r'account',AccountViewSet)
router.register(r'',DefaultViewSet)
# router.register(r'license',LicenseViewSet)

router.register(r'company',CompanyViewSet) # company/home
router.register(r'service',ServiceViewSet)
router.register(r'store',StoreViewSet) 
router.register(r'gallery',GalleryViewSet)
router.register(r'import',ImportViewSet)
router.register(r'mellat',MellatViewSet) 

router.register(r'user',UserViewSet) # user/home
# router.register(r'user/evidence',UserEvidenceViewSet) # user/evidence
# router.register(r'user/vacation',VacationViewSet) # user/vacation
# router.register(r'user/mission',MissionViewSet) # user/mission
# router.register(r'user/worktime',WorkTimeViewSet) # user/worktime 
# router.register(r'user/salary',SalaryViewSet) # user/salary 

urlpatterns = [
    path('',include(router.urls)),
]
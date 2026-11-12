import requests,json




def Login(username, password):
    url = 'https://www.saheam.ir/webapi/account/login/'
    myobj = {'Username': username, 'Password': password}
    headers = {'Content-type': 'application/json'}
    res = requests.post(url, json=myobj, headers=headers)
    text=res.text
    try:
        text= json.loads(res.text)
    except:
        pass
    return {'result': text, 'status': res.status_code}

def GetAccessibleClubs(self):     
    url = 'https://www.saheam.ir/webapi/clubservices/v2/GetAccessibleClubs/' 
    _token = get_mellat_token()
    while _token:
        headers = {'Content-type': 'application/json','Authorization': _token}
        res = requests.get(url,params={},headers=headers)
        text=res.text
        try:
            text= json.loads(res.text)                  
        except:
            pass
        
        if res.status_code == 401:
                delete_mellat_token()
                _token = get_mellat_token()
                continue         
        return {'result': text, 'status': res.status_code}
        
    return {'result': 'unkown error', 'status': 400}

def AddOrUpdate( national_code, mobile_no=None, name=None, family=None,new_national_code=None):    
    url = 'https://www.saheam.ir/webapi/clubservices/v2/AddOrUpdateMember/'
    _token = get_mellat_token()
    while _token:
        myobj = {'NationalCode': national_code}
        if mobile_no:
            myobj.update({'MobileNo': int(mobile_no)})
        if name:
            myobj.update({'Name': name})
        if family:
            myobj.update({'Family': family})
        if new_national_code:
            myobj.update({'NewNationalCode': new_national_code})

        headers = {'Content-type': 'application/json',
                'Authorization': _token}
        print(myobj)
        res = requests.post(url, json=myobj, headers=headers)
        
        text=res.text
        try:
            text= json.loads(res.text)
        except:
            pass
        if res.status_code == 401:
                delete_mellat_token()
                _token = get_mellat_token()
                continue           
        return {'result': text, 'status': res.status_code}
        
    return {'result': 'unkown error', 'status': 400}

def AddBatchMemberShip(memberships_info,clube_id):
    url = 'https://www.saheam.ir/webapi/clubservices/v2/AddBatchMemberShip/'
    _token = get_mellat_token()
    while _token:
        myobj = {"MembershipsInfo": memberships_info}
        
        headers = {'Content-type': 'application/json',
                'Authorization': _token}
        
        res = requests.post(url, json=myobj, headers=headers)
        
        text=res.text
        try:
            text= json.loads(res.text)
        except:
            pass
        if res.status_code == 401:
                delete_mellat_token()
                _token = get_mellat_token()
                continue           
        return {'result': text, 'status': res.status_code}
        
    return {'result': 'unkown error', 'status': 400}

def GetMemberInfo(national_code):
    url = 'https://www.saheam.ir/webapi/clubservices/v2/GetMemberInfo/'
    _token = get_mellat_token()
    while _token:
        headers = {'Content-type': 'application/json','Authorization': _token}
        myobj = {'NationalCode':national_code,}
        res = requests.get(url, params=myobj, headers=headers)
        text=res.text
        try:
            text= json.loads(res.text)
        except:
            pass
        if res.status_code == 401:
                delete_mellat_token()
                _token = get_mellat_token()
                continue           
        return {'result': text, 'status': res.status_code}
        
    return {'result': 'unkown error', 'status': 400}

def RemoveMember( national_code):
    url = 'https://www.saheam.ir/webapi/clubservices/v2/RemoveMember/'
    _token = get_mellat_token()
    while _token:
        myobj = {'NationalCode': national_code}
        
        headers = {'Content-type': 'application/json',
                'Authorization': _token}
        print(myobj)
        res = requests.post(url, json=myobj, headers=headers)
        
        text=res.text
        try:
            text= json.loads(res.text)
        except:
            pass
            
        if res.status_code == 401:
                delete_mellat_token()
                _token = get_mellat_token()
                continue           
        return {'result': text, 'status': res.status_code}
        
    return {'result': 'unkown error', 'status': 400}

def ListMembershipChanges(row_change_pointer):
    url = 'https://www.saheam.ir/webapi/clubservices/v2/ListMembershipChanges/'
    _token = get_mellat_token()
    while _token:
        headers = {'Content-type': 'application/json','Authorization': _token}
        myobj = {'RowChangePointer': row_change_pointer}
        res = requests.get(url,params=myobj,headers=headers)
        text=res.text
        try:
            text= json.loads(res.text)
        except:
            pass
        if res.status_code == 401:
                delete_mellat_token()
                _token = get_mellat_token()
                continue           
        return {'result': text, 'status': res.status_code}
        
    return {'result': 'unkown error', 'status': 400}

def AddMemberCard(national_code,cards):
    url = 'https://www.saheam.ir/webapi/clubservices/v2/AddMemberCard/'
    _token = get_mellat_token()
    while _token:
        _cards = json.dumps(cards)
        myobj = {'NationalCode': national_code, 'Pans': cards}
    
        headers = {'Content-type': 'application/json','Authorization': _token}
        res = requests.post(url, json=myobj, headers=headers)
        text=res.text
        try:
            text= json.loads(res.text)
        except:
            pass
        if res.status_code == 401:
                delete_mellat_token()
                _token = get_mellat_token()
                continue           
        return {'result': text, 'status': res.status_code}
        
    return {'result': 'unkown error', 'status': 400}

def IsPanRegistered(pan):
    url = 'https://www.saheam.ir/webapi/clubservices/v2/IsPanRegistered/'
    _token = get_mellat_token()
    while _token:
        headers = {'Content-type': 'application/json','Authorization': _token}
        myobj = {'Pan':pan,}
        res = requests.get(url, params=myobj, headers=headers)
        text=res.text
        try:
            text= json.loads(res.text)
        except:
            pass
        if res.status_code == 401:
                delete_mellat_token()
                _token = get_mellat_token()
                continue           
        return {'result': text, 'status': res.status_code}
        
    return {'result': 'unkown error', 'status': 400}

def GetCardType():
    url = 'https://www.saheam.ir/webapi/clubservices/v2/GetCardType/'
    _token = get_mellat_token()
    while _token:
        headers = {'Content-type': 'application/json','Authorization': _token}
        res = requests.get(url,params={},headers=headers)
        text=res.text
        try:
            text= json.loads(res.text)
        except:
            pass
        if res.status_code == 401:
                delete_mellat_token()
                _token = get_mellat_token()
                continue           
        return {'result': text, 'status': res.status_code}
        
    return {'result': 'unkown error', 'status': 400}

def RemoveMemberCard(national_code,cards):
    url = 'https://www.saheam.ir/webapi/clubservices/v2/RemoveMemberCard/'
    _token = get_mellat_token()
    while _token:
        _cards = json.dumps(cards)
        myobj = {'NationalCode': national_code, 'Pans': cards}
    
        headers = {'Content-type': 'application/json','Authorization': _token}
        res = requests.post(url, json=myobj, headers=headers)
        text=res.text
        try:
            text= json.loads(res.text)
        except:
            pass
        if res.status_code == 401:
                delete_mellat_token()
                _token = get_mellat_token()
                continue           
        return {'result': text, 'status': res.status_code}
        
    return {'result': 'unkown error', 'status': 400}

def AssignPackageToMember(national_code,package_id,start_date,end_date,generate_new_code):
    from datetime import datetime
    import jdatetime
    url = 'https://www.saheam.ir/webapi/clubservices/v2/AssignPackageToMember/'
    _token = get_mellat_token()
    while _token:
        if len(start_date)==8:
            _year=int(start_date[0:4])
            _month=int(start_date[4:6])
            _day=int(start_date[6:8])
            _start_date = jdatetime.date(_year, _month, _day).togregorian()
        
        if len(end_date)==8:
            _year=int(end_date[0:4])
            _month=int(end_date[4:6])
            _day=int(end_date[6:8])
            _end_date = jdatetime.date(_year, _month, _day).togregorian()
            
        _start_date=_start_date.__str__()
        _end_date=_end_date.__str__()
        headers = {'Content-type': 'application/json','Authorization': _token}
        myobj = {'NationalCode':national_code,"PackageId":package_id,'StartDate':_start_date,'EndDate':_end_date,'GenerateNewCode':generate_new_code}
        res = requests.post(url, json=myobj, headers=headers)
        text=res.text
        try:
            text= json.loads(res.text)
        except:
            pass
        if res.status_code == 401:
                delete_mellat_token()
                _token = get_mellat_token()
                continue           
        return {'result': text, 'status': res.status_code}
        
    return {'result': 'unkown error', 'status': 400}

def GetDiscountDetail(terminal_id,pan,date,clubId=None):
    from datetime import datetime
    import jdatetime
    url = 'https://www.saheam.ir/webapi/Discount/Inquiry'
    _token = get_mellat_token()
    while _token:
        if len(date)==8:
            _year=int(date[0:4])
            _month=int(date[4:6])
            _day=int(date[6:8])
            _date = jdatetime.date(_year, _month, _day).togregorian()
        _params={'TerminalID':terminal_id,'Pan':pan,'Date':_date}
        headers = {'Content-type': 'application/json','Authorization': _token}
        res = requests.get(url,params=_params,headers=headers)
        text=res.text
        try:
            text= json.loads(res.text)
        except:
            pass
        if res.status_code == 401:
                delete_mellat_token()
                _token = get_mellat_token()
                continue           
        return {'result': text, 'status': res.status_code}
        
    return {'result': 'unkown error', 'status': 400}

def GetAllPackages():
    url = 'https://www.saheam.ir/webapi/clubservices/v2/GetAllPackages/'     
    _token=get_mellat_token()
    while _token:
        headers = {'Content-type': 'application/json','Authorization': _token}
        res = requests.get(url,params={},headers=headers)
        text=res.text
        try:
            text= json.loads(res.text)
        except:
            pass
        if res.status_code == 401:
                delete_mellat_token()
                _token = get_mellat_token()
                continue           
        return {'result': text, 'status': res.status_code}

    return {'result': 'unkown error', 'status': 400}

def GetTransactions(last_transactions_row):
    url = 'https://www.saheam.ir/webapi/clubservices/v2/GetTransactions/'
    _token = get_mellat_token()
    while _token: 
        headers = {'Content-type': 'application/json','Authorization': _token}
        res = requests.get(url,params={'LastTransactionsRow':last_transactions_row},headers=headers)
        text=res.text
        try:
            text= json.loads(res.text)
        except:
            pass
        if res.status_code == 401:
                delete_mellat_token()
                _token = get_mellat_token()
                continue           
        return {'result': text, 'status': res.status_code}
        
    return {'result': 'unkown error', 'status': 400}

def get_mellat_token():
    from app.models import SettingModel
    from app.serializers import SettingSerializer
    from django.conf import settings
    _token=None
    try:
        _setting = SettingModel.objects.get(key='mellat_token')
        _token = _setting.value
    except SettingModel.DoesNotExist:
        _username = ""
        _password = ""
        try:
            _username = settings.MELLAT_USERNAME
            try:
                _password = settings.MELLAT_PASSWORD
                _login = Login(_username, _password)
                if _login['status'] == 200:
                    _result = _login['result']
                    if 'jwtToken' in _result:
                        _token = ''.join(['Bearer ',_result['jwtToken']])
                        if _token:
                            _data = {'key': 'mellat_token', 'value': _token}
                            _serializer = SettingSerializer(data=_data)
                            if _serializer.is_valid(raise_exception=True):
                                _serializer.save()                    
            except:
                pass
        except:
            pass                                   
    return _token

def delete_mellat_token():
    from app.models import SettingModel
    from app.serializers import SettingSerializer    
    try:
        _setting = SettingModel.objects.get(key='mellat_token')
        _setting.delete()
    except SettingModel.DoesNotExist:
        pass
    return True






from django.db.models import F,Q
# from celery.decorators import task
from datetime import datetime
from os import path
import jdatetime
from django.db import transaction
import pandas as pd
import numpy as np
import json

from app.serializers import *
from app.mellat import *

# @task(name='mellat_task')
@transaction.atomic
def mellat_task():
    _objects = AccountModel.objects.annotate(cellphone=F('owner__cellphone'),first_name=F('owner__first_name'),last_name=F('owner__last_name')).filter(mellat_status=1)
    _count = _objects.count()
    print(''.join(['insert : ',str(_count)]))
    if _count > 0:
        if _count > 500:
            _objects = _objects[:500]
        _items  = [{"Name":obj.first_name,"Family":obj.last_name,"MobileNo":int(obj.cellphone),"NationalCode":obj.national_code,"PansInfo":[{"Pan":obj.card_no,"Type":0}]} for obj in _objects if obj.cellphone]
        _items2 = [{"Name":obj.first_name,"Family":obj.last_name,"NationalCode":obj.national_code,"PansInfo":[{"Pan":obj.card_no,"Type":0}]} for obj in _objects if not obj.cellphone]
        for item in _items2:
            # Merge _items & _items2
            _items.append(item)
        
        _ids = [obj.id for obj in _objects]
        if _items:
            _res    = AddBatchMemberShip(memberships_info=_items,clube_id=None)
            _status = _res['status']
            if _status == 200:
                _result = _res['result']
                if _result['respCode'] == 0:
                    MellatAccountModel.objects.filter(account_id__in=_ids).update(mellat_status=0)
                else:
                    error_items = _result['membershipsRegistrationInfo']
                    for _item in error_items:
                        _card_no     = _item['pansInfo'][0]['pan']
                        _status_code = _item['statusCode']
                        _object = AccountModel.objects.get(card_no=_card_no)
                        # ma_object = MellatAccountModel.objects.get(account__card_no=_card_no)  
                        _object.mellat.mellat_status = 11
                        _object.mellat.mellat_date   = datetime.now()
                        _object.mellat.mellat_result = _status_code
                        _object.mellat.save()
                    # Change the mellat_status of items registered in the system
                    MellatAccountModel.objects.filter(account_id__in=_ids,mellat_status=1).update(mellat_status=0)


# @task(name='upload_file_task')
def upload_file_task():
    
    
    print('start task ...')
    _status = 'doing'
    _count = ImportModel.objects.filter(import_status=_status).count()
    print(''.join(['doing: ', str(_count)]))
    if _count == 0:
        _status = 'new'
        _count = ImportModel.objects.filter(import_status=_status).count()
        print(''.join(['new: ', str(_count)]))

    print(''.join([_status,':', str(_count)]))
    if _count:
        print("start operation ...")
        _object = ImportModel.objects.filter(import_status=_status).order_by('id').first()        
        _file   = _object.file.path
        print(''.join(['file : ',_file]))
        _import_id = _object.pk        
        _added     = _object.added
        _errors    = _object.errors
        _whole     = _object.whole
        _rows      = _object.rows
        _error_check    = _rows
        _import_company = _object.company
        _error_list = []

        print("start reading ...")
        try:
            #Sheet name:
            _xls = pd.ExcelFile(_file)
            _sheet_name = _xls.sheet_names[0]
            print(''.join(['sheet name : ',_sheet_name]))
            # Clean Data:
            df = pd.read_excel(_file) #'import.xlsx'
            print('file read ...')
            df.columns = df.columns.str.strip() #df = df.rename(columns=lambda x: x.strip())
            columns = df.columns
            df = df.rename(columns=lambda x: x.replace(' ', '')) # df.columns = df.columns.str.replace(' ', '')
            df = df.rename(columns={'نام' : 'first_name','نامخانوادگی':'last_name','کدملی':'national_code','تلفن':'cellphone','شمارهکارت':'card_no'})
            df['first_name'] = df['first_name'].astype(str)
            df['last_name'] = df['last_name'].astype(str)
            df  = df.replace(to_replace='nan', value='')
            df  = df.replace(to_replace=np.nan, value='')
            df['card_no'] = df['card_no'].astype(str)

            # df['cellphone']=np.where(df['cellphone'] == '', df['cellphone'], pd.to_numeric(df['cellphone'])) #int(df['cellphone'])
            # df['national_code']=np.where(df['national_code'] == '', df['national_code'], pd.to_numeric(df['national_code']))
            # Value 
            
            df['error'] = 0
            
            #Initialization:
            _whole = df.shape[0]
            _total = (_rows - 2) + 500
            if _total >= _whole:
                _total = _whole
            for index in range(_rows-2,_total):
                _is_compelete = False
                _error = ''
                row_data = dict(df.loc[index])
                _is_compelete,_error = add_member_with_account(data=row_data,company=_import_company)

                if _is_compelete:
                    _added = _added + 1
                else:
                    _errors = _errors + 1 
                    _error_list.append({'row':index+2,'error':_error})
                    df.loc[index,'error'] = 1
                    row_data.pop('error',None)
                    new_data={'Import':_object,'row_number':index+2,'data':row_data,'description':_error}
                    _object_exept = ImportExceptionModel(** new_data)
                    _object_exept.save()

            _rows = _total + 2                     
            print("end reading ...")
            print("start wiriting ...")
            _writer = pd.ExcelWriter(_file, engine='xlsxwriter')     
            _workbook = _writer.book               
            _worksheet = _workbook.add_worksheet(_sheet_name)
            _writer.sheets[_sheet_name] = _worksheet
            _correct_format = _workbook.add_format({                           
                    'text_wrap': True})
            _correct_format.set_align('center')
            _correct_format.set_align('vcenter')
            _error_format = _workbook.add_format({
                    'bg_color': 'red',  
                    'bold': True,         
                    'text_wrap': True,                           
                    'border': 1})
            _error_format.set_align('center')
            _error_format.set_align('vcenter')
            _col_format = _workbook.add_format({
                    'bg_color': '#FFCC99',  
                    'bold': True,         
                    'text_wrap': True,                           
                    'border': 2})
            _col_format.set_align('center')
            _col_format.set_align('vcenter')
            for col in range(len(columns)):
                _value = columns[col]
                _worksheet.write(0, col , _value,_col_format)
            for index in range(0,df.shape[0]):
                row = df.loc[index]
                if df.loc[index,'error']==1:
                    for col in range(len(row)-1):
                        _value = row[col]
                        if _value is np.nan:
                            _value = None
                        elif col in [2,3] and (_value != ''):
                            _value = str(int(_value))
                        _worksheet.write(index+1, col , _value,_error_format)
                else:
                    for col in range(len(row)-1):
                        _value = row[col]
                        if (_value is np.nan) or (type(_value)==type(np.float64())):
                            _value = None
                        elif col in [2,3] and (_value != ''):
                            _value = str(int(_value))
                        _worksheet.write(index+1, col , _value,_correct_format)
            _writer.save()
            print("end wiriting ...")

            _object = ImportModel.objects.get(pk=_import_id) 
            if (_rows-2) >= _whole:                        
                _object.import_status = 'done'
            else:
                _object.whole = _whole
                _object.import_status = 'doing'
    
    
            _object.added  = _added                
            _object.errors = _errors
            _object.rows   = _rows
            _object.import_date = datetime.now()
            _object.save()
        except Exception as err:
                    print(''.join(['error :',str(err)]))
        print("end operation ...")    
        
    print('end task ...!')    



def add_member_with_account(data,company=None):
    _first_name_cell    = data.get('first_name','')
    _last_name_cell     = data.get('last_name','')
    _cellphone_cell     = data.get('cellphone',None)
    _national_code_cell = data.get('national_code',None) 
    _card_no_cell       = data.get('card_no',None)  
    
    _owner = None
    if not validate_card(_card_no_cell):
            return (False,'card error')
    if _cellphone_cell:
        _cellphone_cell = cellphone_check(str(int(_cellphone_cell)))
        if not _cellphone_cell:
            return (False,'cellphone error')
        try:
            _owner = UserModel.objects.get(cellphone=_cellphone_cell)
        except:
            pass
    if _national_code_cell:
        _national_code_cell = national_code_check(str(int(_national_code_cell)))
        if not _national_code_cell:
            return (False,'national_code error')
        try:
            _owner = UserModel.objects.get(profile__national_code=_national_code_cell)
        except:
            pass
    try:
        # Add User:
        owner_data = {
                'first_name':_first_name_cell,
                'last_name':_last_name_cell,
                'cellphone':_cellphone_cell
            }
        if _owner:
            owner_data['national_code'] = _national_code_cell
            _serializer = UserUpdateSerializer(instance=_owner,data=owner_data,partial=True)
            if _serializer.is_valid():
                _serializer.save()
        else:
            # _name = "".join([_first_name_cell,_last_name_cell])
            _name = 'test'
            owner_data['username'] = generate_username(_name)
            owner_data['company'] = company
            _owner = UserModel(**owner_data)
            _password = str(get_verfication_code())
            if _password is not None:
                _owner.set_password(_password)
                _owner.verification_code = _password
            _owner.status = 1
            _owner.is_active  = False
            _owner.registered = False
            _owner.profile_data = {'national_code':_national_code_cell}
            _owner.save()
        # Add Account:
        account_data = {
                'card_no':_card_no_cell,
                'owner':_owner.pk
            }
        _serializer = AccountSerializer(data=account_data)
        if _serializer.is_valid():
            _serializer.save()
        return (True,'ok')
    except Exception as err:
        return (False,str(err))
def cellphone_check(cellphone):
    if validate_phone_number(cellphone):
        if len(cellphone)==11:
            if cellphone.startswith('0'):
                return cellphone        
        elif len(cellphone)>11:
            if cellphone.startswith('+98'):
                cellphone=cellphone.replace('+98','0')
                return cellphone_check(cellphone)
            elif cellphone.startswith('98'): 
                cellphone=cellphone.replace('98','0')
                return cellphone_check(cellphone)
                
        else:
            if not cellphone.startswith('0'):
                cellphone=''.join(['0',cellphone])
                return cellphone_check(cellphone)
    return None
def national_code_check(national_code):
    if len(national_code) == 10:
        if is_national_code_verify(national_code):
            return national_code
    elif len(national_code) == 8:
        national_code=''.join(['00',national_code])
        if is_national_code_verify(national_code):
            return national_code
    elif len(national_code) == 9:
        national_code=''.join(['0',national_code])
        if is_national_code_verify(national_code):
            return national_code
    return None

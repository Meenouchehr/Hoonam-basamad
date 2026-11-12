import json
import pandas as pd
import numpy as np 


# Clean Data:
df = pd.read_excel('import.xlsx')
df.columns = df.columns.str.strip() #df = df.rename(columns=lambda x: x.strip())
df = df.rename(columns=lambda x: x.replace(' ', '')) # df.columns = df.columns.str.replace(' ', '')
df = df.rename(columns={'نام' : 'first_name','نامخانوادگی':'last_name','کدملی':'national_code','تلفن':'cellphone','شمارهکارت':'card_no'})
columns = df.columns
df['error'] = 0
df.loc[1,'error'] = 1

_writer = pd.ExcelWriter('import2.xlsx', engine='xlsxwriter')     
_workbook = _writer.book               
_worksheet = _workbook.add_worksheet('sheet1')
_writer.sheets['sheet1'] = _worksheet
_correct_format = _workbook.add_format({                           
        'text_wrap': True})
_error_format = _workbook.add_format({
        'bg_color': 'red',  
        'bold': True,         
        'text_wrap': True,                           
        'border': 1})
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
            _worksheet.write(index+1, col , _value,_error_format)
    else:
        for col in range(len(row)-1):
            _value = row[col]
            if (_value is np.nan) or (type(_value)==type(np.float64())):
                _value = None
            _worksheet.write(index+1, col , _value,_correct_format)

_writer.save() 
import erppeek
from datetime import datetime
import psycopg2
import psycopg2.extras
import pandas as pd
import numpy as np

# conn = psycopg2.connect("dbname=copytype11_1 user=odoo11")
conn = psycopg2.connect("dbname=copytype user=odoo13ent")
cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

# api = erppeek.Client('http://localhost:8011', 'copytype11_1','admin', 'admin')
api = erppeek.Client('http://localhost:8013', 'copytype', 'admin', 'admin')


csv_path = "/Users/rolylautenbach/Customers/copytype/Omix_Conversion/DecemberConversion/copytypefilesasrequested/"
#drsmas = pd.read_csv(csv_path + 'drsmas.csv',index_col = "drs_acc")
#contracts = pd.read_csv(csv_path + 'rntmas.csv',index_col = "drs_acc")
#contracts = contracts.replace({pd.np.nan: ''})
drsdlv = pd.read_csv(csv_path + 'drsdlv.csv')
#drsdlv.set_index(["drs_acc"],inplace=True)
drsdlv = drsdlv.replace({pd.np.nan: ''})

SQL = "SELECT DISTINCT * FROM omnix_contracts WHERE contract_no = '11105469'"
cur.execute(SQL)
contracts = cur.fetchall()




    #key = drsmas.loc[['A009'],]
#print key.index
#print contracts.loc[key.index]
#print contracts.to_string(index=False)

for omnix_mas in contracts:
    addr_code = omnix_mas['consumable_addr_code']
    drs_acc = omnix_mas['drs_acc']
print   addr_code
row = drsdlv.loc[(drsdlv['drsdlv_code'] == int(omnix_mas['consumable_addr_code'])) & (drsdlv['drs_acc'] == omnix_mas['drs_acc'])]
print row


#drsmas.loc['A024']
#v = drsmas['vat_no']
#print  drsmas['vat_no'].to_string
#drsmas['vat_no'] = drsmas['vat_no'].fillna("0").astype('int').astype('str')
#print drsmas['vat_no'].dtypes

#print drsmas['vat_no']





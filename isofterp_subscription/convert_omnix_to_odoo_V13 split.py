###################################################################################################

# To use this program, you must fisrt use the create_table.py to create the omnix_drsmas and
# omnix_contracts tables in the copytye database. These can be deleted once the system goes live

###################################################################################################

import erppeek
from datetime import datetime
import psycopg2
import psycopg2.extras
import pandas as pd
import numpy as np

conn = psycopg2.connect("dbname=copytype user=odoo13ent")
cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

api = erppeek.Client('http://localhost:8013', 'copytype', 'admin', 'admin')

csv_path = "/Users/rolylautenbach/Customers/copytype/Omix_Conversion/DecemberConversion/copytypefilesasrequested/"
drsmas = pd.read_csv(csv_path + 'drsmas.csv', dtype={"vat_no": str})
drsmas = drsmas.replace({pd.np.nan: ''})
contracts = pd.read_csv(csv_path + 'rntmas.csv', index_col="drs_acc")
contracts = contracts.replace({pd.np.nan: ''})
# drsdlv = pd.read_csv(csv_path + 'drsdlv.csv')
# drsdlv.set_index("drs_acc", inplace=True)

res_partner_obj = api.model('res.partner')
rental_group_obj = api.model('subscription.rental.group')
subscription_obj = api.model('sale.subscription')
subscription_line_obj = api.model('sale.subscription.line')
product_obj = api.model('product.product')
product_tmpl_obj = api.model('product.template')
lot_obj = api.model('stock.production.lot')


def _create_cust_and_contracts():
    f = open("/Users/rolylautenbach/Customers/copytype/Omix_Conversion/DecemberConversion/Coneversion_errors.txt", "w+")
    string = str(datetime.now()) + " Starting to create contracts\n"
    f.write(string)
    print("Starting to create contracts\n")


    #for drs_acc, contract in contracts.head(n=4).iterrows():  # Limit to 4 records
    for drs_acc, contract in contracts.iterrows():

        # Find the partner for this contract
        partner = res_partner_obj.search([('name', 'ilike', drs_acc)])
        if partner:
            partner_id = partner[0]
            #print ('search partner = ', partner_id)

        name = ''
        if not partner:
            print ('res part not found in db',drs_acc.upper())
            row = drsmas.loc[drsmas['drs_acc'].str.upper() == drs_acc.upper()]
            #print (row)
            res = {'customer_rank': 1,
                   'type': 'contact',
                   'is_company': 1,
                   'name': row['name'].values[0] + ' ' + drs_acc,
                   'street': row['addr1'].values[0],
                   'street2': row['addr2'].values[0],
                   'city': row['addr3'].values[0],
                   'zip': str(row['pcode'].values[0]),
                   'phone': '0' + str(row['tel'].values[0]),
                   'mobile': '0' + str(row['cell'].values[0]),
                   'email': row['email'].values[0],
                   'vat': row["vat_no"].values[0]
                   }
            partner = res_partner_obj.create(res)
            partner_id = partner.id
            #print ('create partner = ', partner_id)

        # Now create the Subscription (Contract)
        sub = subscription_obj.search([('name', 'ilike', contract['contract_no'])])
        if not sub:
            # print 'sale date=',contract['sale_date']
            if contract['sale_date'] != '':
                date_start = contract['sale_date']
            else:
                date_start = contract['start_date']
            date_start = str(date_start).replace('/', '-')

            x_ceded_rental_id = ''
            if contract['rental_ceded'] != '':
                ceded_id = rental_group_obj.search([('group_code', '=', contract['rental_ceded'])])
                if ceded_id:
                    # print ('Rental grp id=%s and rental_ceded=%s' % (ceded_id[0],contract['rental_ceded']))
                    x_ceded_rental_id = ceded_id[0]
            res = {
                'name': contract['contract_no'],
                'code': contract['contract_no'],
                'partner_id': partner_id,
                'date_start': date_start,
                'stage_id': 2,              # Set to 'In Progess'
                'recurring_next_date': '2019-05-31',  # ============== Remember to change this on 'go live' run
                'x_bank_name': contract['bank_name'] + '/' + contract['bank_branch'],
                'x_ceded_reference': contract['bank_reference'],
                'x_ceded_rental_id': x_ceded_rental_id,
                'x_machine_ids': ''
            }
            #print (res)
            subscription_obj.create(res)

    f.write("Finised Loading Contracts\n")
    f.close()
    print ("Finised Loading Contracts  ")

    return

def _create_lots():
    vals = {}
    csv_file = csv_path + "rntacc.csv"
    f = open("Coneversion_errors.txt", "a+")
    f.write("Starting _create_lots\n")
    drsdlv = pd.read_csv(csv_path + 'drsdlv.csv')
    drsdlv = drsdlv.replace({pd.np.nan: ''})

    machine_cat_id = api.model('product.category').search([('name', '=', 'machine')])
    if not machine_cat_id:
        print ("missing Catergory 'machine' = Please  create one")
        exit()
    machine_cat_id = machine_cat_id[0]
    component_cat_id = api.model('product.category').search([('name', '=', 'component')])
    if not component_cat_id:
        print ("missing Catergory 'component' = Please  create one")
        exit()
    component_cat_id = component_cat_id[0]

    # Lets create all the lot is a  Machine linked to a Subscription
    with open(csv_file) as fp:
        i = 1
        for line in fp:  # Read one line at a time
            rntacc = []
            if i > 1:
                for col in line.split(','):  # Separate each rntacc in line
                    rntacc.append(col.strip())
                #if rntacc[0] != '11106933':
                #    continue
                subscription = subscription_obj.browse([('name', '=', rntacc[0])])
                if not subscription:
                    print("missing Subscription %s\n so Quiting Program " % (rntacc[0]))
                    exit()

                if rntacc[2] :
                    SQL = "SELECT DISTINCT * FROM omnix_contracts WHERE contract_no = %s"
                    cur.execute(SQL % ("'" + rntacc[0] + "'"))
                    contracts = cur.fetchall()
                    if not contracts:
                        print("no contract found in omnix_contracts for %s\n" % (rntacc[0]))
                        exit()
                    product_id = product_obj.search([('default_code', '=', rntacc[1])])
                    if not product_id:
                        print('Missing product ', rntacc[1], ' So will create it with serial number ', rntacc[2])
                        if rntacc[6] == '*':
                            cat_id = machine_cat_id
                        else:
                            cat_id = component_cat_id

                        vals = {'name': rntacc[1],
                                'default_code': rntacc[1],
                                'list_price': rntacc[5],
                                'type': 'product',
                                'categ_id': cat_id,
                                'company_id': 1,
                                }
                        product_obj.create(vals)
                        product_id = product_obj.search([('default_code', '=', rntacc[1])])

                    ################## Now create the lot record  ##################

                    lot = lot_obj.search([('name','=',rntacc[2])])
                    if not lot:
                        vals = {
                                'name': rntacc[2],
                                'product_id': product_id[0],
                                'ref': rntacc[0],
                                'company_id': 1,
                                'x_in_use': True,
                                }
                        for omnix_mas in contracts:
                            x_increase_copies_date = omnix_mas['copy_esc_date']
                            x_increase_copies_percent = omnix_mas['copy_esc_perc']
                            x_increase_service_date = omnix_mas['service_esc_date']
                            x_increase_service_percent = omnix_mas['service_esc_perc']
                            x_increase_rental_date = omnix_mas['rental_esc_date']
                            x_increase_rental_percent = omnix_mas['rental_esc_perc']
                            if x_increase_copies_date is not None:
                                vals['x_increase_copies_date'] = x_increase_copies_date.replace('/','-')
                            if x_increase_copies_percent:
                                vals['x_increase_copies_percent'] = x_increase_copies_percent
                            if x_increase_rental_date is not None:
                                vals['x_increase_rental_date'] = x_increase_rental_date.replace('/','-')
                            if x_increase_rental_percent:
                                vals['x_increase_rental_percent'] = x_increase_rental_percent
                            if x_increase_service_date is not None:
                                vals['x_increase_service_date'] = x_increase_service_date.replace('/','-')
                            if x_increase_service_percent:
                                vals['x_increase_service_percent'] = x_increase_service_percent

                            # Now look up the machine address in the drsdlv csv table and add this address to the machine

                            #row = drsdlv.loc[(drsdlv['drsdlv_code'].values[0] == omnix_mas['consumable_addr_code']) & (drsdlv['drs_acc'].values[0] == omnix_mas['drs_acc'])]
                            if omnix_mas['consumable_addr_code']:
                                row = drsdlv.loc[(drsdlv['drsdlv_code'] == int(omnix_mas['consumable_addr_code'])) & (drsdlv['drs_acc'] == omnix_mas['drs_acc'])]
                                if not row.empty:
                                    vals['note'] = ''
                                    tel = ''
                                    if  row['tel'].values[0]:
                                        tel = row['tel'].values[0]
                                    vals['note'] =  row['contact'].values[0] + "  Tel- <b> " + str(tel) + '</b>'
                                    vals['note'] += '<br>' + row['addr1'].values[0]
                                    vals['note'] += '<br>' + row['addr2'].values[0] + "  " + str(row['pcode'].values[0])
                                    vals['note'] += '<br>' + row['addr3'].values[0]

                            # now link this Lot (which is a machine to the subscription record
                            lot_id = lot_obj.create(vals)
                            #### The CUSTOMISED Create and Write must de disabled for this conversion program to run
                            subscription.write({'x_machine_ids': [(4,lot_id.id)]})
                i += 1
        print("Finished Loading Lots #")
        return

def _create_rental_and_service_charges():
    vals = {}
    csv_file = csv_path + "rntacc.csv"
    product_id = product_tmpl_obj.search([('name', '=', 'Rental')])
    if not product_id:
        print("missing Product Rental  for contract Create it as a subscription product of type 'Service' category 'charge")
        exit()
    rental_product_id = product_id[0]
    product_id = product_tmpl_obj.search([('name', '=', 'Service Charge')])
    if not product_id:
        print("missing product Service Charge  for contract Create it as a subscription produsct of type 'Service' category 'charge'")
        exit()
    service_product_id = product_id[0]
    with open(csv_file) as fp:
        i = 0
        for line in fp:  # Read one line at a time
            i += 1
            rntacc = []
            if i > 1:
                #print (i)
                for col in line.split(','):  # Separate each rntacc in line
                    rntacc.append(col.strip())
                #if rntacc[0] != '4261':
                #    continue
                subscription = subscription_obj.browse([('name', '=', rntacc[0])])
                #print (subscription)
                if not subscription:
                    print("missing Subscription %s\n so Quiting Program " % (rntacc[0]))
                    exit()

                SQL = "SELECT DISTINCT * FROM omnix_contracts WHERE contract_no = %s"
                cur.execute(SQL % ("'" + rntacc[0] + "'"))
                contracts = cur.fetchall()
                if not contracts:
                    print("no contract found in omnix_contracts for %s\n" % (rntacc[0]))
                    exit()

                ## ############################ Create RENTAL lines if needs be  ############################
                for omnix_mas in contracts:
                    if rntacc[6] == '*' and omnix_mas['monthly_rental'] != '0' and omnix_mas['end_date']:
                        # Create  Rental Subscription  Lines for this contract
                        vals = {'analytic_account_id': subscription[0],
                                'name': "Monthly Rental",
                                'quantity': 1,
                                'specific_price': omnix_mas['monthly_rental'],
                                'price_unit': omnix_mas['monthly_rental'],
                                'product_id': rental_product_id,
                                'uom_id': 1,
                                # 'x_serial_number': rntacc[2],
                                }

                        grp_id = rental_group_obj.search([('group_type', '=', 'C'), ('group_code', '=', omnix_mas['rental_ceded'])])
                        billable = rental_group_obj.browse(grp_id[0]).billable
                        if billable is True:
                            vals['x_start_date1_billable'] = False
                            vals['x_start_date1'] = omnix_mas['start_date'].replace('/', '-')
                            vals['x_end_date1'] = omnix_mas['end_date'].replace('/', '-')
                            vals['x_start_date2_billable'] = True
                            vals['x_start_date2'] = omnix_mas['end_date'].replace('/', '-')
                        else:
                            vals['x_start_date1_billable'] = True
                            vals['x_start_date1'] = omnix_mas['start_date'].replace('/', '-')
                            vals['x_end_date1'] = omnix_mas['end_date'].replace('/', '-')
                        subscription_line_obj.create(vals)
                        print ('Created Rental %s' % vals['name'])

                    #############################  Create SERVICE  lines if needs be  ############################
                    if rntacc[6] == '*' and omnix_mas['service_amount'] > '0':  # Service amount
                        if omnix_mas['service_start_date1'] is None:
                            print ("Found  Service on contract no %s amount= %s date= %s" % (
                            omnix_mas['contract_no'], omnix_mas['service_amount'],
                            omnix_mas['service_start_date1']))
                            exit()
                        #print (subscription[0])
                        vals = {'analytic_account_id': subscription[0],
                                'name': "Monthly Service",
                                'quantity': 1,
                                'price_unit': omnix_mas['service_amount'],
                                'specific_price': omnix_mas['service_amount'],
                                'product_id': service_product_id,
                                'uom_id': 1,
                                'x_start_date1': omnix_mas['service_start_date1'].replace('/', '-')
                                }
                        grp_id = rental_group_obj.search(
                            [('group_type', '=', 'V'), ('group_code', '=', omnix_mas['service_type1'])])
                        billable = rental_group_obj.browse(grp_id[0]).billable
                        print (omnix_mas['service_type1'],billable)

                        vals['x_start_date1_billable'] = billable
                        subscription_line_obj.create(vals)
                        print ('Service omnix_masord created %s' % vals['name'])
        return

def _create_linvoice_lines():
    f = open("Coneversion_errors.txt", "a+")
    f.write("Starting _create_linvoice_lines\n")
    print("Starting _create_linvoice_lines\n")
    ## Now load a analytic invoice line for B&W and Coulor copies
    csv_file = csv_path + "rntcpc.csv"
    i = 0
    with open(csv_file) as fp:
        for line in fp:  # Read one line at a time
            rntcpc = []
            if i > 1:  #Skip the Header record
                for col in line.split(','):  # Separate each rntcpc in line
                    rntcpc.append(col.strip('"'))
                #if rntcpc[0] != '3407':
                #    continue
                if rntcpc[1] == 'Colour copies' or rntcpc[1] == 'Black copies':
                    sub_rec = subscription_obj.browse([('code', '=', rntcpc[0])])
                    if not sub_rec:
                        print('missing contract %s rntcpc[2]=%s' % (rntcpc[0],rntcpc[2]))
                        exit()
                    #print (" xx this should be the subscription id", sub_rec.id[0], len(sub_rec.x_machine_ids[0]))

                    rec = rental_group_obj.search([('group_type','=','V'),('group_code','=',rntcpc[14])])
                    if rec:
                        bill = rental_group_obj.browse(rec[0]).billable
                        #print (bill)
                        #if not bill:
                        #    print ('no copies')

                    SQL = "SELECT DISTINCT * FROM omnix_contracts WHERE contract_no = %s"
                    cur.execute(SQL % ("'" + rntcpc[0] + "'"))
                    contracts = cur.fetchall()
                    for omnix_mas in contracts:
                        if omnix_mas['billing_type'] == '0' or omnix_mas['billing_type'] == '2':  # 0 = Rental & copies  2 = Copies only
                            product_id = product_obj.search([('name', 'ilike',rntcpc[1])])
                            if not product_id:
                               print('Missing product %s for contract %s\n' % (rntcpc[1], rntcpc[0]))
                               exit()
                            if product_id and sub_rec and rntcpc[2] != '0':
                                vals = {'analytic_account_id': sub_rec.id[0],
                                        'name': rntcpc[1],
                                        'quantity':  0,
                                        'product_id': product_id[0],
                                        'uom_id': 1,
                                        'specific_price': rntcpc[6],
                                        'price_unit': rntcpc[6],
                                        'x_copies_show': True,
                                        'x_copies_free' : rntcpc[11],
                                        'x_copies_last': rntcpc[2],
                                        'x_copies_previous': rntcpc[2],
                                        'x_copies_vol_1': rntcpc[3],
                                        'x_copies_vol_2': rntcpc[4],
                                        'x_copies_price_1': rntcpc[6],
                                        'x_copies_price_2': rntcpc[7],
                                        'x_copies_price_3': rntcpc[8],
                                        'x_copies_minimum': rntcpc[9],
                                        }
                                if len(sub_rec.x_machine_ids[0]):
                                    # Find the Machine amongst all the equipment linked to this Subscription
                                    # and load the serial number on the invoice line as a ref
                                    for production_lot in sub_rec.x_machine_ids:
                                        for mac in production_lot:
                                            if mac.product_id.categ_id.name == 'machine':
                                                vals['x_serial_number_id'] =  mac.id
                                if rntcpc[12]:
                                    vals.update({'x_start_date1': rntcpc[12].replace('/','-')})
                                vals['x_start_date1_billable'] = True
                                grp_id = rental_group_obj.search([('group_type', '=', 'V'), ('group_code', 'ilike',rntcpc[14])])  #copy_type1
                                if not grp_id:
                                    print ('not grp_id  rntcpc[16]=%s' % (rntcpc[16]))
                                    vals['x_start_date1_billable'] = False
                                else:
                                    billable = rental_group_obj.browse(grp_id[0]).billable
                                    if billable:
                                        vals['x_start_date1_billable'] = True
                                print (i)
                                subscription_line_obj.create(vals)
            i += 1
    print ("finished loading copies")
    f.write("Finished _create_linvoice_lines\n")
    f.close()

def _create_adminfee():
    f = open("Coneversion_errors.txt", "a+")
    f.write("Starting to load Admin fees\n")
    print("Starting to load Admin fees\n")
    csv_file = csv_path + "outadminfee.csv"
    with open(csv_file) as fp:
        i = 1
        for line in fp:  # Read one line at a time
            adminfee = []
            if i > 1:
                print(line)
                for col in line.split(','):  # Separate each adminfee in line
                    col = col.lstrip('0')
                    adminfee.append(col)

                subscription_id = subscription_obj.search([('name', '=', adminfee[1])])
                if not subscription_id:
                    # f.write ("no contract found for %s in Admin file\n" % (adminfee[1]))
                    print("%s no contract found for %s in Admin file\n" % (i, adminfee[1]))
                    exit()
                SQL = "SELECT name FROM sale_subscription_line WHERE analytic_account_id = %s and (name = 'Black copies' OR name = 'Colour copies')"
                cur.execute(SQL % (subscription_id[0]))
                copies = cur.fetchall()
                # print(len(copies))
                if len(copies) == 0: continue  # No admin fees if Service only contract

                # Create Analytic Lines for this contract Admin fee
                product_id = product_tmpl_obj.search([('name', '=', 'Admin fee')])
                if not product_id:
                    print ('No Admin fee recored - cerate one !')
                    exit()
                vals = {'analytic_account_id': subscription_id[0],
                        'name': "Admin Fee",
                        'quantity': 1,
                        'specific_price': adminfee[2],
                        'price_unit': adminfee[2],
                        'product_id': product_id[0],
                        'uom_id': 1,
                        'x_start_date1': "2019-04-01",
                        'x_start_date1_billable': True
                        }
                subscription_line_obj.create(vals)
                # print ('Admin feee for %s' % adminfee[1])
            i += 1
        print("Finished loading Admin Fees")
        f.write("Finished loading Admin Fees\n")
        f.close()

def _set_billing_frequency():
    csv_file = csv_path + "rntmas.csv"
    f = open("Coneversion_errors.txt", "a+")
    f.write("Starting to set billing frequency\n")
    print("Starting to set billing frequency\n")
    cur.execute("SELECT * FROM omnix_contracts ")
    contracts = cur.fetchall()
    for contract in contracts:
        if contract['contract_no'] == 'contract_no': continue   # skip first line
        subscription = subscription_obj.search([('code', '=', contract['contract_no'])])
        if subscription:
            if int(contract['copy_frequency']) > 1:
                print(subscription[0])
                id = subscription_line_obj.search([('analytic_account_id', '=', subscription[0]), ('name', 'ilike', 'copies')])
                line = subscription_line_obj.browse(id[0])
                if line:
                    print('copies',contract['contract_no'],contract['copy_frequency'],contract['hold_copy_frequency'])
                    line.x_billing_frequency = contract['copy_frequency']
                    line.x_billing_hold = contract['hold_copy_frequency']
            if int(contract['rental_frequency']) > 1:
                print('Monthly Rental', contract['contract_no'], contract['rental_frequency'],contract['hold_rental_frequency'])
                id = subscription_line_obj.search([('analytic_account_id','=',subscription[0]),('name','=','Monthly Rental')])
                line = subscription_line_obj.browse(id[0])
                if line:
                    line.x_billing_frequency = contract['rental_frequency']
                    line.x_billing_hold = contract['hold_rental_frequency']

            if int(contract['service_frequency']) > 1:
                print('Monthly Service', contract['contract_no'], contract['service_frequency'],contract['hold_service_frequency'])
                id = subscription_line_obj.search([('analytic_account_id', '=', subscription[0]), ('name', '=', 'Monthly Service')])
                line = subscription_line_obj.browse(id[0])
                if line:
                    line.x_billing_frequency = contract['service_frequency']
                    line.x_billing_hold = contract['hold_service_frequency']
        else:
            print('subsription missing from Odoo ',contract['contract_no'])
            exit()

#_create_cust_and_contracts()

#_create_lots()

_create_rental_and_service_charges()

#_create_linvoice_lines()

#_create_adminfee()

#_set_billing_frequency()

# _compare_omnix_odoo()
# _compare_odoo_omnix()

# _read_email()

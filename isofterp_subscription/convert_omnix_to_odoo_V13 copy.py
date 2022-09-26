
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

#conn = psycopg2.connect("dbname=copytype11_1 user=odoo11")
conn = psycopg2.connect("dbname=copytype user=odoo13ent")
cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

#api = erppeek.Client('http://localhost:8011', 'copytype11_1','admin', 'admin')
api = erppeek.Client('http://localhost:8013', 'copytype','admin', 'admin')
csv_path = "/Users/rolylautenbach/Customers/copytype/Omix_Conversion/DecemberConversion/copytypefilesasrequested/"
drsmas = pd.read_csv(csv_path + 'drsmas.csv')
drsmas.set_index("drs_acc", inplace=True)
rntmas = pd.read_csv(csv_path + 'rntmas.csv')
rntmas.set_index("drs_acc", inplace=True)
drsdlv = pd.read_csv(csv_path + 'drsdlv.csv')
drsdlv.set_index("drs_acc", inplace=True)

data.head()

res_partner_obj = api.model('res.partner')
rental_group_obj = api.model('subscription.rental.group')
subscription_obj = api.model('sale.subscription')
subscription_line_obj = api.model('sale.subscription.line')
product_obj = api.model('product.product')
product_tmpl_obj = api.model('product.template')
lot_obj = api.model('stock.production.lot')

def _fix_date(old_date):

    new_date = str(old_date).replace('/','-')
    """
    print ('old date= %s' % (old_date))
    if len(old_date) < 10:
        old_date = '20' + old_date
    day = old_date[2:4]
    mnth = old_date[5:7]
    yr = '20' + old_date[8:11]
    return (yr + '-' + mnth + '-' + day)
    """
    return new_date

def _create_contracts():
    SQL = "SELECT * FROM omnix_contracts"
    cur.execute(SQL)
    contracts = cur.fetchall()


    f = open("Coneversion_errors.txt", "w+")
    f.write("Starting _create_contracts and checking missing Debtors\n")
    # First make sure all debtors exsist

    vals = {}
    """
    for omnix_mas in contracts:
        if i > 1:
            partner_id = res_partner_obj.search([('name', 'ilike', omnix_mas['drs_acc'])])
            if not partner_id:
                res = {'type': 'contact',
                       'is_company': 1,
                       'customer_rank': 1,
                       'name': omnix_mas['drs_acc']  ,
                }
                partner = res_partner_obj.create(res)
                #f.write("no partner found with code so created one = %s id=%s\n" % (omnix_mas['drs_acc'], partner_id))
                print("no partner found with code so created one = %s id=%s\n" % (omnix_mas['drs_acc'], partner_id))
        i += 1
    f.write("Finished checking Debtors exsist\n")
    print (datetime.now(), "Finished checking Debtors exsist\n")
    f.close()
    conn.commit()
    return
    """
    string = str(datetime.now()) + " Starting to create contracts\n"
    f.write(string)
    print("Starting to create contracts\n")
    i = 1
    for omnix_mas in contracts:
        #print i
        if i > 1:   # skip the first omnix_masord which are headers

            id = subscription_obj.search([('name','=',omnix_mas['contract_no'])])
            if id:
                print ('continu',i)
                continue

            # Find the partner for this contract
            #print omnix_mas[0]
            if omnix_mas['drs_acc']:
                partner_id = res_partner_obj.search([('name','ilike',omnix_mas['drs_acc'])])

                if not partner_id:
                    print ('drs_acc',omnix_mas['drs_acc'])
                    SQL = "SELECT * FROM omnix_drsmas where drs_acc = %s"
                    cur.execute(SQL %("'" + omnix_mas['drs_acc'] + "'"))
                    drsmas = cur.fetchone()
                    #drsmas = omnix_partner_obj.search([('drs_acc', 'ilike', omnix_mas['drs_acc'])])

                    if drsmas:
                        res = { 'customer_rank': 1,
                                'type': 'contact',
                                'is_company': 1,
                                'name': drsmas['name'] + ' ' + drsmas['drs_acc'],
                                'street': drsmas['addr1'],
                                'street2': drsmas['addr2'],
                                'city': drsmas['addr3'],
                                'zip': drsmas['pcode'],
                                'phone': drsmas['tel'],
                                'email': drsmas['email'],
                                'vat': drsmas['vat_no'],
                        }

                        res_partner = res_partner_obj.create(res)

                        #print res_partner.id,r.namees_partner


                        #f.write("no partner found with code so created one = %s id=%s\n" % (omnix_mas['drs_acc'],partner_id))
                        #print("no partner found with code so created this one = %s id=%s" % (omnix_mas['drs_acc'], partner_id))
                        #Now create the Subscription (Contract)



                        res = {'customer_rank': 1,
                                'type': 'other',
                                'name': omnix_mas['contact_name'] ,
                                'parent_id': res_partner.id,
                                'street': omnix_mas['service_addr1'],
                                'street2':omnix_mas['service_addr2'],
                                'city': omnix_mas['service_addr3'],
                                'zip': omnix_mas['service_pcode'],
                                'email': omnix_mas['email'],
                                }
                        res_partner = res_partner_obj.create(res)


                    # Start and End Date
            #print ('sale_date %s start_date %s end_date %s' % (omnix_mas['sale_date'],omnix_mas['start_date'], omnix_mas['end_date']))
            """
            if omnix_mas['sale_date']:
                vals['date_start'] = _fix_date(omnix_mas['sale_date'])
            else:
                vals['date_start'] = _fix_date(omnix_mas['start_date'])


            vals['x_bank_name'] = omnix_mas['bank_branch']
            vals['x_ceded_reference'] = omnix_mas['bank_reference']
            # Find the description in rental_ceded table for this contract
            ceded_id = []
            if omnix_mas['rental_ceded']:
                ceded_id = rental_group_obj.search([('group_code', '=', omnix_mas['rental_ceded'])])
                if ceded_id:
                    #print ('Rental grp id=%s and rental_ceded=%s' % (ceded_id[0],omnix_mas['rental_ceded']))
                    vals['x_ceded_rental_id'] = ceded_id[0]

            vals['recurring_next_date'] = '2019-05-31'       # ============== Remember to change this on 'go live' run
            #print  vals['recurring_next_date']
            #Create Analytic Account (Contract)
            subscription_obj.create(vals)
            """
        i += 1

    f.write("Finised Loading Contracts\n")
    f.close()
    print ("Finised Loading Contracts  ")

def _create_linvoice_lines():
    f = open("Coneversion_errors.txt", "a+")
    f.write("Starting _create_linvoice_lines\n")
    ## Now load a analytic invoice line for B&W and Coulor copies
    csv_file = "/Users/rolylautenbach/Customers/copytype/Omix_Conversion/MayConversion/rntcpc.csv"
    i = 0
    with open(csv_file) as fp:
        for line in fp:  # Read one line at a time
            rntcpc = []
            if i > 1:  #Skip the Header record
                for col in line.split(','):  # Separate each rntcpc in line
                    rntcpc.append(col.strip('"'))

                if rntcpc[1] == 'Colour copies' or rntcpc[1] == 'Black copies':
                    analytic_id = subscription_obj.search([('name', '=', rntcpc[0])])
                    if not analytic_id:
                        print('missing contract %s rntcpc[2]=%s' % (rntcpc[0],rntcpc[2]))
                        f.write('missing contract %s rntcpc[2]=%s\n' % (rntcpc[0], rntcpc[2]))
                        continue
                    analytic_account = subscription_obj.browse(analytic_id)
                    rec = rental_group_obj.search([('group_type','=','V'),('group_code','=',rntcpc[14])])
                    if rec:
                        bill = rental_group_obj.browse(rec[0]).billable
                        #print (bill)
                        if not bill:
                            print ('no copies')


                    # Need to find the machine and put the serial number and machine name on the recurring line
                    mac_id = machine_obj.search([('analytic_id', '=', analytic_id[0]),('product_id.product_tmpl_id.categ_id.name','=','machine')])
                    serial_no = ''
                    macId = ''
                    if mac_id:
                        #print (analytic_account.name, mac_id)
                        macId = mac_id[0]
                        machine = machine_obj.browse(mac_id[0])
                        if machine.serial_number_id:
                            serial_no = machine.serial_number_id.name
                    else:
                        f.write('missing machine for this invoice line  contract=%s \n' % (analytic_account.name))
                        print('missing machine for this invoice line  contract=%s \n' % (analytic_account.name))

                    SQL = "SELECT DISTINCT * FROM omnix_contracts WHERE contract_no = %s"
                    cur.execute(SQL % ("'" + rntcpc[0] + "'"))
                    contracts = cur.fetchall()
                    for omnix_mas in contracts:
                        if omnix_mas['billing_type'] == '0' or omnix_mas['billing_type'] == '2':  # 0 = Rental & copies  2 = Copies only
                            product_id = product_obj.search([('name', 'ilike',rntcpc[1])])
                            if not product_id:
                               f.write('Missing product %s for contract %s\n' % (rntcpc[1],rntcpc[0]))
                               print('Missing product %s for contract %s\n' % (rntcpc[1], rntcpc[0]))
                               continue
                            if product_id and analytic_id and rntcpc[2] != '0':
                                #print ('about to create ',analytic_account.name, )

                                vals = {'analytic_account_id': analytic_id[0],
                                        'name': rntcpc[1],
                                        'quantity':  0,
                                        'product_id': product_id[0],
                                        'uom_id': 1,
                                        'specific_price': rntcpc[6],
                                        'x_machine_master_id': macId,
                                        'x_serial_number': serial_no,
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

                                if rntcpc[12]:
                                    vals.update({'x_start_date1':  _fix_date(rntcpc[12])})
                                vals['x_start_date1_billable'] = True
                                grp_id = rental_group_obj.search([('group_type', '=', 'V'), ('group_code', 'ilike',rntcpc[14])])  #copy_type1
                                if not grp_id:
                                    print ('not grp_id  rntcpc[16]=%s' % (rntcpc[16]))
                                    vals['x_start_date1_billable'] = False
                                else:
                                    billable = rental_group_obj.browse(grp_id[0]).billable
                                    vals['x_start_date1_billable'] = billable
                                subscription_line_obj.create(vals)
                                #print('invoice created', analytic_id[0], rntcpc[1])

            i += 1
    print ("finished loading copies")
    f.write("Finished _create_linvoice_lines\n")
    f.close()

def _create_adminfee():
    f = open("Coneversion_errors.txt", "a+")
    f.write("Starting to load Admin fees\n")
    print("Starting to load Admin fees\n")
    csv_file = "/Users/rolylautenbach/Customers/copytype/Omix_Conversion/MayConversion/adminfee.csv"
    with open(csv_file) as fp:
        i = 1
        for line in fp:  # Read one line at a time
            adminfee = []
            if i > 1:
                #print(line)
                for col in line.split(','):  # Separate each adminfee in line
                    adminfee.append(col.strip(' '))

                analytic_id = subscription_obj.search([('name', '=', adminfee[1])])
                if not analytic_id:
                    #f.write ("no contract found for %s in Admin file\n" % (adminfee[1]))
                    print("%s no contract found for %s in Admin file\n" % (i,adminfee[1]))
                    continue
                SQL = "SELECT name FROM account_analytic_invoice_line WHERE analytic_account_id = %s and (name = 'Black copies' OR name = 'Colour copies')"
                cur.execute(SQL % (analytic_id[0]))
                copies = cur.fetchall()
                #print(len(copies))
                if len(copies) == 0: continue           # No admin fees if Service only contract

                # Create Analytic Lines for this contract Admin fee
                product_id = product_tmpl_obj.search([('default_code', '=', 'ADMIN FEE')])
                vals = {'analytic_account_id': analytic_id[0],
                        'name': "Admin Fee",
                        'quantity': 1,
                        'specific_price': adminfee[2],
                        'product_id': product_id[0],
                        'uom_id': 1,
                        'x_start_date1': "2019-04-01",
                        'x_start_date1_billable': True
                        }
                subscription_line_obj.create(vals)
                #print ('Admin feee for %s' % adminfee[1])
            i += 1
        print("Finished loading Admin Fees")
        f.write("Finished loading Admin Fees\n")
        f.close()

def _create_lots():
    csv_file = "/Users/rolylautenbach/Customers/copytype/Omix_Conversion/MayConversion/rntacc.csv"
    f = open("Coneversion_errors.txt", "a+")
    f.write("Starting _create_lots\n")
    # Lets create all the lots before we create the Machines as they need to reference the lot numbers
    with open(csv_file) as fp:
        i = 1
        for line in fp:  # Read one line at a time
            rntacc = []
            if i > 1:
                for col in line.split(','):  # Separate each rntacc in line
                    rntacc.append(col.strip('"'))


                if rntacc[2]:
                    #print rntacc[2]
                    product_id = product_obj.search([('default_code', '=', rntacc[1])])
                    if product_id:
                        x = lot_obj.search([('name', '=', rntacc[2]),('product_id','=',product_id[0])])
                        if not x:
                            #print('About to created lot %s %s' % (rntacc[0],rntacc[2]))
                            lot_obj.create({'name': rntacc[2], 'product_id': product_id[0], 'ref': rntacc[0]})
                    else:
                        print('Missing product ',rntacc[1], ' So will create it with serial number ',rntacc[2])
                        f.write('Missing product %s So will create it with serial number %s\n' % (rntacc[1], rntacc[2]))
                        vals = { 'name': rntacc[1],
                                 'default_code': rntacc[1]

                        }
                        product_id = product_obj.create(vals)

                        vals = {'name': rntacc[2],
                                'product_id': product_id.id,
                                'ref': rntacc[0]

                                }
                        lot_obj.create(vals)


            i += 1
        print ("Finished Loading Serial #")

def _create_machines():
    f = open("Coneversion_errors.txt", "a+")
    f.write("Starting to load Machines\n")
    ## Now load a Machines and other stock for contracts
    csv_file = "/Users/rolylautenbach/Customers/copytype/Omix_Conversion/MayConversion/rntacc.csv"


    print ("start loading machines")
    product_id = product_tmpl_obj.search([('default_code', '=', 'RENT')])
    if not product_id:
        f.write("missing product RENT service for contract")
        exit()
    rental_product_id = product_id[0]
    product_id = product_obj.search([('default_code', '=', 'SERV')])
    if not product_id:
        f.write("missing product SERV service for contract")
        exit()
    service_product_id = product_id[0]

    i = 0
    with open(csv_file) as fp:
        for line in fp:  # Read one line at a time
            i += 1
            rntacc = []
            if i > 1:
                for col in line.split(','):  # Separate each rntacc in line
                    # print (f)
                    rntacc.append(col.strip('"'))
                #if rntacc[0] != '11103688': continue                                   ######## SET FOR TESTING
                analytic_id = subscription_obj.search([('name', '=', rntacc[0])])
                if not analytic_id:
                    f.write ("no contract found for %s\n" % (rntacc[0]))
                    print("no contract found for %s\n" % (rntacc[0]))
                    continue

                #print ("dealing with contract no %s" % (rntacc[0]))
                SQL = "SELECT DISTINCT * FROM omnix_contracts WHERE contract_no = %s"
                cur.execute(SQL % ("'" + rntacc[0] + "'"))
                contracts = cur.fetchall()
                for omnix_mas in contracts:
                    copy_esc_date    = omnix_mas['copy_esc_date']
                    copy_esc_perc    = omnix_mas['copy_esc_perc']
                    service_esc_date = omnix_mas['service_esc_date']
                    service_esc_perc = omnix_mas['service_esc_perc']
                    rental_esc_date  = omnix_mas['rental_esc_date']
                    rental_esc_perc  = omnix_mas['rental_esc_perc']
                    product_id = product_tmpl_obj.search([('default_code', '=',rntacc[1] )])
                    if not product_id:
                        f.write("missing product_id = %s serial number=%s for contract %s\n" % (rntacc[1], rntacc[2], rntacc[0]))
                        print("missing product_id = %s serial number=%s for contract %s\n" % (rntacc[1], rntacc[2],rntacc[0]))
                        continue
                    product_tmpl = product_tmpl_obj.browse(product_id)
                    if product_tmpl and analytic_id :
                        vals = {'analytic_id': analytic_id[0],
                                'name': rntacc[1],
                                'product_id':product_id[0],
                                }
                        lot = lot_obj.search([('name', '=', rntacc[2])])
                        if lot:
                            vals['serial_number_id'] = lot[0]
                        else:
                            print(rntacc)

                        if copy_esc_date is not None:
                            vals['increase_copies_date'] = _fix_date(copy_esc_date)
                        if copy_esc_perc :
                            vals['increase_copies_percent'] = copy_esc_perc
                        if rental_esc_date is not None:
                            vals['increase_rental_date'] =  _fix_date(rental_esc_date)
                        if rental_esc_perc:
                            vals['increase_rental_percent'] =  rental_esc_perc
                        if service_esc_date is not None:
                            vals['increase_service_date'] =  _fix_date(service_esc_date)
                        if service_esc_perc :
                            vals['increase_service_percent'] =  service_esc_perc
                        vals['client_name']  = omnix_mas['contact_name']
                        vals['client_email'] = omnix_mas['email']
                        vals['client_phone'] = omnix_mas['contact_tel']
                        new_machine = machine_obj.create(vals)



                        ##  Create RENTAL lines if needs be  ############################
                        if rntacc[6] == '*'  and omnix_mas['monthly_rental'] != '0' and omnix_mas['end_date']:
                            # Create Analytic Lines for this contract (rental line,service line
                            vals = {'analytic_account_id': analytic_id[0],
                                    'name': "Monthly Rental",
                                    'quantity': 1,
                                    'specific_price': omnix_mas['monthly_rental'],
                                    'product_id': rental_product_id,
                                    'uom_id': 1,
                                    'x_machine_master_id': new_machine.id,
                                    #'x_serial_number': rntacc[2],
                                    }
                            grp_id = rental_group_obj.search([('group_type','=','C'),('group_code', '=', omnix_mas['rental_ceded'])])
                            billable =  rental_group_obj.browse(grp_id[0]).billable
                            if billable is True:
                                vals['x_start_date1_billable'] = False
                                vals['x_start_date1'] = _fix_date(omnix_mas['start_date'])
                                vals['x_end_date1'] = _fix_date(omnix_mas['end_date'])
                                vals['x_start_date2_billable'] = True
                                vals['x_start_date2'] = _fix_date(omnix_mas['end_date'])
                            else:
                                vals['x_start_date1_billable'] = True
                                vals['x_start_date1'] = _fix_date(omnix_mas['start_date'])
                                vals['x_end_date1'] = _fix_date(omnix_mas['end_date'])

                            subscription_line_obj.create(vals)
                            # print ('Created @ 414 %s' % vals['name'])

                        ##  Create SERVICE  lines if needs be  ############################
                        if rntacc[6] == '*' and omnix_mas['service_amount'] > '0' :  # Service amount
                            if omnix_mas['service_start_date1'] is  None:
                                print ("Found  Service on contract no %s amount= %s date= %s" % (omnix_mas['contract_no'], omnix_mas['service_amount'], omnix_mas['service_start_date1']))
                                exit()

                            vals = {'analytic_account_id': analytic_id[0],
                                    'name': "Monthly Service",
                                    'quantity': 1,
                                    'specific_price': omnix_mas['service_amount'],
                                    'product_id': service_product_id,
                                    'uom_id': 1,
                                    'x_machine_master_id': new_machine.id,
                                    #'x_serial_number': new_machine.serial_number_id.name,
                                    'x_start_date1': _fix_date(omnix_mas['service_start_date1'])
                                    }
                            grp_id = rental_group_obj.search([('group_type','=','V'),('group_code', '=', omnix_mas['service_type1'])])
                            billable = rental_group_obj.browse(grp_id[0]).billable
                            vals['x_start_date1_billable'] = billable
                            subscription_line_obj.create(vals)
                            #print ('Service omnix_masord created %s' % vals['name'])

    print ("finished loading machines")
    f.write("finished loading machines\n")
    f.close()

def _set_machine_categ_id():
    f = open("Coneversion_errors.txt", "a+")
    f.write("Starting to set category\n")
    csv_file = "/Users/rolylautenbach/Customers/copytype/Omix_Conversion/MayConversion/rntmet31052019.csv"
    i = 0
    with open(csv_file) as fp:
        for line in fp:  # Read one line at a time
            i += 1
            rntmet = []
            if i > 1:
                for col in line.split(','):  # Separate each rntacc in line
                    # print (f)
                    rntmet.append(col.strip('"'))
                #print(rntmet)
                mac = machine_obj.search([('serial_number_id','=',rntmet[0])])
                if mac:
                    for machine in machine_obj.browse(mac):
                        #print (rntmet[0],machine.name,machine.product_id.id)
                        product_tmpl_id = product_obj.browse(machine.product_id.id).product_tmpl_id
                        #print (product_tmpl_id)
                        product_tmpl = product_tmpl_obj.browse([('id','=',product_tmpl_id.id)])
                        product_tmpl.write({'categ_id': 3})  # Set the product category = 'machine' - this is used later in the software


    f.write("Finished setting categ\n")
    print ("Finished setting categ\n")
    f.close()

def _set_billing_frequency():
    csv_file = "/Users/rolylautenbach/Customers/copytype/Omix_Conversion/MayConversion/rntmas.csv"
    f = open("Coneversion_errors.txt", "a+")
    f.write("Starting to set billing frequency\n")
    print("Starting to set billing frequency\n")
    i = 0
    for contract in contracts:

                if int(contract['copy_frequency']) > 1:
                    analytic_account = subscription_obj.search([('name','=',contract['contract_no'])])
                    if analytic_account:
                        line_id = subscription_line_obj.search([('analytic_account_id', '=', analytic_account[0]), ('name', 'ilike', 'copies')])
                        if line_id:
                            line = subscription_line_obj.browse(line_id)
                            line.write({'x_billing_frequency': contract['copy_frequency']})
                            line.write({'x_billing_hold':  contract['hold_copy_frequency']})
                            print(contract['contract_no'],contract['copy_frequency'],contract['hold_copy_frequency'])
                if int(contract['rental_frequency']) > 1:
                    analytic_account = subscription_obj.search([('name', '=', contract['contract_no'])])
                    if analytic_account:
                        line_id = subscription_line_obj.search([('analytic_account_id','=',analytic_account[0]),('name','=','Monthly Rental')])
                        if line_id:
                            line = subscription_line_obj.browse(line_id)
                            line.write({'x_billing_frequency': contract['rental_frequency']})
                            line.write({'x_billing_hold': contract['hold_rental_frequency']})
                            print(contract['contract_no'],contract['rental_frequency'],contract['hold_rental_frequency'])
                if int(contract['service_frequency']) > 1:
                    analytic_account = subscription_obj.search([('name', '=', contract['contract_no'])])
                    if analytic_account:
                        line_id = subscription_line_obj.search([('analytic_account_id', '=', analytic_account[0]), ('name', '=', 'Monthly Service')])
                        if line_id:
                            line = subscription_line_obj.browse(line_id)
                            line.write({'x_billing_frequency': contract['service_frequency']})
                            line.write({'x_billing_hold': contract['hold_service_frequency']})
                            print(contract['contract_no'],contract['service_frequency'],contract['hold_service_frequency'])

def _compare_omnix_odoo():
    f = open("Coneversion_errors.txt", "a+")
    f.write("Comparing Invoice Totals\n")
    csv_file = "/Users/rolylautenbach/Customers/copytype/Omix_Conversion/MayConversion/allmay2019.csv"
    account_obj = api.model('account.invoice')

    print ("start compare results")
    i = 0
    diff = 0
    missing_diff = 0
    total_omnix = 0
    with open(csv_file) as fp:
        for line in fp:  # Read one line at a time
            rntacc = []
            for col in line.split(','):  # Separate each rntacc in line
                # print (f)
                rntacc.append(col.strip('"'))
            if rntacc[7] != '\n' and rntacc[0]!= 'Drs Accno':
                total_omnix += float(rntacc[7])
                id = account_obj.search([('origin','=',rntacc[1])])
                if not id:
                    #print (data[0])
                    f.write ('Missing invoice for contract %s in Odoo  - Omnix invoice number %s amount = %s\n' % (rntacc[1],rntacc[2],rntacc[7]) )
                    print('Missing invoice for contract %s in Odoo  - Omnix invoice number %s amount = %s\n' % (rntacc[1],rntacc[2],rntacc[7]) )
                    missing_diff += float(rntacc[7])
                    continue
                amt = account_obj.browse([id[0]]).amount_total

                difference = amt[0] - float(rntacc[7])
                if amt[0] != float(rntacc[7]):
                    difference = round(amt[0] - float(rntacc[7]),2)
                    diff += difference

                    if difference == -0.01: continue
                    if difference > 0.01 :
                        f.write('Contract=%s Omnix amt= %s Odoo amt= %s \n' % (rntacc[1],rntacc[7].strip(' '),amt[0]))
                        print ('Contract=%s Omnix amt= %s Odoo amt= %s  -----------------> Differenc=%s\n' % (rntacc[1],rntacc[7].strip(' '),amt[0],difference))
        print('Total Invoice amt from Omnix = ', total_omnix)
        print ('Total Diff = %s\n Missing diff= %s\n' % (diff, missing_diff))
        f.write('Total Invoice amt from Omnix = %s\n' % (total_omnix))

        f.write('Total Diff = %s\n Missing diff= %s\n' % (diff, missing_diff))
        f.close()

def _compare_odoo_omnix():
    f = open("Coneversion_errors.txt", "a+")
    f.write("Comparing Invoice Totals\n")
    csv_file = "/Users/rolylautenbach/Customers/copytype/Omix_Conversion/MayConversion/allmay2019.csv"
    account_obj = api.model('account.invoice')

    print ("start compare results")
    i = 0
    diff = 0
    missing_diff = 0
    total_omnix = 0
    contract_numbers =[]
    with open(csv_file) as fp:
        for line in fp:  # Read one line at a time
            col = line.split(',')  # Separate each rntacc in line

            contract_numbers.append(col[1])

        for rec in account_obj.browse([]):

            if rec.origin not in contract_numbers:
                print('missing invoice in Omnix for this contract ',rec.origin)
                missing_diff += rec.amount_total
        print('Total Invoice amt from Omnix = ', total_omnix)
        print ('Total Diff = %s\n Missing diff= %s\n' % (diff, missing_diff))
        f.write('Total Invoice amt from Omnix = %s\n' % (total_omnix))

        f.write('Total Diff = %s\n Missing diff= %s\n' % (diff, missing_diff))
        f.close()

def _read_email():
    import poplib
    import email  # new statement

    import string, random


    # input email address, password and pop3 server domain or ip address
    SERVER = 'pop.isnet.co.za'
    USER = 'dev@isoft.co.za'
    PASSWORD = 'D!isoft01!V'
    # connect to server
    server = poplib.POP3(SERVER)
    # login
    server.user(USER)
    server.pass_(PASSWORD)

    # list items on server
    resp, items, octets = server.list()

    for i in range(0, 10):
        id, size = string.split(items[i])
        resp, text, octets = server.retr(id)
        text = string.join(text, "\n")
        b = email.message_from_string(text)
        body = ""
        if b.is_multipart():
            for part in b.walk():
                ctype = part.get_content_type()
                cdispo = str(part.get('Content-Disposition'))

                # skip any text/plain (txt) attachments
                if ctype == 'text/plain' and 'attachment' not in cdispo:
                    body = part.get_payload(decode=True)  # decode
                    break
        # not multipart - i.e. plain text, no attachments, keeping fingers crossed
        else:
            body = b.get_payload(decode=True)
        print (body)

_create_contracts()
#_create_lots()
#_create_machines()
#_set_machine_categ_id()
#_create_linvoice_lines()

#_create_adminfee()
#_set_billing_frequency()


#_compare_omnix_odoo()
#_compare_odoo_omnix()

#_read_email()





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

# conn = psycopg2.connect("dbname=copytype11_1 user=odoo11")
conn = psycopg2.connect("dbname=copytype user=odoo13ent")
cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

# api = erppeek.Client('http://localhost:8011', 'copytype11_1','admin', 'admin')
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


def _create_contracts():
    f = open("Coneversion_errors.txt", "w+")
    string = str(datetime.now()) + " Starting to create contracts\n"
    f.write(string)
    print("Starting to create contracts\n")

    for drs_acc, contract in contracts.head(n=4).iterrows():
        # Find the partner for this contract
        partner = res_partner_obj.search([('name', 'ilike', drs_acc)])
        if partner:
            partner_id = partner[0]
            #print ('search partner = ', partner_id)

        name = ''
        if not partner:
            #print 'res part not found in db',drs_acc
            row = drsmas.loc[drsmas['drs_acc'] == drs_acc]
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
            print ('create partner = ', partner_id)

        # Now create the Subscription (Contract)
        # Start and End Date
        # print ('sale_date %s start_date %s end_date %s' % (omnix_mas['sale_date'],omnix_mas['start_date'], omnix_mas['end_date']))

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
            'x_bank_name': contract['bank_branch'],
            'x_ceded_reference': contract['bank_reference'],
            'x_ceded_rental_id': x_ceded_rental_id,
            'recurring_next_date': '2019-05-31',  # ============== Remember to change this on 'go live' run
            'x_machine_ids': ''

        }
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
    # Lets create all the lots before we create the Machines as they need to reference the lot numbers
    with open(csv_file) as fp:
        i = 1
        for line in fp:  # Read one line at a time
            rntacc = []
            if i > 1:
                for col in line.split(','):  # Separate each rntacc in line
                    #rntacc.append(col.strip('"').strip(' '))
                    rntacc.append(col.strip())
                #print rntacc[7]
                #if rntacc[7]  not in ['A024',]: #'A009','A046'
                #    continue
                if rntacc[2]:
                    # print rntacc[2]
                    product_id = product_obj.search([('default_code', '=', rntacc[1])])
                    if product_id:
                        x = lot_obj.search([('name', '=', rntacc[2]), ('product_id', '=', product_id[0])])
                        if not x:
                            # print('About to created lot %s %s' % (rntacc[0],rntacc[2]))
                            lot_obj.create({'name': rntacc[2], 'product_id': product_id[0], 'ref': rntacc[0], 'company_id':1})
                    else:
                        print('Missing product ', rntacc[1], ' So will create it with serial number ', rntacc[2])
                        f.write('Missing product %s So will create it with serial number %s\n' % (rntacc[1], rntacc[2]))
                        vals = {'name': rntacc[1],
                                'default_code': rntacc[1],
                                'company_id': 1,

                                }
                        product_obj.create(vals)
                        product_id = product_obj.search([('default_code', '=', rntacc[1])])

                        vals = {'name': rntacc[2],
                                'product_id': product_id[0],
                                'ref': rntacc[0],
                                'company_id': 1,

                                }
                        lot = lot_obj.create(vals)
                    subscription = subscription_obj.browse([('name', '=', rntacc[0])])
                    print ('product_id=',product_id)
                    lot = lot_obj.browse([('name', '=', rntacc[2])])
                    SQL = "SELECT DISTINCT * FROM omnix_contracts WHERE contract_no = %s"
                    cur.execute(SQL % ("'" + rntacc[0] + "'"))
                    contracts = cur.fetchall()
                    if not contracts:
                        f.write("no contract found for %s\n" % (rntacc[0]))
                        #print("no contract found for %s\n" % (rntacc[0]))
                        continue
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
                        #vals['client_name'] = omnix_mas['contact_name']
                        #vals['client_email'] = omnix_mas['email']
                        #vals['client_phone'] = omnix_mas['contact_tellot']

                        lot.write(vals)
                        lot = lot_obj.browse([('name', '=', rntacc[2])])



                    # now link this Lot (which is a macine to the subscription record

                        print ('lot_id=', lot.id)
                        subscription.write({'x_machine_ids': [4,lot.id[0]] })

            i += 1
        print ("Finished Loading Serial #")

    return

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
                # print(rntmet)
                mac = machine_obj.search([('serial_number_id', '=', rntmet[0])])
                if mac:
                    for machine in machine_obj.browse(mac):
                        # print (rntmet[0],machine.name,machine.product_id.id)
                        product_tmpl_id = product_obj.browse(machine.product_id.id).product_tmpl_id
                        # print (product_tmpl_id)
                        product_tmpl = product_tmpl_obj.browse([('id', '=', product_tmpl_id.id)])
                        product_tmpl.write({
                            'categ_id': 3})  # Set the product category = 'machine' - this is used later in the software

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
            analytic_account = subscription_obj.search([('name', '=', contract['contract_no'])])
            if analytic_account:
                line_id = subscription_line_obj.search(
                    [('analytic_account_id', '=', analytic_account[0]), ('name', 'ilike', 'copies')])
                if line_id:
                    line = subscription_line_obj.browse(line_id)
                    line.write({'x_billing_frequency': contract['copy_frequency']})
                    line.write({'x_billing_hold': contract['hold_copy_frequency']})
                    print(contract['contract_no'], contract['copy_frequency'], contract['hold_copy_frequency'])
        if int(contract['rental_frequency']) > 1:
            analytic_account = subscription_obj.search([('name', '=', contract['contract_no'])])
            if analytic_account:
                line_id = subscription_line_obj.search(
                    [('analytic_account_id', '=', analytic_account[0]), ('name', '=', 'Monthly Rental')])
                if line_id:
                    line = subscription_line_obj.browse(line_id)
                    line.write({'x_billing_frequency': contract['rental_frequency']})
                    line.write({'x_billing_hold': contract['hold_rental_frequency']})
                    print(contract['contract_no'], contract['rental_frequency'], contract['hold_rental_frequency'])
        if int(contract['service_frequency']) > 1:
            analytic_account = subscription_obj.search([('name', '=', contract['contract_no'])])
            if analytic_account:
                line_id = subscription_line_obj.search(
                    [('analytic_account_id', '=', analytic_account[0]), ('name', '=', 'Monthly Service')])
                if line_id:
                    line = subscription_line_obj.browse(line_id)
                    line.write({'x_billing_frequency': contract['service_frequency']})
                    line.write({'x_billing_hold': contract['hold_service_frequency']})
                    print(contract['contract_no'], contract['service_frequency'], contract['hold_service_frequency'])


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
            if rntacc[7] != '\n' and rntacc[0] != 'Drs Accno':
                total_omnix += float(rntacc[7])
                id = account_obj.search([('origin', '=', rntacc[1])])
                if not id:
                    # print (data[0])
                    f.write('Missing invoice for contract %s in Odoo  - Omnix invoice number %s amount = %s\n' % (
                        rntacc[1], rntacc[2], rntacc[7]))
                    print('Missing invoice for contract %s in Odoo  - Omnix invoice number %s amount = %s\n' % (
                        rntacc[1], rntacc[2], rntacc[7]))
                    missing_diff += float(rntacc[7])
                    continue
                amt = account_obj.browse([id[0]]).amount_total

                difference = amt[0] - float(rntacc[7])
                if amt[0] != float(rntacc[7]):
                    difference = round(amt[0] - float(rntacc[7]), 2)
                    diff += difference

                    if difference == -0.01: continue
                    if difference > 0.01:
                        f.write('Contract=%s Omnix amt= %s Odoo amt= %s \n' % (rntacc[1], rntacc[7].strip(' '), amt[0]))
                        print ('Contract=%s Omnix amt= %s Odoo amt= %s  -----------------> Differenc=%s\n' % (
                            rntacc[1], rntacc[7].strip(' '), amt[0], difference))
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
    contract_numbers = []
    with open(csv_file) as fp:
        for line in fp:  # Read one line at a time
            col = line.split(',')  # Separate each rntacc in line

            contract_numbers.append(col[1])

        for rec in account_obj.browse([]):

            if rec.origin not in contract_numbers:
                print('missing invoice in Omnix for this contract ', rec.origin)
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
# _set_machine_categ_id()
# _create_linvoice_lines()

# _create_adminfee()
# _set_billing_frequency()


# _compare_omnix_odoo()
# _compare_odoo_omnix()

# _read_email()

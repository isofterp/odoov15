###################################################################################################

# To use this program, you must fisrt use the create_table.py to create the omnix_drsmas and
# omnix_contracts tables in the copytye database. These can be deleted once the system goes live

###################################################################################################

import erppeek
from datetime import datetime
from dateutil.relativedelta import relativedelta

import psycopg2
import psycopg2.extras
import pandas as pd
import numpy as np
version = 'V15'
#version = 'V14'

if version == 'V14':
    conn = psycopg2.connect("dbname=copyType-test user=odoo14ent")
    api = erppeek.Client('http://localhost:8014', 'copyType-test', 'admin', 'admin')
elif version == 'V15':
    conn = psycopg2.connect("host=172.16.12.32 dbname=copytype-test user=odoo15ent")
    api = erppeek.Client('http://172.16.12.32:8015', 'copytype-test', 'admin', '!$0ft')

cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)



#csv_path = "/Users/rolylautenbach/Customers/copytype/Omnix_Data/"
csv_path = "/tmp/Omnix_Data/"

drsmas = pd.read_csv(csv_path + 'drsmas.csv', dtype={"vat_no": str, "tel": str, "fax": str, "cell": str})
drsmas = drsmas.replace({np.nan: ''})
print(csv_path + 'rntmas.csv')
contracts = pd.read_csv(csv_path + 'rntmas.csv', index_col="drs_acc")
contracts = contracts.replace({np.nan: ''})

res_partner_obj = api.model('res.partner')
rental_group_obj = api.model('subscription.rental.group')
subscription_obj = api.model('sale.subscription')
subscription_line_obj = api.model('sale.subscription.line')
product_obj = api.model('product.product')
product_tmpl_obj = api.model('product.template')
lot_obj = api.model('stock.production.lot')
#acctab = pd.read_csv(csv_path + 'acctab.csv', index_col="acct_type", dtype={"acct_type": str})
acctab = pd.read_csv(csv_path + 'acctab.csv' )
acctab = acctab.replace({np.nan: ''})
acctab['description'] = acctab['description'].str.replace("'S CLIENT", "")
user_obj = api.model('res.users')

def _fix_date(old_date):
    # print (old_date,'day',old_date[8:10],'mnth', old_date[5:7],'yr',old_date[0:4])
    day = old_date[8:10]
    mnth = old_date[5:7]
    yr = old_date[0:4]
    if int(day) not in range(0, 32):
        print('Day problem', old_date, 'day', old_date[8:10], 'mnth', old_date[5:7], 'yr', old_date[0:4])
    if int(mnth) not in range(0, 13):
        print('Day problem', old_date, 'day', old_date[8:10], 'mnth', old_date[5:7], 'yr', old_date[0:4])
    if int(yr) not in range(1900, 2035):
        print('Year prolem ==============', old_date, 'day', old_date[8:10], 'mnth', old_date[5:7], 'yr', old_date[0:4])

    new_date = str(old_date).replace('/', '-')

    return new_date
def _create_reps_users():
    team_obj = api.model('crm.team')
    reps = pd.read_csv(csv_path + 'reptab.csv', index_col="rep_code", dtype={"rep_team": str})
    reps = reps.replace({np.nan: ''})

    """ First create users and partners for sales people from acctab.csv """
    "The below is not needed as the users are already created in the database"
    # for id, acctab_rec in acctab.iterrows():
    #     #print(id,acctab_rec['description'])
    #     user = user_obj.search([('name', 'ilike', acctab_rec['description'])])
    #     print('user=',user,acctab_rec['description'])
    #     if user:
    #         print('@68**********************')
    #         continue
    #     partner = res_partner_obj.create({'name': acctab_rec['description'],'company_id':1})
    #     vals = {'name': acctab_rec['description'],
    #             'login':acctab_rec['description'],
    #             'partner_id': partner.id
    #             }
    #     print(vals)
    #     user_obj.create(vals)
    exit()
    # Not adding users who are not linked to sales etc - maybe do manually
    for id, rep in reps.iterrows():
        if rep['rep_status'] == 'Enabled':
            user = user_obj.search([('name', '=',rep['name'])])
            #print('user=',user,rep['name'])
            if user:
                print('@83**********************')
                continue
            partner = res_partner_obj.create({'name': rep['name'], 'company_id': 1})
            vals = {'name': rep['name'],
                    'login': rep['name'],
                    'partner_id': partner.id
                    }
            # team = team_obj.search([('name', '=', rep['rep_team'])])
            # if team:
            #     team_x = team
            # else:
            #     team_obj.create({'name': rep['rep_team']})
            #     team = team_obj.search([('name', '=', rep['rep_team'])])
            # vals['sale_team_id'] = team[0]
            # print(vals)
            user_obj.create(vals)


def _create_cust_and_contracts():
    # drsdlv = pd.read_csv(csv_path + 'drsdlv.csv')
    # drsdlv = drsdlv.replace({np.nan: ''})
    f = open("Conversion_errors.txt", "w+")
    string = str(datetime.now()) + " Starting to create contracts\n"
    f.write(string)

    # Fix the terms table
    # for term in api.model('account.payment.term').browse([]):
    #     for line in term.line_ids:
    #         if term.id == 2:
    #             term.name = "30 Days"
    #             term.note = 'Payment Terms: 30 Days'
    #             line.days = 30
    #         if term.id == 3:
    #             term.name = "60 Days"
    #             term.note = 'Payment Terms: 60 Days'
    #             line.days = 60
    #         if term.id == 4:
    #             term.name = "90 Days"
    #             term.note = 'Payment Terms: 90 Days'
    #             line.days = 90
    #         if term.id == 5:
    #             term.name = "180 Days"
    #             term.note = 'Payment Terms: 180 Days'
    #             line.days = 180

    print("Starting to create Customers and Contracts\n")
    for drs_acc, contract in contracts.iterrows():
        if contract['prefix'] == 'D':  # This is a DEMO contract so ignore
            continue
        partner = res_partner_obj.search([('x_account_number', '=', drs_acc.upper())])
        print('@134',partner)
        if partner:
            # print('found partner == ', partner[0])
            partner_id = partner[0]
        else:
            drs_mas = drsmas.loc[(drsmas['drs_acc'].str.upper() == drs_acc.upper())]
            print('@135',drs_acc.upper(),partner)
            print('@136 acct_type',drs_mas['acct_type'].values[0])
            # Find the User in acct_tab based on the drsmas 'acct_type' field and return the description field which is the rep name
            user_name = acctab[acctab.acct_type == drs_mas['acct_type'].values[0]].description.item()
            #user_name = acctab.loc[(acctab['acct_type'] == drs_mas['acct_type'].values[0] )]
            print('user=',user_name)
            user_id = api.model('res.users').search([('name', 'ilike', user_name)])
            if not user_id:
                user_id = 2 # set to admin
            else:
                user_id = user_id[0]
            print('user_id',user_id)
            res = _prepare_partner_record(drs_mas,user_id)
            partner = res_partner_obj.create(res)
            partner_id = partner.id
            # Now create the Main Partner's Contact details
            # print ('HERE',drs_mas['con_acct_no'])
            # Now create Contact for this Partner
            # res = {'parent_id': partner_id,
            #        'type': 'contact',
            #        'name': drs_mas['contact'].values[0],
            #        'x_account_number':drs_acc,
            #        'phone': drs_mas['tel'].values[0],
            #        'email': drs_mas['email'].values[0],
            #        }
            # res_partner_obj.create(res)

        """ Now create the Subscription (Contract)  """
        sub = subscription_obj.search([('name', 'ilike', contract['contract_no'])])
        if not sub:
            # print 'sale date=',contract['sale_date']
            if contract['sale_date'] != '':
                date_start = contract['sale_date']
            else:
                date_start = contract['start_date']
            date_start = _fix_date(date_start)

            x_rental_group_id = ''
            if contract['rental_ceded'] != '':
                # print('rental_ceded',contract['rental_ceded'])
                ceded_id = rental_group_obj.search([('group_code', '=', int(contract['rental_ceded']))])
                if ceded_id:
                    # print ('Rental grp id=%s and rental_ceded=%s' % (ceded_id[0],contract['rental_ceded']))
                    x_ceded_rental_id = ceded_id[0]
            print(partner)
            res = {
                'name': contract['contract_no'],
                'code': contract['contract_no'],
                'partner_id': partner_id,
                'user_id': user_id,
                'date_start': date_start,
                'template_id': 1,  # Monthly Suscription Template
                # 'stage_id': 2,              # Set to 'In Progess go live'
                'recurring_next_date': '2023-09-28',  # ============== Remember to change this on 'go live' run
                'x_bank_name': contract['bank_name'] ,
                'x_ceded_reference': contract['bank_reference'] + '/' + contract['bank_branch'],
                'x_rental_group_id': x_ceded_rental_id,
                'x_add_hoc_increase': contract['increase'],
                'x_machine_ids': '',
                'stage_category': 'progress' # Check if this is not set when moving contracts to in progress
            }
            # print ('@ 216 Subscription',res)
            subscription_obj.create(res)


    f.write("Finised _create_cust_and_contracts\n")
    f.close()
    print("Finised Loading Contracts  ")

    return

def _create_analytic_history():
    analytic_acc_obj = api.model('account.analytic.account')
    analytic_acc_grp_obj = api.model('account.analytic.group')
    analytic_line_obj = api.model('account.analytic.line')
    csv_file = csv_path + "gp052023.csv"
    f = open("Conversion_errors.txt", "a+")
    f.write("Starting _create_analytic_history\n")
    contract_group = analytic_acc_grp_obj.search([('name', '=', 'Contracts')])
    print(contract_group[0])

    with open(csv_file) as fp:
        i = 1
        for line in fp:  # Read one line at a time
            gp = []
            if i > 1:
                for col in line.split(','):  # Separate each rntacc in line
                    gp.append(col.strip())

                account = analytic_acc_obj.search([('name', '=', gp[0])])
                if account:
                    account_id = account[0]
                else:
                    """ Create an Analytic account if it does not exist"""
                    analytic = analytic_acc_obj.create({'name': gp[0], 'group_id': contract_group[0]})
                    account_id = analytic.id
                    # print(account_id)
                """ Create an Analytic line for this account """
                analytic_line_obj.create({'name': 'Omnix BF ' + gp[1], 'account_id': account_id, 'amount': gp[4]})
                print('account_id=',account_id)
            i += 1
    f.write("Finished _create_analytic_history\n")
    analytic_ids = analytic_acc_obj.search([('balance','=',0.0)])
    for ids in analytic_ids:
        an_head = analytic_acc_obj.browse([('id','=',ids)])
        for an_line in an_head.line_ids:
            if an_line:
                print("Analytic name has line ", an_head.name, an_head.balance,an_line )
            else:
                print(("Analytic name has no lines ", an_head.name, an_head.balance,an_line ))
                an_head.unlink()

def _create_lots():
    analytic_acc_obj = api.model('account.analytic.account')
    analytic_acc_grp_obj = api.model('account.analytic.group')
    contract_group = analytic_acc_grp_obj.search([('name','=','Contracts')])
    csv_file = csv_path + "rntacc.csv"
    f = open("Conversion_errors.txt", "a+")
    f.write("Starting _create_lots\n")

    stkmas = pd.read_csv(csv_path + 'stkmas.csv')
    stkmas = stkmas.replace({np.nan: ''})

    product_id = product_tmpl_obj.search([('name', '=', 'Rental')])
    if not product_id:
        print(
            "missing Product Rental  Go to Subscriptions/Subscription Product and create one a Product called 'Rental' as a 'Service' and category as 'charge")
        exit()
    rental_product_id = product_id[0]
    machine_cat_id = api.model('product.category').search([('name', '=', 'main product')])
    if not machine_cat_id:
        print("missing Catergory 'main product' = Please  create one")
        exit()
    machine_cat_id = machine_cat_id[0]
    component_cat_id = api.model('product.category').search([('name', '=', 'component')])
    if not component_cat_id:
        print("missing Catergory 'component' = Please  create one")
        exit()
    component_cat_id = component_cat_id[0]
    product_id = product_tmpl_obj.search([('name', '=', 'Service charge')])
    if not product_id:
        print(
            "missing product Service charge  for contract Create it as a subscription product of type 'Service' "
            "category 'charge'")
        exit()
    service_product_id = product_id[0]
    # Let's create all the lot is a  Machine linked to a Subscription
    with open(csv_file) as fp:
        i = 1
        for line in fp:  # Read one line at a time
            rntacc = []
            if i > 1:
                for col in line.split(','):  # Separate each rntacc in line
                    rntacc.append(col.strip())
                ###################################################
                # if rntacc[0] not in ['11104810','5773'] :   #'11107052', 11107099
                #     continue
                ###################################################
                print('@256',rntacc)
                subscription = subscription_obj.browse([('name', '=', rntacc[0])])
                if not subscription:
                    print("missing Subscription %s ckeck Error File Conversion_errors.txt" % (rntacc[0]))
                    f.write("missing Subscription %s ckeck Error File Conversion_errors.txt" % (rntacc[0]))
                    continue

                if rntacc[2]:
                    SQL = "SELECT DISTINCT * FROM omnix_contracts WHERE contract_no = %s"
                    cur.execute(SQL % ("'" + rntacc[0] + "'"))
                    contracts = cur.fetchall()
                    if not contracts:
                        print("no contract found in omnix_contracts for %s\n" % (rntacc[0]))
                        f.write("no contract found in omnix_contracts for %s\n" % (rntacc[0]))
                        continue
                    product_id = product_obj.search([('default_code', '=', rntacc[1])])
                    if not product_id:
                        # print('Missing product ', rntacc[1], ' So will create it with serial number ', rntacc[2])
                        if rntacc[6] == '*':  # Main product
                            cat_id = machine_cat_id
                            tracking = 'serial'
                        else:
                            cat_id = component_cat_id
                            tracking = 'none'
                        stk_mas = stkmas.loc[(stkmas['stock_code'] == rntacc[1])]
                        if stk_mas.empty:
                            continue
                        # --------  we need to add the cost price to the product from stkmas
                        vals = {'name': stk_mas['description'].values[0],
                                'default_code': rntacc[1],
                                'type': 'product',
                                'categ_id': cat_id,
                                'company_id': 1,
                                'tracking': tracking
                                }
                        product_obj.create(vals)
                        product_id = product_obj.search([('default_code', '=', rntacc[1])])

                    # ################# Now create the lot record  ##################
                    lot = lot_obj.search([('name', '=', rntacc[2])])
                    if not lot:
                        if rntacc[6] == '*':
                            main = True
                        else:
                            main = False
                        vals = {
                            'name': rntacc[2],
                            'product_id': product_id[0],
                            'x_main_product': main,
                            'x_subscription_id': subscription[0],
                            'x_list_price': rntacc[5],
                            'x_cost_price': rntacc[4],
                            'company_id': 1,

                        }
                        for omnix_mas in contracts:
                            service_type_id = rental_group_obj.search(
                                [('group_type', '=', 'V'), ('group_code', '=', omnix_mas['service_type1'])])
                            print(service_type_id)
                            if service_type_id:
                                vals['x_service_type_id'] = service_type_id[0]

                            x_increase_copies_date = omnix_mas['copy_esc_date']
                            x_increase_copies_percent = omnix_mas['copy_esc_perc']
                            x_increase_service_date = omnix_mas['service_esc_date']
                            x_increase_service_percent = omnix_mas['service_esc_perc']
                            x_increase_rental_date = omnix_mas['rental_esc_date']
                            x_increase_rental_percent = omnix_mas['rental_esc_perc']
                            x_service_type = omnix_mas['service_type1']
                            if x_increase_copies_date is not None:
                                vals['x_increase_copies_date'] = _fix_date(x_increase_copies_date)
                            if x_increase_copies_percent:
                                vals['x_increase_copies_percent'] = x_increase_copies_percent
                            if x_increase_rental_date is not None:
                                vals['x_increase_rental_date'] = _fix_date(x_increase_rental_date)
                            if x_increase_rental_percent:
                                vals['x_increase_rental_percent'] = x_increase_rental_percent
                            if x_increase_service_date is not None:
                                vals['x_increase_service_date'] = _fix_date(x_increase_service_date)
                            if x_increase_service_percent:
                                vals['x_increase_service_percent'] = x_increase_service_percent

                            # Now look up the machine address in the drsdlv  table and add this address to the machine
                            # print('drs account -=',omnix_mas['drs_acc'], 'Addr=',omnix_mas['consumable_addr_code'])
                            if omnix_mas['consumable_addr_code']:
                                SQL = "SELECT DISTINCT * FROM drsdlv WHERE drsdlv_code = %s and drs_acc = %s"
                                cur.execute(SQL % (
                                "'" + omnix_mas['consumable_addr_code'] + "'", "'" + omnix_mas['drs_acc'] + "'"))
                                drsdlv = cur.fetchone()
                                # print('@344', drsdlv)
                                # drsdlv = drsdlv.loc[(drsdlv['drsdlv_code'] == int(omnix_mas['consumable_addr_code'])) & (drsdlv['drs_acc'] == omnix_mas['drs_acc'])]
                                if drsdlv:
                                    # print('found rec in DF',subscription[0].partner_id.id)
                                    res = {'name': drsdlv['contact'] or 'Unknown',
                                           'parent_id': subscription[0].partner_id.id,
                                           'type': 'delivery',
                                           'vat': drsdlv['zz_char05'],
                                           'street': drsdlv['addr1'],
                                           'street2': drsdlv['addr2'],
                                           'city': drsdlv['addr3'],
                                           'phone': drsdlv['tel'],
                                           'mobile': drsdlv['tel'],
                                           'x_fax': drsdlv['fax'],
                                           'x_account_number': drsdlv['drsdlv_code'],
                                           'email': omnix_mas['email']
                                           }
                                    dlv_id = res_partner_obj.search(
                                        [('name', '=', res['name']), ('parent_id', '=', res['parent_id'])])
                                    if dlv_id:  # Contact exsists so dont create again
                                        vals['x_dlv_id'] = dlv_id[0]
                                    else:
                                        dlv_id = res_partner_obj.create(res)
                                        vals['x_dlv_id'] = dlv_id.id

                            # now create and link this Lot (which is a machine to the subscription record
                            print('about to create lot with',vals)
                            lot_id = lot_obj.create(vals)

                            # Create an Analytic Account for this Lot and link Subscription
                            analytic = ''
                            if rntacc[6] == '*':     #main machine so create a analytic account
                                #print('@379',contract_group,analytic)
                                analytic = analytic_acc_obj.create(
                                    {'name': rntacc[2], 'partner_id': res['parent_id'], 'group_id': contract_group[0]})
                            subscription.write({'x_machine_ids': [(4, lot_id.id)],'analytic_account_id': analytic or False})


                    ## ############################ Create RENTAL lines if needs be  ############################
                    lot = lot_obj.search([('name', '=', rntacc[2])])
                    # print('*********', lot_id,rntacc[2] )
                    for omnix_mas in contracts:
                        if rntacc[6] == '*' and omnix_mas['monthly_rental'] != '0' and omnix_mas['end_date']:
                            # Create Subscription  Lines for this contract (rental line)
                            vals = {'analytic_account_id': subscription[0],        #This is confusing as the link fromthe line to master is the field analtyic_account_id
                                    'name': "Monthly Rental",
                                    'quantity': 1,
                                    'specific_price': omnix_mas['monthly_rental'],
                                    'price_unit': omnix_mas['monthly_rental'],
                                    'product_id': rental_product_id,
                                    'uom_id': 1,
                                    'x_serial_number_id': lot[0],
                                    }

                            grp = rental_group_obj.browse(
                                [('group_type', '=', 'C'), ('group_code', '=', omnix_mas['rental_ceded'])])
                            # print(grp.group_type,grp.group_code,grp.billable)
                            # print('bill=',billable,'renta_ceded=',omnix_mas['rental_ceded'],'end date',omnix_mas['end_date'])
                            if grp.billable[0] is True:
                                vals['x_start_date1_billable'] = False
                            else:
                                vals['x_start_date1_billable'] = True

                            vals['x_start_date1'] = _fix_date(omnix_mas['start_date'])
                            vals['x_end_date1'] = _fix_date(omnix_mas['end_date'])

                            subscription_line_obj.create(vals)

                        #############################  Create SERVICE  lines if needs be  ############################
                        if rntacc[6] == '*' and omnix_mas['service_amount'] > '0':  # Service amount
                            # print('In service lines')
                            if omnix_mas['service_start_date1'] is None:
                                # print ("Found  Service on contract no %s amount= %s date= %s" % (
                                # omnix_mas['contract_no'], omnix_mas['service_amount'],
                                # omnix_mas['service_start_date1']))
                                exit()
                            # print (product_id[0])

                            vals = {'analytic_account_id': subscription[0],
                                    'name': "Monthly Service",
                                    'quantity': 1,
                                    'specific_price': omnix_mas['service_amount'],
                                    'price_unit': omnix_mas['service_amount'],
                                    'product_id': service_product_id,
                                    'uom_id': 1,
                                    'x_serial_number_id': lot[0],
                                    'x_start_date1': _fix_date(omnix_mas['service_start_date1']),

                                    }
                            grp_id = rental_group_obj.search(
                                [('group_type', '=', 'V'), ('group_code', '=', omnix_mas['service_type1'])])
                            billable = rental_group_obj.browse(grp_id[0]).billable
                            vals['x_start_date1_billable'] = billable
                            # print('lot rec number=',lot[0],'Serial Number=',rntacc[2])
                            # print('@ 386',vals)
                            subscription_line_obj.create(vals)
                            # print ('Service omnix_masord created %s' % vals['name'])

            i += 1
        print("Finished _create_lots #")
        f.close()

    return

def _create_subscription_lines():
    f = open("Conversion_errors.txt", "a+")
    f.write("Starting _create_subscription_lines\n")
    print("Starting _create_subscription_lines\n")
    ## Now load a analytic invoice line for B&W and Coulor copies
    csv_file = csv_path + "rntcpc.csv"
    i = 0
    with open(csv_file) as fp:
        for line in fp:  # Read one line at a time
            rntcpc = []
            if i > 1:  # Skip the Header record
                for col in line.split(','):  # Separate each rntcpc in line
                    rntcpc.append(col.strip('"'))
                # if rntcpc[0] == '11109288':
                #    print('found it',rntcpc[0])
                # else:
                #    continue

                if rntcpc[1] == 'Colour copies' or rntcpc[1] == 'Black copies':
                    sub_rec = subscription_obj.browse([('code', 'ilike', rntcpc[0])])
                    if not sub_rec:
                        print('missing contract %s rntcpc[2]=%s' % (rntcpc[0], rntcpc[2]))
                        exit()
                    # print (" xx this should be the subscription id", sub_rec.id[0], len(sub_rec.x_machine_ids[0]))

                    rec = rental_group_obj.search([('group_type', '=', 'V'), ('group_code', '=', rntcpc[14])])
                    if rec:
                        bill = rental_group_obj.browse(rec[0]).billable
                        # print (bill)
                        # if not bill:
                        #    print ('no copies')

                    SQL = "SELECT DISTINCT * FROM omnix_contracts WHERE contract_no = %s"
                    cur.execute(SQL % ("'" + rntcpc[0] + "'"))
                    contracts = cur.fetchall()
                    for omnix_mas in contracts:
                        # print('contarct number',omnix_mas['contract_no'])
                        if omnix_mas['billing_type'] == '0' or omnix_mas['billing_type'] == '2':  # 0 = Rental & copies  2 = Copies only
                            product_id = product_obj.search([('name', 'ilike', rntcpc[1])])
                            if not product_id:
                                print('Missing product %s for contract %s\n' % (rntcpc[1], rntcpc[0]))
                                exit()

                            if product_id and sub_rec:
                                if sub_rec.x_machine_ids[0]:
                                    for lots in sub_rec.x_machine_ids:
                                        for lot in lots:
                                            if lot.x_main_product is True:
                                                s_id = lot.id
                                vals = {'analytic_account_id': sub_rec.id[0],
                                        'name': rntcpc[1],
                                        'quantity': 0,
                                        'product_id': product_id[0],
                                        'uom_id': 1,
                                        'specific_price': rntcpc[6],
                                        'price_unit': rntcpc[6],
                                        'x_copies_show': True,
                                        'x_copies_free': rntcpc[11],
                                        'x_copies_last': rntcpc[2],
                                        'x_copies_previous': rntcpc[2],
                                        'x_copies_vol_1': rntcpc[3],
                                        'x_copies_vol_2': rntcpc[4],
                                        'x_copies_price_1': rntcpc[6],
                                        'x_copies_price_2': rntcpc[7],
                                        'x_copies_price_3': rntcpc[8],
                                        'x_copies_minimum': rntcpc[9],
                                        'x_serial_number_id': s_id
                                        }
                                # if rntcpc[0] == '11105709':
                                #    print(vals)

                                # Find the Machine amongst all the equipment linked to this Subscription
                                # and load the serial number of the 'main product' onto the invoice line as a ref
                                # print(sub_rec.x_machine_ids)

                                if rntcpc[12]:
                                    vals.update({'x_start_date1': _fix_date(rntcpc[12])})
                                vals['x_start_date1_billable'] = True
                                grp_id = rental_group_obj.search(
                                    [('group_type', '=', 'V'), ('group_code', 'ilike', rntcpc[14])])  # copy_type1
                                if not grp_id:
                                    # print ('not grp_id  rntcpc[16]=%s' % (rntcpc[16]))
                                    vals['x_start_date1_billable'] = False
                                else:
                                    billable = rental_group_obj.browse(grp_id[0]).billable
                                    if billable:
                                        vals['x_start_date1_billable'] = True
                                # print (vals)
                                subscription_line_obj.create(vals)
            i += 1
    print("finished _create_subscription_lines")
    f.write("Finished _create_subscription_lines\n")
    f.close()

def _create_adminfee():
    f = open("Conversion_errors.txt", "a+")
    f.write("Starting to load Admin fees\n")
    print("Starting to load Admin fees\n")
    csv_file = csv_path + "outadminfee.csv"
    product_id = product_tmpl_obj.search([('name', '=', 'Admin fee')])
    if not product_id:
        print('No Admin fee recored - cerate one !')
        exit()
    with open(csv_file) as fp:
        i = 1
        for line in fp:  # Read one line at a time
            adminfee = []
            vals = []
            if i > 1:
                for col in line.split(','):  # Separate each adminfee in line
                    col = col.lstrip('0')
                    adminfee.append(col)
                # if  adminfee[1] != '1846':
                #    continue
                SQL = "SELECT DISTINCT copy_frequency FROM omnix_contracts WHERE contract_no = %s"
                cur.execute(SQL % ("'" + adminfee[1] + "'"))
                contracts = cur.fetchone()
                if not contracts: continue
                if contracts[0] == '0':  # only create Admin fee fot copies
                    continue
                sub_rec = subscription_obj.browse([('name', '=', adminfee[1])])
                if not sub_rec:
                    # f.write ("no contract found for %s in Admin file\n" % (adminfee[1]))
                    print("%s no contract found for %s in Admin file\n" % (i, adminfee[1]))
                    exit()

                # Create Subscriptio Lines for this contract's Admin fee
                if sub_rec.x_machine_ids[0]:
                    for lots in sub_rec.x_machine_ids:
                        for lot in lots:
                            if lot.x_main_product is True:
                                s_id = lot.id

                vals = {'analytic_account_id': sub_rec.id[0],
                        'name': "Admin Fee",
                        'quantity': 1,
                        'specific_price': adminfee[2],
                        'price_unit': adminfee[2],
                        'product_id': product_id[0],
                        'uom_id': 1,
                        'x_start_date1': "2019-04-01",
                        'x_start_date1_billable': True,
                        'x_serial_number_id': s_id
                        }
                subscription_line_obj.create(vals)
                vals['x_serial_number_id'] = ''
                print('Admin feee for %s' % adminfee[1])
            i += 1
        print("Finished loading Admin Fees")
        f.write("Finished loading Admin Fees\n")
        f.close()

def _set_billing_frequency():
    csv_file = csv_path + "rntmas.csv"
    f = open("Conversion_errors.txt", "a+")
    f.write("Starting to set billing frequency\n")
    print("Starting to set billing frequency\n")
    cur.execute("SELECT * FROM omnix_contracts ")
    contracts = cur.fetchall()
    for contract in contracts:
        if contract['contract_no'] == 'contract_no': continue  # skip first line
        subscription = subscription_obj.search([('code', '=', contract['contract_no'])])
        if subscription:
            if int(contract['copy_frequency']) > 1:
                # print(subscription[0])
                id = subscription_line_obj.search(
                    [('analytic_account_id', '=', subscription[0]), ('name', 'ilike', 'copies')])
                line = subscription_line_obj.browse(id[0])
                if line:
                    # print('copies',contract['contract_no'],contract['copy_frequency'],contract['hold_copy_frequency'])
                    line.x_billing_frequency = contract['copy_frequency']
                    line.x_billing_hold = contract['hold_copy_frequency']
            if int(contract['rental_frequency']) > 1:
                # print('Monthly Rental', contract['contract_no'], contract['rental_frequency'],contract['hold_rental_frequency'])
                id = subscription_line_obj.search(
                    [('analytic_account_id', '=', subscription[0]), ('name', '=', 'Monthly Rental')])
                line = subscription_line_obj.browse(id[0])
                if line:
                    line.x_billing_frequency = contract['rental_frequency']
                    line.x_billing_hold = contract['hold_rental_frequency']

            if int(contract['service_frequency']) > 1:
                # print('Monthly Service', contract['contract_no'], contract['service_frequency'],contract['hold_service_frequency'])
                id = subscription_line_obj.search(
                    [('analytic_account_id', '=', subscription[0]), ('name', '=', 'Monthly Service')])
                if id:
                    line = subscription_line_obj.browse(id[0])
                    if line:
                        line = subscription_line_obj.browse(id[0])
                        line.x_billing_frequency = contract['service_frequency']
                        line.x_billing_hold = contract['hold_service_frequency']
        else:
            print('subscription missing from Odoo ', contract['contract_no'])
            f.write('subscription missing from Odoo ' + contract['contract_no'])

    print('Finished Billing Frequency')

def _create_partners_without_contracts():
    for id, rec in drsmas.iterrows():
        if rec['bal_tot'] != int('0'):
            partner = res_partner_obj.search(
                [('name', '=', rec['name']), ('x_account_number', '=', rec['drs_acc'].upper())])
            if not partner:
                # print('this account must be created ',rec['name'],rec['bal_tot'])
                drs_mas = drsmas.loc[(drsmas['drs_acc'] == rec['drs_acc'].upper())]
                if len(drs_mas):
                    res = _prepare_partner_record(drs_mas,user_id[0])
                    partner = res_partner_obj.create(res)
                    print("partner created =", partner.name)
    return

def _prepare_partner_record(drs_mas,user_id):

    # if drs_mas['rep_code'].values[0] == 1:
    #     user_id = 2
    # else:
    #     user_id = api.model('res.users').search([('name', 'ilike', str(drs_mas['rep_code'].values[0]))])
    #     if user_id:
    #         user_id = user_id[0]
    #     else:
    #         user_id = 2

    # terms = ''
    # if drs_mas['terms_pmt'].values[0] == 0:
    #     terms = 1
    # if drs_mas['terms_pmt'].values[0] == 30:
    #     terms = 2
    # if drs_mas['terms_pmt'].values[0] == 60:
    #     terms = 3
    # if drs_mas['terms_pmt'].values[0] == 90:
    #     terms = 4
    # if drs_mas['terms_pmt'].values[0] == 180:
    #     terms = 5
    terms = 2
    rank = 1
    if drs_mas['sales_category'].values[0] == 'A':
        rank = 3
    if drs_mas['sales_category'].values[0] == 'B':
        rank = 2

    # print ('TERM=====',terms)
    email = drs_mas['email'].values[0]
    email = email.replace('##', ',')
    print(drs_mas['drs_acc'].values[0],drs_mas['drs_acc'])
    res = {'customer_rank': rank,
           'type': 'invoice',
           'is_company': 1,
           'user_id': user_id,
           'ref': drs_mas['contact'].values[0],
           'credit_limit': str(drs_mas['credit_limit'].values[0]),
           'property_payment_term_id': terms,
           'name': drs_mas['name'].values[0],
           'x_company_reg_no': drs_mas['zz_char04'].values[0],
           'x_account_number': drs_mas['drs_acc'].values[0].upper(),
           'street': drs_mas['addr1'].values[0],
           'street2': drs_mas['addr2'].values[0],
           'city': drs_mas['addr3'].values[0],
           'zip': str(drs_mas['pcode'].values[0]),
           'phone': str(drs_mas['tel'].values[0]),
           'x_fax': str(drs_mas['fax'].values[0]),
           'mobile': str(drs_mas['cell'].values[0]),
           'email': email,
           'vat': drs_mas["vat_no"].values[0]
           }
    # if drs_mas['tax_exempt'].value[0] == 'Yes':
    #     res['property_account_position_id'] = 1
    # print (res)
    return res

def _compare_omnix_odoo():
    f = open("/tmp/Omnix_Data/Conversion_errors.txt", "w+")
    f.write("Comparing Invoice Totals\n")
    csv_file = csv_path + "allmay2020.csv"
    account_obj = api.model('account.move')

    print("start compare results")
    i = 0
    diff = 0
    missing_diff = 0
    total_omnix = 0
    with open(csv_file) as fp:
        for line in fp:  # Read one line at a time
            rntacc = []
            for col in line.split(','):  # Separate each rntacc in line
                # print (f)
                rntacc.append(col.strip('"').strip(" "))
            if len(rntacc) == 8 and rntacc[0] != 'Drs Accno':
                total_omnix += float(rntacc[7])
                # print(rntacc[1])
                id = account_obj.search([('invoice_origin', '=', rntacc[1])])
                if not id:
                    # print (data[0])
                    f.write('Missing invoice for contract %s in Odoo  - Omnix invoice number %s amount = %s\n' % (
                        rntacc[1], rntacc[2], rntacc[7]))
                    print('Missing invoice for contract %s in Odoo  - Omnix Inv No %s amount = %s\n' % (
                        rntacc[1], rntacc[2], rntacc[7]))
                    missing_diff += float(rntacc[7])
                    continue
                amt = account_obj.browse([id[0]]).amount_total

                difference = amt[0] - float(rntacc[7])
                if amt[0] != float(rntacc[7]):
                    difference = round(amt[0] - float(rntacc[7]), 2)
                    diff += difference

                    if difference < -0.01:
                        f.write('Contract=%s Omnix amt= %s Odoo amt= %s Omnix invoice number %s\n' % (
                        rntacc[1], rntacc[7].strip(' '), amt[0], rntacc[2]))
                        print('Contract=%s Omnix amt= %s Odoo amt= %s ---> Differenc=%s\n' % (
                        rntacc[1], rntacc[7].strip(' '), amt[0], difference))
                    if difference > 0.01:
                        f.write('Contract=%s Omnix amt= %s Odoo amt= %s \n' % (rntacc[1], rntacc[7].strip(' '), amt[0]))
                        print('Contract=%s Omnix amt= %s Odoo amt= %s ---> Differenc=%s\n' % (
                        rntacc[1], rntacc[7].strip(' '), amt[0], difference))
        print('Total Invoice amt from Omnix = ', total_omnix)
        print('Total Diff = %s\n Missing diff= %s\n' % (diff, missing_diff))
        f.write('Total Invoice amt from Omnix = %s\n' % (total_omnix))

        f.write('Total Diff = %s\n Missing diff= %s\n' % (diff, missing_diff))
        f.close()

def _compare_odoo_omnix():
    f = open("Conversion_errors.txt", "a+")
    f.write("Comparing Invoice Totals\n")
    csv_file = csv_path + "allmay2020.csv"
    account_obj = api.model('account.move')

    print("start compare results")
    i = 0
    diff = 0
    missing_diff = 0
    total_omnix = 0
    contract_numbers = []
    with open(csv_file) as fp:
        for line in fp:  # Read one line at a time
            col = line.split(',')  # Separate each field in line
            contract_numbers.append(col[1].strip(" "))
        # print(contract_numbers,len(contract_numbers ))
        for rec in account_obj.browse([]):
            if rec.invoice_origin not in contract_numbers:
                print('missing invoice in Omnix for this contract ', rec.invoice_origin, rec.amount_total)
                missing_diff += rec.amount_total
        print('Total Invoice amt from Omnix = ', total_omnix)
        print('Total Diff = %s\n Missing diff= %s\n' % (diff, missing_diff))
        f.write('Total Invoice amt from Omnix = %s\n' % (total_omnix))

        f.write('Total Diff = %s\n Missing diff= %s\n' % (diff, missing_diff))
        f.close()

def _fix_bank_details():
    subscription_obj = api.model('sale.subscription')
    ids = subscription_obj.search([])
    # ids = subscription_obj.search([('x_bank_name','ilike','CTC')])
    for id in ids:
        rec  = subscription_obj.browse([id])
        if rec.x_bank_name[0]:
            pos = rec.x_bank_name[0].find('/SEE')
            if pos >= 0:
                # print(rec.x_bank_name)
                name = rec.x_bank_name[0][:pos]
                print(name)
                ref = rec.x_bank_name[0][pos + 1:]
                print('ref=', ref)
                rec.write({'x_bank_name': name, 'x_ceded_reference': rec.x_ceded_reference[0] + ' ' + ref})

            pos = rec.x_bank_name[0].find('/WAS')
            if pos >= 0:
                # print(rec.x_bank_name)
                name = rec.x_bank_name[0][:pos]
                print (name)
                ref = rec.x_bank_name[0][pos + 1:]
                print('ref=',ref)
                rec.write({'x_bank_name': name,'x_ceded_reference': rec.x_ceded_reference[0] + ' ' + ref})



def _update_cpc_charges_on_lots():
    analytic_acc_obj = api.model('account.analytic.account')
    analytic_acc_grp_obj = api.model('account.analytic.group')
    contract_group = analytic_acc_grp_obj.search([('name','=','Contracts')])
    csv_file = csv_path + "rntacc.csv"
    f = open("Conversion_errors.txt", "a+")
    f.write("Update CPC Charges On Lots\n")

    stkmas = pd.read_csv(csv_path + 'stkmas.csv')
    stkmas = stkmas.replace({np.nan: ''})

    product_id = product_tmpl_obj.search([('name', '=', 'Rental')])
    if not product_id:
        print(
            "missing Product Rental  Go to Subscriptions/Subscription Product and create one a Product called 'Rental' as a 'Service' and category as 'charge")
        exit()
    rental_product_id = product_id[0]
    machine_cat_id = api.model('product.category').search([('name', '=', 'main product')])
    if not machine_cat_id:
        print("missing Catergory 'main product' = Please  create one")
        exit()
    machine_cat_id = machine_cat_id[0]
    component_cat_id = api.model('product.category').search([('name', '=', 'component')])
    if not component_cat_id:
        print("missing Catergory 'component' = Please  create one")
        exit()
    component_cat_id = component_cat_id[0]
    product_id = product_tmpl_obj.search([('name', '=', 'Service charge')])
    if not product_id:
        print(
            "missing product Service charge  for contract Create it as a subscription product of type 'Service' "
            "category 'charge'")
        exit()
    service_product_id = product_id[0]
    # Let's create all the lot is a  Machine linked to a Subscription
    with open(csv_file) as fp:
        i = 1
        for line in fp:  # Read one line at a time
            rntacc = []
            if i > 1:
                for col in line.split(','):  # Separate each rntacc in line
                    rntacc.append(col.strip())
                ###################################################
                # if rntacc[0] not in ['11104810','5773'] :   #'11107052', 11107099
                #     continue
                ###################################################
                print('@256',rntacc)
                subscription = subscription_obj.browse([('name', '=', rntacc[0])])
                if not subscription:
                    print("missing Subscription %s ckeck Error File Conversion_errors.txt" % (rntacc[0]))
                    f.write("missing Subscription %s ckeck Error File Conversion_errors.txt" % (rntacc[0]))
                    continue

                if rntacc[2]:
                    SQL = "SELECT DISTINCT * FROM omnix_contracts WHERE contract_no = %s"
                    cur.execute(SQL % ("'" + rntacc[0] + "'"))
                    contracts = cur.fetchall()
                    if not contracts:
                        print("no contract found in omnix_contracts for %s\n" % (rntacc[0]))
                        f.write("no contract found in omnix_contracts for %s\n" % (rntacc[0]))
                        continue
                    product_id = product_obj.search([('default_code', '=', rntacc[1])])

                    # ################# Now update the lot record  ##################
                    #lot = lot_obj.search([('name', '=', rntacc[2])])
                    lot = lot_obj.search([('name','=', '3379PC05573')])
                    if lot:
                        print("Working with Lot %", lot)
                        vals = {}
                        if rntacc[6] == '*':
                            main = True
                        else:
                            main = False

                        for omnix_mas in contracts:
                            service_type_id = rental_group_obj.search(
                                [('group_type', '=', 'V'), ('group_code', '=', omnix_mas['service_type1'])])
                            print(service_type_id)
                            if service_type_id:
                                vals['x_service_type_id'] = service_type_id[0]

                            x_increase_copies_date = omnix_mas['copy_esc_date']
                            x_increase_copies_percent = omnix_mas['copy_esc_perc']
                            x_increase_service_date = omnix_mas['service_esc_date']
                            x_increase_service_percent = omnix_mas['service_esc_perc']
                            x_increase_rental_date = omnix_mas['rental_esc_date']
                            x_increase_rental_percent = omnix_mas['rental_esc_perc']
                            x_service_type = omnix_mas['service_type1']
                            if x_increase_copies_date is not None:
                                vals['x_increase_copies_date'] = _fix_date(x_increase_copies_date)
                            if x_increase_copies_percent:
                                vals['x_increase_copies_percent'] = x_increase_copies_percent
                            if x_increase_rental_date is not None:
                                vals['x_increase_rental_date'] = _fix_date(x_increase_rental_date)
                            if x_increase_rental_percent:
                                vals['x_increase_rental_percent'] = x_increase_rental_percent
                            if x_increase_service_date is not None:
                                vals['x_increase_service_date'] = _fix_date(x_increase_service_date)
                            if x_increase_service_percent:
                                vals['x_increase_service_percent'] = x_increase_service_percent

                            # Now look up the machine address in the drsdlv  table and add this address to the machine
                            # print('drs account -=',omnix_mas['drs_acc'], 'Addr=',omnix_mas['consumable_addr_code'])

                            # now create and link this Lot (which is a machine to the subscription record
                            print('about to update lot lot with',vals)
                            lot_id = lot_obj.wite(lot_id,vals)




                    ## ############################ Create RENTAL lines if needs be  ############################
                    # lot = lot_obj.search([('name', '=', rntacc[2])])
                    # print('*********', lot_id,rntacc[2] )
                    # for omnix_mas in contracts:
                    #     if rntacc[6] == '*' and omnix_mas['monthly_rental'] != '0' and omnix_mas['end_date']:
                    #         # Create Subscription  Lines for this contract (rental line)
                    #         vals = {'analytic_account_id': subscription[0],        #This is confusing as the link fromthe line to master is the field analtyic_account_id
                    #                 'name': "Monthly Rental",
                    #                 'quantity': 1,
                    #                 'specific_price': omnix_mas['monthly_rental'],
                    #                 'price_unit': omnix_mas['monthly_rental'],
                    #                 'product_id': rental_product_id,
                    #                 'uom_id': 1,
                    #                 'x_serial_number_id': lot[0],
                    #                 }
                    #
                    #         grp = rental_group_obj.browse(
                    #             [('group_type', '=', 'C'), ('group_code', '=', omnix_mas['rental_ceded'])])
                    #         # print(grp.group_type,grp.group_code,grp.billable)
                    #         # print('bill=',billable,'renta_ceded=',omnix_mas['rental_ceded'],'end date',omnix_mas['end_date'])
                    #         if grp.billable[0] is True:
                    #             vals['x_start_date1_billable'] = False
                    #         else:
                    #             vals['x_start_date1_billable'] = True
                    #
                    #         vals['x_start_date1'] = _fix_date(omnix_mas['start_date'])
                    #         vals['x_end_date1'] = _fix_date(omnix_mas['end_date'])
                    #
                    #         subscription_line_obj.create(vals)
                    #
                    #     #############################  Create SERVICE  lines if needs be  ############################
                    #     if rntacc[6] == '*' and omnix_mas['service_amount'] > '0':  # Service amount
                    #         # print('In service lines')
                    #         if omnix_mas['service_start_date1'] is None:
                    #             # print ("Found  Service on contract no %s amount= %s date= %s" % (
                    #             # omnix_mas['contract_no'], omnix_mas['service_amount'],
                    #             # omnix_mas['service_start_date1']))
                    #             exit()
                    #         # print (product_id[0])
                    #
                    #         vals = {'analytic_account_id': subscription[0],
                    #                 'name': "Monthly Service",
                    #                 'quantity': 1,
                    #                 'specific_price': omnix_mas['service_amount'],
                    #                 'price_unit': omnix_mas['service_amount'],
                    #                 'product_id': service_product_id,
                    #                 'uom_id': 1,
                    #                 'x_serial_number_id': lot[0],
                    #                 'x_start_date1': _fix_date(omnix_mas['service_start_date1']),
                    #
                    #                 }
                    #         grp_id = rental_group_obj.search(
                    #             [('group_type', '=', 'V'), ('group_code', '=', omnix_mas['service_type1'])])
                    #         billable = rental_group_obj.browse(grp_id[0]).billable
                    #         vals['x_start_date1_billable'] = billable
                    #         # print('lot rec number=',lot[0],'Serial Number=',rntacc[2])
                    #         # print('@ 386',vals)
                    #         subscription_line_obj.create(vals)
                    #         # print ('Service omnix_masord created %s' % vals['name'])

            i += 1
        print("Finished _updating_lots #")
        f.close()

    return

def _update_subscription_lines():
    f = open("Conversion_errors.txt", "a+")
    f.write("Starting _create_subscription_lines\n")
    print("Starting _create_subscription_lines\n")
    ## Now load a analytic invoice line for B&W and Coulor copies
    csv_file = csv_path + "rntcpc.csv"
    i = 0
    with open(csv_file) as fp:
        for line in fp:  # Read one line at a time
            rntcpc = []
            if i > 1:  # Skip the Header record
                for col in line.split(','):  # Separate each rntcpc in line
                    rntcpc.append(col.strip('"'))
                # if rntcpc[0] == '11109288':
                #    print('found it',rntcpc[0])
                # else:
                #    continue
                if rntcpc[0] == '11109856':
                    if rntcpc[1] == 'Colour copies' or rntcpc[1] == 'Black copies':
                        sub_rec = subscription_obj.browse([('code', 'ilike', rntcpc[0])])
                        if not sub_rec:
                            print('missing contract %s rntcpc[2]=%s' % (rntcpc[0], rntcpc[2]))
                            exit()
                        if sub_rec.name == '11109856':
                            print("Working with Contract", sub_rec.name)
                            # print (" xx this should be the subscription id", sub_rec.id[0], len(sub_rec.x_machine_ids[0]))

                            rec = rental_group_obj.search([('group_type', '=', 'V'), ('group_code', '=', rntcpc[14])])
                            if rec:
                                bill = rental_group_obj.browse(rec[0]).billable
                                # print (bill)
                                # if not bill:
                                #    print ('no copies')

                            SQL = "SELECT DISTINCT * FROM omnix_contracts WHERE contract_no = %s"
                            cur.execute(SQL % ("'" + rntcpc[0] + "'"))
                            contracts = cur.fetchall()
                            for omnix_mas in contracts:
                                # print('contarct number',omnix_mas['contract_no'])
                                if omnix_mas['billing_type'] == '0' or omnix_mas['billing_type'] == '2':  # 0 = Rental & copies  2 = Copies only
                                    product_id = product_obj.search([('name', 'ilike', rntcpc[1])])
                                    if not product_id:
                                        print('Missing product %s for contract %s\n' % (rntcpc[1], rntcpc[0]))
                                        exit()

                                    if product_id and sub_rec:
                                        if sub_rec.x_machine_ids[0]:
                                            for lots in sub_rec.x_machine_ids:
                                                for lot in lots:
                                                    if lot.x_main_product is True:
                                                        s_id = lot.id
                                        sub_line_id = subscription_line_obj.search([('analytic_account_id','=',sub_rec.id[0])])
                                        sub_line_rec = subscription_line_obj.browse([('id','=',sub_line_id),('product_id','=',product_id[0])])
                                        if sub_line_rec and sub_line_rec.product_id == rntcpc[1]:
                                            print("Contract is and product is",sub_line_rec.analytic_account_id.name,sub_line_rec.product_id.name  )
                                            vals = {
                                                    'specific_price': rntcpc[6],
                                                    'price_unit': rntcpc[6],
                                                    'x_copies_show': True,
                                                    'x_copies_free': rntcpc[11],
                                                    'x_copies_last': rntcpc[2],
                                                    'x_copies_previous': rntcpc[2],
                                                    'x_copies_vol_1': rntcpc[3],
                                                    'x_copies_vol_2': rntcpc[4],
                                                    'x_copies_price_1': rntcpc[6],
                                                    'x_copies_price_2': rntcpc[7],
                                                    'x_copies_price_3': rntcpc[8],
                                                    'x_copies_minimum': rntcpc[9],
                                                    'x_serial_number_id': s_id
                                                    }
                                        # if rntcpc[0] == '11105709':
                                        #    print(vals)

                                        # Find the Machine amongst all the equipment linked to this Subscription
                                        # and load the serial number of the 'main product' onto the invoice line as a ref
                                        # print(sub_rec.x_machine_ids)

                                        if rntcpc[12]:
                                            vals.update({'x_start_date1': _fix_date(rntcpc[12])})
                                        vals['x_start_date1_billable'] = True
                                        grp_id = rental_group_obj.search(
                                            [('group_type', '=', 'V'), ('group_code', 'ilike', rntcpc[14])])  # copy_type1
                                        if not grp_id:
                                            # print ('not grp_id  rntcpc[16]=%s' % (rntcpc[16]))
                                            vals['x_start_date1_billable'] = False
                                        else:
                                            billable = rental_group_obj.browse(grp_id[0]).billable
                                            if billable:
                                                vals['x_start_date1_billable'] = True
                                        # print (vals)
                                        sub_line_rec.write(vals)
            i += 1
    print("finished _create_subscription_lines")
    f.write("Finished _create_subscription_lines\n")
    f.close()


def _create_quants():
    print('creating quants')
    # Create quants for all products
    quant_obj = api.model('stock.quant')
    # lot_obj = api.model('stock.production.lot')
    ids = api.model('stock.production.lot').search([])
    for id in ids:
        rec = api.model('stock.production.lot').browse([id])
        print('lot ', rec.name,rec.id[0],rec.product_id.id[0])
        q = quant_obj.search([('lot_id', '=', rec.id)])
        if not q:
            # #print('creating quant for lot ', rec.name)
            quant_obj.create({'lot_id': rec.id[0], 'create_uid': 2,'company_id': 1,'product_id': rec.product_id.id[0], 'location_id': 8, 'quantity': -1}) # 8 is the location id for 'Stock'
            quant_obj.create({'lot_id': rec.id[0], 'create_uid': 2,'company_id': 1,'product_id': rec.product_id.id[0], 'location_id': 5, 'quantity': 1}) # 5 is the location id for 'Customers'
        else:
            print('quant already exists for lot ', rec.name)




# ================================== Run this progam one function at a time in the follwing sequence (Backup after each phase)=====================

print("running version ----------------------------> ",version)

"""This function is to fix Bank details"""
#_fix_bank_details() - No need to run
""""""
"""This is a fix to  add quants to already converted data. In future this will be done in the conversion program"""
########_create_quants() - No need to run this
""""""
####_create_reps_users() - Dont run this part!!!!!!!!!!!!!

# _create_cust_and_contracts() ###### 'recurring_next_date': '2020-01-31',  # ============== Remember to change this on 'go live' run

# _create_lots()

# _create_subscription_lines()

# _set_billing_frequency()

# _create_partners_without_contracts()

#_create_analytic_history()  ###### change the csv file name from modelgpXXXXXXX.csv to the latest

# _compare_omnix_odoo()

# _compare_odoo_omnix() - Dont run this

# _read_email()

_update_cpc_charges_on_lots()

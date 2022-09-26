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
                # print(line)
                for col in line.split(','):  # Separate each adminfee in line
                    adminfee.append(col.strip(' '))

                analytic_id = subscription_obj.search([('name', '=', adminfee[1])])
                if not analytic_id:
                    # f.write ("no contract found for %s in Admin file\n" % (adminfee[1]))
                    print("%s no contract found for %s in Admin file\n" % (i, adminfee[1]))
                    continue
                SQL = "SELECT name FROM account_analytic_invoice_line WHERE analytic_account_id = %s and (name = 'Black copies' OR name = 'Colour copies')"
                cur.execute(SQL % (analytic_id[0]))
                copies = cur.fetchall()
                # print(len(copies))
                if len(copies) == 0: continue  # No admin fees if Service only contract

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
                # print ('Admin feee for %s' % adminfee[1])
            i += 1
        print("Finished loading Admin Fees")
        f.write("Finished loading Admin Fees\n")
        f.close()
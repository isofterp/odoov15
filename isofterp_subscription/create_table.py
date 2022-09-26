import psycopg2
# This program is run fisrt in a series of programs.It creates tables which are
# then used to create output ????.csv file for imorting into OpenERP.
# YOU CAN ONLY PRODUCE ONE TABLE AT A TIME

# table_name = "drsdlv"
# csv_file = "/tmp/drsdlv.csv"
table_name = "omnix_contracts"
csv_file = "/tmp/rntmas.csv"
filein = open(csv_file)

conn = psycopg2.connect("dbname=copytype14 user=odoo14ent")
cur = conn.cursor()

headerline = [f.strip('"') for f in filein.readline().split(',')]

print ("This is the header line= ",headerline)

# This creates the table and adds all the fields from the input CSV file
create = 'y'
if  create == 'y':
    SQL = "DROP TABLE IF EXISTS %s"
    try:
        cur.execute(SQL %(table_name))
        print('dropped  table', table_name)
    except:
        print('could not drop table',table_name)
    
    SQL = "CREATE TABLE %s ()  WITH (OIDS=TRUE); ALTER TABLE %s OWNER TO odoo11;"
    try:
        cur.execute(SQL % (table_name,table_name))
    except:
        print ("could not create table",table_name)

    SQL = "ALTER TABLE %s ADD COLUMN %s text;"
    i = 0
    for value in  headerline:
        i = i + 1

        fieldName = value.strip('"')
        #fieldName = fieldName.strip(' ')
        #fieldName = fieldName.strip('%')
        #fieldName = fieldName.strip('#')
        print ('field name = %s with len= %s' % (fieldName, len(fieldName)))
        cur.execute(SQL % (table_name , fieldName))

print ("about to delete all previous data records")
SQL = "DELETE FROM %s;"    
cur.execute(SQL % (table_name))
print ("all previous data records deleted")

# Import all data into newly created Table based on Headerline fields.
SQL = "COPY %s FROM '%s' WITH CSV;"
cur.execute(SQL % (table_name,csv_file))

filein.close()
conn.commit() 
conn.close()
print ("Finished Loading data in table Omnix_contracts")
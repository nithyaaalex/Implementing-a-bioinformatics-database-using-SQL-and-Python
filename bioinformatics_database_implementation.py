#importing required libraries
import argparse
import sqlite3
import sys
import os
import matplotlib.pyplot as plt
import re

#setting argparse for command line interface
myparser = argparse.ArgumentParser(prog= "Database in Python using sqlite3", description = "To make a database from multi-omics data and to run some pre-determined queries on it", formatter_class = argparse.ArgumentDefaultsHelpFormatter)
myparser.add_argument('--createdb', default = False, action='store_true', help= "Creates a empty database with the name given")
myparser.add_argument('--loaddb', default = False, action='store_true', help= "Inserts relevant data into the database")
myparser.add_argument('--querydb', default = None, help= "Gives output from the database according to the query number specified")
myparser.add_argument('databasefilename', help= "The name of the database file to interact with")

args = myparser.parse_args()
#2933044.py --createdb --loaddb --querydb 2933044.db

#initializing global variables
age = []
bmi = []
data_for_sample = {}
data_for_biomolecule = {}
data_for_measurement = {}

#hardcoding file names for input
createdb_file = "createtable.txt"
querydb_file = "queries.txt"
subject_file = "Subject.csv"
metabolomics_file = "HMP_metabolome_abundance.tsv"
proteomics_file = "HMP_proteome_abundance.tsv"
transcriptomics_file = "HMP_transcriptome_abundance.tsv"
annotations_file = "HMP_metabolome_annotation.csv"

#checking if all files are accessible
files_to_check = [createdb_file,querydb_file,subject_file,metabolomics_file,proteomics_file,transcriptomics_file,annotations_file]
for file_name in files_to_check:
    try: 
        with open(file_name):
            pass  # File is accessible
    except FileNotFoundError:
        sys.exit(f'Input file {file_name} is not found. Please check the directory.')

#class to interface with sqlite3 database
class Database_Manager:
    def __init__(self, db_file):
        """
        Initialise the object with the filename of the sqlite database 
        """
        self.database_filename = db_file
    
    def createdb(self, query):
        """
        This function executes one or multiple CREATE statements using executescript on the database specified
        Keyword arguments:
        query -- can be one or multiple CREATE statements
        """
        connection = sqlite3.connect(self.database_filename)
        cursor = connection.cursor()
        error  = False
        #if no errors occur during creation of tables/database, the changes will be committed, else they'll be rolled back
        try:
            cursor.executescript(query)
        except Exception as e:
            connection.rollback()
            print(f"An exception has been encountered {e} and the create statements (DDL) did not complete")
            error = True
        if error == False:
            connection.commit()
        cursor.close()
        connection.close()

    def loaddb(self, query, parameters):
        """
        This function executes a group of INSERT queries on the database specified
        Keyword arguments:
        query -- INSERT statement 
        parameters -- list of (tuples of parameters) for the INSERT statement
        """
        connection = sqlite3.connect(self.database_filename)
        cursor = connection.cursor()
        error = False
        #if no errors occur during insertion, the changes will be committed, else they'll be rolled back
        try:
            cursor.executemany(query, parameters) #need to supply list of parameters as tuples
        except Exception as e:
            connection.rollback()
            print(f"An exception has been encountered {e} and the insert query with parameters did not complete")
            error = True
        if error == False:
            connection.commit()
        cursor.close()
        connection.close()
    
    def querydb(self, query):
        """
        This function executes a single sql SELECT query on the database specified and returns the result of the transaction
        It returns an iterable object with each line as a row retrived from the database
        Keyword arguments:
        query -- select statement 
        """
        connection = sqlite3.connect(self.database_filename)
        cursor = connection.cursor()
        rows = cursor.execute(query).fetchall()
        connection.commit()
        cursor.close()
        connection.close()
        return rows


#function that can be used to parse all 3 omics files and gather all the information required in dictionaries for their respective entity/table
def parse_files_to_store(input, omics_type):
    parameters = input.readline().rstrip('\n').rsplit('\t') #retrieving only the header
    column_names = parameters[1:] #this variable stores the BiomoleculeID

    #now iterating through rest of file
    for line in input:
        #for each line, seperating the first column which has the subject and visit id and further splitting it
        parameters = line.rstrip('\n').rsplit('\t') #rest of the abundances are stored here
        subjectid, visitid = parameters[0].rsplit('-') #splitting the sampleID into subjectid and visitid 

        #this if statement stores the parameters of the table Sample, and the subjectid-visitid are stored together as the key of the dictionary
        if parameters[0] not in data_for_sample: #if it's not already in the dictionary, this if adds the key-value pair to the dictionary
            data_for_sample[parameters[0]] = omics_type
        #if the sample is already saved with one omics type, it concatenates the string to add more omics types incase the sample was analysed for more than one omics type
        elif parameters[0] in data_for_sample:
            temp = data_for_sample[parameters[0]]
            temp = temp+","+omics_type 
            data_for_sample[parameters[0]] = temp

        column_count = 1 #to keep count of column
        for column in column_names: #iterating through each column of each row now

            #this part here is for storing the parameters of the table Biomolecule, 
            #same logic used for storing in the dict as table Sample, only the primary key is now BiomoleculeID which is the column
            if column not in data_for_biomolecule:
                data_for_biomolecule[column] = omics_type
            elif column in data_for_biomolecule:
                temp = data_for_biomolecule[column]
                temp = temp+","+omics_type
                data_for_biomolecule[column] = temp    

            #this part is for storing the parameters in BiomoleculeMeasurement
            key_tuple = (column, subjectid, visitid) #group the primary keys of table BiomoleculeMeasurement together to make it the key of the dictionary
            if key_tuple not in data_for_measurement:
                data_for_measurement[key_tuple] = parameters[column_count]  #storing all the parameters for Biomolecule Measurement
            column_count +=1

              
        

#main starts here
db_file = args.databasefilename
omics_database = Database_Manager(db_file) #creating an object of the database manager class

#using CLI input in if statements to determine what action is to be carried out

#action - creating database
if args.createdb == True: 
    with open(createdb_file) as create_table:
        create_query = create_table.read() #storing all the lines as one big string
    omics_database.createdb(create_query) #calling function createdb from object omics database

#action - inserting data into database 
elif args.loaddb == True:
    if os.path.isfile(db_file): #following only runs when a database file has already been created
        with open(subject_file) as input_file1: #the following code inserts data into table Subject
            next(input_file1) #skipping header
            final_parameters = [] #list of parameters for table Subject
            for line in input_file1:
                parameters = line.rstrip('\n').rsplit(',') #seperating by comma 
                count = 0
                for parameter in parameters:
                    if parameter=='Unknown' or parameter =='unknown' or parameter == 'NA':
                        parameters[count] = None #setting to none in case of unknown or NA value 
                    count+=1 #this counter is used to go through each column in the row
                final_parameters.append(tuple(parameters)) #converting into a tuple and appending to main list

            general_query = 'INSERT INTO Subject VALUES (?,?,?,?,?,?,?)' 
            omics_database.loaddb(general_query, final_parameters) #calling function loaddb from object omics database
        
        #opening each abundance file and using the parse_files_to_store function to store the parameters for insert queries in dictionaries(so that the keys are unique)
        with open(metabolomics_file) as input_file2:        
            omicstype = "metabolomics"
            parse_files_to_store(input_file2, omicstype) 
        with open(proteomics_file) as input_file3:
            omicstype = "proteomics"
            parse_files_to_store(input_file3, omicstype)
        with open(transcriptomics_file) as input_file4:
            omicstype = "transcriptomics"
            parse_files_to_store(input_file4, omicstype)
        
        #extracting information from the dictionary data_for_sample to convert it into a list of tuples appropriate to supply into the insert query placeholder
        #this is for the table Sample
        inserts_for_sample = []
        for sampleid, omic_type in data_for_sample.items():
            subjectid, visitid = sampleid.rsplit('-')
            inserts_for_sample.append((subjectid,visitid,omic_type)) #import to order it in the same order of attributes in the create table
        sample_query = 'INSERT INTO Sample VALUES (?,?,?)'
        omics_database.loaddb(sample_query, inserts_for_sample)

        #extracting information from the dictionary data_for_Biomolecule to convert it into a list of tuples appropriate to supply into the insert query placeholder
        #this is for the table Biomolecule           
        inserts_for_biomolecule = []
        for biomoleculeid, value in data_for_biomolecule.items():
            inserts_for_biomolecule.append((biomoleculeid,value))
        biomolecule_query = 'INSERT INTO Biomolecule VALUES (?,?)'
        omics_database.loaddb(biomolecule_query, inserts_for_biomolecule)

        #extracting information from the dictionary data_for_measurement to convert it into a list of tuples appropriate to supply into the insert query placeholder
        #this is for the table BiomoleculeMeasurement
        inserts_for_measurement = []
        for key_dict, value in data_for_measurement.items():
            a,b,c = key_dict #extracting the individual attributes from the key (had to combine to create primary key uniqueness)
            all_parameters = (a,b,c,value)
            inserts_for_measurement.append(all_parameters)
        measurement_query = 'INSERT INTO BiomoleculeMeasurement VALUES (?,?,?,?)'
        omics_database.loaddb(measurement_query, inserts_for_measurement)

        #opening the annotation file to insert its data into the Annotations table
        with open(annotations_file) as input_file5:
            next(input_file5) #skipping header
            final_parameters = []  #this list stores almost all annotations
            special_cases = [] #this list stores those annotations where one peak corresponds to multiple compounds
            for line in input_file5:
                parameters = line.rstrip('\n').rsplit(',') #this list has each parameter of the annotations table, peakid at 0 ,metabolite name at 1, etc
                count = 0 
                parameters[1] = re.sub(r'\(\d\)', '', parameters[1]) #removing the suffixes of compounds that are linked to multiple peaks - re matches pattern and subtracts it

                for parameter in parameters:
                    if parameter== '' or parameter == 'unknown':
                        parameters[count] = None #setting any unknown or empty parameters to none
                    count+=1 #to go through the columns

                match = re.search(r'\|', parameters[1]) 
                if match: #incase there are multiple compounds for one peak
                    try:
                        if parameters[2]: #checking if it is not none
                            first, second = parameters[2].rsplit("|") #splitting the compounds KEGG
                        else: #incase it is already None
                            first, second = None, None
                    except ValueError: #incase the KEGG isn't different for multiple compounds (there is no "|" in the other parameters (we only searched that it was there in metabolite name, KEGG and HMBD may or may not have multiple entries))
                        first = parameters[2]   
                        second = None
                    try: #similar logic as KEGG for splitting HMBD ID as well
                        if parameters[3]: 
                            third, fourth = parameters[3].rsplit("|")
                        else:
                            third, fourth = None, None
                    except ValueError:
                        third = parameters[3]
                        fourth = None

                    #creating two seperate tuples with appropriate metabolite name, KEGG, HMBD ID respectively
                    version1 = (parameters[0],parameters[1][0:match.start()],first,third, parameters[4], parameters[5])
                    version2 = (parameters[0],parameters[1][match.end():],second,fourth, parameters[4], parameters[5])
                    #saving to seperate list for manual checking and continuing loop
                    special_cases.append(version1)
                    special_cases.append(version2)
                    continue
                final_parameters.append(tuple(parameters)) #all other annotations get added here

            #print(special_cases)
                
            #inserting both the lists into the table one by one    
            general_query = 'INSERT INTO Annotations VALUES (?,?,?,?,?,?)'
            omics_database.loaddb(general_query, final_parameters)
            omics_database.loaddb(general_query, special_cases)
    else:
        print("Please create a database before loading data into it.")

#action - query the database
elif args.querydb is not None: #doesn't run unless a number is given at CLI 
    if os.path.isfile(db_file):# following runs only if a database file has already been created
        with open(querydb_file) as query_file:
            queries = query_file.readlines() #reads all the lines into a list, each element is one line

        line_number = int(args.querydb) #setting line number based on CLI input

        if line_number>0 and (line_number<=len(queries)): #making sure the input is within queries provided 
            line_that_has_query = queries[line_number - 1] #determining position of line in list
            query_output = omics_database.querydb(line_that_has_query) #calling querydb using object omics_database

            #following code is for appropriately formatting the output
            for row in query_output:
                if len(row) == 1: #for single column
                    first = row[0]
                    print(f"{first}")
                elif len(row) == 2: #two columns
                    first,second = row
                    print(f"{first}\t{second}")
                    if line_number == 9: #if it's query 9, storing it in a list for plotting later
                        age.append((int(first)))
                        bmi.append((int(second)))
                elif len(row) == 3: #three columns
                    first,second,third = row
                    print(f"{first}\t{second}\t{third}")
                else:
                    print(row) #just in case any other query like select * is needed for verification, unformatted output is given
            
        else: #just to tell the user incase they enter a number outside 1-9
            print("query number entered exceeds number of predetermined queries provided in input file. Please choose from 1-9.")
    else:
        print("Please create a database before you query it.")

#code for creating a plot if query 9 executes successfully and it's results are stored in the age and bmi lists
if (len(age)!=0) and (len(bmi)!=0):
    plt.scatter(age,bmi, color='blue')
    plt.xlabel('Age')
    plt.ylabel('BMI')
    plt.title('Scatter plot of Age vs BMI')
    plt.savefig('age_bmi_scatterplot.png')
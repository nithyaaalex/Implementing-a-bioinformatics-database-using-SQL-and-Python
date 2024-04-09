
Input files required:
1. The createtable.txt file with DDL statements.
2. The queries.txt file with DML statements, more can be added if needed.
3. 3 abundance files for metabolomics, proteomics and transcriptomics each.
4. Annotations file for the genes that are present in the abundance files.

How to run the program:
python <program>.py [–-createdb] [–-loaddb] [–-querydb=n] <SQLite database file>
1. The –-createdb option creates the database structure.
2. The –-loaddb option parses the data files and inserts the relevant data into the database. 
3. The –-querydb option runs one of the queries specified in the queries file on the created and loaded database. The argument n is a number from 1 to 9.

How the code runs:
1. Uses SQLite3 to interface with a SQL database.
2. Based on user input at the command line, it can create, load or query the database. (or all three at the same time.)
3. For creating, it uses the DDL statements provided to make the database file.
4. For loading, for this design, it extracts the data from the input files and stores it in the tables in the database.
5. Querying the database, based on user input of 1-9, it pulls that query from the query file and outputs the data to the console.


ER Diagram:
![image](https://github.com/nithyaaalex/Implementing-a-bioinformatics-database-using-SQL-and-Python/assets/151146371/75fd480c-6de3-415b-9dd2-02ac80f83c21)

Notes:
This program is very specific to this database design. 
Please don't load or query before creating this will throw an error, and don't query before loading, the output will be empty.


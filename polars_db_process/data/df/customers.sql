--{'model_code': 'chinook customers', 'db_conf': 'Chinook', 'name': 'chinook customers', 'where': ['1=1', "Email like 'A%"]}
SELECT LastName AS name, State AS state, PostalCode AS zip, Email AS mail
-- , Company, Address, City, Country, Phone, Fax, SupportRepId
FROM customers;

--{"model": "res.partner", "db_conf": "Chinook"}
SELECT LastName AS name, State AS state, PostalCode AS zip, Email AS mail
-- , Company, Address, City, Country, Phone, Fax, SupportRepId
FROM customers;

CREATE DATABASE jde;
CREATE USER jde WITH PASSWORD 'jde';
ALTER ROLE jde SET client_encoding TO 'utf8';
ALTER ROLE jde SET default_transaction_isolation TO 'read committed';
ALTER ROLE jde SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE jde TO jde;
\c jde;
CREATE EXTENSION postgis;
CREATE EXTENSION pg_trgm;
CREATE EXTENSION unaccent;
CREATE TEXT SEARCH CONFIGURATION french_unaccent( COPY = french );
ALTER TEXT SEARCH CONFIGURATION french_unaccent
ALTER MAPPING FOR hword, hword_part, word
WITH unaccent, french_stem;

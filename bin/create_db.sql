CREATE USER mle WITH PASSWORD 'mle';
ALTER ROLE mle SET client_encoding TO 'utf8';
ALTER ROLE mle SET default_transaction_isolation TO 'read committed';
ALTER ROLE mle SET timezone TO 'UTC';

CREATE DATABASE mledb;
ALTER DATABASE mledb OWNER TO mle;

GRANT ALL PRIVILEGES ON DATABASE mledb TO mle;

\c mledb;
CREATE EXTENSION postgis;
CREATE EXTENSION pg_trgm;
CREATE EXTENSION unaccent;
CREATE TEXT SEARCH CONFIGURATION french_unaccent( COPY = french );
ALTER TEXT SEARCH CONFIGURATION french_unaccent
ALTER MAPPING FOR hword, hword_part, word
WITH unaccent, french_stem;

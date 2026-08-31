-- ANSI-oriented DDL; adjust identity/boolean syntax for the target platform.
CREATE TABLE dim_date (
    date_key INTEGER PRIMARY KEY,
    calendar_date DATE NOT NULL UNIQUE,
    calendar_year INTEGER NOT NULL,
    calendar_quarter VARCHAR(2) NOT NULL,
    month_number INTEGER NOT NULL,
    month_name VARCHAR(12) NOT NULL,
    year_month VARCHAR(7) NOT NULL
);

CREATE TABLE dim_product (
    product_key INTEGER PRIMARY KEY,
    product_name VARCHAR(40) NOT NULL UNIQUE,
    product_description VARCHAR(200),
    portfolio VARCHAR(80) NOT NULL
);

CREATE TABLE dim_region (
    region_key INTEGER PRIMARY KEY,
    region_name VARCHAR(40) NOT NULL UNIQUE,
    operating_zone VARCHAR(30),
    latitude DECIMAL(9,6),
    longitude DECIMAL(9,6)
);

CREATE TABLE dim_claim_type (
    claim_type_key INTEGER PRIMARY KEY,
    claim_type_name VARCHAR(50) NOT NULL UNIQUE,
    cause_group VARCHAR(40) NOT NULL
);

CREATE TABLE dim_handler (
    handler_key INTEGER PRIMARY KEY,
    handler_name VARCHAR(50) NOT NULL UNIQUE,
    team_name VARCHAR(40) NOT NULL,
    experience_band VARCHAR(20),
    monthly_capacity INTEGER CHECK (monthly_capacity > 0)
);

CREATE TABLE dim_channel (
    channel_key INTEGER PRIMARY KEY,
    channel_name VARCHAR(30) NOT NULL UNIQUE,
    channel_group VARCHAR(30) NOT NULL
);

CREATE TABLE dim_supplier (
    supplier_key INTEGER PRIMARY KEY,
    supplier_name VARCHAR(60) NOT NULL UNIQUE,
    supplier_type VARCHAR(40),
    home_region_key INTEGER REFERENCES dim_region(region_key)
);

CREATE TABLE dim_status (
    status_key INTEGER PRIMARY KEY,
    claim_status VARCHAR(40) NOT NULL UNIQUE,
    stage_group VARCHAR(30) NOT NULL,
    status_order INTEGER NOT NULL,
    open_status_flag INTEGER NOT NULL CHECK (open_status_flag IN (0, 1))
);

CREATE TABLE dim_severity (
    severity_key INTEGER PRIMARY KEY,
    severity_band VARCHAR(20) NOT NULL UNIQUE,
    severity_order INTEGER NOT NULL,
    definition VARCHAR(80)
);

CREATE TABLE dim_risk (
    risk_key INTEGER PRIMARY KEY,
    risk_band VARCHAR(20) NOT NULL UNIQUE,
    risk_order INTEGER NOT NULL,
    definition VARCHAR(80)
);

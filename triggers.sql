
/* creating triggers to run in the background so we do not need to query and check for every insertion (automates the process)*/


CREATE OR REPLACE FUNCTION check_email_exists() RETURNS TRIGGER AS $$
BEGIN
    IF EXISTS (SELECT 1 FROM users WHERE email = NEW.email) THEN
        RAISE EXCEPTION 'Email already exists';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_check_email_exists
    BEFORE INSERT ON users
    FOR EACH ROW
    EXECUTE FUNCTION check_email_exists();


CREATE OR REPLACE FUNCTION check_password() RETURNS TRIGGER AS $$
BEGIN
    IF LENGTH(NEW.password) < 8 THEN
        RAISE EXCEPTION 'Password must be at least 8 characters long';
    END IF;
    IF NEW.password !~ '[a-z]' THEN
        RAISE EXCEPTION 'Password must contain at least 1 lowercase letter';
    END IF;
    IF NEW.password !~ '[A-Z]' THEN
        RAISE EXCEPTION 'Password must contain at least 1 uppercase letter';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_check_password
    BEFORE INSERT ON users
    FOR EACH ROW
    EXECUTE FUNCTION check_password();

CREATE OR REPLACE FUNCTION expenses_amount_check() 
RETURNS TRIGGER 
AS $$ 
BEGIN 
    IF NEW.amount <= 0 THEN 
        RAISE EXCEPTION 'Amount must be greater than zero'; 
    END IF; 
    RETURN NEW; 
END; 
$$ 
LANGUAGE plpgsql; 

CREATE TRIGGER expenses_amount_trigger 
BEFORE INSERT ON expenses 
FOR EACH ROW 
EXECUTE FUNCTION expenses_amount_check();



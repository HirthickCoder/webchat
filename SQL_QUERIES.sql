-- ============================================================
-- SQL QUERIES TO VIEW TABLES
-- Copy and paste these in MySQL Workbench
-- ============================================================

-- 1. SHOW ALL DATABASES
-- ============================================================
SHOW DATABASES;


-- 2. SELECT THE DATABASE
-- ============================================================
USE chatbot_db;


-- 3. SHOW ALL TABLES IN DATABASE
-- ============================================================
SHOW TABLES;


-- 4. VIEW TABLE STRUCTURE - LEADS
-- ============================================================
DESCRIBE leads;
-- OR
SHOW COLUMNS FROM leads;


-- 5. VIEW TABLE STRUCTURE - CHATBOTS
-- ============================================================
DESCRIBE chatbots;
-- OR
SHOW COLUMNS FROM chatbots;


-- 6. VIEW ALL DATA IN LEADS TABLE
-- ============================================================
SELECT * FROM leads;


-- 7. VIEW ALL DATA IN CHATBOTS TABLE
-- ============================================================
SELECT * FROM chatbots;


-- 8. VIEW LEADS WITH READABLE FORMAT
-- ============================================================
SELECT 
    userid,
    username,
    mailid,
    phonenumber,
    questions_asked,
    timestart,
    timeend,
    company_name
FROM leads
ORDER BY timestart DESC;


-- 9. COUNT TOTAL LEADS
-- ============================================================
SELECT COUNT(*) AS total_leads FROM leads;


-- 10. COUNT TOTAL CHATBOTS
-- ============================================================
SELECT COUNT(*) AS total_chatbots FROM chatbots;


-- 11. VIEW RECENT LEADS (Last 10)
-- ============================================================
SELECT 
    userid,
    username,
    mailid,
    phonenumber,
    company_name,
    timestart
FROM leads
ORDER BY timestart DESC
LIMIT 10;


-- 12. VIEW LEADS BY COMPANY
-- ============================================================
SELECT 
    company_name,
    COUNT(*) AS lead_count
FROM leads
GROUP BY company_name;


-- 13. SEARCH LEADS BY EMAIL
-- ============================================================
SELECT * FROM leads 
WHERE mailid LIKE '%@example.com%';


-- 14. VIEW ACTIVE CONVERSATIONS (timeend is NULL)
-- ============================================================
SELECT 
    userid,
    username,
    mailid,
    company_name,
    questions_asked,
    timestart
FROM leads
WHERE timeend IS NULL;


-- 15. VIEW COMPLETED CONVERSATIONS
-- ============================================================
SELECT 
    userid,
    username,
    mailid,
    company_name,
    questions_asked,
    timestart,
    timeend,
    TIMESTAMPDIFF(MINUTE, timestart, timeend) AS duration_minutes
FROM leads
WHERE timeend IS NOT NULL
ORDER BY timestart DESC;


-- 16. GET TABLE SIZE AND ROW COUNT
-- ============================================================
SELECT 
    table_name AS 'Table',
    table_rows AS 'Row Count',
    ROUND(((data_length + index_length) / 1024 / 1024), 2) AS 'Size (MB)'
FROM information_schema.TABLES
WHERE table_schema = 'chatbot_db'
ORDER BY (data_length + index_length) DESC;


-- 17. VIEW TABLE CREATION INFO
-- ============================================================
SHOW CREATE TABLE leads;
SHOW CREATE TABLE chatbots;


-- 18. VIEW INDEXES ON TABLES
-- ============================================================
SHOW INDEX FROM leads;
SHOW INDEX FROM chatbots;


-- 19. VERIFY DATABASE IS SELECTED
-- ============================================================
SELECT DATABASE();


-- 20. DELETE ALL DATA (TESTING ONLY - BE CAREFUL!)
-- ============================================================
-- TRUNCATE TABLE leads;      -- Removes all leads
-- TRUNCATE TABLE chatbots;   -- Removes all chatbots
-- DROP DATABASE chatbot_db;  -- Deletes entire database


-- ============================================================
-- QUICK START QUERIES (Most Common)
-- ============================================================

-- To quickly check everything:
USE chatbot_db;
SHOW TABLES;
SELECT COUNT(*) FROM leads;
SELECT COUNT(*) FROM chatbots;
SELECT * FROM leads ORDER BY timestart DESC LIMIT 5;

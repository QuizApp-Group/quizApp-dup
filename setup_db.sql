DROP USER IF EXISTS 'quizapp'@'localhost';
DROP DATABASE IF EXISTS quizapp;
DROP DATABASE IF EXISTS quizapp_test;

CREATE USER 'quizapp'@'localhost' IDENTIFIED BY 'foobar';
CREATE DATABASE quizapp;
CREATE DATABASE quizapp_test;
GRANT ALL ON quizapp.* TO 'quizapp'@'localhost';
GRANT ALL ON quizapp_test.* TO 'quizapp'@'localhost';

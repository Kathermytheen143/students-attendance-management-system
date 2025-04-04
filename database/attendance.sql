
CREATE DATABASE attendance;
USE attendance;
 drop database attendance;

-- Common structure for cs_stu_details and bca_stu_details
CREATE TABLE cs_stu_details (
    stu_roll_num VARCHAR(100),
    stu_name VARCHAR(100),
    class VARCHAR(100),
    pass VARCHAR(100),
    temp_present INT DEFAULT 0,
    temp_absent INT DEFAULT 0,
    present INT DEFAULT 0,
    absent INT DEFAULT 0,
    total_presents INT DEFAULT 0,
    total_days INT DEFAULT 0,
    percentagae varchar(100) default 0,
    mail_id varchar(100) default 0
);


insert into cs_stu_details(stu_roll_num,stu_name,class,pass,mail_id) values
("23PCS 4601","AKASH","CS","2001","kathermytheen143143@gmail.com"),
("23PCS 4602","DHANARAJ","CS","2002","kathermytheen143143@gmail.com"),
("23PCS 4603","DINESH","CS","2003","kathermytheen143143@gmail.com"),
("23PCS 4604","GUNALAN","CS","2004","kathermytheen143143@gmail.com"),
("23PCS 4605","HARI","CS","2005","kathermytheen143143@gmail.com");



CREATE TABLE bca_stu_details (
    stu_roll_num VARCHAR(100),
    stu_name VARCHAR(100),
    class VARCHAR(100),
    pass VARCHAR(100),
    temp_present INT DEFAULT 0,
    temp_absent INT DEFAULT 0,
    present INT DEFAULT 0,
    absent INT DEFAULT 0,
    total_presents INT DEFAULT 0,
    total_days INT DEFAULT 0,
    percentagae varchar(100) default 0,
    mail_id varchar(100) default 0
);



insert into bca_stu_details(stu_roll_num,stu_name,class,pass,mail_id) values
("23BCA 4601","BALA","BCA","2006","kathermytheen143143@gmail.com"),
("23BCA 4602","PALANI","BCA","2007","kathermytheen143143@gmail.com"),
("23BCA 4603","MURUGA","BCA","2008","kathermytheen143143@gmail.com"),
("23BCA 4604","SIVA","BCA","2009","kathermytheen143143@gmail.com"),
("23BCA 4605","DHANABAL","BCA","2010","kathermytheen143143@gmail.com");


-- Admin table
CREATE TABLE admins (
    aname VARCHAR(100),
    pass VARCHAR(100),
	allowed_table VARCHAR(100),
    role varchar(100)
);

insert into admins(aname,pass,allowed_table,role) values("sk","3001","cs_stu_details","superradmin"),
("ravi","3002","bca_stu_details","prof"),
("gn",3003,"cs_stu_details","prof"),
("sk","3001","bca_stu_details","superradmin"),
("sk","3001","cs_stu_details","superradmin"),
("gn",3003,"bca_stu_details","prof");

show tables;
select * from  admins;
drop table admins;
select * from admins;
select * from cs_stu_details_archive_2025_02_07;
select* from  cs_stu_details_archive_2025_02_04;
select* from  bca_stu_details_2025_01_21;



-- Admin table
-- Create the admins table
CREATE TABLE admins (
    id INT AUTO_INCREMENT PRIMARY KEY,  -- Adding an ID field for easier reference
    aname VARCHAR(100),
    pass VARCHAR(100),
    role VARCHAR(100)
);

-- Insert sample data into the admins table
insert into admins(aname, pass, role) 
values 
("sk", "3001", "superadmin"),
("ravi", "3002", "prof"),
("gn", "3003", "prof");

-- Create the allowed_tables table to store the relationship between admins and allowed tables
CREATE TABLE allowed_tables (
    admin_id INT,
    table_name VARCHAR(100),
    FOREIGN KEY (admin_id) REFERENCES admins(id)  -- Linking the admin_id to the admins table
);

-- Insert sample data into the allowed_tables table
insert into allowed_tables(admin_id, table_name) 
values 
(1, "cs_stu_details"),
(1, "bca_stu_details"),
(2, "bca_stu_details"),
(3, "cs_stu_details"),
(3, "bca_stu_details");


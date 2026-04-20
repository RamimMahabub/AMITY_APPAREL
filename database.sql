BEGIN TRANSACTION;
CREATE TABLE buyers (
	id INTEGER NOT NULL, 
	name VARCHAR(128) NOT NULL, 
	country VARCHAR(64), 
	contact_info VARCHAR(128), 
	PRIMARY KEY (id)
);
INSERT INTO "buyers" VALUES(1,'H&M','Sweden','contact@hm.com');
INSERT INTO "buyers" VALUES(2,'Zara','Spain','hello@zara.com');
CREATE TABLE dyeing_jobs (
	id INTEGER NOT NULL, 
	knitting_job_id INTEGER NOT NULL, 
	dyeing_unit_name VARCHAR(128) NOT NULL, 
	color_specification VARCHAR(64) NOT NULL, 
	input_qty NUMERIC(10, 2) NOT NULL, 
	output_qty NUMERIC(10, 2), 
	status VARCHAR(20), 
	PRIMARY KEY (id), 
	FOREIGN KEY(knitting_job_id) REFERENCES knitting_jobs (id)
);
CREATE TABLE knitting_jobs (
	id INTEGER NOT NULL, 
	yarn_purchase_id INTEGER NOT NULL, 
	company_name VARCHAR(128) NOT NULL, 
	sent_qty_kg NUMERIC(10, 2) NOT NULL, 
	received_fabric_kg NUMERIC(10, 2), 
	waste_kg NUMERIC(10, 2), 
	status VARCHAR(20), 
	PRIMARY KEY (id), 
	FOREIGN KEY(yarn_purchase_id) REFERENCES yarn_purchases (id)
);
CREATE TABLE orders (
	id INTEGER NOT NULL, 
	buyer_id INTEGER NOT NULL, 
	product_name VARCHAR(128) NOT NULL, 
	design_image VARCHAR(256), 
	total_qty INTEGER NOT NULL, 
	deadline DATETIME NOT NULL, 
	status VARCHAR(20), 
	PRIMARY KEY (id), 
	FOREIGN KEY(buyer_id) REFERENCES buyers (id)
);
INSERT INTO "orders" VALUES(1,1,'Basic T-Shirt',NULL,10000,'2026-03-31 20:24:10.077840','Active');
INSERT INTO "orders" VALUES(2,2,'Summer Polo',NULL,5000,'2026-04-07 20:24:10.079580','Active');
CREATE TABLE production_stages (
	id INTEGER NOT NULL, 
	order_id INTEGER NOT NULL, 
	stage_name VARCHAR(64) NOT NULL, 
	input_qty INTEGER NOT NULL, 
	output_qty INTEGER NOT NULL, 
	waste INTEGER NOT NULL, 
	status VARCHAR(20), 
	PRIMARY KEY (id), 
	FOREIGN KEY(order_id) REFERENCES orders (id)
);
CREATE TABLE shipments (
	id INTEGER NOT NULL, 
	order_id INTEGER NOT NULL, 
	container_no VARCHAR(64) NOT NULL, 
	shipping_date DATETIME, 
	final_qty INTEGER NOT NULL, 
	status VARCHAR(20), 
	PRIMARY KEY (id), 
	FOREIGN KEY(order_id) REFERENCES orders (id)
);
CREATE TABLE suppliers (
	id INTEGER NOT NULL, 
	name VARCHAR(128) NOT NULL, 
	contact_person VARCHAR(64), 
	phone VARCHAR(32), 
	email VARCHAR(120), 
	address TEXT, 
	PRIMARY KEY (id)
);
INSERT INTO "suppliers" VALUES(1,'Global Yarns Ltd','John Doe','123-456','john@globalyarns.com','Dhaka');
INSERT INTO "suppliers" VALUES(2,'Premium Threads Inc','Jane Smith','987-654','jane@premiumthreads.com','Chattogram');
CREATE TABLE users (
	id INTEGER NOT NULL, 
	username VARCHAR(64) NOT NULL, 
	email VARCHAR(120) NOT NULL, 
	password_hash VARCHAR(256) NOT NULL, 
	role VARCHAR(20) NOT NULL, 
	PRIMARY KEY (id)
);
INSERT INTO "users" VALUES(1,'admin','admin@amityapparel.com','scrypt:32768:8:1$e0OzolQwOm36AS6m$deef05aff0a39208182cc6af83b0caee065e138792a908a838b93ce56f929f2b216034f9eecf7b2a35f5dac492342a40beec3591e56dc5da4992bf68621447a3','Admin');
INSERT INTO "users" VALUES(2,'manager','manager@amityapparel.com','scrypt:32768:8:1$V9icAO1TG8hLxX97$8146d018915f92d5d70a1f5f1f8a2cdc8fbff2a6359f047347b130d95e2b90e9515890db32bf3aed18bdb650d98fea25652c5bc34a0b4015d1e5194fa37a6289','Manager');
INSERT INTO "users" VALUES(3,'staff','staff@amityapparel.com','scrypt:32768:8:1$T9GfHqRFt1CqNNP9$c0a489493349f22ef757cea993388d07bde865bf0fb1c3e4752e7d367ee8a3bdbc75e95e15f5adcd0c9d5553483f703f91b3964fe0e625e0bfd4b6a24fff01da','Staff');
CREATE TABLE yarn_purchases (
	id INTEGER NOT NULL, 
	supplier_id INTEGER NOT NULL, 
	yarn_type VARCHAR(64) NOT NULL, 
	color VARCHAR(64) NOT NULL, 
	qty_kg NUMERIC(10, 2) NOT NULL, 
	price_per_kg NUMERIC(10, 2) NOT NULL, 
	status VARCHAR(20), 
	created_at DATETIME, 
	PRIMARY KEY (id), 
	FOREIGN KEY(supplier_id) REFERENCES suppliers (id)
);
INSERT INTO "yarn_purchases" VALUES(1,1,'Cotton 30s','Raw White',5000,3.5,'Received','2026-03-28 20:24:10.047361');
INSERT INTO "yarn_purchases" VALUES(2,2,'Polyester 20d','Black',2000,2.8,'Received','2026-03-28 20:24:10.047379');
CREATE UNIQUE INDEX ix_users_username ON users (username);
CREATE UNIQUE INDEX ix_users_email ON users (email);
COMMIT;

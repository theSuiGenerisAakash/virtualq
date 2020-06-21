
-- Drop table

-- DROP TABLE business;

CREATE TABLE business (
	id uuid NOT NULL DEFAULT uuid_generate_v4(),
	"name" varchar(255) NOT NULL,
	email varchar(255) NOT NULL,
	username varchar(255) NOT NULL,
	"password" varchar(255) NOT NULL,
	phone_no varchar(255) NOT NULL,
	url varchar(255) NOT NULL,
	created_at timestamp NOT NULL DEFAULT now(),
	updated_at timestamp NULL,
	deleted_at timestamp NULL,
	CONSTRAINT "PK_0bd850da8dafab992e2e9b058e5" PRIMARY KEY (id)
);

-- Drop table

-- DROP TABLE customer;

CREATE TABLE customer (
	id uuid NOT NULL DEFAULT uuid_generate_v4(),
	"name" varchar(255) NOT NULL,
	phone_no varchar(255) NOT NULL,
	created_at timestamp NOT NULL DEFAULT now(),
	updated_at timestamp NULL,
	deleted_at timestamp NULL,
	CONSTRAINT "PK_a7a13f4cacb744524e44dfdad32" PRIMARY KEY (id),
	CONSTRAINT customer_phone_no_unique UNIQUE (phone_no)
);

-- Drop table

-- DROP TABLE queue_status;

CREATE TABLE queue_status (
	id uuid NOT NULL DEFAULT uuid_generate_v4(),
	business_queue_id uuid NOT NULL,
	queue _uuid NOT NULL DEFAULT ARRAY[]::uuid[],
	created_at timestamp NOT NULL DEFAULT now(),
	updated_at timestamp NULL,
	deleted_at timestamp NULL,
	CONSTRAINT "PK_1aa45156bd9ec2b4fc905860fff" PRIMARY KEY (id),
	CONSTRAINT fk_businessqueue_qs UNIQUE (business_queue_id)
);

-- Drop table

-- DROP TABLE queue_type;

CREATE TABLE queue_type (
	id uuid NOT NULL DEFAULT uuid_generate_v4(),
	"type" varchar(255) NOT NULL,
	CONSTRAINT "PK_6a44adcd023730aa29350bdb397" PRIMARY KEY (id),
	CONSTRAINT "UQ_52f3ee01501ab825a7d1256e956" UNIQUE (type)
);

-- Drop table

-- DROP TABLE business_queue;

CREATE TABLE business_queue (
	id uuid NOT NULL DEFAULT uuid_generate_v4(),
	business_id uuid NOT NULL,
	queue_id uuid NOT NULL,
	"name" varchar(255) NOT NULL,
	"isEnabled" bool NOT NULL DEFAULT true,
	max_queue_length int4 NULL DEFAULT 50,
	created_at timestamp NOT NULL DEFAULT now(),
	updated_at timestamp NULL,
	deleted_at timestamp NULL,
	CONSTRAINT "PK_2bd45b59df5489b01bb751c678e" PRIMARY KEY (id),
	CONSTRAINT composite_business_queue_key UNIQUE (business_id, queue_id),
	CONSTRAINT fk_business_bq FOREIGN KEY (business_id) REFERENCES business(id) ON UPDATE CASCADE,
	CONSTRAINT fk_queue_bq FOREIGN KEY (queue_id) REFERENCES queue_type(id) ON UPDATE CASCADE
);

-- Drop table

-- DROP TABLE customer_queue;

CREATE TABLE customer_queue (
	id uuid NOT NULL DEFAULT uuid_generate_v4(),
	customer_id uuid NOT NULL,
	business_queue_id uuid NOT NULL,
	otp varchar(6) NOT NULL,
	created_at timestamp NOT NULL DEFAULT now(),
	updated_at timestamp NULL,
	deleted_at timestamp NULL,
	is_registered bool NOT NULL DEFAULT false,
	CONSTRAINT "PK_e7c5bcb9d9f5346a7132d8952c6" PRIMARY KEY (id),
	CONSTRAINT customer_queue_unique UNIQUE (customer_id, business_queue_id),
	CONSTRAINT customer_queue_fk FOREIGN KEY (business_queue_id) REFERENCES business_queue(id) ON UPDATE CASCADE,
	CONSTRAINT customer_queue_fk_1 FOREIGN KEY (customer_id) REFERENCES customer(id) ON UPDATE CASCADE
);

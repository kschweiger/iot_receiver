-- Postgres 14
CREATE SCHEMA iot_receiver;

CREATE TABLE iot_receiver.senders (
	"id" SERIAL PRIMARY KEY,
	"sender_name" VARCHAR(50) NOT NULL,
	"hashed_key" VARCHAR(50) NOT NULL
);

CREATE TABLE iot_receiver.endpoint_request_subsets (
	"id" INT NOT NULL,
	"endpoint" VARCHAR(50) NOT NULL,
	"subset" JSON NOT NULL,
	FOREIGN KEY("id")
 	REFERENCES iot_receiver.senders("id")
)
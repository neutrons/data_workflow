------------------------------------------------------------------
-- My2Pg 1.32 translated dump
--
------------------------------------------------------------------

BEGIN;


-- MySQL dump 10.13  Distrib 5.5.24, for Linux (x86_64)
--
-- Host: mac83808.ornl.gov    Database: reporting_db
-- ------------------------------------------------------
-- Server version	5.5.27
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO,POSTGRESQL' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table "auth_group"
--

;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE "auth_group" (
  "id" INT4 NOT NULL,
  "name" varchar(80) NOT NULL,
  PRIMARY KEY ("id")

);
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table "django_content_type"
--

;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE "django_content_type" (
  "id" INT4 NOT NULL,
  "name" varchar(100) NOT NULL,
  "app_label" varchar(100) NOT NULL,
  "model" varchar(100) NOT NULL,
  PRIMARY KEY ("id")

);
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table "auth_permission"
--

;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE "auth_permission" (
  "id" INT4 NOT NULL,
  "name" varchar(50) NOT NULL,
  "content_type_id" INT4 NOT NULL,
  "codename" varchar(100) NOT NULL,
  PRIMARY KEY ("id"),
  FOREIGN KEY ("content_type_id") REFERENCES "django_content_type" ("id")
);
/*!40101 SET character_set_client = @saved_cs_client */;
--
-- Table structure for table "auth_group_permissions"
--

;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE "auth_group_permissions" (
  "id" INT4 NOT NULL,
  "group_id" INT4 NOT NULL,
  "permission_id" INT4 NOT NULL,
  PRIMARY KEY ("id"),

  FOREIGN KEY ("group_id") REFERENCES "auth_group" ("id"),
  FOREIGN KEY ("permission_id") REFERENCES "auth_permission" ("id")
);
/*!40101 SET character_set_client = @saved_cs_client */;


--
-- Table structure for table "auth_user"
--

;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE "auth_user" (
  "id" INT4 NOT NULL,
  "username" varchar(30) NOT NULL,
  "first_name" varchar(30) NOT NULL,
  "last_name" varchar(30) NOT NULL,
  "email" varchar(75) NOT NULL,
  "password" varchar(128) NOT NULL,
  "is_staff" INT2 NOT NULL,
  "is_active" INT2 NOT NULL,
  "is_superuser" INT2 NOT NULL,
  "last_login" TIMESTAMP NOT NULL,
  "date_joined" TIMESTAMP NOT NULL,
  PRIMARY KEY ("id")

);
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table "auth_user_groups"
--

;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE "auth_user_groups" (
  "id" INT4 NOT NULL,
  "user_id" INT4 NOT NULL,
  "group_id" INT4 NOT NULL,
  PRIMARY KEY ("id"),

  FOREIGN KEY ("user_id") REFERENCES "auth_user" ("id"),
  FOREIGN KEY ("group_id") REFERENCES "auth_group" ("id")
);
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table "auth_user_user_permissions"
--

;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE "auth_user_user_permissions" (
  "id" INT4 NOT NULL,
  "user_id" INT4 NOT NULL,
  "permission_id" INT4 NOT NULL,
  PRIMARY KEY ("id"),

  FOREIGN KEY ("user_id") REFERENCES "auth_user" ("id"),
  FOREIGN KEY ("permission_id") REFERENCES "auth_permission" ("id")
);
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table "db_datarun"
--

;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE "db_datarun" (
  "id" INT4 NOT NULL,
  "run_number" INT4 NOT NULL,
  "created_on" TIMESTAMP NOT NULL,
  PRIMARY KEY ("id")

);
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table "db_statusinfo"
--

;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE "db_statusinfo" (
  "id" INT4 NOT NULL,
  "name" varchar(100) NOT NULL,
  PRIMARY KEY ("id")

);
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table "db_runstatus"
--

;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE "db_runstatus" (
  "id" INT4 NOT NULL,
  "run_id_id" INT4 NOT NULL,
  "queue_id_id" INT4 NOT NULL,
  "message_id" varchar(100) DEFAULT NULL,
  "created_on" TIMESTAMP NOT NULL,
  PRIMARY KEY ("id"),

  FOREIGN KEY ("run_id_id") REFERENCES "db_datarun" ("id"),
  FOREIGN KEY ("queue_id_id") REFERENCES "db_statusinfo" ("id")
);
/*!40101 SET character_set_client = @saved_cs_client */;


--
-- Table structure for table "django_admin_log"
--

;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE "django_admin_log" (
  "id" INT4 NOT NULL,
  "action_time" TIMESTAMP NOT NULL,
  "user_id" INT4 NOT NULL,
  "content_type_id" INT4 DEFAULT NULL,
  "object_id" text,
  "object_repr" varchar(200) NOT NULL,
  "action_flag" INT2  NOT NULL,
  "change_message" text NOT NULL,
  PRIMARY KEY ("id"),

  FOREIGN KEY ("content_type_id") REFERENCES "django_content_type" ("id"),
  FOREIGN KEY ("user_id") REFERENCES "auth_user" ("id")
);
/*!40101 SET character_set_client = @saved_cs_client */;
--
-- Table structure for table "django_session"
--

;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE "django_session" (
  "session_key" varchar(40) NOT NULL,
  "session_data" text NOT NULL,
  "expire_date" TIMESTAMP NOT NULL,
  PRIMARY KEY ("session_key")

);
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table "django_site"
--

;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE "django_site" (
  "id" INT4 NOT NULL,
  "domain" varchar(100) NOT NULL,
  "name" varchar(50) NOT NULL,
  PRIMARY KEY ("id")

);
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table "report_instrument"
--

;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE "report_instrument" (
  "id" INT4 NOT NULL,
  "name" varchar(20) NOT NULL,
  PRIMARY KEY ("id")

);
/*!40101 SET character_set_client = @saved_cs_client */;


--
-- Table structure for table "report_ipts"
--

;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE "report_ipts" (
  "id" INT4 NOT NULL,
  "expt_name" varchar(20) NOT NULL,
  "created_on" TIMESTAMP NOT NULL,
  PRIMARY KEY ("id")

);
/*!40101 SET character_set_client = @saved_cs_client */;
--
-- Table structure for table "report_datarun"
--

;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE "report_datarun" (
  "id" INT4 NOT NULL,
  "run_number" INT4 NOT NULL,
  "ipts_id_id" INT4 NOT NULL,
  "instrument_id_id" INT4 NOT NULL,
  "file" varchar(128) NOT NULL,
  "created_on" TIMESTAMP NOT NULL,
  PRIMARY KEY ("id"),

  FOREIGN KEY ("instrument_id_id") REFERENCES "report_instrument" ("id"),
  FOREIGN KEY ("ipts_id_id") REFERENCES "report_ipts" ("id")
);
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table "report_statusqueue"
--

;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE "report_statusqueue" (
  "id" INT4 NOT NULL,
  "name" varchar(100) NOT NULL,
  PRIMARY KEY ("id")

);
/*!40101 SET character_set_client = @saved_cs_client */;


--
-- Table structure for table "report_runstatus"
--

;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE "report_runstatus" (
  "id" INT4 NOT NULL,
  "run_id_id" INT4 NOT NULL,
  "queue_id_id" INT4 NOT NULL,
  "message_id" varchar(100) DEFAULT NULL,
  "created_on" TIMESTAMP NOT NULL,
  PRIMARY KEY ("id"),

  FOREIGN KEY ("run_id_id") REFERENCES "report_datarun" ("id"),
  FOREIGN KEY ("queue_id_id") REFERENCES "report_statusqueue" ("id")
);
/*!40101 SET character_set_client = @saved_cs_client */;
--
-- Table structure for table "report_errors"
--

;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE "report_errors" (
  "id" INT4 NOT NULL,
  "run_status_id_id" INT4 NOT NULL,
  "description" varchar(200) DEFAULT NULL,
  PRIMARY KEY ("id"),

  FOREIGN KEY ("run_status_id_id") REFERENCES "report_runstatus" ("id")
);
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table "report_ipts_instruments"
--

;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE "report_ipts_instruments" (
  "id" INT4 NOT NULL,
  "ipts_id" INT4 NOT NULL,
  "instrument_id" INT4 NOT NULL,
  PRIMARY KEY ("id"),

  FOREIGN KEY ("ipts_id") REFERENCES "report_ipts" ("id"),
  FOREIGN KEY ("instrument_id") REFERENCES "report_instrument" ("id")
);
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table "report_workflowsummary"
--

;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE "report_workflowsummary" (
  "id" INT4 NOT NULL,
  "run_id_id" INT4 NOT NULL,
  "complete" INT2 NOT NULL,
  "catalog_started" INT2 NOT NULL,
  "cataloged" INT2 NOT NULL,
  "reduction_needed" INT2 NOT NULL,
  "reduction_started" INT2 NOT NULL,
  "reduced" INT2 NOT NULL,
  "reduction_cataloged" INT2 NOT NULL,
  "reduction_catalog_started" INT2 NOT NULL,
  PRIMARY KEY ("id"),

  FOREIGN KEY ("run_id_id") REFERENCES "report_datarun" ("id")
);
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2012-08-23 12:33:10


COMMIT;

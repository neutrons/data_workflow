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

DROP TABLE IF EXISTS "auth_group";
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE "auth_group" (
  "id" int(11) NOT NULL,
  "name" varchar(80) NOT NULL,
  PRIMARY KEY ("id"),
  UNIQUE KEY "name" ("name")
);
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table "auth_group_permissions"
--

DROP TABLE IF EXISTS "auth_group_permissions";
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE "auth_group_permissions" (
  "id" int(11) NOT NULL,
  "group_id" int(11) NOT NULL,
  "permission_id" int(11) NOT NULL,
  PRIMARY KEY ("id"),
  UNIQUE KEY "group_id" ("group_id","permission_id"),
  KEY "auth_group_permissions_bda51c3c" ("group_id"),
  KEY "auth_group_permissions_1e014c8f" ("permission_id"),
  CONSTRAINT "group_id_refs_id_3cea63fe" FOREIGN KEY ("group_id") REFERENCES "auth_group" ("id"),
  CONSTRAINT "permission_id_refs_id_a7792de1" FOREIGN KEY ("permission_id") REFERENCES "auth_permission" ("id")
);
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table "auth_permission"
--

DROP TABLE IF EXISTS "auth_permission";
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE "auth_permission" (
  "id" int(11) NOT NULL,
  "name" varchar(50) NOT NULL,
  "content_type_id" int(11) NOT NULL,
  "codename" varchar(100) NOT NULL,
  PRIMARY KEY ("id"),
  UNIQUE KEY "content_type_id" ("content_type_id","codename"),
  KEY "auth_permission_e4470c6e" ("content_type_id"),
  CONSTRAINT "content_type_id_refs_id_728de91f" FOREIGN KEY ("content_type_id") REFERENCES "django_content_type" ("id")
);
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table "auth_user"
--

DROP TABLE IF EXISTS "auth_user";
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE "auth_user" (
  "id" int(11) NOT NULL,
  "username" varchar(30) NOT NULL,
  "first_name" varchar(30) NOT NULL,
  "last_name" varchar(30) NOT NULL,
  "email" varchar(75) NOT NULL,
  "password" varchar(128) NOT NULL,
  "is_staff" tinyint(1) NOT NULL,
  "is_active" tinyint(1) NOT NULL,
  "is_superuser" tinyint(1) NOT NULL,
  "last_login" datetime NOT NULL,
  "date_joined" datetime NOT NULL,
  PRIMARY KEY ("id"),
  UNIQUE KEY "username" ("username")
);
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table "auth_user_groups"
--

DROP TABLE IF EXISTS "auth_user_groups";
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE "auth_user_groups" (
  "id" int(11) NOT NULL,
  "user_id" int(11) NOT NULL,
  "group_id" int(11) NOT NULL,
  PRIMARY KEY ("id"),
  UNIQUE KEY "user_id" ("user_id","group_id"),
  KEY "auth_user_groups_fbfc09f1" ("user_id"),
  KEY "auth_user_groups_bda51c3c" ("group_id"),
  CONSTRAINT "user_id_refs_id_831107f1" FOREIGN KEY ("user_id") REFERENCES "auth_user" ("id"),
  CONSTRAINT "group_id_refs_id_f0ee9890" FOREIGN KEY ("group_id") REFERENCES "auth_group" ("id")
);
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table "auth_user_user_permissions"
--

DROP TABLE IF EXISTS "auth_user_user_permissions";
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE "auth_user_user_permissions" (
  "id" int(11) NOT NULL,
  "user_id" int(11) NOT NULL,
  "permission_id" int(11) NOT NULL,
  PRIMARY KEY ("id"),
  UNIQUE KEY "user_id" ("user_id","permission_id"),
  KEY "auth_user_user_permissions_fbfc09f1" ("user_id"),
  KEY "auth_user_user_permissions_1e014c8f" ("permission_id"),
  CONSTRAINT "user_id_refs_id_f2045483" FOREIGN KEY ("user_id") REFERENCES "auth_user" ("id"),
  CONSTRAINT "permission_id_refs_id_67e79cb" FOREIGN KEY ("permission_id") REFERENCES "auth_permission" ("id")
);
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table "db_datarun"
--

DROP TABLE IF EXISTS "db_datarun";
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE "db_datarun" (
  "id" int(11) NOT NULL,
  "run_number" int(11) NOT NULL,
  "created_on" datetime NOT NULL,
  PRIMARY KEY ("id")
);
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table "db_runstatus"
--

DROP TABLE IF EXISTS "db_runstatus";
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE "db_runstatus" (
  "id" int(11) NOT NULL,
  "run_id_id" int(11) NOT NULL,
  "queue_id_id" int(11) NOT NULL,
  "message_id" varchar(100) DEFAULT NULL,
  "created_on" datetime NOT NULL,
  PRIMARY KEY ("id"),
  KEY "db_runstatus_981118df" ("run_id_id"),
  KEY "db_runstatus_60b0e6c9" ("queue_id_id"),
  CONSTRAINT "run_id_id_refs_id_fe1d836f" FOREIGN KEY ("run_id_id") REFERENCES "db_datarun" ("id"),
  CONSTRAINT "queue_id_id_refs_id_4c6cccfd" FOREIGN KEY ("queue_id_id") REFERENCES "db_statusinfo" ("id")
);
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table "db_statusinfo"
--

DROP TABLE IF EXISTS "db_statusinfo";
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE "db_statusinfo" (
  "id" int(11) NOT NULL,
  "name" varchar(100) NOT NULL,
  PRIMARY KEY ("id")
);
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table "django_admin_log"
--

DROP TABLE IF EXISTS "django_admin_log";
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE "django_admin_log" (
  "id" int(11) NOT NULL,
  "action_time" datetime NOT NULL,
  "user_id" int(11) NOT NULL,
  "content_type_id" int(11) DEFAULT NULL,
  "object_id" longtext,
  "object_repr" varchar(200) NOT NULL,
  "action_flag" smallint(5) unsigned NOT NULL,
  "change_message" longtext NOT NULL,
  PRIMARY KEY ("id"),
  KEY "django_admin_log_fbfc09f1" ("user_id"),
  KEY "django_admin_log_e4470c6e" ("content_type_id"),
  CONSTRAINT "content_type_id_refs_id_288599e6" FOREIGN KEY ("content_type_id") REFERENCES "django_content_type" ("id"),
  CONSTRAINT "user_id_refs_id_c8665aa" FOREIGN KEY ("user_id") REFERENCES "auth_user" ("id")
);
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table "django_content_type"
--

DROP TABLE IF EXISTS "django_content_type";
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE "django_content_type" (
  "id" int(11) NOT NULL,
  "name" varchar(100) NOT NULL,
  "app_label" varchar(100) NOT NULL,
  "model" varchar(100) NOT NULL,
  PRIMARY KEY ("id"),
  UNIQUE KEY "app_label" ("app_label","model")
);
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table "django_session"
--

DROP TABLE IF EXISTS "django_session";
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE "django_session" (
  "session_key" varchar(40) NOT NULL,
  "session_data" longtext NOT NULL,
  "expire_date" datetime NOT NULL,
  PRIMARY KEY ("session_key"),
  KEY "django_session_c25c2c28" ("expire_date")
);
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table "django_site"
--

DROP TABLE IF EXISTS "django_site";
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE "django_site" (
  "id" int(11) NOT NULL,
  "domain" varchar(100) NOT NULL,
  "name" varchar(50) NOT NULL,
  PRIMARY KEY ("id")
);
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table "report_datarun"
--

DROP TABLE IF EXISTS "report_datarun";
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE "report_datarun" (
  "id" int(11) NOT NULL,
  "run_number" int(11) NOT NULL,
  "ipts_id_id" int(11) NOT NULL,
  "instrument_id_id" int(11) NOT NULL,
  "file" varchar(128) NOT NULL,
  "created_on" datetime NOT NULL,
  PRIMARY KEY ("id"),
  KEY "report_datarun_1b2cd3f5" ("ipts_id_id"),
  KEY "report_datarun_15e795e8" ("instrument_id_id"),
  CONSTRAINT "instrument_id_id_refs_id_96579ec4" FOREIGN KEY ("instrument_id_id") REFERENCES "report_instrument" ("id"),
  CONSTRAINT "ipts_id_id_refs_id_be432db7" FOREIGN KEY ("ipts_id_id") REFERENCES "report_ipts" ("id")
);
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table "report_errors"
--

DROP TABLE IF EXISTS "report_errors";
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE "report_errors" (
  "id" int(11) NOT NULL,
  "run_status_id_id" int(11) NOT NULL,
  "description" varchar(200) DEFAULT NULL,
  PRIMARY KEY ("id"),
  KEY "report_errors_8048c2dd" ("run_status_id_id"),
  CONSTRAINT "run_status_id_id_refs_id_c8b93724" FOREIGN KEY ("run_status_id_id") REFERENCES "report_runstatus" ("id")
);
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table "report_instrument"
--

DROP TABLE IF EXISTS "report_instrument";
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE "report_instrument" (
  "id" int(11) NOT NULL,
  "name" varchar(20) NOT NULL,
  PRIMARY KEY ("id"),
  UNIQUE KEY "name" ("name")
);
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table "report_ipts"
--

DROP TABLE IF EXISTS "report_ipts";
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE "report_ipts" (
  "id" int(11) NOT NULL,
  "expt_name" varchar(20) NOT NULL,
  "created_on" datetime NOT NULL,
  PRIMARY KEY ("id"),
  UNIQUE KEY "expt_name" ("expt_name")
);
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table "report_ipts_instruments"
--

DROP TABLE IF EXISTS "report_ipts_instruments";
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE "report_ipts_instruments" (
  "id" int(11) NOT NULL,
  "ipts_id" int(11) NOT NULL,
  "instrument_id" int(11) NOT NULL,
  PRIMARY KEY ("id"),
  UNIQUE KEY "ipts_id" ("ipts_id","instrument_id"),
  KEY "instrument_id_refs_id_969e5485" ("instrument_id"),
  CONSTRAINT "ipts_id_refs_id_85a248d0" FOREIGN KEY ("ipts_id") REFERENCES "report_ipts" ("id"),
  CONSTRAINT "instrument_id_refs_id_969e5485" FOREIGN KEY ("instrument_id") REFERENCES "report_instrument" ("id")
);
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table "report_runstatus"
--

DROP TABLE IF EXISTS "report_runstatus";
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE "report_runstatus" (
  "id" int(11) NOT NULL,
  "run_id_id" int(11) NOT NULL,
  "queue_id_id" int(11) NOT NULL,
  "message_id" varchar(100) DEFAULT NULL,
  "created_on" datetime NOT NULL,
  PRIMARY KEY ("id"),
  KEY "report_runstatus_981118df" ("run_id_id"),
  KEY "report_runstatus_60b0e6c9" ("queue_id_id"),
  CONSTRAINT "run_id_id_refs_id_742129e7" FOREIGN KEY ("run_id_id") REFERENCES "report_datarun" ("id"),
  CONSTRAINT "queue_id_id_refs_id_7b810197" FOREIGN KEY ("queue_id_id") REFERENCES "report_statusqueue" ("id")
);
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table "report_statusqueue"
--

DROP TABLE IF EXISTS "report_statusqueue";
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE "report_statusqueue" (
  "id" int(11) NOT NULL,
  "name" varchar(100) NOT NULL,
  PRIMARY KEY ("id"),
  UNIQUE KEY "name" ("name")
);
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table "report_workflowsummary"
--

DROP TABLE IF EXISTS "report_workflowsummary";
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE "report_workflowsummary" (
  "id" int(11) NOT NULL,
  "run_id_id" int(11) NOT NULL,
  "complete" tinyint(1) NOT NULL,
  "catalog_started" tinyint(1) NOT NULL,
  "cataloged" tinyint(1) NOT NULL,
  "reduction_needed" tinyint(1) NOT NULL,
  "reduction_started" tinyint(1) NOT NULL,
  "reduced" tinyint(1) NOT NULL,
  "reduction_cataloged" tinyint(1) NOT NULL,
  "reduction_catalog_started" tinyint(1) NOT NULL,
  PRIMARY KEY ("id"),
  UNIQUE KEY "run_id_id" ("run_id_id"),
  CONSTRAINT "run_id_id_refs_id_53eb9857" FOREIGN KEY ("run_id_id") REFERENCES "report_datarun" ("id")
);
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2012-08-23 13:01:28

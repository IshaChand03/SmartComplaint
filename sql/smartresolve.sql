-- MySQL dump 10.13  Distrib 8.0.46, for Win64 (x86_64)
--
-- Host: localhost    Database: smartresolve
-- ------------------------------------------------------
-- Server version	8.0.46

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `audit_logs`
--

DROP TABLE IF EXISTS `audit_logs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `audit_logs` (
  `id` int NOT NULL AUTO_INCREMENT,
  `action_name` varchar(50) NOT NULL,
  `entity_type` varchar(50) NOT NULL,
  `entity_id` int DEFAULT NULL,
  `details` text,
  `user_id` int NOT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `audit_logs_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=12 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `audit_logs`
--

LOCK TABLES `audit_logs` WRITE;
/*!40000 ALTER TABLE `audit_logs` DISABLE KEYS */;
INSERT INTO `audit_logs` VALUES (1,'DEPARTMENT_CREATED','department',5,'Created department \'Logistics\'',1,'2026-10-08 05:16:02'),(2,'DEPARTMENT_UPDATED','department',5,'Renamed \'Logistics\' to \'Logistics\'',1,'2026-10-08 05:16:54'),(3,'DEPARTMENT_UPDATED','department',5,'Renamed \'Logistics\' to \'Logistics & Delivery\'',1,'2026-10-08 05:17:11'),(4,'CATEGORY_UPDATED','category',2,'\'Technical Issue\' -> \'Technical Issue\', department 2 -> 2, critical False -> True',1,'2026-10-08 05:17:35'),(5,'SLA_RULE_UPDATED','sla_rule',1,'Critical: resolution 4h -> 6h, near 1h -> 2h',1,'2026-10-08 05:18:39'),(6,'SLA_RULE_UPDATED','sla_rule',1,'Critical: resolution 6h -> 4h, near 2h -> 1h',1,'2026-10-08 05:23:17'),(7,'SLA_RULE_UPDATED','sla_rule',1,'Critical: resolution 4h -> 4h, near 1h -> 1h',1,'2026-10-08 05:28:10'),(8,'ESCALATION_RULE_UPDATED','escalation_rule',4,'Low: grace 4h -> 6h, level 1 -> 1, target Manager -> Manager',1,'2026-10-08 05:29:33'),(9,'ESCALATION_RULE_UPDATED','escalation_rule',4,'Low: grace 6h -> 4h, level 1 -> 1, target Manager -> Manager',1,'2026-10-08 05:30:09'),(10,'USER_UPDATED','user',5,'Customer Two: role Customer -> Support Agent, department None -> 2',1,'2026-10-08 05:39:14'),(11,'USER_UPDATED','user',7,'sonu: role Customer -> Support Agent, department None -> 3',1,'2026-10-08 06:12:56');
/*!40000 ALTER TABLE `audit_logs` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `categories`
--

DROP TABLE IF EXISTS `categories`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `categories` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `department_id` int NOT NULL,
  `is_critical` tinyint(1) NOT NULL DEFAULT '0',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`),
  KEY `department_id` (`department_id`),
  CONSTRAINT `categories_ibfk_1` FOREIGN KEY (`department_id`) REFERENCES `departments` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `categories`
--

LOCK TABLES `categories` WRITE;
/*!40000 ALTER TABLE `categories` DISABLE KEYS */;
INSERT INTO `categories` VALUES (1,'Billing & Payments',1,1,'2026-10-07 10:35:38'),(2,'Technical Issue',2,1,'2026-10-07 10:35:38'),(3,'Account & Login',3,0,'2026-10-07 10:35:38'),(4,'Security / Fraud',4,1,'2026-10-07 10:35:38');
/*!40000 ALTER TABLE `categories` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `comments`
--

DROP TABLE IF EXISTS `comments`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `comments` (
  `id` int NOT NULL AUTO_INCREMENT,
  `complaint_id` int NOT NULL,
  `user_id` int NOT NULL,
  `comment_text` text NOT NULL,
  `is_system` tinyint(1) NOT NULL DEFAULT '0',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `complaint_id` (`complaint_id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `comments_ibfk_1` FOREIGN KEY (`complaint_id`) REFERENCES `complaints` (`id`),
  CONSTRAINT `comments_ibfk_2` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `comments`
--

LOCK TABLES `comments` WRITE;
/*!40000 ALTER TABLE `comments` DISABLE KEYS */;
INSERT INTO `comments` VALUES (1,2,4,'Please update me as soon as possible.',0,'2026-10-07 11:28:25'),(2,2,2,'Checking the payment gateway logs now.',0,'2026-10-07 11:29:08'),(3,4,6,'SLA breached. Escalated to Manager One.',1,'2026-10-07 12:26:51'),(4,4,6,'SLA breached. Escalated to Manager One.',1,'2026-10-07 12:34:03'),(5,5,6,'SLA breached. Escalated to Manager One.',1,'2026-10-07 12:36:02'),(6,3,6,'SLA breached. Escalated to Manager One.',1,'2026-10-07 19:04:03'),(7,6,6,'SLA breached. Escalated to Manager One.',1,'2026-10-08 05:00:07'),(8,9,4,'plz solve this',0,'2026-10-08 06:00:49');
/*!40000 ALTER TABLE `comments` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `complaint_escalations`
--

DROP TABLE IF EXISTS `complaint_escalations`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `complaint_escalations` (
  `id` int NOT NULL AUTO_INCREMENT,
  `complaint_id` int NOT NULL,
  `level` int NOT NULL,
  `manager_id` int DEFAULT NULL,
  `reason` varchar(255) NOT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `complaint_id` (`complaint_id`),
  KEY `manager_id` (`manager_id`),
  CONSTRAINT `complaint_escalations_ibfk_1` FOREIGN KEY (`complaint_id`) REFERENCES `complaints` (`id`),
  CONSTRAINT `complaint_escalations_ibfk_2` FOREIGN KEY (`manager_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `complaint_escalations`
--

LOCK TABLES `complaint_escalations` WRITE;
/*!40000 ALTER TABLE `complaint_escalations` DISABLE KEYS */;
INSERT INTO `complaint_escalations` VALUES (1,4,1,3,'SLA breached (High priority) and the 1-hour grace period has passed','2026-10-07 12:26:51'),(2,4,1,3,'SLA breached (High priority) and the 1-hour grace period has passed','2026-10-07 12:34:02'),(3,5,1,3,'SLA breached (High priority) and the 1-hour grace period has passed','2026-10-07 12:36:02'),(4,3,1,3,'SLA breached (Critical priority) and the 0-hour grace period has passed','2026-10-07 19:04:03'),(5,6,1,3,'SLA breached (High priority) and the 1-hour grace period has passed','2026-10-08 05:00:07');
/*!40000 ALTER TABLE `complaint_escalations` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `complaint_history`
--

DROP TABLE IF EXISTS `complaint_history`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `complaint_history` (
  `id` int NOT NULL AUTO_INCREMENT,
  `complaint_id` int NOT NULL,
  `action` varchar(50) NOT NULL,
  `old_value` varchar(100) DEFAULT NULL,
  `new_value` varchar(100) DEFAULT NULL,
  `changed_by` int NOT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `complaint_id` (`complaint_id`),
  KEY `changed_by` (`changed_by`),
  CONSTRAINT `complaint_history_ibfk_1` FOREIGN KEY (`complaint_id`) REFERENCES `complaints` (`id`),
  CONSTRAINT `complaint_history_ibfk_2` FOREIGN KEY (`changed_by`) REFERENCES `users` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=35 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `complaint_history`
--

LOCK TABLES `complaint_history` WRITE;
/*!40000 ALTER TABLE `complaint_history` DISABLE KEYS */;
INSERT INTO `complaint_history` VALUES (1,1,'Assigned',NULL,'Agent One',1,'2026-10-07 11:17:14'),(2,1,'Status changed','Open','Assigned',1,'2026-10-07 11:17:14'),(3,1,'Status changed','Assigned','In Progress',2,'2026-10-07 11:19:33'),(4,1,'Status changed','In Progress','Resolved',2,'2026-10-07 11:19:46'),(5,1,'Status changed','Resolved','Closed',1,'2026-10-07 11:20:27'),(6,2,'Created',NULL,'Open',4,'2026-10-07 11:26:02'),(7,2,'Assigned',NULL,'Agent One',1,'2026-10-07 11:27:29'),(8,2,'Status changed','Open','Assigned',1,'2026-10-07 11:27:29'),(9,3,'Created',NULL,'Open',4,'2026-10-07 12:11:37'),(10,4,'Created',NULL,'Open',4,'2026-10-07 12:19:31'),(11,4,'Assigned',NULL,'Agent One',1,'2026-10-07 12:25:15'),(12,4,'Status changed','Open','Assigned',1,'2026-10-07 12:25:15'),(13,4,'Status changed','Assigned','Escalated',6,'2026-10-07 12:26:51'),(14,4,'Status changed','Escalated','In Progress',2,'2026-10-07 12:31:19'),(15,4,'Status changed','In Progress','Escalated',6,'2026-10-07 12:34:03'),(16,5,'Created',NULL,'Open',4,'2026-10-07 12:34:51'),(17,5,'Status changed','Open','Escalated',6,'2026-10-07 12:36:02'),(18,3,'Status changed','Open','Escalated',6,'2026-10-07 19:04:03'),(19,6,'Created',NULL,'Open',1,'2026-10-07 19:09:59'),(20,7,'Created',NULL,'Open',4,'2026-10-07 19:12:55'),(21,7,'Assigned',NULL,'Agent One',1,'2026-10-07 19:20:40'),(22,7,'Status changed','Open','Assigned',1,'2026-10-07 19:20:40'),(23,7,'Status changed','Assigned','In Progress',2,'2026-10-07 19:23:25'),(24,7,'Status changed','In Progress','Resolved',2,'2026-10-07 19:24:27'),(25,8,'Created',NULL,'Open',4,'2026-10-07 20:01:44'),(26,6,'Status changed','Open','Escalated',6,'2026-10-08 05:00:07'),(27,9,'Created',NULL,'Open',4,'2026-10-08 06:00:25'),(28,2,'Status changed','Assigned','In Progress',1,'2026-10-08 06:03:35'),(29,2,'Status changed','In Progress','Resolved',1,'2026-10-08 06:03:37'),(30,2,'Status changed','Resolved','Closed',1,'2026-10-08 06:03:38'),(31,3,'Assigned',NULL,'Agent One',1,'2026-10-08 06:03:48'),(32,3,'Status changed','Escalated','In Progress',2,'2026-10-08 06:04:57'),(33,3,'Status changed','In Progress','Resolved',2,'2026-10-08 06:04:58'),(34,3,'Status changed','Resolved','Closed',4,'2026-10-08 06:05:32');
/*!40000 ALTER TABLE `complaint_history` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `complaints`
--

DROP TABLE IF EXISTS `complaints`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `complaints` (
  `id` int NOT NULL AUTO_INCREMENT,
  `reference_no` varchar(30) DEFAULT NULL,
  `title` varchar(200) NOT NULL,
  `description` text NOT NULL,
  `category_id` int NOT NULL,
  `department_id` int NOT NULL,
  `urgency` tinyint NOT NULL,
  `sentiment` varchar(20) NOT NULL DEFAULT 'Neutral',
  `priority` varchar(20) NOT NULL DEFAULT 'Low',
  `due_at` datetime DEFAULT NULL,
  `status` enum('Open','Assigned','In Progress','Resolved','Closed','Escalated') NOT NULL DEFAULT 'Open',
  `raised_by` int NOT NULL,
  `assigned_to` int DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `reference_no` (`reference_no`),
  KEY `category_id` (`category_id`),
  KEY `department_id` (`department_id`),
  KEY `raised_by` (`raised_by`),
  KEY `assigned_to` (`assigned_to`),
  CONSTRAINT `complaints_ibfk_1` FOREIGN KEY (`category_id`) REFERENCES `categories` (`id`),
  CONSTRAINT `complaints_ibfk_2` FOREIGN KEY (`department_id`) REFERENCES `departments` (`id`),
  CONSTRAINT `complaints_ibfk_3` FOREIGN KEY (`raised_by`) REFERENCES `users` (`id`),
  CONSTRAINT `complaints_ibfk_4` FOREIGN KEY (`assigned_to`) REFERENCES `users` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=10 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `complaints`
--

LOCK TABLES `complaints` WRITE;
/*!40000 ALTER TABLE `complaints` DISABLE KEYS */;
INSERT INTO `complaints` VALUES (1,'CMP-20261007-000001','Payment failed','My payment failed three times and I am frustrated.',1,1,4,'Neutral','Critical',NULL,'Closed',1,2,'2026-10-07 10:55:25','2026-10-07 11:20:27'),(2,'CMP-20261007-000002','Refund not received','I am still waiting for my refund.',1,1,2,'Neutral','Medium',NULL,'Closed',4,2,'2026-10-07 11:26:02','2026-10-08 06:03:38'),(3,'CMP-20261007-000003','Payment failed','My payment failed three times. I am frustrated and this is urgent.',1,1,2,'Negative','Critical','2026-10-07 21:41:37','Closed',4,2,'2026-10-07 12:11:37','2026-10-08 06:05:32'),(4,'CMP-20261007-000004','Escalation test','This complaint is for testing escalation.',1,1,2,'Neutral','High','2026-10-07 07:55:48','Escalated',4,2,'2026-10-07 12:19:31','2026-10-07 12:34:02'),(5,'CMP-20261007-000005','Automatic escalation test','Testing the background job.',1,1,2,'Neutral','High','2026-10-07 08:05:30','Escalated',4,NULL,'2026-10-07 12:34:51','2026-10-07 12:36:02'),(6,'CMP-20261008-000006','Notification test','Testing notifications.',1,1,2,'Neutral','High','2026-10-08 08:39:59','Escalated',1,NULL,'2026-10-07 19:09:59','2026-10-08 05:00:07'),(7,'CMP-20261008-000007','Notification test','Testing notifications.',1,1,2,'Neutral','High','2026-10-07 14:55:13','Resolved',4,2,'2026-10-07 19:12:55','2026-10-07 19:25:13'),(8,'CMP-20261008-000008','Wi-Fi not connecting','The app cannot connect on my phone.',2,2,2,'Neutral','Medium','2026-10-09 01:31:45','Open',4,NULL,'2026-10-07 20:01:44','2026-10-07 20:01:44'),(9,'CMP-20261008-000009','Payment failed','I got really frustrated I\'m continuously trying for payment each time it shows failed',1,1,3,'Negative','Critical','2026-10-08 15:30:26','Open',4,NULL,'2026-10-08 06:00:25','2026-10-08 06:00:25');
/*!40000 ALTER TABLE `complaints` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `departments`
--

DROP TABLE IF EXISTS `departments`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `departments` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `departments`
--

LOCK TABLES `departments` WRITE;
/*!40000 ALTER TABLE `departments` DISABLE KEYS */;
INSERT INTO `departments` VALUES (1,'Finance & Accounts','2026-10-07 09:52:09'),(2,'IT / Technical Support','2026-10-07 09:52:09'),(3,'Customer Support','2026-10-07 09:52:09'),(4,'Security / Risk','2026-10-07 09:52:09'),(5,'Logistics & Delivery','2026-10-08 05:16:02');
/*!40000 ALTER TABLE `departments` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `escalation_rules`
--

DROP TABLE IF EXISTS `escalation_rules`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `escalation_rules` (
  `id` int NOT NULL AUTO_INCREMENT,
  `priority` varchar(20) NOT NULL,
  `grace_hours` int NOT NULL,
  `escalation_level` int NOT NULL DEFAULT '1',
  `target_role` varchar(30) NOT NULL DEFAULT 'Manager',
  `active` tinyint(1) NOT NULL DEFAULT '1',
  PRIMARY KEY (`id`),
  UNIQUE KEY `priority` (`priority`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `escalation_rules`
--

LOCK TABLES `escalation_rules` WRITE;
/*!40000 ALTER TABLE `escalation_rules` DISABLE KEYS */;
INSERT INTO `escalation_rules` VALUES (1,'Critical',0,1,'Manager',1),(2,'High',1,1,'Manager',1),(3,'Medium',2,1,'Manager',1),(4,'Low',4,1,'Manager',1);
/*!40000 ALTER TABLE `escalation_rules` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `notifications`
--

DROP TABLE IF EXISTS `notifications`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `notifications` (
  `id` int NOT NULL AUTO_INCREMENT,
  `complaint_id` int DEFAULT NULL,
  `recipient_id` int NOT NULL,
  `channel` varchar(20) NOT NULL,
  `event` varchar(50) NOT NULL,
  `status` varchar(20) NOT NULL,
  `message` text NOT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `complaint_id` (`complaint_id`),
  KEY `recipient_id` (`recipient_id`),
  CONSTRAINT `notifications_ibfk_1` FOREIGN KEY (`complaint_id`) REFERENCES `complaints` (`id`),
  CONSTRAINT `notifications_ibfk_2` FOREIGN KEY (`recipient_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=23 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `notifications`
--

LOCK TABLES `notifications` WRITE;
/*!40000 ALTER TABLE `notifications` DISABLE KEYS */;
INSERT INTO `notifications` VALUES (1,3,3,'Email','Escalated','Skipped','Complaint #3 was escalated to you. SLA breached (Critical priority) and the 0-hour grace period has passed.','2026-10-07 19:04:03'),(2,3,3,'WhatsApp','Escalated','Mock','Complaint #3 was escalated to you. SLA breached (Critical priority) and the 0-hour grace period has passed.','2026-10-07 19:04:03'),(3,6,1,'Email','Created','Skipped','Your complaint CMP-20261008-000006 has been received. Priority: High.','2026-10-07 19:09:59'),(4,6,1,'WhatsApp','Created','Mock','Your complaint CMP-20261008-000006 has been received. Priority: High.','2026-10-07 19:09:59'),(5,7,4,'Email','Created','Skipped','Your complaint CMP-20261008-000007 has been received. Priority: High.','2026-10-07 19:12:55'),(6,7,4,'WhatsApp','Created','Mock','Your complaint CMP-20261008-000007 has been received. Priority: High.','2026-10-07 19:12:55'),(7,7,2,'Email','Assigned','Skipped','Complaint CMP-20261008-000007 has been assigned to you.','2026-10-07 19:20:40'),(8,7,2,'WhatsApp','Assigned','Mock','Complaint CMP-20261008-000007 has been assigned to you.','2026-10-07 19:20:40'),(9,7,4,'Email','Resolved','Skipped','Your complaint CMP-20261008-000007 has been marked as resolved.','2026-10-07 19:24:27'),(10,7,4,'WhatsApp','Resolved','Mock','Your complaint CMP-20261008-000007 has been marked as resolved.','2026-10-07 19:24:27'),(11,8,4,'Email','Created','Skipped','Your complaint CMP-20261008-000008 has been received. Priority: Medium.','2026-10-07 20:01:44'),(12,8,4,'WhatsApp','Created','Mock','Your complaint CMP-20261008-000008 has been received. Priority: Medium.','2026-10-07 20:01:44'),(13,6,3,'Email','Escalated','Skipped','Complaint #6 was escalated to you. SLA breached (High priority) and the 1-hour grace period has passed.','2026-10-08 05:00:07'),(14,6,3,'WhatsApp','Escalated','Mock','Complaint #6 was escalated to you. SLA breached (High priority) and the 1-hour grace period has passed.','2026-10-08 05:00:07'),(15,9,4,'Email','Created','Skipped','Your complaint CMP-20261008-000009 has been received. Priority: Critical.','2026-10-08 06:00:25'),(16,9,4,'WhatsApp','Created','Mock','Your complaint CMP-20261008-000009 has been received. Priority: Critical.','2026-10-08 06:00:25'),(17,2,4,'Email','Resolved','Skipped','Your complaint CMP-20261007-000002 has been marked as resolved.','2026-10-08 06:03:37'),(18,2,4,'WhatsApp','Resolved','Mock','Your complaint CMP-20261007-000002 has been marked as resolved.','2026-10-08 06:03:37'),(19,3,2,'Email','Assigned','Skipped','Complaint CMP-20261007-000003 has been assigned to you.','2026-10-08 06:03:48'),(20,3,2,'WhatsApp','Assigned','Mock','Complaint CMP-20261007-000003 has been assigned to you.','2026-10-08 06:03:48'),(21,3,4,'Email','Resolved','Skipped','Your complaint CMP-20261007-000003 has been marked as resolved.','2026-10-08 06:04:58'),(22,3,4,'WhatsApp','Resolved','Mock','Your complaint CMP-20261007-000003 has been marked as resolved.','2026-10-08 06:04:58');
/*!40000 ALTER TABLE `notifications` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `sla_rules`
--

DROP TABLE IF EXISTS `sla_rules`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `sla_rules` (
  `id` int NOT NULL AUTO_INCREMENT,
  `priority` varchar(20) NOT NULL,
  `resolution_hours` int NOT NULL,
  `near_breach_hours` int NOT NULL,
  `active` tinyint(1) NOT NULL DEFAULT '1',
  PRIMARY KEY (`id`),
  UNIQUE KEY `priority` (`priority`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `sla_rules`
--

LOCK TABLES `sla_rules` WRITE;
/*!40000 ALTER TABLE `sla_rules` DISABLE KEYS */;
INSERT INTO `sla_rules` VALUES (1,'Critical',4,1,1),(2,'High',8,1,1),(3,'Medium',24,2,1),(4,'Low',48,4,1);
/*!40000 ALTER TABLE `sla_rules` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `users` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `email` varchar(150) NOT NULL,
  `password_hash` varchar(255) NOT NULL,
  `role` enum('Admin','Manager','Support Agent','Customer') NOT NULL DEFAULT 'Customer',
  `department_id` int DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `email` (`email`),
  KEY `department_id` (`department_id`),
  CONSTRAINT `users_ibfk_1` FOREIGN KEY (`department_id`) REFERENCES `departments` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `users`
--

LOCK TABLES `users` WRITE;
/*!40000 ALTER TABLE `users` DISABLE KEYS */;
INSERT INTO `users` VALUES (1,'Isha','isha@test.com','scrypt:32768:8:1$mBH7EPaeeJ7UroI3$f34c60fdfa4190507f2d74604d218b86060fb9736e49b099f92627597d48ba4d576c037e3119d7ac597ae55e3cea1492618cc64f24ab9b4a6700380b0f3ae68c','Admin',NULL,'2026-10-07 10:21:04'),(2,'Agent One','agent@test.com','scrypt:32768:8:1$pLzBqN9myHzNy5UN$ae6187355b43b2c9093fbfbd2fbb3bf9a459420ebace0852b1d92124eafbe541b2717b2bfe3e532d5c25aea3d771d954cecc772a2c87104afc368bdd3a20c349','Support Agent',1,'2026-10-07 11:05:48'),(3,'Manager One','manager@test.com','scrypt:32768:8:1$34h8SVUdkmIeoNKt$f92fe2fc63be1c6e19d9a8803cf6ef64e68aee01fd89eacfa4606101f60cdbf946042ab7504e9ced4d0e28eeff2866be9b016f093698f04addaa56b2972d2997','Manager',1,'2026-10-07 11:06:06'),(4,'Customer One','customer@test.com','scrypt:32768:8:1$9PORtu0vr7Nd1gYt$b05f68084c2d959f8da446f2f0a3c45262e8db054df4dee9dedf2c973c9db47dff7840855c87893c312a3dcfea856057501d545f6c60bf31e74f330fc0ffecb9','Customer',NULL,'2026-10-07 11:06:28'),(5,'Customer Two','customer2@test.com','scrypt:32768:8:1$E4pe4SvD4NzZZGmG$6e4c0516b6aa5ce54ccfed08c925810b6fc1e8e87cf893eb5c82252b5c5982a8a5a52fb9d739d3e825fa551d5f29aa60599be1b0da09de71a3b0b225b6e2c53c','Support Agent',2,'2026-10-07 11:41:54'),(6,'System','system@smartresolve.local','!','Admin',NULL,'2026-10-07 12:12:57'),(7,'sonu','sonu@gmail.com','scrypt:32768:8:1$mEKZW8dVWsIlNTVR$3472bc1cad48cbabbb73d9e5d76185d83738ad25f67eca8bc32a9d01a20ff676831462294d93986c650760a8b2f0de931175ac7069ee4940726947f5e1096dad','Support Agent',3,'2026-10-08 05:50:55');
/*!40000 ALTER TABLE `users` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-10-08 11:57:37

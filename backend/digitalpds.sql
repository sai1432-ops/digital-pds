-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: Apr 11, 2026 at 11:08 AM
-- Server version: 10.4.32-MariaDB
-- PHP Version: 8.2.12

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `digitalpds`
--

-- --------------------------------------------------------

--
-- Table structure for table `admins`
--

CREATE TABLE `admins` (
  `id` int(11) NOT NULL,
  `name` varchar(100) NOT NULL,
  `email` varchar(120) NOT NULL,
  `phone` varchar(20) DEFAULT NULL,
  `password_hash` varchar(255) NOT NULL,
  `office_location` varchar(150) DEFAULT 'Central Headquarters'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `admins`
--

INSERT INTO `admins` (`id`, `name`, `email`, `phone`, `password_hash`, `office_location`) VALUES
(4, 'Super Admin', 'admin@gmail.com', '9876543210', '$2b$12$ZjuxEjsU30vfluW3ZtpbUOzXbyx4WtBd4.y8AZcsZzMNCBEm4PhZy', 'Central Headquarters');

-- --------------------------------------------------------

--
-- Table structure for table `appointments`
--

CREATE TABLE `appointments` (
  `id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `clinic_id` int(11) NOT NULL,
  `appointment_date` date NOT NULL,
  `time_slot` varchar(50) DEFAULT NULL,
  `status` enum('BOOKED','COMPLETED','CANCELLED') DEFAULT 'BOOKED',
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `brushing_checkins`
--

CREATE TABLE `brushing_checkins` (
  `id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `member_id` int(11) DEFAULT NULL,
  `checkin_date` date NOT NULL,
  `session` enum('MORNING','EVENING') DEFAULT 'MORNING',
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `brushing_checkins`
--

INSERT INTO `brushing_checkins` (`id`, `user_id`, `member_id`, `checkin_date`, `session`, `created_at`) VALUES
(5, 12, NULL, '2026-03-06', 'MORNING', '2026-03-06 05:11:09'),
(6, 12, NULL, '2026-03-06', 'EVENING', '2026-03-06 05:11:12'),
(18, 12, 9, '2026-03-06', 'MORNING', '2026-03-06 05:54:30'),
(22, 12, 9, '2026-03-06', 'EVENING', '2026-03-06 05:54:46'),
(23, -1, NULL, '2026-03-06', 'MORNING', '2026-03-06 07:23:51'),
(25, -1, NULL, '2026-03-06', 'EVENING', '2026-03-06 07:24:04'),
(43, 12, 6, '2026-03-06', 'MORNING', '2026-03-06 11:11:44'),
(44, 12, 7, '2026-03-06', 'MORNING', '2026-03-06 11:11:44'),
(45, 12, 8, '2026-03-06', 'MORNING', '2026-03-06 11:11:44'),
(74, 12, 10, '2026-03-06', 'MORNING', '2026-03-06 13:44:54'),
(79, 17, NULL, '2026-03-06', 'MORNING', '2026-03-06 15:38:02'),
(80, 18, NULL, '2026-03-06', 'MORNING', '2026-03-06 15:39:31'),
(81, 21, NULL, '2026-03-06', 'MORNING', '2026-03-06 16:02:36'),
(82, 21, 4, '2026-03-06', 'MORNING', '2026-03-06 16:02:36'),
(83, 21, 5, '2026-03-06', 'MORNING', '2026-03-06 16:02:36'),
(84, 17, NULL, '2026-03-06', 'EVENING', '2026-03-06 16:03:35'),
(87, 22, NULL, '2026-03-06', 'MORNING', '2026-03-06 18:50:20'),
(228, 55, 25, '2026-04-07', 'MORNING', '2026-04-07 13:02:06'),
(229, 55, NULL, '2026-04-07', 'MORNING', '2026-04-07 13:02:06'),
(231, 63, NULL, '2026-04-08', 'MORNING', '2026-04-08 06:50:42'),
(232, 1, NULL, '2026-04-08', 'MORNING', '2026-04-08 19:09:30'),
(233, 13, NULL, '2026-04-08', 'MORNING', '2026-04-08 19:14:52'),
(234, 63, NULL, '2026-04-09', 'MORNING', '2026-04-09 04:00:25'),
(235, 13, NULL, '2026-04-09', 'MORNING', '2026-04-09 08:22:12'),
(236, 73, NULL, '2026-04-10', 'MORNING', '2026-04-10 04:58:17'),
(237, 75, NULL, '2026-04-10', 'MORNING', '2026-04-10 07:51:11'),
(238, 85, NULL, '2026-04-11', 'MORNING', '2026-04-11 05:57:12');

-- --------------------------------------------------------

--
-- Table structure for table `brushing_logs`
--

CREATE TABLE `brushing_logs` (
  `id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `member_id` int(11) NOT NULL,
  `date` date NOT NULL,
  `session_type` enum('MORNING','EVENING') NOT NULL,
  `created_at` datetime DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `clinics`
--

CREATE TABLE `clinics` (
  `id` int(11) NOT NULL,
  `clinic_name` varchar(150) NOT NULL,
  `address` text DEFAULT NULL,
  `district` varchar(100) DEFAULT NULL,
  `contact_number` varchar(20) DEFAULT NULL,
  `latitude` double DEFAULT NULL,
  `longitude` double DEFAULT NULL,
  `website` varchar(255) DEFAULT NULL,
  `booking_available` tinyint(1) DEFAULT 1
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `clinics`
--

INSERT INTO `clinics` (`id`, `clinic_name`, `address`, `district`, `contact_number`, `latitude`, `longitude`, `website`, `booking_available`) VALUES
(12, 'clove dental', NULL, NULL, NULL, NULL, NULL, 'https://clovedental.in/', 1),
(13, '32 dental', NULL, NULL, NULL, NULL, NULL, 'https://www.32dentalcare.org/', 1);

-- --------------------------------------------------------

--
-- Table structure for table `dealers`
--

CREATE TABLE `dealers` (
  `id` int(11) NOT NULL,
  `name` varchar(100) NOT NULL,
  `email` varchar(120) NOT NULL,
  `phone` varchar(20) DEFAULT NULL,
  `company_name` varchar(150) DEFAULT NULL,
  `password_hash` varchar(255) NOT NULL,
  `dealer_qr_value` varchar(255) DEFAULT NULL,
  `dealer_qr_image` varchar(255) DEFAULT NULL,
  `address` text DEFAULT NULL,
  `username` varchar(100) DEFAULT NULL,
  `city` varchar(100) DEFAULT NULL,
  `state` varchar(100) DEFAULT NULL,
  `location` varchar(150) DEFAULT NULL,
  `is_active` tinyint(1) DEFAULT 1,
  `pincode` varchar(20) DEFAULT NULL,
  `contact_person` varchar(100) DEFAULT NULL,
  `contact_phone` varchar(20) DEFAULT NULL,
  `handle` varchar(100) DEFAULT NULL,
  `active_status` varchar(50) DEFAULT 'Active',
  `is_enabled` tinyint(1) DEFAULT 1,
  `reset_code` varchar(255) DEFAULT NULL,
  `reset_expiry` datetime DEFAULT NULL,
  `email_verified` tinyint(1) DEFAULT 0,
  `email_verification_otp` varchar(10) DEFAULT NULL,
  `email_verification_expiry` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `dealers`
--

INSERT INTO `dealers` (`id`, `name`, `email`, `phone`, `company_name`, `password_hash`, `dealer_qr_value`, `dealer_qr_image`, `address`, `username`, `city`, `state`, `location`, `is_active`, `pincode`, `contact_person`, `contact_phone`, `handle`, `active_status`, `is_enabled`, `reset_code`, `reset_expiry`, `email_verified`, `email_verification_otp`, `email_verification_expiry`) VALUES
(17, 'Appanagiri Sai', 'appanagirisai7569@gmail.com', '9059892833', 'PDS-shop', '$2b$12$npOeYEEtU8DnFQA3AAOKc.gB04hRXmRe2ph0.7ti8C/7FP5xfRDka', 'DLR-17-19A3F741', 'dealer_qr_codes/DLR-17-19A3F741.png', 'POONAMALLE', 'appanagirisai7569@gmail.com', 'chennai', 'Tamil Nadu', 'POONAMALLE', 1, NULL, NULL, NULL, NULL, 'Active', 1, NULL, NULL, 1, '917815', '2026-04-09 05:24:25'),
(18, 'Arjun', 'cyril1991@gmail.com', '9677262688', 'PDS-SAVEETHA', '$2b$12$HgYEjN4ytV.sfEGEZzVQv.kIs8uJFml1mEqtJt5VztKah8uqWt5Sy', 'DLR-18-DEC091C7', 'dealer_qr_codes/DLR-18-DEC091C7.png', 'Ponnamalle', 'cyril1991@gmail.com', 'chennai', 'Tamil Nadu', 'Ponnamalle', 1, NULL, NULL, NULL, NULL, 'Active', 1, NULL, NULL, 1, '283746', '2026-04-09 08:25:50'),
(33, 'Appanagiri ', 'chinna@gmail.com', '9059892833', 'PDS SAVEETHA', '$2b$12$8K3ZWczl0QsfHL0gEVApo.NtdX5bGgOuh0jTsm365hX4cDlN8HP6q', 'DLR-33-0C4C07AF', 'dealer_qr_codes/DLR-33-0C4C07AF.png', 'chinna', 'chinna@gmail.com', 'gajja', 'hshsj', 'chinna', 1, NULL, NULL, NULL, NULL, 'Active', 1, NULL, NULL, 1, NULL, NULL),
(35, 'koti', 'koteswararaop1581.sse@saveetha.com', '8967838898', 'ghgv', '$2b$12$jZvSf0TsOCwYSkR/1178COp/V8tZQcIa7mBuUxHBwbA9TmSESmG2S', 'DLR-35-5DFC375C', 'dealer_qr_codes/DLR-35-5DFC375C.png', ' kjnk', 'koteswararaop1581.sse@saveetha.com', 'lkjlnlk', 'nkj', ' kjnk', 1, NULL, NULL, NULL, NULL, 'Active', 1, NULL, NULL, 1, NULL, NULL),
(37, 'sanjay', 'sanjaykuruvella112@gmail.com', '9059892833', 'jhbibnei', '$2b$12$gMPmT07UqtM0gD.bB4AwF.7PtV/JB5sMQMSBoA1zvHwExrYF1W9Z6', 'DLR-37-CB9BDF1D', 'dealer_qr_codes/DLR-37-CB9BDF1D.png', 'nbdwksjn', 'sanjaykuruvella112@gmail.com', 'jjsknk', 'jsb dk', 'nbdwksjn', 1, NULL, NULL, NULL, NULL, 'Active', 1, NULL, NULL, 1, NULL, NULL),
(38, 'raja', 'shivaraj6t6@gmail.com', '8978190055', 'PDS-SAVEETHA', '$2b$12$3Q9qGJPN0fh8SAZe9jgYXeUmx8nw2I5rGQUDlnpbZE8./mFhx3g/u', 'DLR-38-50CDEE86', 'dealer_qr_codes/DLR-38-50CDEE86.png', 'T Nagar', 'shivaraj6t6@gmail.com', 'chennai', 'Tamil nadu', 'T Nagar', 1, NULL, NULL, NULL, NULL, 'Active', 1, NULL, NULL, 1, NULL, NULL);

-- --------------------------------------------------------

--
-- Table structure for table `dealer_locations`
--

CREATE TABLE `dealer_locations` (
  `id` int(11) NOT NULL,
  `location_name` varchar(150) NOT NULL,
  `dealer_id` int(11) NOT NULL,
  `is_active` tinyint(1) DEFAULT 1,
  `created_at` datetime DEFAULT current_timestamp(),
  `updated_at` datetime DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `dealer_locations`
--

INSERT INTO `dealer_locations` (`id`, `location_name`, `dealer_id`, `is_active`, `created_at`, `updated_at`) VALUES
(10, 'POONAMALLE', 17, 1, '2026-04-09 10:44:25', '2026-04-09 10:44:25'),
(11, 'Ponnamalle', 18, 1, '2026-04-09 13:45:50', '2026-04-09 13:45:50'),
(25, 'chinna', 33, 1, '2026-04-10 09:47:15', '2026-04-10 09:47:15'),
(27, ' kjnk', 35, 1, '2026-04-10 10:58:54', '2026-04-10 10:58:54'),
(29, 'nbdwksjn', 37, 1, '2026-04-10 11:59:41', '2026-04-10 11:59:41'),
(30, 'T Nagar', 38, 1, '2026-04-11 11:47:49', '2026-04-11 11:47:49');

-- --------------------------------------------------------

--
-- Table structure for table `dealer_stock`
--

CREATE TABLE `dealer_stock` (
  `id` int(11) NOT NULL,
  `dealer_id` int(11) NOT NULL,
  `item_name` varchar(100) NOT NULL,
  `quantity` int(11) DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `dealer_stock`
--

INSERT INTO `dealer_stock` (`id`, `dealer_id`, `item_name`, `quantity`) VALUES
(26, 17, 'BRUSH', 17),
(27, 17, 'TOOTHPASTE', 17),
(28, 17, 'FLYER', 17),
(29, 37, 'BRUSH', 9),
(30, 37, 'TOOTHPASTE', 9),
(31, 37, 'FLYER', 9);

-- --------------------------------------------------------

--
-- Table structure for table `family_members`
--

CREATE TABLE `family_members` (
  `id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `member_name` varchar(100) NOT NULL,
  `age` int(11) DEFAULT NULL,
  `brushing_target` int(11) DEFAULT 14,
  `weekly_brush_count` int(11) DEFAULT 0,
  `relation` varchar(50) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `family_members`
--

INSERT INTO `family_members` (`id`, `user_id`, `member_name`, `age`, `brushing_target`, `weekly_brush_count`, `relation`) VALUES
(4, 21, 'Raju ', 16, 14, 1, 'son'),
(5, 21, 'raju ', 17, 14, 0, 'son'),
(9, 12, 'sai', 14, 14, 0, 'son'),
(10, 12, 'rakesh ', 10, 14, 0, 'son'),
(17, 29, 'raja', 15, 14, 0, 'Male'),
(18, 29, 'rani', 18, 14, 0, 'Female'),
(19, 30, 'kim', 15, 14, 0, 'Male'),
(20, 30, 'ram', 13, 14, 0, 'Male'),
(21, 31, 'sai', 15, 14, 0, 'Male'),
(22, 31, 'raj', 16, 14, 0, 'Male'),
(23, 45, 'shiva', 15, 14, 0, 'son'),
(26, 13, 'arjun', 24, 14, 0, 'son'),
(30, 85, 'krishna', 15, 14, 0, 'son'),
(31, 85, 'shiva', 17, 14, 0, 'son');

-- --------------------------------------------------------

--
-- Table structure for table `kit_distributions`
--

CREATE TABLE `kit_distributions` (
  `id` int(11) NOT NULL,
  `beneficiary_id` int(11) NOT NULL,
  `dealer_id` int(11) NOT NULL,
  `kit_unique_id` varchar(100) NOT NULL,
  `status` enum('PENDING','CONFIRMED') DEFAULT 'PENDING',
  `expiry` datetime DEFAULT NULL,
  `confirmed_at` datetime DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `confirmation_mode` varchar(50) DEFAULT 'USER_QR_SCAN',
  `old_kit_returned` tinyint(1) NOT NULL DEFAULT 0,
  `paste_received` int(11) NOT NULL DEFAULT 0,
  `iec_received` int(11) NOT NULL DEFAULT 0,
  `brush_received` int(11) DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `kit_distributions`
--

INSERT INTO `kit_distributions` (`id`, `beneficiary_id`, `dealer_id`, `kit_unique_id`, `status`, `expiry`, `confirmed_at`, `created_at`, `confirmation_mode`, `old_kit_returned`, `paste_received`, `iec_received`, `brush_received`) VALUES
(74, 74, 37, '7e85de21-597a-425a-835e-f0ebc15ff453', 'CONFIRMED', '2026-04-11 06:35:59', '2026-04-10 06:35:59', '2026-04-10 06:35:59', 'DEALER_MANUAL', 1, 1, 1, 1),
(76, 82, 17, '0ec7e159-7566-44a5-a658-eeb6ae3c4ce1', 'CONFIRMED', '2026-04-12 03:02:39', '2026-04-11 03:02:39', '2026-04-11 03:02:39', 'USER_QR_SCAN', 1, 1, 1, 1),
(77, 86, 38, 'f35d2ef0-8621-4ef1-8890-ad522df67673', 'PENDING', '2026-04-12 06:29:17', NULL, '2026-04-11 06:29:17', 'USER_QR_SCAN', 0, 0, 0, 0);

-- --------------------------------------------------------

--
-- Table structure for table `member_monthly_usage`
--

CREATE TABLE `member_monthly_usage` (
  `id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `member_id` int(11) NOT NULL,
  `month_year` varchar(7) NOT NULL,
  `paste_consumption` varchar(30) DEFAULT 'Unknown',
  `brush_condition` varchar(30) DEFAULT 'Unknown',
  `remarks` text DEFAULT NULL,
  `created_at` datetime DEFAULT current_timestamp(),
  `updated_at` datetime DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `registration_otps`
--

CREATE TABLE `registration_otps` (
  `id` int(11) NOT NULL,
  `email` varchar(120) NOT NULL,
  `otp_code` varchar(10) NOT NULL,
  `created_at` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `registration_otps`
--

INSERT INTO `registration_otps` (`id`, `email`, `otp_code`, `created_at`) VALUES
(16, 's49093485@gmail.com', '860772', '2026-04-09 04:47:34'),
(17, 'karjunm338@gmail.com', '621394', '2026-04-09 04:48:49'),
(34, 'shivaraj6t6@gmil.com', '682839', '2026-04-10 04:00:22'),
(39, 'koteswararao1581.sse@saveetha.com', '915682', '2026-04-10 05:27:21');

-- --------------------------------------------------------

--
-- Table structure for table `stock_requests`
--

CREATE TABLE `stock_requests` (
  `id` int(11) NOT NULL,
  `dealer_id` int(11) NOT NULL,
  `item_name` enum('BRUSH','TOOTHPASTE','FLYER','KIT') NOT NULL,
  `requested_quantity` int(11) NOT NULL,
  `total_kits` int(11) DEFAULT 0,
  `status` enum('PENDING','APPROVED','DISPATCHED','DELIVERED','REJECTED') DEFAULT 'PENDING',
  `requested_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `reviewed_at` datetime DEFAULT NULL,
  `request_id` varchar(100) NOT NULL DEFAULT '',
  `urgency` varchar(50) DEFAULT 'Normal',
  `dispatched_at` datetime DEFAULT NULL,
  `courier_name` varchar(120) DEFAULT NULL,
  `tracking_id` varchar(120) DEFAULT NULL,
  `dispatch_address` text DEFAULT NULL,
  `dispatch_city` varchar(100) DEFAULT NULL,
  `dispatch_state` varchar(100) DEFAULT NULL,
  `delivered_at` datetime DEFAULT NULL,
  `admin_note` text DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `stock_requests`
--

INSERT INTO `stock_requests` (`id`, `dealer_id`, `item_name`, `requested_quantity`, `total_kits`, `status`, `requested_at`, `reviewed_at`, `request_id`, `urgency`, `dispatched_at`, `courier_name`, `tracking_id`, `dispatch_address`, `dispatch_city`, `dispatch_state`, `delivered_at`, `admin_note`) VALUES
(86, 17, 'KIT', 10, 10, 'DELIVERED', '2026-04-09 08:43:39', '2026-04-09 08:43:59', 'REQ-D8FC8D03', 'Normal', '2026-04-09 08:44:16', 'DTDC', 'hsskjshs', 'POONAMALLE', 'chennai', 'Tamil Nadu', '2026-04-09 08:47:07', 'nill'),
(87, 37, 'KIT', 10, 10, 'DELIVERED', '2026-04-10 06:32:21', '2026-04-10 06:32:46', 'REQ-401A21A7', 'Normal', '2026-04-10 06:33:01', 'all', '9838', 'nbdwksjn', 'jjsknk', 'jsb dk', '2026-04-10 06:35:26', 'hzhzhshs'),
(88, 17, 'KIT', 10, 10, 'APPROVED', '2026-04-10 08:48:17', '2026-04-10 08:48:59', 'REQ-4CE2965C', 'Normal', NULL, NULL, NULL, 'POONAMALLE', 'chennai', 'Tamil Nadu', NULL, ''),
(89, 17, 'KIT', 10, 10, 'DELIVERED', '2026-04-11 06:12:46', '2026-04-11 06:13:38', 'REQ-07F64BE4', 'Normal', '2026-04-11 06:14:22', 'DTDC', 'xfyteb', 'POONAMALLE', 'chennai', 'Tamil Nadu', '2026-04-11 06:14:30', 'NILL');

-- --------------------------------------------------------

--
-- Table structure for table `teeth_reports`
--

CREATE TABLE `teeth_reports` (
  `id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `member_id` int(11) DEFAULT NULL,
  `image_path` text DEFAULT NULL,
  `ai_result` text DEFAULT NULL,
  `risk_level` enum('LOW','MEDIUM','HIGH') DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `teeth_reports`
--

INSERT INTO `teeth_reports` (`id`, `user_id`, `member_id`, `image_path`, `ai_result`, `risk_level`, `created_at`) VALUES
(5, 12, NULL, 'C:\\xampp\\htdocs\\pdssystem\\uploads\\1fefe1b3-7f3e-4b0f-a00a-a03dec513591_temp_image_1772780441921.jpg', '[{\'class_name\': \'Caries\', \'confidence\': 0.5467813014984131, \'box\': [288.2505798339844, 118.38902282714844, 375.2183532714844, 232.5498809814453]}, {\'class_name\': \'Caries\', \'confidence\': 0.48453405499458313, \'box\': [402.333984375, 151.29173278808594, 471.7346496582031, 236.64871215820312]}]', 'MEDIUM', '2026-03-06 07:00:41'),
(11, 12, NULL, 'C:\\xampp\\htdocs\\pdssystem\\uploads\\33239b17-ea96-463c-868c-5f14ee5fa165_temp_image_1772804353798.jpg', '[{\'class_name\': \'Caries\', \'confidence\': 0.5467813014984131, \'box\': [288.2505798339844, 118.38902282714844, 375.2183532714844, 232.5498809814453]}, {\'class_name\': \'Caries\', \'confidence\': 0.48453405499458313, \'box\': [402.333984375, 151.29173278808594, 471.7346496582031, 236.64871215820312]}]', 'MEDIUM', '2026-03-06 13:39:13'),
(12, 12, NULL, 'C:\\xampp\\htdocs\\pdssystem\\uploads\\d4e126dc-67de-4aa3-a8dd-c54092698eeb_temp_image_1772826547188.jpg', '[{\'class_name\': \'Caries\', \'confidence\': 0.5467813014984131, \'box\': [288.2505798339844, 118.38902282714844, 375.2183532714844, 232.5498809814453]}, {\'class_name\': \'Caries\', \'confidence\': 0.48453405499458313, \'box\': [402.333984375, 151.29173278808594, 471.7346496582031, 236.64871215820312]}]', 'MEDIUM', '2026-03-06 19:49:08'),
(75, 13, 0, 'uploads/fdb6d51e-52b2-4f04-a551-bf201395050a_teeth.jpg', '{\"message\": \"Analysis successful\", \"reportId\": 75, \"riskLevel\": \"MEDIUM\", \"detections\": [{\"class\": \"Caries\", \"confidence\": 0.6594640016555786, \"bbox\": [166.6547393798828, 36.87675857543945, 187.76458740234375, 62.65375518798828]}, {\"class\": \"Caries\", \"confidence\": 0.4609174430370331, \"bbox\": [37.347774505615234, 26.847509384155273, 142.74542236328125, 61.15714645385742]}, {\"class\": \"Caries\", \"confidence\": 0.44269365072250366, \"bbox\": [32.62185287475586, 76.3338394165039, 50.669315338134766, 93.50890350341797]}, {\"class\": \"Caries\", \"confidence\": 0.2862069606781006, \"bbox\": [158.6038818359375, 77.43919372558594, 169.92601013183594, 91.39512634277344]}]}', 'MEDIUM', '2026-04-08 15:44:24'),
(76, 13, 0, 'uploads/10586136-61e5-409b-941a-b1dd23bea32a_teeth.jpg', '{\"message\": \"Analysis successful\", \"reportId\": 76, \"riskLevel\": \"MEDIUM\", \"detections\": [{\"class\": \"Caries\", \"confidence\": 0.6594640016555786, \"bbox\": [166.6547393798828, 36.87675857543945, 187.76458740234375, 62.65375518798828]}, {\"class\": \"Caries\", \"confidence\": 0.4609174430370331, \"bbox\": [37.347774505615234, 26.847509384155273, 142.74542236328125, 61.15714645385742]}, {\"class\": \"Caries\", \"confidence\": 0.44269365072250366, \"bbox\": [32.62185287475586, 76.3338394165039, 50.669315338134766, 93.50890350341797]}, {\"class\": \"Caries\", \"confidence\": 0.2862069606781006, \"bbox\": [158.6038818359375, 77.43919372558594, 169.92601013183594, 91.39512634277344]}]}', 'MEDIUM', '2026-04-09 02:52:46'),
(77, 85, 0, 'uploads/9b34144b-d00d-4eca-b4fb-384ffadf1144_temp_image_1775891348460.jpg', '{\"message\": \"Analysis successful\", \"reportId\": 77, \"riskLevel\": \"LOW\", \"detections\": []}', 'LOW', '2026-04-11 01:39:10');

-- --------------------------------------------------------

--
-- Table structure for table `users`
--

CREATE TABLE `users` (
  `id` int(11) NOT NULL,
  `name` varchar(100) NOT NULL,
  `email` varchar(120) NOT NULL,
  `phone` varchar(20) DEFAULT NULL,
  `password_hash` varchar(255) NOT NULL,
  `pds_card_no` varchar(50) DEFAULT NULL,
  `pds_linked_at` datetime DEFAULT NULL,
  `pds_verified` tinyint(1) DEFAULT 0,
  `reset_code` varchar(255) DEFAULT NULL,
  `reset_expiry` datetime DEFAULT NULL,
  `dealer_id` int(11) DEFAULT NULL,
  `location_id` int(11) DEFAULT NULL,
  `created_by_type` varchar(20) DEFAULT 'SELF',
  `dealer_assigned_at` datetime DEFAULT NULL,
  `dealer_assignment_locked` tinyint(1) DEFAULT 0,
  `pds_card_front` varchar(255) DEFAULT NULL,
  `pds_card_back` varchar(255) DEFAULT NULL,
  `address` text DEFAULT NULL,
  `age` int(11) DEFAULT NULL,
  `gender` varchar(20) DEFAULT NULL,
  `education` varchar(100) DEFAULT NULL,
  `employment` varchar(100) DEFAULT NULL,
  `profile_image` varchar(255) DEFAULT NULL,
  `created_at` datetime DEFAULT current_timestamp(),
  `email_verified` tinyint(1) DEFAULT 0,
  `email_verification_otp` varchar(10) DEFAULT NULL,
  `email_verification_expiry` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `users`
--

INSERT INTO `users` (`id`, `name`, `email`, `phone`, `password_hash`, `pds_card_no`, `pds_linked_at`, `pds_verified`, `reset_code`, `reset_expiry`, `dealer_id`, `location_id`, `created_by_type`, `dealer_assigned_at`, `dealer_assignment_locked`, `pds_card_front`, `pds_card_back`, `address`, `age`, `gender`, `education`, `employment`, `profile_image`, `created_at`, `email_verified`, `email_verification_otp`, `email_verification_expiry`) VALUES
(11, 'Maveen ', 'mave@gamil.com', '9089754631', 'welcome@123', 'PDS-523145', '2026-03-05 23:35:53', 1, NULL, NULL, NULL, NULL, 'SELF', NULL, 0, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, '2026-04-03 11:35:12', 1, NULL, NULL),
(12, 'sasi', 'sasi@gamil.com', '9865321470', 'welcome@123', NULL, NULL, 0, NULL, NULL, NULL, NULL, 'SELF', NULL, 0, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, '2026-04-03 11:35:12', 1, NULL, NULL),
(13, 'rohith', 'rohith@gmail.com', '9867543210', '$2b$12$1nqYW8r0d5EQJQ3OLtNewOHz1tur03X4PmNZ5CiT1w2BZsUzoK2WG', 'PDS-567645', '2026-04-08 19:13:44', 1, NULL, NULL, 11, NULL, 'SELF', '2026-04-08 19:14:09', 1, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, '2026-04-03 11:35:12', 1, NULL, NULL),
(14, 'Appanagiri ', 'appangiri@gamil.com', '9638527412', 'welcome@123', NULL, NULL, 0, NULL, NULL, NULL, NULL, 'SELF', NULL, 0, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, '2026-04-03 11:35:12', 1, NULL, NULL),
(15, 'chandu', 'chandu@gamil.com', '9089765431', 'welcome@123', NULL, NULL, 0, NULL, NULL, NULL, NULL, 'SELF', NULL, 0, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, '2026-04-03 11:35:12', 1, NULL, NULL),
(16, 'Nadh', 'nadh@gamil.com', '9638527410', 'welcome@123', NULL, NULL, 0, NULL, NULL, NULL, NULL, 'SELF', NULL, 0, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, '2026-04-03 11:35:12', 1, NULL, NULL),
(17, 'malli', 'malli@gmail.com', '8052741963', 'welcome@123', NULL, NULL, 0, NULL, NULL, NULL, NULL, 'SELF', NULL, 0, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, '2026-04-03 11:35:12', 1, NULL, NULL),
(18, 'ANJI', 'anji@gmail.com', '9089583211', 'welcome@123', NULL, NULL, 0, NULL, NULL, NULL, NULL, 'SELF', NULL, 0, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, '2026-04-03 11:35:12', 1, NULL, NULL),
(19, 'Reddy', 'reddy@gmail.com', '8097654312', 'welcome@123', NULL, NULL, 0, NULL, NULL, NULL, NULL, 'SELF', NULL, 0, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, '2026-04-03 11:35:12', 1, NULL, NULL),
(21, 'Rao', 'rao@gamil.com', '9806532147', 'welcome@123', 'PDS-573934', '2026-03-06 00:45:11', 1, NULL, NULL, NULL, NULL, 'SELF', '2026-03-17 16:20:54', 1, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, '2026-04-03 11:35:12', 1, NULL, NULL),
(22, 'keshav', 'keshav@gmail.com', '9086754321', 'welcome@123', 'PDS-546346', '2026-03-07 00:19:46', 1, NULL, NULL, NULL, NULL, 'SELF', '2026-03-16 13:02:26', 1, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, '2026-04-03 11:35:12', 1, NULL, NULL),
(23, 'User1', 's49093485@gmail.com', '5555555555', 'welcome@123', NULL, NULL, 0, 'ckPCYE0tEScMm4aQGFhM-m4MCIwDxsTKB9ZpMUXDa48', '2026-03-30 04:32:31', NULL, NULL, 'SELF', NULL, 0, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, '2026-04-03 11:35:12', 1, NULL, NULL),
(24, 'Shiva5', 'raj@gmail.com', '9078645312', 'welcome@123', 'PDS-678546', '2026-03-13 06:34:45', 1, NULL, NULL, NULL, NULL, 'SELF', '2026-03-16 11:45:16', 1, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, '2026-04-03 11:35:12', 1, NULL, NULL),
(26, 'ramesh', 'ramesh@gmail.com', '9706446348', 'welcome@123', 'PDS-456765', '2026-03-13 12:04:34', 1, NULL, NULL, NULL, NULL, 'DEALER', NULL, 0, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, '2026-04-03 11:35:12', 1, NULL, NULL),
(29, 'Ganesh', 'Ganesh@gmail.com', '8052963147', 'welcome@123', 'PDS-523148', '2026-04-02 03:37:25', 1, NULL, NULL, 9, NULL, 'DEALER', '2026-04-02 03:37:25', 1, 'uploads/pds_cards/front_00b1acb1-ea19-4ac9-bac6-be568c86e80f_front.jpg', 'uploads/pds_cards/back_1a56a0bc-1e10-4189-85f1-30a4adc704b0_back.jpg', NULL, NULL, NULL, NULL, NULL, NULL, '2026-04-03 11:35:12', 1, NULL, NULL),
(30, 'RAMESH', 'ramesh1@gmail.com', '7584643108', 'welcome@123', 'PDS-584927', '2026-04-02 03:56:29', 1, NULL, NULL, 9, NULL, 'DEALER', '2026-04-02 03:56:29', 1, 'uploads/pds_cards/front_09e7ae2f-6de2-49e2-b67a-cb9e6a3bae12_front.jpg', 'uploads/pds_cards/back_45e2d469-abb5-483f-b9c3-f3b1ec9bf3d1_back.jpg', 'kilambakam', 30, 'Male', 'Primary', 'Government Job', NULL, '2026-04-03 11:35:12', 1, NULL, NULL),
(31, 'Vignesh', 'vignesh@gmail.com', '8649453194', 'welcome@123', 'PDS-567245', '2026-04-02 04:42:35', 1, NULL, NULL, 9, NULL, 'ADMIN', '2026-04-02 04:42:35', 1, 'uploads/pds_cards/front_e6f5206e-878c-410c-baae-4bde2e6dc922_front.jpg', 'uploads/pds_cards/back_5ca41db3-6d01-4c16-9335-d9e5eaee2c4b_back.jpg', 'Avadi', 30, 'Male', 'Intermediate', 'Private Job', NULL, '2026-04-03 11:35:12', 1, NULL, NULL),
(32, 'Raheem', 'raheem@gamil.com', '8461648648', 'Raheem@123', 'httpscanovaio', '2026-04-02 10:49:49', 1, NULL, NULL, NULL, NULL, 'SELF', NULL, 0, NULL, NULL, 'poonamalle', 47, 'Male', 'Undergraduate', 'Private Sector', NULL, '2026-04-03 11:35:12', 1, NULL, NULL),
(33, 'Suresh', 'suresh@gamil.com', '8731649487', 'Suresh@123', 'httpenmwikip', '2026-04-02 10:57:17', 1, NULL, NULL, NULL, NULL, 'SELF', NULL, 0, NULL, NULL, 'pooonamallee', 38, 'Male', 'Undergraduate', 'Self-Employed', NULL, '2026-04-03 11:35:12', 1, NULL, NULL),
(34, 'Harish', 'harish@gmail.com', '9494694945', 'Harish@123', 'vsjsjabsha', '2026-04-02 10:58:48', 1, NULL, NULL, NULL, NULL, 'SELF', NULL, 0, NULL, NULL, 'ponnalmale', 38, 'Male', 'Undergraduate', 'Self-Employed', NULL, '2026-04-03 11:35:12', 1, NULL, NULL),
(35, 'Vikram', 'vikram@gmail.com', '8976451321', 'Vikram@123', NULL, NULL, 0, NULL, NULL, NULL, NULL, 'SELF', NULL, 0, NULL, NULL, 'avadi', 39, 'Male', 'Undergraduate', 'Self-Employed', NULL, '2026-04-03 11:35:12', 1, NULL, NULL),
(36, 'sikram', 'sikram@gmail.com', '8976325401', 'Sikram@123', 'PDS-876456', '2026-04-02 12:46:37', 1, NULL, NULL, 9, NULL, 'SELF', '2026-04-02 07:16:53', 1, NULL, NULL, 'Avadi', 39, 'Male', 'Undergraduate', 'Self-Employed', NULL, '2026-04-03 11:35:12', 1, NULL, NULL),
(37, 'Abhishek ', 'abhishek@gmail.com', '8794384358', 'Abhishek@123', 'PDS-783645', '2026-04-02 19:30:47', 1, NULL, NULL, NULL, NULL, 'SELF', NULL, 0, NULL, NULL, 'avadi', 35, 'Male', 'Undergraduate', 'Self-Employed', NULL, '2026-04-03 11:35:12', 1, NULL, NULL),
(38, 'Head', 'head@gamil.com', '8046434849', 'Head@123', 'PDS-638627', '2026-04-02 19:44:14', 1, NULL, NULL, NULL, NULL, 'SELF', NULL, 0, NULL, NULL, 'poonamalle', 38, 'Male', 'Undergraduate', 'Self-Employed', NULL, '2026-04-03 11:35:12', 1, NULL, NULL),
(39, 'Rayudu', 'rayudu@gmail.com', '8672484348', 'Rayudu@123', 'PDS-176737', '2026-04-02 19:50:33', 1, NULL, NULL, NULL, NULL, 'SELF', NULL, 0, NULL, NULL, 'poonamalle ', 38, 'Male', 'Undergraduate', 'Self-Employed', NULL, '2026-04-03 11:35:12', 1, NULL, NULL),
(40, 'Supraja', 'supraja@gmail.com', '8734849646', 'Supraja@123', 'PDS-126836', '2026-04-02 19:58:22', 1, NULL, NULL, NULL, NULL, 'SELF', NULL, 0, NULL, NULL, 'poonamalle', 38, 'Male', 'Undergraduate', 'Self-Employed', NULL, '2026-04-03 11:35:12', 1, NULL, NULL),
(41, 'Janaki', 'janaki@gmail.com', '8643484846', 'Janaki@123', 'PDS-461862', '2026-04-02 20:09:54', 1, NULL, NULL, NULL, NULL, 'SELF', NULL, 0, NULL, NULL, 'poonamalle ', 35, 'Male', 'Undergraduate', 'Self-Employed', NULL, '2026-04-03 11:35:12', 1, NULL, NULL),
(42, 'Gani', 'gani@gmail.com', '8646494846', 'Gani@123', 'PDS-638539', '2026-04-02 20:14:09', 1, NULL, NULL, 9, NULL, 'SELF', '2026-04-02 14:44:11', 1, NULL, NULL, 'poonamalle ', 38, 'Male', 'Undergraduate', 'Self-Employed', NULL, '2026-04-03 11:35:12', 1, NULL, NULL),
(44, 'Kishan', 'kishan@gmail.com', '8434248464', 'Kishan@123', 'PDS-583528', '2026-04-02 22:35:34', 1, NULL, NULL, 9, NULL, 'SELF', '2026-04-02 17:05:36', 1, NULL, NULL, 'poonamalle ', 38, 'Male', 'Undergraduate', 'Self-Employed', NULL, '2026-04-03 11:35:12', 1, NULL, NULL),
(45, 'Rinku', 'rinku@gmail.com', '8435494649', '$2b$12$MqppcQmDE2VVodmqonp1iesMw.H/JnPYA3UBTst2Ex9sm11FH9YeW', 'PDS-638363', '2026-04-02 22:38:48', 1, NULL, NULL, 9, NULL, 'SELF', '2026-04-02 17:08:50', 1, NULL, NULL, 'poonamalle ', 35, 'Male', 'Undergraduate', 'Self-Employed', 'uploads/profile_pictures/profile_7e681a3f-8f83-4269-864c-bae8fdc4c5db_profile.jpg', '2026-04-03 11:35:12', 1, NULL, NULL),
(46, 'Kanna', 'kanna@gmail.com', '8946484319', 'Kanna@123', 'PDS-538352', '2026-04-02 22:45:32', 1, NULL, NULL, 9, NULL, 'SELF', '2026-04-02 17:15:35', 1, NULL, NULL, 'poonamalle ', 38, 'Male', 'Undergraduate', 'Self-Employed', 'uploads/profile_pictures/profile_9ecd9403-3e92-4148-8e33-3ffc76c8e3e8_profile.jpg', '2026-04-03 11:35:12', 1, NULL, NULL),
(47, 'Sanjay1', 'sanjay1@gmail.com', '8973484319', 'Sanjay@123', 'PDS-573682', '2026-04-02 23:19:20', 1, NULL, NULL, 9, NULL, 'SELF', '2026-04-02 17:49:22', 1, NULL, NULL, 'poonamalle ', 35, 'Male', 'Undergraduate', 'Self-Employed', 'uploads/profile_pictures/profile_3a60250b-77dc-45d7-b3a0-039a62d90598_profile.jpg', '2026-04-03 11:35:12', 1, NULL, NULL),
(48, 'Asriya', 'asriya@gmail.com', '8943494494', 'Asriya@123', 'PDS-687368', '2026-04-02 23:49:31', 1, NULL, NULL, 9, NULL, 'SELF', '2026-04-02 18:19:33', 1, NULL, NULL, 'poonamalle ', 38, 'Male', 'Undergraduate', 'Self-Employed', NULL, '2026-04-03 11:35:12', 1, NULL, NULL),
(49, 'Asriya1', 'asriya1@gmail.com', '9648543494', 'Asriya@123', 'PDS-682682', '2026-04-02 23:51:24', 1, NULL, NULL, 9, NULL, 'SELF', '2026-04-02 18:21:26', 1, NULL, NULL, 'poonamalle ', 28, 'Male', 'Undergraduate', 'Self-Employed', 'uploads/profile_pictures/user_49_83322e91_profile_upload_1775154410614.jpg', '2026-04-03 11:35:12', 1, NULL, NULL),
(50, 'One', 'one@gmail.com', '8943481894', 'One@1234', 'PDS-573568', '2026-04-03 05:37:54', 1, NULL, NULL, 9, NULL, 'SELF', '2026-04-03 00:07:56', 1, NULL, NULL, 'poonamalle ', 35, 'Male', 'Undergraduate', 'Self-Employed', 'uploads/profile_pictures/profile_54785481-1787-45bd-a551-43cdbf725b58_profile.jpg', '2026-04-03 11:35:12', 1, NULL, NULL),
(51, 'Rasool', 'rasool@gmail.com', '8643484946', 'Rasool@123', 'PDS-123573', '2026-04-03 09:06:04', 1, NULL, NULL, 9, NULL, 'SELF', '2026-04-03 03:36:05', 1, NULL, NULL, 'poonamalle', 35, 'Male', 'Undergraduate', 'Self-Employed', NULL, '2026-04-03 11:35:12', 1, NULL, NULL),
(52, 'Sabir', 'sabir@gmail.com', '8646494945', 'Sabir@123', 'PDS-283745', '2026-04-03 09:32:57', 1, NULL, NULL, 9, NULL, 'SELF', '2026-04-03 04:03:01', 1, NULL, NULL, 'poonamalle ', 38, 'Male', 'Undergraduate', 'Self-Employed', NULL, '2026-04-03 11:35:12', 1, NULL, NULL),
(56, 'krishna', 'krishana123@gmail.com', '9059892835', '$2b$12$gHxD97LqtRAgxUy7mDUIhepqcKz7/YJ.7n6OgH4ntKQFe2ArAXaLW', 'PDS-572936', '2026-04-07 15:51:49', 1, NULL, NULL, 15, NULL, 'ADMIN', '2026-04-07 15:51:49', 1, NULL, NULL, 'poonamalle ', 35, 'Male', 'Graduate', 'Government Job', NULL, '2026-04-07 21:21:49', 1, NULL, NULL),
(57, 'kareem', 'kareem@gmail.com', '8978190053', '$2b$12$Bxkvx0dR5gb8F3GbfRqU0uBXjA2UOvg5r9Mb8Eq46zKnO685X7kKO', 'PDS-584674', '2026-04-07 16:14:22', 1, NULL, NULL, 11, NULL, 'DEALER', '2026-04-07 16:14:22', 1, NULL, NULL, 'poonamalle', 35, 'Male', '', '', NULL, '2026-04-07 21:44:22', 1, NULL, NULL),
(58, 'haseem', 'hassem@gmail.com', '8397488928', '$2b$12$SR9BGRT88Ads/KBUp3/x/ebZwwCNGl7nEIo642p59xFoEndKUhqba', 'PDS-763783', '2026-04-07 19:53:52', 1, NULL, NULL, 15, NULL, 'DEALER', '2026-04-07 19:53:52', 1, NULL, NULL, 'poonamelle', 35, 'Male', 'Secondary', 'Self-Employed', NULL, '2026-04-08 01:23:52', 1, NULL, NULL),
(59, 'chinna', 'nill', '9580231478', '$2b$12$gY0pW9bBsMQ4OI1kJIAdMOa/vt.6p.szPskF9SQMyCUjbF/50.hty', 'PDS-574795', '2026-04-08 00:52:10', 1, NULL, NULL, 15, NULL, 'DEALER', '2026-04-08 00:52:10', 1, NULL, NULL, 'poonamelle', 35, 'Male', 'Intermediate', 'Daily Wage', NULL, '2026-04-08 06:22:10', 1, NULL, NULL),
(66, 'arjun', 'cyril1991@gmail.com', '8978190053', '$2b$12$m17Ce95wiDDUY33snbl5COvU0/7ADVVuqlgvrRyNnPDX7uphayfHi', 'PDS-765678', '2026-04-09 08:27:55', 1, NULL, NULL, 18, 11, 'SELF', '2026-04-09 08:28:21', 1, NULL, NULL, 'poonamalle', 56, 'Male', 'Higher', 'Employed', 'uploads/profile_pictures/profile_1f323b81-c74f-4ec3-bfbb-f44481920f6e_WhatsApp_Image_2026-04-05_at_10.53.17_1.jpeg', '2026-04-09 13:57:34', 1, '921253', '2026-04-09 08:37:34'),
(74, 'sanjay', 'sanjay@gmail.com', '9059892836', '$2b$12$1O6lKaz2g5375E6zeenaqeBoD1Uueh/VAxQzRXy31I40V29X4xIoK', 'PDS-567865', '2026-04-10 06:31:19', 1, NULL, NULL, 37, 29, 'DEALER', '2026-04-10 06:31:19', 1, NULL, NULL, 'kjsnikcnhdssindc', 34, 'Male', 'Secondary', 'Self-Employed', NULL, '2026-04-10 12:01:19', 1, NULL, NULL),
(82, 'chinna', 'koteswararaop1581.sse@saveetha.com', '9086532147', '$2b$12$n/Y3FWCEjQovjfk6ItvmOuRIJql.o0/K6DIL9OS8dsjxZCixnR2aW', 'PDS-567890', '2026-04-11 03:01:11', 1, NULL, NULL, 17, 10, 'SELF', '2026-04-11 03:01:13', 1, NULL, NULL, 'poonamalle ', 35, 'Male', 'Undergraduate', 'Self-Employed', NULL, '2026-04-11 08:31:04', 1, '549925', '2026-04-11 03:11:04'),
(83, 'Krish', 'nill@gmail.com', '9807654231', '$2b$12$K0KAGOvHUjLT7PA1cW9ZJerxTeeeXWM1v0WjU4eplK7DbOt/Y6z5.', 'PDS-458956', '2026-04-11 03:08:22', 1, NULL, NULL, 17, 10, 'DEALER', '2026-04-11 03:08:22', 1, NULL, NULL, 'poonamalle', 65, 'Male', 'Primary', 'Self-Employed', NULL, '2026-04-11 08:38:22', 1, NULL, NULL),
(84, 'mani', 'none', '8956231470', '$2b$12$WER1OvPR7H1vDbSs4Db68.Pb3NHKE7.AiVi2bBlpscqq.KJIY/2Vi', 'PDS-682667', '2026-04-11 03:12:23', 1, NULL, NULL, 17, 10, 'DEALER', '2026-04-11 03:12:23', 1, 'uploads/pds_cards/front_71cd4ab2-07ca-41d1-8f6f-f486d4620798_front.jpg', 'uploads/pds_cards/back_3549515d-cbc3-43c8-9f3d-535ebe6c2335_back.jpg', 'ponamalle', 35, 'Male', 'Primary', 'Daily Wage', NULL, '2026-04-11 08:42:23', 1, NULL, NULL),
(85, 'Sai', 'appanagirisai7569@gmail.com', '9089592833', '$2b$12$tbmt7HrMy6N5UVi/ZlqfiekDxO0ZUC96k0O9opJ6z8QvVZJBUzy5m', 'PDS-569867', '2026-04-11 05:56:44', 1, NULL, NULL, 17, 10, 'SELF', '2026-04-11 05:56:48', 1, NULL, NULL, 'poonamalle', 50, 'Male', 'Secondary', 'Self-Employed', 'uploads/profile_pictures/profile_0097bcaf-96dc-4b33-bc66-578676b9e2b7_WhatsApp_Image_2026-04-10_at_13.28.23_1.jpeg', '2026-04-11 11:26:31', 1, '988786', '2026-04-11 06:06:31'),
(86, 'Shivaraj', 'shivaraj6t6@gmail.com', '8977190053', '$2b$12$VarXIevNDSIdWcw078sahuaZ/T2ORAdBggyVYXBXX5JthWCuqjFbi', 'PDS-563428', '2026-04-11 06:24:47', 1, NULL, NULL, 38, 30, 'SELF', '2026-04-11 06:27:15', 1, NULL, NULL, 'T.nagar', 50, 'Male', 'Secondary', 'Self-Employed', NULL, '2026-04-11 11:54:38', 1, '398186', '2026-04-11 06:34:38');

--
-- Indexes for dumped tables
--

--
-- Indexes for table `admins`
--
ALTER TABLE `admins`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `email` (`email`);

--
-- Indexes for table `appointments`
--
ALTER TABLE `appointments`
  ADD PRIMARY KEY (`id`),
  ADD KEY `user_id` (`user_id`),
  ADD KEY `clinic_id` (`clinic_id`);

--
-- Indexes for table `brushing_checkins`
--
ALTER TABLE `brushing_checkins`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `unique_member_date_session` (`user_id`,`member_id`,`checkin_date`,`session`);

--
-- Indexes for table `brushing_logs`
--
ALTER TABLE `brushing_logs`
  ADD PRIMARY KEY (`id`),
  ADD KEY `user_id` (`user_id`),
  ADD KEY `member_id` (`member_id`);

--
-- Indexes for table `clinics`
--
ALTER TABLE `clinics`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `dealers`
--
ALTER TABLE `dealers`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `email` (`email`),
  ADD UNIQUE KEY `dealer_qr_value` (`dealer_qr_value`);

--
-- Indexes for table `dealer_locations`
--
ALTER TABLE `dealer_locations`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `location_name` (`location_name`),
  ADD KEY `dealer_id` (`dealer_id`);

--
-- Indexes for table `dealer_stock`
--
ALTER TABLE `dealer_stock`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `unique_dealer_item` (`dealer_id`,`item_name`);

--
-- Indexes for table `family_members`
--
ALTER TABLE `family_members`
  ADD PRIMARY KEY (`id`),
  ADD KEY `user_id` (`user_id`);

--
-- Indexes for table `kit_distributions`
--
ALTER TABLE `kit_distributions`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `kit_unique_id` (`kit_unique_id`),
  ADD KEY `beneficiary_id` (`beneficiary_id`),
  ADD KEY `dealer_id` (`dealer_id`);

--
-- Indexes for table `member_monthly_usage`
--
ALTER TABLE `member_monthly_usage`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `registration_otps`
--
ALTER TABLE `registration_otps`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `email` (`email`);

--
-- Indexes for table `stock_requests`
--
ALTER TABLE `stock_requests`
  ADD PRIMARY KEY (`id`),
  ADD KEY `dealer_id` (`dealer_id`);

--
-- Indexes for table `teeth_reports`
--
ALTER TABLE `teeth_reports`
  ADD PRIMARY KEY (`id`),
  ADD KEY `user_id` (`user_id`);

--
-- Indexes for table `users`
--
ALTER TABLE `users`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `email` (`email`),
  ADD KEY `fk_users_location` (`location_id`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `admins`
--
ALTER TABLE `admins`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=5;

--
-- AUTO_INCREMENT for table `appointments`
--
ALTER TABLE `appointments`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- AUTO_INCREMENT for table `brushing_checkins`
--
ALTER TABLE `brushing_checkins`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=239;

--
-- AUTO_INCREMENT for table `brushing_logs`
--
ALTER TABLE `brushing_logs`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `clinics`
--
ALTER TABLE `clinics`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=14;

--
-- AUTO_INCREMENT for table `dealers`
--
ALTER TABLE `dealers`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=39;

--
-- AUTO_INCREMENT for table `dealer_locations`
--
ALTER TABLE `dealer_locations`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=31;

--
-- AUTO_INCREMENT for table `dealer_stock`
--
ALTER TABLE `dealer_stock`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=32;

--
-- AUTO_INCREMENT for table `family_members`
--
ALTER TABLE `family_members`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=32;

--
-- AUTO_INCREMENT for table `kit_distributions`
--
ALTER TABLE `kit_distributions`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=78;

--
-- AUTO_INCREMENT for table `member_monthly_usage`
--
ALTER TABLE `member_monthly_usage`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `registration_otps`
--
ALTER TABLE `registration_otps`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=54;

--
-- AUTO_INCREMENT for table `stock_requests`
--
ALTER TABLE `stock_requests`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=90;

--
-- AUTO_INCREMENT for table `teeth_reports`
--
ALTER TABLE `teeth_reports`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=78;

--
-- AUTO_INCREMENT for table `users`
--
ALTER TABLE `users`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=87;

--
-- Constraints for dumped tables
--

--
-- Constraints for table `appointments`
--
ALTER TABLE `appointments`
  ADD CONSTRAINT `appointments_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `appointments_ibfk_2` FOREIGN KEY (`clinic_id`) REFERENCES `clinics` (`id`) ON DELETE CASCADE;

--
-- Constraints for table `brushing_logs`
--
ALTER TABLE `brushing_logs`
  ADD CONSTRAINT `brushing_logs_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`),
  ADD CONSTRAINT `brushing_logs_ibfk_2` FOREIGN KEY (`member_id`) REFERENCES `family_members` (`id`);

--
-- Constraints for table `dealer_locations`
--
ALTER TABLE `dealer_locations`
  ADD CONSTRAINT `dealer_locations_ibfk_1` FOREIGN KEY (`dealer_id`) REFERENCES `dealers` (`id`) ON DELETE CASCADE;

--
-- Constraints for table `dealer_stock`
--
ALTER TABLE `dealer_stock`
  ADD CONSTRAINT `dealer_stock_ibfk_1` FOREIGN KEY (`dealer_id`) REFERENCES `dealers` (`id`) ON DELETE CASCADE;

--
-- Constraints for table `family_members`
--
ALTER TABLE `family_members`
  ADD CONSTRAINT `family_members_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE;

--
-- Constraints for table `kit_distributions`
--
ALTER TABLE `kit_distributions`
  ADD CONSTRAINT `kit_distributions_ibfk_1` FOREIGN KEY (`beneficiary_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `kit_distributions_ibfk_2` FOREIGN KEY (`dealer_id`) REFERENCES `dealers` (`id`) ON DELETE CASCADE;

--
-- Constraints for table `stock_requests`
--
ALTER TABLE `stock_requests`
  ADD CONSTRAINT `stock_requests_ibfk_1` FOREIGN KEY (`dealer_id`) REFERENCES `dealers` (`id`) ON DELETE CASCADE;

--
-- Constraints for table `teeth_reports`
--
ALTER TABLE `teeth_reports`
  ADD CONSTRAINT `teeth_reports_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE;

--
-- Constraints for table `users`
--
ALTER TABLE `users`
  ADD CONSTRAINT `fk_users_location` FOREIGN KEY (`location_id`) REFERENCES `dealer_locations` (`id`) ON DELETE SET NULL;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;

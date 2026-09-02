
-- Error loading dashboard: Failed to fetch


-- ============================================
-- Smart Medicine Reminder System
-- Database Schema Creation Script
-- ============================================
-- Version: 1.0
-- Date: October 25, 2025
-- Database: MySQL 8.0+
-- ============================================

-- Drop database if exists (use with caution)
-- DROP DATABASE IF EXISTS medreminder_db;

-- Create database
CREATE DATABASE IF NOT EXISTS medreminder_db;
USE medreminder_db;

-- ============================================
-- 1. USERS TABLE
-- ============================================
-- Stores all system users (patients, caregivers, doctors)

CREATE TABLE Users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    role ENUM('patient', 'caregiver', 'doctor') NOT NULL,
    contact_info VARCHAR(100),
    email VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    created_by INT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (created_by) REFERENCES Users(id) ON DELETE SET NULL,
    INDEX idx_role (role),
    INDEX idx_email (email),
    INDEX idx_created_by (created_by)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- 2. MEDICINES TABLE
-- ============================================
-- Stores medicine information linked to users

CREATE TABLE Medicines (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    name VARCHAR(100) NOT NULL,
    dosage VARCHAR(50) NOT NULL,
    instructions TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES Users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- 3. SCHEDULES TABLE
-- ============================================
-- Defines when medicines should be taken

CREATE TABLE Schedules (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    medicine_id INT NOT NULL,
    schedule_time TIME NOT NULL,
    days_of_week VARCHAR(50) NOT NULL COMMENT 'Comma-separated days (e.g., Mon,Wed,Fri)',
    start_date DATE NOT NULL,
    end_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES Users(id) ON DELETE CASCADE,
    FOREIGN KEY (medicine_id) REFERENCES Medicines(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_medicine_id (medicine_id),
    INDEX idx_schedule_time (schedule_time),
    INDEX idx_start_date (start_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- 4. INTAKE LOGS TABLE
-- ============================================
-- Tracks actual medicine intake events and weight sensor telemetry

CREATE TABLE IntakeLogs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    medicine_id INT NOT NULL,
    scheduled_time DATETIME NOT NULL,
    actual_time DATETIME,
    status ENUM('taken', 'missed', 'pending') NOT NULL DEFAULT 'pending',
    weight_before DECIMAL(6,2) DEFAULT NULL COMMENT 'Pill container weight before schedule in grams',
    weight_after DECIMAL(6,2) DEFAULT NULL COMMENT 'Pill container weight after dose in grams',
    delta_weight DECIMAL(6,2) DEFAULT NULL COMMENT 'Weight change detected (weight_before - weight_after)',
    verification_method ENUM('weight_sensor', 'camera_vision', 'caregiver_manual') DEFAULT 'weight_sensor',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES Users(id) ON DELETE CASCADE,
    FOREIGN KEY (medicine_id) REFERENCES Medicines(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_medicine_id (medicine_id),
    INDEX idx_status (status),
    INDEX idx_scheduled_time (scheduled_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- 5. NOTIFICATIONS TABLE
-- ============================================
-- Stores all system notifications sent to users

CREATE TABLE Notifications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    message TEXT NOT NULL,
    sent_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    type ENUM('reminder', 'alert', 'info') NOT NULL,
    
    FOREIGN KEY (user_id) REFERENCES Users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_type (type),
    INDEX idx_sent_time (sent_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- 6. PATIENT-DOCTOR LINKS TABLE
-- ============================================
-- Assigns doctors to patients

CREATE TABLE IF NOT EXISTS PatientDoctorLinks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id INT NOT NULL,
    doctor_id INT NOT NULL,
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES Users(id) ON DELETE CASCADE,
    FOREIGN KEY (doctor_id) REFERENCES Users(id) ON DELETE CASCADE,
    UNIQUE KEY unique_patient_doctor (patient_id, doctor_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- 7. MESSAGES TABLE
-- ============================================
-- Doctor-patient secure messaging log

CREATE TABLE IF NOT EXISTS Messages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    sender_id INT NOT NULL,
    receiver_id INT NOT NULL,
    message TEXT NOT NULL,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_read TINYINT(1) DEFAULT 0,
    FOREIGN KEY (sender_id) REFERENCES Users(id) ON DELETE CASCADE,
    FOREIGN KEY (receiver_id) REFERENCES Users(id) ON DELETE CASCADE,
    INDEX idx_sender (sender_id),
    INDEX idx_receiver (receiver_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- 8. APPOINTMENTS TABLE
-- ============================================
-- Appointment requests between patients and doctors

CREATE TABLE IF NOT EXISTS Appointments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id INT NOT NULL,
    doctor_id INT NOT NULL,
    requested_date DATE NOT NULL,
    requested_time TIME NOT NULL,
    notes TEXT,
    status ENUM('pending', 'accepted', 'declined') DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES Users(id) ON DELETE CASCADE,
    FOREIGN KEY (doctor_id) REFERENCES Users(id) ON DELETE CASCADE,
    INDEX idx_patient (patient_id),
    INDEX idx_doctor (doctor_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- SAMPLE DATA INSERTION (Optional)
-- ============================================
-- Uncomment the following lines to insert sample data

-- Insert sample users
INSERT INTO Users (name, role, contact_info, email, password) VALUES
('John Smith', 'patient', '555-1234', 'john@example.com', 'password123'),
('Elena Garcia', 'patient', '555-5678', 'elena@example.com', 'password123'),
('Carey Nurse', 'caregiver', '555-9012', 'carey@example.com', 'password123'),
('Sophie Tran', 'caregiver', '555-3456', 'sophie@example.com', 'password123'),
('Dr. Gregory', 'doctor', '555-7890', 'gregory@example.com', 'password123'),
('Dr. Chen', 'doctor', '555-2468', 'chen@example.com', 'password123');

-- Insert sample medicines
INSERT INTO Medicines (user_id, name, dosage, instructions) VALUES
(1, 'Aspirin', '100mg', 'Take with food in the morning'),
(1, 'Metformin', '500mg', 'Take twice daily with meals'),
(2, 'Lisinopril', '10mg', 'Take once daily in the morning'),
(2, 'Atorvastatin', '20mg', 'Take at bedtime');

-- Insert sample schedules
INSERT INTO Schedules (user_id, medicine_id, schedule_time, days_of_week, start_date, end_date) VALUES
(1, 1, '08:00:00', 'Mon,Tue,Wed,Thu,Fri,Sat,Sun', '2025-10-01', '2025-12-31'),
(1, 2, '08:00:00', 'Mon,Tue,Wed,Thu,Fri,Sat,Sun', '2025-10-01', '2025-12-31'),
(1, 2, '20:00:00', 'Mon,Tue,Wed,Thu,Fri,Sat,Sun', '2025-10-01', '2025-12-31'),
(2, 3, '09:00:00', 'Mon,Tue,Wed,Thu,Fri,Sat,Sun', '2025-10-01', NULL),
(2, 4, '22:00:00', 'Mon,Tue,Wed,Thu,Fri,Sat,Sun', '2025-10-01', NULL);

-- Insert sample intake logs
INSERT INTO IntakeLogs (user_id, medicine_id, scheduled_time, actual_time, status) VALUES
(1, 1, '2025-10-25 08:00:00', '2025-10-25 08:05:00', 'taken'),
(1, 2, '2025-10-25 08:00:00', '2025-10-25 08:10:00', 'taken'),
(1, 2, '2025-10-25 20:00:00', NULL, 'missed'),
(2, 3, '2025-10-25 09:00:00', '2025-10-25 09:02:00', 'taken'),
(2, 4, '2025-10-25 22:00:00', NULL, 'pending');

-- Insert sample notifications
INSERT INTO Notifications (user_id, message, type) VALUES
(1, 'Time to take your Aspirin (100mg)', 'reminder'),
(1, 'You missed your evening Metformin dose', 'alert'),
(2, 'Your Lisinopril prescription needs refill', 'info'),
(2, 'Remember to take your bedtime medication', 'reminder');

-- ============================================
-- VERIFICATION QUERIES
-- ============================================
-- Run these to verify the schema and data

-- Check all tables
-- SHOW TABLES;

-- Verify table structures
-- DESCRIBE Users;
-- DESCRIBE Medicines;
-- DESCRIBE Schedules;
-- DESCRIBE IntakeLogs;
-- DESCRIBE Notifications;

-- Count records in each table
-- SELECT 'Users' AS table_name, COUNT(*) AS record_count FROM Users
-- UNION ALL
-- SELECT 'Medicines', COUNT(*) FROM Medicines
-- UNION ALL
-- SELECT 'Schedules', COUNT(*) FROM Schedules
-- UNION ALL
-- SELECT 'IntakeLogs', COUNT(*) FROM IntakeLogs
-- UNION ALL
-- SELECT 'Notifications', COUNT(*) FROM Notifications;

-- ============================================
-- USEFUL QUERIES FOR TESTING
-- ============================================

-- Get all medicines for a specific user
-- SELECT m.id, m.name, m.dosage, m.instructions 
-- FROM Medicines m 
-- WHERE m.user_id = 1;

-- Get all schedules with medicine and user details
-- SELECT s.id, u.name AS user_name, m.name AS medicine_name, 
--        s.schedule_time, s.days_of_week, s.start_date, s.end_date
-- FROM Schedules s
-- JOIN Users u ON s.user_id = u.id
-- JOIN Medicines m ON s.medicine_id = m.id;

-- Get intake logs with details
-- SELECT il.id, u.name AS user_name, m.name AS medicine_name,
--        il.scheduled_time, il.actual_time, il.status
-- FROM IntakeLogs il
-- JOIN Users u ON il.user_id = u.id
-- JOIN Medicines m ON il.medicine_id = m.id
-- ORDER BY il.scheduled_time DESC;

-- Get all notifications for a user
-- SELECT n.id, n.message, n.sent_time, n.type
-- FROM Notifications n
-- WHERE n.user_id = 1
-- ORDER BY n.sent_time DESC;

-- ============================================
-- MAINTENANCE QUERIES
-- ============================================

-- Clear all data (keep tables)
-- TRUNCATE TABLE Notifications;
-- TRUNCATE TABLE IntakeLogs;
-- TRUNCATE TABLE Schedules;
-- TRUNCATE TABLE Medicines;
-- TRUNCATE TABLE Users;

-- Drop all tables (use with extreme caution)
-- DROP TABLE IF EXISTS Notifications;
-- DROP TABLE IF EXISTS IntakeLogs;
-- DROP TABLE IF EXISTS Schedules;
-- DROP TABLE IF EXISTS Medicines;
-- DROP TABLE IF EXISTS Users;

-- ============================================
-- END OF SCHEMA
-- ============================================
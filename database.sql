-- Create tables based on the SS12000 standard
CREATE DATABASE IF NOT EXISTS ss12000_db;

USE ss12000_db;

-- Drop tables if they exist to allow for clean re-creation
-- The order is important due to foreign key constraints
DROP TABLE IF EXISTS subscriptions;
DROP TABLE IF EXISTS log;
DROP TABLE IF EXISTS deletedEntities;
DROP TABLE IF EXISTS aggregatedAttendance;
DROP TABLE IF EXISTS grades;
DROP TABLE IF EXISTS attendance;
DROP TABLE IF EXISTS attendanceEvents;
DROP TABLE IF EXISTS calendarEvents;
DROP TABLE IF EXISTS activities;
DROP TABLE IF EXISTS schoolUnitOfferings;
DROP TABLE IF EXISTS syllabuses;
DROP TABLE IF EXISTS studyPlans;
DROP TABLE IF EXISTS programmes;
DROP TABLE IF EXISTS groups;
DROP TABLE IF EXISTS duties;
DROP TABLE IF EXISTS placements;
DROP TABLE IF EXISTS persons;
DROP TABLE IF EXISTS organisations;
DROP TABLE IF EXISTS attendanceSchedules;
DROP TABLE IF EXISTS resources;
DROP TABLE IF EXISTS rooms;

-- Organisations table
CREATE TABLE organisations (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    parent_id VARCHAR(36),
    school_unit_code VARCHAR(255),
    organisation_code VARCHAR(255),
    municipality_code VARCHAR(255),
    type VARCHAR(255),
    school_types VARCHAR(255),
    start_date DATE,
    end_date DATE,
    created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (parent_id) REFERENCES organisations(id)
);


-- Persons table
CREATE TABLE persons (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    securityMarking VARCHAR(50) NOT NULL,
    created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Placements table
CREATE TABLE placements (
    id VARCHAR(36) PRIMARY KEY,
    organisation_id VARCHAR(36),
    person_id VARCHAR(36),
    FOREIGN KEY (organisation_id) REFERENCES organisations(id),
    FOREIGN KEY (person_id) REFERENCES persons(id),
    created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Duties table
CREATE TABLE duties (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Groups table
CREATE TABLE groups (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Programmes table
CREATE TABLE programmes (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- StudyPlans table
CREATE TABLE studyPlans (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Syllabuses table
CREATE TABLE syllabuses (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- SchoolUnitOfferings table
CREATE TABLE schoolUnitOfferings (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Activities table
CREATE TABLE activities (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- CalendarEvents table
CREATE TABLE calendarEvents (
    id VARCHAR(36) PRIMARY KEY,
    activity_id VARCHAR(36),
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    FOREIGN KEY (activity_id) REFERENCES activities(id),
    created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- AttendanceEvents table
CREATE TABLE attendanceEvents (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Attendance table
CREATE TABLE attendance (
    id VARCHAR(36) PRIMARY KEY,
    person_id VARCHAR(36),
    activity_id VARCHAR(36),
    attendance_event_id VARCHAR(36),
    FOREIGN KEY (person_id) REFERENCES persons(id),
    FOREIGN KEY (activity_id) REFERENCES activities(id),
    FOREIGN KEY (attendance_event_id) REFERENCES attendanceEvents(id),
    created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- AttendanceSchedules table
CREATE TABLE attendanceSchedules (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Grades table
CREATE TABLE grades (
    id VARCHAR(36) PRIMARY KEY,
    person_id VARCHAR(36),
    grade_value VARCHAR(10) NOT NULL,
    FOREIGN KEY (person_id) REFERENCES persons(id),
    created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- AggregatedAttendance table
CREATE TABLE aggregatedAttendance (
    id VARCHAR(36) PRIMARY KEY,
    person_id VARCHAR(36),
    attendance_percentage FLOAT,
    FOREIGN KEY (person_id) REFERENCES persons(id),
    created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Resources table
CREATE TABLE resources (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Rooms table
CREATE TABLE rooms (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Subscriptions table
CREATE TABLE subscriptions (
    id VARCHAR(36) PRIMARY KEY,
    resource_type VARCHAR(255) NOT NULL,
    resource_id VARCHAR(36) NOT NULL,
    user_id VARCHAR(36) NOT NULL,
    created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- DeletedEntities table
CREATE TABLE deletedEntities (
    id VARCHAR(36) PRIMARY KEY,
    resource_type VARCHAR(255) NOT NULL,
    deleted_at TIMESTAMP NOT NULL,
    created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Log table
CREATE TABLE log (
    id VARCHAR(36) PRIMARY KEY,
    log_message TEXT NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);


--
-- Sample data
--

-- Insert data into organisations
INSERT INTO organisations (id, name, parent_id, school_unit_code, organisation_code, municipality_code, type, school_types, start_date, end_date) VALUES
('org-1', 'Stora Komvux', NULL, '123456', 'SK-01', '1480', 'Kommun', 'Grundskola,Gymnasium', '2020-01-01', NULL),
('org-2', 'Stora Komvux Administration', 'org-1', NULL, 'SK-01-ADM', '1480', 'Avdelning', NULL, '2020-01-01', NULL),
('org-3', 'Lilla Gymnasiet', 'org-1', '654321', 'LG-01', '1480', 'Skola', 'Gymnasium', '2021-08-15', NULL),
('org-4', 'Stora Komvux - SFI', 'org-1', '555666', 'SK-01-SFI', '1480', 'Skola', 'Grundskola', '2022-01-01', '2025-12-31');


-- Insert data into persons
INSERT INTO persons (id, name, email, securityMarking) VALUES
('person-1', 'Maria Andersson', 'maria.andersson@example.com', 'Ingen'),
('person-2', 'Johan Karlsson', 'johan.karlsson@example.com', 'Ingen'),
('person-3', 'Fatima Ahmed', 'fatima.ahmed@example.com', 'Sekretessmarkering'),
('person-4', 'Erik Berg', 'erik.berg@example.com', 'Ingen'),
('person-5', 'Anna Lindqvist', 'anna.lindqvist@example.com', 'Ingen'),
('person-6', 'Karl Johansson', 'karl.johansson@example.com', 'Ingen'),
('person-7', 'Eva Svensson', 'eva.svensson@example.com', 'Skyddad folkbokföring'),
('person-8', 'Mohammed Ali', 'mohammed.ali@example.com', 'Ingen');


-- Insert data into placements
INSERT INTO placements (id, organisation_id, person_id) VALUES
('placement-1', 'org-1', 'person-1'),
('placement-2', 'org-2', 'person-2'),
('placement-3', 'org-3', 'person-3'),
('placement-4', 'org-4', 'person-4'),
('placement-5', 'org-3', 'person-5'),
('placement-6', 'org-3', 'person-6');

-- Insert data into duties
INSERT INTO duties (id, name) VALUES
('duty-1', 'Lärare'),
('duty-2', 'Rektor'),
('duty-3', 'Elev'),
('duty-4', 'Bibliotekarie');

-- Insert data into groups
INSERT INTO groups (id, name) VALUES
('group-1', 'Klass 7A'),
('group-2', 'Klass 8B'),
('group-3', 'Programmering 2');

-- Insert data into programmes
INSERT INTO programmes (id, name) VALUES
('programme-1', 'Teknikprogrammet'),
('programme-2', 'Samhällsvetenskapsprogrammet'),
('programme-3', 'Estetiska programmet');

-- Insert data into studyPlans
INSERT INTO studyPlans (id, name) VALUES
('studyplan-1', 'Individuell studieplan Maria'),
('studyplan-2', 'Studieplan för klass 7A');

-- Insert data into syllabuses
INSERT INTO syllabuses (id, name) VALUES
('syllabus-1', 'Syllabus Matematik 1b'),
('syllabus-2', 'Syllabus Svenska 2'),
('syllabus-3', 'Syllabus Webbutveckling 1');

-- Insert data into schoolUnitOfferings
INSERT INTO schoolUnitOfferings (id, name) VALUES
('offering-1', 'Matematik 1b'),
('offering-2', 'Svenska 2'),
('offering-3', 'Webbutveckling 1');

-- Insert data into activities
INSERT INTO activities (id, name) VALUES
('activity-1', 'Matematiklektion'),
('activity-2', 'Webbutvecklingsprojekt'),
('activity-3', 'Svenskalektion'),
('activity-4', 'Idrottslektion'),
('activity-5', 'Utvecklingssamtal');

-- Insert data into calendarEvents
INSERT INTO calendarEvents (id, activity_id, start_time, end_time) VALUES
('cal-event-1', 'activity-1', '2024-08-15 08:30:00', '2024-08-15 09:30:00'),
('cal-event-2', 'activity-2', '2024-08-15 10:00:00', '2024-08-15 12:00:00'),
('cal-event-3', 'activity-3', '2024-08-16 13:00:00', '2024-08-16 14:00:00'),
('cal-event-4', 'activity-1', '2024-08-16 08:30:00', '2024-08-16 09:30:00'),
('cal-event-5', 'activity-4', '2024-08-17 10:00:00', '2024-08-17 11:00:00');

-- Insert data into attendanceEvents
INSERT INTO attendanceEvents (id, name) VALUES
('att-event-1', 'Närvarande'),
('att-event-2', 'Frånvarande'),
('att-event-3', 'Sjuk'),
('att-event-4', 'Sen ankomst');

-- Insert data into attendance
INSERT INTO attendance (id, person_id, activity_id, attendance_event_id) VALUES
('att-1', 'person-1', 'activity-1', 'att-event-1'),
('att-2', 'person-2', 'activity-1', 'att-event-1'),
('att-3', 'person-3', 'activity-1', 'att-event-2'),
('att-4', 'person-4', 'activity-2', 'att-event-1'),
('att-5', 'person-5', 'activity-2', 'att-event-1'),
('att-6', 'person-6', 'activity-2', 'att-event-4'),
('att-7', 'person-1', 'activity-4', 'att-event-1'),
('att-8', 'person-2', 'activity-4', 'att-event-3');

-- Insert data into attendanceSchedules
INSERT INTO attendanceSchedules (id, name) VALUES
('att-schedule-1', 'Schema läsår 2024/2025'),
('att-schedule-2', 'Sommarschema 2024');

-- Insert data into grades
INSERT INTO grades (id, person_id, grade_value) VALUES
('grade-1', 'person-1', 'A'),
('grade-2', 'person-2', 'C'),
('grade-3', 'person-3', 'B'),
('grade-4', 'person-4', 'D'),
('grade-5', 'person-5', 'A');

-- Insert data into aggregatedAttendance
INSERT INTO aggregatedAttendance (id, person_id, attendance_percentage) VALUES
('agg-att-1', 'person-1', 98.5),
('agg-att-2', 'person-2', 91.0),
('agg-att-3', 'person-3', 75.2),
('agg-att-4', 'person-4', 99.1),
('agg-att-5', 'person-5', 85.0);

-- Insert data into resources
INSERT INTO resources (id, name) VALUES
('res-1', 'Projektor i sal 301'),
('res-2', 'Datorlabb 10'),
('res-3', 'Bärbara datorer vagn A');

-- Insert data into rooms
INSERT INTO rooms (id, name) VALUES
('room-1', 'Sal 301'),
('room-2', 'Biblioteket'),
('room-3', 'Datorlabb 10');

-- Insert data into subscriptions
INSERT INTO subscriptions (id, resource_type, resource_id, user_id) VALUES
('sub-1', 'person', 'person-1', 'user-abc'),
('sub-2', 'organisation', 'org-3', 'user-def');

-- Insert data into deletedEntities
INSERT INTO deletedEntities (id, resource_type, deleted_at) VALUES
('deleted-1', 'person', '2024-07-20 10:00:00');

-- Insert data into log
INSERT INTO log (id, log_message, timestamp) VALUES
('log-1', 'Person "Kalle Anka" skapades.', '2024-07-25 09:00:00'),
('log-2', 'Organisation "Rådhusskolan" uppdaterades.', '2024-07-25 10:15:00'),
('log-3', 'Aktivitet "Matematiklektion" lades till i kalendern.', '2024-07-26 08:30:00');

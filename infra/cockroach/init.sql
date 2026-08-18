-- Initialize GhostOps database on CockroachDB
CREATE DATABASE IF NOT EXISTS ghostops;
USE ghostops;

-- Ensure vector extension capabilities are enabled
-- CockroachDB natively supports VECTOR data types and cosine_distance / l2_distance functions.

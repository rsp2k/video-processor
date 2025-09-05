-- Database initialization for Video Processor
-- Creates necessary databases and extensions

-- Create test database
CREATE DATABASE video_processor_test;

-- Connect to main database
\c video_processor;

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create basic schema (Procrastinate will handle its own tables)
CREATE SCHEMA IF NOT EXISTS video_processor;

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE video_processor TO video_user;
GRANT ALL PRIVILEGES ON DATABASE video_processor_test TO video_user;
GRANT ALL PRIVILEGES ON SCHEMA video_processor TO video_user;

-- Create a sample videos table for demo purposes
CREATE TABLE IF NOT EXISTS video_processor.videos (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    filename VARCHAR(255) NOT NULL,
    original_path TEXT,
    processed_path TEXT,
    status VARCHAR(50) DEFAULT 'pending',
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index for efficient queries
CREATE INDEX IF NOT EXISTS idx_videos_status ON video_processor.videos(status);
CREATE INDEX IF NOT EXISTS idx_videos_created_at ON video_processor.videos(created_at);

-- Insert sample data
INSERT INTO video_processor.videos (filename, status) VALUES 
    ('sample_video_1.mp4', 'pending'),
    ('sample_video_2.mp4', 'processing'),
    ('sample_video_3.mp4', 'completed')
ON CONFLICT DO NOTHING;
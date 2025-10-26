-- Database initialization script for LeetCode Analytics API
-- This script sets up the initial database schema and indexes

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create problems table
CREATE TABLE IF NOT EXISTS problems (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(255) NOT NULL,
    difficulty VARCHAR(20) NOT NULL CHECK (difficulty IN ('EASY', 'MEDIUM', 'HARD')),
    frequency DECIMAL(5,2) NOT NULL DEFAULT 0.0,
    acceptance_rate DECIMAL(5,4) NOT NULL DEFAULT 0.0,
    link TEXT,
    company VARCHAR(100) NOT NULL,
    timeframe VARCHAR(20) NOT NULL,
    source_file TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create topics table
CREATE TABLE IF NOT EXISTS topics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL UNIQUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create problem_topics junction table
CREATE TABLE IF NOT EXISTS problem_topics (
    problem_id UUID REFERENCES problems(id) ON DELETE CASCADE,
    topic_id UUID REFERENCES topics(id) ON DELETE CASCADE,
    PRIMARY KEY (problem_id, topic_id)
);

-- Create company_stats table for pre-computed statistics
CREATE TABLE IF NOT EXISTS company_stats (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company VARCHAR(100) NOT NULL,
    timeframe VARCHAR(20) NOT NULL,
    total_problems INTEGER NOT NULL DEFAULT 0,
    avg_frequency DECIMAL(5,2) NOT NULL DEFAULT 0.0,
    avg_acceptance_rate DECIMAL(5,4) NOT NULL DEFAULT 0.0,
    difficulty_distribution JSONB,
    top_topics JSONB,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(company, timeframe)
);

-- Create topic_trends table for time-series topic data
CREATE TABLE IF NOT EXISTS topic_trends (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    topic_name VARCHAR(100) NOT NULL,
    timeframe VARCHAR(20) NOT NULL,
    frequency_count INTEGER NOT NULL DEFAULT 0,
    problem_count INTEGER NOT NULL DEFAULT 0,
    avg_difficulty_score DECIMAL(3,2) NOT NULL DEFAULT 0.0,
    trend_score DECIMAL(5,2) NOT NULL DEFAULT 0.0,
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(topic_name, timeframe, recorded_at::date)
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_problems_company ON problems(company);
CREATE INDEX IF NOT EXISTS idx_problems_timeframe ON problems(timeframe);
CREATE INDEX IF NOT EXISTS idx_problems_difficulty ON problems(difficulty);
CREATE INDEX IF NOT EXISTS idx_problems_frequency ON problems(frequency DESC);
CREATE INDEX IF NOT EXISTS idx_problems_company_timeframe ON problems(company, timeframe);
CREATE INDEX IF NOT EXISTS idx_problems_title ON problems(title);
CREATE INDEX IF NOT EXISTS idx_problems_created_at ON problems(created_at);

CREATE INDEX IF NOT EXISTS idx_topics_name ON topics(name);

CREATE INDEX IF NOT EXISTS idx_problem_topics_problem_id ON problem_topics(problem_id);
CREATE INDEX IF NOT EXISTS idx_problem_topics_topic_id ON problem_topics(topic_id);

CREATE INDEX IF NOT EXISTS idx_company_stats_company ON company_stats(company);
CREATE INDEX IF NOT EXISTS idx_company_stats_timeframe ON company_stats(timeframe);
CREATE INDEX IF NOT EXISTS idx_company_stats_last_updated ON company_stats(last_updated);

CREATE INDEX IF NOT EXISTS idx_topic_trends_topic_name ON topic_trends(topic_name);
CREATE INDEX IF NOT EXISTS idx_topic_trends_timeframe ON topic_trends(timeframe);
CREATE INDEX IF NOT EXISTS idx_topic_trends_recorded_at ON topic_trends(recorded_at);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
CREATE TRIGGER update_problems_updated_at 
    BEFORE UPDATE ON problems 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_company_stats_updated_at 
    BEFORE UPDATE ON company_stats 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert some sample data for testing (optional)
INSERT INTO topics (name) VALUES 
    ('Array'),
    ('String'),
    ('Dynamic Programming'),
    ('Tree'),
    ('Graph'),
    ('Hash Table'),
    ('Two Pointers'),
    ('Binary Search'),
    ('Sliding Window'),
    ('Backtracking')
ON CONFLICT (name) DO NOTHING;

-- Create a view for problem statistics
CREATE OR REPLACE VIEW problem_stats AS
SELECT 
    p.title,
    p.difficulty,
    p.company,
    p.timeframe,
    p.frequency,
    p.acceptance_rate,
    ARRAY_AGG(t.name ORDER BY t.name) as topics,
    COUNT(pt.topic_id) as topic_count
FROM problems p
LEFT JOIN problem_topics pt ON p.id = pt.problem_id
LEFT JOIN topics t ON pt.topic_id = t.id
GROUP BY p.id, p.title, p.difficulty, p.company, p.timeframe, p.frequency, p.acceptance_rate;

-- Create a view for company analytics
CREATE OR REPLACE VIEW company_analytics AS
SELECT 
    company,
    timeframe,
    COUNT(*) as total_problems,
    AVG(frequency) as avg_frequency,
    AVG(acceptance_rate) as avg_acceptance_rate,
    COUNT(CASE WHEN difficulty = 'EASY' THEN 1 END) as easy_count,
    COUNT(CASE WHEN difficulty = 'MEDIUM' THEN 1 END) as medium_count,
    COUNT(CASE WHEN difficulty = 'HARD' THEN 1 END) as hard_count,
    MAX(updated_at) as last_updated
FROM problems
GROUP BY company, timeframe;

-- Grant permissions (adjust as needed for your security requirements)
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO leetcode;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO leetcode;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO leetcode;

-- Log successful initialization
INSERT INTO company_stats (company, timeframe, total_problems, avg_frequency, avg_acceptance_rate, difficulty_distribution)
VALUES ('_system', '_init', 0, 0.0, 0.0, '{"status": "initialized", "timestamp": "' || CURRENT_TIMESTAMP || '"}');

COMMIT;
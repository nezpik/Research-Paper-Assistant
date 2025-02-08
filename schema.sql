DROP TABLE IF EXISTS papers;
CREATE TABLE papers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    url TEXT,
    authors TEXT,
    source TEXT,
    year INTEGER,
    citations INTEGER,
    abstract TEXT,
    section TEXT,
    query TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Insert some sample data
INSERT INTO papers (title, url, authors, source, year, citations, abstract) VALUES
('An Introduction to Machine Learning', 'https://example.com/ml-intro', 'John Smith, Jane Doe', 'Sample', 2023, 100, 'This paper provides a comprehensive introduction to machine learning concepts.'),
('Deep Learning Fundamentals', 'https://example.com/dl-fundamentals', 'Alice Johnson', 'Sample', 2022, 75, 'A detailed overview of deep learning principles and architectures.'),
('Neural Networks in Practice', 'https://example.com/nn-practice', 'Bob Wilson, Carol Brown', 'Sample', 2023, 50, 'Practical applications of neural networks in real-world scenarios.');

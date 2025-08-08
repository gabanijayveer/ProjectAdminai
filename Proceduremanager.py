import os
import mysql.connector
from mysql.connector import Error
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage, SystemMessage
import json
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass
from enum import Enum

# Set your Google API key
os.environ["GOOGLE_API_KEY"] = "AIzaSyAatriP47wO05S2e-egmPZjvWGnqyB_izQ"

# Configuration Classes for Better Structure
@dataclass
class LLMConfig:
    """Configuration for LLM instances"""
    model: str = "gemini-2.5-flash"
    temperature_analytical: float = 0.0
    temperature_conversational: float = 0.7
    api_key: str = os.environ.get("GOOGLE_API_KEY", "")

@dataclass
class DatabaseConfig:
    """Database configuration wrapper"""
    procedure_name: str = "user_query_procedure"
    batch_size: int = 1000
    limit_results: int = 100

class ErrorType(Enum):
    """Enumeration for different error types"""
    LLM_GENERATION = "llm_generation"
    PROCEDURE_VALIDATION = "procedure_validation" 
    DATABASE_CONNECTION = "database_connection"
    PROCEDURE_CREATION = "procedure_creation"
    PROCEDURE_EXECUTION = "procedure_execution"

# Global Configuration Instances
LLM_CONFIG = LLMConfig()
DB_CONFIG_WRAPPER = DatabaseConfig()

# Mathematical formulas and aggregation functions for large datasets
MATH_FORMULAS = {
    'statistical': {
        'mean': 'AVG({column})',
        'median': 'PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY {column})',
        'mode': 'MODE() WITHIN GROUP (ORDER BY {column})',
        'std_dev': 'STDDEV({column})',
        'variance': 'VARIANCE({column})',
        'percentile_25': 'PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY {column})',
        'percentile_75': 'PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY {column})',
        'range': 'MAX({column}) - MIN({column})',
        'coefficient_variation': 'STDDEV({column}) / AVG({column}) * 100'
    },
    'aggregation': {
        'sum': 'SUM({column})',
        'count': 'COUNT({column})',
        'count_distinct': 'COUNT(DISTINCT {column})',
        'min': 'MIN({column})',
        'max': 'MAX({column})',
        'avg': 'AVG({column})',
        'group_concat': 'GROUP_CONCAT({column} SEPARATOR \', \')'
    },
    'business': {
        'growth_rate': '((current_value - previous_value) / previous_value) * 100',
        'moving_average': 'AVG({column}) OVER (ORDER BY {date_column} ROWS BETWEEN {n} PRECEDING AND CURRENT ROW)',
        'cumulative_sum': 'SUM({column}) OVER (ORDER BY {date_column} ROWS UNBOUNDED PRECEDING)',
        'rank': 'RANK() OVER (ORDER BY {column} DESC)',
        'dense_rank': 'DENSE_RANK() OVER (ORDER BY {column} DESC)',
        'row_number': 'ROW_NUMBER() OVER (ORDER BY {column} DESC)'
    },
    'performance_ranking': {
        'employee_performance_rank': 'RANK() OVER (ORDER BY performance_rating DESC)',
        'salary_rank': 'RANK() OVER (ORDER BY salary DESC)',
        'department_rank': 'RANK() OVER (PARTITION BY department ORDER BY performance_rating DESC)',
        'overall_employee_score': 'RANK() OVER (ORDER BY (performance_rating * 0.7 + (salary/1000) * 0.3) DESC)',
        'percentile_rank': 'PERCENT_RANK() OVER (ORDER BY performance_rating)',
        'ntile_quartile': 'NTILE(4) OVER (ORDER BY performance_rating DESC)',
        'top_performer': 'CASE WHEN RANK() OVER (ORDER BY performance_rating DESC) <= 3 THEN "Top Performer" ELSE "Standard" END'
    },
    'interview_ranking': {
        'technical_rank': 'RANK() OVER (ORDER BY technical_score DESC)',
        'communication_rank': 'RANK() OVER (ORDER BY communication_score DESC)',
        'overall_interview_rank': 'RANK() OVER (ORDER BY overall_score DESC)',
        'combined_score': '(technical_score * 0.4 + communication_score * 0.3 + overall_score * 0.3)',
        'hire_recommendation': 'CASE WHEN overall_score >= 4.0 THEN "Strongly Recommend" WHEN overall_score >= 3.5 THEN "Recommend" WHEN overall_score >= 3.0 THEN "Consider" ELSE "Not Recommended" END',
        'top_candidates': 'CASE WHEN RANK() OVER (ORDER BY overall_score DESC) <= 5 THEN "Top 5 Candidate" ELSE "Standard" END'
    },
    'hiring_metrics': {
        'best_candidate_score': '(technical_score * 0.4 + communication_score * 0.3 + overall_score * 0.3)',
        'position_competition': 'COUNT(*) OVER (PARTITION BY position_applied)',
        'success_rate_by_position': 'AVG(CASE WHEN outcome = "hired" THEN 1 ELSE 0 END) OVER (PARTITION BY position_applied)'
    },
    'financial': {
        'profit_margin': '(revenue - cost) / revenue * 100',
        'roi': '(gain - investment) / investment * 100',
        'compound_growth': 'POWER((ending_value / beginning_value), (1.0 / years)) - 1'
    }
}

# Database schema information - Smart table selection based on query
alltable_describe = {
    'orders': [
        {'Field': 'order_id', 'Type': 'int(11)', 'Null': 'NO', 'Key': 'PRI', 'Default': None, 'Extra': 'auto_increment', 'Comment': 'Unique identifier for each order'},
        {'Field': 'user_id', 'Type': 'int(11)', 'Null': 'NO', 'Key': 'MUL', 'Default': None, 'Extra': '', 'Comment': 'Foreign key referencing the customer who placed the order'},
        {'Field': 'product_id', 'Type': 'int(11)', 'Null': 'NO', 'Key': 'MUL', 'Default': None, 'Extra': '', 'Comment': 'Foreign key referencing the product that was ordered'},
        {'Field': 'quantity', 'Type': 'int(11)', 'Null': 'NO', 'Key': '', 'Default': None, 'Extra': '', 'Comment': 'Number of units of the product ordered'},
        {'Field': 'total_amount', 'Type': 'decimal(10,2)', 'Null': 'NO', 'Key': '', 'Default': None, 'Extra': '', 'Comment': 'Total monetary value of the order including price * quantity'},
        {'Field': 'order_date', 'Type': 'timestamp', 'Null': 'NO', 'Key': '', 'Default': 'CURRENT_TIMESTAMP', 'Extra': '', 'Comment': 'Date and time when the order was placed'},
        {'Field': 'status', 'Type': "enum('pending','processing','shipped','delivered','cancelled')", 'Null': 'YES', 'Key': '', 'Default': 'pending', 'Extra': '', 'Comment': 'Current status of the order in the fulfillment process'}
    ],
    'products': [
        {'Field': 'product_id', 'Type': 'int(11)', 'Null': 'NO', 'Key': 'PRI', 'Default': None, 'Extra': 'auto_increment', 'Comment': 'Unique identifier for each product'},
        {'Field': 'product_name', 'Type': 'varchar(100)', 'Null': 'NO', 'Key': '', 'Default': None, 'Extra': '', 'Comment': 'Name or title of the product'},
        {'Field': 'category', 'Type': 'varchar(50)', 'Null': 'NO', 'Key': '', 'Default': None, 'Extra': '', 'Comment': 'Product category classification (e.g., Electronics, Accessories)'},
        {'Field': 'price', 'Type': 'decimal(10,2)', 'Null': 'NO', 'Key': '', 'Default': None, 'Extra': '', 'Comment': 'Unit price of the product in currency'},
        {'Field': 'stock_quantity', 'Type': 'int(11)', 'Null': 'NO', 'Key': '', 'Default': None, 'Extra': '', 'Comment': 'Current available inventory count for this product'},
        {'Field': 'created_date', 'Type': 'timestamp', 'Null': 'NO', 'Key': '', 'Default': 'CURRENT_TIMESTAMP', 'Extra': '', 'Comment': 'Date and time when the product was added to the catalog'}
    ],
    'users': [
        {'Field': 'user_id', 'Type': 'int(11)', 'Null': 'NO', 'Key': 'PRI', 'Default': None, 'Extra': 'auto_increment', 'Comment': 'Unique identifier for each user/customer'},
        {'Field': 'first_name', 'Type': 'varchar(50)', 'Null': 'NO', 'Key': '', 'Default': None, 'Extra': '', 'Comment': 'User\'s first name'},
        {'Field': 'last_name', 'Type': 'varchar(50)', 'Null': 'NO', 'Key': '', 'Default': None, 'Extra': '', 'Comment': 'User\'s last name'},
        {'Field': 'email', 'Type': 'varchar(100)', 'Null': 'NO', 'Key': 'UNI', 'Default': None, 'Extra': '', 'Comment': 'User\'s unique email address for login and communication'},
        {'Field': 'phone', 'Type': 'varchar(15)', 'Null': 'YES', 'Key': '', 'Default': None, 'Extra': '', 'Comment': 'User\'s contact phone number'},
        {'Field': 'address', 'Type': 'text', 'Null': 'YES', 'Key': '', 'Default': None, 'Extra': '', 'Comment': 'User\'s physical address for shipping and billing'},
        {'Field': 'registration_date', 'Type': 'timestamp', 'Null': 'NO', 'Key': '', 'Default': 'CURRENT_TIMESTAMP', 'Extra': '', 'Comment': 'Date and time when the user registered on the platform'}
    ],
    'employees': [
        {'Field': 'emp_id', 'Type': 'int(11)', 'Null': 'NO', 'Key': 'PRI', 'Default': None, 'Extra': 'auto_increment', 'Comment': 'Unique identifier for each employee'},
        {'Field': 'first_name', 'Type': 'varchar(50)', 'Null': 'NO', 'Key': '', 'Default': None, 'Extra': '', 'Comment': 'Employee\'s first name'},
        {'Field': 'last_name', 'Type': 'varchar(50)', 'Null': 'NO', 'Key': '', 'Default': None, 'Extra': '', 'Comment': 'Employee\'s last name'},
        {'Field': 'email', 'Type': 'varchar(100)', 'Null': 'NO', 'Key': 'UNI', 'Default': None, 'Extra': '', 'Comment': 'Employee\'s unique email address for work communication'},
        {'Field': 'department', 'Type': 'varchar(50)', 'Null': 'NO', 'Key': '', 'Default': None, 'Extra': '', 'Comment': 'Department where the employee works (e.g., Sales, Marketing, HR, IT)'},
        {'Field': 'position', 'Type': 'varchar(50)', 'Null': 'NO', 'Key': '', 'Default': None, 'Extra': '', 'Comment': 'Employee\'s job title or position within the department'},
        {'Field': 'salary', 'Type': 'decimal(10,2)', 'Null': 'NO', 'Key': '', 'Default': None, 'Extra': '', 'Comment': 'Employee\'s annual salary in currency'},
        {'Field': 'performance_rating', 'Type': 'decimal(3,2)', 'Null': 'YES', 'Key': '', 'Default': None, 'Extra': '', 'Comment': 'Employee performance rating on a scale of 1-5 where 5 is excellent'},
        {'Field': 'status', 'Type': "enum('active','inactive','terminated','on_leave')", 'Null': 'YES', 'Key': '', 'Default': 'active', 'Extra': '', 'Comment': 'Current employment status of the employee'}
    ],
    'interviews': [
    {'Field': 'interview_id', 'Type': 'int(11)', 'Null': 'NO', 'Key': 'PRI', 'Default': None, 'Extra': 'auto_increment', 'Comment': 'Unique identifier for each interview session'},
    {'Field': 'candidate_name', 'Type': 'varchar(100)', 'Null': 'NO', 'Key': '', 'Default': None, 'Extra': '', 'Comment': 'Full name of the candidate being interviewed'},
    {'Field': 'email', 'Type': 'varchar(100)', 'Null': 'YES', 'Key': '', 'Default': None, 'Extra': '', 'Comment': 'Candidate\'s email address for communication'},
    {'Field': 'phone', 'Type': 'varchar(15)', 'Null': 'YES', 'Key': '', 'Default': None, 'Extra': '', 'Comment': 'Candidate\'s contact phone number'},
    {'Field': 'position_applied', 'Type': 'varchar(50)', 'Null': 'NO', 'Key': '', 'Default': None, 'Extra': '', 'Comment': 'Job position the candidate applied for'},
    {'Field': 'department', 'Type': 'varchar(50)', 'Null': 'YES', 'Key': '', 'Default': None, 'Extra': '', 'Comment': 'Department where the position is located'},
    {'Field': 'interview_date', 'Type': 'date', 'Null': 'YES', 'Key': '', 'Default': None, 'Extra': '', 'Comment': 'Date when the interview was conducted'},
    {'Field': 'interview_time', 'Type': 'time', 'Null': 'YES', 'Key': '', 'Default': None, 'Extra': '', 'Comment': 'Time when the interview was conducted'},
    {'Field': 'interviewer_id', 'Type': 'int(11)', 'Null': 'YES', 'Key': '', 'Default': None, 'Extra': '', 'Comment': 'ID of the employee who conducted the interview'},
    {'Field': 'interview_type', 'Type': "enum('online','offline','telephonic')", 'Null': 'YES', 'Key': '', 'Default': 'offline', 'Extra': '', 'Comment': 'Type of interview conducted (online, offline, or telephonic)'},
    {'Field': 'interview_round', 'Type': 'int(2)', 'Null': 'YES', 'Key': '', 'Default': 1, 'Extra': '', 'Comment': 'Round number of the interview process (1st round, 2nd round, etc.)'},
    {'Field': 'technical_score', 'Type': 'decimal(3,2)', 'Null': 'YES', 'Key': '', 'Default': None, 'Extra': '', 'Comment': 'Technical skills score on a scale of 1-5'},
    {'Field': 'communication_score', 'Type': 'decimal(3,2)', 'Null': 'YES', 'Key': '', 'Default': None, 'Extra': '', 'Comment': 'Communication skills score on a scale of 1-5'},
    {'Field': 'cultural_fit_score', 'Type': 'decimal(3,2)', 'Null': 'YES', 'Key': '', 'Default': None, 'Extra': '', 'Comment': 'Cultural fit assessment score on a scale of 1-5'},
    {'Field': 'overall_score', 'Type': 'decimal(3,2)', 'Null': 'YES', 'Key': '', 'Default': None, 'Extra': '', 'Comment': 'Overall interview score calculated from all assessment areas'},
    {'Field': 'interview_notes', 'Type': 'text', 'Null': 'YES', 'Key': '', 'Default': None, 'Extra': '', 'Comment': 'Detailed notes and observations from the interview'},
    {'Field': 'outcome', 'Type': "enum('pass','fail','pending','hold','hired')", 'Null': 'YES', 'Key': '', 'Default': 'pending', 'Extra': '', 'Comment': 'Final outcome or decision of the interview process'},
    {'Field': 'salary_expectation', 'Type': 'decimal(10,2)', 'Null': 'YES', 'Key': '', 'Default': None, 'Extra': '', 'Comment': 'Candidate\'s expected salary in currency'},
    {'Field': 'years_experience', 'Type': 'decimal(3,1)', 'Null': 'YES', 'Key': '', 'Default': None, 'Extra': '', 'Comment': 'Number of years of relevant work experience'},
    {'Field': 'created_date', 'Type': 'datetime', 'Null': 'YES', 'Key': '', 'Default': None, 'Extra': '', 'Comment': 'Date and time when the interview record was created'},
    {'Field': 'updated_date', 'Type': 'datetime', 'Null': 'YES', 'Key': '', 'Default': None, 'Extra': '', 'Comment': 'Date and time when the interview record was last updated'}
]

}
alltable_demo_data = {
    'orders': [
        {'order_id': 1, 'user_id': 101, 'product_id': 201, 'quantity': 2, 'total_amount': 499.98, 'order_date': '2025-08-01 10:00:00', 'status': 'processing'},
        {'order_id': 2, 'user_id': 102, 'product_id': 202, 'quantity': 1, 'total_amount': 249.99, 'order_date': '2025-08-02 14:20:00', 'status': 'shipped'},
        {'order_id': 3, 'user_id': 103, 'product_id': 203, 'quantity': 3, 'total_amount': 899.97, 'order_date': '2025-08-03 16:45:00', 'status': 'delivered'},
        {'order_id': 4, 'user_id': 104, 'product_id': 204, 'quantity': 1, 'total_amount': 299.99, 'order_date': '2025-08-04 12:10:00', 'status': 'cancelled'},
        {'order_id': 5, 'user_id': 105, 'product_id': 205, 'quantity': 4, 'total_amount': 1199.96, 'order_date': '2025-08-05 09:30:00', 'status': 'pending'},
    ],
    'products': [
        {'product_id': 201, 'product_name': 'Wireless Mouse', 'category': 'Electronics', 'price': 249.99, 'stock_quantity': 50, 'created_date': '2025-07-01 10:00:00'},
        {'product_id': 202, 'product_name': 'Bluetooth Headphones', 'category': 'Electronics', 'price': 249.99, 'stock_quantity': 30, 'created_date': '2025-07-02 10:00:00'},
        {'product_id': 203, 'product_name': 'Gaming Keyboard', 'category': 'Electronics', 'price': 299.99, 'stock_quantity': 20, 'created_date': '2025-07-03 10:00:00'},
        {'product_id': 204, 'product_name': 'Smart Watch', 'category': 'Wearables', 'price': 299.99, 'stock_quantity': 15, 'created_date': '2025-07-04 10:00:00'},
        {'product_id': 205, 'product_name': 'USB-C Hub', 'category': 'Accessories', 'price': 299.99, 'stock_quantity': 40, 'created_date': '2025-07-05 10:00:00'},
    ],
    'users': [
        {'user_id': 101, 'first_name': 'Alice', 'last_name': 'Johnson', 'email': 'alice@example.com', 'phone': '9876543210', 'address': '123 Elm St', 'registration_date': '2025-06-01 08:30:00'},
        {'user_id': 102, 'first_name': 'Bob', 'last_name': 'Smith', 'email': 'bob@example.com', 'phone': '9876543211', 'address': '456 Oak St', 'registration_date': '2025-06-02 09:00:00'},
        {'user_id': 103, 'first_name': 'Carol', 'last_name': 'Williams', 'email': 'carol@example.com', 'phone': '9876543212', 'address': '789 Pine St', 'registration_date': '2025-06-03 10:00:00'},
        {'user_id': 104, 'first_name': 'David', 'last_name': 'Taylor', 'email': 'david@example.com', 'phone': '9876543213', 'address': '101 Maple St', 'registration_date': '2025-06-04 11:00:00'},
        {'user_id': 105, 'first_name': 'Eve', 'last_name': 'Brown', 'email': 'eve@example.com', 'phone': '9876543214', 'address': '202 Cedar St', 'registration_date': '2025-06-05 12:00:00'},
    ],
    'employees': [
        {'emp_id': 301, 'first_name': 'John', 'last_name': 'Doe', 'email': 'john.doe@example.com', 'department': 'Sales', 'position': 'Manager', 'salary': 70000.00, 'performance_rating': 4.5, 'status': 'active'},
        {'emp_id': 302, 'first_name': 'Jane', 'last_name': 'Smith', 'email': 'jane.smith@example.com', 'department': 'Marketing', 'position': 'Executive', 'salary': 55000.00, 'performance_rating': 4.2, 'status': 'active'},
        {'emp_id': 303, 'first_name': 'Mike', 'last_name': 'Brown', 'email': 'mike.brown@example.com', 'department': 'HR', 'position': 'Coordinator', 'salary': 48000.00, 'performance_rating': 3.9, 'status': 'on_leave'},
        {'emp_id': 304, 'first_name': 'Sara', 'last_name': 'Lee', 'email': 'sara.lee@example.com', 'department': 'Finance', 'position': 'Analyst', 'salary': 60000.00, 'performance_rating': 4.7, 'status': 'active'},
        {'emp_id': 305, 'first_name': 'Tom', 'last_name': 'Wilson', 'email': 'tom.wilson@example.com', 'department': 'IT', 'position': 'Engineer', 'salary': 65000.00, 'performance_rating': 4.3, 'status': 'inactive'},
    ],
    'interviews': [
    {
        'interview_id': 401,
        'candidate_name': 'Alex Green',
        'email': 'alex.green@example.com',
        'phone': '9876543210',
        'position_applied': 'Software Developer',
        'department': 'Engineering',
        'interview_date': '2025-08-05',
        'interview_time': '10:00:00',
        'interviewer_id': 201,
        'interview_type': 'online',
        'interview_round': 2,
        'technical_score': 4.5,
        'communication_score': 4.0,
        'cultural_fit_score': 4.4,
        'overall_score': 4.3,
        'interview_notes': 'Strong in backend, good coding test performance.',
        'outcome': 'hired',
        'salary_expectation': 90000.00,
        'years_experience': 4.5,
        'created_date': '2025-08-01 12:00:00',
        'updated_date': '2025-08-05 17:00:00'
    },
    {
        'interview_id': 402,
        'candidate_name': 'Lily Adams',
        'email': 'lily.adams@example.com',
        'phone': '9123456780',
        'position_applied': 'QA Engineer',
        'department': 'Quality Assurance',
        'interview_date': '2025-08-04',
        'interview_time': '11:30:00',
        'interviewer_id': 202,
        'interview_type': 'offline',
        'interview_round': 1,
        'technical_score': 3.9,
        'communication_score': 4.2,
        'cultural_fit_score': 4.1,
        'overall_score': 4.0,
        'interview_notes': 'Good analytical skills.',
        'outcome': 'pass',
        'salary_expectation': 70000.00,
        'years_experience': 3.0,
        'created_date': '2025-08-01 14:00:00',
        'updated_date': '2025-08-04 16:00:00'
    },
    {
        'interview_id': 403,
        'candidate_name': 'James White',
        'email': 'james.white@example.com',
        'phone': '9012345678',
        'position_applied': 'Project Manager',
        'department': 'Management',
        'interview_date': '2025-08-03',
        'interview_time': '09:00:00',
        'interviewer_id': 203,
        'interview_type': 'telephonic',
        'interview_round': 1,
        'technical_score': 4.2,
        'communication_score': 3.8,
        'cultural_fit_score': 3.9,
        'overall_score': 4.0,
        'interview_notes': 'Needs improvement in delivery estimation.',
        'outcome': 'hold',
        'salary_expectation': 120000.00,
        'years_experience': 6.0,
        'created_date': '2025-07-30 09:00:00',
        'updated_date': '2025-08-03 15:00:00'
    },
    {
        'interview_id': 404,
        'candidate_name': 'Emma Black',
        'email': 'emma.black@example.com',
        'phone': '9988776655',
        'position_applied': 'UI/UX Designer',
        'department': 'Design',
        'interview_date': '2025-08-02',
        'interview_time': '14:00:00',
        'interviewer_id': 204,
        'interview_type': 'offline',
        'interview_round': 2,
        'technical_score': 4.0,
        'communication_score': 4.5,
        'cultural_fit_score': 4.3,
        'overall_score': 4.3,
        'interview_notes': 'Creative portfolio, good teamwork skills.',
        'outcome': 'pass',
        'salary_expectation': 85000.00,
        'years_experience': 4.0,
        'created_date': '2025-07-29 10:30:00',
        'updated_date': '2025-08-02 16:00:00'
    },
    {
        'interview_id': 405,
        'candidate_name': 'Oliver Gray',
        'email': 'oliver.gray@example.com',
        'phone': '9876501234',
        'position_applied': 'DevOps Engineer',
        'department': 'IT Operations',
        'interview_date': '2025-08-01',
        'interview_time': '16:00:00',
        'interviewer_id': 205,
        'interview_type': 'online',
        'interview_round': 1,
        'technical_score': 3.5,
        'communication_score': 3.6,
        'cultural_fit_score': 3.2,
        'overall_score': 3.55,
        'interview_notes': 'Average CI/CD knowledge. Needs more experience.',
        'outcome': 'fail',
        'salary_expectation': 75000.00,
        'years_experience': 2.0,
        'created_date': '2025-07-28 11:15:00',
        'updated_date': '2025-08-01 17:45:00'
    }
]

}

# Smart table selection based on query keywords
TABLE_KEYWORDS = {
    'users': ['user', 'customer', 'client', 'buyer', 'person', 'people'],
    'products': ['product', 'item', 'goods', 'merchandise', 'inventory'],
    'orders': ['order', 'purchase', 'transaction', 'sale', 'buy'],
    'employees': ['employee', 'staff', 'worker', 'hire', 'hiring', 'performance', 'best performer', 'emp', 'rating'],
    'interviews': ['interview', 'candidate', 'hiring', 'recruit', 'selection', 'technical score', 'communication', 'overall score']
}

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'password',
    'database': 'custom',
    'port': 3312
}

# Optimization settings for large datasets (5000+ records)
OPTIMIZATION_CONFIG = {
    'batch_size': 1000,  # Process data in batches
    'limit_results': 100,  # Limit final results for display
    'use_pagination': True,  # Enable pagination for large result sets
    'memory_optimization': True,  # Use memory-efficient queries
    'parallel_processing': False,  # Enable if MySQL supports it
    'cache_intermediate_results': True  # Cache intermediate calculations
}

# Performance optimization hints for procedures (safe comments only)
PERFORMANCE_HINTS = {
    'query_optimization': [
        'Use LIMIT for large result sets',
        'Use EXISTS instead of IN for subqueries',
        'Use INNER JOIN instead of WHERE clauses when possible',
         'Use EXPLAIN to analyze query performance'
    ]
}

# Legacy constant - now moved to DatabaseConfig class
PROCEDURE_NAME = DB_CONFIG_WRAPPER.procedure_name

SYSTEM_PROMPT = f"""You are an expert SQL developer and database analyst specialized in handling large datasets (5000+ records) with mathematical formulas and optimized procedures. Your task is to create MySQL stored procedures based on user queries.

Database Schema:
{json.dumps(alltable_describe, indent=2)}
Database demo data:
{json.dumps(alltable_demo_data, indent=2)}

Available Mathematical Formulas:
{json.dumps(MATH_FORMULAS, indent=2)}

Optimization Configuration:
{json.dumps(OPTIMIZATION_CONFIG, indent=2)}

Available Tables and Their Purposes:
1. orders - Contains order information with fields: order_id, user_id, product_id, quantity, total_amount, order_date, status
2. products - Contains product information with fields: product_id, product_name, category, price, stock_quantity, created_date
3. users - Contains user information with fields: user_id, first_name, last_name, email, phone, address, registration_date
4. employees - Contains employee information with fields: emp_id, first_name, last_name, email, department, position, salary, performance_rating, status
5. interviews - Contains interview data with fields: interview_id, candidate_name, position_applied, department, interview_date, interview_time, technical_score, communication_score, overall_score, outcome , interview_notes

SMART TABLE SELECTION INSTRUCTIONS:
Analyze the user query and intelligently select ONLY the relevant tables based on:

QUERY TYPE ANALYSIS:
- Hiring/Recruitment queries: Use employees + interviews tables
- Company/event/ new interview date queries: Use employees + interviews tables
- Employee performance analysis: Use employees table only
- Candidate selection/interview analysis: Use interviews table only
- Customer Analyze /analysis/behavior: Use users + orders + products tables
- Sales analysis/revenue: Use orders + products + users tables
- Product analysis/inventory: Use products + orders tables
- User behavior/engagement: Use users + orders tables""
- Comprehensive business analysis: Use all relevant tables
- Financial analysis: Use orders + products tables
- Marketing analysis: Use users + orders + products tables

KEYWORD-BASED TABLE SELECTION:
- "employee", "staff", "worker", "hire", "hiring", "performance", "best performer", "emp", "rating" → employees table
- "interview", "candidate", "hiring", "recruit", "selection", "technical score","bestdateforinterview","interviewdate","interviewtime" , "communication", "overall score" → interviews table
- "user", "customer", "client", "buyer", "person", "people" → users table
- "product", "item", "goods", "merchandise", "inventory" → products table
- "order", "purchase", "transaction", "sale", "buy" → orders table
- "sales", "revenue", "income", "profit" → orders + products tables
- "department", "team", "group" → employees table
- "salary", "compensation", "pay" → employees table
- "ranking", "top", "best", "worst" → relevant table based on context
- "average", "mean", "statistics" → relevant table based on context
- "trend", "growth", "improvement" → relevant table based on context

ADVANCED TABLE SELECTION RULES:
- For queries mentioning multiple entities, use appropriate JOINs
- For comparative analysis, include all relevant tables
- For trend analysis over time, include date-based tables
- For performance rankings, focus on the primary entity table
- For cross-department analysis, use employees table with department filtering
- For customer-product analysis, use users + orders + products tables
- For interview-performance correlation, use interviews + employees tables
- For New interview date available correlation, use interviews
- For sales-performance correlation, use orders + employees tables

HIRING & PERFORMANCE ANALYSIS FOCUS:
- Use RANK() OVER (ORDER BY performance_rating DESC) for employee ranking
- Use RANK() OVER (ORDER BY overall_score DESC) for candidate ranking
- Use NTILE(4) for quartile-based performance grouping
- Focus on top performers for hiring recommendations

Instructions for Large Dataset Optimization (5000+ records):
1. FIRST: Analyze the user query and identify which tables are relevant to the query using the keyword-based selection rules above.
2. SECOND: Create a COMPLETE MySQL stored procedure named '{PROCEDURE_NAME}' that generates the required report/query using ONLY the relevant tables.
3. OPTIMIZATION REQUIREMENTS for large datasets:
   - Use LIMIT clauses to control result set size (default: 100 records for display)
   - Use appropriate mathematical formulas from the MATH_FORMULAS collection
   - Use EXISTS instead of IN for subqueries when possible
   - Implement pagination logic when dealing with large result sets
   - Keep procedures simple and avoid complex cursor operations
4. The procedure MUST be complete and executable with:
   - Proper BEGIN and END statements
   - Complete SQL logic that answers the user's question
   - Appropriate JOINs between tables when needed
   - Proper WHERE clauses for filtering conditions
   - Mathematical formulas (SUM, AVG, STDDEV, VARIANCE, PERCENTILE, etc.)
   - Date filtering using functions like YEAR(), MONTH(), DATE()
   - Clear, readable SELECT statements that return optimized results
   - Batch processing logic for large datasets
5. Always include proper error handling with DECLARE EXIT HANDLER FOR SQLEXCEPTION.
6. Use simple SQL without CTEs (Common Table Expressions) or WITH clauses.
8. Be compatible with MySQL 5.7 and earlier versions.
9. DO NOT use DELIMITER statements - return only the CREATE PROCEDURE statement.
10. DO NOT use WITH clauses or Common Table Expressions (CTEs).
12. IMPORTANT: The procedure MUST end with END; statement.
13. PERFORMANCE RANKING & HIRING DECISIONS:
    - Use RANK() OVER (ORDER BY performance_score DESC) for performance ranking
    - Use NTILE(4) for quartile-based performance grouping
    - Use PERCENT_RANK() for percentile-based positioning
    - Implement weighted scoring: (performance_score * 0.4 + target_achieved * 0.6)
    - Use LAG() and LEAD() for trend analysis
    - Include consistency analysis using STDDEV()
    - For hiring decisions, focus on top 10% or top 3 performers
    - Use CASE statements to categorize performance levels
14. SMART TABLE USAGE:
    - Only use tables relevant to the query (not all tables)
    - For hiring queries: employees + interviews tables
    - For customer analysis: users + orders + products tables
    - Optimize JOINs based on selected tables only
15. For reports, follow a structured format including:
    - Report title with dynamic month and year (e.g., '### Monthly Sales Report: July 2025')
    - Description of the report
    - Key metrics section (e.g., total sales)
    - Detailed tables for data presentation (e.g., top performers, rankings)
    - Conclusion and actionable insights
    - Recommendations for next steps
16. Use cursors when iterating over result sets for complex reports.
14. Ensure all SELECT statements are labeled clearly for structured output (e.g., 'report_title', 'key_metrics').
15. Ensure variable declarations come before cursor and handler declarations to avoid error 1337.
16. The procedure MUST NOT have any parameters (e.g., IN month VARCHAR(20)) to avoid error 1318.
17. IMPORTANT: Format all data tables using structured output:
    - Use clear column headers separated by pipes (|) for table compatibility
    - Format data rows consistently with pipe separators
    - Ensure proper alignment and readability
    - Use standard SQL SELECT statements for data output
18. For each data table, include:
    - A clear header row with column names separated by ' | '
    - Data rows formatted consistently with ' | ' separators
    - Proper spacing for table readability
19. Non-table outputs (e.g., key metrics, conclusion) should use simple text formatting.
20. Ensure the output is clean, professional, and well-structured for display formatting.
21. **Response Format Requirements**:
   - Use pipe separators (|) for table data
   - Use clear headings and structure for better display
   - Format lists and metrics consistently

Example of a complete procedure structure with clean table formatting:
CREATE PROCEDURE {PROCEDURE_NAME}()
BEGIN
    -- Variable Declarations
    DECLARE total_sales DECIMAL(10,2);
    DECLARE current_month VARCHAR(20);
    DECLARE current_year INT;

    -- Error Handler
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SELECT 'Please check the database.' AS message;
        ROLLBACK;
    END;

    -- Check for sufficient data in required tables
    IF NOT EXISTS (SELECT 1 FROM users LIMIT 1)
       OR NOT EXISTS (SELECT 1 FROM orders LIMIT 1)
       OR NOT EXISTS (SELECT 1 FROM products LIMIT 1) THEN

        SELECT 'Not have sufficient data' AS message;

    ELSE
        -- Initialize Date Variables
        SET current_month = MONTHNAME(CURRENT_DATE);
        SET current_year = YEAR(CURRENT_DATE);

        -- Calculate Key Metric: Total Sales This Month
        SELECT SUM(total_amount)
        INTO total_sales
        FROM orders
        WHERE MONTH(order_date) = MONTH(CURRENT_DATE)
          AND YEAR(order_date) = YEAR(CURRENT_DATE);

        -- Report Title
        SELECT CONCAT('### Monthly Sales Report: ', current_month, ' ', current_year) AS report_title;

        -- Report Description
        SELECT 'Description: This report summarizes sales performance for the current month.' AS report_description;

        -- Key Metrics Section
        SELECT CONCAT('• Key Metrics: Total Sales: $', FORMAT(total_sales, 2)) AS key_metrics;

        -- Data Table Header
        SELECT 'User ID | Customer Name | Total Orders | Total Amount' AS table_header;

        -- Data Table Content
        SELECT
            CONCAT(
                u.user_id, ' | ',
                CONCAT(u.first_name, ' ', u.last_name), ' | ',
                COUNT(o.order_id), ' | ',
                '$', FORMAT(SUM(o.total_amount), 2)
            ) AS row_data
        FROM users u
        LEFT JOIN orders o ON u.user_id = o.user_id
        GROUP BY u.user_id, u.first_name, u.last_name
        ORDER BY SUM(o.total_amount) DESC
        LIMIT 100;

        -- Conclusion
        SELECT 'Conclusion: This report highlights the most valuable customers based on total sales.' AS conclusion;

        -- Recommendations
        SELECT 'Recommendation: Focus marketing and retention efforts on top-performing customers.' AS recommendations;

    END IF;
END;

CRITICAL: Return ONLY the complete, executable MySQL procedure code. The procedure must be complete from CREATE PROCEDURE to END; with all necessary SQL logic to answer the user's question. DO NOT include any parameters in the procedure definition. Focus on creating clean, readable output with simple table formatting using pipe separators."""

class LLMManager:
    """Centralized LLM management with consistent configuration"""
    
    def __init__(self, config: LLMConfig):
        self.config = config
        self._analytical_llm: Optional[ChatGoogleGenerativeAI] = None
        self._conversational_llm: Optional[ChatGoogleGenerativeAI] = None
    
    @property
    def analytical_llm(self) -> ChatGoogleGenerativeAI:
        """Get LLM instance for analytical tasks (deterministic)"""
        if self._analytical_llm is None:
            self._analytical_llm = ChatGoogleGenerativeAI(
                model=self.config.model,
                temperature=self.config.temperature_analytical,
                google_api_key=self.config.api_key
            )
        return self._analytical_llm
    
    @property
    def conversational_llm(self) -> ChatGoogleGenerativeAI:
        """Get LLM instance for conversational tasks"""
        if self._conversational_llm is None:
            self._conversational_llm = ChatGoogleGenerativeAI(
                model=self.config.model,
                temperature=self.config.temperature_conversational,
                google_api_key=self.config.api_key
            )
        return self._conversational_llm
    
    def invoke_analytical(self, messages: List[Any]) -> Any:
        """Invoke LLM for analytical tasks with error handling"""
        try:
            return self.analytical_llm.invoke(messages)
        except Exception as e:
            raise RuntimeError(f"LLM analytical invocation failed: {str(e)}")
    
    def invoke_conversational(self, messages: List[Any]) -> Any:
        """Invoke LLM for conversational tasks with error handling"""
        try:
            return self.conversational_llm.invoke(messages)
        except Exception as e:
            raise RuntimeError(f"LLM conversational invocation failed: {str(e)}")

# Global LLM Manager Instance
llm_manager = LLMManager(LLM_CONFIG)

class ErrorHandler:
    """Centralized error handling with consistent fallback responses"""
    
    @staticmethod
    def create_fallback_response(error_type: ErrorType, context: str = "") -> str:
        """Create consistent fallback responses for different error types"""
        
        base_templates = {
            ErrorType.LLM_GENERATION: {
                "title": "Query Analysis Issue",
                "description": "I encountered a temporary issue while analyzing your query, but I can still provide guidance for your data analysis needs.",
                "status": "Switching to alternative processing method",
                "examples": [
                    "Show me the top performers this month",
                    "Analyze sales trends by quarter", 
                    "Compare employee performance by department",
                    "Find customers with highest orders"
                ]
            },
            ErrorType.PROCEDURE_VALIDATION: {
                "title": "Query Processing Optimization",
                "description": "I detected an issue with the query processing parameters, but I can still assist you with your data analysis.",
                "status": "Adjusting processing parameters for compatibility",
                "examples": [
                    "List top 5 employees by performance",
                    "Show sales summary by department",
                    "Count products by category", 
                    "Average customer order value"
                ]
            },
            ErrorType.DATABASE_CONNECTION: {
                "title": "Database Connection Status",
                "description": "I'm experiencing a temporary connection issue with the database, but I can still provide guidance for your data analysis query.",
                "status": "Database connection being restored",
                "examples": [
                    "Employee performance and rankings",
                    "Sales analysis and trends",
                    "Customer behavior insights",
                    "Product performance metrics"
                ]
            },
            ErrorType.PROCEDURE_CREATION: {
                "title": "Procedure Setup Issue", 
                "description": "I encountered an issue while generating the SQL procedure for your query, but I can still help you with your data analysis needs.",
                "status": "Optimizing query structure for better results",
                "examples": [
                    "Show me employee performance rankings",
                    "Analyze sales data by month",
                    "Compare department statistics",
                    "Find top performing products"
                ]
            },
            ErrorType.PROCEDURE_EXECUTION: {
                "title": "Data Analysis Processing",
                "description": "I encountered a technical issue while executing the data analysis, but I can provide you with general guidance for your query.",
                "status": "Analysis attempted but requires optimization",
                "examples": [
                    "Show me the top 10 customers by order value",
                    "Count employees by department", 
                    "Average sales by month",
                    "List products with low stock"
                ]
            }
        }
        
        template = base_templates.get(error_type, base_templates[ErrorType.LLM_GENERATION])
        
        return f"""**Description:** {template['description']}

### 💡 {template['title']}

Your request has been received, but I need to handle it using an alternative approach.

- **Query Type**: Data analysis request identified
- **Current Status**: {template['status']}
- **Suggested Action**: Please try rephrasing your query with clearer specifications
- **Available Options**: You can ask about:
  - Basic data analysis and summaries
  - Performance metrics and rankings
  - Trend analysis and comparisons
  - Business intelligence insights

### 📊 Effective Query Examples

{chr(10).join(f'{i+1}. "{example}"' for i, example in enumerate(template['examples']))}

### 🔧 Technical Note

The analysis system is optimizing for better reliability. Please try a simplified version of your request.

**Conclusion:** I'm ready to help you analyze your data once you provide a clearer query format."""

    @staticmethod
    def handle_error(error_type: ErrorType, error: Exception, context: str = "") -> str:
        """Handle errors and return appropriate fallback response"""
        print(f"❌ Error ({error_type.value}): {error}")
        if context:
            print(f"Context: {context}")
        
        fallback_response = ErrorHandler.create_fallback_response(error_type, context)
        print(fallback_response)
        return fallback_response

def identify_relevant_tables(user_query: str, demo_data: Dict[str, Any]) -> List[str]:
    """
    Dynamically identify relevant tables based on user query and available demo data content.
    
    Args:
        user_query: The user's natural language query
        demo_data: Dictionary containing demo data for each table
        
    Returns:
        List of relevant table names for the query
        
    Example:
        >>> identify_relevant_tables("show employee performance", demo_data)
        ['employees', 'interviews']
    """
    query_lower = user_query.lower()
    relevant_tables = set()

    for table_name, rows in demo_data.items():
        # Skip empty tables
        if not rows:
            continue

        # Combine all keys (column names) from sample rows
        all_columns = set()
        for row in rows:
            all_columns.update(str(k).lower() for k in row.keys())

        # If any column name matches a word in the query, mark the table as relevant
        if any(col in query_lower for col in all_columns):
            relevant_tables.add(table_name)

        # Also match table name directly
        if table_name.lower() in query_lower:
            relevant_tables.add(table_name)

    # Add logic for special keywords (hiring, performance, etc.)
    if any(word in query_lower for word in ['hire', 'hiring', 'best', 'top', 'performance', 'rank']):
        if 'employees' in demo_data:
            relevant_tables.add('employees')
        if 'interviews' in demo_data:
            relevant_tables.add('interviews')

    if any(word in query_lower for word in ['candidate', 'interview', 'technical', 'communication', 'overall score','interview date']):
        if 'interviews' in demo_data:
            relevant_tables.add('interviews')

    if any(word in query_lower for word in ['customer', 'sales', 'revenue', 'purchase', 'order']):
        for tbl in ['users', 'orders', 'products']:
            if tbl in demo_data:
                relevant_tables.add(tbl)

    # Fallback: if no tables matched, return all non-empty demo tables
    if not relevant_tables:
        relevant_tables = {tbl for tbl, rows in demo_data.items() if rows}

    return list(relevant_tables)


def get_relevant_schema_from_demo_data(relevant_tables: list, demo_data: dict) -> dict:
    """
    Build schema for relevant tables from demo data (sample rows).
    """
    relevant_schema = {}
    for table in relevant_tables:
        if table in demo_data and demo_data[table]:
            sample_row = demo_data[table][0]
            column_types = {col: type(val).__name__ for col, val in sample_row.items()}
            relevant_schema[table] = column_types
    return relevant_schema


def suggest_performance_formulas(user_query: str) -> List[str]:
    """
    Suggest performance and ranking formulas based on query content.
    
    Args:
        user_query: The user's natural language query
        
    Returns:
        List of suggested performance formulas relevant to the query
        
    Example:
        >>> suggest_performance_formulas("find top employees")
        ['Performance Ranking: RANK() OVER (ORDER BY performance_score DESC)', ...]
    """
    suggestions = []
    query_lower = user_query.lower()

    if any(word in query_lower for word in ['hire', 'hiring', 'best', 'top']):
        suggestions.extend([
            "Performance Ranking: RANK() OVER (ORDER BY performance_score DESC)",
            "Top Performer: NTILE(4) for quartile ranking",
            "Overall Performance: Weighted scoring formula",
            "Percentile Rank: PERCENT_RANK() for relative positioning"
        ])

    if any(word in query_lower for word in ['sales', 'target', 'achievement']):
        suggestions.extend([
            "Sales Ranking: RANK() OVER (ORDER BY sales_amount DESC)",
            "Target Achievement: target_achieved percentage analysis",
            "Efficiency Ranking: sales_amount/sales_count ratio"
        ])

    if any(word in query_lower for word in ['trend', 'improvement', 'growth']):
        suggestions.extend([
            "Trend Analysis: LAG() and LEAD() functions",
            "Improvement Rate: Growth calculation over time",
            "Consistency Score: STDDEV() for performance stability"
        ])

    return suggestions

def generate_optimized_formulas(query_type, columns):
    """Generate optimized mathematical formulas based on query type and columns."""
    formulas = []

    if 'sales' in query_type.lower() or 'revenue' in query_type.lower():
        formulas.extend([
            f"SUM({columns.get('amount', 'total_amount')}) as total_sales",
            f"AVG({columns.get('amount', 'total_amount')}) as avg_sale",
            f"COUNT(DISTINCT {columns.get('customer', 'user_id')}) as unique_customers",
            f"STDDEV({columns.get('amount', 'total_amount')}) as sales_deviation",
            f"MAX({columns.get('amount', 'total_amount')}) - MIN({columns.get('amount', 'total_amount')}) as sales_range"
        ])

    if 'performance' in query_type.lower() or 'analysis' in query_type.lower():
        formulas.extend([
            f"RANK() OVER (ORDER BY {columns.get('metric', 'total_amount')} DESC) as performance_rank",
            f"PERCENT_RANK() OVER (ORDER BY {columns.get('metric', 'total_amount')}) as percentile_rank",
            f"ROW_NUMBER() OVER (PARTITION BY {columns.get('category', 'category')} ORDER BY {columns.get('metric', 'total_amount')} DESC) as category_rank"
        ])

    if 'trend' in query_type.lower() or 'growth' in query_type.lower():
        formulas.extend([
            f"LAG({columns.get('amount', 'total_amount')}, 1) OVER (ORDER BY {columns.get('date', 'order_date')}) as previous_value",
            f"LEAD({columns.get('amount', 'total_amount')}, 1) OVER (ORDER BY {columns.get('date', 'order_date')}) as next_value",
            f"AVG({columns.get('amount', 'total_amount')}) OVER (ORDER BY {columns.get('date', 'order_date')} ROWS BETWEEN 2 PRECEDING AND CURRENT ROW) as moving_avg_3"
        ])

    return formulas

def create_optimization_hints(table_names):
    """Create safe optimization hints for the given tables (comments only)."""
    hints = []

    # Add safe table-specific optimization comments 
    for table in table_names:
        if 'orders' in table:
            hints.append("-- Optimize orders table queries with date and user_id filtering")
        elif 'products' in table:
            hints.append("-- Optimize products table queries with category filtering")
        elif 'users' in table:
            hints.append("-- Optimize users table queries with registration date filtering")

    # Add general optimization hints (safe comments only )
    hints.extend([
        "-- Use LIMIT for large result sets",
        "-- Use batch processing for datasets > 5000 records",
        "-- Monitor execution time and optimize accordingly",
        "-- Use proper JOIN conditions for better performance",
        "-- IMPORTANT: Keep procedures simple and avoid complex cursor operations"
    ])

    return hints

def create_simple_sales_procedure_example():
    """Create a simple, working sales procedure"""
    return """
CREATE PROCEDURE user_query_procedure()
BEGIN
    DECLARE v_current_month VARCHAR(20);
    DECLARE v_current_year INT;

    -- Simple error handling
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SELECT 'Please check the database' AS message;
        ROLLBACK;
    END;

    SET v_current_month = MONTHNAME(CURRENT_DATE());
    SET v_current_year = YEAR(CURRENT_DATE());

    -- Report Title
    SELECT CONCAT('### Sales Analysis Report: ', v_current_month, ' ', v_current_year) AS report_title;

    -- Report Description
    SELECT 'Description: This report provides a simple analysis of sales data with monthly trends and top products.' AS report_description;

    -- Key Metrics (simple calculation)
    SELECT CONCAT(
        '• Key Metrics: ',
        'Total Orders: ', COUNT(*),
        ' | Total Revenue: $', FORMAT(SUM(total_amount), 2)
    ) AS key_metrics
    FROM orders
    WHERE order_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 12 MONTH);

    -- Monthly Sales Table Header
    SELECT 'Year | Month | Total Sales | Order Count' AS table_header;

    -- Monthly Sales Data (simple aggregation )
    SELECT CONCAT(
        YEAR(order_date), ' | ',
        MONTHNAME(order_date), ' | ',
        '$', FORMAT(SUM(total_amount), 2), ' | ',
        COUNT(*)
    ) AS monthly_sales_data
    FROM orders
    WHERE order_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 12 MONTH)
    GROUP BY YEAR(order_date), MONTH(order_date)
    ORDER BY YEAR(order_date), MONTH(order_date)
    LIMIT 12;

    -- Top Products (simple join )
    SELECT CONCAT(
        p.product_name, ' | ',
        p.category, ' | ',
        SUM(o.quantity), ' | ',
        '$', FORMAT(SUM(o.total_amount), 2)
    ) AS top_products_data
    FROM orders o
    INNER JOIN products p ON o.product_id = p.product_id
    WHERE o.order_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 3 MONTH)
    GROUP BY p.product_id, p.product_name, p.category
    ORDER BY SUM(o.total_amount) DESC
    LIMIT 10;

    -- Conclusion
    SELECT 'Conclusion: This simplified report shows sales trends without complex calculations or dependencies.' AS conclusion;

END;
"""

def estimate_data_size(cursor, table_name):
    """Estimate the size of data in a table."""
    try:
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        return count
    except:
        return 0

def has_repeated_sql_keywords(procedure_code):
    """Check for repeated SQL keywords in the generated procedure."""
    repeated_patterns = [
        r'FROM\s+FROM',
        r'WHERE\s+WHERE',
        r'ORDER BY\s+ORDER BY',
        r'GROUP BY\s+GROUP BY',
        r'SELECT\s+SELECT',
    ]
    for pattern in repeated_patterns:
        if re.search(pattern, procedure_code, re.IGNORECASE):
            return True
    return False

def has_parameters(procedure_code):
    """Check if the procedure has parameters."""
    return bool(re.search(r'CREATE\s+PROCEDURE\s+user_query_procedure\s*\([^)]+\)', procedure_code, re.IGNORECASE))

def extract_procedure_code(procedure_code):
    """Extract only the CREATE PROCEDURE...END; part from the LLM response."""
    try:
        procedure_code = procedure_code.strip()
        
        # Remove markdown code blocks if present
        if '```sql' in procedure_code:
            sql_match = re.search(r'```sql\s*(.*?)\s*```', procedure_code, re.DOTALL | re.IGNORECASE)
            if sql_match:
                procedure_code = sql_match.group(1).strip()
        elif '```' in procedure_code:
            code_match = re.search(r'```\s*(.*?)\s*```', procedure_code, re.DOTALL)
            if code_match:
                procedure_code = code_match.group(1).strip()
        
        # Find the CREATE PROCEDURE statement
        create_match = re.search(r'CREATE\s+PROCEDURE\s+[^(]+\([^)]*\)\s*BEGIN.*?END\s*;?\s*$', procedure_code, re.IGNORECASE | re.DOTALL)
        if create_match:
            result = create_match.group(0).strip()
            if not result.upper().endswith('END;'):
                result = result.rstrip(';') + ';'
            return result
        
        # Alternative pattern for CREATE PROCEDURE
        create_match = re.search(r'CREATE\s+PROCEDURE.*?END', procedure_code, re.IGNORECASE | re.DOTALL)
        if create_match:
            result = create_match.group(0).strip() + ";"
            return result
        
        # If no pattern matches, return the original code
        return procedure_code
        
    except Exception as e:
        print(f"Error extracting procedure code: {e}")
        return procedure_code  # Return original code if extraction fails



def format_structured_report(results, generation_time, procedure_code, user_query):
    """Format the query results into a structured markdown report starting from description."""
    markdown_output = []

    if not results:
        markdown_output.append("⚠️ **No results returned from the procedure.**")
        markdown_output.append("*Possible cause: Empty tables or query returned no data.*")
        return "\n".join(markdown_output)

    # Process results and identify different types
    report_description = None
    key_metrics = []
    table_data = []
    table_components = []
    conclusions = []

    for row in results:
        if isinstance(row, tuple) and len(row) == 1:
            value = row[0]
            if isinstance(value, str):
                if value.startswith('Description:'):
                    report_description = value.replace('Description:', '').strip()
                elif value.startswith('• Key Metrics:') or value.startswith('Key Metrics:'):
                    key_metrics.append(value)
                elif value.startswith('Conclusion:'):
                    conclusions.append(value.replace('Conclusion:', '').strip())
                elif 'insufficient data' in value.lower() or 'error' in value.lower():
                    error_messages.append(value)
                elif ' | ' in value and not value.startswith('###'):
                    # This is likely table data with pipe separators
                    table_components.append(value)
                else:
                    table_data.append(value)
    # if error_messages:
    #     markdown_output.append("❌ **Error Messages:**")
    #     for error in error_messages:
    #         markdown_output.append(f"- {error}")
    #     markdown_output.append("")
    #     return "\n".join(markdown_output)
    # Start directly with Report Description (skip title)
    if report_description:
        markdown_output.append(f"**Description:** {report_description}")
        markdown_output.append("")

    # Display Key Metrics
    if key_metrics:
        markdown_output.append("### 📊 Key Metrics")
        for metric in key_metrics:
            # Clean up the metric text and format as bullet point
            clean_metric = metric.replace('• Key Metrics:', '').replace('Key Metrics:', '').strip()
            markdown_output.append(f"- {clean_metric}")
        markdown_output.append("")

    # Display Tables in Markdown format (only if there's actual data)
    if table_components:
        # Check if we have actual data rows (not just headers)
        has_data_rows = False
        header_row = None
        data_rows = []

        if len(table_components) > 0:
            header_row = table_components[0]
            # Check for actual data rows beyond the header
            for component in table_components[1:]:
                if ' | ' in component and component.strip():
                    # Check if the row has actual data (not just empty cells)
                    data_cells = [cell.strip() for cell in component.split(' | ')]
                    if any(cell for cell in data_cells):  # At least one non-empty cell
                        has_data_rows = True
                        data_rows.append(component)

        # Only display table if we have both header and actual data
        if has_data_rows and header_row and ' | ' in header_row:
            markdown_output.append("### 📋 Data Tables")
            markdown_output.append("")

            # Create markdown table header
            headers = [h.strip() for h in header_row.split(' | ')]
            markdown_output.append('| ' + ' | '.join(headers) + ' |')
            markdown_output.append('|' + '---|' * len(headers))

            # Add data rows
            for component in data_rows:
                if ' | ' in component:
                    data_cells = [cell.strip() for cell in component.split(' | ')]
                    # Ensure we have the same number of cells as headers
                    while len(data_cells) < len(headers):
                        data_cells.append('')
                    markdown_output.append('| ' + ' | '.join(data_cells) + ' |')

            markdown_output.append("")

    # Display Other Data
    if table_data:
        markdown_output.append("### 📄 Additional Information")
        for item in table_data:
            if item.strip():
                markdown_output.append(f"- {item}")
        markdown_output.append("")

    # Display Conclusions
    if conclusions:
        markdown_output.append("### 💡 Conclusions")
        for conclusion in conclusions:
            markdown_output.append(f"**Conclusion:** {conclusion}")
        markdown_output.append("")

    # Return the formatted markdown content (no footer)
    markdown_content = "\n".join(markdown_output)
    return markdown_content

def analyze_dataset_size(cursor):
    """Analyze your existing dataset size and recommend optimization strategies."""
    try:
        dataset_info = {}
        required_tables = ['users', 'products', 'orders']

        for table in required_tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            dataset_info[table] = count

        total_records = sum(dataset_info.values())

        print(f"\n📊 Your Dataset Analysis:")
        print(f"{'='*50}")
        for table, count in dataset_info.items():
            print(f"{table.capitalize()}: {count:,} records")
        print(f"Total Records: {total_records:,}")

        # Recommend optimization strategies based on actual data size
        if total_records > 5000:
            print(f"\n🚀 Large Dataset ({total_records:,} records)")
            print("Applying Advanced Optimizations:")
            print("• Batch processing for complex calculations")
            print("• Result pagination and limiting")
           
        elif total_records > 1000:
            print(f"\n⚡ Medium Dataset ({total_records:,} records)")
            print("Applying Standard Optimizations:")
            print("• Result limiting for display")
            print("• Efficient JOIN operations")
        elif total_records > 0:
            print(f"\n✅ Dataset Ready ({total_records:,} records)")
            print("Using standard processing - efficient for this size")
        else:
            print(f"\n⚠️ Empty Dataset")
            print("No data found in tables - procedures may return empty results")

        return dataset_info, total_records

    except Error as e:
        print(f"❌ Error analyzing dataset: {e}")
        return {}, 0

def verify_database_setup(cursor):
    """Verify that required tables exist and contain data in the database"""
    try:
        cursor.execute("SHOW TABLES")
        tables = [table[0] for table in cursor.fetchall()]

        required_tables = ['users', 'products', 'orders']
        missing_tables = [table for table in required_tables if table not in tables]

        if missing_tables:
            print(f"❌ Missing required tables: {missing_tables}")
            print("Please run check_tables.py to create sample tables first.")
            return False

        # Analyze dataset size and provide optimization recommendations
        _, total_records = analyze_dataset_size(cursor)

        if total_records == 0:
            print("⚠️ Warning: All tables are empty.")
            print("This may cause the procedure to return no results.")

        print("✅ All required tables found: users, products, orders")
        return True

    except Error as e:
        print(f"❌ Error checking tables: {e}")
        return False

def suggest_mathematical_formulas(user_query):
    """Suggest relevant mathematical formulas based on user query."""
    suggestions = []
    query_lower = user_query.lower()

    # Analyze query for mathematical requirements
    if any(word in query_lower for word in ['average', 'mean', 'avg']):
        suggestions.append("Statistical: AVG() for mean calculations")

    if any(word in query_lower for word in ['total', 'sum', 'revenue', 'sales']):
        suggestions.append("Aggregation: SUM() for total calculations")

    if any(word in query_lower for word in ['growth', 'trend', 'change', 'increase']):
        suggestions.append("Business: Growth rate and trend analysis formulas")

    if any(word in query_lower for word in ['rank', 'top', 'best', 'worst']):
        suggestions.append("Ranking: RANK(), DENSE_RANK(), ROW_NUMBER()")

    if any(word in query_lower for word in ['deviation', 'variance', 'spread']):
        suggestions.append("Statistical: STDDEV(), VARIANCE() for data spread")

    if any(word in query_lower for word in ['percentile', 'median', 'quartile']):
        suggestions.append("Statistical: PERCENTILE_CONT() for distribution analysis")

    return suggestions

class ProcedureAgent:
    """Main agent class for SQL procedure generation and execution"""
    
    def __init__(self, llm_manager: LLMManager, db_config: DatabaseConfig):
        self.llm_manager = llm_manager
        self.db_config = db_config
        self.error_handler = ErrorHandler()
    
    def analyze_query(self, user_query: str) -> None:
        """Step 1: Analyze user query and display information"""
        print("\n" + "="*60)
        print("STEP 1: LLM-Based Query Analysis & Smart Table Selection")
        print("="*60)
        print(f"Query: {user_query}")
        print("🤖 Using LLM for intelligent table selection and query analysis...")
    
    def generate_procedure_code(self, user_query: str) -> Tuple[str, str]:
        """Step 2: Generate procedure code using LLM"""
        print("\n" + "="*60)
        print("STEP 2: Create Optimized Procedure (LLM Smart Table Selection)")
        print("="*60)
        generation_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S IST")
        print(f"Procedure Generation Time: {generation_time}")
        print("🎯 LLM will intelligently select relevant tables and optimize for performance...")
        
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=user_query)
        ]
        
        try:
            response = self.llm_manager.invoke_analytical(messages)
            procedure_code = response.content
            print("✅ LLM generated optimized procedure with smart table selection")
            print("Generated Procedure:")
            print(procedure_code)
            return procedure_code, generation_time
        except Exception as e:
            self.error_handler.handle_error(ErrorType.LLM_GENERATION, e, user_query)
            raise
    
    def validate_procedure_code(self, procedure_code: str) -> bool:
        """Step 3: Validate generated procedure code"""
        if has_repeated_sql_keywords(procedure_code):
            print("\n❌ ERROR: Detected repeated SQL keywords in generated code.")
            print("Please review and correct before execution.")
            self.error_handler.handle_error(
                ErrorType.PROCEDURE_VALIDATION, 
                Exception("Repeated SQL keywords detected"), 
                "SQL validation"
            )
            return False
        
        if has_parameters(procedure_code):
            print("\n❌ ERROR: Generated procedure contains parameters, which is not allowed.")
            print("Please ensure the procedure is parameterless.")
            self.error_handler.handle_error(
                ErrorType.PROCEDURE_VALIDATION,
                Exception("Procedure contains parameters"),
                "Parameter validation"
            )
            return False
            
        return True
    
    def establish_database_connection(self) -> Tuple[Any, Any]:
        """Step 4: Establish database connection"""
        print("\n" + "="*60)
        print("STEP 3: Execute Procedure")
        print("="*60)
        
        try:
            connection = mysql.connector.connect(**DB_CONFIG)
            if not connection.is_connected():
                print("❌ Failed to connect to MySQL database.")
                self.error_handler.handle_error(
                    ErrorType.DATABASE_CONNECTION,
                    Exception("Failed to connect to MySQL"),
                    "Connection establishment"
                )
                raise ConnectionError("Database connection failed")
            
            cursor = connection.cursor()
            print("✅ Connected to MySQL database")
            
            # Verify database setup
            if not verify_database_setup(cursor):
                raise Exception("Database setup verification failed")
                
            return connection, cursor
            
        except Error as e:
            self.error_handler.handle_error(ErrorType.DATABASE_CONNECTION, e, "MySQL connection")
            raise
    
    def create_procedure(self, connection: Any, cursor: Any, procedure_code: str) -> bool:
        """Step 5: Create SQL procedure"""
        try:
            cursor.execute(f"DROP PROCEDURE IF EXISTS {self.db_config.procedure_name}")
            connection.commit()
            print("✅ Dropped existing procedure")
        except Error as e:
            print(f"❌ Error dropping procedure: {e}")
        
        cleaned_procedure = extract_procedure_code(procedure_code)
        try:
            print(f"Extracted procedure code:")
            print("-" * 40)
            print(cleaned_procedure)
            print("-" * 40)
            
            cursor.execute(cleaned_procedure)
            connection.commit()
            print(f"✅ Successfully created procedure: {self.db_config.procedure_name}")
            
            # Verify procedure was created
            cursor.execute("SHOW PROCEDURE STATUS WHERE Name = %s", (self.db_config.procedure_name,))
            procedures = cursor.fetchall()
            if procedures:
                print(f"✅ Procedure verified in database: {self.db_config.procedure_name}")
                return True
            else:
                print(f"❌ Procedure not found in database after creation: {self.db_config.procedure_name}")
                self.error_handler.handle_error(
                    ErrorType.PROCEDURE_CREATION,
                    Exception("Procedure not found after creation"),
                    "Procedure verification"
                )
                return False
                
        except Error as e:
            self.error_handler.handle_error(ErrorType.PROCEDURE_CREATION, e, "Procedure creation")
            return False
    
    def execute_procedure_and_get_results(self, cursor: Any, user_query: str, procedure_code: str, generation_time: str) -> None:
        """Step 6: Execute procedure and process results"""
        try:
            # Execute procedure using CALL statement
            cursor.execute(f"CALL {self.db_config.procedure_name}()")
            results = []
            
            # Process all result sets robustly
            more_results = True
            while more_results:
                try:
                    # Fetch results from current result set
                    result = cursor.fetchall()
                    if result:
                        results.extend(result)
                except Error as e:
                    if "No result set" not in str(e):
                        print(f"⚠️ Warning: Error fetching result set: {e}")
                
                # Move to next result set
                try:
                    more_results = cursor.nextset()
                except Error:
                    more_results = False
            
            print("✅ Procedure executed successfully")

            # Generate and display markdown report
            markdown_content = format_structured_report(results, generation_time, procedure_code, user_query)
            print(markdown_content)
                
        except Error as e:
            print(f"❌ Error executing procedure: {e}")
            print("Trying alternative execution method...")
            try:
                # Alternative: use callproc
                cursor.callproc(self.db_config.procedure_name)
                results = []
                
                # Process all result sets from callproc
                more_results = True
                while more_results:
                    try:
                        result = cursor.fetchall()
                        if result:
                            results.extend(result)
                    except Error as e:
                        if "No result set" not in str(e):
                            print(f"⚠️ Warning: Error fetching result set: {e}")
                    
                    try:
                        more_results = cursor.nextset()
                    except Error:
                        more_results = False
                
                print("✅ Procedure executed successfully (alternative method)")
                # Generate and display markdown report
                markdown_content = format_structured_report(results, generation_time, procedure_code, user_query)
                print(markdown_content)
                
            except Error as e2:
                self.error_handler.handle_error(ErrorType.PROCEDURE_EXECUTION, e2, "Alternative execution")
                raise
    
    def cleanup_resources(self, connection: Any, cursor: Any) -> None:
        """Step 7: Clean up database resources"""
        # Clean up any remaining results
        try:
            while cursor.nextset():
                pass
        except Error:
            pass

        try:
            cursor.execute(f"DROP PROCEDURE IF EXISTS {self.db_config.procedure_name}")
            connection.commit()
        except Error as e:
            print(f"❌ Error dropping procedure: {e}")
        finally:
            # Properly close cursor and connection
            try:
                if cursor:
                    try:
                        while cursor.nextset():
                            pass
                    except:
                        pass
                    cursor.close()
            except:
                pass
            
            try:
                if connection and connection.is_connected():
                    connection.close()
            except:
                pass
    
    def execute_procedure(self, user_query: str, procedure_code: str, generation_time: str) -> None:
        """Execute the complete procedure workflow"""
        connection = None
        cursor = None
        
        try:
            # Establish database connection
            connection, cursor = self.establish_database_connection()
            
            # Create procedure
            if not self.create_procedure(connection, cursor, procedure_code):
                return
            
            # Execute procedure and get results
            self.execute_procedure_and_get_results(cursor, user_query, procedure_code, generation_time)
            
        finally:
            # Always cleanup resources
            if connection and cursor:
                self.cleanup_resources(connection, cursor)

def run_sql_procedure_agent(user_query: str) -> None:
    """Enhanced main function with LLM-based smart table selection and performance ranking."""
    
    # Create agent instance
    agent = ProcedureAgent(llm_manager, DB_CONFIG_WRAPPER)
    
    try:
        # Step 1: Analyze query
        agent.analyze_query(user_query)
        
        # Step 2: Generate procedure code
        procedure_code, generation_time = agent.generate_procedure_code(user_query)
        
        # Step 3: Validate procedure code
        if not agent.validate_procedure_code(procedure_code):
            return
            
        # Step 4: Execute procedure (remaining implementation)
        agent.execute_procedure(user_query, procedure_code, generation_time)
        
    except Exception as e:
        # All errors are already handled by individual methods
        return







def show_example_queries():
    """Display example queries that demonstrate mathematical formulas and optimization for your existing data."""
    examples = [
        {
            "title": "🏆 Best Employee for Hiring/Promotion",
            "query": "Find the top 3 best performing employees based on performance rating and salary efficiency for hiring decisions",
            "formulas": ["RANK()", "NTILE()", "Performance Rating Analysis", "TOP N Selection"],
            "tables": ["employees"]
        },
        {
            "title": " Best Candidates from Interviews",
            "query": "Rank interview candidates by overall score and recommend top 5 candidates for hiring",
            "formulas": ["RANK()", "ROW_NUMBER()", "Combined Score", "Hire Recommendation"],
            "tables": ["interviews"]
        },
        {
            "title": " Department Performance Analysis",
            "query": "Analyze employee performance by department with rankings and statistical measures",
            "formulas": ["RANK() PARTITION BY", "AVG()", "STDDEV()", "Department Comparison"],
            "tables": ["employees"]
        },
        {
            "title": " Interview Success Analysis",
            "query": "Analyze interview success rates by position with technical vs communication score analysis",
            "formulas": ["Success Rate", "AVG()", "Technical vs Communication Analysis"],
            "tables": ["interviews"]
        },
        {
            "title": "💰 Salary vs Performance Analysis",
            "query": "Find employees with best performance-to-salary ratio for promotion recommendations",
            "formulas": ["Performance/Salary Ratio", "RANK()", "Efficiency Analysis"],
            "tables": ["employees"]
        },
        {
            "title": " Hiring Pipeline Analysis",
            "query": "Analyze hiring pipeline with candidate scores, success rates, and position-wise performance",
            "formulas": ["Pipeline Analysis", "Success Rate by Position", "Score Distribution"],
            "tables": ["interviews"]
        },
        {
            "title": "📊 Sales Performance Analysis",
            "query": "Generate comprehensive sales report with customer rankings and statistical analysis",
            "formulas": ["SUM()", "AVG()", "STDDEV()", "RANK()", "COUNT()"],
            "tables": ["users", "orders", "products"]
        }
    ]

    print("\n" + "="*60)
    print("📚 EXAMPLE QUERIES FOR YOUR EXISTING DATA")
    print("="*60)

    for i, example in enumerate(examples, 1):
        print(f"\n{i}. {example['title']}")
        print(f"   Query: {example['query']}")
        print(f"   Formulas: {', '.join(example['formulas'])}")
        if 'tables' in example:
            print(f"   Tables: {', '.join(example['tables'])}")

    print(f"\n{'='*60}")
    print("💡 Tips for Hiring & Performance Queries:")
    print("• Use 'top 3 employees' or 'best 5 candidates' for specific results")
    print("• Ask for performance rankings by department")
    print("• Request interview success analysis by position")
    print("• Mention salary efficiency or performance-to-salary ratio")
    print("• Ask for hiring recommendations based on scores")
    print("• Include statistical analysis (avg, stddev, percentiles)")
    print("• Request quartile-based performance grouping")
    print("="*60)

def test_llm_table_selection():
    """Test function to demonstrate LLM-based table selection with different query types."""
    test_queries = [
        "Find the top 3 best performing employees for hiring decisions",
        "Analyze interview candidates and rank them by overall score",
        "Generate a sales report with customer rankings",
        "Show product performance analysis with inventory levels",
        "Analyze user behavior and purchase patterns",
        "Find employees with best performance-to-salary ratio",
        "Compare interview success rates across different positions",
        "Generate comprehensive business analysis report"
    ]
    
    print("\n" + "="*60)
    print("🧪 TESTING LLM-BASED TABLE SELECTION")
    print("="*60)
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{i}. Query: {query}")
        print("Expected LLM Table Selection:")
        
        # Show expected table selection based on keywords
        if any(word in query.lower() for word in ['employee', 'performance', 'hiring', 'best']):
            print("   → Expected: employees table")
        elif any(word in query.lower() for word in ['interview', 'candidate', 'overall score']):
            print("   → Expected: interviews table")
        elif any(word in query.lower() for word in ['sales', 'customer', 'revenue']):
            print("   → Expected: users + orders + products tables")
        elif any(word in query.lower() for word in ['product', 'inventory']):
            print("   → Expected: products + orders tables")
        elif any(word in query.lower() for word in ['user', 'behavior', 'purchase']):
            print("   → Expected: users + orders tables")
        elif any(word in query.lower() for word in ['salary', 'ratio']):
            print("   → Expected: employees table")
        elif any(word in query.lower() for word in ['success rate', 'position']):
            print("   → Expected: interviews table")
        elif any(word in query.lower() for word in ['comprehensive', 'business']):
            print("   → Expected: All relevant tables based on context")
        
        print("   → LLM will intelligently select based on context and keywords")
    
    print(f"\n{'='*60}")
    print("✅ LLM will handle complex queries and edge cases better than hardcoded rules")
    print("✅ LLM can understand context and select appropriate tables")
    print("✅ LLM can handle queries that span multiple domains")
    print("✅ LLM can optimize JOINs based on actual query needs")
    print("="*60)

if __name__ == "__main__":
    print("SQL Procedure Agent - Large Dataset Optimization")
    print("Specialized for handling large datasets with mathematical formulas")
    print("Works with your existing MySQL data")
    print("📄 Enhanced structured formatting for reports!")
    print("Type 'quit' to exit, 'examples' to see sample queries")
    print("="*60)

    while True:
        user_query = input("\nEnter your query: ").strip()
        if user_query.lower() in ['quit', 'exit', 'q']:
            print("Goodbye!")
            break
        elif user_query.lower() in ['examples', 'example', 'help']:
            show_example_queries()
        elif user_query.lower() in ['test', 'test_llm']:
            test_llm_table_selection()

        elif user_query:
            run_sql_procedure_agent(user_query)
        else:
            print("Please enter a query, 'examples' for sample queries, or 'quit' to exit.")

def direct_llm_conversation(user_query: str, query_history: Optional[List[str]] = None, past_conversations: Optional[List[Dict[str, Any]]] = None) -> str:
    """Handle direct conversation with LLM using query history and past conversations."""
    try:

        # Build context from query history and past conversations
        context_parts = []

        if past_conversations:
            context_parts.append("Previous conversations:")
            for conv in past_conversations[-5:]:  # Last 5 conversations
                context_parts.append(f"User: {conv.get('user_message', '')}")
                context_parts.append(f"Assistant: {conv.get('ai_response', '')}")

        if query_history:
            context_parts.append("Recent queries:")
            for query in query_history[-3:]:  # Last 3 queries
                context_parts.append(f"- {query}")

        context = "\n".join(context_parts) if context_parts else "No previous context available."

        # Check if it's a simple greeting or casual conversation
        simple_greetings = ['hi', 'hello', 'hey', 'hy', 'good morning', 'good afternoon', 'good evening']
        if any(greeting in user_query.lower() for greeting in simple_greetings):
            simple_responses = [
                "Hello! How can I help you today?",
                "Hi there! What would you like to know?",
                "Hey! I'm here to assist you with data queries and conversations.",
                "Hello! Feel free to ask me anything about your data or just chat."
            ]
            import random
            return random.choice(simple_responses)

        # Create conversation prompt
        system_message = SystemMessage(content=f"""You are a helpful AI assistant for a data chat application.
        You can have conversations about data, answer questions, and provide assistance.

        Context from previous interactions:
        {context}

        Guidelines:
        - Be conversational and helpful
        - If asked about data but no database context is available, explain that you can still help with general questions
        - Keep responses concise but informative
        - Be friendly and engaging
        - If the user asks simple questions like greetings, respond naturally
        """)

        human_message = HumanMessage(content=user_query)
        messages = [system_message, human_message]

        # Get LLM response using the global LLM manager
        response = llm_manager.invoke_conversational(messages)
        return response.content.strip()

    except Exception as e:
        print(f"Error in direct LLM conversation: {e}")
        return "I'm here to help! Could you please rephrase your question?"

def check_database_availability():
    """Check if database is available and has sufficient data."""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor()

        # Check if main tables exist and have data
        required_tables = ['users', 'products', 'orders']
        table_data_count = {}

        for table in required_tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                table_data_count[table] = count
            except Error:
                table_data_count[table] = 0

        cursor.close()
        connection.close()

        # Check if we have sufficient data (at least 10 records in main tables)
        total_records = sum(table_data_count.values())
        has_sufficient_data = total_records >= 30  # At least 10 records per table

        return True, has_sufficient_data, table_data_count

    except Error as e:
        print(f"Database not available: {e}")
        return False, False, {}



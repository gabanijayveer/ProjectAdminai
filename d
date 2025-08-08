[33mcommit adfd18f184102071fe5d5aca5db648121a176e4f[m[33m ([m[1;36mHEAD[m[33m -> [m[1;32mjayveer[m[33m, [m[1;33mtag: [m[1;33mv1.0[m[33m)[m
Author: jayveergabani <jayveerjnext@gmail.com>
Date:   Fri Aug 8 16:36:38 2025 +0530

    task for the Ai assiestent admin updated

[1mdiff --git a/.vscode/settings.json b/.vscode/settings.json[m
[1mnew file mode 100644[m
[1mindex 0000000..961f036[m
[1m--- /dev/null[m
[1m+++ b/.vscode/settings.json[m
[36m@@ -0,0 +1,7 @@[m
[32m+[m[32m{[m
[32m+[m	[32m"python.testing.pytestArgs": [[m
[32m+[m		[32m"frontend"[m
[32m+[m	[32m],[m
[32m+[m	[32m"python.testing.unittestEnabled": false,[m
[32m+[m	[32m"python.testing.pytestEnabled": true[m
[32m+[m[32m}[m
[1mdiff --git a/Proceduremanager.py b/Proceduremanager.py[m
[1mnew file mode 100644[m
[1mindex 0000000..758b8f3[m
[1m--- /dev/null[m
[1m+++ b/Proceduremanager.py[m
[36m@@ -0,0 +1,1728 @@[m
[32m+[m[32mimport os[m
[32m+[m[32mimport mysql.connector[m
[32m+[m[32mfrom mysql.connector import Error[m
[32m+[m[32mfrom langchain_google_genai import ChatGoogleGenerativeAI[m
[32m+[m[32mfrom langchain.schema import HumanMessage, SystemMessage[m
[32m+[m[32mimport json[m
[32m+[m[32mimport re[m
[32m+[m[32mfrom datetime import datetime[m
[32m+[m[32mfrom typing import Dict, List, Optional, Tuple, Any, Union[m
[32m+[m[32mfrom dataclasses import dataclass[m
[32m+[m[32mfrom enum import Enum[m
[32m+[m
[32m+[m[32m# Set your Google API key[m
[32m+[m[32mos.environ["GOOGLE_API_KEY"] = "AIzaSyAatriP47wO05S2e-egmPZjvWGnqyB_izQ"[m
[32m+[m
[32m+[m[32m# Configuration Classes for Better Structure[m
[32m+[m[32m@dataclass[m
[32m+[m[32mclass LLMConfig:[m
[32m+[m[32m    """Configuration for LLM instances"""[m
[32m+[m[32m    model: str = "gemini-2.5-flash"[m
[32m+[m[32m    temperature_analytical: float = 0.0[m
[32m+[m[32m    temperature_conversational: float = 0.7[m
[32m+[m[32m    api_key: str = os.environ.get("GOOGLE_API_KEY", "")[m
[32m+[m
[32m+[m[32m@dataclass[m
[32m+[m[32mclass DatabaseConfig:[m
[32m+[m[32m    """Database configuration wrapper"""[m
[32m+[m[32m    procedure_name: str = "user_query_procedure"[m
[32m+[m[32m    batch_size: int = 1000[m
[32m+[m[32m    limit_results: int = 100[m
[32m+[m
[32m+[m[32mclass ErrorType(Enum):[m
[32m+[m[32m    """Enumeration for different error types"""[m
[32m+[m[32m    LLM_GENERATION = "llm_generation"[m
[32m+[m[32m    PROCEDURE_VALIDATION = "procedure_validation"[m[41m [m
[32m+[m[32m    DATABASE_CONNECTION = "database_connection"[m
[32m+[m[32m    PROCEDURE_CREATION = "procedure_creation"[m
[32m+[m[32m    PROCEDURE_EXECUTION = "procedure_execution"[m
[32m+[m
[32m+[m[32m# Global Configuration Instances[m
[32m+[m[32mLLM_CONFIG = LLMConfig()[m
[32m+[m[32mDB_CONFIG_WRAPPER = DatabaseConfig()[m
[32m+[m
[32m+[m[32m# Mathematical formulas and aggregation functions for large datasets[m
[32m+[m[32mMATH_FORMULAS = {[m
[32m+[m[32m    'statistical': {[m
[32m+[m[32m        'mean': 'AVG({column})',[m
[32m+[m[32m        'median': 'PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY {column})',[m
[32m+[m[32m        'mode': 'MODE() WITHIN GROUP (ORDER BY {column})',[m
[32m+[m[32m        'std_dev': 'STDDEV({column})',[m
[32m+[m[32m        'variance': 'VARIANCE({column})',[m
[32m+[m[32m        'percentile_25': 'PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY {column})',[m
[32m+[m[32m        'percentile_75': 'PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY {column})',[m
[32m+[m[32m        'range': 'MAX({column}) - MIN({column})',[m
[32m+[m[32m        'coefficient_variation': 'STDDEV({column}) / AVG({column}) * 100'[m
[32m+[m[32m    },[m
[32m+[m[32m    'aggregation': {[m
[32m+[m[32m        'sum': 'SUM({column})',[m
[32m+[m[32m        'count': 'COUNT({column})',[m
[32m+[m[32m        'count_distinct': 'COUNT(DISTINCT {column})',[m
[32m+[m[32m        'min': 'MIN({column})',[m
[32m+[m[32m        'max': 'MAX({column})',[m
[32m+[m[32m        'avg': 'AVG({column})',[m
[32m+[m[32m        'group_concat': 'GROUP_CONCAT({column} SEPARATOR \', \')'[m
[32m+[m[32m    },[m
[32m+[m[32m    'business': {[m
[32m+[m[32m        'growth_rate': '((current_value - previous_value) / previous_value) * 100',[m
[32m+[m[32m        'moving_average': 'AVG({column}) OVER (ORDER BY {date_column} ROWS BETWEEN {n} PRECEDING AND CURRENT ROW)',[m
[32m+[m[32m        'cumulative_sum': 'SUM({column}) OVER (ORDER BY {date_column} ROWS UNBOUNDED PRECEDING)',[m
[32m+[m[32m        'rank': 'RANK() OVER (ORDER BY {column} DESC)',[m
[32m+[m[32m        'dense_rank': 'DENSE_RANK() OVER (ORDER BY {column} DESC)',[m
[32m+[m[32m        'row_number': 'ROW_NUMBER() OVER (ORDER BY {column} DESC)'[m
[32m+[m[32m    },[m
[32m+[m[32m    'performance_ranking': {[m
[32m+[m[32m        'employee_performance_rank': 'RANK() OVER (ORDER BY performance_rating DESC)',[m
[32m+[m[32m        'salary_rank': 'RANK() OVER (ORDER BY salary DESC)',[m
[32m+[m[32m        'department_rank': 'RANK() OVER (PARTITION BY department ORDER BY performance_rating DESC)',[m
[32m+[m[32m        'overall_employee_score': 'RANK() OVER (ORDER BY (performance_rating * 0.7 + (salary/1000) * 0.3) DESC)',[m
[32m+[m[32m        'percentile_rank': 'PERCENT_RANK() OVER (ORDER BY performance_rating)',[m
[32m+[m[32m        'ntile_quartile': 'NTILE(4) OVER (ORDER BY performance_rating DESC)',[m
[32m+[m[32m        'top_performer': 'CASE WHEN RANK() OVER (ORDER BY performance_rating DESC) <= 3 THEN "Top Performer" ELSE "Standard" END'[m
[32m+[m[32m    },[m
[32m+[m[32m    'interview_ranking': {[m
[32m+[m[32m        'technical_rank': 'RANK() OVER (ORDER BY technical_score DESC)',[m
[32m+[m[32m        'communication_rank': 'RANK() OVER (ORDER BY communication_score DESC)',[m
[32m+[m[32m        'overall_interview_rank': 'RANK() OVER (ORDER BY overall_score DESC)',[m
[32m+[m[32m        'combined_score': '(technical_score * 0.4 + communication_score * 0.3 + overall_score * 0.3)',[m
[32m+[m[32m        'hire_recommendation': 'CASE WHEN overall_score >= 4.0 THEN "Strongly Recommend" WHEN overall_score >= 3.5 THEN "Recommend" WHEN overall_score >= 3.0 THEN "Consider" ELSE "Not Recommended" END',[m
[32m+[m[32m        'top_candidates': 'CASE WHEN RANK() OVER (ORDER BY overall_score DESC) <= 5 THEN "Top 5 Candidate" ELSE "Standard" END'[m
[32m+[m[32m    },[m
[32m+[m[32m    'hiring_metrics': {[m
[32m+[m[32m        'best_candidate_score': '(technical_score * 0.4 + communication_score * 0.3 + overall_score * 0.3)',[m
[32m+[m[32m        'position_competition': 'COUNT(*) OVER (PARTITION BY position_applied)',[m
[32m+[m[32m        'success_rate_by_position': 'AVG(CASE WHEN outcome = "hired" THEN 1 ELSE 0 END) OVER (PARTITION BY position_applied)'[m
[32m+[m[32m    },[m
[32m+[m[32m    'financial': {[m
[32m+[m[32m        'profit_margin': '(revenue - cost) / revenue * 100',[m
[32m+[m[32m        'roi': '(gain - investment) / investment * 100',[m
[32m+[m[32m        'compound_growth': 'POWER((ending_value / beginning_value), (1.0 / years)) - 1'[m
[32m+[m[32m    }[m
[32m+[m[32m}[m
[32m+[m
[32m+[m[32m# Database schema information - Smart table selection based on query[m
[32m+[m[32malltable_describe = {[m
[32m+[m[32m    'orders': [[m
[32m+[m[32m        {'Field': 'order_id', 'Type': 'int(11)', 'Null': 'NO', 'Key': 'PRI', 'Default': None, 'Extra': 'auto_increment', 'Comment': 'Unique identifier for each order'},[m
[32m+[m[32m        {'Field': 'user_id', 'Type': 'int(11)', 'Null': 'NO', 'Key': 'MUL', 'Default': None, 'Extra': '', 'Comment': 'Foreign key referencing the customer who placed the order'},[m
[32m+[m[32m        {'Field': 'product_id', 'Type': 'int(11)', 'Null': 'NO', 'Key': 'MUL', 'Default': None, 'Extra': '', 'Comment': 'Foreign key referencing the product that was ordered'},[m
[32m+[m[32m        {'Field': 'quantity', 'Type': 'int(11)', 'Null': 'NO', 'Key': '', 'Default': None, 'Extra': '', 'Comment': 'Number of units of the product ordered'},[m
[32m+[m[32m        {'Field': 'total_amount', 'Type': 'decimal(10,2)', 'Null': 'NO', 'Key': '', 'Default': None, 'Extra': '', 'Comment': 'Total monetary value of the order including price * quantity'},[m
[32m+[m[32m        {'Field': 'order_date', 'Type': 'timestamp', 'Null': 'NO', 'Key': '', 'Default': 'CURRENT_TIMESTAMP', 'Extra': '', 'Comment': 'Date and time when the order was placed'},[m
[32m+[m[32m        {'Field': 'status', 'Type': "enum('pending','processing','shipped','delivered','cancelled')", 'Null': 'YES', 'Key': '', 'Default': 'pending', 'Extra': '', 'Comment': 'Current status of the order in the fulfillment process'}[m
[32m+[m[32m    ],[m
[32m+[m[32m    'products': [[m
[32m+[m[32m        {'Field': 'product_id', 'Type': 'int(11)', 'Null': 'NO', 'Key': 'PRI', 'Default': None, 'Extra': 'auto_increment', 'Comment': 'Unique identifier for each product'},[m
[32m+[m[32m        {'Field': 'product_name', 'Type': 'varchar(100)', 'Null': 'NO', 'Key': '', 'Default': None, 'Extra': '', 'Comment': 'Name or title of the product'},[m
[32m+[m[32m        {'Field': 'category', 'Type': 'varchar(50)', 'Null': 'NO', 'Key': '', 'Default': None, 'Extra': '', 'Comment': 'Product category classification (e.g., Electronics, Accessories)'},[m
[32m+[m[32m        {'Field': 'price', 'Type': 'decimal(10,2)', 'Null': 'NO', 'Key': '', 'Default': None, 'Extra': '', 'Comment': 'Unit price of the product in currency'},[m
[32m+[m[32m        {'Field': 'stock_quantity', 'Type': 'int(11)', 'Null': 'NO', 'Key': '', 'Default': None, 'Extra': '', 'Comment': 'Current available inventory count for this product'},[m
[32m+[m[32m        {'Field': 'created_date', 'Type': 'timestamp', 'Null': 'NO', 'Key': '', 'Default': 'CURRENT_TIMESTAMP', 'Extra': '', 'Comment': 'Date and time when the product was added to the catalog'}[m
[32m+[m[32m    ],[m
[32m+[m[32m    'users': [[m
[32m+[m[32m        {'Field': 'user_id', 'Type': 'int(11)', 'Null': 'NO', 'Key': 'PRI', 'Default': None, 'Extra': 'auto_increment', 'Comment': 'Unique identifier for each user/customer'},[m
[32m+[m[32m        {'Field': 'first_name', 'Type': 'varchar(50)', 'Null': 'NO', 'Key': '', 'Default': None, 'Extra': '', 'Comment': 'User\'s first name'},[m
[32m+[m[32m        {'Field': 'last_name', 'Type': 'varchar(50)', 'Null': 'NO', 'Key': '', 'Default': None, 'Extra': '', 'Comment': 'User\'s last name'},[m
[32m+[m[32m        {'Field': 'email', 'Type': 'varchar(100)', 'Null': 'NO', 'Key': 'UNI', 'Default': None, 'Extra': '', 'Comment': 'User\'s unique email address for login and communication'},[m
[32m+[m[32m        {'Field': 'phone', 'Type': 'varchar(15)', 'Null': 'YES', 'Key': '', 'Default': None, 'Extra': '', 'Comment': 'User\'s contact phone number'},[m
[32m+[m[32m        {'Field': 'address', 'Type': 'text', 'Null': 'YES', 'Key': '', 'Default': None, 'Extra': '', 'Comment': 'User\'s physical address for shipping and billing'},[m
[32m+[m[32m        {'Field': 'registration_date', 'Type': 'timestamp', 'Null': 'NO', 'Key': '', 'Default': 'CURRENT_TIMESTAMP', 'Extra': '', 'Comment': 'Date and time when the user registered on the platform'}[m
[32m+[m[32m    ],[m
[32m+[m[32m    'employees': [[m
[32m+[m[32m        {'Field': 'emp_id', 'Type': 'int(11)', 'Null': 'NO', 'Key': 'PRI', 'Default': None, 'Extra': 'auto_increment', 'Comment': 'Unique identifier for each employee'},[m
[32m+[m[32m        {'Field': 'first_name', 'Type': 'varchar(50)', 'Null': 'NO', 'Key': '', 'Default': None, 'Extra': '', 'Comment': 'Employee\'s first name'},[m
[32m+[m[32m        {'Field': 'last_name', 'Type': 'varchar(50)', 'Null': 'NO', 'Key': '', 'Default': None, 'Extra': '', 'Comment': 'Employee\'s last name'},[m
[32m+[m[32m        {'Field': 'email', 'Type': 'varchar(100)', 'Null': 'NO', 'Key': 'UNI', 'Default': None, 'Extra': '', 'Comment': 'Employee\'s unique email address for work communication'},[m
[32m+[m[32m        {'Field': 'department', 'Type': 'varchar(50)', 'Null': 'NO', 'Key': '', 'Default': None, 'Extra': '', 'Comment': 'Department where the employee works (e.g., Sales, Marketing, HR, IT)'},[m
[32m+[m[32m        {'Field': 'position', 'Type': 'varchar(50)', 'Null': 'NO', 'Key': '', 'Default': None, 'Extra': '', 'Comment': 'Employee\'s job title or position within the department'},[m
[32m+[m[32m        {'Field': 'salary', 'Type': 'decimal(10,2)', 'Null': 'NO', 'Key': '', 'Default': None, 'Extra': '', 'Comment': 'Employee\'s annual salary in currency'},[m
[32m+[m[32m        {'Field': 'performance_rating', 'Type': 'decimal(3,2)', 'Null': 'YES', 'Key': '', 'Default': None, 'Extra': '', 'Comment': 'Employee performance rating on a scale of 1-5 where 5 is excellent'},[m
[32m+[m[32m        {'Field': 'status', 'Type': "enum('active','inactive','terminated','on_leave')", 'Null': 'YES', 'Key': '', 'Default': 'active', 'Extra': '', 'Comment': 'Current employment status of the employee'}[m
[32m+[m[32m    ],[m
[32m+[m[32m    'interviews': [[m
[32m+[m[32m    {'Field': 'interview_id', 'Type': 'int(11)', 'Null': 'NO', 'Key': 'PRI', 'Default': None, 'Extra': 'auto_increment', 'Comment': 'Unique identifier for each interview session'},[m
[32m+[m[32m    {'Field': 'candidate_name', 'Type': 'varchar(100)', 'Null': 'NO', 'Key': '', 'Default': None, 'Extra': '', 'Comment': 'Full name of the candidate being interviewed'},[m
[32m+[m[32m    {'Field': 'email', 'Type': 'varchar(100)', 'Null': 'YES', 'Key': '', 'Default': None, 'Extra': '', 'Comment': 'Candidate\'s email address for communication'},[m
[32m+[m[32m    {'Field': 'phone', 'Type': 'varchar(15)', 'Null': 'YES', 'Key': '', 'Default': None, 'Extra': '', 'Comment': 'Candidate\'s contact phone number'},[m
[32m+[m[32m    {'Field': 'position_applied', 'Type': 'varchar(50)', 'Null': 'NO', 'Key': '', 'Default': None, 'Extra': '', 'Comment': 'Job position the candidate applied for'},[m
[32m+[m[32m    {'Field': 'department', 'Type': 'varchar(50)', 'Null': 'YES', 'Key': '', 'Default': None, 'Extra': '', 'Comment': 'Department where the position is located'},[m
[32m+[m[32m    {'Field': 'interview_date', 'Type': 'date', 'Null': 'YES', 'Key': '', 'Default': None, 'Extra': '', 'Comment': 'Date when the interview was conducted'},[m
[32m+[m[32m    {'Field': 'interview_time', 'Type': 'time', 'Null': 'YES', 'Key': '', 'Default': None, 'Extra': '', 'Comment': 'Time when the interview was conducted'},[m
[32m+[m[32m    {'Field': 'interviewer_id', 'Type': 'int(11)', 'Null': 'YES', 'Key': '', 'Default': None, 'Extra': '', 'Comment': 'ID of the employee who conducted the interview'},[m
[32m+[m[32m    {'Field': 'interview_type', 'Type': "enum('online','offline','telephonic')", 'Null': 'YES', 'Key': '', 'Default': 'offline', 'Extra': '', 'Comment': 'Type of interview conducted (online, offline, or telephonic)'},[m
[32m+[m[32m    {'Field': 'interview_round', 'Type': 'int(2)', 'Null': 'YES', 'Key': '', 'Default': 1, 'Extra': '', 'Comment': 'Round number of the interview process (1st round, 2nd round, etc.)'},[m
[32m+[m[32m    {'Field': 'technical_score', 'Type': 'decimal(3,2)', 'Null': 'YES', 'Key': '', 'Default': None, 'Extra': '', 'Comment': 'Technical skills score on a scale of 1-5'},[m
[32m+[m[32m    {'Field': 'communication_score', 'Type': 'decimal(3,2)', 'Null': 'YES', 'Key': '', 'Default': None, 'Extra': '', 'Comment': 'Communication skills score on a scale of 1-5'},[m
[32m+[m[32m    {'Field': 'cultural_fit_score', 'Type': 'decimal(3,2)', 'Null': 'YES', 'Key': '', 'Default': None, 'Extra': '', 'Comment': 'Cultural fit assessment score on a scale of 1-5'},[m
[32m+[m[32m    {'Field': 'overall_score', 'Type': 'decimal(3,2)', 'Null': 'YES', 'Key': '', 'Default': None, 'Extra': '', 'Comment': 'Overall interview score calculated from all assessment areas'},[m
[32m+[m[32m    {'Field': 'interview_notes', 'Type': 'text', 'Null': 'YES', 'Key': '', 'Default': None, 'Extra': '', 'Comment': 'Detailed notes and observations from the interview'},[m
[32m+[m[32m    {'Field': 'outcome', 'Type': "enum('pass','fail','pending','hold','hired')", 'Null': 'YES', 'Key': '', 'Default': 'pending', 'Extra': '', 'Comment': 'Final outcome or decision of the interview process'},[m
[32m+[m[32m    {'Field': 'salary_expectation', 'Type': 'decimal(10,2)', 'Null': 'YES', 'Key': '', 'Default': None, 'Extra': '', 'Comment': 'Candidate\'s expected salary in currency'},[m
[32m+[m[32m    {'Field': 'years_experience', 'Type': 'decimal(3,1)', 'Null': 'YES', 'Key': '', 'Default': None, 'Extra': '', 'Comment': 'Number of years of relevant work experience'},[m
[32m+[m[32m    {'Field': 'created_date', 'Type': 'datetime', 'Null': 'YES', 'Key': '', 'Default': None, 'Extra': '', 'Comment': 'Date and time when the interview record was created'},[m
[32m+[m[32m    {'Field': 'updated_date', 'Type': 'datetime', 'Null': 'YES', 'Key': '', 'Default': None, 'Extra': '', 'Comment': 'Date and time when the interview record was last updated'}[m
[32m+[m[32m][m
[32m+[m
[32m+[m[32m}[m
[32m+[m[32malltable_demo_data = {[m
[32m+[m[32m    'orders': [[m
[32m+[m[32m        {'order_id': 1, 'user_id': 101, 'product_id': 201, 'quantity': 2, 'total_amount': 499.98, 'order_date': '2025-08-01 10:00:00', 'status': 'processing'},[m
[32m+[m[32m        {'order_id': 2, 'user_id': 102, 'product_id': 202, 'quantity': 1, 'total_amount': 249.99, 'order_date': '2025-08-02 14:20:00', 'status': 'shipped'},[m
[32m+[m[32m        {'order_id': 3, 'user_id': 103, 'product_id': 203, 'quantity': 3, 'total_amount': 899.97, 'order_date': '2025-08-03 16:45:00', 'status': 'delivered'},[m
[32m+[m[32m        {'order_id': 4, 'user_id': 104, 'product_id': 204, 'quantity': 1, 'total_amount': 299.99, 'order_date': '2025-08-04 12:10:00', 'status': 'cancelled'},[m
[32m+[m[32m        {'order_id': 5, 'user_id': 105, 'product_id': 205, 'quantity': 4, 'total_amount': 1199.96, 'order_date': '2025-08-05 09:30:00', 'status': 'pending'},[m
[32m+[m[32m    ],[m
[32m+[m[32m    'products': [[m
[32m+[m[32m        {'product_id': 201, 'product_name': 'Wireless Mouse', 'category': 'Electronics', 'price': 249.99, 'stock_quantity': 50, 'created_date': '2025-07-01 10:00:00'},[m
[32m+[m[32m        {'product_id': 202, 'product_name': 'Bluetooth Headphones', 'category': 'Electronics', 'price': 249.99, 'stock_quantity': 30, 'created_date': '2025-07-02 10:00:00'},[m
[32m+[m[32m        {'product_id': 203, 'product_name': 'Gaming Keyboard', 'category': 'Electronics', 'price': 299.99, 'stock_quantity': 20, 'created_date': '2025-07-03 10:00:00'},[m
[32m+[m[32m        {'product_id': 204, 'product_name': 'Smart Watch', 'category': 'Wearables', 'price': 299.99, 'stock_quantity': 15, 'created_date': '2025-07-04 10:00:00'},[m
[32m+[m[32m        {'product_id': 205, 'product_name': 'USB-C Hub', 'category': 'Accessories', 'price': 299.99, 'stock_quantity': 40, 'created_date': '2025-07-05 10:00:00'},[m
[32m+[m[32m    ],[m
[32m+[m[32m    'users': [[m
[32m+[m[32m        {'user_id': 101, 'first_name': 'Alice', 'last_name': 'Johnson', 'email': 'alice@example.com', 'phone': '9876543210', 'address': '123 Elm St', 'registration_date': '2025-06-01 08:30:00'},[m
[32m+[m[32m        {'user_id': 102, 'first_name': 'Bob', 'last_name': 'Smith', 'email': 'bob@example.com', 'phone': '9876543211', 'address': '456 Oak St', 'registration_date': '2025-06-02 09:00:00'},[m
[32m+[m[32m        {'user_id': 103, 'first_name': 'Carol', 'last_name': 'Williams', 'email': 'carol@example.com', 'phone': '9876543212', 'address': '789 Pine St', 'registration_date': '2025-06-03 10:00:00'},[m
[32m+[m[32m        {'user_id': 104, 'first_name': 'David', 'last_name': 'Taylor', 'email': 'david@example.com', 'phone': '9876543213', 'address': '101 Maple St', 'registration_date': '2025-06-04 11:00:00'},[m
[32m+[m[32m        {'user_id': 105, 'first_name': 'Eve', 'last_name': 'Brown', 'email': 'eve@example.com', 'phone': '9876543214', 'address': '202 Cedar St', 'registration_date': '2025-06-05 12:00:00'},[m
[32m+[m[32m    ],[m
[32m+[m[32m    'employees': [[m
[32m+[m[32m        {'emp_id': 301, 'first_name': 'John', 'last_name': 'Doe', 'email': 'john.doe@example.com', 'department': 'Sales', 'position': 'Manager', 'salary': 70000.00, 'performance_rating': 4.5, 'status': 'active'},[m
[32m+[m[32m        {'emp_id': 302, 'first_name': 'Jane', 'last_name': 'Smith', 'email': 'jane.smith@example.com', 'department': 'Marketing', 'position': 'Executive', 'salary': 55000.00, 'performance_rating': 4.2, 'status': 'active'},[m
[32m+[m[32m        {'emp_id': 303, 'first_name': 'Mike', 'last_name': 'Brown', 'email': 'mike.brown@example.com', 'department': 'HR', 'position': 'Coordinator', 'salary': 48000.00, 'performance_rating': 3.9, 'status': 'on_leave'},[m
[32m+[m[32m        {'emp_id': 304, 'first_name': 'Sara', 'last_name': 'Lee', 'email': 'sara.lee@example.com', 'department': 'Finance', 'position': 'Analyst', 'salary': 60000.00, 'performance_rating': 4.7, 'status': 'active'},[m
[32m+[m[32m        {'emp_id': 305, 'first_name': 'Tom', 'last_name': 'Wilson', 'email': 'tom.wilson@example.com', 'department': 'IT', 'position': 'Engineer', 'salary': 65000.00, 'performance_rating': 4.3, 'status': 'inactive'},[m
[32m+[m[32m    ],[m
[32m+[m[32m    'interviews': [[m
[32m+[m[32m    {[m
[32m+[m[32m        'interview_id': 401,[m
[32m+[m[32m        'candidate_name': 'Alex Green',[m
[32m+[m[32m        'email': 'alex.green@example.com',[m
[32m+[m[32m        'phone': '9876543210',[m
[32m+[m[32m        'position_applied': 'Software Developer',[m
[32m+[m[32m        'department': 'Engineering',[m
[32m+[m[32m        'interview_date': '2025-08-05',[m
[32m+[m[32m        'interview_time': '10:00:00',[m
[32m+[m[32m        'interviewer_id': 201,[m
[32m+[m[32m        'interview_type': 'online',[m
[32m+[m[32m        'interview_round': 2,[m
[32m+[m[32m        'technical_score': 4.5,[m
[32m+[m[32m        'communication_score': 4.0,[m
[32m+[m[32m        'cultural_fit_score': 4.4,[m
[32m+[m[32m        'overall_score': 4.3,[m
[32m+[m[32m        'interview_notes': 'Strong in backend, good coding test performance.',[m
[32m+[m[32m        'outcome': 'hired',[m
[32m+[m[32m        'salary_expectation': 90000.00,[m
[32m+[m[32m        'years_experience': 4.5,[m
[32m+[m[32m        'created_date': '2025-08-01 12:00:00',[m
[32m+[m[32m        'updated_date': '2025-08-05 17:00:00'[m
[32m+[m[32m    },[m
[32m+[m[32m    {[m
[32m+[m[32m        'interview_id': 402,[m
[32m+[m[32m        'candidate_name': 'Lily Adams',[m
[32m+[m[32m        'email': 'lily.adams@example.com',[m
[32m+[m[32m        'phone': '9123456780',[m
[32m+[m[32m        'position_applied': 'QA Engineer',[m
[32m+[m[32m        'department': 'Quality Assurance',[m
[32m+[m[32m        'interview_date': '2025-08-04',[m
[32m+[m[32m        'interview_time': '11:30:00',[m
[32m+[m[32m        'interviewer_id': 202,[m
[32m+[m[32m        'interview_type': 'offline',[m
[32m+[m[32m        'interview_round': 1,[m
[32m+[m[32m        'technical_score': 3.9,[m
[32m+[m[32m        'communication_score': 4.2,[m
[32m+[m[32m        'cultural_fit_score': 4.1,[m
[32m+[m[32m        'overall_score': 4.0,[m
[32m+[m[32m        'interview_notes': 'Good analytical skills.',[m
[32m+[m[32m        'outcome': 'pass',[m
[32m+[m[32m        'salary_expectation': 70000.00,[m
[32m+[m[32m        'years_experience': 3.0,[m
[32m+[m[32m        'created_date': '2025-08-01 14:00:00',[m
[32m+[m[32m        'updated_date': '2025-08-04 16:00:00'[m
[32m+[m[32m    },[m
[32m+[m[32m    {[m
[32m+[m[32m        'interview_id': 403,[m
[32m+[m[32m        'candidate_name': 'James White',[m
[32m+[m[32m        'email': 'james.white@example.com',[m
[32m+[m[32m        'phone': '9012345678',[m
[32m+[m[32m        'position_applied': 'Project Manager',[m
[32m+[m[32m        'department': 'Management',[m
[32m+[m[32m        'interview_date': '2025-08-03',[m
[32m+[m[32m        'interview_time': '09:00:00',[m
[32m+[m[32m        'interviewer_id': 203,[m
[32m+[m[32m        'interview_type': 'telephonic',[m
[32m+[m[32m        'interview_round': 1,[m
[32m+[m[32m        'technical_score': 4.2,[m
[32m+[m[32m        'communication_score': 3.8,[m
[32m+[m[32m        'cultural_fit_score': 3.9,[m
[32m+[m[32m        'overall_score': 4.0,[m
[32m+[m[32m        'interview_notes': 'Needs improvement in delivery estimation.',[m
[32m+[m[32m        'outcome': 'hold',[m
[32m+[m[32m        'salary_expectation': 120000.00,[m
[32m+[m[32m        'years_experience': 6.0,[m
[32m+[m[32m        'created_date': '2025-07-30 09:00:00',[m
[32m+[m[32m        'updated_date': '2025-08-03 15:00:00'[m
[32m+[m[32m    },[m
[32m+[m[32m    {[m
[32m+[m[32m        'interview_id': 404,[m
[32m+[m[32m        'candidate_name': 'Emma Black',[m
[32m+[m[32m        'email': 'emma.black@example.com',[m
[32m+[m[32m        'phone': '9988776655',[m
[32m+[m[32m        'position_applied': 'UI/UX Designer',[m
[32m+[m[32m        'department': 'Design',[m
[32m+[m[32m        'interview_date': '2025-08-02',[m
[32m+[m[32m        'interview_time': '14:00:00',[m
[32m+[m[32m        'interviewer_id': 204,[m
[32m+[m[32m        'interview_type': 'offline',[m
[32m+[m[32m        'interview_round': 2,[m
[32m+[m[32m        'technical_score': 4.0,[m
[32m+[m[32m        'communication_score': 4.5,[m
[32m+[m[32m        'cultural_fit_score': 4.3,[m
[32m+[m[32m        'overall_score': 4.3,[m
[32m+[m[32m        'interview_notes': 'Creative portfolio, good teamwork skills.',[m
[32m+[m[32m        'outcome': 'pass',[m
[32m+[m[32m        'salary_expectation': 85000.00,[m
[32m+[m[32m        'years_experience': 4.0,[m
[32m+[m[32m        'created_date': '2025-07-29 10:30:00',[m
[32m+[m[32m        'updated_date': '2025-08-02 16:00:00'[m
[32m+[m[32m    },[m
[32m+[m[32m    {[m
[32m+[m[32m        'interview_id': 405,[m
[32m+[m[32m        'candidate_name': 'Oliver Gray',[m
[32m+[m[32m        'email': 'oliver.gray@example.com',[m
[32m+[m[32m        'phone': '9876501234',[m
[32m+[m[32m        'position_applied': 'DevOps Engineer',[m
[32m+[m[32m        'department': 'IT Operations',[m
[32m+[m[32m        'interview_date': '2025-08-01',[m
[32m+[m[32m        'interview_time': '16:00:00',[m
[32m+[m[32m        'interviewer_id': 205,[m
[32m+[m[32m        'interview_type': 'online',[m
[32m+[m[32m        'interview_round': 1,[m
[32m+[m[32m        'technical_score': 3.5,[m
[32m+[m[32m        'communication_score': 3.6,[m
[32m+[m[32m        'cultural_fit_score': 3.2,[m
[32m+[m[32m        'overall_score': 3.55,[m
[32m+[m[32m        'interview_notes': 'Average CI/CD knowledge. Needs more experience.',[m
[32m+[m[32m        'outcome': 'fail',[m
[32m+[m[32m        'salary_expectation': 75000.00,[m
[32m+[m[32m        'years_experience': 2.0,[m
[32m+[m[32m        'created_date': '2025-07-28 11:15:00',[m
[32m+[m[32m        'updated_date': '2025-08-01 17:45:00'[m
[32m+[m[32m    }[m
[32m+[m[32m][m
[32m+[m
[32m+[m[32m}[m
[32m+[m
[32m+[m[32m# Smart table selection based on query keywords[m
[32m+[m[32mTABLE_KEYWORDS = {[m
[32m+[m[32m    'users': ['user', 'customer', 'client', 'buyer', 'person', 'people'],[m
[32m+[m[32m    'products': ['product', 'item', 'goods', 'merchandise', 'inventory'],[m
[32m+[m[32m    'orders': ['order', 'purchase', 'transaction', 'sale', 'buy'],[m
[32m+[m[32m    'employees': ['employee', 'staff', 'worker', 'hire', 'hiring', 'performance', 'best performer', 'emp', 'rating'],[m
[32m+[m[32m    'interviews': ['interview', 'candidate', 'hiring', 'recruit', 'selection', 'technical score', 'communication', 'overall score'][m
[32m+[m[32m}[m
[32m+[m
[32m+[m[32mDB_CONFIG = {[m
[32m+[m[32m    'host': 'localhost',[m
[32m+[m[32m    'user': 'root',[m
[32m+[m[32m    'passwo
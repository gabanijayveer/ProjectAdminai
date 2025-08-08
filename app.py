# from flask import Flask, render_template, request, jsonify, session, redirect
# import os
# import json
# import mysql.connector
# from datetime import datetime
# import uuid
# import threading
# import io
# import sys
# from contextlib import redirect_stdout, redirect_stderr
# from config import DB_CONFIG, FLASK_CONFIG, validate_db_config
# from Proceduremanager import run_sql_procedure_agent, MATH_FORMULAS

# app = Flask(__name__)
# app.secret_key = FLASK_CONFIG['SECRET_KEY']

# # Validate database configuration on startup
# validate_db_config()

# # Default session configuration for chat history management
# DEFAULT_SESSION_ID = "114"
# DEFAULT_TOKEN = "123456"
# current_session = {
#     'session_id': DEFAULT_SESSION_ID,
#     'token': DEFAULT_TOKEN,
#     'chat_history': []
# }

# # AI Chat processor using your Proceduremanager.py
# def is_greeting_or_simple_query(query):
#     """Check if query is a greeting or simple conversation that doesn't need SQL processing."""
#     greeting_patterns = [
#         'hi', 'hello', 'hey', 'hy', 'hii', 'helo',
#         'how are you', 'how r u', 'whats up', 'what\'s up',
#         'good morning', 'good afternoon', 'good evening',
#         'thanks', 'thank you', 'bye', 'goodbye', 'see you',
#         'ok', 'okay', 'yes', 'no', 'sure', 'fine'
#     ]

#     query_lower = query.lower().strip()

#     # Check for exact matches or simple greetings
#     if query_lower in greeting_patterns:
#         return True

#     # Check for greeting-like patterns (short queries with greeting words)
#     if len(query_lower) <= 20:  # Short queries
#         for pattern in greeting_patterns:
#             if pattern in query_lower:
#                 return True

#     return False

# def needs_context(query):
#     """Determine if query needs previous conversation context."""
#     context_keywords = [
#         'previous', 'before', 'earlier', 'last time', 'again',
#         'same', 'similar', 'like before', 'as we discussed',
#         'continue', 'more', 'also', 'additionally', 'further',
#         'update', 'modify', 'change', 'compare', 'difference'
#     ]

#     query_lower = query.lower()

#     # Check if query explicitly references previous conversation
#     for keyword in context_keywords:
#         if keyword in query_lower:
#             return True

#     # If it's a greeting or simple query, no context needed
#     if is_greeting_or_simple_query(query):
#         return False

#     # For complex data queries, use minimal context only if recent history exists
#     return False  # Default to no context unless explicitly needed

# def handle_greeting(query):
#     """Handle greeting messages without running SQL procedures."""
#     greeting_responses = {
#         'hi': "Hello! I'm your AI data assistant. I can help you analyze your data, run SQL queries, and provide insights. What would you like to explore today?",
#         'hello': "Hi there! I'm ready to help you with data analysis and SQL queries. What can I assist you with?",
#         'hey': "Hey! I'm your data assistant. Ask me anything about your database or data analysis needs.",
#         'hy': "Hi! I'm here to help with your data queries and analysis. What would you like to know?",
#         'how are you': "I'm doing great and ready to help with your data analysis! What database queries or insights do you need today?",
#         'thanks': "You're welcome! Feel free to ask me anything about your data or if you need help with SQL queries.",
#         'thank you': "You're very welcome! I'm here whenever you need data analysis or database assistance.",
#         'good morning': "Good morning! Ready to dive into some data analysis today? What can I help you with?",
#         'good afternoon': "Good afternoon! I'm here to assist with your data queries and analysis needs.",
#         'good evening': "Good evening! How can I help you with your data today?"
#     }

#     query_lower = query.lower().strip()

#     # Try exact match first
#     if query_lower in greeting_responses:
#         return greeting_responses[query_lower]

#     # Try partial matches for variations
#     for greeting, response in greeting_responses.items():
#         if greeting in query_lower:
#             return response

#     # Default friendly response
#     return "Hello! I'm your AI data assistant. I can help you analyze data, run SQL queries, and provide insights. What would you like to explore?"

# def process_user_query(user_query, session_id=None, token=None):
#     """Process user query using the actual Proceduremanager.py backend with smart context usage."""
#     try:
#         # Use default session if not provided
#         if not session_id:
#             session_id = DEFAULT_SESSION_ID
#         if not token:
#             token = DEFAULT_TOKEN

#         # Handle greetings without running procedures
#         if is_greeting_or_simple_query(user_query):
#             greeting_response = handle_greeting(user_query)

#             # Add to session history with high quality score
#             add_to_session_history(session_id, token, user_query, [greeting_response], 95)

#             return {
#                 'success': True,
#                 'results': [greeting_response],
#                 'summary': "Greeting handled successfully",
#                 'quality_score': 95,
#                 'raw_output': greeting_response
#             }

#         # Smart context usage - only get context if needed
#         enhanced_query = user_query
#         if needs_context(user_query):
#             context = get_context_from_history(session_id, token, limit=2)
#             if context:
#                 enhanced_query = f"Context from previous conversation:\n{context}\n\nCurrent Query: {user_query}"

#         # Capture raw output from your Proceduremanager
#         stdout_capture = io.StringIO()
#         stderr_capture = io.StringIO()

#         with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
#             # Run your actual Proceduremanager function with enhanced query
#             run_sql_procedure_agent(enhanced_query)

#         # Get the raw output
#         raw_output = stdout_capture.getvalue()
#         error_output = stderr_capture.getvalue()

#         if raw_output:
#             # Extract only the EXECUTION RESULTS section
#             execution_results = extract_execution_results(raw_output)

#             # Debug: Let's see what we extracted
#             print(f"DEBUG: Extracted {len(execution_results)} result lines:")
#             for i, result in enumerate(execution_results[:5]):  # Show first 5 lines
#                 print(f"  {i+1}: {result}")

#             if execution_results and len(execution_results) > 0:
#                 # Filter out the "No execution results found" message if we have real data
#                 if execution_results[0] != "No execution results found in the output. The query may have completed without returning data.":
#                     result = {
#                         'success': True,
#                         'results': execution_results,
#                         'summary': f"Query executed successfully - {len(execution_results)} result lines",
#                         'quality_score': 90,
#                         'raw_output': raw_output
#                     }

#                     # Add to session history
#                     add_to_session_history(session_id, token, user_query, execution_results, 90)

#                     return result

#             # If no meaningful results found, show a simple message
#             return {
#                 'success': True,
#                 'results': ["The query executed successfully but no data results were returned to display."],
#                 'summary': "Query completed - no display data available",
#                 'quality_score': 75,
#                 'raw_output': raw_output
#             }
#         else:
#             return {
#                 'success': False,
#                 'results': [f"No output captured from Proceduremanager.py"],
#                 'summary': "No output received",
#                 'quality_score': 0,
#                 'error': error_output if error_output else 'No output or error captured'
#             }

#     except Exception as e:
#         return {
#             'success': False,
#             'results': [f"❌ Error processing query: {str(e)}"],
#             'summary': "System error occurred",
#             'quality_score': 0,
#             'error': str(e)
#         }

# def extract_execution_results(raw_output):
#     """Extract from Description or DATA TABLES to the end - no SQL content."""
#     lines = raw_output.split('\n')

#     execution_results = []
#     found_start = False

#     # Look for "Description" or "DATA TABLES" sections
#     for line in lines:
#         line_stripped = line.strip()

#         # Check if we found the start of meaningful content
#         if (line_stripped.startswith('Description:') or
#             line_stripped == 'DATA TABLES' or
#             line_stripped.startswith('• • Key Metrics:') or
#             (line_stripped.startswith('###') and not any(sql_word in line_stripped.upper() for sql_word in ['CREATE', 'SELECT', 'PROCEDURE']))):
#             found_start = True
#             execution_results.append(line_stripped)
#             continue

#         # If we found the start, capture everything after it (excluding SQL)
#         if found_start:
#             # Skip empty lines and separator lines
#             if not line_stripped or line_stripped.startswith('=') or line_stripped.startswith('-'):
#                 continue

#             # Skip all SQL-related content
#             if any(sql_word in line_stripped.upper() for sql_word in [
#                 'CREATE PROCEDURE', 'DECLARE', 'BEGIN', 'END;', 'SELECT', 'FROM', 'WHERE',
#                 'GROUP BY', 'ORDER BY', 'LIMIT', 'INSERT', 'UPDATE', 'DELETE', 'ALTER TABLE',
#                 'DROP', 'CALL', 'SET @', 'IF', 'ELSE', 'WHILE', 'LOOP', 'CURSOR', 'DELIMITER',
#                 'COMMIT', 'ROLLBACK', 'TRANSACTION', 'INDEX', 'PRIMARY KEY', 'FOREIGN KEY'
#             ]):
#                 continue

#             # Skip technical/debug lines
#             if any(skip_word in line_stripped for skip_word in [
#                 'Generated Procedure:', 'Connected to MySQL', 'Dataset Analysis:',
#                 'Using standard processing', 'All required tables found',
#                 'Dropped existing procedure', 'Extracted procedure code:',
#                 'Successfully created procedure', 'Procedure verified', 'Procedure executed',
#                 'Report Generated at:', 'Cleaned up', 'Database connection closed',
#                 'STEP', 'PROCEDURE EXPLANATION', 'Generated SQL Procedure:',
#                 'EXECUTION RESULTS', 'EXECUTION COMPLETED'
#             ]):
#                 continue

#             # Add the line to results
#             execution_results.append(line_stripped)

#     # If no Description or DATA TABLES found, look for table data directly
#     if not execution_results:
#         for line in lines:
#             line_stripped = line.strip()

#             # Look for table headers or meaningful data
#             if (' | ' in line_stripped and
#                 any(header_word in line_stripped for header_word in ['ID', 'Name', 'Email', 'Date', 'Amount', 'Status'])):
#                 found_start = True
#                 execution_results.append(line_stripped)
#                 continue

#             # If we found table data, continue capturing
#             if found_start:
#                 if not line_stripped or line_stripped.startswith('=') or line_stripped.startswith('-'):
#                     continue

#                 # Skip SQL content
#                 if any(sql_word in line_stripped.upper() for sql_word in [
#                     'CREATE', 'SELECT', 'FROM', 'WHERE', 'DECLARE', 'BEGIN', 'END;'
#                 ]):
#                     continue

#                 execution_results.append(line_stripped)

#     return execution_results if execution_results else ["No execution results found in the output."]

# def validate_session(session_id, token):
#     """Validate session ID and token."""
#     return session_id == DEFAULT_SESSION_ID and token == DEFAULT_TOKEN

# def get_session_history(session_id, token, limit=50):
#     """Get chat history for a valid session from database."""
#     if not validate_session(session_id, token):
#         return []

#     try:
#         conn = get_db_connection()
#         cursor = conn.cursor()

#         # Query for session-specific chat history
#         cursor.execute('''
#             SELECT id, timestamp, user_query, execution_results, quality_score, status
#             FROM query_history
#             WHERE session_id = %s AND query_type = 'session_chat'
#             ORDER BY timestamp DESC
#             LIMIT %s
#         ''', (session_id, limit))

#         rows = cursor.fetchall()
#         cursor.close()
#         conn.close()

#         history = []
#         for row in rows:
#             try:
#                 # Parse execution results (AI response)
#                 ai_response = json.loads(row[3]) if row[3] else []

#                 history.append({
#                     'id': row[0],
#                     'timestamp': row[1].isoformat() if row[1] else '',
#                     'user_query': row[2],
#                     'ai_response': ai_response,
#                     'quality_score': row[4] or 0,
#                     'status': row[5],
#                     'session_id': session_id
#                 })
#             except (json.JSONDecodeError, IndexError) as e:
#                 print(f"Error parsing history entry: {e}")
#                 continue

#         # Reverse to show oldest first (chronological order)
#         return list(reversed(history))

#     except Exception as e:
#         print(f"Error retrieving session history: {e}")
#         return current_session['chat_history']  # Fallback to memory

# def add_to_session_history(session_id, token, user_query, ai_response, quality_score=None):
#     """Add a chat interaction to session history in database."""
#     if not validate_session(session_id, token):
#         return False

#     try:
#         # Generate unique ID for this chat entry
#         chat_id = str(uuid.uuid4())
#         timestamp = datetime.now()

#         # Prepare data for database storage
#         query_data = {
#             'id': chat_id,
#             'timestamp': timestamp.isoformat(),
#             'user_query': user_query,
#             'query_type': 'session_chat',
#             'suggested_formulas': [],
#             'procedure_code': f'Session chat - Token: {token}',
#             'execution_results': ai_response if isinstance(ai_response, list) else [str(ai_response)],
#             'quality_score': quality_score or 0,
#             'status': 'completed',
#             'session_id': session_id
#         }

#         # Save to database
#         save_query_history(query_data)

#         # Also keep in memory for quick access
#         chat_entry = {
#             'id': chat_id,
#             'timestamp': timestamp.isoformat(),
#             'user_query': user_query,
#             'ai_response': ai_response,
#             'quality_score': quality_score or 0,
#             'session_id': session_id
#         }

#         current_session['chat_history'].append(chat_entry)

#         # Keep only last 20 entries in memory
#         if len(current_session['chat_history']) > 20:
#             current_session['chat_history'] = current_session['chat_history'][-20:]

#         return True

#     except Exception as e:
#         print(f"Error saving session history: {e}")
#         return False

# def clear_session_history(session_id, token):
#     """Clear chat history for a session from database."""
#     if not validate_session(session_id, token):
#         return False

#     try:
#         conn = get_db_connection()
#         cursor = conn.cursor()

#         # Delete session-specific chat history
#         cursor.execute('''
#             DELETE FROM query_history
#             WHERE session_id = %s AND query_type = 'session_chat'
#         ''', (session_id,))

#         deleted_count = cursor.rowcount
#         conn.commit()
#         cursor.close()
#         conn.close()

#         # Also clear memory
#         current_session['chat_history'] = []

#         print(f"Cleared {deleted_count} chat entries for session {session_id}")
#         return True

#     except Exception as e:
#         print(f"Error clearing session history: {e}")
#         return False

# def get_context_from_history(session_id, token, limit=2):
#     """Get selective chat context for better AI responses - only when needed."""
#     if not validate_session(session_id, token):
#         return ""

#     # Get recent history from database (reduced limit for efficiency)
#     recent_history = get_session_history(session_id, token, limit)

#     if not recent_history:
#         return ""

#     context_parts = []

#     # Only include non-greeting conversations in context
#     for entry in recent_history[-limit:]:
#         user_query = entry['user_query']

#         # Skip greetings and simple responses from context
#         if not is_greeting_or_simple_query(user_query):
#             context_parts.append(f"Previous Query: {user_query}")

#             # Include only relevant parts of response
#             if isinstance(entry['ai_response'], list):
#                 # For list responses, take first meaningful line
#                 meaningful_response = ""
#                 for line in entry['ai_response']:
#                     if line and not line.startswith("Hello") and not line.startswith("Hi"):
#                         meaningful_response = line[:150]
#                         break
#                 if meaningful_response:
#                     context_parts.append(f"Previous Response: {meaningful_response}...")
#             else:
#                 response_str = str(entry['ai_response'])
#                 if not response_str.startswith(("Hello", "Hi", "Hey")):
#                     context_parts.append(f"Previous Response: {response_str[:150]}...")

#     return "\n".join(context_parts) if context_parts else ""

# def get_actual_database_results(user_query):
#     """Get actual database results by running the procedure and capturing data."""
#     try:
#         import mysql.connector
#         from mysql.connector import Error

#         # Database connection (using same config as Proceduremanager)
#         connection = mysql.connector.connect(
#             host='localhost',
#             database='custom',
#             user='root',
#             password='root'
#         )

#         if connection.is_connected():
#             cursor = connection.cursor()

#             # Run the Proceduremanager to create and execute procedure
#             stdout_capture = io.StringIO()
#             with redirect_stdout(stdout_capture):
#                 run_sql_procedure_agent(user_query)

#             # Try to get results from a simple query based on the user's request
#             results_data = []
#             query_lower = user_query.lower()

#             # Determine what kind of data to fetch based on query
#             if any(word in query_lower for word in ['employee', 'user', 'staff', 'worker']):
#                 try:
#                     cursor.execute("SELECT * FROM users LIMIT 10")
#                     rows = cursor.fetchall()
#                     column_names = [desc[0] for desc in cursor.description]

#                     for row in rows:
#                         row_data = []
#                         for i, value in enumerate(row):
#                             row_data.append(f"{column_names[i]}: {value}")
#                         results_data.append(" | ".join(row_data))

#                 except Error:
#                     pass
                    
#             elif any(word in query_lower for word in ['product', 'item', 'inventory']):
#                 try:
#                     cursor.execute("SELECT * FROM products LIMIT 10")
#                     rows = cursor.fetchall()
#                     column_names = [desc[0] for desc in cursor.description]

#                     for row in rows:
#                         row_data = []
#                         for i, value in enumerate(row):
#                             row_data.append(f"{column_names[i]}: {value}")
#                         results_data.append(" | ".join(row_data))

#                 except Error:
#                     pass

#             elif any(word in query_lower for word in ['order', 'sale', 'transaction']):
#                 try:
#                     cursor.execute("SELECT * FROM orders LIMIT 10")
#                     rows = cursor.fetchall()
#                     column_names = [desc[0] for desc in cursor.description]

#                     for row in rows:
#                         row_data = []
#                         for i, value in enumerate(row):
#                             row_data.append(f"{column_names[i]}: {value}")
#                         results_data.append(" | ".join(row_data))

#                 except Error:
#                     pass

#             cursor.close()
#             connection.close()

#             if results_data:
#                 return {
#                     'success': True,
#                     'data': results_data[:10],
#                     'summary': f"📊 Retrieved {len(results_data)} records from database",
#                     'quality_score': 90,
#                     'table_data': results_data
#                 }

#     except Exception as e:
#         print(f"Error getting database results: {e}")

#     return None

# def parse_proceduremanager_output(output, user_query):
#     """Parse output from Proceduremanager.py to extract actual data table results."""
#     try:
#         lines = output.split('\n')
#         results = []
#         procedure_code = ""
#         quality_score = 85  # Default score
#         table_data = []
#         key_metrics = []
#         report_description = ""
#         in_results_section = False
#         in_table_section = False

#         # Extract meaningful information from output
#         for line in lines:
#             line = line.strip()

#             # Look for procedure code
#             if 'CREATE PROCEDURE' in line.upper():
#                 procedure_code = line

#             # Look for execution results section
#             if 'EXECUTION RESULTS' in line:
#                 in_results_section = True
#                 continue

#             # Look for table data section
#             if in_results_section and ('TABLE DATA' in line or 'Data Table:' in line):
#                 in_table_section = True
#                 continue

#             # Extract table data rows
#             if in_table_section and line and not line.startswith('=') and not line.startswith('-'):
#                 # Skip headers and separators
#                 if not any(skip in line.lower() for skip in ['column', 'row', 'total', 'count']):
#                     # Look for actual data rows (usually contain numbers, names, etc.)
#                     if any(char.isdigit() for char in line) or any(word in line.lower() for word in ['employee', 'user', 'product', 'order']):
#                         table_data.append(line)

#             # Extract key metrics
#             if 'Key Metrics:' in line or (in_results_section and any(metric in line.lower() for metric in ['total', 'average', 'count', 'sum'])):
#                 if line and not line.startswith('=') and not line.startswith('-'):
#                     key_metrics.append(line)

#             # Extract description
#             if 'Description:' in line:
#                 report_description = line.replace('Description:', '').strip()

#         # If we found actual table data, use it
#         if table_data:
#             results = table_data[:15]  # Limit to 15 rows for clean display

#         # If we found key metrics, add them
#         elif key_metrics:
#             results = key_metrics[:10]

#         # Otherwise, look for any meaningful data in the output
#         else:
#             for line in lines:
#                 line = line.strip()
#                 if not line or line.startswith('=') or line.startswith('-') or line.startswith('STEP'):
#                     continue

#                 # Look for data-like content
#                 if (any(char.isdigit() for char in line) and
#                     len(line) > 10 and
#                     not line.startswith('Report Generated') and
#                     not line.startswith('User Query')):
#                     results.append(line)

#         # If still no results, create a meaningful summary
#         if not results:
#             query_lower = user_query.lower()
#             if any(word in query_lower for word in ['employee', 'hire', 'performance', 'top']):
#                 results = [
#                     "📊 Employee Performance Analysis",
#                     "🏆 Top performers identified based on criteria",
#                     "📈 Performance metrics calculated successfully",
#                     "✅ Data analysis completed - check database for detailed results"
#                 ]
#             elif any(word in query_lower for word in ['sales', 'revenue', 'customer', 'order']):
#                 results = [
#                     "💰 Sales Data Analysis Complete",
#                     "📊 Revenue trends analyzed successfully",
#                     "👥 Customer metrics processed",
#                     "✅ Business insights generated - check database for details"
#                 ]
#             else:
#                 results = [
#                     "🔍 Data Analysis Complete",
#                     "📊 Query processed successfully",
#                     "✅ Results generated and stored in database",
#                     "💡 Check your database tables for detailed output"
#                 ]

#         # Create summary based on what we found
#         if table_data:
#             summary = f"📊 Found {len(table_data)} data records from your query"
#         elif key_metrics:
#             summary = f"📈 Generated {len(key_metrics)} key metrics from analysis"
#         else:
#             summary = f"✅ Query processed successfully with {len(results)} insights"

#         return {
#             'success': True,
#             'data': results[:12],  # Limit for clean chat display
#             'summary': summary,
#             'quality_score': quality_score,
#             'procedure_code': procedure_code,
#             'description': report_description
#         }

#     except Exception as e:
#         return {
#             'success': False,
#             'data': [f"❌ Error parsing results: {str(e)}"],
#             'summary': "Result parsing failed",
#             'quality_score': 0
#         }

# def extract_clean_results(output_text, user_query):
#     """Extract clean, user-friendly results from procedure output."""
#     clean_results = {
#         'procedure_code': '',
#         'results': [],
#         'summary': '',
#         'data_points': []
#     }

#     try:
#         lines = output_text.split('\n')
#         current_section = None
#         procedure_lines = []
#         result_lines = []

#         for line in lines:
#             line = line.strip()

#             # Skip empty lines and separators
#             if not line or line.startswith('=') or line.startswith('-'):
#                 continue

#             # Identify sections
#             if 'CREATE PROCEDURE' in line.upper():
#                 current_section = 'procedure'
#                 procedure_lines.append(line)
#             elif current_section == 'procedure' and ('END' in line.upper() or 'DELIMITER' in line.upper()):
#                 procedure_lines.append(line)
#                 current_section = None
#             elif current_section == 'procedure':
#                 procedure_lines.append(line)
#             elif any(keyword in line.lower() for keyword in ['employee', 'candidate', 'performance', 'rank', 'score']):
#                 # Extract meaningful data points
#                 if '|' in line or 'Name:' in line or 'Rating:' in line:
#                     result_lines.append(line)

#         # Clean up procedure code
#         if procedure_lines:
#             clean_results['procedure_code'] = '\n'.join(procedure_lines)

#         # Process results into clean format
#         if result_lines:
#             clean_results['results'] = format_results_cleanly(result_lines, user_query)
#         else:
#             clean_results['results'] = ['Query executed successfully. Results may be available in the database.']

#         # Generate summary
#         clean_results['summary'] = generate_result_summary(user_query, clean_results['results'])

#     except Exception as e:
#         clean_results['results'] = [f'Error processing results: {str(e)}']

#     return clean_results

# def format_results_cleanly(result_lines, user_query):
#     """Format results in a clean, readable format."""
#     formatted_results = []

#     try:
#         query_lower = user_query.lower()

#         # Determine result type based on query
#         if any(word in query_lower for word in ['top', 'best', 'rank', 'performance']):
#             # Format as ranking results
#             for i, line in enumerate(result_lines[:10], 1):  # Limit to top 10
#                 if '|' in line:
#                     parts = [part.strip() for part in line.split('|')]
#                     if len(parts) >= 3:
#                         formatted_results.append(f"{i}. {parts[1]} - {parts[2]} (Rating: {parts[-1] if parts[-1].replace('.', '').isdigit() else 'N/A'})")
#                 else:
#                     formatted_results.append(f"{i}. {line}")
#         else:
#             # Format as general results
#             for line in result_lines[:20]:  # Limit to 20 results
#                 if line and not line.startswith('|'):
#                     formatted_results.append(line)

#         if not formatted_results:
#             formatted_results = ['Query completed successfully. No specific results to display.']

#     except Exception as e:
#         formatted_results = [f'Error formatting results: {str(e)}']

#     return formatted_results

# def generate_result_summary(user_query, results):
#     """Generate a brief summary of the results."""
#     try:
#         query_lower = user_query.lower()
#         result_count = len([r for r in results if not r.startswith('Error')])

#         if 'top' in query_lower or 'best' in query_lower:
#             return f"Found {result_count} top performers based on your criteria."
#         elif 'analysis' in query_lower or 'statistical' in query_lower:
#             return f"Statistical analysis completed with {result_count} data points."
#         elif 'hire' in query_lower or 'candidate' in query_lower:
#             return f"Hiring analysis completed for {result_count} candidates."
#         else:
#             return f"Query executed successfully with {result_count} results."
#     except:
#         return "Query completed."

# def get_query_type_from_text(user_query):
#     """Determine query type from user input."""
#     query_lower = user_query.lower()

#     if any(word in query_lower for word in ['hire', 'hiring', 'candidate', 'recruit']):
#         return 'HIRING'
#     elif any(word in query_lower for word in ['sales', 'revenue', 'profit', 'customer']):
#         return 'SALES'
#     elif any(word in query_lower for word in ['analysis', 'statistical', 'trend', 'pattern']):
#         return 'STATISTICAL'
#     elif any(word in query_lower for word in ['performance', 'rank', 'top', 'best']):
#         return 'PERFORMANCE'
#     else:
#         return 'GENERAL'

# def suggest_optimal_formulas_for_query(query_type):
#     """Suggest optimal formulas based on query type."""
#     suggestions = []

#     if query_type == 'HIRING':
#         suggestions.extend([
#             "Performance ranking analysis",
#             "Employee scoring system",
#             "Candidate comparison metrics"
#         ])
#     elif query_type == 'SALES':
#         suggestions.extend([
#             "Revenue trend analysis",
#             "Sales performance metrics",
#             "Customer value ranking"
#         ])
#     elif query_type == 'STATISTICAL':
#         suggestions.extend([
#             "Statistical analysis",
#             "Data distribution metrics",
#             "Trend identification"
#         ])
#     elif query_type == 'PERFORMANCE':
#         suggestions.extend([
#             "Performance ranking",
#             "Comparative analysis",
#             "Top performer identification"
#         ])

#     return suggestions

# def suggest_performance_formulas(user_query=None):
#     """Simple performance suggestions."""
#     return [
#         "Data analysis completed",
#         "Performance metrics calculated",
#         "Results optimized for your query"
#     ]

# # Simple formulas for the formulas page
# MATH_FORMULAS = {
#     'basic': {
#         'average': 'Calculate average values',
#         'sum': 'Calculate total values',
#         'count': 'Count records',
#         'ranking': 'Rank items by criteria'
#     }
# }

# # Template helper functions
# @app.template_filter('get_category_icon')
# def get_category_icon(category):
#     """Get Font Awesome icon for formula category."""
#     icons = {
#         'statistical': 'chart-bar',
#         'aggregation': 'calculator',
#         'business': 'briefcase',
#         'performance_ranking': 'trophy',
#         'interview_ranking': 'users',
#         'hiring_metrics': 'user-tie',
#         'financial': 'dollar-sign',
#         'time_series': 'clock',
#         'data_quality': 'check-circle'
#     }
#     return icons.get(category, 'cog')
    
# # Database setup for history
# def get_db_connection():
#     """Get MySQL database connection."""
#     return mysql.connector.connect(**DB_CONFIG)

# def init_db():
#     """Initialize MySQL database for storing query history."""
#     try:
#         conn = get_db_connection()
#         cursor = conn.cursor()

#         cursor.execute('''
#             CREATE TABLE IF NOT EXISTS query_history (
#                 id VARCHAR(255) PRIMARY KEY,
#                 timestamp DATETIME,
#                 user_query TEXT,
#                 query_type VARCHAR(100),
#                 suggested_formulas JSON,
#                 procedure_code LONGTEXT,
#                 execution_results JSON,
#                 quality_score INTEGER,
#                 status VARCHAR(50),
#                 session_id VARCHAR(50),
#                 INDEX idx_timestamp (timestamp),
#                 INDEX idx_status (status),
#                 INDEX idx_query_type (query_type),
#                 INDEX idx_session_id (session_id)
#             ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
#         ''')

#         # Add session_id column if it doesn't exist (for existing tables)
#         try:
#             cursor.execute('''
#                 ALTER TABLE query_history
#                 ADD COLUMN session_id VARCHAR(50),
#                 ADD INDEX idx_session_id (session_id)
#             ''')
#             print("✅ Added session_id column to existing query_history table")
#         except mysql.connector.Error as alter_error:
#             if "Duplicate column name" in str(alter_error):
#                 print("✅ session_id column already exists")
#             else:
#                 print(f"⚠️ Note: {alter_error}")

#         conn.commit()
#         cursor.close()
#         conn.close()
#         print("✅ MySQL database initialized successfully")
#     except mysql.connector.Error as e:
#         print(f"❌ Database initialization error: {e}")
#         # Try to create database if it doesn't exist
#         try:
#             temp_config = DB_CONFIG.copy()
#             temp_config.pop('database')
#             temp_conn = mysql.connector.connect(**temp_config)
#             temp_cursor = temp_conn.cursor()
#             temp_cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_CONFIG['database']}")
#             temp_conn.commit()
#             temp_cursor.close()
#             temp_conn.close()
#             print(f"✅ Database '{DB_CONFIG['database']}' created")
#             # Retry initialization
#             init_db()
#         except mysql.connector.Error as create_error:
#             print(f"❌ Failed to create database: {create_error}")

# def save_query_history(query_data):
#     """Save query execution to history database."""
#     try:
#         conn = get_db_connection()
#         cursor = conn.cursor()

#         # Convert timestamp to MySQL datetime format
#         timestamp = datetime.fromisoformat(query_data['timestamp'].replace('Z', '+00:00'))

#         cursor.execute('''
#             INSERT INTO query_history
#             (id, timestamp, user_query, query_type, suggested_formulas,
#              procedure_code, execution_results, quality_score, status, session_id)
#             VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) AS new_values
#             ON DUPLICATE KEY UPDATE
#             timestamp = new_values.timestamp,
#             user_query = new_values.user_query,
#             query_type = new_values.query_type,
#             suggested_formulas = new_values.suggested_formulas,
#             procedure_code = new_values.procedure_code,
#             execution_results = new_values.execution_results,
#             quality_score = new_values.quality_score,
#             status = new_values.status,
#             session_id = new_values.session_id
#         ''', (
#             query_data['id'],
#             timestamp,
#             query_data['user_query'],
#             query_data['query_type'],
#             json.dumps(query_data['suggested_formulas']),
#             query_data['procedure_code'],
#             json.dumps(query_data['execution_results']),
#             query_data['quality_score'],
#             query_data['status'],
#             query_data.get('session_id', None)
#         ))

#         conn.commit()
#         cursor.close()
#         conn.close()
#     except mysql.connector.Error as e:
#         print(f"❌ Error saving query history: {e}")

# def get_query_history(limit=50):
#     """Retrieve query history from database."""
#     try:
#         conn = get_db_connection()
#         cursor = conn.cursor()

#         cursor.execute('''
#             SELECT id, timestamp, user_query, query_type, suggested_formulas,
#                    procedure_code, execution_results, quality_score, status, session_id
#             FROM query_history
#             ORDER BY timestamp DESC
#             LIMIT %s
#         ''', (limit,))

#         rows = cursor.fetchall()
#         cursor.close()
#         conn.close()

#         history = []
#         for row in rows:
#             history.append({
#                 'id': row[0],
#                 'timestamp': row[1].isoformat() if row[1] else '',
#                 'user_query': row[2],
#                 'query_type': row[3],
#                 'suggested_formulas': json.loads(row[4]) if row[4] else [],
#                 'procedure_code': row[5],
#                 'execution_results': json.loads(row[6]) if row[6] else [],
#                 'quality_score': row[7],
#                 'status': row[8],
#                 'session_id': row[9] if len(row) > 9 else None
#             })

#         return history
#     except mysql.connector.Error as e:
#         print(f"❌ Error retrieving query history: {e}")
#         return []

# # Initialize database on startup
# init_db()

# @app.route('/')
# def index():
#     """Redirect to AI Chat interface."""
#     return redirect('/chat')

# @app.route('/chat')
# def chat():
#     """AI Chat interface page."""
#     return render_template('chat.html', session_id=DEFAULT_SESSION_ID)

# @app.route('/history/recent')
# def recent_chats():
#     """Get recent 5 chat history for sidebar"""
#     try:
#         conn = get_db_connection()
#         cursor = conn.cursor()

#         # Get recent chats from existing query_history table
#         try:
#             cursor.execute("""
#                 SELECT user_query, timestamp, session_id, quality_score
#                 FROM query_history
#                 WHERE user_query IS NOT NULL AND user_query != ''
#                 ORDER BY timestamp DESC
#                 LIMIT 5
#             """)
#         except mysql.connector.Error as e:
#             print(f"Error querying recent chats: {e}")
#             cursor.execute("""
#                 SELECT user_query, timestamp, quality_score
#                 FROM query_history
#                 WHERE user_query IS NOT NULL AND user_query != ''
#                 ORDER BY timestamp DESC
#                 LIMIT 5
#             """)

#         results = cursor.fetchall()
#         recent_chats = []

#         for row in results:
#             # Handle different row structures based on what columns are available
#             if len(row) >= 4:  # Has session_id column
#                 recent_chats.append({
#                     'query': row[0],
#                     'timestamp': row[1].isoformat() if row[1] else '',
#                     'session_id': row[2] if row[2] else DEFAULT_SESSION_ID,
#                     'quality_score': row[3] if row[3] else None
#                 })
#             elif len(row) >= 3:  # No session_id column
#                 recent_chats.append({
#                     'query': row[0],
#                     'timestamp': row[1].isoformat() if row[1] else '',
#                     'session_id': DEFAULT_SESSION_ID,
#                     'quality_score': row[2] if row[2] else None
#                 })
#             else:  # Minimal data
#                 recent_chats.append({
#                     'query': row[0],
#                     'timestamp': row[1].isoformat() if len(row) > 1 and row[1] else '',
#                     'session_id': DEFAULT_SESSION_ID,
#                     'quality_score': None
#                 })

#         cursor.close()
#         conn.close()

#         print(f"Found {len(recent_chats)} recent chats for session {DEFAULT_SESSION_ID}")
#         return jsonify(recent_chats)
#     except Exception as e:
#         print(f"Error fetching recent chats: {e}")
#         # Return empty array on error
#         return jsonify([])

# # @app.route('/debug/add_sample_chats')
# def add_sample_chats_disabled():
#     """Add sample chat data for testing"""
#     try:
#         conn = get_db_connection()
#         cursor = conn.cursor()

#         # Add some sample chat history
#         sample_chats = [
#             ("Show me user statistics", "Sample response with user data", 85),
#             ("List all employees", "Employee list generated successfully", 92),
#             ("Performance analysis", "Performance metrics calculated", 78),
#             ("Sales data for Q1", "Q1 sales report generated", 88),
#             ("Customer demographics", "Demographics analysis complete", 90)
#         ]

#         for query, response, quality in sample_chats:
#             cursor.execute("""
#                 INSERT INTO query_history (query, ai_response, session_id, quality_score, timestamp)
#                 VALUES (%s, %s, %s, %s, NOW())
#             """, (query, response, DEFAULT_SESSION_ID, quality))

#         conn.commit()
#         cursor.close()
#         conn.close()

#         return jsonify({"success": True, "message": f"Added {len(sample_chats)} sample chats"})
#     except Exception as e:
#         print(f"Error adding sample chats: {e}")
#         return jsonify({"success": False, "error": str(e)})

# @app.route('/debug/check_database')
# def check_database():
#     """Check what's in the query_history table"""
#     try:
#         conn = get_db_connection()
#         cursor = conn.cursor()

#         # Check table structure
#         cursor.execute("DESCRIBE query_history")
#         columns = cursor.fetchall()

#         # Check recent data with user_query
#         cursor.execute("""
#             SELECT user_query, timestamp, session_id, quality_score, status
#             FROM query_history
#             WHERE user_query IS NOT NULL
#             ORDER BY timestamp DESC
#             LIMIT 10
#         """)
#         recent_data = cursor.fetchall()

#         # Count total rows
#         cursor.execute("SELECT COUNT(*) FROM query_history WHERE user_query IS NOT NULL")
#         total_count = cursor.fetchone()[0]

#         cursor.close()
#         conn.close()

#         return jsonify({
#             "columns": [{"Field": col[0], "Type": col[1]} for col in columns],
#             "recent_data": [list(row) for row in recent_data],
#             "total_rows": total_count,
#             "sample_queries": [row[0] for row in recent_data if row[0]]
#         })
#     except Exception as e:
#         return jsonify({"error": str(e)})



# @app.route('/api/analyze_query', methods=['POST'])
# def analyze_query():
#     """Analyze user query and provide suggestions."""
#     try:
#         data = request.get_json()
#         user_query = data.get('query', '').strip()
        
#         if not user_query:
#             return jsonify({'error': 'Query cannot be empty'}), 400
        
#         # Analyze query
#         query_type = get_query_type_from_text(user_query)
#         optimal_formulas = suggest_optimal_formulas_for_query(query_type)
#         performance_suggestions = suggest_performance_formulas(user_query)
        
#         return jsonify({
#             'query_type': query_type,
#             'optimal_formulas': optimal_formulas[:10],  # Limit to top 10
#             'performance_suggestions': performance_suggestions[:5],  # Limit to top 5
#             'available_formulas': MATH_FORMULAS
#         })
        
#     except Exception as e:
#         return jsonify({'error': str(e)}), 500

# @app.route('/api/execute_query', methods=['POST'])
# def execute_query():
#     """Execute the SQL procedure generation and execution with session management."""
#     try:
#         data = request.get_json()
#         user_query = data.get('query', '').strip()
#         session_id = data.get('session_id', DEFAULT_SESSION_ID)
#         token = data.get('token', DEFAULT_TOKEN)

#         if not user_query:
#             return jsonify({'error': 'Query cannot be empty'}), 400

#         # Validate session
#         if not validate_session(session_id, token):
#             return jsonify({'error': 'Invalid session credentials'}), 401
        
#         # Generate unique ID for this execution
#         execution_id = str(uuid.uuid4())
#         timestamp = datetime.now().isoformat()
        
#         # Store initial data
#         query_data = {
#             'id': execution_id,
#             'timestamp': timestamp,
#             'user_query': user_query,
#             'query_type': get_query_type_from_text(user_query),
#             'suggested_formulas': suggest_optimal_formulas_for_query(get_query_type_from_text(user_query)),
#             'procedure_code': '',
#             'execution_results': [],
#             'quality_score': 0,
#             'status': 'processing',
#             'session_id': session_id
#         }
        
#         # Save initial state
#         save_query_history(query_data)
        
#         # Execute in background thread to avoid timeout
#         def execute_in_background():
#             try:
#                 # Process the query using our simple backend with session context
#                 result = process_user_query(user_query, session_id, token)

#                 if result['success']:
#                     query_data['status'] = 'completed'
#                     query_data['quality_score'] = result['quality_score']
#                     query_data['procedure_code'] = 'Query processed successfully'
#                     query_data['execution_results'] = result['results']
#                 else:
#                     query_data['status'] = 'error'
#                     query_data['quality_score'] = 0
#                     query_data['procedure_code'] = 'Query processing failed'
#                     query_data['execution_results'] = result['results']

#                 save_query_history(query_data)

#             except Exception as e:
#                 query_data['status'] = 'error'
#                 query_data['execution_results'] = [f'System error: {str(e)}']
#                 save_query_history(query_data)
        
#         # Start background execution
#         thread = threading.Thread(target=execute_in_background)
#         thread.start()
        
#         return jsonify({
#             'execution_id': execution_id,
#             'status': 'processing',
#             'message': 'Query execution started. Check status for updates.'
#         })
        
#     except Exception as e:
#         return jsonify({'error': str(e)}), 500

# @app.route('/api/execution_status/<execution_id>')
# def get_execution_status(execution_id):
#     """Get the status of a query execution."""
#     try:
#         conn = get_db_connection()
#         cursor = conn.cursor()

#         cursor.execute('''
#             SELECT id, timestamp, user_query, query_type, suggested_formulas,
#                    procedure_code, execution_results, quality_score, status, session_id
#             FROM query_history WHERE id = %s
#         ''', (execution_id,))
#         row = cursor.fetchone()
#         cursor.close()
#         conn.close()

#         if not row:
#             return jsonify({'error': 'Execution not found'}), 404

#         return jsonify({
#             'id': row[0],
#             'timestamp': row[1].isoformat() if row[1] else '',
#             'user_query': row[2],
#             'query_type': row[3],
#             'suggested_formulas': json.loads(row[4]) if row[4] else [],
#             'procedure_code': row[5],
#             'execution_results': json.loads(row[6]) if row[6] else [],
#             'quality_score': row[7],
#             'status': row[8],
#             'session_id': row[9] if len(row) > 9 else None
#         })

#     except Exception as e:
#         return jsonify({'error': str(e)}), 500

# @app.route('/api/history')
# def get_history():
#     """Get query execution history."""
#     try:
#         limit = request.args.get('limit', 50, type=int)
#         history = get_query_history(limit)
#         return jsonify(history)
        
#     except Exception as e:
#         return jsonify({'error': str(e)}), 500

# @app.route('/api/delete_history/<history_id>', methods=['DELETE'])
# def delete_history_item(history_id):
#     """Delete a specific history item."""
#     try:
#         conn = get_db_connection()
#         cursor = conn.cursor()

#         cursor.execute('DELETE FROM query_history WHERE id = %s', (history_id,))
#         conn.commit()
#         cursor.close()
#         conn.close()

#         return jsonify({'message': 'History item deleted successfully'})

#     except Exception as e:
#         return jsonify({'error': str(e)}), 500

# @app.route('/api/clear_history', methods=['DELETE'])
# def clear_all_history():
#     """Clear all query history."""
#     try:
#         conn = get_db_connection()
#         cursor = conn.cursor()

#         cursor.execute('DELETE FROM query_history')
#         conn.commit()
#         cursor.close()
#         conn.close()

#         return jsonify({'message': 'All history cleared successfully'})

#     except Exception as e:
#         return jsonify({'error': str(e)}), 500

# @app.route('/history')
# def history_page():
#     """History page."""
#     return render_template('history.html')

# @app.route('/formulas')
# def formulas_page():
#     """Mathematical formulas reference page."""
#     return render_template('formulas.html', formulas=MATH_FORMULAS)

# @app.route('/api/session/history', methods=['GET'])
# def get_session_history_api():
#     """Get chat history for the current session from database."""
#     try:
#         session_id = request.args.get('session_id', DEFAULT_SESSION_ID)
#         token = request.args.get('token', DEFAULT_TOKEN)
#         limit = request.args.get('limit', 50, type=int)

#         if not validate_session(session_id, token):
#             return jsonify({'error': 'Invalid session credentials'}), 401

#         history = get_session_history(session_id, token, limit)
#         return jsonify({
#             'session_id': session_id,
#             'history': history,
#             'count': len(history),
#             'source': 'database'
#         })

#     except Exception as e:
#         return jsonify({'error': str(e)}), 500

# @app.route('/api/session/validate', methods=['POST'])
# def validate_session_endpoint():
#     """Validate session credentials."""
#     try:
#         data = request.get_json()
#         session_id = data.get('session_id', DEFAULT_SESSION_ID)
#         token = data.get('token', DEFAULT_TOKEN)

#         is_valid = validate_session(session_id, token)

#         return jsonify({
#             'valid': is_valid,
#             'session_id': session_id if is_valid else None,
#             'message': 'Session valid' if is_valid else 'Invalid session credentials'
#         })

#     except Exception as e:
#         return jsonify({'error': str(e)}), 500

# @app.route('/api/session/clear', methods=['POST'])
# def clear_session_history_endpoint():
#     """Clear chat history for the current session."""
#     try:
#         data = request.get_json()
#         session_id = data.get('session_id', DEFAULT_SESSION_ID)
#         token = data.get('token', DEFAULT_TOKEN)

#         if not validate_session(session_id, token):
#             return jsonify({'error': 'Invalid session credentials'}), 401

#         success = clear_session_history(session_id, token)

#         if success:
#             return jsonify({
#                 'message': 'Session history cleared successfully from database',
#                 'session_id': session_id
#             })
#         else:
#             return jsonify({'error': 'Failed to clear session history'}), 500

#     except Exception as e:
#         return jsonify({'error': str(e)}), 500

# @app.route('/api/session/stats', methods=['GET'])
# def get_session_stats():
#     """Get session statistics from database."""
#     try:
#         session_id = request.args.get('session_id', DEFAULT_SESSION_ID)
#         token = request.args.get('token', DEFAULT_TOKEN)

#         if not validate_session(session_id, token):
#             return jsonify({'error': 'Invalid session credentials'}), 401

#         conn = get_db_connection()
#         cursor = conn.cursor()

#         # Get session statistics
#         cursor.execute('''
#             SELECT
#                 COUNT(*) as total_queries,
#                 AVG(quality_score) as avg_quality,
#                 MAX(timestamp) as last_activity,
#                 MIN(timestamp) as first_activity
#             FROM query_history
#             WHERE session_id = %s AND query_type = 'session_chat'
#         ''', (session_id,))

#         stats = cursor.fetchone()
#         cursor.close()
#         conn.close()

#         return jsonify({
#             'session_id': session_id,
#             'total_queries': stats[0] or 0,
#             'average_quality': round(stats[1] or 0, 2),
#             'last_activity': stats[2].isoformat() if stats[2] else None,
#             'first_activity': stats[3].isoformat() if stats[3] else None,
#             'session_active': stats[0] > 0 if stats[0] else False
#         })

#     except Exception as e:
#         return jsonify({'error': str(e)}), 500

# if __name__ == '__main__':
#     app.run(
#         debug=FLASK_CONFIG['DEBUG'],
#         host=FLASK_CONFIG['HOST'],
#         port=FLASK_CONFIG['PORT'],
#         threaded=FLASK_CONFIG['THREADED']
#     )

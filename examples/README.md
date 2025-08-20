# splurge-sql-generator Examples

This directory contains examples demonstrating how to use splurge-sql-generator with the simplified logger approach.

## Files

### SQL Template Files
- **`User.sql`** - User management operations (CRUD)
- **`ProductRepository.sql`** - Product catalog operations
- **`OrderService.sql`** - Order processing operations

### Generated Python Classes
- **`output/User.py`** - Generated User class
- **`output/ProductRepository.py`** - Generated ProductRepository class  
- **`output/OrderService.py`** - Generated OrderService class

### Example Scripts
- **`usage_example.py`** - Comprehensive usage example with database setup
- **`logger_comparison.py`** - Comparison between old and new logger approaches

## Quick Start

1. **Generate the Python classes** (already done):
   ```bash
   # Using console script
   splurge-sql-gen *.sql --output output/

   # Or using module path
   python -m splurge_sql_generator.cli *.sql --output output/
   ```

2. **Run the comprehensive example**:
   ```bash
   python usage_example.py
   ```

3. **See the logger comparison**:
   ```bash
   python logger_comparison.py
   ```

## Key Features Demonstrated

### Simplified Logger Approach (v0.2.2+)

The generated classes now use a simplified logger approach:

```python
# Before (v0.2.1 and earlier)
users = User.get_user_by_id(
    connection=connection,
    user_id=1,
    logger=custom_logger,  # Optional parameter
)

# After (v0.2.2+)
users = User.get_user_by_id(
    connection=connection,
    user_id=1,
    # No logger parameter needed - uses class-level logger automatically
)
```

### Benefits of the New Approach

- ✅ **Cleaner method signatures** - No optional logger parameter
- ✅ **Consistent logging** - All methods use the same class-level logger
- ✅ **Simpler API** - Fewer parameters to manage
- ✅ **Better maintainability** - Less complexity in generated code
- ✅ **Python best practices** - Class-level logger follows utility class patterns

### Class-Level Logger

Each generated class has its own logger:

```python
class User:
    logger = logging.getLogger(f"{__name__}.User")
    
    @classmethod
    def get_user_by_id(cls, *, connection: Connection, user_id: Any) -> List[Row]:
        logger = cls.logger  # Uses class-level logger
        # ... rest of method
```

## Example Output

When you run the examples, you'll see:

1. **Debug logging** showing SQL execution details
2. **Parameter logging** showing the values being passed
3. **Result logging** showing the number of rows returned
4. **Error logging** if any issues occur

Example log output:
```
2025-01-XX XX:XX:XX,XXX - output.User.User - DEBUG - Executing get_user_by_id operation
2025-01-XX XX:XX:XX,XXX - output.User.User - DEBUG - Parameters: {'user_id': 1}
2025-01-XX XX:XX:XX,XXX - output.User.User - DEBUG - Fetched 1 rows
```

## Database Setup

The examples use SQLite for simplicity, but the generated classes work with any SQLAlchemy-compatible database:

- **SQLite** (examples) - `sqlite:///example.db`
- **PostgreSQL** - `postgresql://user:pass@localhost/dbname`
- **MySQL** - `mysql://user:pass@localhost/dbname`
- **SQL Server** - `mssql+pyodbc://user:pass@server/dbname`

## Transaction Management

The examples demonstrate proper transaction management:

```python
# For data modification operations
with connection.begin():
    result = User.create_user(
        connection=connection,
        username='john_doe',
        email='john@example.com',
        password_hash='hashed_password',
        status='active'
    )
    # Transaction commits automatically when context exits
```

## Customizing Logging

You can customize the logging behavior by configuring the class-level loggers:

```python
import logging

# Configure logging for all generated classes
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Or configure specific class loggers
User.logger.setLevel(logging.INFO)
ProductRepository.logger.setLevel(logging.WARNING)
```

## Running the Examples

Make sure you have the required dependencies:

```bash
pip install sqlalchemy
```

Then run any of the example scripts:

```bash
# Comprehensive example with database operations
python usage_example.py

# Logger comparison and benefits
python logger_comparison.py
```

The examples will create a SQLite database file (`example.db`) in the current directory. 
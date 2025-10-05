import logging
import math
import sqlite3

def log_function(func):
    def wrapper(*args, **kwargs):
        logging.info(f"Calling {func.__name__} with args: {args} {kwargs}")
        result = func(*args, **kwargs)
        logging.info(f"{func.__name__} returned: {result}")
        return result
    return wrapper

DATABASE_PATH = r"D:\Himanshu\EAG-V2\emloyee_salary.db"

@log_function
def number_list_to_sum(lst):
    if not lst:
        return 0
    return sum(lst)

@log_function
def calculate_difference(a, b):
    return a - b

@log_function
def number_list_to_product(lst):
    if not lst:
        return 0
    result = 1
    for num in lst:
        result *= num
    return result

@log_function
def calculate_division(a, b):
    if b == 0:
        raise ValueError("Division by zero is not allowed")
    return a / b

@log_function
def strings_to_chars_to_int(s):
    return [ord(c) for c in s]

@log_function
def int_list_to_exponential_values(lst):
    return [math.e**x for x in lst]

@log_function
def fibonacci_numbers(n):
    fib = [0, 1]
    for i in range(2, n):
        fib.append(fib[i-1] + fib[i-2])
    return fib[:n]

@log_function
def calculate_factorial(n):
    if n < 0:
        raise ValueError("Factorial is not defined for negative numbers")
    if n == 0:
        return [1]
    factorials = [1]  # 0!
    current = 1
    for i in range(1, n):
        current *= i
        factorials.append(current)
    return factorials

@log_function
def calculate_permutation(n, r):
    if n < 0 or r < 0 or r > n:
        raise ValueError("Invalid values for n and r in permutation")
    return math.factorial(n) // math.factorial(n - r)


@log_function
def calculate_combination(n, r):
    if n < 0 or r < 0 or r > n:
        raise ValueError("Invalid values for n and r in combination")
    return math.factorial(n) // (math.factorial(r) * math.factorial(n - r)) 


@log_function
def calculate_salary_for_id(emp_id: int, db_path: str = DATABASE_PATH):
    """Return the salary for the given employee id from the SQLite database.

    Args:
        emp_id (int): The id of the employee whose salary needs to be fetched.
        db_path (str, optional): Path to the SQLite database. Defaults to DATABASE_PATH.

    Returns:
        float | int | None: Salary of the employee if found else None.
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT salary FROM employee WHERE id = ?", (emp_id,))
        result = cursor.fetchone()
        return result[0] if result else None
    finally:
        if 'conn' in locals():
            conn.close()

@log_function
def calculate_salary_for_name(emp_name: str, db_path: str = DATABASE_PATH):
    """Return the salary for the given employee name from the SQLite database.

    Args:
        emp_name (str): The name of the employee whose salary needs to be fetched.
        db_path (str, optional): Path to the SQLite database. Defaults to DATABASE_PATH.

    Returns:
        float | int | None: Salary of the employee if found else None.
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT salary FROM employee WHERE name = ?", (emp_name,))
        result = cursor.fetchone()
        return result[0] if result else None
    finally:
        if 'conn' in locals():
            conn.close()


@log_function
def calculate_percentage(percent: float | int, number: float | int):
    """Calculate the percentage of a given number.

    Args:
        percent (float | int): The percentage value (e.g., 10 for 10%).
        number (float | int): The base number on which percentage is calculated.

    Returns:
        float: The calculated percentage value.

    Example:
        >>> calculate_percentage(10, 5000)
        500.0
    """
    return (percent / 100) * number
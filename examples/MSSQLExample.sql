# MSSQLExample

#get_employee_by_id
SELECT id, employee_code, first_name, last_name, email, salary, hire_date, is_active
FROM employees
WHERE id = :employee_id;

#get_employees_by_department
SELECT e.id, e.first_name, e.last_name, e.salary, d.name as department_name
FROM employees e
JOIN departments d ON e.department_id = d.id
WHERE e.department_id = :department_id AND e.is_active = :is_active;

#create_employee
INSERT INTO employees (first_name, last_name, email, salary, department_id, is_active)
VALUES (:first_name, :last_name, :email, :salary, :department_id, :is_active)
OUTPUT INSERTED.id;

#update_employee_salary
UPDATE employees
SET salary = :new_salary, row_version = DEFAULT
WHERE id = :employee_id;

#get_projects_by_budget_range
SELECT id, name, description, start_date, end_date, budget, status
FROM projects
WHERE budget BETWEEN :min_budget AND :max_budget
ORDER BY budget DESC;

#get_department_budget_summary
SELECT d.name, COUNT(e.id) as employee_count, SUM(e.salary) as total_salary
FROM departments d
LEFT JOIN employees e ON d.id = e.department_id
WHERE d.is_active = :is_active
GROUP BY d.id, d.name
HAVING SUM(e.salary) > :min_total_salary;

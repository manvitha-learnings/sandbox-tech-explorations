CREATE TABLE IF NOT EXISTS `cicd_demo.sample_customers`
(
  customer_id INT64 OPTIONS(description="Unique customer identifier"),
  first_name STRING OPTIONS(description="Customer first name"),
  last_name STRING OPTIONS(description="Customer last name"),
  email STRING OPTIONS(description="Customer email address"),
  signup_date DATE OPTIONS(description="Date the customer signed up"),
  country STRING OPTIONS(description="Customer country"),
  total_spend NUMERIC OPTIONS(description="Customer lifetime spending")
)
PARTITION BY signup_date
CLUSTER BY customer_id
OPTIONS (
  description = "Sample customer table deployed through GitHub Actions CI/CD",
  labels = [
    ("environment", "demo"),
    ("managed_by", "github-actions"),
    ("project", "bigquery-cicd")
  ]
);
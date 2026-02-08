# Invoicing System Backend - Backend Assessment

**Time Limit: 60 minutes**

## Important Instructions

> **1. Fork this repo into your personal github account**
> 
> **2. Do not raise Pull Request in the original repo**
> 
> **3. Application must be runnable with `docker-compose up` command**
> 
> **4. Complete as many APIs as possible within the time limit**
> 
> **5. Prioritize working functionality - do not submit broken code that fails to run with `docker-compose up`**

### Tips
- Focus on core functionality first, then add features incrementally
- Test your application with `docker-compose up` before final submission
- A partially complete but working solution is better than a complete but broken one

---

A FastAPI backend project with SQLite database.

## Objective

Build a backend API for an **Invoicing System** that allows users to create and manage invoices.

## Functional Requirements

### Single User System
- No authentication required. The system is designed for a single user.

### Invoice Management
- User should be able to create invoices
- User should be able to list invoices
- User should be able to get an invoice by ID
- User should be able to delete an invoice

An invoice consists of:
- **Client**
- **Products** (items)

For **products** and **clients**, do not create APIs—use seed data. The developer needs to design the database schema and APIs for the invoicing system.



## Data Requirements (Fields)

### Product (seed data only)
- name
- price

### Client (seed data only)
- name
- address
- company registration no.

### Invoice
- Invoice no
- issue date
- due date
- client
- address
- items
- tax
- total

## Quick Start (Docker)

The easiest way to run the application:

```bash
docker-compose up --build
```

This will:
- Build the Docker image
- Run database migrations automatically (if applicable)
- Start the API server at `http://localhost:8000`

To stop the application:

```bash
docker-compose down
```

## API Examples (curl)

Use these curl commands to exercise the invoices API. Replace localhost and port if your server is hosted elsewhere.

1) List seeded products (seed data)

```bash
curl -s http://localhost:8000/invoices/products | jq
```

2) List seeded clients (seed data)

```bash
curl -s http://localhost:8000/invoices/clients | jq
```

3) Create a new invoice

Sample JSON payload (products and clients are seeded by migrations; use ids returned from the commands above):

```bash
curl -s -X POST http://localhost:8000/invoices \
	-H "Content-Type: application/json" \
	-d '{
		"issue_date": "2026-02-08",
		"due_date": "2026-02-22",
		"client_id": 1,
		"address": "123 Main St",
		"items": [
			{"product_id": 1, "quantity": 2},
			{"product_id": 2, "quantity": 1}
		],
		"tax": 2.5
	}' | jq
```

4) List all invoices

```bash
curl -s http://localhost:8000/invoices | jq
```

5) Get a single invoice by id (replace 1 with the invoice id returned from create)

```bash
curl -s http://localhost:8000/invoices/1 | jq
```

6) Delete an invoice

```bash
curl -s -X DELETE http://localhost:8000/invoices/1 -I
```

Notes:
- If you don't have `jq` installed, omit the `| jq` or use `python -m json.tool` to pretty-print JSON.
- If running with Docker Desktop / Colima, use the compose commands documented above to start the server before running the curl commands.


## Manual Setup (Without Docker)

### 1. Create and activate a virtual environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run database migrations (if applicable)

```bash
python migrate.py upgrade
```

### 4. Start the server

```bash
uvicorn app.main:app --reload
```

Or run directly:

```bash
python -m app.main
```

The API will be available at `http://localhost:8000`

## Database Migrations

### Running Migrations

**Apply all pending migrations:**
```bash
python migrate.py upgrade
```

**Revert all migrations:**
```bash
python migrate.py downgrade
```

**List migration status:**
```bash
python migrate.py list
```

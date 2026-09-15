# Real-Time Fraud & Ledger Reconciliation Pipeline
## Project Overview
This project implements an end-to-end fraud detection and ledger reconciliation pipeline for a simulated fintech environment. Synthetic transaction data is generated in Python and loaded into PostgreSQL as two independent sources of truth, an internal ledger and a payment gateway feed, deliberately seeded with reconciliation drift. Databricks (PySpark) then joins the two sources to surface mismatches and applies fraud-scoring logic to flag suspicious activity. Results are written back to PostgreSQL, where Grafana renders a live monitoring dashboard.

The objective is to demonstrate the full lifecycle a fintech data team deals with in production: ingesting transactional data, detecting where two systems of record disagree, scoring transactions for suspicious patterns, and surfacing all of it on a dashboard an analyst would actually use.

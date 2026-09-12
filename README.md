# NovaCart Customer Support Agent

A deterministic, policy-grounded customer-support agent built with FastAPI, vector search, and manually authored NovaCart policy documents.

NovaCart is a fictional e-commerce brand used to demonstrate customer-support query classification, policy retrieval, response generation, and escalation decisions.

## Features

- Customer-support query classification
- Policy document retrieval using vector search
- Context-grounded response generation
- Order tracking support
- Order cancellation support
- Payment issue support
- Damaged or defective product support
- Return and refund guidance
- Shipping-related guidance
- Source references in API responses
- Retrieval confidence information
- Escalation decision fields
- Safety warnings for sensitive payment information
- Automated test suite
- FastAPI Swagger documentation

## Tech Stack

- Python
- FastAPI
- Pydantic
- Sentence Transformers
- Vector search
- Pytest
- Uvicorn
- Markdown policy documents

## Project Structure

```text
ai-customer-support-agent/
│
├── backend/
│   └── app/
│       ├── main.py
│       ├── orchestration.py
│       ├── policy.py
│       ├── context.py
│       ├── support_response.py
│       └── ...
│
├── data/
│   └── policies/
│       ├── orders.md
│       ├── returns.md
│       ├── payments.md
│       ├── shipping.md
│       └── company_overview.md
│
├── tests/
│   ├── test_evaluation.py
│   ├── test_support_response.py
│   └── ...
│
├── requirements.txt
├── README.md
└── .gitignore
```

## How the System Works

The system follows a deterministic support-agent workflow:

```text
Customer Query
      │
      ▼
Query Classification
      │
      ▼
Policy Retrieval
      │
      ▼
Relevant Context Preparation
      │
      ▼
Context-Grounded Response Generation
      │
      ▼
Support Answer + Sources + Confidence + Escalation
```

## Supported Query Types

The current prototype supports questions related to:

### Order Tracking

Example:

```text
Where is my order?
```

The response explains that tracking information is provided after dispatch and advises the customer to check their order history.

### Order Cancellation

Example:

```text
How can I cancel my order?
```

The response explains the difference between cancellation before and after dispatch.

### Payment Issues

Example:

```text
My payment was deducted but the order failed.
```

The response advises customers not to place repeated orders immediately and explains what information can safely be shared with support.

### Damaged or Defective Products

Example:

```text
I received a damaged product.
```

The response advises customers to report the issue as soon as possible and provide photographs when requested.

### Returns and Refunds

Example:

```text
How do I return an item?
```

The response provides return-related guidance based on the retrieved NovaCart policy documents.

## Setup

### 1. Clone the Repository

```powershell
git clone <your-repository-url>
cd ai-customer-support-agent
```

Replace `<your-repository-url>` with the URL of this GitHub repository.

### 2. Create a Virtual Environment

```powershell
python -m venv .venv
```

### 3. Activate the Virtual Environment

On Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks script execution, run PowerShell with the required execution-policy permission or use the virtual-environment Python executable directly.

### 4. Install Dependencies

```powershell
pip install -r requirements.txt
```

## Run the Test Suite

Run all tests using:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

The current test suite contains 88 tests.

The expected result is similar to:

```text
88 passed
```

## Run the FastAPI Server

Start the API using:

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --reload
```

The API will be available at:

```text
http://127.0.0.1:8000
```

## Swagger Documentation

Open the following URL in your browser:

```text
http://127.0.0.1:8000/docs
```

The Swagger interface can be used to test the support endpoint interactively.

## API Endpoint

### POST `/support`

This endpoint accepts a customer-support query and returns a generated response.

### Request Body

```json
{
  "query": "Where is my order?"
}
```

### Example Queries

```json
{
  "query": "Where is my order?"
}
```

```json
{
  "query": "How can I cancel my order?"
}
```

```json
{
  "query": "My payment was deducted but the order failed."
}
```

```json
{
  "query": "I received a damaged product."
}
```

### Response Fields

The API response contains:

- `answer`: Generated customer-support response
- `sources`: Retrieved policy context used for the response
- `has_usable_context`: Indicates whether usable policy context was found
- `retrieval_confidence`: Confidence level of the retrieval process
- `confidence_reason`: Explanation of the retrieval confidence
- `should_escalate`: Indicates whether the query should be escalated
- `escalation_reason`: Reason for escalation, when applicable

### Example Response

```json
{
  "answer": "Tracking details are provided after dispatch. Check your order history for tracking information. If tracking is missing or appears incorrect, contact NovaCart support with your order ID.",
  "sources": [
    {
      "text": "Tracking is provided after dispatch.",
      "source": "orders.md",
      "chunk_id": "orders.md:8",
      "distance": 1.22
    }
  ],
  "has_usable_context": true,
  "retrieval_confidence": "medium",
  "confidence_reason": "Relevant retrieved policy context is available and was used to generate the answer.",
  "should_escalate": false,
  "escalation_reason": null
}
```

## Policy Documents

The current policy knowledge base is stored in Markdown files under:

```text
data/policies/
```

The policy documents cover:

- Orders
- Returns
- Payments
- Shipping
- Company overview

The system uses these documents as the source of truth for customer-support responses.

## Safety and Privacy Considerations

The support agent avoids requesting sensitive payment information.

Customers should never share the following information in support messages:

- Passwords
- One-time passwords
- CVVs
- Full card numbers
- Unrelated personal information

Only the minimum information required to locate a support request should be provided, such as an order ID or limited transaction details.

## Testing Coverage

The test suite checks important behavior such as:

- Query classification
- Policy retrieval
- Response generation
- Order-related questions
- Cancellation questions
- Payment-related questions
- Damaged-product questions
- Source inclusion
- Context availability
- Confidence fields
- Escalation fields
- Safety-related response content

## Current Limitations

- NovaCart is a fictional brand used for this prototype.
- The policy documents are manually authored.
- The system does not access real customer orders.
- The system does not connect to real payment providers.
- Tracking information cannot be verified against live order systems.
- Payment status cannot be checked against a real bank or payment provider.
- The current response generation is deterministic and policy-based.
- The system does not send emails or create real support tickets.
- Retrieval confidence is based on the current prototype's retrieval logic.
- The project is not connected to a production customer-support platform.
- The project is separate from the Hiver customer-support assignment.

## Example Workflow

A customer sends:

```text
My payment was deducted but I did not receive an order confirmation.
```

The system:

1. Classifies the query as a payment/order-confirmation issue.
2. Retrieves relevant order and payment policies.
3. Generates a policy-grounded response.
4. Advises the customer not to place another order immediately.
5. Recommends checking order history and email.
6. Advises contacting support with limited transaction details.
7. Warns the customer not to share sensitive payment credentials.
8. Returns the answer along with source and confidence information.

## Development Commands

Run tests:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Start the API:

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --reload
```

Check Git status:

```powershell
git status
```

Check formatting-related whitespace errors:

```powershell
git diff --check
```

## Project Status

The NovaCart Customer Support Agent is a working prototype with:

- Policy retrieval
- Deterministic response generation
- Support intent handling
- Source references
- Confidence information
- Escalation fields
- Automated tests
- FastAPI API documentation

Further improvements may include better retrieval ranking, more support intents, real ticketing integration, live order lookup, human evaluation, and deployment.
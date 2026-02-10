# 🛒 AI Abandoned Cart Recovery Agent

A multi-step AI agent that automatically detects abandoned shopping carts and triggers personalized recovery actions using Elastic Agent Builder with Elasticsearch workflows.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🎯 Features

- **🤖 AI-Powered Detection**: Automatically identifies abandoned carts from real-time data
- **🎯 Smart Recovery**: Context-aware action selection based on customer segments
- **📊 Real-Time Analytics**: Complete recovery history and performance tracking
- **🛡️ Business Guardrails**: Risk-aware decision making with fraud protection
- **⚡ Serverless Ready**: Built for Elastic Serverless deployment
- **🔧 Extensible**: Easy to add new recovery strategies and integrations

---

## 📖 Agent Overview

The AI Abandoned Cart Recovery Agent is an intelligent e-commerce automation solution that addresses the critical problem of abandoned shopping carts, which costs businesses billions in lost revenue annually. Traditional approaches rely on generic discount blasts that waste margins and fail to address root causes, while this agent uses sophisticated AI-driven analysis to deliver personalized recovery strategies.

### Problem Solved

The agent solves the challenge of ineffective cart recovery by automatically detecting abandoned carts, diagnosing abandonment reasons, and selecting optimal recovery actions based on customer segmentation, fraud risk assessment, and cart value. Instead of one-size-fits-all solutions, it provides context-aware responses that balance revenue recovery with business risk management.

### Features Used

The solution leverages Elastic's complete serverless platform, including:

- **Elasticsearch** for real-time data correlation across cart events, checkout attempts, payment logs, and customer profiles
- **Elastic Workflows** engine orchestrates a complex multi-step process with conditional logic and foreach loops
- **AI Assistant** provides natural language interface and intelligent decision-making
- **Liquid templating** for dynamic content transformation
- **Recovery history** maintains a complete audit trail

### Key Highlights

The **serverless workflow orchestration** was particularly impressive - the ability to create sophisticated nested logic with foreach loops that process each abandoned cart individually while maintaining performance at scale.

The **AI Agent Builder integration** was another standout feature, allowing the complex workflow to be executed through simple natural language commands while maintaining business guardrails and safety constraints.

### Development Challenges

The main challenge was implementing the complex decision matrix that considers multiple variables (customer segment, abandonment reason, cart value, fraud risk) to select the optimal recovery action. This required careful design of the workflow's conditional logic and extensive testing to ensure all scenarios were handled correctly.

The result is a production-ready system that demonstrates how AI, workflows, and real-time analytics can work together to solve complex business problems with intelligence and efficiency.

---

## Hackathon pitch (2 minutes)

- **Problem:** E-commerce sites lose revenue when shoppers add items but never finish checkout. Generic "discount blasts" waste margin and miss root cause.
- **Solution:** An AI agent that correlates cart, checkout, payment, and performance signals in Elasticsearch, diagnoses abandonment cause, learns from past recoveries, and chooses least-intrusive, highest-success action.
- **Why Elastic Agent Builder:** The agent is defined as a serverless workflow with AI, guardrails, and learning—all orchestrated by Elastic AI Assistant.
- **Business impact:** Higher recovery rates, fewer unnecessary discounts, and a self-improving automation loop.

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Cart Events   │    │  Checkout Events │    │ Customer Profile│
│   (ES Index)    │    │   (ES Index)    │    │   (ES Index)    │
└────────┬────────┘    └────────┬─────────┘    └────────┬────────┘
         │                      │                        │
         └──────────────────────┼────────────────────────┘
                                │
                    ┌───────────▼───────────┐
                    │  Serverless Workflow     │
                    │                      │
                    │ 1. Detect Carts      │
                    │ 2. Analyze Signals   │
                    │ 3. Get Customer     │
                    │ 4. Decide Action     │
                    │ 5. Trigger Recovery  │
                    │ 6. Record Attempt    │
                    └───────────┬───────────┘
                                │
                    ┌───────────▼───────────┐
                    │  Recovery Actions     │
                    │  - Payment Retry     │
                    │  - Discount          │
                    │  - Free Shipping     │
                    │  - Reminder          │
                    └──────────────────────┘
```

---

## 🚀 Quickstart (Elastic Serverless)

### 1. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` with your Serverless details:
```env
ES_SERVERLESS_ENDPOINT=https://your-project-id.es.us-east-1.aws.elastic-cloud.com
ES_SERVERLESS_API_KEY=your-api-key
```

### 2. Install Dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Bootstrap Elasticsearch

```bash
python scripts/bootstrap_indices.py
python scripts/seed_sample_data.py
```

### 4. Import Workflow

1. Open your Serverless Kibana
2. Navigate to **Stack Management → Workflows**
3. Import `elastic_workflows/serverless_workflow.yml`
4. Enable the workflow

### 5. Create Agent

1. Go to **AI Assistants → Agent Builder**
2. Create new agent
3. Go to **Manage Tools** and create workflow tool
4. Select the workflow you imported
5. Go to agent and enable this tool

### 6. Test Agent

```
Detect abandoned carts in the last 24h, diagnose the top 3, and trigger the best recovery action.
```

---

## 📊 Project Documentation

For detailed technical documentation including:
- Elasticsearch index schemas and mappings
- Serverless workflow implementation
- Data flow diagrams
- Deployment guides
- Troubleshooting tips

See: **[docs/serverless_documentation.md](docs/serverless_documentation.md)**

---

## 📁 Repository Structure

```
├── elastic_workflows/
│   └── serverless_workflow.yml              # Complete serverless workflow with nested logic
├── agent_builder/
│   ├── serverless_agent.yaml                 # Agent definition
│   └── serverless_demo_script.md            # Demo script
├── scripts/
│   ├── bootstrap_indices.py                 # Create ES indices
│   └── seed_sample_data.py                  # Sample data
├── mappings/                               # ES index mappings
├── queries/                                # Pre-built ES queries (legacy - now in workflow)
└── docs/                                   # Technical documentation
    ├── serverless_documentation.md         # Complete architecture docs
    ├── serverless_workflow_diagram.md      # Workflow flow and decision logic
    ├── requirements_analysis.md            # Business requirements
    └── sample_data_reference.md            # Data structure reference
```

---

## 🔧 Development

### Add New Recovery Actions

1. Update the prompt in the workflow step
2. Add corresponding HTTP endpoint configuration
3. Update guardrails if needed

---

## 📈 Monitoring

Track recovery performance in Kibana:
- Recovery rate by action type
- Conversion by customer segment
- Revenue recovered per campaign

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Update tests and documentation
4. Submit a pull request

---

## 📄 License

MIT License - see LICENSE file for details

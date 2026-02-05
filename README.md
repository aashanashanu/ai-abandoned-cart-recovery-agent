# 🛒 AI Abandoned Cart Recovery Agent

**Hackathon-ready showcase:** A multi-step AI agent built with **Elastic Agent Builder** that diagnoses why shoppers abandon carts and automatically triggers best recovery action—turning lost revenue into recovered sales.

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
3. Go to manage tool and create workflow tool.
4. select the workflow you created.
5. Go to agent and enable this tool.

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
│   └── serverless_workflow.yml              # Serverless workflow
├── agent_builder/
│   ├── serverless_agent.yaml                 # Agent definition
│   ├── serverless_demo_script.md            # Demo script
│   └── serverless_setup_guide.md             # Setup guide
├── docs/
│   ├── serverless_documentation.md          # Complete technical docs
│   └── serverless_workflow_diagram.md       # Workflow diagrams
├── scripts/
│   ├── bootstrap_indices.py                 # Create ES indices
│   └── seed_sample_data.py                  # Sample data
├── mappings/                               # ES index mappings
├── queries/                                # Pre-built ES queries (legacy)
└── .env.example                            # Environment template
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

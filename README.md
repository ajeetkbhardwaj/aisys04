This is the perfect progression. We are moving from "Alfred," a linear helper, to a **Stateful, Multi-Agent Corporate System** with **Human-in-the-Loop** controls.

Copy and paste the following **Product Specification** into your Agentic IDE (Cursor/Windsurf). It translates the "Logistics Damage Claims" business case into a concrete coding plan using **LangGraph**.

---

# 📋 Project Prompt: Enterprise Logistics Claims Agent (LangGraph)

**Goal:** Build a production-grade **LangGraph** application that automates logistics damage claims. It must handle multi-modal input (images), query a database (SQL), enforce policy (RAG/Logic), and pause for human manager approval when high-value refunds are detected.

## 🏗️ 1. Technical Stack

* **Orchestration:** LangGraph (StateGraph, Checkpointers).
* **LLM:** `gpt-4o` (for Vision and Reasoning).
* **Database:** `sqlite3` (Simulated Orders DB).
* **Vector Store:** `ChromaDB` (or a simple in-memory retriever for Policy).
* **Observability:** Langfuse (via CallbackHandler).
* **Persistence:** LangGraph `MemorySaver` (to handle Human-in-the-loop state).

## 📂 2. Project Structure

```text
.
├── main.py                # Entry point & Graph definition
├── state.py               # TypedDict definitions (ClaimState)
├── nodes/                 # Graph Nodes
│   ├── vision_node.py     # GPT-4o Image Analysis
│   ├── crm_node.py        # SQLite Order Lookup
│   ├── logic_node.py      # Policy checking
│   └── human_node.py      # Manager Review logic
├── tools/                 # Tool definitions
│   └── db_tools.py        # SQL interactions
├── data/                  # Dummy images and policy.txt
└── .env                   # OPENAI_API_KEY, LANGFUSE_KEYS
```

## 🛠️ 3. Implementation Requirements

### Phase 1: State & Data Foundations

1. **State Definition (`state.py`):**
   Create a `ClaimState(TypedDict)` that tracks:

   * `claim_id`: str
   * `user_email`: str
   * `image_path`: str
   * `is_valid_damage`: bool (Result of Vision Node)
   * `damage_description`: str
   * `order_value`: float (Result of CRM Node)
   * `customer_tier`: str (VIP/Regular)
   * `refund_status`: str (Pending/Approved/Rejected)
   * `messages`: list[AnyMessage]
2. **Database Setup:**
   Create a helper in `tools/db_tools.py` that initializes a SQLite DB with dummy orders:

   * `ORD-123`: Value $1500 (Requires approval).
   * `ORD-456`: Value $50 (Auto-approve).

### Phase 2: The Nodes (Agents)

1. **`vision_node`:**

   * Accepts `image_path`.
   * Uses `gpt-4o` to analyze the image.
   * Updates state: `is_valid_damage` (True/False) and `damage_description`.
2. **`crm_node`:**

   * Uses `claim_id` to query SQLite.
   * Updates state: `order_value` and `customer_tier`.
3. **`logic_node` (The Supervisor):**

   * **Rule 1:** If `is_valid_damage` is False -> Route to **End** (Reject).
   * **Rule 2:** If `order_value` > $1000 -> Route to **Human Review**.
   * **Rule 3:** If `order_value` < $1000 AND `is_valid_damage` is True -> Route to **Auto Refund**.

### Phase 3: The Graph & Human-in-the-Loop

1. **Graph Construction:**

   * Initialize `StateGraph(ClaimState)`.
   * Add nodes: `vision`, `crm`, `logic`, `refund`.
   * Edge: `START` -> `vision` -> `crm` -> `logic`.
   * **Conditional Edge:** From `logic`, route to either `refund` or `END` based on the rules above.
2. **The Interrupt:**

   * When compiling the graph, set `interrupt_before=["refund"]` **ONLY IF** the logic node flags it for review.
   * *Implementation Detail:* Actually, simpler approach for LangGraph: Create a specific node called `human_review`. Route high-value claims there. Set `interrupt_before=["human_review"]`.

### Phase 4: Execution Script (`main.py`)

Create a script that simulates the lifecycle:

1. **Run 1 (The Bot):** Start the graph with a High Value claim ($1500).
   * *Expected Result:* The graph runs Vision, runs CRM, sees $1500, and **pauses** at `human_review`.
2. **Run 2 (The Manager):** The script simulates a manager saying "Approve".
   * Use `graph.update_state()` to inject `refund_status="Approved"`.
   * Resume execution.
   * *Expected Result:* The graph proceeds to `refund` and finishes.

---

## ⚠️ Constraints

* **Vision:** If you don't have a real image, mock the `vision_node` to accept a text description of the image for now, OR use a base64 placeholder.
* **Security:** Ensure `OPENAI_API_KEY` is loaded from `.env`.
* **Observability:** Wrap the graph invocation in the `Langfuse` callback handler.

---

Act on this project.

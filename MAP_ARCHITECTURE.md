# MAP (Multi-App Agent Protocol) Architecture Plan

## What is MAP?

MAP is a cousin to MCP (Model Context Protocol). While MCP handles LLM ↔ Tool communication, MAP handles **agent identity across external integrations**.

MAP solves the "teammate problem" - making Aleq appear as a first-class agent/teammate in platforms like ClickUp, Monday.com, Asana, etc. that don't natively support agent users the way Linear does.

## The Problem MAP Solves

**Linear Example (Native Agent Support):**

- Linear has `actor=app` OAuth parameter
- Creates a real agent user automatically
- Agent can be @mentioned, assigned tasks
- Shows up as distinct user in audit logs
- Clean, native experience

**ClickUp/Monday/Asana (No Native Support):**

- Standard OAuth only gives impersonation (actions appear as human user)
- No way to create bot user programmatically
- No native @mentions or assignments for agents
- Aleq's actions look like human actions

**MAP bridges this gap by providing two modes:**

1. **Impersonation Mode** - Free, automatic, 70% experience (uses polyfill)
2. **Bot User Mode** - Manual setup, 95% experience (native platform features)

---

## The 4 Layers of MAP

### **Layer 1: Platform Connectors** (Already Exists)

**What it does:**

- Direct API integration with each platform
- Files: `app/connectors/linear.py`, `app/connectors/clickup.py`, `app/connectors/monday.py`
- Handles OAuth flows, API calls, token management
- Pure execution - no abstraction

**Status:** ✅ Complete for Linear, ClickUp, Monday.com

---

### **Layer 2: Schema Mapping**

**What it does:**

- Translates universal Aleq commands into platform-specific API calls
- Example: `priority: "high"` → ClickUp uses `1`, Monday uses `"High"`, Linear uses `"urgent"`
- Maps workspace concepts across platforms
- Bidirectional translation (platform → universal for webhooks)

**Where it lives:** New file `app/map_layer.py`

**Example:**

```
MIND says: "Create task with high priority in workspace X"
Layer 2 translates:
- ClickUp: {"list_id": "123", "priority": 1}
- Monday: {"board_id": "456", "column_values": {"priority": "High"}}
- Linear: {"teamId": "789", "priority": 1}
```

**Status:** ❌ Not implemented yet

---

### **Layer 3: Identity Polyfill** (The "Retrofit Kit")

**What it does:**

- Makes Aleq APPEAR as an agent on platforms without native support
- ONLY runs in **impersonation mode**
- Uses conventions to fake agent behavior

**Conventions:**

- **Signatures:** Prepend "🤖 Created by Aleq AI" to descriptions
- **Tags:** Add "aleq-automation" tag to all Aleq-created items
- **Assignment Detection:** Watch for "#aleq" tag or "assigned:aleq" in webhooks
- **Mention Detection:** Parse comments for "@aleq" pattern

**When it runs:**

- ✅ Impersonation mode: Inject signatures, tags, parse conventions
- ❌ Bot user mode: Skip entirely, use native platform identity

**Where it lives:** New file `app/map_layer.py`

**Status:** ❌ Not implemented yet

---

### **Layer 4: Bot User Provisioning** (Cross-Platform Identity)

**What it does:**

- Manages Aleq's bot user identity across ALL platforms
- Core concept: ONE email (aleq@domain.com) used everywhere
- Provides setup instructions per platform
- Tracks which platforms have bot user linked

**The Flow:**

1. User creates Gmail for bot: `aleq@dockwa.com`
2. User completes Gmail OAuth AS the bot account
3. User invites `aleq@dockwa.com` to ClickUp workspace
4. Bot accepts invite via Gmail inbox
5. User generates API token AS bot user in ClickUp
6. Repeat for Monday, Linear, Slack, etc.
7. ALL platforms now recognize `aleq@dockwa.com` as same identity

**What it stores:**

- Bot email per org (one identity per organization)
- Which platforms are linked
- Credential mode per platform (impersonation vs bot_user)

**Where it lives:** New file `app/bot_provisioning.py`

**Status:** ❌ Not implemented yet

---

## Does This Live in Stargate?

**THIS IS THE QUESTION I NEED ANSWERED:**

### Yes, All 4 Layers Live in Stargate

**Reasoning:**

- MAP is about EXTERNAL INTEGRATIONS (Stargate's job)
- Layer 1 already in Stargate (connectors)
- Layer 2-4 are extensions of connector behavior
- Stargate becomes "execution layer + identity layer"

**What this means:**

- Add `app/map_layer.py` to Stargate
- Add `app/bot_provisioning.py` to Stargate
- Add bot provisioning endpoints to `app/main.py`
- Store bot identities in Stargate database
- Add credential_mode tracking to existing credentials

---

## What Stargate Currently Does

**Stargate is "The Hands" - pure execution:**

- Takes commands from MIND
- Executes API calls to external platforms
- Returns results
- Stores credentials securely
- Handles OAuth flows

**Stargate does NOT:**

- Make decisions (MIND's job)
- Run workflows (LangGraph in MIND)
- Handle domain logic (OCR, calculations, reconciliation - MIND's job)

**MAP Question:**
Is agent identity management (Layers 2-4) considered "execution" or "orchestration"?

- If execution → Belongs in Stargate
- If orchestration → Belongs in MIND

---

## My Understanding (What I Think You Want)

**I believe you want Option A: All 4 Layers in Stargate**

**Why:**

1. MAP is about EXTERNAL INTEGRATIONS (Stargate's domain)
2. Layer 1 already exists in Stargate
3. Layers 2-4 are natural extensions of connector behavior
4. MIND shouldn't care about ClickUp vs Linear differences
5. MAP acts as translation layer between MIND and platforms

**This makes Stargate:**

- Platform Connectors (Layer 1)
- Schema Translator (Layer 2)
- Identity Manager (Layer 3-4)
- Pure execution + identity abstraction

**MIND stays focused on:**

- Business logic
- Workflows (LangGraph)
- Decision making
- Domain-specific operations (OCR, calculations, etc.)

---

## Next Steps IF This Lives in Stargate

**Create `app/map_layer.py`**

- [ ] Schema mapping logic (Layer 2)
- [ ] Identity polyfill logic (Layer 3)
- [ ] Platform conventions registry

**Create `app/bot_provisioning.py`**

- [ ] Bot identity management (Layer 4)
- [ ] Setup instruction generators
- [ ] Platform linking logic

**Update `app/main.py`**

- [ ] Add bot provisioning endpoints
- [ ] Add credential mode parameter to OAuth flows

**Database changes** (handled separately, not touching schema directly)

- [ ] Track bot identities per org
- [ ] Track credential_mode per credential
- [ ] Link credentials to bot email

**Update existing connectors**

- [ ] Call MAP layer before API calls
- [ ] Conditional polyfill based on credential_mode

---

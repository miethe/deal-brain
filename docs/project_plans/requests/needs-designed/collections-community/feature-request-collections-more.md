# Deal Brain – Community & Collections Feature Request Report (for AI PM Agents)

> **Purpose:** This document defines *what* we want to build and *why* for Deal Brain’s first community-centric release (pre–Black Friday) and subsequent phases.
> **Audience:** AI PM / Architect / Dev agents.
> **Scope:** Feature *ideas, value, and success criteria* only. No implementation details.
> **Author:** ChatGPT 5.1 Thinking

---

## 0) High-Level Objectives

* Turn Deal Brain from a **solo deal evaluator** into a **shared decision tool**.
* Allow users to:

  * Share **individual deals** (as “cards”) and **groups of deals** (collections).
  * Organize deals into **Collections** aligned to their goals (builds, watchlists, etc.).
  * Gradually evolve into a **community catalog** of high-quality, vetted deals.

Pre–Black Friday emphasis:

* **Sharing** + **Private Collections** + **Light public surface** (no heavy moderation needed yet).

---

## 1) Feature Group A – Sharing & Social Surfaces

### FR-A1: Shareable Deal Pages (“Deal Cards via Link”)

**Idea**
Each listing in Deal Brain should be shareable as a **public, read-only “deal page”**. When shared in chats or social media, it appears as a visually appealing “card” summarizing the deal and Deal Brain’s evaluation.

**User Intent / Stories (conceptual)**

* “I want to send my friend this deal *with* the Deal Brain verdict attached, not just the raw store link.”
* “I want to post a deal in Discord/Reddit and let people see why it scores well or poorly.”

**Why / Value**

* Introduces people to Deal Brain *through* real deals, not marketing pages.
* Makes the “Deal Brain Score + explanation” the core artifact people talk about.
* Creates a canonical public representation of a deal, reusable later in collections & community catalog.

**What Success Looks Like**

* Users frequently click **Share** on listings.
* Shared links generate:

  * Consistent previews across major platforms (Slack, Discord, X, etc.).
  * Measurable new traffic and sign-ups from these links.
* Early qualitative feedback: users say “this is the cleanest way to show people why a deal is good/bad.”

**Key Considerations (no implementation detail)**

* Privacy expectations (what can be shared publicly by default vs opt-in).
* Clear distinction between **store’s original listing** vs **Deal Brain’s analysis**.
* Basic trust: ensure content on public pages is accurate, non-misleading, and clearly time-stamped.

---

### FR-A2: Shareable Deal Card Images (Static Visuals)

**Idea**
Allow users to generate a **static visual card** (image) of a deal that includes key information and Deal Brain’s verdict, suitable for posting where link previews are weak or stripped.

**User Intent / Stories**

* “I want a nice image I can drop directly into a chat or a forum that shows the deal and score.”
* “I might be embarrassed to share a pure link; a neutral, branded card feels better.”

**Why / Value**

* Extends sharing to environments that don’t render link previews well.
* Increases brand visibility and makes the Deal Brain experience more tangible.
* Helps users quickly compare screenshots of multiple options.

**What Success Looks Like**

* Noticeable usage of “Download card” / “Copy image” actions.
* Screenshots of Deal Brain cards start appearing in communities where deals are discussed.
* Feedback from users that “it’s easier to convince others because the card is clear and compact.”

**Key Considerations**

* The card should be **legible and neutral**, not overly salesy.
* Needs to clearly show **time context** (e.g., “as of [date/time]”) because prices change.
* Should work well on both desktop and mobile screens.

---

### FR-A3: User-to-User Deal Sharing & Import (Structured Share)

**Idea**
Enable users to share deals **directly to another Deal Brain user** (or via a share link) such that the receiver can **preview, compare, and import** that deal into their own workspace/collections.

**User Intent / Stories**

* “My friend and I are planning a build; I want to send him three candidate deals *inside* Deal Brain so we can both work from the same baseline.”
* “I want to receive deals in a way that’s already normalized by Deal Brain, not raw URLs.”

**Why / Value**

* Supports **collaborative decision-making** around purchases.
* Reduces friction compared to sending raw URLs back and forth.
* Establishes the pattern for future **collaborative collections** and community curation.

**What Success Looks Like**

* Users regularly send deals to other users and import them.
* Pre–Black Friday: small but meaningful “share → import → organize” flows, especially among power users.
* Qualitative reports of “We used Deal Brain together to make our buying decision.”

**Key Considerations**

* Concept of a **“snapshot vs current state”**: user must understand that the shared deal may change over time (price, availability).
* Avoid confusion between:

  * “What Nick saw when sharing” vs
  * “What the deal looks like now.”
* Minimal abuse/spam risk management when sharing to specific users.

---

### FR-A4: Export / Import of Deals as Portable Artifacts

**Idea**
Provide a **portable representation of a deal** (and eventually collections) that can be exported and imported. Think of it as a “Deal Brain deal file” that captures the key facts and evaluation.

**User Intent / Stories**

* “I want to back up my evaluations, or attach them as files in a project doc.”
* “I want to share a deal with someone who might use Deal Brain later or in a different environment.”

**Why / Value**

* Supports **power users**, advanced workflows, and external analysis.
* Lets Deal Brain integrate into other tooling/workflows (docs, tickets, etc.) conceptually.
* Lays groundwork for offline/agent workflows where an agent can take a “deal artifact” and process it.

**What Success Looks Like**

* Users in technical communities mention exporting/importing deals as part of their workflow.
* Deal artifacts get reused as inputs to AI agents or external systems.
* Exported representations remain understandable across versions (with clear compatibility messaging).

**Key Considerations**

* Versioning of the conceptual deal format.
* Keeping representation focused on **facts + evaluation**, not implementation detail.
* Clear communication of “what is guaranteed to be present” vs optional enrichments.

---

### FR-A5: “Send to Collection” from Shared Items

**Idea**
When a user views a shared deal, they should be able to **quickly place it into an existing or new collection** as part of their decision-making.

**User Intent / Stories**

* “Someone sent me a deal; I want to instantly drop it into my ‘Black Friday 2025 SFF Candidates’ collection.”
* “Shared items should naturally become part of my organized comparison workflow.”

**Why / Value**

* Smooths the path from **discovery → evaluation → decision**.
* Strengthens both Sharing and Collections by linking them.
* Encourages a consistent mental model: “Everything lives in a collection when I’m deciding.”

**What Success Looks Like**

* High proportion of imported shared deals end up in collections.
* Collections become the default workspace for comparing shared deals.
* Users describe the flow as “frictionless” in feedback.

**Key Considerations**

* UX should make it obvious **what collection is being targeted** and allow simple creation of new ones.
* Avoid overwhelming the user with choices (especially if they have many collections).

---

## 2) Feature Group B – Collections (Organization & Comparison)

### FR-B1: Private Collections (User-Defined Groupings of Deals)

**Idea**
Allow users to create **Collections**: named groupings of deals aligned to their goals (e.g., builds, budgets, roles). Collections act as the primary way to organize and compare candidates.

**User Intent / Stories**

* “I want a collection for SFF gaming builds under $800, and another for Plex/NAS candidates.”
* “I want to compare 3–6 items side by side and take notes before deciding.”

**Why / Value**

* Transforms Deal Brain from a **single-deal evaluator** into a **decision workspace**.
* Mirrors how people actually make buying decisions: shortlist → compare → choose → buy.
* Encourages users to keep returning as their collections evolve or as prices change.

**What Success Looks Like**

* A significant portion of active users create ≥1 collection.
* Most deals that users care about long-term end up in collections.
* Users report that collections helped them reach a decision more confidently.

**Key Considerations**

* Collections must feel **flexible** (user can choose any organizing scheme: builds, budgets, use cases, time-bound events like “Black Friday 2025”).
* Per-item annotations (notes, statuses like “shortlisted”, “rejected”, “bought”) should be intuitive.
* A user may accumulate many collections; navigation and naming clarity matter.

---

### FR-B2: Collections Workspace View (Comparison & Notes)

**Idea**
Each collection should have a **dedicated workspace view** where users can see items in the collection, compare them conceptually, and record their thoughts.

**User Intent / Stories**

* “I want to see at a glance how these candidates differ in key dimensions (price, CPU, GPU, power, etc.).”
* “I want a space to write down pros/cons and keep track of my decision process.”

**Why / Value**

* Makes collections feel like a **tool**, not just a folder.
* Encourages deeper engagement with Deal Brain’s evaluation, not just the numeric score.
* Facilitates more thoughtful purchasing and fosters trust in the product.

**What Success Looks Like**

* Users spend meaningful time in collection workspaces (not just adding/removing items).
* Qualitative feedback that “this view helped me finalize my decision.”
* Collections are mentioned in user stories as their main “working surface.”

**Key Considerations**

* Must balance **information density** with **readability**; avoid overwhelming users.
* Consider the notion of a “primary lens” for comparison (e.g., price/perf, total cost, power draw, etc.).
* Support both casual users (simple list) and power users (deeper comparative detail) without overcomplicating.

---

### FR-B3: Shareable Collections (Unlisted & Public Read-Only)

**Idea**
Allow users to **share entire collections** via a public/unlisted link, so others can view the curated set and optionally copy it into their own workspace.

**User Intent / Stories**

* “I want to publish my ‘Top 5 SFF Plex Boxes for 2025’ and send it to my Discord.”
* “I want to share my build candidates with a friend so they can see everything I’m considering.”

**Why / Value**

* Turns users into **curators**, not just consumers.
* Provides a bridge between private organization and public/community content.
* Creates artifacts that can be embedded in content (blog posts, YT descriptions, forum threads).

**What Success Looks Like**

* Public/unlisted collections are shared externally and referenced in other communities.
* People copy popular collections into their own Deal Brain account as starting points.
* Over time, some collections become recognized as “canonical starting points” for common needs.

**Key Considerations**

* Visibility model: private (default), unlisted, public (discoverable).
* Clear communication when viewing a shared collection as a **guest vs logged-in user**.
* Need guardrails around inappropriate content/titles once sharing is public.

---

### FR-B4: Collaborative Collections (Multi-User Planning) – Later Phase

**Idea**
Allow multiple users to **collaborate on a single collection** with varying levels of access (view/comment/edit).

**User Intent / Stories**

* “Our Discord wants a shared ‘Best deals for homelab newbies’ list that a few of us can maintain.”
* “My friend and I want a shared build plan that we both can modify and annotate.”

**Why / Value**

* Enables **group decision-making** workflows.
* Encourages communities and influencers to adopt Deal Brain as their canonical planning space.
* Lays groundwork for a “team” concept in future (e.g., orgs, clubs).

**What Success Looks Like**

* Collections with multiple contributors become active hubs of editing and discussion.
* Entire groups adopt Deal Brain as “where we keep our build lists and deal plans.”
* Influencers or community leaders use collaborative collections as their “public-facing” working board.

**Key Considerations**

* Role clarity (who owns what, who can modify what).
* Conflict and change-management: avoid user confusion when items change or disappear.
* Abuse and moderation; avoid collaborative collections becoming spam vectors.

---

## 3) Feature Group C – Community Deals & Social Layer (Future-facing)

These are important for evolution but **not required** for initial pre–Black Friday MVP.

### FR-C1: Community Deal Catalog (User-Submitted Deals Directory)

**Idea**
Create a **community catalog** where users can publish deals (backed by Deal Brain evaluations) into a shared, browsable directory (e.g., “Trending Deals,” “Best in last 24h”).

**User Intent / Stories**

* “I found an amazing deal and want the whole community to see it, not just my friends.”
* “I want to browse deals others have found and let Deal Brain filter out the junk.”

**Why / Value**

* Turns Deal Brain into a **destination**, not just a tool.
* Leverages the crowd to find and surface deals, while relying on Deal Brain for the objective evaluation.
* Aligns perfectly with big events (Black Friday, Prime Day): “live deals feed” anchored on analysis, not hype.

**What Success Looks Like**

* Users regularly publish deals into the catalog.
* Catalog becomes a go-to page for active buyers during deal events.
* Community deals exhibit clear quality: high signal-to-noise ratio compared to raw deal subreddits.

**Key Considerations**

* Requires basic moderation strategy to handle spam, miscategorized items, and malicious links.
* Needs thoughtful ranking logic: recency, score, community signals (votes), etc.
* Affiliation considerations: how to handle affiliate links (user vs platform).

---

### FR-C2: Voting & Reputation (Quality Signals)

**Idea**
Allow simple **upvoting** (and possibly downvoting/flagging) of community deals and track basic **reputation** for contributors.

**User Intent / Stories**

* “I want to say ‘this was helpful’ or ‘this is a genuinely good deal’.”
* “I want to know which contributors consistently post strong deals.”

**Why / Value**

* Helps users navigate the catalog by surfacing **highly endorsed** deals.
* Encourages better submissions by rewarding good curators.
* Creates the possibility of “Top curators” or “trusted contributors” later.

**What Success Looks Like**

* Deals show varied engagement; some clearly stand out as “community favorites.”
* Users pay attention to basic reputation metrics when evaluating deals.
* Low-value or spam deals tend to be suppressed via low votes/flags.

**Key Considerations**

* Distinguish between “upvotes” as **quality signals** vs resets or popularity contests.
* Keep model simple initially: avoid complex karma/XP systems early on.
* Anti-abuse: prevent users from gaming the system easily.

---

### FR-C3: Profiles, Following, and Notifications (Social Graph – Later)

**Idea**
Introduce **user profiles** that highlight their best deals/collections and provide optional **following** and **notifications** for new contributions.

**User Intent / Stories**

* “I want to see all deals and collections from this person; they consistently find stuff I like.”
* “I want to be notified when new deals appear that match my interests or when my favorite curator posts something.”

**Why / Value**

* Creates **ongoing engagement** loops: users return not just for themselves, but for others’ activity.
* Encourages the emergence of **trusted curators** and community leaders.
* Bridges Deal Brain into a **semi-social platform** around deal intelligence.

**What Success Looks Like**

* Users follow a small set of curators; those curators become influential in what people buy.
* Notifications drive meaningful return visits and conversions, especially around major events.
* Profiles become a recognizable part of Deal Brain’s identity.

**Key Considerations**

* Must respect user privacy and notification preferences.
* Needs thoughtful defaults to avoid spamming users.
* Should be clearly additive, not required; casual users should not feel forced into a social graph.

---

## 4) Success Metrics (Conceptual, Not Implementation)

For AI PM agents to translate into measurable KPIs:

* **Sharing**

  * % of evaluated deals that are shared at least once.
  * New-user acquisition attributed to shared links/pages.
  * Qualitative feedback: user comments about how sharing helped them coordinate purchases.

* **Collections**

  * % of active users with ≥1 collection and ≥3 items in a collection.
  * Frequency of actions within collections: add/remove items, notes, status changes.
  * Self-reported usefulness: “Collections helped me decide what to buy.”

* **Community (later)**

  * Number of community-deal submissions per day/week.
  * Ratio of “highly engaged” deals vs total submissions.
  * Emerging curators (users whose deals consistently see high engagement).

---

## 5) Strategic Phasing Guidance (For PM Agents)

**Phase 1 – Pre–Black Friday (High Priority)**

* FR-A1: Shareable deal pages.
* FR-A3/FR-A5: User-to-user share & import into collections.
* FR-B1/FR-B2: Private collections + workspace view (minimal but usable).

**Phase 2 – Post–Black Friday (Medium Priority)**

* FR-B3: Shareable collections (unlisted/public).
* FR-A2/FR-A4: Static card images & portable deal artifacts.

**Phase 3 – Community Layer (Longer-Horizon)**

* FR-C1: Community deal catalog.
* FR-C2: Voting & basic reputation.
* FR-B4: Collaborative collections.
* FR-C3: Profiles, following, notifications.

// The real output of the projectwright scripts on a sample project.
// Written by make_contract.py: do not edit; run it again after changing the scripts.

export const TASKS: Record<string, unknown>[] = [
  {
    "task": "[[T-PRJ-0001-release-notes]]",
    "progress": "done",
    "priority": "medium",
    "phase": "sprint-1",
    "assignee": "maintainer",
    "title": "Release notes"
  },
  {
    "task": "[[T-WEB-0001-checkout-page]]",
    "progress": "in-progress",
    "priority": "high",
    "phase": "sprint-1",
    "assignee": "frontend developer",
    "title": "Checkout page"
  },
  {
    "task": "[[T-WEB-0002-payment-step]]",
    "progress": "todo",
    "priority": "medium",
    "phase": "sprint-1",
    "assignee": "frontend developer",
    "title": "Payment step"
  },
  {
    "task": "[[T-WEB-0003-order-history]]",
    "progress": "blocked",
    "priority": "low",
    "phase": "sprint-2",
    "assignee": "",
    "title": "Order history"
  },
  {
    "task": "[[T-WEB-0004-old-cart]]",
    "progress": "cancelled",
    "priority": "low",
    "phase": "",
    "assignee": "",
    "title": "Old cart"
  }
]

export const DETAILS: Record<string, Record<string, unknown>> = {
  "T-WEB-0001-checkout-page": {
    "title": "Checkout page",
    "type": "task",
    "id": "T-WEB-0001",
    "area": "WEB",
    "progress": "in-progress",
    "priority": "high",
    "phase": "sprint-1",
    "assignee": "frontend developer",
    "created": "2026-01-12",
    "updated": "2026-01-19",
    "closed_on": null,
    "decisions": [],
    "questions": [],
    "blocked_by": [],
    "commits": [],
    "name": "T-WEB-0001-checkout-page",
    "path": "wiki/components/web/tasks/T-WEB-0001-checkout-page.md",
    "component": "WEB",
    "body": "# T-WEB-0001 — Checkout page\n\n**Goal** — A checkout page that leads to [[T-WEB-0002-payment-step]].\n\n**Acceptance criteria**\n- The customer sees the order before paying.\n\n**Notes** — Part of [[web]].\n",
    "links": [
      "T-WEB-0002-payment-step",
      "web"
    ]
  },
  "T-WEB-0002-payment-step": {
    "title": "Payment step",
    "type": "task",
    "id": "T-WEB-0002",
    "area": "WEB",
    "progress": "todo",
    "priority": "medium",
    "phase": "sprint-1",
    "assignee": "frontend developer",
    "created": "2026-01-12",
    "updated": "2026-01-19",
    "closed_on": null,
    "decisions": [],
    "questions": [],
    "blocked_by": [],
    "commits": [],
    "name": "T-WEB-0002-payment-step",
    "path": "wiki/components/web/tasks/T-WEB-0002-payment-step.md",
    "component": "WEB",
    "body": "# T-WEB-0002 — Payment step\n\n**Goal** — The payment step of the checkout.\n\n**Acceptance criteria**\n- A failed payment can be tried again.\n\n**Notes** — After [[T-WEB-0001-checkout-page]].\n",
    "links": [
      "T-WEB-0001-checkout-page"
    ]
  },
  "T-WEB-0003-order-history": {
    "title": "Order history",
    "type": "task",
    "id": "T-WEB-0003",
    "area": "WEB",
    "progress": "blocked",
    "priority": "low",
    "phase": "sprint-2",
    "assignee": null,
    "created": "2026-01-12",
    "updated": "2026-01-19",
    "closed_on": null,
    "decisions": [],
    "questions": [],
    "blocked_by": [
      "[[T-WEB-0002-payment-step]]"
    ],
    "commits": [],
    "name": "T-WEB-0003-order-history",
    "path": "wiki/components/web/tasks/T-WEB-0003-order-history.md",
    "component": "WEB",
    "body": "# T-WEB-0003 — Order history\n\n**Goal** — The customer's past orders.\n\n**Acceptance criteria**\n- Orders are listed newest first.\n\n**Notes** — None.\n",
    "links": [
      "T-WEB-0002-payment-step"
    ]
  },
  "T-WEB-0004-old-cart": {
    "title": "Old cart",
    "type": "task",
    "id": "T-WEB-0004",
    "area": "WEB",
    "progress": "cancelled",
    "priority": "low",
    "phase": null,
    "assignee": null,
    "created": "2026-01-12",
    "updated": "2026-01-19",
    "closed_on": "2026-01-15",
    "decisions": [],
    "questions": [],
    "blocked_by": [],
    "commits": [],
    "name": "T-WEB-0004-old-cart",
    "path": "wiki/components/web/tasks/T-WEB-0004-old-cart.md",
    "component": "WEB",
    "body": "# T-WEB-0004 — Old cart\n\n**Goal** — The cart of the first version.\n\n**Acceptance criteria**\n- None.\n\n**Notes** — Replaced by the checkout page.\n",
    "links": []
  },
  "T-PRJ-0001-release-notes": {
    "title": "Release notes",
    "type": "task",
    "id": "T-PRJ-0001",
    "area": "PRJ",
    "progress": "done",
    "priority": "medium",
    "phase": "sprint-1",
    "assignee": "maintainer",
    "created": "2026-01-12",
    "updated": "2026-01-19",
    "closed_on": "2026-01-19",
    "decisions": [],
    "questions": [],
    "blocked_by": [],
    "commits": [],
    "name": "T-PRJ-0001-release-notes",
    "path": "wiki/tasks/T-PRJ-0001-release-notes.md",
    "component": null,
    "body": "# T-PRJ-0001 — Release notes\n\n**Goal** — Notes for the first release.\n\n**Acceptance criteria**\n- Every change is listed.\n\n**Notes** — None.\n",
    "links": []
  }
}

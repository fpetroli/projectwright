// The real output of the projectwright scripts on a sample project, and the board model.
// Written by make_contract.py: do not edit; run it again after changing the scripts.

export const TASKS: Record<string, unknown>[] = [
  {
    "task": "[[T-PRJ-0001-release-notes]]",
    "progress": "done",
    "priority": "medium",
    "phase": "sprint-1",
    "assignee": "maintainer",
    "title": "Release notes",
    "id": "T-PRJ-0001",
    "updated": "2026-01-19",
    "closed_on": "2026-01-19",
    "blocked_by": ""
  },
  {
    "task": "[[T-WEB-0001-checkout-page]]",
    "progress": "in-progress",
    "priority": "high",
    "phase": "sprint-1",
    "assignee": "frontend developer",
    "title": "Checkout page",
    "id": "T-WEB-0001",
    "updated": "2026-01-19",
    "closed_on": "",
    "blocked_by": ""
  },
  {
    "task": "[[T-WEB-0002-payment-step]]",
    "progress": "todo",
    "priority": "medium",
    "phase": "sprint-1",
    "assignee": "frontend developer",
    "title": "Payment step",
    "id": "T-WEB-0002",
    "updated": "2026-01-19",
    "closed_on": "",
    "blocked_by": ""
  },
  {
    "task": "[[T-WEB-0003-order-history]]",
    "progress": "blocked",
    "priority": "low",
    "phase": "sprint-2",
    "assignee": "",
    "title": "Order history",
    "id": "T-WEB-0003",
    "updated": "2026-01-19",
    "closed_on": "",
    "blocked_by": "T-WEB-0002-payment-step"
  },
  {
    "task": "[[T-WEB-0004-old-cart]]",
    "progress": "cancelled",
    "priority": "low",
    "phase": "",
    "assignee": "",
    "title": "Old cart",
    "id": "T-WEB-0004",
    "updated": "2026-01-19",
    "closed_on": "2026-01-15",
    "blocked_by": ""
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

export const MODEL: Record<string, unknown> = {
  "_comment": "What the two boards show, defined once: board.html (scripts/board.py) and the pane of projectwright-board read this file. Colors are names; each board turns them into its own palette. Tasks are in ID order; the history columns show the newest first.",
  "columns": [
    {
      "progress": "in-progress",
      "label": "In progress",
      "color": "blue"
    },
    {
      "progress": "blocked",
      "label": "Blocked",
      "color": "red"
    },
    {
      "progress": "todo",
      "label": "To do",
      "color": "gray"
    },
    {
      "progress": "done",
      "label": "Done",
      "color": "green"
    },
    {
      "progress": "cancelled",
      "label": "Cancelled",
      "color": "gray"
    }
  ],
  "hide_when_empty": [
    "cancelled"
  ],
  "history": {
    "columns": [
      "done",
      "cancelled"
    ],
    "shown": 3,
    "newest_first": true
  },
  "priorities": [
    {
      "value": "high",
      "label": "High",
      "color": "red"
    },
    {
      "value": "medium",
      "label": "Medium",
      "color": "yellow"
    },
    {
      "value": "low",
      "label": "Low",
      "color": "gray"
    }
  ],
  "card": [
    "title",
    "id",
    "priority",
    "assignee",
    "blocked_by"
  ],
  "table": [
    "title",
    "id",
    "progress",
    "priority",
    "phase",
    "assignee",
    "updated"
  ],
  "detail": [
    "progress",
    "priority",
    "phase",
    "assignee",
    "created",
    "updated",
    "closed_on",
    "blocked_by"
  ],
  "fields": {
    "title": "Name",
    "id": "ID",
    "progress": "Status",
    "priority": "Priority",
    "phase": "Phase",
    "assignee": "Assignee",
    "created": "Created",
    "updated": "Updated",
    "closed_on": "Closed on",
    "blocked_by": "Blocked by"
  }
}

export const PROPOSALS: Record<string, unknown>[] = [
  {
    "id": "P-0001",
    "kind": "create",
    "summary": "Address book",
    "why": "The checkout asks for an address every time.",
    "items": [
      {
        "title": "Address book",
        "priority": "medium"
      }
    ],
    "status": "open",
    "created": "2026-01-20T10:00:00",
    "updated": "2026-01-20T10:00:00"
  },
  {
    "id": "P-0002",
    "kind": "move",
    "task": "T-WEB-0003-order-history",
    "summary": "Blocked -> To do",
    "why": "The payment step is done.",
    "changes": {
      "progress": "todo"
    },
    "status": "revising",
    "created": "2026-01-20T10:00:00",
    "updated": "2026-01-20T10:00:00",
    "comment": "Not blocked: later"
  },
  {
    "id": "P-0003",
    "kind": "split",
    "task": "T-WEB-0002-payment-step",
    "summary": "Split the payment step in two",
    "why": "Cards and bank transfers go to different providers.",
    "items": [
      {
        "title": "Card payments"
      },
      {
        "title": "Bank transfers"
      }
    ],
    "status": "open",
    "created": "2026-01-20T10:00:00",
    "updated": "2026-01-20T10:00:00"
  },
  {
    "id": "P-0004",
    "kind": "close",
    "task": "T-WEB-0001-checkout-page",
    "summary": "In progress -> Done",
    "why": "Its criteria are met.",
    "consolidation": "How the checkout works moves to the note of the web component.",
    "status": "open",
    "created": "2026-01-20T10:00:00",
    "updated": "2026-01-20T10:00:00"
  },
  {
    "id": "P-0005",
    "kind": "remind",
    "summary": "Ask the provider for test cards",
    "why": "The payment step needs them.",
    "items": [
      {
        "title": "Ask the provider for test cards",
        "due": "2026-01-26"
      }
    ],
    "status": "open",
    "created": "2026-01-20T10:00:00",
    "updated": "2026-01-20T10:00:00"
  }
]

export const REMINDERS: Record<string, unknown>[] = [
  {
    "id": "R-0001",
    "text": "Send the release notes to the reviewers",
    "due": "2026-01-23",
    "created": "2026-01-20"
  },
  {
    "id": "R-0002",
    "text": "Renew the payment provider key",
    "created": "2026-01-20"
  },
  {
    "id": "R-0003",
    "text": "Book the demo",
    "due": "2026-01-21",
    "created": "2026-01-20",
    "done_on": "2026-01-20"
  }
]

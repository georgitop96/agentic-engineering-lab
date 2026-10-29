# Repository instructions

This repository contains publicly reproducible AI applications. Optimize for
useful software that another engineer can install, run, test, and understand.

## Working principles

- Inspect the repository and Git status before changing files.
- Keep changes small, focused, and easy to review.
- Prefer simple explicit interfaces over premature frameworks.
- Separate prompts, model adapters, application logic, retrieval, and external
  integrations.
- Treat PDFs, retrieved text, prompts, tool inputs, and model outputs as
  untrusted data.
- Validate model output before using it in important operations.
- Document assumptions, limitations, failure modes, cost, latency, and privacy.
- Mark planned behavior as planned; do not claim features that are not tested.

## Python and dependencies

- Use Python 3.12 and `uv` as the baseline.
- Use the repository or project environment explicitly; do not rely on shell
  activation persisting between commands.
- Check existing dependencies before adding another package.
- Explain why a new dependency is needed and update the relevant project
  configuration and lock file.
- Never install global tools or silently upgrade unrelated packages.

## Testing and verification

- Add tests for business logic, parsing, retrieval, citations, persistence,
  error handling, and state transitions when applicable.
- Keep CI deterministic and free of live model calls, network dependencies,
  secrets, and paid services.
- Use fakes or fixtures for model providers and external services.
- Run focused tests, formatting/linting, and type checks when configured.
- Report exactly what was run and what remains uncertain.

## AI and financial safety

- Keep document evidence separate from trusted application instructions.
- Defend against prompt injection in retrieved documents.
- Prefer extractive or evidence-constrained answers when possible.
- Include citations and an insufficient-evidence response path.
- Do not provide investment advice or take financial actions.
- Do not add tools that send messages, change records, trade, spend money, or
  deploy infrastructure without explicit user approval and a confirmation step.

## Permissions and approvals

Work independently on bounded, approved repository changes and verify them.
Require user approval before:

- publishing, pushing, or connecting a remote;
- destructive operations, deletion, history rewriting, or force-pushes;
- deployment or infrastructure changes;
- paid API calls or sending user data to an external service;
- external side effects such as messages, record changes, or transactions.

Never commit secrets, credentials, private documents, `.env` files, virtual
environments, local indexes, or generated artifacts.

## Completion report

Every completed task should state:

1. what changed;
2. why it changed;
3. tests and checks run;
4. assumptions made;
5. remaining risks and recommended next steps.

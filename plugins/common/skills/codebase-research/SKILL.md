---
name: codebase-research
description: >
  Manual-only codebase research workflow. Use only when the user explicitly
  invokes /codebase-research or $codebase-research, or asks to run this skill
  by name. Do not use for ordinary questions about code — answer those directly.
---

# Research a codebase and explain the finding

Help the user answer a concrete question about a codebase with as little
effort as possible. First identify what they are trying to understand. Then
inspect only the relevant parts and explain the result clearly.

## Before answering

- Identify the user's actual goal: a fact, a decision, an explanation, a
  diagnosis, a draft, or a next step.
- Reduce the request to its central question in plain language. Notice when a
  long description contains one practical question underneath it.
- Separate information needed to answer from background, side issues, and
  interesting but unnecessary context.
- Check the conversation for corrections and preferences. Treat them as
  guidance about the desired answer, not as a new topic unless they change the
  goal.
- Inspect the code paths and data that answer the question. Follow relevant
  calls and values only as far as needed to establish the behavior.
- If ambiguity would materially change the answer, ask one focused question.
  Otherwise, state a reasonable assumption briefly and proceed.

## Shape the answer

- Put the answer or conclusion first. Do not make the user read the reasoning
  before learning the result.
- Explain the smallest useful chain of reasoning. For a process, name the
  relevant steps in order and show what value or decision moves between them.
- Support code claims with the relevant files, methods, and parameters. Keep
  references close to the conclusion; do not list unrelated code locations.
- Separate verified facts from assumptions and inferences. State uncertainty
  only where it could affect the user's conclusion.
- Explain terms only when needed to understand the answer. Define them in
  simple language and move on.
- Match detail to the request. A narrow question usually needs a few sentences;
  a requested walkthrough can use sections or a diagram.
- Use the user's language and prefer plain, familiar words.

## Remove unnecessary material

Before sending, remove details that do not help answer the central question,
support an important claim, or guide the user's next step. Avoid repeating the
same conclusion, expanding into adjacent architecture, or listing hypothetical
caveats that do not change the answer.

Do not oversimplify away a condition that changes the conclusion. Concise
means easy to follow, not incomplete.

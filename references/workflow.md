# Review and delivery workflow

## Knowledge check

For a user's self-explanation, split the prose into atomic claims. Preserve the user's wording in the review, then state the corrected version. A claim is `无法判断` when the available context is insufficient; it is not a reason to silently guess.

## Draft gate

The draft is the review boundary. It should be short enough to inspect in one message and detailed enough to catch a wrong premise, missing topic, or unsuitable card mode. Ask for confirmation through the normal conversation; the renderer does not provide a second confirmation prompt.

## Choosing a mode

- Use `quick_check` when the goal is recall under interview pressure: definitions, lists, one-to-one mappings, comparisons, and “what does X mean?” prompts.
- Use `explanation` when the goal is understanding: mechanisms, causal relationships, examples, trade-offs, and common mistakes.
- If the user requests both, create separate groups and label them clearly. Do not merge their content into a single PNG.

## Caption

The caption is a short, factual introduction for social sharing. It should name the topic, describe the recall value, and optionally include a compact call to save or review the card. Do not add claims absent from the cards.

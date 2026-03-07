# Checklist for Diagnostic Bot Core - Author Self-Check

**Purpose**: This checklist is designed for the author to self-check the requirements for the Diagnostic Bot Core, with a focus on user-facing features and detailed edge cases.
**Created**: 2026-03-07

---

## Requirement Completeness

- [ ] CHK001 - Are the requirements for handling unsupported file formats (e.g., PDF, Word document, video) fully specified? [Gap]
- [ ] CHK002 - Are the requirements for handling images that are too large for Telegram's limits or the local API's payload limits fully specified? [Gap]
- [ ] CHK003 - Are the requirements for handling multiple images sent in a single batch (album) fully specified? [Gap]
- [ ] CHK004 - Is the behavior of the `/clear` command fully defined (e.g., confirmation message)? [Completeness, Spec §FR-008]
- [ ] CHK005 - Are the requirements for the initial message a user receives upon first interacting with the bot defined? [Gap]

## Requirement Clarity

- [ ] CHK006 - Is the 30-second timeout for local server unreachability or processing clearly defined as a maximum limit? [Clarity, Spec §FR-006]
- [ ] CHK007 - Is the definition of "24 hours of inactivity" for session clearing specified (e.g., time since last message)? [Clarity, Spec §FR-008]
- [ ] CHK008 - Is the "diagnostic report" content and format specified? [Clarity, User Story 2]
- [ ] CHK009 - Is the term "coherent" in the text-based medical query user story defined with measurable criteria? [Clarity, User Story 1]

## Scenario Coverage

- [ ] CHK010 - Are the scenarios for a user manually clearing their session via `/clear` command fully documented? [Coverage, Spec §FR-008]
- [ ] CHK011 - Are the requirements for the bot's response when a user sends an unsupported file format specified? [Coverage, Edge Case]
- [ ] CHK012 - Are the requirements for the bot's response when a user sends an image that is too large specified? [Coverage, Edge Case]
- [ ] CHK013 - Are the requirements for the bot's response when a user sends multiple images in a batch specified? [Coverage, Edge Case]
- [ ] CHK014 - Is the scenario where a user sends a text message while an image is still being processed covered? [Coverage, Gap]

## Acceptance Criteria Quality

- [ ] CHK015 - Can the "coherent responses" for text and image interactions be objectively measured? [Measurability, Spec §SC-001]
- [ ] CHK016 - Is the "clear error notification" for server disconnection defined in terms of content and format? [Measurability, Spec §SC-002]

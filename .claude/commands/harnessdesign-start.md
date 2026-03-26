Read and follow the Skill SOP at `.harnessdesign/knowledge/skills/harnessdesign-router.md`.

This is the main entry point for the HarnessDesign AI-UX Workflow. The router will:
1. Check if onboarding is needed (Phase 0)
2. Invite the designer to provide task input (verbal description / upload PRD / both)
3. Create a task subfolder and initialize task-progress.json
4. Dispatch to the correct phase based on state

If the user provided arguments: $ARGUMENTS

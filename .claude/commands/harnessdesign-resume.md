Read and follow the Skill SOP at `.harnessdesign/knowledge/skills/harnessdesign-router.md`.

Resume an existing HarnessDesign task. The router will:
1. Read task-progress.json from the specified task folder to restore state
2. Dispatch to the correct phase based on current_state
3. Recall relevant archives from .harnessdesign/memory/sessions/ if needed

Task to resume: $ARGUMENTS

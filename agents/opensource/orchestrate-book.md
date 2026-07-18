# Master Orchestrator Script: 20-Page Self-Healing Pipeline Book

## Context Configuration
- Target Length: 20 Pages (~6,000 words)
- Narrative Voice: First-person authoritative expert, founder/operator perspective
- Agent Files: `./book-co-author.md`, `./data-engineer.md`, `./ai-data-remidation-engineer.md`
- Output Directory: `./book_output/`

## Step 1: Structural Initialization (Phase 1)
1. Call `book-co-author.md`. Feed it the author's raw ideas, transcripts, or notes.
2. Instruct the agent to generate an explicit `table_of_contents.md` targeting exactly 20 pages across 5-6 logical chapters.
3. Every chapter outline must explicitly declare:
   - A target page count budget (e.g., Chapter 1: 3 pages)
   - Core data engineering infrastructure to cover
   - Core AI-remediation architecture to cover
4. **CRITICAL:** Pause the CLI tool and wait for the author to reply with `APPROVED`.

## Step 2: Sequential Technical Drafting Loop (Phases 2 & 3)
For each chapter defined in the approved `table_of_contents.md`, execute the following sequentially:

1. **Invoke Technical Foundation:** 
   Pass the chapter objective to `data-engineer.md`. Instruct it to generate the production-grade pipeline architecture, lakehouse schemas, and code blocks (e.g., PySpark, dbt models) required for this section of the book. Save output as `.tmp_infra_specs`.

2. **Invoke Remediation Layer:** 
   Pass the same chapter objective and `.tmp_infra_specs` to `ai-data-remidation-engineer.md`. Instruct it to inject the self-healing layers: anomaly capture, air-gapped local SLM configurations, semantic clustering techniques, and zero-data-loss rollback loops using Ollama. Save output as `.tmp_remediation_specs`.

3. **Invoke Narrative Synthesis:**
   Pass `.tmp_infra_specs` and `.tmp_remediation_specs` to `book-co-author.md`. Instruct it to synthesize these highly technical documents into the book's established first-person voice. 
   - Ensure code snippets are clean and heavily commented.
   - Maintain the page budget allocated in Step 1.
   - Output the raw text to `./book_output/chapter_[X].md`.

## Step 3: Human-in-the-Loop Review (Phase 4)
1. Print the following summary to the terminal:
   "Completed Chapter [X]. Target Page Budget: [Y]. Actual Word Count: [Z]."
2. Display the first 200 words and the last 200 words of the chapter draft for high-level continuity tracking.
3. **CRITICAL:** Pause the pipeline execution. Prompt the user: "Type 'APPROVE' to advance to the next chapter, or provide modification feedback."
4. If feedback is given, stream it back to `book-co-author.md` for a targeted chapter rewrite. If `APPROVE` is given, flush `.tmp` files and advance the loop.

## Step 4: Book Compilation
1. Once all chapters are marked `APPROVED`, concatenate `./book_output/chapter_*.md` into a single unified file: `./book_output/self_healing_data_pipelines_final.md`.
2. Generate an automated executive summary and forward to the author.

---
name: transcription-reader
description: "Efficiently read, parse, and analyze transcription and subtitle files (STJ, VTT, SRT, ASS, SSA). Use this skill whenever the user uploads or references a transcription file, subtitle file, or meeting recording transcript. Trigger on file extensions like .stj, .stjson, .vtt, .srt, .ass, .ssa, or when the user mentions transcripts, captions, subtitles, meeting notes from recordings, or wants to summarize a recording, find who said what, extract action items, or convert between transcription formats."
license: MIT
metadata:
  author: Yaniv Golan
  version: "0.4.0"
  compatibility: "Requires Python 3. Optional packages: stjlib (STJ), webvtt-py (VTT), pysubs2 (SRT/ASS/SSA)."
---

# Transcription Reader

Transcription files contain timing metadata that inflates token usage without adding analytical value. This skill helps you decide the fastest path to get the content into context and work with it.

## Quick Decision Tree

1. **Identify the format** from the file extension:
   - `.stj`, `.stjson`, `.stj.json` → STJ (Standard Transcription JSON)
   - `.vtt` → WebVTT
   - `.srt` → SubRip
   - `.ass`, `.ssa` → Advanced SubStation Alpha / SubStation Alpha
   - `.json` (with `"stj"` root key) → STJ

2. **If STJ → run the extraction script immediately.** Do not read the raw JSON. STJ is deeply nested with speaker ID maps, word-level timing arrays, and metadata — raw JSON is unreadable and wastes tokens. No exceptions, regardless of file size. If `stjlib` is not installed, install it first (`pip install stjlib`).
   ```bash
   # Basic extraction
   python3 ${CLAUDE_SKILL_DIR}/scripts/extract_transcript.py INPUT_FILE
   # For summarization (recommended — produces compact speaker blocks)
   python3 ${CLAUDE_SKILL_DIR}/scripts/extract_transcript.py INPUT_FILE --merge-speakers
   # Quick overview
   python3 ${CLAUDE_SKILL_DIR}/scripts/extract_transcript.py INPUT_FILE --stats
   ```

3. **For other formats, check the file size** to decide your approach:

   **Small files (under ~200 lines / ~10KB):** Just read the file directly. The overhead of running the extraction script isn't worth it — you can mentally skip the timestamps as you read. For SRT and VTT, the text is easy to parse visually. For ASS/SSA, look for `Dialogue:` lines.

   **Large files (over ~200 lines):** Use the extraction script. This is where the savings matter — a 2400-line Zoom VTT becomes ~1400 lines of clean text (41% reduction, ~7K tokens saved). STJ files typically see 80-96% reduction depending on content.

   ```bash
   python3 ${CLAUDE_SKILL_DIR}/scripts/extract_transcript.py INPUT_FILE [--format FORMAT] [--output OUTPUT_FILE]
   ```

4. **Read the extracted text** (or the raw file if small) into context.

5. **Analyze** based on the user's request (summarize, search, extract action items, etc.).

## When Timing Data Matters

Sometimes the user needs timestamps — for example, "at what point did they discuss budgets?" or "create a clip list." In these cases, use the `--keep-timestamps` flag:
```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/extract_transcript.py INPUT_FILE --keep-timestamps
```
This produces a format like:
```
[00:05:12] Alice: We need to revisit the budget for Q3.
[00:05:28] Bob: Agreed, let me pull up the numbers.
```

## Format-Specific Notes

### STJ (Standard Transcription JSON)

**Always use the extraction script for STJ**, regardless of file size. Raw STJ is deeply nested JSON with speaker ID maps, word-level timing arrays, confidence scores, and metadata — it's unreadable as raw text and extremely token-heavy.

Key features available in STJ:
- **Speaker names** (not just IDs) — mapped from the `speakers` array
- **Language per segment** — useful for multilingual recordings
- **Confidence scores** — can filter out low-confidence segments with `--min-confidence 0.8`
- **Word-level timing** — available when `word_timing_mode` is "complete" or "partial"

**Diarization-only STJ files**: Some STJ files contain only speaker timing without transcribed text (the `text` field is empty). These are produced by diarization-only tools that identify *who* spoke *when*, but don't transcribe the words. The extraction script detects this automatically and emits a warning. All post-processing flags work on these files — use `--merge-speakers` to collapse consecutive same-speaker segments (e.g., 954 segments → ~200 merged blocks), `--time-range` to answer "who was talking between minute 20-30?", and `--output-format jsonl` for structured output. Use `--stats` or `--list-speakers` for speaker timing summaries. If you encounter a diarization-only file, let the user know it contains speaker timing but no transcribed words — they would need to run a separate transcription tool (e.g., Whisper) on the original audio to get the actual text.

For advanced STJ work (building on top of the STJ data model, custom queries, programmatic access), read `references/stj-format.md` for the full specification and `stjlib` API reference.

### WebVTT (.vtt)

WebVTT files may contain speaker labels in two forms: voice tags (`<v Speaker Name>text</v>`) or inline labels (`Speaker Name: text`). Zoom recordings use the inline form. The extraction script handles both patterns.

For small VTT files, the text is readable directly — captions are separated by blank lines with a timestamp line above each one. Just skip the timestamp lines mentally.

### SRT (.srt)

SRT is the simplest format — numbered blocks with a timestamp line and text. Speaker information is not part of the format spec but is sometimes embedded in the text (e.g., `SPEAKER 1: Hello` or `[ALICE] Hello`).

For small SRT files, direct reading works fine — the structure is very regular and easy to scan.

### ASS/SSA (.ass, .ssa)

ASS/SSA files have a large header (styles, metadata) followed by `Dialogue:` lines. The `Name` field in each dialogue event contains the speaker. The extraction script strips the header and style metadata, which can be 50%+ of the file.

For small ASS files, you can read directly but skip everything above the `[Events]` section.

## Installation

The extraction script requires these Python packages:
```bash
pip install stjlib webvtt-py pysubs2
```

If any package is missing, the script will tell you which one to install — it gracefully handles missing optional dependencies and only requires the library for the format being processed.

## Common Analysis Patterns

After getting the transcript text into context, here are effective approaches for common tasks:

**Summarize a meeting**: Use `--merge-speakers` for the best summarization input — it produces compact speaker blocks instead of one-line-per-cue output. Identify the main topics discussed, key decisions made, and action items. Structure the summary with a brief overview followed by topic-by-topic detail.

**Find what was said about a topic**: Search for relevant keywords. Include surrounding context (a few lines before and after) to capture the full discussion.

**List action items**: Look for commitment language ("I'll do", "let's", "we need to", "action item", "TODO", "by Friday", "deadline") and extract who committed to what.

**Who said what**: The extracted transcript has speaker labels. Filter or group by speaker name to show each person's contributions. For large files, use `--speakers-only NAME` to extract just one speaker's segments.

**Speaker analytics**: Use `--stats` for duration, word counts, and speaker segment counts. Use `--list-speakers` for a quick overview of who's in the file.

## Script Reference

The bundled `scripts/extract_transcript.py` supports these options:

```
Usage: extract_transcript.py INPUT_FILE [options]

Options:
  --format FORMAT        Force format (stj, vtt, srt, ass, ssa). Auto-detected from extension if omitted.
  --output FILE          Write to file instead of stdout.
  --output-format FMT    Output as 'text' (default) or 'jsonl' (one JSON object per line).
  --keep-timestamps      Include timestamps in output.
  --merge-speakers       Merge consecutive segments from the same speaker into single blocks.
  --time-range RANGE     Extract only a time range (e.g., 10:00-20:00 or 1:05:00-1:30:00).
  --min-confidence N     Skip segments below this confidence (STJ only, default: 0.0).
  --speakers-only NAME   Filter to segments from a specific speaker.
  --language LANG        Filter to segments in a specific language (STJ only).
  --list-speakers        Just list speakers found in the file, don't extract text.
  --stats                Show transcript statistics (duration, speaker counts, word counts).
```

**Token-saving tips**: Use `--merge-speakers` to consolidate short segments (a 954-segment file becomes ~200 merged blocks). Combine with `--time-range` to extract just the section you need. For maximum token efficiency with structured data, use `--merge-speakers --output-format jsonl`.
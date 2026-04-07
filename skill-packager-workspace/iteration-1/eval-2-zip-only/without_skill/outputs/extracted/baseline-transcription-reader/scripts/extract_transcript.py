#!/usr/bin/env python3
"""
Extract plain-text transcripts from various transcription/subtitle formats.
Strips timing metadata to produce compact, analysis-ready text.

Supported formats: STJ (.stj, .stjson, .stj.json), WebVTT (.vtt),
                   SRT (.srt), ASS/SSA (.ass, .ssa)

Required packages (install only what you need):
  - STJ:     pip install stjlib
  - VTT:     pip install webvtt-py
  - SRT/ASS: pip install pysubs2
"""

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional


@dataclass
class Segment:
    """Common segment representation across all formats."""
    speaker: Optional[str]
    text: str
    start: Optional[float] = None  # seconds
    end: Optional[float] = None    # seconds


def parse_speaker_from_text(text: str) -> tuple:
    """Extract speaker label from text using common transcription patterns.

    Tries patterns in order of specificity:
    1. >> Name: text  (Zoom/Teams prefix)
    2. [NAME] text    (bracketed label)
    3. Name: text     (inline colon — permissive: allows digits, hyphens, apostrophes, parens)

    Returns (speaker, remaining_text) or (None, original_text).
    """
    # Pattern 1: >> Speaker: text (Zoom/Teams style)
    m = re.match(r'^>>\s*([A-Za-z0-9][A-Za-z0-9\s.\-\'()]{0,30}):\s+(.+)$', text, re.DOTALL)
    if m:
        return m.group(1).strip(), m.group(2).strip()

    # Pattern 2: [SPEAKER] text (bracketed label)
    m = re.match(r'^\[([A-Za-z0-9][A-Za-z0-9\s.\-\']{0,30})\]\s+(.+)$', text, re.DOTALL)
    if m:
        return m.group(1).strip(), m.group(2).strip()

    # Pattern 3: Speaker: text (inline colon, 2+ char label)
    m = re.match(r'^([A-Za-z0-9][A-Za-z0-9\s.\-\'()]{0,30}):\s+(.+)$', text, re.DOTALL)
    if m:
        label = m.group(1).strip()
        # Reject if label is a single character (likely not a speaker)
        if len(label) >= 2:
            return label, m.group(2).strip()

    return None, text


def parse_time_range(time_range: str):
    """Parse a time range string like '10:00-20:00' or '1:05:00-1:30:00'.
    Returns (start_seconds, end_seconds)."""
    parts = time_range.split('-', 1)
    if len(parts) != 2:
        print(f"Error: Invalid time range '{time_range}'. Use format MM:SS-MM:SS or HH:MM:SS-HH:MM:SS.",
              file=sys.stderr)
        sys.exit(1)
    return timestamp_str_to_seconds(parts[0]), timestamp_str_to_seconds(parts[1])


def filter_by_time_range(segments: List[Segment], time_range: str) -> List[Segment]:
    """Filter segments to those overlapping the given time range."""
    start, end = parse_time_range(time_range)
    return [s for s in segments if s.start is not None and s.end is not None
            and s.end > start and s.start < end]


def merge_speaker_runs(segments: List[Segment]) -> List[Segment]:
    """Merge consecutive segments from the same speaker into single blocks."""
    if not segments:
        return segments
    merged = []
    current = Segment(
        speaker=segments[0].speaker,
        text=segments[0].text,
        start=segments[0].start,
        end=segments[0].end,
    )
    for seg in segments[1:]:
        if seg.speaker is not None and seg.speaker == current.speaker:
            if current.text and seg.text:
                current.text = current.text + " " + seg.text
            else:
                current.text = current.text or seg.text
            if seg.end is not None:
                current.end = seg.end
        else:
            merged.append(current)
            current = Segment(
                speaker=seg.speaker,
                text=seg.text,
                start=seg.start,
                end=seg.end,
            )
    merged.append(current)
    return merged


def segments_to_text(segments: List[Segment], keep_timestamps: bool) -> str:
    """Render segments as plain text."""
    lines = []
    last_speaker = None
    for seg in segments:
        prefix = ""
        if keep_timestamps and seg.start is not None:
            prefix = f"[{format_time(seg.start)}] "
        if seg.speaker and seg.speaker != last_speaker:
            if seg.text:
                lines.append(f"{prefix}{seg.speaker}: {seg.text}")
            else:
                lines.append(f"{prefix}{seg.speaker}:")
            last_speaker = seg.speaker
        elif seg.speaker:
            if seg.text:
                lines.append(f"{prefix}{seg.text}")
            elif prefix:
                lines.append(prefix.rstrip())
        else:
            lines.append(f"{prefix}{seg.text}")
            last_speaker = None
    return '\n'.join(lines)


def segments_to_jsonl(segments: List[Segment]) -> str:
    """Render segments as JSONL (one JSON object per line)."""
    lines = []
    for seg in segments:
        obj = {}
        if seg.speaker is not None:
            obj["speaker"] = seg.speaker
        obj["text"] = seg.text
        if seg.start is not None:
            obj["start"] = round(seg.start, 3)
        if seg.end is not None:
            obj["end"] = round(seg.end, 3)
        lines.append(json.dumps(obj, ensure_ascii=False))
    return '\n'.join(lines)


def detect_format(filepath: str) -> str:
    """Auto-detect transcription format from file extension and content."""
    p = filepath.lower()
    if p.endswith('.stj.json') or p.endswith('.stjson') or p.endswith('.stj'):
        return 'stj'
    if p.endswith('.vtt'):
        return 'vtt'
    if p.endswith('.srt'):
        return 'srt'
    if p.endswith('.ass'):
        return 'ass'
    if p.endswith('.ssa'):
        return 'ssa'
    # Try JSON content detection for .json files
    if p.endswith('.json'):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if 'stj' in data:
                return 'stj'
        except (json.JSONDecodeError, IOError):
            pass
    return None


def format_time(seconds: float) -> str:
    """Format seconds as HH:MM:SS."""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    if h > 0:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


def ms_to_seconds(ms: int) -> float:
    """Convert milliseconds to seconds."""
    return ms / 1000.0


def timestamp_str_to_seconds(ts: str) -> float:
    """Convert HH:MM:SS.mmm or MM:SS.mmm to seconds."""
    parts = ts.strip().split(':')
    if len(parts) == 3:
        h, m, rest = parts
        s = float(rest)
        return int(h) * 3600 + int(m) * 60 + s
    elif len(parts) == 2:
        m, rest = parts
        s = float(rest)
        return int(m) * 60 + s
    return 0.0


# ── STJ ──────────────────────────────────────────────────────────────────────

def extract_stj(filepath, keep_timestamps=False, min_confidence=0.0,
                speakers_only=None, language=None, list_speakers=False, stats=False,
                **kwargs) -> 'str | List[Segment]':
    try:
        import stjlib
    except ImportError:
        print("Error: stjlib not installed. Run: pip install stjlib", file=sys.stderr)
        sys.exit(1)

    stj = stjlib.StandardTranscriptionJSON.from_file(filepath)
    transcript = stj.transcript

    # Build speaker name map
    speaker_map = {}
    if transcript.speakers:
        for sp in transcript.speakers:
            speaker_map[sp.id] = sp.name or sp.id

    if list_speakers:
        if not speaker_map:
            print("No speakers defined in this STJ file.")
        else:
            for sid, name in speaker_map.items():
                segs = stj.get_segments_by_speaker(sid)
                print(f"  {name} ({sid}): {len(segs)} segments")
        return

    segments = transcript.segments

    # Detect diarization-only files (speaker timing without transcribed text)
    has_text = any(s.text.strip() for s in segments if s.text)
    if not has_text and not list_speakers and not stats:
        # Check metadata for diarization-only mode
        is_diarization = False
        try:
            meta = stj.metadata
            if meta and meta.extensions:
                for ext_val in meta.extensions.values():
                    if isinstance(ext_val, dict) and ext_val.get('mode') == 'diarization_only':
                        is_diarization = True
        except (AttributeError, TypeError):
            pass

        print("Warning: This STJ file contains no transcribed text.", file=sys.stderr)
        if is_diarization:
            print("  This is a diarization-only file (speaker timing without transcription).", file=sys.stderr)
            print("  It contains speaker segments showing who spoke when, but no words.", file=sys.stderr)
        print("  Use --stats or --list-speakers to see speaker timing information.", file=sys.stderr)

        # Return Segment objects so post-processing pipeline works
        # (--merge-speakers, --time-range, --output-format jsonl)
        return [
            Segment(
                speaker=speaker_map.get(seg.speaker_id, seg.speaker_id) if seg.speaker_id else "Unknown",
                text=seg.text or "",
                start=seg.start,
                end=seg.end,
            )
            for seg in segments
        ]

    # Apply filters
    if min_confidence > 0:
        segments = [s for s in segments if (s.confidence or 1.0) >= min_confidence]
    if speakers_only:
        # Match by name or ID
        target_ids = set()
        for sid, name in speaker_map.items():
            if speakers_only.lower() in name.lower() or speakers_only.lower() == sid.lower():
                target_ids.add(sid)
        if not target_ids:
            print(f"Warning: No speaker matching '{speakers_only}' found.", file=sys.stderr)
        segments = [s for s in segments if s.speaker_id in target_ids]
    if language:
        segments = [s for s in segments if (s.language or '').lower() == language.lower()]

    if stats:
        return _print_stats_stj(stj, segments, speaker_map)

    # Return common Segment objects
    return [
        Segment(
            speaker=speaker_map.get(seg.speaker_id, seg.speaker_id) if seg.speaker_id else None,
            text=seg.text,
            start=seg.start,
            end=seg.end,
        )
        for seg in segments
    ]


def _print_stats_stj(stj, segments, speaker_map):
    meta = stj.metadata
    lines = ["=== Transcript Statistics ==="]
    if meta and meta.source and meta.source.duration:
        lines.append(f"Duration: {format_time(meta.source.duration)}")
    if meta and meta.languages:
        lines.append(f"Languages: {', '.join(meta.languages)}")
    lines.append(f"Total segments: {len(segments)}")
    total_words = sum(len(s.text.split()) for s in segments)
    lines.append(f"Total words: {total_words}")

    # Per-speaker stats
    if speaker_map:
        lines.append("\nPer speaker:")
        for sid, name in speaker_map.items():
            sp_segs = [s for s in segments if s.speaker_id == sid]
            sp_words = sum(len(s.text.split()) for s in sp_segs)
            sp_time = sum(s.end - s.start for s in sp_segs)
            lines.append(f"  {name}: {len(sp_segs)} segments, {sp_words} words, ~{format_time(sp_time)} speaking time")

    return '\n'.join(lines)


# ── WebVTT ───────────────────────────────────────────────────────────────────

def extract_vtt(filepath, keep_timestamps=False, speakers_only=None, list_speakers=False, stats=False,
                **kwargs) -> 'str | List[Segment]':
    try:
        import webvtt
    except ImportError:
        print("Error: webvtt-py not installed. Run: pip install webvtt-py", file=sys.stderr)
        sys.exit(1)

    captions = webvtt.read(filepath)

    # Try to extract speaker labels from VTT voice tags or text patterns
    def parse_speaker(caption):
        """Extract speaker from VTT voice tags or inline text patterns."""
        # webvtt-py provides caption.voice for <v Speaker>text</v> tags
        if hasattr(caption, 'voice') and caption.voice:
            return caption.voice, caption.text
        # Fall back to raw lines check for older webvtt-py versions
        raw = '\n'.join(caption.lines) if hasattr(caption, 'lines') else caption.text
        m = re.match(r'<v\s+([^>]+)>(.*?)(?:</v>)?$', raw, re.DOTALL)
        if m:
            clean_text = re.sub(r'<[^>]+>', '', m.group(2)).strip()
            return m.group(1).strip(), clean_text
        # Fall back to shared speaker parser for inline labels
        return parse_speaker_from_text(caption.text)

    if list_speakers:
        speakers = set()
        for cap in captions:
            sp, _ = parse_speaker(cap)
            if sp:
                speakers.add(sp)
        if speakers:
            for sp in sorted(speakers):
                print(f"  {sp}")
        else:
            print("No speaker labels detected in this VTT file.")
        return

    if stats:
        total_words = sum(len(cap.text.split()) for cap in captions)
        lines = ["=== Transcript Statistics ==="]
        if captions:
            last = captions[-1]
            dur = timestamp_str_to_seconds(last.end)
            lines.append(f"Duration: ~{format_time(dur)}")
        lines.append(f"Total captions: {len(captions)}")
        lines.append(f"Total words: {total_words}")
        return '\n'.join(lines)

    # Build Segment objects
    result = []
    for cap in captions:
        speaker, text = parse_speaker(cap)
        text = re.sub(r'<[^>]+>', '', text).strip()
        if not text:
            continue
        if speakers_only:
            if not speaker or speakers_only.lower() not in speaker.lower():
                continue
        result.append(Segment(
            speaker=speaker,
            text=text,
            start=timestamp_str_to_seconds(cap.start),
            end=timestamp_str_to_seconds(cap.end),
        ))

    return result


# ── SRT / ASS / SSA ─────────────────────────────────────────────────────────

def extract_pysubs2(filepath, fmt, keep_timestamps=False, speakers_only=None,
                    list_speakers=False, stats=False, **kwargs) -> 'str | List[Segment]':
    try:
        import pysubs2
    except ImportError:
        print("Error: pysubs2 not installed. Run: pip install pysubs2", file=sys.stderr)
        sys.exit(1)

    subs = pysubs2.load(filepath)

    def get_speaker(event):
        """Extract speaker from ASS Name field or inline text patterns."""
        # ASS/SSA uses the Name field
        if event.name and event.name.strip():
            return event.name.strip()
        # SRT sometimes has inline labels — use shared parser
        speaker, _ = parse_speaker_from_text(event.text)
        return speaker

    def get_text(event):
        """Get clean text, stripping inline speaker label if present."""
        if not event.name or not event.name.strip():
            _, text = parse_speaker_from_text(event.text)
        else:
            text = event.text
        # Clean ASS override tags like {\an8}
        text = re.sub(r'\{\\[^}]+\}', '', text)
        # Replace \N with space
        text = text.replace('\\N', ' ').replace('\\n', ' ')
        return text.strip()

    # Only process dialogue events
    events = [e for e in subs if e.type == 'Dialogue' or not hasattr(e, 'type')]

    if list_speakers:
        speakers = set()
        for e in events:
            sp = get_speaker(e)
            if sp:
                speakers.add(sp)
        if speakers:
            for sp in sorted(speakers):
                count = sum(1 for e in events if get_speaker(e) == sp)
                print(f"  {sp}: {count} segments")
        else:
            print("No speaker labels detected in this file.")
        return

    if speakers_only:
        events = [e for e in events if get_speaker(e) and
                  speakers_only.lower() in get_speaker(e).lower()]

    if stats:
        total_words = sum(len(get_text(e).split()) for e in events)
        lines = ["=== Transcript Statistics ==="]
        if events:
            dur_ms = max(e.end for e in events)
            lines.append(f"Duration: ~{format_time(ms_to_seconds(dur_ms))}")
        lines.append(f"Total events: {len(events)}")
        lines.append(f"Total words: {total_words}")
        speakers = set(get_speaker(e) for e in events if get_speaker(e))
        if speakers:
            lines.append(f"Speakers: {', '.join(sorted(speakers))}")
        return '\n'.join(lines)

    # Build Segment objects
    result = []
    for e in events:
        speaker = get_speaker(e)
        text = get_text(e)
        if not text:
            continue
        result.append(Segment(
            speaker=speaker,
            text=text,
            start=ms_to_seconds(e.start),
            end=ms_to_seconds(e.end),
        ))

    return result


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Extract plain-text transcripts from transcription/subtitle files.",
        epilog="Supported formats: STJ, WebVTT, SRT, ASS, SSA"
    )
    parser.add_argument('input', help='Input transcription file')
    parser.add_argument('--format', '-f', choices=['stj', 'vtt', 'srt', 'ass', 'ssa'],
                        help='Force format (auto-detected from extension if omitted)')
    parser.add_argument('--output', '-o', help='Output file (default: stdout)')
    parser.add_argument('--output-format', choices=['text', 'jsonl'], default='text',
                        help='Output format: text (default) or jsonl')
    parser.add_argument('--keep-timestamps', '-t', action='store_true',
                        help='Include timestamps in output')
    parser.add_argument('--min-confidence', type=float, default=0.0,
                        help='Skip segments below this confidence (STJ only)')
    parser.add_argument('--speakers-only', '-s',
                        help='Filter to a specific speaker (by name or ID)')
    parser.add_argument('--language', '-l',
                        help='Filter to a specific language (STJ only)')
    parser.add_argument('--list-speakers', action='store_true',
                        help='List speakers found in the file')
    parser.add_argument('--stats', action='store_true',
                        help='Show transcript statistics')
    parser.add_argument('--merge-speakers', '-m', action='store_true',
                        help='Merge consecutive segments from the same speaker')
    parser.add_argument('--time-range',
                        help='Extract only a time range (e.g., 10:00-20:00 or 1:05:00-1:30:00)')

    args = parser.parse_args()

    if not os.path.isfile(args.input):
        print(f"Error: File not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    fmt = args.format or detect_format(args.input)
    if not fmt:
        print(f"Error: Cannot detect format for '{args.input}'. Use --format to specify.",
              file=sys.stderr)
        sys.exit(1)

    kwargs = dict(
        keep_timestamps=args.keep_timestamps,
        min_confidence=args.min_confidence,
        speakers_only=args.speakers_only,
        language=args.language,
        list_speakers=args.list_speakers,
        stats=args.stats,
    )

    if fmt == 'stj':
        result = extract_stj(args.input, **kwargs)
    elif fmt == 'vtt':
        result = extract_vtt(args.input, **kwargs)
    elif fmt in ('srt', 'ass', 'ssa'):
        result = extract_pysubs2(args.input, fmt, **kwargs)
    else:
        print(f"Error: Unsupported format: {fmt}", file=sys.stderr)
        sys.exit(1)

    if result is None:
        return

    # If result is a string (stats, list_speakers, diarization fallback), output directly
    if isinstance(result, str):
        if args.output:
            Path(args.output).write_text(result, encoding='utf-8')
            print(f"Written to {args.output}", file=sys.stderr)
        else:
            print(result)
        return

    # result is List[Segment] — apply post-processing pipeline
    segments = result

    if args.time_range:
        segments = filter_by_time_range(segments, args.time_range)

    if args.merge_speakers:
        segments = merge_speaker_runs(segments)

    # Render output
    if args.output_format == 'jsonl':
        output = segments_to_jsonl(segments)
    else:
        output = segments_to_text(segments, args.keep_timestamps)

    if args.output:
        Path(args.output).write_text(output, encoding='utf-8')
        print(f"Written to {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == '__main__':
    main()
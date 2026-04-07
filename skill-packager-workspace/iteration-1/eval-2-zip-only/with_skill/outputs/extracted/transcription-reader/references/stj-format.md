# STJ (Standard Transcription JSON) Format Reference

Version: 0.6.1 | Spec: https://yaniv-golan.github.io/STJ/ | Repo: https://github.com/yaniv-golan/STJ

## Table of Contents
1. [File Structure](#file-structure)
2. [Metadata](#metadata)
3. [Transcript](#transcript)
4. [Segments](#segments)
5. [Words](#words)
6. [Speakers](#speakers)
7. [Styles](#styles)
8. [Python Library (stjlib)](#python-library)

## File Structure

File extensions: `.stjson`, `.stj`, `.stj.json`

```json
{
  "stj": {
    "version": "0.6.1",
    "metadata": { ... },
    "transcript": {
      "speakers": [ ... ],
      "styles": [ ... ],
      "segments": [ ... ]
    }
  }
}
```

Root key is always `"stj"`. Version follows semver.

## Metadata

```json
"metadata": {
  "transcriber": { "name": "YAWT", "version": "0.4.0" },
  "created_at": "2024-10-24T15:30:00Z",
  "source": {
    "uri": "https://example.com/recording.mp4",
    "duration": 1800.0,
    "languages": ["en", "es"]
  },
  "languages": ["en", "es"],
  "confidence_threshold": 0.6,
  "extensions": { ... }
}
```

- `transcriber`: Tool that produced the transcript (name required, version optional)
- `created_at`: ISO 8601 timestamp
- `source.duration`: Total duration in seconds
- `source.languages`: Languages detected in the source
- `languages`: Languages present in the transcript
- `confidence_threshold`: Minimum confidence used during transcription
- `extensions`: Arbitrary additional data (project info, custom fields)

## Transcript

Contains `speakers`, `styles`, and `segments` arrays. Only `segments` is required.

## Segments

Each segment represents a continuous piece of speech:

```json
{
  "start": 0.0,
  "end": 5.0,
  "text": "Hello, world!",
  "speaker_id": "Speaker1",
  "confidence": 0.98,
  "language": "en",
  "style_id": "Style1",
  "word_timing_mode": "complete",
  "words": [ ... ],
  "extensions": { ... }
}
```

- `start`, `end`: Time in seconds (required, floats)
- `text`: The transcribed text (required)
- `speaker_id`: References a speaker in the `speakers` array
- `confidence`: 0.0 to 1.0 (segment-level confidence)
- `language`: BCP-47 language tag (e.g., "en", "es", "de")
- `word_timing_mode`: "complete" (all words timed), "partial" (some timed), "none"
- `words`: Array of word-level timing (see below)
- `is_zero_duration`: Boolean, true if start == end (e.g., annotations)

## Words

When `word_timing_mode` is "complete" or "partial":

```json
{
  "start": 0.0,
  "end": 0.5,
  "text": "Hello,",
  "confidence": 0.99
}
```

Word-level timing is useful for precise clip generation or karaoke-style highlighting but should typically be stripped for text analysis.

## Speakers

```json
{
  "id": "Speaker1",
  "name": "Dr. Smith",
  "extensions": {
    "role": { "title": "Keynote Speaker" }
  }
}
```

- `id`: Unique identifier (required)
- `name`: Human-readable name
- `extensions`: Additional metadata (role, department, etc.)

## Styles

Styles define visual presentation (for subtitle rendering). Generally not needed for text analysis.

```json
{
  "id": "Style1",
  "text": { "color": "#FF5733", "bold": true, "size": "100%" },
  "display": { "align": "center", "vertical": "bottom" }
}
```

## Python Library

Install: `pip install stjlib`

```python
from stjlib import StandardTranscriptionJSON

# Load and validate
stj = StandardTranscriptionJSON.from_file('recording.stj.json', validate=True)

# Access metadata
meta = stj.metadata
print(meta.source.duration)  # 1800.0
print(meta.languages)         # ['en', 'es']

# Access transcript
transcript = stj.transcript

# Speakers
for speaker in transcript.speakers:
    print(f"{speaker.id}: {speaker.name}")

# All segments
for seg in transcript.segments:
    print(f"[{seg.start:.1f}-{seg.end:.1f}] {seg.speaker_id}: {seg.text}")

# Segments by speaker
segs = stj.get_segments_by_speaker("Speaker1")

# Get a speaker object
speaker = stj.get_speaker("Speaker1")
print(speaker.name)

# Export back to dict/file
data = stj.to_dict()
stj.to_file('output.stj.json')
```

### Key API Methods

| Method | Description |
|--------|-------------|
| `StandardTranscriptionJSON.from_file(path, validate=True)` | Load from file |
| `StandardTranscriptionJSON.from_dict(data)` | Load from dict |
| `stj.transcript.segments` | List of Segment objects |
| `stj.transcript.speakers` | List of Speaker objects |
| `stj.get_segments_by_speaker(speaker_id)` | Filter segments by speaker |
| `stj.get_speaker(speaker_id)` | Get Speaker object by ID |
| `stj.metadata` | Metadata object |
| `stj.validate()` | Validate against schema |
| `stj.to_dict()` / `stj.to_file(path)` | Serialize |

### Segment Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `start` | float | Start time in seconds |
| `end` | float | End time in seconds |
| `text` | str | Transcribed text |
| `speaker_id` | str/None | Speaker identifier |
| `confidence` | float/None | 0.0 to 1.0 |
| `language` | str/None | BCP-47 language tag |
| `style_id` | str/None | Style reference |
| `word_timing_mode` | str/None | "complete"/"partial"/"none" |
| `words` | list/None | Word-level timing data |
| `is_zero_duration` | bool | Whether segment has zero duration |
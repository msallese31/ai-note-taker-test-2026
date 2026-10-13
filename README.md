# AI note takers tested on five public meetings (October 2026)

We ran the same five recorded meetings through four AI note takers: Fireflies, Granola, Otter and Scribbl. Then we scored each tool's notes two ways, with the scoring written down before meetings 2 to 5 were run. This repository has everything: the audio we fed in, each tool's notes, the answer keys, every prompt, every grader's and judge's answer, and the scripts that recompute every number.

This test was run by Scribbl, one of the four tools tested. That's why every input and every answer is published, so anyone can check the results or run the test again.

## Results

### 1. Graded against the researchers' own notes

Each meeting comes from the AMI Meeting Corpus, and the researchers who recorded it also wrote their own summary of it: the decisions, actions and problems. Every sentence of that summary is one answer-key item (103 across the five meetings). Three AI graders (Claude Opus 5.5, Claude Fable 5.1, GPT-6.1 Sol) checked each tool's notes against the key and the transcript, one set of notes at a time, with no tool names. Correct = 1 point, partial = 0.5.

| Meeting | Length | Fireflies | Granola | Otter | Scribbl |
|---|---|---|---|---|---|
| IS1008d | 24.5 min | 60% | 61% | 78% | 81% |
| IB4003 | 34 min | 86% | 80% | 60% | 67% |
| ES2008b | 37 min | 56% | 80% | 67% | 80% |
| IS1001c | 24 min | 57% | 77% | 91% | 79% |
| TS3012a | 14 min | 86% | 87% | 87% | 83% |
| **Average** | | **69%** | **77%** | **77%** | **78%** |

The graders also listed every statement in the notes that was wrong or not supported by the transcript. Totals across all five meetings, averaged across the three graders:

| Kind of mistake | Fireflies | Granola | Otter | Scribbl |
|---|---|---|---|---|
| Wrong fact | 7.0 | 2.7 | 2.7 | 3.7 |
| Wrong person | 4.0 | 0.3 | 3.7 | 1.0 |
| Action item nobody agreed to | 9.3 | 0.3 | 0.7 | 0.7 |
| Other content that didn't happen | 4.0 | 0.7 | 5.7 | 0.0 |
| Decision described differently from how it happened | 3.7 | 2.0 | 5.0 | 1.0 |
| **Total** | **28.0** | **6.0** | **17.7** | **6.3** |

Every mistake each grader listed is in [RESULTS.md](RESULTS.md).

### 2. Blind side-by-side judging

For each meeting, four AI judges (Claude Opus 5.5, Claude Fable 5.1, Claude Sonnet 5.5, GPT-6.1 Sol) got the transcript and all four sets of notes labeled A to D, with no tool names. They scored each on accuracy, completeness, decisions and action items, and usefulness (25% each), and ranked them. Each judge ran 4 times per meeting with the order rotated, so every tool sat in every slot once: 80 judgments in all.

| Meeting | Fireflies | Granola | Otter | Scribbl |
|---|---|---|---|---|
| IS1008d | 0 first, 5.3 | 3 first, 7.5 | 0 first, 5.2 | 13 first, 7.9 |
| IB4003 | 0 first, 6.4 | 11 first, 8.0 | 0 first, 4.7 | 5 first, 7.7 |
| ES2008b | 0 first, 5.0 | 2 first, 7.7 | 0 first, 5.4 | 14 first, 8.3 |
| IS1001c | 0 first, 5.4 | 16 first, 8.7 | 0 first, 6.2 | 0 first, 7.7 |
| TS3012a | 0 first, 5.5 | 0 first, 7.2 | 0 first, 5.7 | 16 first, 8.1 |
| **All 80** | **0 first, 5.5** | **32 first, 7.8** | **0 first, 5.4** | **48 first, 7.9** |

Each cell is the number of judgments that ranked that tool first, then its average overall score out of 10.

## Limits

- Five meetings, all in English, all from one research corpus. Most are product design meetings where people play assigned roles.
- All grades come from AI models. No human graders were used.
- Free plans were used for Fireflies and Otter. Paid plans may produce different notes.
- Granola has no file upload, so the audio was played through the Mac while Granola recorded.
- Deviations from the written plan are listed at the end of [PROTOCOL.md](PROTOCOL.md).

## What's here

| Path | What it is |
|---|---|
| [PROTOCOL.md](PROTOCOL.md) | The test as written before meetings 2 to 5 were run, plus every deviation |
| [plans.md](plans.md) | The plan each tool ran on |
| `meetings/<meeting>/` | The audio file every tool got, the reference transcript, and the answer key |
| `meetings/SHA256SUMS` | Checksums of the audio files |
| `notes/<meeting>/<tool>.md` | Each tool's notes, copied as written (see PROTOCOL.md for the two changes) |
| `grading/` | Answer-key grading: `manifest.json` (which prompt was which tool and grader), `prompts/`, `out/` (each grader's raw answer) |
| `sidebyside/` | Side-by-side judging for meetings 2 to 5: manifest, prompts, raw answers |
| `judge/` | Side-by-side judging for meeting 1 (IS1008d), run 2026-10-12 |
| `ami-source/` | The AMI corpus files the transcripts and answer keys were built from |
| `build_meeting.py` | Builds each reference transcript and answer key from `ami-source/` |
| `grade_key.py`, `run_gpt_grading.py` | Build and run the answer-key grading |
| `sidebyside.py`, `judge/judge.py`, `judge/run_openai.py` | Build and run the side-by-side judging |
| `score.py`, `score_sidebyside.py` | Recompute every number above from the raw answers |

## How the audio files were made

Each file is the corpus's mixed headset recording (`<meeting>.Mix-Headset.wav`, downloaded from the AMI corpus mirror), converted to mono MP3:

```bash
ffmpeg -i IS1008d.Mix-Headset.wav -ac 1 -c:a libmp3lame -b:a 48k IS1008d-test-audio.mp3
ffmpeg -i <meeting>.Mix-Headset.wav -ac 1 -c:a libmp3lame -b:a 64k <meeting>-test-audio.mp3   # meetings 2 to 5
```

Where a tool was given a video file instead (see PROTOCOL.md, Deviations), it was the corpus's meeting video with this same audio, re-encoded at 96 kbps AAC.

## Recompute the results

```bash
python3 score.py
python3 score_sidebyside.py
```

Both use only the Python standard library and rewrite `RESULTS.md` and `RESULTS-sidebyside.md` from the raw answers.

## Source and license

Meetings, transcripts and researcher summaries are from the AMI Meeting Corpus (University of Edinburgh and partners), licensed under CC BY 4.0: https://groups.inf.ed.ac.uk/ami/corpus/ . See `ami-source/LICENCE`. Each tool's notes are that tool's output on this audio, published for the purpose of this comparison.

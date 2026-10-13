# Test protocol: four AI note takers on five public meetings

Written 2026-10-13, before any of meetings 2 to 5 were run through any tool. Nothing below may change after results come in. Any deviation is logged at the bottom with the date and the reason.

## Tools
Fireflies, Granola, Otter, Scribbl. The plan each tool runs on is recorded in `plans.md`, with the date.

## Meetings
All from the AMI Meeting Corpus (University of Edinburgh, CC BY 4.0), chosen because the researchers who recorded them also wrote their own notes on each one (abstract, decisions, actions, problems). The selection rule: meetings that have researcher notes, are 40 minutes or shorter, and come from different recording sites and groups.

| # | Meeting | Length | Site and kind |
|---|---|---|---|
| 1 | IS1008d | 24.5 min | Idiap (Switzerland), design team, final meeting (already run 2026-10-12, before this protocol) |
| 2 | IB4003 | 34 min | Idiap, a non-design meeting: a group planning a simplified, fictional office move (the corpus calls it a non-scenario meeting) |
| 3 | ES2008b | 37 min | Edinburgh, design team |
| 4 | IS1001c | 24 min | Idiap, a different design team |
| 5 | TS3012a | 14 min | TNO (Netherlands), design team kickoff |

## Input
- One audio file per meeting (the corpus's mixed headset audio, mono MP3), and the same file goes into every tool.
- Fireflies and Otter: the file is uploaded through their own upload screens.
- Granola: it has no upload. The same file is played through the Mac's audio with output volume and microphone input at zero, while a new Granola note records.
- Scribbl: the same file goes through Scribbl's production transcription and notes steps (the same path a desktop Zoom recording takes), with the number of speakers set to the number of participants, the way a real call would supply it. The meeting video is attached for playback.
- Each tool's notes are copied exactly as written, with only the product's own buttons and labels removed, into `notes/<meeting>/<tool>.md`. Nothing is edited.

## Primary score: the researchers' answer key
- The answer key for each meeting is every sentence in the researchers' own notes (abstract, decisions, actions, problems), unedited. We don't add or remove items.
- Each tool's notes are graded on their own, against the key and the transcript. For each item the grader marks it correct (1 point), partial (0.5), missed (0), or wrong (0, and counted as an error).
- Graders also list every statement in the notes that is wrong or unsupported by the transcript, sorted into: wrong fact, wrong person (speaker or owner), invented action item, other invented content, decision described differently from how it happened.
- Human graders: two or more people with no tie to any of the four companies. They see the transcript, the recording and one set of notes at a time, labeled with a random code, never the tool name.
- AI graders: Claude Opus 5.5, Claude Fable 5.1 and GPT-6.1 Sol, each run separately, each seeing one set of notes at a time with no tool name.
- A meeting's score for a tool is its points divided by the number of items, averaged across graders. The overall score is the average across the five meetings. Human and AI grader results are reported separately and together.

## Secondary score: blind side-by-side judging
Each meeting's four sets of notes, labeled A to D, judged together by Claude Opus 5.5, Claude Fable 5.1, Claude Sonnet 5.5 and GPT-6.1 Sol on accuracy, completeness, decisions and action items, and usefulness (equal weight), 4 times per model with the order rotated so each tool sits in each slot once. The prompt is the one in `judge/judge.py`, version v1-objective, unchanged.

## Error table
For every tool, counts in each error category above, per meeting and in total, from the graders' lists. Every error is kept, including the winner's.

## Reporting
- Results are reported per meeting, including any meeting where Scribbl doesn't score highest.
- What counts as a Scribbl loss: on any meeting where another tool's average answer-key score is higher, that meeting is reported as a loss for Scribbl.
- Everything is published: audio source links, each tool's notes, the answer keys, every prompt, every grader's and judge's answer, and a script that recomputes every number.

## Deviations
- 2026-10-13: Otter ran on its free Basic plan (Mike chose not to pay), and meetings 2 to 5 were split across two of Mike's Otter accounts (IB4003 and IS1001c in one, ES2008b and TS3012a in the other). Otter showed IB4003 as 33 minutes long against a 34-minute file; that is recorded as is. Fireflies was also split across two accounts on its free plan: IB4003 in one, IS1001c, TS3012a and ES2008b in the other (the first account's free meetings ran out). In the first account, the three later uploads exist but were never transcribed; only the second account's copies are used.
- 2026-10-13: For Otter (and possibly Fireflies), the uploaded file was the meeting's video file (`<meeting>-scribbl.mp4`, the same audio re-encoded at 96 kbps with the video) rather than the MP3. Its file name contained a tool name, and Otter wrote the file name into its notes ("the IS1001c-scribbl remote control"). That token was replaced with the meeting code only in the saved notes, so the judges stay blind. No other text was changed.
- 2026-10-13: Scribbl's IS1008d notes contain an invented speaker name ("Moritz" for the User Interface Designer, who is Agnes). For the answer-key score, that name is corrected to Agnes in a copy of the notes (notes/IS1008d/scribbl-corrected.md); nothing else in the copy differs. The notes as produced are in notes/IS1008d/scribbl.md, and the side-by-side judging of meeting 1 (run 2026-10-12) used those. Scribbl is fixing how it names speakers.
- 2026-10-13: In the second Fireflies account, the meeting pages for IS1001c, TS3012a and ES2008b showed Notes and Action items with no separate General Summary block (unlike IB4003 in the first account). The saved notes are everything those pages showed.
- 2026-10-13: The side-by-side prompt for meetings 2 to 5 describes "a meeting" instead of "a 24-minute product design meeting" (the meeting 1 wording), and says speakers are labeled by role or letter. The criteria, weights, instructions and output format are the v1-objective ones, unchanged.
- 2026-10-13: Human graders were not run. All grades in this release are from the AI graders. Human grades, if added later, will be reported separately.

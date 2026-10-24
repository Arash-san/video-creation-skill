# Writing the narration

The narration is the spine of the video: the timeline, the scene lengths and the subtitles all come from it.

## Structure

- Open with the question or problem, not with "In this video we will...".
- One idea per scene; usually two to four lines per scene, 15 to 45 seconds.
- A typical explainer moves: hook, problem, intuition, mechanism (one step at a time), evidence or numbers, limits or caveats, a one-sentence takeaway.
- Ten-minute videos run about 1,400 words at the default rate. Short demos: 150 to 300 words.

## Sentences for the ear

- Short and spoken. Read every line aloud in your head; if you would not say it that way, rewrite it.
- Define each term the first time it appears, in plain words, then use it consistently.
- Put the new information at the end of the sentence, where the voice lands.
- Write numbers the way they are spoken when it matters ("about a hundred million", "0.75 to 11 hertz").
- Spell out abbreviations on first use; avoid ones the voice will mispronounce, or write them phonetically.
- Use concrete examples ("say the word cat") instead of abstractions ("a given input").
- Avoid filler and stock phrasing: "delve", "tapestry", "crucial", "in today's world", "it's important to note", "game-changer", "unlock", "seamless". Avoid rhetorical "Not X, but Y" constructions in every other line.
- Prefer full stops over long chains of commas; the subtitle splitter uses sentence ends.

## Honesty

- Every claim and number must come from the sources. Name the source on screen for key numbers.
- If the sources disagree or a figure looks inconsistent, show it as published and say so; do not silently "fix" it.
- Include limits: sample sizes, lab-only results, open questions.
- Describe who did the work accurately (first author, coauthor, a group's work) when covering people.

## narration.json

```json
{
  "voice": "en-US-AvaMultilingualNeural",
  "rate": "+4%",
  "subtitles": {"font": "Space Grotesk", "size": 46, "text": "#F3EEE3", "box": "#24366E", "box_alpha": 0.86, "max_chars": 54, "bold": true},
  "timing": {"lead_first": 1.6, "lead": 1.9, "line_gap": 0.45, "tail": 0.7},
  "scenes": [
    {"id": "title", "lines": ["First line.", {"text": "A line followed by a pause.", "pause": 0.6}]},
    {"id": "mechanism", "lines": ["..."], "min_dur": 14}
  ]
}
```

- `lead` is the silence at the start of each scene (time for the transition and first visuals).
- `min_dur` stretches a scene whose animation needs more time than its speech.
- Other good edge-tts voices: `en-US-AndrewMultilingualNeural`, `en-US-EmmaMultilingualNeural`, `en-GB-SoniaNeural`, `en-US-BrianMultilingualNeural`. List all with `edge-tts --list-voices`.
- Subtitle colors should come from the palette: a box in the darkest ink at 80 to 90 percent opacity with paper-colored text reads well on any background.

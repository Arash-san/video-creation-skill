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
  "tts": {"engine": "ming", "design": "A calm, warm woman in her fifties, a nature documentary narrator. Low pitch, unhurried, clear diction."},
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
- Subtitle colors should come from the palette: a box in the darkest ink at 80 to 90 percent opacity with paper-colored text reads well on any background.

## The voice

The narrator is part of the art direction. Cast it the way you chose the palette: a cyanotype light lab and a kitchen-table zine should not sound the same.

### Ming-3.0-tts (default when installed)

[Ming-3.0-tts-0.5B](https://huggingface.co/inclusionAI/Ming-3.0-tts-0.5B) is an open-weight speech model from Ant Group (inclusionAI, MIT license) that runs locally on an NVIDIA GPU. Install it once with `python scripts/setup_ming.py`. Pick one of three ways to choose the voice in the `"tts"` block:

| Key | What it does |
|-----|--------------|
| `"design": "<description>"` | Invents a voice from a description. Best for matching the art direction; `style_roll.py` suggests one with each style. Describe who is speaking (gender, age, accent), the timbre, the pace and the attitude in one or two sentences. |
| `"voice": "US_James"` | A built-in voice: `US_James` (male, American, documentary), `US_Emma`, `US_Stella` (female, American), `UK_George` (male, British), `UK_Charlotte` (female, British). |
| `"clone": "voice/ref.wav", "clone_text": "..."` | Clones a 5 to 15 second recording; `clone_text` must be exactly what it says. Only clone a voice you have permission to use. |

Optional keys: `"tempo": 1.05` (speed up or slow down without changing pitch), `"workers": 3` (parallel model copies, about 3 GB of GPU memory each), `"anchor_text"` (the sentence used to fix the voice), `"language": "de"` (also `fr`, `es`, `ja`, `ko`, `zh`).

How it keeps one voice: a designed or built-in voice is first spoken once into `audio/voice_anchor.wav`, and every line then clones that clip, so the speaker does not drift between lines. Listen to the anchor before synthesizing everything; if you do not like it, change the description and rerun (the anchor and all lines are remade).

Ming can also make sounds inline. Write one of these tags in a line where a person would naturally make it: `[Laughter]`, `[Sigh]`, `[Breathing]`, `[Uhm]`, `[Surprise-oh]`, `[Surprise-ah]`, `[Question-huh]`. Tags are left out of the subtitles. Use them rarely (one or two per video at most) and only where the content is genuinely funny or surprising.

Ming spells out numbers itself ("2,147" becomes "two thousand one hundred forty-seven"), but write ambiguous ones the way they should be said ("twenty twenty-four" vs "two thousand twenty-four").

Generation is slower than real time (one worker makes about 0.4 seconds of speech per second on an RTX 4090 or 5090; three workers about 0.8). Lines are cached, so only edited lines are redone. Word timings come from forced alignment against your text, so subtitles and `cue.t(k)` stay exact.

### edge-tts (fallback)

Microsoft Edge neural voices: free, no GPU, needs internet. Used when Ming is not installed, or with `"tts": {"engine": "edge", "edge_voice": "en-US-AvaMultilingualNeural", "edge_rate": "+4%"}`. Good voices: `en-US-AvaMultilingualNeural`, `en-US-AndrewMultilingualNeural`, `en-US-EmmaMultilingualNeural`, `en-GB-SoniaNeural`, `en-US-BrianMultilingualNeural` (list all with `edge-tts --list-voices`). Inline tags are not supported. Older projects with top-level `"voice"` and `"rate"` keys still work.

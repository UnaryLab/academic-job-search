# Rank (the lowest rank the user applies at)
<!-- Edited only on request. -->

| Setting | Value |
|---|---|
| Minimum rank | assistant |

An ad counts only when it accepts applicants at the minimum rank or below (`assistant` < `associate` < `full`); `open` rank always counts. Search and verify agents skip senior-only posts instead of returning them.

## Title to rank mapping

The `rank` field is the lowest rank the ad accepts.

| Rank | Titles |
|---|---|
| `assistant` | Assistant Professor; UK Lecturer; UK "Associate Professor" where it is the entry grade (Oxford, Warwick, UCL, Nottingham and the like, i.e. the ad says Associate Professor with no Lecturer grade below it); Nordic and Dutch Assistant Professor / Universitair Docent; German W1 or Juniorprofessur / tenure-track W2; French Maître de conférences; Swiss tenure-track Assistant Professor; Spanish Serra Hunter or Ayudante Doctor; teaching-stream Lecturer (continuing) and Assistant Professor of Teaching |
| `associate` | UK Senior Lecturer, Reader, Principal Lecturer; Dutch Universitair Hoofddocent; German W2 without tenure track; Spanish Titular |
| `full` | Professor, Chair, Professorial fellowships, German W3, Dutch Hoogleraar, French Professeur des universités |
| `open` | The ad names several grades starting at the lowest one (e.g. "Lecturer/Senior Lecturer/Reader", "Assistant/Associate/Full", "W2/W3 tenure-track"), or says open rank |

import io
import re
import zipfile
from pathlib import Path

import music21

_KNOWN_NAMESPACES = {
    "xsi": "http://www.w3.org/2001/XMLSchema-instance",
    "xlink": "http://www.w3.org/1999/xlink",
}


def _repair_xml(xml: str) -> str:
    used = set(re.findall(r"<[^>]*?\s([A-Za-z_][\w.-]*):[\w.-]+\s*=", xml))
    used |= set(re.findall(r"<([A-Za-z_][\w.-]*):", xml))
    missing = [p for p in used if p in _KNOWN_NAMESPACES and f'xmlns:{p}=' not in xml]
    if not missing:
        return xml

    m = re.search(r"<([A-Za-z_][\w.-]*)(\s|>)", xml)
    if not m:
        return xml
    insert_at = m.end(1)
    decls = "".join(f' xmlns:{p}="{_KNOWN_NAMESPACES[p]}"' for p in missing)
    return xml[:insert_at] + decls + xml[insert_at:]


def read_musicxml(path: Path) -> str:
    if path.suffix.lower() == ".mxl" or zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as zf:
            score_entry = None
            try:
                with zf.open("META-INF/container.xml") as cf:
                    container = cf.read().decode("utf-8", errors="replace")
                    m = re.search(r'full-path="([^"]+)"', container)
                    if m:
                        score_entry = m.group(1)
            except KeyError:
                pass
            if not score_entry:
                score_entry = next(
                    (n for n in zf.namelist() if n.endswith(".xml") and not n.startswith("META-INF")),
                    None,
                )
            if not score_entry:
                raise ValueError(f"No score XML found in MXL archive: {path}")
            with zf.open(score_entry) as f:
                raw = f.read().decode("utf-8", errors="replace")
    else:
        raw = path.read_text(encoding="utf-8", errors="replace")

    return _repair_xml(raw)


def _load_score(path: Path):
    xml = read_musicxml(path)
    return music21.converter.parse(xml, format="musicxml")


def parse_notes(path: Path, tempo_bpm: float | None = None) -> list[dict]:
    score = _load_score(path)
    out: list[dict] = []
    sec_per_quarter = (60.0 / tempo_bpm) if tempo_bpm else None

    for part in score.parts:
        for element in part.recurse().notes:
            measure_obj = element.getContextByClass(music21.stream.Measure)
            measure_num = measure_obj.number if measure_obj else None
            ql = float(element.duration.quarterLength)
            base_value = element.duration.type
            dots = element.duration.dots
            note_value = ("dotted-" * (1 if dots else 0)) + base_value if base_value != "zero" else ""

            pitches = []
            if hasattr(element, "pitches") and element.pitches:
                pitches = list(element.pitches)
            elif hasattr(element, "pitch"):
                pitches = [element.pitch]

            for p in pitches:
                accidental = p.accidental.modifier if p.accidental is not None else ""
                entry = {
                    "measure": measure_num,
                    "step": p.step,
                    "accidental": accidental,
                    "name": f"{p.step}{accidental}",
                    "octave": p.octave,
                    "name_with_octave": p.nameWithOctave,
                    "midi": p.midi,
                    "duration": ql,
                    "note_value": note_value,
                }
                if sec_per_quarter is not None:
                    entry["seconds"] = round(ql * sec_per_quarter, 3)
                out.append(entry)

    return out


def musicxml_to_midi(xml_path: Path, midi_path: Path) -> Path:
    score = _load_score(xml_path)
    score.write("midi", fp=str(midi_path))
    return midi_path

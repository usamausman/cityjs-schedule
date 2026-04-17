#!/usr/bin/env python3
"""Extract talk details from talks.html and output as JSON."""

import json
import re
from html.parser import HTMLParser


class TalksParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.talks = []
        self.current_track = None
        self.current_talk = None

        # State flags
        self._in_row_title = False
        self._in_event_card = False
        self._in_card_wrapper = False
        self._in_event_time = False
        self._in_event_location = False
        self._in_event_title = False
        self._in_speaker_name = False
        self._in_speaker_company = False
        self._in_tags = False
        self._in_tag = False

        # Depth tracking for nested divs
        self._event_card_depth = 0
        self._card_wrapper_depth = 0
        self._tag_container_depth = 0

        self._tag_buffer = []

    def _has_class(self, attrs, cls):
        classes = dict(attrs).get("class", "")
        return cls in classes.split()

    def _class_contains(self, attrs, fragment):
        classes = dict(attrs).get("class", "")
        return any(fragment in c for c in classes.split())

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        classes = attrs_dict.get("class", "")

        # Track title (h3 inside scheduleRow)
        if tag == "h3" and "schedule-module__XkLJqW__rowTitle" in classes:
            self._in_row_title = True
            return

        # Event card container
        if tag == "div" and "ScheduleEventCard-module__qruiRG__eventCard" in classes:
            self._in_event_card = True
            self._event_card_depth = 1
            self.current_talk = {"track": self.current_track, "time": None, "location": None,
                                 "title": None, "speaker": None, "speaker_role": None, "tags": []}
            return

        if self._in_event_card:
            self._event_card_depth += 1 if tag == "div" else 0

        # Card wrapper (clickable talks have role="button"; non-clickable ones are breaks/registration)
        if tag == "div" and "ScheduleEventCard-module__qruiRG__cardWrapper" in classes:
            self._in_card_wrapper = True
            self._card_wrapper_depth = 1
            return

        if not self._in_card_wrapper:
            return

        # Time
        if tag == "div" and "ScheduleEventCard-module__qruiRG__eventTime" in classes:
            self._in_event_time = True
        elif tag == "div" and "ScheduleEventCard-module__qruiRG__eventLocation" in classes:
            self._in_event_location = True
        elif tag == "h3" and "ScheduleEventCard-module__qruiRG__eventTitle" in classes:
            self._in_event_title = True
        elif tag == "h4" and "ScheduleEventCard-module__qruiRG__speakerName" in classes:
            self._in_speaker_name = True
        elif tag == "p" and "ScheduleEventCard-module__qruiRG__speakerCompany" in classes:
            self._in_speaker_company = True
        elif tag == "div" and "ScheduleEventCard-module__qruiRG__tags" in classes:
            self._in_tags = True
            self._tag_container_depth = 1
        elif self._in_tags and tag == "span" and "ScheduleEventCard-module__qruiRG__tag" in classes:
            self._in_tag = True
            self._tag_buffer = []

        if self._in_card_wrapper and tag in ("div", "span", "p", "h3", "h4"):
            self._card_wrapper_depth += 1 if tag in ("div",) else 0

    def handle_endtag(self, tag):
        if self._in_row_title and tag == "h3":
            self._in_row_title = False

        if self._in_tag and tag == "span":
            self._in_tag = False
            if self.current_talk is not None:
                self.current_talk["tags"].append("".join(self._tag_buffer).strip())

        if self._in_event_time and tag == "div":
            self._in_event_time = False
        if self._in_event_location and tag == "div":
            self._in_event_location = False
        if self._in_event_title and tag == "h3":
            self._in_event_title = False
        if self._in_speaker_name and tag == "h4":
            self._in_speaker_name = False
        if self._in_speaker_company and tag == "p":
            self._in_speaker_company = False

        if self._in_tags and tag == "div":
            self._in_tags = False

        # End of card wrapper
        if self._in_card_wrapper and tag == "div":
            self._card_wrapper_depth -= 1
            if self._card_wrapper_depth <= 0:
                self._in_card_wrapper = False

        # End of event card
        if self._in_event_card and tag == "div":
            self._event_card_depth -= 1
            if self._event_card_depth <= 0:
                self._in_event_card = False
                if self.current_talk and self.current_talk.get("title"):
                    self.talks.append(self.current_talk)
                self.current_talk = None

    def handle_data(self, data):
        text = data.strip()
        if not text:
            return

        if self._in_row_title:
            self.current_track = text
            return

        if self.current_talk is None:
            return

        if self._in_event_time:
            # Only capture the span text (date/time), not SVG content
            if re.match(r'\d{2}-\d{2}-\d{4}', text):
                self.current_talk["time"] = text

        elif self._in_event_location:
            if not text.startswith("<") and len(text) < 100:
                self.current_talk["location"] = text

        elif self._in_event_title:
            self.current_talk["title"] = " ".join(text.split())

        elif self._in_speaker_name:
            self.current_talk["speaker"] = " ".join(text.split())

        elif self._in_speaker_company:
            self.current_talk["speaker_role"] = " ".join(text.split())

        elif self._in_tag:
            self._tag_buffer.append(text)


def main():
    with open("talks.html", "r", encoding="utf-8") as f:
        html = f.read()

    parser = TalksParser()
    parser.feed(html)

    # Remove duplicates (the HTML may repeat cards for mobile/desktop layouts)
    seen = set()
    unique_talks = []
    for talk in parser.talks:
        key = (talk["track"], talk["time"], talk["title"])
        if key not in seen:
            seen.add(key)
            unique_talks.append(talk)

    print(json.dumps(unique_talks, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
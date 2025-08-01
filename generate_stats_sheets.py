#!/usr/bin/env python3
"""
generate_stats_sheets.py

Produces printable weekly stats sheets using ReportLab Platypus.
Modify INTERACTION_TYPES, DURATIONS, and TIME_BLOCKS as needed.
"""

import argparse
import calendar
import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import mm, inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Spacer,
    PageBreak,
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.styles import getSampleStyleSheet

# ------------------ constants section ------------------
INTERACTION_TYPES = [
    "3d services",
    "video games",
    "crafts",
    "sewing machines",
    "vinyl cutter",
    "podcasting",
    "general library",
    "other"

]
DURATIONS = [" "]  # under 10 min, 10–30, over 30
TIME_BLOCKS = ["8a-10a", "10a-12p", "12p-2p", "2p-4p", "4p-6p", "6p-8p"]

SCRIPT_VERSION = "0.4"
DATE_FMT = "%Y-%m-%d"

# page layout constants
LEFT_MARGIN = 0.25 * inch
RIGHT_MARGIN = 0.25 * inch
TOP_MARGIN = 1 * inch
BOTTOM_MARGIN = 0.25 * inch
HEADER_HEIGHT = 16  # pts for header row
SUBHEADER_HEIGHT = 16  # pts for sub-header row
NOTES_HEIGHT = 8 * 12  # pts (3 lines at 12pt)


# ------------------ helper / layout functions ------------------


def iso_week_monday(any_date: datetime.date) -> datetime.date:
    """Return the Monday of the ISO week containing any_date."""
    return any_date - datetime.timedelta(days=any_date.weekday())


class WeekDocTemplate(SimpleDocTemplate):
    """Custom SimpleDocTemplate to inject per-page headers/footers with week mapping."""

    def __init__(self, filename, week_starts, name="Library", *args, **kwargs):
        super().__init__(filename, *args, **kwargs)
        self.week_starts = week_starts  # list of datetime.date for each page
        self.name = name
        self.gen_timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def handle_pageBegin(self):
        # override to ensure page count is updated before drawing
        super().handle_pageBegin()

    def beforePage(self):
        # called before drawing each page; draw header/footer here
        canvas = self.canv
        page_num = canvas.getPageNumber()
        # safety: if page_num exceeds provided weeks, use last
        try:
            week_start = self.week_starts[page_num - 1]
        except IndexError:
            week_start = self.week_starts[-1]
        header_text = f"{self.name} – Daily Stats Sheet – Date {week_start.strftime(DATE_FMT)}"
        footer_text = f"Generated: {self.gen_timestamp} | version: {SCRIPT_VERSION}"
        # header
        canvas.saveState()
        height = self.pagesize[1]
        canvas.setFont("Helvetica-Bold", 11)
        canvas.drawString(inch * 0.75, height - 0.65 * inch, header_text)
        # footer
        canvas.setFont("Helvetica", 8)
        canvas.drawString(inch * 0.75, 0.5 * inch - 4, footer_text)
        canvas.restoreState()


def build_day_page(day: datetime.date) -> Table:
    """
    Build the stats table for a single day (portrait, time blocks as columns).
    """
    # prepare headers: time axis across columns
    first_row = ["Interaction Type"]
    for blk in TIME_BLOCKS:
        first_row.extend([blk] + [""] * (len(DURATIONS) - 1))
    second_row = [" "]
    for _ in TIME_BLOCKS:
        second_row.extend(DURATIONS)
    data = [first_row, second_row]
    # one row per interaction type
    for itype in INTERACTION_TYPES:
        data.append([itype] + [""] * (len(TIME_BLOCKS) * len(DURATIONS)))
    # compute column widths to fill page width
    usable_width = letter[0] - (LEFT_MARGIN + RIGHT_MARGIN)
    time_col_w = 30 * mm
    total_dur_cols = len(TIME_BLOCKS) * len(DURATIONS)
    dur_col_w = (usable_width - time_col_w) / total_dur_cols
    col_widths = [time_col_w] + [dur_col_w] * total_dur_cols
    # compute custom row heights: header, subheader, then one per interaction
    body_rows = len(INTERACTION_TYPES)
    usable_height = (
        letter[1]
        - TOP_MARGIN
        - BOTTOM_MARGIN
        - HEADER_HEIGHT
        - SUBHEADER_HEIGHT
        - NOTES_HEIGHT
        - (20 * mm)
    )
    body_h = usable_height / body_rows
    row_heights = [HEADER_HEIGHT, SUBHEADER_HEIGHT] + [body_h] * body_rows
    # build table with custom row heights
    table = Table(data, colWidths=col_widths, rowHeights=row_heights, repeatRows=2)
    style = TableStyle()
    # span each time-block header across its duration cols
    for i in range(len(TIME_BLOCKS)):
        start = 1 + i * len(DURATIONS)
        end = start + len(DURATIONS) - 1
        style.add("SPAN", (start, 0), (end, 0))
    # header styling
    style.add("FONTNAME", (0, 0), (-1, 1), "Helvetica-Bold")
    style.add("FONTSIZE", (0, 0), (-1, 1), 9)
    style.add("ALIGN", (0, 0), (-1, 1), "CENTER")
    style.add("VALIGN", (0, 0), (-1, -1), "MIDDLE")
    style.add("BACKGROUND", (0, 0), (-1, 0), colors.whitesmoke)
    style.add("BACKGROUND", (0, 1), (-1, 1), colors.lightgrey)
    # grid for tick cells
    style.add("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#BBBBBB"))
    # alternate shading for time-block columns (data rows only)
    for i in range(len(TIME_BLOCKS)):
        if i % 2 == 1:
            start = 1 + i * len(DURATIONS)
            end = start + len(DURATIONS) - 1
            style.add("BACKGROUND", (start, 2), (end, -1), colors.lightgrey)
    table.setStyle(style)
    return table


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate weekly stats sheets PDF."
    )
    parser.add_argument(
        "--start",
        type=str,
        default=None,
        help="Start date (any date in week) in YYYY-MM-DD, defaults to current date's week.",
    )
    parser.add_argument(
        "--weeks",
        type=int,
        default=1,
        help="Number of consecutive ISO weeks to generate (default 1).",
    )
    parser.add_argument(
        "--outfile",
        type=str,
        default="stats_sheets.pdf",
        help="Output PDF path (default stats_sheets.pdf).",
    )
    parser.add_argument(
        "--name",
        type=str,
        default="Library",
        help="Display name for header (default 'Library').",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    # determine first week Monday
    if args.start:
        try:
            given = datetime.datetime.strptime(args.start, DATE_FMT).date()
        except ValueError:
            raise SystemExit(f"Bad --start date format, expected YYYY-MM-DD: {args.start}")
    else:
        given = datetime.date.today()
    first_monday = iso_week_monday(given)

    # build list of week start dates
    week_starts = [first_monday + datetime.timedelta(weeks=i) for i in range(args.weeks)]

    # expand to individual days, one page each
    days = []
    for ws in week_starts:
        for d in range(7):
            days.append(ws + datetime.timedelta(days=d))

    # set up document with custom header/footer
    doc = WeekDocTemplate(
        args.outfile,
        week_starts=days,
        name=args.name,
        pagesize=letter,
        rightMargin=0.25 * inch,
        leftMargin=0.25 * inch,
        topMargin=1 * inch,
        bottomMargin=0.25 * inch,
    )

    story = []

    for idx, day in enumerate(days):
        # page table
        story.append(build_day_page(day))
        story.append(Spacer(0, 5 * mm))
        # notes table box
        usable_width = letter[0] - LEFT_MARGIN - RIGHT_MARGIN
        notes_tbl = Table(
            [["Notes:"]],
            colWidths=[usable_width],
            rowHeights=[NOTES_HEIGHT],
        )
        notes_tbl.setStyle(TableStyle([
            ("BOX", (0,0), (-1,-1), 0.5, colors.black),
            ("VALIGN", (0,0), (-1,-1), "TOP"),
            ("LEFTPADDING", (0,0), (-1,-1), 3),
        ]))
        story.append(notes_tbl)
        if idx != len(days) - 1:
            story.append(PageBreak())

    # build PDF
    doc.build(
        story,
        onFirstPage=lambda canvas, doc: doc.beforePage(),
        onLaterPages=lambda canvas, doc: doc.beforePage(),
    )


if __name__ == "__main__":
    main()
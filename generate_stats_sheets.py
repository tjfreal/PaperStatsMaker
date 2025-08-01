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
from reportlab.lib.pagesizes import letter, landscape
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
    "3d model",
    "3d print",
    "3d scan",
    "software",
    "sewing machines",
    "vinyl cutter",
    "podcasting",
    "virtual reality",
]
DURATIONS = ["<5", "5-15", ">15"]  # under 10 min, 10–30, over 30
TIME_BLOCKS = ["8a-10a", "10a-12p", "12p-2p", "2p-4p", "4p-6p"]
SCRIPT_VERSION = "0.2"
DATE_FMT = "%Y-%m-%d"


# ------------------ helper / layout functions ------------------


def iso_week_monday(any_date: datetime.date) -> datetime.date:
    """Return the Monday of the ISO week containing any_date."""
    return any_date - datetime.timedelta(days=any_date.weekday())


class WeekDocTemplate(SimpleDocTemplate):
    """Custom SimpleDocTemplate to inject per-page headers/footers with week mapping."""

    def __init__(self, filename, week_starts, *args, **kwargs):
        super().__init__(filename, *args, **kwargs)
        self.week_starts = week_starts  # list of datetime.date for each page
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
        header_text = f"Library – Weekly Stats Sheet – Week of {week_start.strftime(DATE_FMT)}"
        footer_text = f"Generated: {self.gen_timestamp} | version: {SCRIPT_VERSION}"
        # header
        canvas.saveState()
        height = self.pagesize[1]
        canvas.setFont("Helvetica-Bold", 11)
        canvas.drawString(inch * 0.75, letter[1] - 0.65 * inch, header_text)
        # footer
        canvas.setFont("Helvetica", 8)
        canvas.drawString(inch * 0.75, 0.5 * inch - 4, footer_text)
        canvas.restoreState()


def build_week_page(monday: datetime.date) -> Table:
    """
    Build the main table for one ISO week starting on monday.
    Returns a Platypus Table (ready to go).
    """
    # Prepare header rows
    # Top header: "Time Block" + each interaction type spanning 3 columns
    first_row = ["Time Block"]
    for itype in INTERACTION_TYPES:
        first_row.extend([itype, "", ""])  # placeholders for colspan effect
    # Second header: durations under each interaction type
    second_row = [""]  # time block blank
    for _ in INTERACTION_TYPES:
        second_row.extend(DURATIONS)

    data = [first_row, second_row]

    # Build body: for each day Monday->Sunday, insert a day separator row then blocks
    for day_offset in range(7):
        day = monday + datetime.timedelta(days=day_offset)
        day_label = day.strftime("%A %Y-%m-%d")
        # day separator full-width
        sep_row = [day_label] + [""] * (1 + len(INTERACTION_TYPES) * len(DURATIONS) - 1)
        data.append(sep_row)
        # 5 blocks: 08-10, 10-12, 12-14, 14-16, 16-18
        for block_label in TIME_BLOCKS:
            row = [block_label]
            # one small square cell per duration per interaction type
            for _ in INTERACTION_TYPES:
                for _ in DURATIONS:
                    row.append("")  # cell to tick
            data.append(row)

    # Column widths: time block about 15 mm, durations approx 10 mm each
    time_block_w = 15 * mm
    duration_w = 10 * mm
    col_widths = [time_block_w] + [duration_w] * (len(INTERACTION_TYPES) * len(DURATIONS))

    table = Table(data, colWidths=col_widths, repeatRows=2, hAlign="LEFT")

    # Styling: light grid, header shading, alignments, fixed cell size for tick boxes
    style = TableStyle()

    # span interaction type headers over their duration columns
    for i in range(len(INTERACTION_TYPES)):
        start = 1 + i * len(DURATIONS)
        end = start + len(DURATIONS) - 1
        style.add("SPAN", (start, 0), (end, 0))

    # top header style
    style.add("FONTNAME", (0, 0), (-1, 1), "Helvetica-Bold")
    style.add("FONTSIZE", (0, 0), (-1, 1), 8)
    style.add("ALIGN", (0, 0), (-1, 1), "CENTER")
    style.add("VALIGN", (0, 0), (-1, -1), "MIDDLE")
    style.add("BACKGROUND", (0, 0), (-1, 0), colors.whitesmoke)
    style.add("BACKGROUND", (0, 1), (-1, 1), colors.lightgrey)

    # locate row indexes: after headers, every (1 + len(TIME_BLOCKS)) rows per day, starting at index 2
    for i in range(7):
        row_index = 2 + i * (1 + len(TIME_BLOCKS))
        style.add("SPAN", (0, row_index), (len(col_widths) - 1, row_index))
        style.add("FONTNAME", (0, row_index), (-1, row_index), "Helvetica-Bold")
        style.add("FONTSIZE", (0, row_index), (-1, row_index), 9)
        style.add("BACKGROUND", (0, row_index), (-1, row_index), colors.lightgrey)
        style.add("ALIGN", (0, row_index), (-1, row_index), "LEFT")
        style.add("LEFTPADDING", (0, row_index), (-1, row_index), 4)

    # Grid for all tick cells: light border
    style.add("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#BBBBBB"))
    # Set fixed row heights so squares approximate size: each duration cell ~14pt tall
    # Can't easily set per-row height here; rely on default with small font to keep compact.

    # Ensure time block column aligns left for labels
    style.add("ALIGN", (0, 2), (0, -1), "LEFT")
    style.add("LEFTPADDING", (0, 2), (0, -1), 3)

    # Minimal padding for tick boxes to keep them small
    style.add("LEFTPADDING", (1, 2), (-1, -1), 2)
    style.add("RIGHTPADDING", (1, 2), (-1, -1), 2)
    style.add("TOPPADDING", (1, 2), (-1, -1), 2)
    style.add("BOTTOMPADDING", (1, 2), (-1, -1), 2)

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

    # set up document with custom header/footer
    doc = WeekDocTemplate(
        args.outfile,
        week_starts=week_starts,
        pagesize=landscape(letter),
        rightMargin=0.4 * inch,
        leftMargin=0.4 * inch,
        topMargin=1 * inch,
        bottomMargin=0.9 * inch,
    )

    story = []

    for idx, wk in enumerate(week_starts):
        tbl = build_week_page(wk)
        story.append(tbl)
        if idx != len(week_starts) - 1:
            story.append(PageBreak())

    # build PDF
    doc.build(
        story,
        onFirstPage=lambda canvas, doc: doc.beforePage(),
        onLaterPages=lambda canvas, doc: doc.beforePage(),
    )


if __name__ == "__main__":
    main()
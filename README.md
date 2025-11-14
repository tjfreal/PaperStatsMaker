# PaperStatsMaker

A Python tool for generating printable PDF statistics tracking sheets, designed for libraries, makerspaces, and community spaces to manually record visitor interactions throughout the day.

## Overview

PaperStatsMaker creates daily tracking forms with a grid layout where staff can tick boxes to record different types of visitor activities during specific time blocks. The generated PDFs can be printed and used for manual data collection at physical locations.

## Features

- **Daily tracking pages**: One page per day with a comprehensive grid layout
- **Time-block tracking**: Day divided into 2-hour segments (8am-10am, 10am-12pm, 12pm-2pm, 2pm-4pm, 4pm-6pm, 6pm-8pm)
- **Multiple interaction types**: Pre-configured categories for different services
- **Notes section**: Each page includes dedicated space for staff notes
- **Multi-week generation**: Create sheets for multiple weeks in a single PDF
- **Customizable headers**: Set your organization name in the header
- **Professional layout**: Clean, printable format optimized for letter-sized paper

## Tracked Interaction Types

The default configuration tracks the following interaction types:
- 3D services
- Video games
- Crafts
- Sewing machines
- Vinyl cutter
- Podcasting
- General library
- Other

## Requirements

- Python 3.6+
- ReportLab library

## Installation

1. Clone this repository:
```bash
git clone https://github.com/tjfreal/PaperStatsMaker.git
cd PaperStatsMaker
```

2. Install dependencies:
```bash
pip install reportlab
```

## Usage

### Basic Usage

Generate sheets for the current week:
```bash
python generate_stats_sheets.py
```

This creates `stats_sheets.pdf` with 7 pages (one per day) for the current ISO week.

### Advanced Usage

Generate sheets for a specific date range:
```bash
python generate_stats_sheets.py --start 2025-01-13 --weeks 4 --outfile january_stats.pdf
```

Customize the organization name:
```bash
python generate_stats_sheets.py --name "Community Makerspace" --weeks 2
```

### Command-Line Options

- `--start`: Start date (YYYY-MM-DD format). Can be any date in the desired week; the script will automatically find the Monday of that week. Defaults to current week.
- `--weeks`: Number of consecutive ISO weeks to generate (default: 1)
- `--outfile`: Output PDF filename (default: `stats_sheets.pdf`)
- `--name`: Organization name displayed in the header (default: `Library`)

### Example Commands

```bash
# Generate 4 weeks starting from January 13, 2025
python generate_stats_sheets.py --start 2025-01-13 --weeks 4

# Generate 1 week for a specific library
python generate_stats_sheets.py --name "City Central Library" --outfile city_central_stats.pdf

# Generate entire month (4 weeks)
python generate_stats_sheets.py --start 2025-02-01 --weeks 4 --name "Makerspace Lab"
```

## Customization

To customize the tracked interaction types, durations, or time blocks, edit the constants at the top of `generate_stats_sheets.py`:

```python
INTERACTION_TYPES = [
    "3d services",
    "video games",
    "crafts",
    # Add your custom types here
]

TIME_BLOCKS = ["8a-10a", "10a-12p", "12p-2p", "2p-4p", "4p-6p", "6p-8p"]
```

## Output Format

Each generated page includes:
- **Header**: Organization name, date, and "Daily Stats Sheet" label
- **Grid table**: Interaction types (rows) × Time blocks (columns)
- **Notes section**: Text box for additional observations
- **Footer**: Generation timestamp and script version

## Use Cases

- **Libraries**: Track patron usage of different resources and services
- **Makerspaces**: Monitor equipment usage throughout the day
- **Community centers**: Record activity participation by time of day
- **Museums**: Track visitor engagement with different exhibits

## Version

Current version: 0.4

## License

This project is provided as-is for use in tracking visitor statistics at community spaces.

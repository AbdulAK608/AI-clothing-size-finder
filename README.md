# AI Clothing Size Finder

A Python/Flask web app that recommends a clothing size based on your body measurements and a product's size chart.

Enter your measurements, pick a clothing category and fit preference, and the app compares your measurements against a size chart to recommend the best-fitting size — with a confidence level and a plain-English explanation.

## Overview

Buying clothes online is frustrating when sizes vary by brand and country. This app solves that by comparing **actual body measurements** against **actual garment measurements** rather than relying on arbitrary size labels like "M" or "XL".

The core sizing logic is written in plain Python — no machine learning, no paid APIs. Every decision the app makes is transparent and explainable.

## Features

- **Body measurement input** — chest, waist, hips, shoulder, sleeve, inseam, thigh, foot, head
- **Unit conversion** — heights like `5'8"`, weights like `208 lb`, lengths in cm or inches
- **Clothing category awareness** — shirts use chest/shoulder/waist; pants use waist/hips/inseam; shoes use foot length/width; hats use head circumference
- **Fit preference** — fitted, regular, relaxed, oversized, or not sure
- **Size recommendation** — best match plus an alternative if you fall between sizes
- **Confidence level** — High / Medium / Low, based on how many measurements matched
- **Plain-English explanation** — tells you exactly why it picked that size
- **International-friendly** — all comparisons use centimeters internally; labels are just labels

## How It Works
User measurements (any units)
|
v
Normalize to cm / kg (conversions.py)
|
v
Pick relevant measurements by clothing type
|
v
Score each size in the chart (sizing.py)
|
v
Apply fit-preference tiebreaker
|
v
Detect between-size ties and expose alternative
|
v
Assign confidence + generate explanation
|
v
Render results page (Flask + Jinja2)

text

### The scoring rule

For each size, every relevant measurement is compared:

- Inside the size's range -> **+2 points**
- Just outside (within 3 cm) -> **+1 point** (near-miss)
- Way outside -> **0 points**
- Missing measurement -> skipped

The size with the highest score wins. A small **+/-1 fit-preference bias** is applied only to break ties, so it can never override clear measurement evidence.

## Technologies

- **Python 3** — core logic
- **Flask** — web framework
- **Jinja2** — HTML templating (comes with Flask)
- **HTML / CSS** — frontend
- **Git / GitHub** — version control

## Project Structure
ai-clothing-size-finder/
├── app.py # Flask routes + demo size charts
├── conversions.py # Height/weight/length unit parsers
├── sizing.py # Recommendation engine
├── test_boundary.py # Boundary-case tests for the engine
├── requirements.txt
├── .gitignore
├── templates/
│ ├── index.html
│ └── results.html
└── static/
└── style.css

text

## Installation

Clone the repository and set up a virtual environment:

```bash
git clone https://github.com/AbdulAK608/AI-clothing-size-finder.git
cd AI-clothing-size-finder

# Create and activate a virtual environment
python -m venv venv
source venv/Scripts/activate     # Windows Git Bash
# OR
venv\Scripts\Activate.ps1        # Windows PowerShell
# OR
source venv/bin/activate         # macOS / Linux

# Install dependencies
pip install -r requirements.txt


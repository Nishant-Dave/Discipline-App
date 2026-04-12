# Discipline App

A disciplined, proof-based task enforcement system designed to help users maintain consistency and accountability through strict task management, consequence tracking, and actionable analytics.

## Features
- **Proof-Based Completion:** Requires photographic evidence for high-stakes tasks.
- **Consequence Engine:** Automatically applies penalties for missed deadlines based on task severity (Easy, Medium, Hard).
- **Streak Tracking:** Monitors current and longest discipline streaks.
- **Analytics Dashboard:** Visualize your weekly and monthly performance with interactive charts.
- **Activity Logging:** Comprehensive audit trail of all actions and task completions.
- **Real-time UI:** Built with HTMX and Alpine.js for a seamless, fast, and responsive user experience.

## Tech Stack
- **Framework:** Django
- **API:** Django Rest Framework (DRF)
- **Frontend:** Tailwind CSS, HTMX, Alpine.js
- **Visualization:** Chart.js

## Setup Instructions

### Prerequisites
- Python 3.10+
- Node.js (for Tailwind CSS development)

### Installation
1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd discipline_app
   ```
2. Create and activate virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Configure environment variables:
   Create a `.env` file and set `DEBUG=True`, `SECRET_KEY`, and `DATABASE_URL`.

5. Run migrations:
   ```bash
   python manage.py migrate
   ```
6. Start the development server:
   ```bash
   python manage.py runserver
   ```

## Live Demo
[Link to live application placeholder]

# Comment Copilot 🚀

A powerful YouTube comment management platform that helps content creators efficiently manage, categorize, and respond to comments using AI-powered automation.

## Features ✨

- **AI-Powered Comment Classification**: Automatically categorizes comments into actionable groups using Google's Gemini API
- **Real-time Comment Sync**: Fetch and process latest YouTube comments on demand
- **Secure Authentication**: Google OAuth 2.0 integration for secure YouTube account access
- **Smart Categorization**: Comments are automatically sorted into:
  - Reply to Question
  - Appreciate Fan
  - Ideas
  - Criticisms
  - Delete Junk
  - Miscellaneous
- **Direct Reply Interface**: Reply to comments directly from the dashboard
- **Modern UI**: Responsive and intuitive interface built with React and Tailwind CSS

## Tech Stack 🛠️

### Backend

- **Framework**: Flask (Python)
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Authentication**: Google OAuth 2.0
- **Task Queue**: Celery with Redis
- **AI Integration**: Google Gemini API
- **API Integration**: YouTube Data API v3

### Frontend

- **Framework**: React with TypeScript
- **Build Tool**: Vite
- **State Management**: TanStack Query
- **Routing**: TanStack Router
- **Styling**: Tailwind CSS, Radix UI
- **Code Quality**: ESLint, Prettier

## Getting Started 🚀

### Prerequisites

- Python 3.8+
- Node.js 16+
- PostgreSQL
- Redis

### Backend Setup

1. Navigate to the backend directory:

```bash
cd commco_backend
```

2. Create and activate a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Set up environment variables:

```bash
cp .env.example .env
# Edit .env with your configuration
```

5. Initialize the database:

```bash
flask db upgrade
```

6. Run the development server:

```bash
python run.py
```

### Frontend Setup

1. Navigate to the frontend directory:

```bash
cd commco_frontend
```

2. Install dependencies:

```bash
npm install
```

3. Set up environment variables:

```bash
cp .env.example .env
# Edit .env with your configuration
```

4. Run the development server:

```bash
npm run dev
```

## Project Structure 📁

```
comment-copilot/
├── commco_backend/           # Backend Flask application
│   ├── app/                 # Application code
│   │   ├── models.py       # Database models
│   │   ├── routes.py       # API endpoints
│   │   ├── services.py     # Business logic
│   │   └── tasks.py        # Celery tasks
│   └── migrations/         # Database migrations
└── commco_frontend/         # Frontend React application
    ├── src/
    │   ├── components/     # React components
    │   ├── context/        # React context
    │   ├── hooks/         # Custom hooks
    │   ├── queries/       # API queries
    │   └── routes/        # Application routes
    └── public/            # Static assets
```

## API Documentation 📚

### Authentication Endpoints

- `GET /api/auth/google/login`: Initiates Google OAuth flow
- `GET /api/auth/google/callback`: Handles OAuth callback
- `POST /api/auth/logout`: Logs out the user

### Comment Management Endpoints

- `GET /api/comments`: Fetches categorized comments
- `POST /api/channel/sync`: Triggers comment synchronization
- `POST /api/comments/{id}/reply`: Replies to a specific comment

## Contributing 🤝

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License 📝

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments 🙏

- Google YouTube Data API
- Google Gemini API
- All open-source libraries used in this project

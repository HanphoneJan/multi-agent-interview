# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an **AI Interview Agent** system with a dual-backend architecture:

- **Django Backend** (`django/`): Main backend with WebSocket support (Daphne), handling user management, interviews, evaluations, and learning management
- **FastAPI Backend** (`fastapi/`): Async API service handling real-time interview sessions and WebSocket communications
- **Database**: PostgreSQL (shared between both backends)

## Architecture

### Django Backend (`django/`)

Django 5.2.3 with ASGI support via Daphne, using Django REST Framework for APIs and Django Channels for WebSockets.

**Key Apps:**
- `user_manager` - User authentication, JWT tokens (simplejwt), WeChat mini-program integration
- `interview_manager` - Interview sessions, scheduling, real-time communication
- `evaluation_system` - Performance evaluation and scoring
- `learning_manager` - Learning materials and progress tracking

**Key Configuration:**
- ASGI application: `AiInterviewAgent.asgi.application`
- Custom user model: `user_manager.User`
- JWT authentication with 30min access / 1 day refresh tokens
- CORS enabled for all origins (development)
- Media files served from `media/` directory

### FastAPI Backend (`fastapi/`)

Modern async Python API with SQLAlchemy ORM and Alembic migrations.

**Key Structure:**
- `app/api/v1/` - API routes (versioned)
- `app/models/` - SQLAlchemy models
- `app/services/` - Business logic
- `app/websockets/` - WebSocket handlers
- `app/config.py` - Pydantic settings management
- `alembic/` - Database migrations

**Configuration:**
- Settings loaded from `.env` via Pydantic
- Development docs at `/docs` and `/redoc`
- GZip compression enabled
- CORS middleware configured

## Common Commands

### Django Backend

```bash
cd django

# Development server (with hot reload)
python manage.py runserver

# Production ASGI server
daphne -b 0.0.0.0 -p 8000 AiInterviewAgent.asgi:application

# Database migrations
python manage.py makemigrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Shell
python manage.py shell

# Collect static files
python manage.py collectstatic
```

### FastAPI Backend

```bash
cd fastapi

# Using uv (recommended)
uv sync                              # Install dependencies
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Or activate venv manually
.venv\Scripts\activate               # Windows
source .venv/bin/activate            # Unix
uvicorn app.main:app --reload

# Database migrations (Alembic)
uv run alembic revision --autogenerate -m "description"
uv run alembic upgrade head
uv run alembic downgrade -1

# Using Python directly
uv run python app/main.py
```

### Testing

**Django:**
```bash
cd django
python manage.py test
python manage.py test app_name.TestClass.test_method  # Single test
```

**FastAPI:**
```bash
cd fastapi
pytest
pytest -xvs tests/test_file.py::test_function  # Single test with verbose output
pytest -k "test_name_pattern"  # Run tests matching pattern
```

### Docker

```bash
# Build and run both services
docker-compose up --build

# Run in background
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## Environment Configuration

Both backends require `.env` files with these key variables:

**Django** (`django/.env`):
- `SECRET_KEY` - Django secret key
- `DATABASE_NAME`, `DATABASE_USER`, `DATABASE_PASSWORD`, `DATABASE_HOST`, `DATABASE_PORT`
- `SIGNING_KEY` - JWT signing key
- `WECHAT_APP_ID`, `WECHAT_APP_SECRET` - WeChat mini-program credentials
- `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` - SMTP settings

**FastAPI** (`fastapi/.env`):
- `DATABASE_URL` - PostgreSQL connection string
- `APP_NAME`, `VERSION` - Application metadata
- `HOST`, `PORT` - Server binding
- `DEBUG` - Enable debug mode

## Development Notes

- **WebSocket Timeout**: Django Daphne timeout set to 600 seconds (`DAPHNE_TIMEOUT`)
- **Media Files**: Django serves user-uploaded files from `media/` directory
- **Logging**: Django logs to both console and `logs/django.log`
- **FFmpeg**: Required for media processing; path configured in `settings.py`
- **CORS**: Both backends have CORS enabled for all origins in development

## Development Workflow

### Task Completion Checklist

**Before marking any task as complete, you MUST:**

1. **Run relevant tests:**
   - API changes: `pytest app/tests/test_api/ -v`
   - WebSocket changes: `pytest app/tests/test_websockets.py -v`
   - Service changes: `pytest app/tests/test_services/ -v`
   - Single test: `pytest path/to/test.py::test_function -xvs`

2. **Verify functionality:**
   - Core feature works as expected
   - Exception handling is tested
   - Return data format is correct

3. **Update documentation:**
   - Update `fastapi/docs/REFACTOR_PLAN.md` when completing tasks
   - Mark completed tasks with ✅
   - Update progress percentage in section 6.0
   - Add version history entry

### Testing Requirements

**New features must include:**
- Unit tests for core logic
- Integration tests for API endpoints
- Edge case coverage
- Error path testing

**Test commands (using uv):**
```bash
cd fastapi
uv run pytest                          # Run all tests
uv run pytest -x                       # Stop on first failure
uv run pytest --tb=short               # Short traceback
uv run pytest -k "websocket"           # Run tests matching pattern
uv run pytest app/tests/test_api/ -v   # API tests only
uv run pytest app/tests/test_recommenders/ -v  # Recommender tests
```

### Documentation Updates

**When completing tasks in FastAPI:**
1. Read `fastapi/docs/REFACTOR_PLAN.md`
2. Update the "6.0 当前实施进度" table
3. Add completed tasks to "已完成任务" section
4. Update "下一步" section
5. Increment version in "文档版本历史"

**Example update:**
```markdown
**已完成任务：**
- ✅ **任务名称**（步骤X）
  - ✅ 子任务1
  - ✅ 子任务2

**文档版本历史**：
- v1.2（2026-02-26）：完成任务X，启动任务Y
```

## Code Standards

### Python Style
- Follow **PEP 8** code style
- Use **type hints** for all function parameters and return values
- Use **Pydantic** models for data validation

### FastAPI Patterns
- **SQLAlchemy Core** (not ORM) for database operations
- **Pydantic Schema** for data validation
- Full **async/await** throughout the chain
- Business logic in `app/services/`

### Git Commit Convention
```
[module] type: description

Details (optional):
- Feature details
- Fixed issues
- Notes

Related Issue: #123
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Code formatting
- `refactor`: Refactoring
- `test`: Tests
- `chore`: Build/tools

**Example:**
```
[interview_manager] feat: Add interview recording

- Implement audio/video recording
- Support format conversion
- Add recording duration limit

Related Issue: #45
```

### UniApp Frontend (`uniapp/`)

Vue 3 + UniApp 跨平台应用，支持微信小程序和 H5。

**Key Features:**
- **主题系统**: 基于 CSS 变量，参考 DeepSeek 配色方案
  - 主色调: `#3964fe` (deepseek-500)
  - 配置位于 `uniapp/src/styles/theme.css`
  - 文档见 `uniapp/docs/THEME.md`
- **图标库**: Font Awesome 6 (CDN 引入)
  - 使用方式: `<text class="fa-solid fa-icon-name"></text>`
  - 规则见 `.claude/rules/ui-icons.mdc`
- **状态管理**: Pinia (`stores/`)
- **HTTP 客户端**: 基于 uni.request 的封装 (`stores/request.js`)

**Key Directories:**
- `src/pages/` - 页面组件
- `src/components/` - 公共组件
- `src/stores/` - Pinia stores
- `src/styles/` - 全局样式、主题变量
- `src/static/` - 静态资源

## Project Structure

```
Ai-Interview-Agent/
├── django/                    # Django backend
│   ├── AiInterviewAgent/     # Project settings
│   ├── user_manager/         # User management app
│   ├── interview_manager/    # Interview logic app
│   ├── evaluation_system/    # Evaluation/scoring app
│   ├── learning_manager/     # Learning materials app
│   ├── logs/                 # Log files
│   └── media/                # User-uploaded files
├── fastapi/                   # FastAPI backend
│   ├── app/
│   │   ├── api/v1/          # API routes
│   │   ├── models/          # SQLAlchemy models
│   │   ├── services/        # Business logic
│   │   ├── websockets/      # WebSocket handlers
│   │   ├── config.py        # Settings
│   │   └── main.py          # Entry point
│   ├── alembic/             # Database migrations
│   ├── tests/               # Test files
│   └── docs/                # Documentation (REFACTOR_PLAN.md, etc.)
├── uniapp/                    # UniApp frontend
│   ├── src/
│   │   ├── pages/           # Pages
│   │   ├── components/      # Components
│   │   ├── stores/          # Pinia stores
│   │   ├── styles/          # Global styles, theme
│   │   └── static/          # Static assets
│   └── docs/                # Frontend docs
└── scripts/                   # Utility scripts
```

## Skill routing

When the user's request matches an available skill, ALWAYS invoke it using the Skill
tool as your FIRST action. Do NOT answer directly, do NOT use other tools first.
The skill has specialized workflows that produce better results than ad-hoc answers.

Key routing rules:
- Product ideas, "is this worth building", brainstorming → invoke office-hours
- Bugs, errors, "why is this broken", 500 errors → invoke investigate
- Ship, deploy, push, create PR → invoke ship
- QA, test the site, find bugs → invoke qa
- Code review, check my diff → invoke review
- Update docs after shipping → invoke document-release
- Weekly retro → invoke retro
- Design system, brand → invoke design-consultation
- Visual audit, design polish → invoke design-review
- Architecture review → invoke plan-eng-review
- Save progress, checkpoint, resume → invoke checkpoint
- Code quality, health check → invoke health

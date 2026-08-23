# AIeyu

## 中文

AIeyu 是一款面向俄语考试的学生端 AI 自适应备考助手。项目当前以俄语专业八级为第一版 MVP，目标是根据学生真实作答表现建立能力画像，识别薄弱题型与知识点，并结合题库、RAG 知识库和 AI 生成能力，持续提供个性化、不重复的专项训练。

这个项目不包含教师端，核心体验面向学生：做题、批改、错题解析、追问、复习、背单词。

### 当前功能

- 学生账号注册、登录和会话隔离
- 俄语专八题库组卷
- 支持语法、文学、国情、阅读等题型
- 阅读题按文章成组展示
- 自动判分和错题记录
- 基于 DeepSeek API 的中文错题讲解
- 可继续追问的 AI 对话窗口
- 用户画像与题型掌握度统计
- 错题本功能
- 单词打卡与复习词库
- AI 仿真题生成与人工审核链路
- RAG 知识块召回，用于辅助生成国情等题目
- PDF / OCR 数据处理脚本

### 技术框架

当前版本采用轻量化 Python 服务和静态前端，便于快速试用、部署和迭代。

```text
apps/student_web/static/      学生端网页
scripts/serve_student_app.py  本地与服务器启动入口
scripts/                     数据抽取、题库导入、词库清洗、质量检查脚本
database/                    本地 SQLite 数据库目录
docs/                        产品记录、需求文档和开发上下文
prompts/                     AI 讲解和生成题提示词
data/                        原始资料和处理产物，本仓库默认忽略
```

### 数据与版权说明

本仓库默认不提交以下内容：

- `.env`
- SQLite 数据库
- 真题 PDF
- 扫描书籍 PDF
- OCR 中间产物
- 听力音频
- 其他可能含版权或学生隐私的数据

如果你在本地或服务器部署，需要自行准备数据库和资料文件。

### 环境配置

复制 `.env.example` 为 `.env`，并填写 DeepSeek 配置：

```env
DEEPSEEK_API_KEY=your_deepseek_api_key_here
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-v4-flash
DEEPSEEK_THINKING=disabled
DEEPSEEK_REASONING_EFFORT=high
```

### 启动

在项目根目录运行：

```powershell
python scripts\serve_student_app.py --host 127.0.0.1 --port 8765
```

局域网或服务器测试：

```powershell
python scripts\serve_student_app.py --host 0.0.0.0 --port 8765
```

浏览器访问：

```text
http://127.0.0.1:8765/
```

服务器部署时，请保留：

```text
C:\AIeyu\.env
C:\AIeyu\database\russian_ai_tutor.sqlite
```

不要用更新包覆盖这两个文件，否则会丢失 API 配置、学生账号和学习记录。

### 词库质量修正

项目包含确定性词库修正脚本：

```powershell
python scripts\apply_vocabulary_quality_fixes.py
```

脚本会先备份数据库，再修正常见 OCR 错误，并导出剩余可疑项表。

### 当前产品阶段

AIeyu 仍处于 MVP 和内部测试阶段。当前重点不是公开大规模上线，而是验证：

- 学生是否愿意持续使用
- AI 错题讲解是否真正有帮助
- 用户画像是否能指导专项训练
- 题库和 AI 生成题能否形成可控、可审核的闭环

后续规划包括更多等级考试、听力训练、热点新闻听力、背单词体系增强、更加完整的 RAG 知识库和商业化部署。

---

## Русский

AIeyu — это студенческий AI-помощник для подготовки к экзаменам по русскому языку. Первая MVP-версия ориентирована на китайский экзамен по русскому языку TEM-8. Цель проекта — строить индивидуальный профиль учащегося на основе реальных ответов, находить слабые темы и типы заданий, а затем предлагать персонализированные упражнения с помощью банка заданий, RAG-базы знаний и генерации AI.

Проект не включает кабинет преподавателя. Основной пользовательский сценарий рассчитан на студента: выполнение заданий, автоматическая проверка, разбор ошибок, вопросы к AI, повторение и изучение слов.

### Возможности

- Регистрация и вход студентов
- Изоляция данных разных пользователей
- Генерация тренировочных вариантов по TEM-8
- Поддержка грамматики, литературы, страноведения и чтения
- Группировка заданий по чтению по одному тексту
- Автоматическая проверка ответов
- Запись ошибок в личный список
- Подробные объяснения ошибок на китайском языке через DeepSeek API
- Диалоговое окно для уточняющих вопросов
- Профиль уровня и статистика владения типами заданий
- Словарные карточки и личный список слов для повторения
- Цепочка генерации AI-заданий с последующей ручной проверкой
- RAG-поиск по базе знаний для генерации и проверки заданий
- Скрипты для обработки PDF, OCR и контроля качества данных

### Архитектура

```text
apps/student_web/static/      веб-интерфейс студента
scripts/serve_student_app.py  запуск локального или серверного приложения
scripts/                     обработка данных, импорт, OCR, контроль качества
database/                    локальная SQLite-база
docs/                        продуктовые документы и рабочий контекст
prompts/                     промпты для объяснений и генерации заданий
data/                        исходные и обработанные материалы, не коммитятся
```

### Данные и приватность

В репозиторий не добавляются:

- `.env`
- SQLite-базы данных
- PDF с экзаменационными материалами
- сканированные книги
- OCR-файлы
- аудиоматериалы
- данные, которые могут содержать авторские материалы или личную информацию студентов

Для запуска проекта необходимо подготовить локальную базу данных и собственные материалы.

### Настройка

Скопируйте `.env.example` в `.env` и заполните параметры DeepSeek:

```env
DEEPSEEK_API_KEY=your_deepseek_api_key_here
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-v4-flash
DEEPSEEK_THINKING=disabled
DEEPSEEK_REASONING_EFFORT=high
```

### Запуск

Локально:

```powershell
python scripts\serve_student_app.py --host 127.0.0.1 --port 8765
```

На сервере или в локальной сети:

```powershell
python scripts\serve_student_app.py --host 0.0.0.0 --port 8765
```

Откройте в браузере:

```text
http://127.0.0.1:8765/
```

При обновлении серверной версии сохраните:

```text
C:\AIeyu\.env
C:\AIeyu\database\russian_ai_tutor.sqlite
```

Эти файлы содержат API-настройки, аккаунты студентов и историю обучения.

### Статус проекта

AIeyu находится на стадии MVP и внутреннего тестирования. Основные задачи текущего этапа:

- проверить полезность AI-разбора ошибок
- проверить модель профиля учащегося
- улучшить качество банка заданий
- построить контролируемую цепочку AI-генерации и ручной проверки
- подготовить архитектуру для будущих экзаменов и уровней

---

## English

AIeyu is a student-facing AI adaptive study assistant for Russian language exams. The first MVP focuses on the Chinese Russian major TEM-8 exam. Its goal is to build a learner profile from real answer behavior, detect weak question types and knowledge areas, and provide personalized, non-repetitive practice through a question bank, RAG knowledge base, and AI-assisted question generation.

There is no teacher dashboard in the current product scope. The core experience is built for students: practice, grading, error analysis, follow-up questions, review, and vocabulary training.

### Features

- Student registration, login, and session isolation
- TEM-8 Russian question bank practice
- Grammar, literature, culture, and reading questions
- Reading questions grouped by passage
- Automatic grading
- Personal wrong-answer notebook
- Chinese error explanations powered by DeepSeek API
- AI follow-up chat for further questions
- Learner profile and mastery statistics by question type
- Vocabulary check-in and personal review pool
- AI-generated question drafts with human review workflow
- RAG retrieval for knowledge-grounded question generation
- PDF, OCR, import, and quality-audit scripts

### Architecture

```text
apps/student_web/static/      student web frontend
scripts/serve_student_app.py  local/server app entry point
scripts/                     extraction, import, OCR, audit, and cleanup scripts
database/                    local SQLite database directory
docs/                        product docs and development context
prompts/                     AI explanation and generation prompts
data/                        source and processed materials, ignored by git
```

The current stack is intentionally lightweight: a Python backend, a static web frontend, and SQLite for local/server pilot testing.

### Data And Privacy

The repository intentionally excludes:

- `.env`
- SQLite databases
- past-exam PDFs
- scanned books
- OCR intermediate files
- listening audio
- any material that may contain copyrighted content or student data

To run the project, prepare your own local database and source materials.

### Configuration

Copy `.env.example` to `.env` and fill in your DeepSeek configuration:

```env
DEEPSEEK_API_KEY=your_deepseek_api_key_here
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-v4-flash
DEEPSEEK_THINKING=disabled
DEEPSEEK_REASONING_EFFORT=high
```

### Run

Local:

```powershell
python scripts\serve_student_app.py --host 127.0.0.1 --port 8765
```

LAN or server:

```powershell
python scripts\serve_student_app.py --host 0.0.0.0 --port 8765
```

Open:

```text
http://127.0.0.1:8765/
```

When updating a server deployment, keep:

```text
C:\AIeyu\.env
C:\AIeyu\database\russian_ai_tutor.sqlite
```

These files store API settings, student accounts, and learning records.

### Vocabulary Quality Fixes

Run the deterministic vocabulary cleanup script when needed:

```powershell
python scripts\apply_vocabulary_quality_fixes.py
```

The script backs up the database before applying fixes and exports a review report for suspicious remaining entries.

### Project Status

AIeyu is currently an MVP for private and classroom testing. The near-term focus is to validate:

- whether students find AI explanations useful
- whether learner profiles guide better practice
- whether the question bank and generated questions remain high quality
- whether the human review workflow can keep AI-generated content reliable

Planned extensions include more Russian exam levels, listening practice, news-based listening, a stronger vocabulary system, a broader RAG knowledge base, and production deployment.

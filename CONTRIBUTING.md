# 🤝 Contributing to EduCloud Portal

Thank you for your interest in contributing to the **Cloud-Based Student Assignment Submission & Feedback Portal**! We welcome contributions to enhance cloud architecture, scalability, UI/UX, testing, and security.

---

## 🛠️ Development Setup

### 1. Clone & Set Up Environment
```bash
git clone https://github.com/rohitsingh83/Cloud-Assignment-Submission-Portal.git
cd Cloud-Assignment-Submission-Portal

# Create and activate virtual environment
python -m venv venv

# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
cp .env.example .env
```
Default settings run with local SQLite and local storage drivers—zero external cloud accounts required for development!

### 3. Seed Demo Data & Launch
```bash
python seed_full_demo.py
python main.py
```
Visit `http://localhost:8000` to interact with the application.

---

## 🧪 Testing Guidelines

Before opening a pull request, ensure all tests pass:
```bash
pytest -v
```
To run the automated 12-step end-to-end cloud lifecycle simulation:
```bash
python demo_walkthrough.py
```

---

## 🌿 Branching Strategy & Pull Requests

1. Fork the repository and create your branch from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```
2. Commit your changes following conventional commits (`feat:`, `fix:`, `docs:`, `test:`, `refactor:`).
3. Push to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```
4. Open a Pull Request against `main` with a clear description of changes.

---

## 📜 Code of Conduct
Please be respectful, collaborative, and constructive in all issue discussions and PR reviews.

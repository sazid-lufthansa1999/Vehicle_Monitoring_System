---
description: How to push the project to GitHub
---

# GitHub Push Workflow

Follow these steps to safely push your code to GitHub.

### 1. Initialize Git (One-time setup)
This creates a hidden `.git` folder in your project, turning it into a repository.
```bash
git init
```

### 2. Configure .gitignore (CRITICAL)
Before staging files, ensure `.gitignore` exists. This prevents uploading sensitive data (like `.env` or Firebase keys) and heavy files (like `.mp4` videos or AI models).
**Required entries:**
- `.env`
- `node_modules/`
- `static/uploads/`
- `*.mp4`
- `*.pt` (AI weights)

### 3. Link to GitHub
Replace `YOUR_REPO_URL` with your actual GitHub repository URL.
```bash
git remote add origin https://github.com/sazid-lufthansa1999/Vehicle_Monitoring_System.git
```

### 4. Stage and Commit
Staging prepares files, and committing saves a "snapshot" of your work locally.
```bash
git add .
git commit -m "Integrated MongoDB, Firebase Auth, and RBAC"
```

### 5. Push to GitHub
Upload your local snapshots to the server.
```bash
git branch -M main
git push -u origin main
```

> [!TIP]
> If `git` is not recognized, use the full path: `& "C:\Program Files\Git\cmd\git.exe" ...` in PowerShell.

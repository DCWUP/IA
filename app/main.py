import os, re, statistics, json, threading, time, glob, subprocess
from datetime import datetime, timezone, timedelta
from typing import Optional, List
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import pyodbc

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

def get_db():
    return pyodbc.connect(
        f"DRIVER={{SQL Server}};SERVER={os.environ['DB_SERVER']};DATABASE={os.environ['DB_NAME']};UID={os.environ['DB_USER']};PWD={os.environ['DB_PASSWORD']};TrustServerCertificate=yes"
    )

# ---- Models ----
class NovelCreate(BaseModel): Title: str = "未命名小说"; Outline: str = ""
class NovelUpdate(BaseModel): Title: Optional[str] = None; Outline: Optional[str] = None
class ChapterCreate(BaseModel): title: str = "未命名"; content: str = ""
class ChapterUpdate(BaseModel): title: Optional[str] = None; content: Optional[str] = None
class CharCreate(BaseModel): name: str; traits: List[str] = []; desc: str = ""
class CharUpdate(BaseModel): name: Optional[str] = None; traits: Optional[List[str]] = None; desc: Optional[str] = None
class VersionCreate(BaseModel): Content: str = ""; Label: str = ""; Title: str = ""
class SyncBody(BaseModel): Outline: str = ""; chapters: list = []; characters: list = []
class RuleCreate(BaseModel): content: str; category: str = ""
class RuleUpdate(BaseModel): content: Optional[str] = None; category: Optional[str] = None
class AnalyzeBody(BaseModel): content: str

# ---- Health ----
@app.head("/api/novels")
@app.get("/api/novels/health")
def health():
    return {"status": "ok"}

# ---- Novel API ----
@app.get("/api/novels")
def list_novels():
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT Id, Title, Outline, CreatedAt, UpdatedAt FROM Novels ORDER BY UpdatedAt DESC")
        return [dict(zip([d[0] for d in cur.description], row)) for row in cur.fetchall()]

@app.post("/api/novels")
def create_novel(body: NovelCreate):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("INSERT INTO Novels (Title, Outline) OUTPUT INSERTED.Id VALUES (?, ?)", body.Title, body.Outline)
        row = cur.fetchone()
        conn.commit()
        return {"id": row[0]}

@app.get("/api/novels/{novel_id}")
def get_novel(novel_id: int):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT Id, Title, Outline, CreatedAt, UpdatedAt FROM Novels WHERE Id=?", novel_id)
        novel = cur.fetchone()
        if not novel:
            raise HTTPException(404, "not found")
        cols = [d[0] for d in cur.description]
        result = dict(zip(cols, novel))
        cur.execute("SELECT Id, Title, Content, SortOrder, CreatedAt FROM Chapters WHERE NovelId=? ORDER BY SortOrder", novel_id)
        result["chapters"] = [dict(zip([d[0] for d in cur.description], r)) for r in cur.fetchall()]
        cur.execute("SELECT Id, Name, Traits, Description, CreatedAt FROM Characters WHERE NovelId=? ORDER BY Id", novel_id)
        result["characters"] = [dict(zip([d[0] for d in cur.description], r)) for r in cur.fetchall()]
        cur.execute("SELECT Id, SortOrder, Category, Content, CreatedAt FROM Rules WHERE NovelId=? ORDER BY SortOrder", novel_id)
        result["rules"] = [dict(zip([d[0] for d in cur.description], r)) for r in cur.fetchall()]
        return result

@app.put("/api/novels/{novel_id}")
def update_novel(novel_id: int, body: NovelUpdate):
    with get_db() as conn:
        cur = conn.cursor()
        if body.Title is not None:
            cur.execute("UPDATE Novels SET Title=?, UpdatedAt=GETDATE() WHERE Id=?", body.Title, novel_id)
        if body.Outline is not None:
            cur.execute("UPDATE Novels SET Outline=?, UpdatedAt=GETDATE() WHERE Id=?", body.Outline, novel_id)
        conn.commit()
        return {"success": True}

@app.delete("/api/novels/{novel_id}")
def delete_novel(novel_id: int):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM Novels WHERE Id=?", novel_id)
        conn.commit()
        return {"success": True}

# ---- Chapter API ----
@app.post("/api/novels/{novel_id}/chapters")
def add_chapter(novel_id: int, body: ChapterCreate):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT ISNULL(MAX(SortOrder), -1) FROM Chapters WHERE NovelId=?", novel_id)
        next_sort = cur.fetchone()[0] + 1
        cur.execute("INSERT INTO Chapters (NovelId, Title, Content, SortOrder) VALUES (?, ?, ?, ?)",
                    novel_id, body.title, body.content, next_sort)
        conn.commit()
        return {"success": True, "sortOrder": next_sort}

@app.put("/api/novels/{novel_id}/chapters/{index}")
def update_chapter(novel_id: int, index: int, body: ChapterUpdate):
    with get_db() as conn:
        cur = conn.cursor()
        if body.title is not None:
            cur.execute("UPDATE Chapters SET Title=?, UpdatedAt=GETDATE() WHERE NovelId=? AND SortOrder=?", body.title, novel_id, index)
        if body.content is not None:
            cur.execute("UPDATE Chapters SET Content=?, UpdatedAt=GETDATE() WHERE NovelId=? AND SortOrder=?", body.content, novel_id, index)
        conn.commit()
        return {"success": True}

@app.delete("/api/novels/{novel_id}/chapters/{index}")
def delete_chapter(novel_id: int, index: int):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM Chapters WHERE NovelId=? AND SortOrder=?", novel_id, index)
        cur.execute("UPDATE Chapters SET SortOrder=SortOrder-1 WHERE NovelId=? AND SortOrder>?", novel_id, index)
        conn.commit()
        return {"success": True}

# ---- Character API ----
@app.post("/api/novels/{novel_id}/characters")
def add_character(novel_id: int, body: CharCreate):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("INSERT INTO Characters (NovelId, Name, Traits, Description) VALUES (?, ?, ?, ?)",
                    novel_id, body.name, ", ".join(body.traits), body.desc)
        conn.commit()
        return {"success": True}

@app.put("/api/novels/{novel_id}/characters/{index}")
def update_character(novel_id: int, index: int, body: CharUpdate):
    with get_db() as conn:
        cur = conn.cursor()
        if body.name is not None:
            cur.execute("UPDATE Characters SET Name=?, UpdatedAt=GETDATE() WHERE NovelId=? AND Id=?", body.name, novel_id, index)
        if body.traits is not None:
            cur.execute("UPDATE Characters SET Traits=?, UpdatedAt=GETDATE() WHERE NovelId=? AND Id=?", ", ".join(body.traits), novel_id, index)
        if body.desc is not None:
            cur.execute("UPDATE Characters SET Description=?, UpdatedAt=GETDATE() WHERE NovelId=? AND Id=?", body.desc, novel_id, index)
        conn.commit()
        return {"success": True}

@app.delete("/api/novels/{novel_id}/characters/{char_id}")
def delete_character(novel_id: int, char_id: int):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM Characters WHERE NovelId=? AND Id=?", novel_id, char_id)
        conn.commit()
        return {"success": True}

# ---- Sync API ----
@app.post("/api/novels/{novel_id}/sync")
def sync_novel(novel_id: int, body: SyncBody):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("UPDATE Novels SET Outline=?, UpdatedAt=GETDATE() WHERE Id=?", body.Outline, novel_id)
        cur.execute("DELETE FROM Chapters WHERE NovelId=?", novel_id)
        for i, ch in enumerate(body.chapters):
            cur.execute("INSERT INTO Chapters (NovelId, Title, Content, SortOrder) VALUES (?, ?, ?, ?)",
                        novel_id, ch.get("title", ""), ch.get("content", ""), i)
        cur.execute("DELETE FROM Characters WHERE NovelId=?", novel_id)
        for ch in body.characters:
            cur.execute("INSERT INTO Characters (NovelId, Name, Traits, Description) VALUES (?, ?, ?, ?)",
                        novel_id, ch.get("name", ""), ", ".join(ch.get("traits", [])), ch.get("desc", ""))
        conn.commit()
        return {"success": True}

# ---- Version API (chapter-level) ----
@app.get("/api/novels/{novel_id}/chapters/{index}/versions")
def list_versions(novel_id: int, index: int):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT Id, VersionNumber, Label, TitleSnapshot, CreatedAt FROM ChapterVersions WHERE NovelId=? AND ChapterIndex=? ORDER BY VersionNumber DESC",
                    novel_id, index)
        return [dict(zip([d[0] for d in cur.description], r)) for r in cur.fetchall()]

@app.post("/api/novels/{novel_id}/chapters/{index}/versions")
def create_version(novel_id: int, index: int, body: VersionCreate):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT ISNULL(MAX(VersionNumber), 0) FROM ChapterVersions WHERE NovelId=? AND ChapterIndex=?", novel_id, index)
        next_ver = cur.fetchone()[0] + 1
        cur.execute("INSERT INTO ChapterVersions (NovelId, ChapterIndex, VersionNumber, Content, Label, TitleSnapshot) VALUES (?, ?, ?, ?, ?, ?)",
                    novel_id, index, next_ver, body.Content, body.Label, body.Title)
        conn.commit()
        return {"versionNumber": next_ver, "label": body.Label, "createdAt": datetime.now(timezone.utc).isoformat()}

@app.get("/api/novels/{novel_id}/chapters/{index}/versions/{vid}")
def get_version(novel_id: int, index: int, vid: int):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT Id, VersionNumber, Content, Label, TitleSnapshot, CreatedAt FROM ChapterVersions WHERE NovelId=? AND ChapterIndex=? AND Id=?",
                    novel_id, index, vid)
        row = cur.fetchone()
        if not row:
            raise HTTPException(404, "not found")
        return dict(zip([d[0] for d in cur.description], row))

@app.put("/api/novels/{novel_id}/chapters/{index}/versions/{vid}/restore")
def restore_version(novel_id: int, index: int, vid: int):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT Content, TitleSnapshot FROM ChapterVersions WHERE NovelId=? AND ChapterIndex=? AND Id=?", novel_id, index, vid)
        row = cur.fetchone()
        if not row:
            raise HTTPException(404, "not found")
        content, title = row
        cur.execute("UPDATE Chapters SET Content=?, Title=?, UpdatedAt=GETDATE() WHERE NovelId=? AND SortOrder=?", content, title, novel_id, index)
        conn.commit()
        return {"success": True}

# ---- Rules API ----
@app.get("/api/novels/{novel_id}/rules")
def list_rules(novel_id: int):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT Id, SortOrder, Category, Content, CreatedAt FROM Rules WHERE NovelId=? ORDER BY SortOrder", novel_id)
        return [dict(zip([d[0] for d in cur.description], r)) for r in cur.fetchall()]

@app.post("/api/novels/{novel_id}/rules")
def add_rule(novel_id: int, body: RuleCreate):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT ISNULL(MAX(SortOrder), -1) FROM Rules WHERE NovelId=?", novel_id)
        next_sort = cur.fetchone()[0] + 1
        cur.execute("INSERT INTO Rules (NovelId, SortOrder, Category, Content) VALUES (?, ?, ?, ?)",
                    novel_id, next_sort, body.category, body.content)
        conn.commit()
        return {"success": True}

@app.put("/api/novels/{novel_id}/rules/{rule_id}")
def update_rule(novel_id: int, rule_id: int, body: RuleUpdate):
    with get_db() as conn:
        cur = conn.cursor()
        if body.content is not None:
            cur.execute("UPDATE Rules SET Content=?, UpdatedAt=GETDATE() WHERE NovelId=? AND Id=?", body.content, novel_id, rule_id)
        if body.category is not None:
            cur.execute("UPDATE Rules SET Category=?, UpdatedAt=GETDATE() WHERE NovelId=? AND Id=?", body.category, novel_id, rule_id)
        conn.commit()
        return {"success": True}

@app.delete("/api/novels/{novel_id}/rules/{rule_id}")
def delete_rule(novel_id: int, rule_id: int):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM Rules WHERE NovelId=? AND Id=?", novel_id, rule_id)
        conn.commit()
        return {"success": True}

# ---- AIGC Analysis ----
AI_PATTERNS = [
    "首先", "其次", "总的来说", "综上所述", "值得注意的是", "需要指出的是",
    "不可否认", "毫无疑问", "从某种意义上说", "从这个角度来看",
    "我们可以看出", "我们可以看到", "让我们来", "让我们考虑",
    "具体来说", "换句话说", "更准确地说", "更具体地说",
    "一方面", "另一方面", "第一", "第二", "第三",
    "总而言之", "因此", "所以", "然而", "但是", "不过",
    "这是一个", "这是一种", "这充分体现了", "这反映了",
    "具有重要的意义", "重要作用", "不可或缺",
]

def calc_aigc_rate(content: str) -> dict:
    if not content or not content.strip():
        return {"rate": 0, "detail": {"chars": 0, "unique_ratio": 0, "ai_pattern_score": 0, "sent_len_uniformity": 0}}

    chars = len(content)
    content_clean = re.sub(r'\s+', '', content)

    # 1. Unique character ratio
    unique_ratio = len(set(content_clean)) / max(len(content_clean), 1)

    # 2. AI pattern detection
    pattern_count = 0
    for p in AI_PATTERNS:
        pattern_count += len(re.findall(re.escape(p), content))
    pattern_density = pattern_count / max(chars, 1) * 1000
    ai_pattern_score = min(pattern_density / 2, 1.0)

    # 3. Sentence length uniformity
    sentences = re.split(r'[。！？\n]', content)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 5]
    if len(sentences) >= 3:
        sent_lens = [len(s) for s in sentences]
        mean_len = statistics.mean(sent_lens)
        cv = statistics.stdev(sent_lens) / mean_len if mean_len > 0 else 0
        sent_len_uniformity = max(0, 1 - cv)
    else:
        sent_len_uniformity = 0.5

    # 4. Bigram repetition
    bigrams = [content_clean[i:i+2] for i in range(len(content_clean)-1)]
    bigram_unique = len(set(bigrams)) / max(len(bigrams), 1)

    # Combined score
    score = (
        0.25 * (1 - unique_ratio) +
        0.30 * ai_pattern_score +
        0.20 * sent_len_uniformity +
        0.25 * (1 - bigram_unique)
    )
    score = min(max(round(score * 100), 0), 100)

    return {
        "rate": score,
        "detail": {
            "chars": chars,
            "unique_ratio": round(unique_ratio, 4),
            "ai_pattern_score": round(ai_pattern_score, 4),
            "sent_len_uniformity": round(sent_len_uniformity, 4),
            "bigram_diversity": round(bigram_unique, 4),
        }
    }

@app.post("/api/aigc/analyze")
def analyze_aigc(body: AnalyzeBody):
    return calc_aigc_rate(body.content)

# ============================================================
# Backup API
# ============================================================
BACKUP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'backups')
BACKUP_CONFIG_PATH = os.path.join(BACKUP_DIR, 'config.json')
os.makedirs(BACKUP_DIR, exist_ok=True)

def load_backup_config():
    try:
        with open(BACKUP_CONFIG_PATH, 'r') as f:
            return json.load(f)
    except:
        return {"enabled": False, "frequency": "daily", "time": "03:00", "lastBackup": None}

def save_backup_config(cfg):
    with open(BACKUP_CONFIG_PATH, 'w') as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)

def _docker_backup(filename):
    """Run backup via docker exec + docker cp to work around bind mount issues."""
    now = datetime.now()
    tmp = f"/tmp/{filename}"
    subprocess.run(
        ["docker", "exec", "sqlserver-demo", "/opt/mssql-tools18/bin/sqlcmd",
         "-C", "-S", "localhost", "-U", "sa", "-P", os.environ.get("DB_PASSWORD", ""),
         "-Q", f"BACKUP DATABASE DemoDB TO DISK = N'{tmp}' WITH INIT"],
        check=True, capture_output=True, timeout=120, text=True)
    subprocess.run(
        ["docker", "cp", f"sqlserver-demo:{tmp}", os.path.join(BACKUP_DIR, filename)],
        check=True, capture_output=True, timeout=120)
    subprocess.run(
        ["docker", "exec", "sqlserver-demo", "rm", tmp],
        check=True, capture_output=True, timeout=30)

@app.post("/api/backup/run")
def run_backup():
    now = datetime.now()
    filename = f"novel_backup_{now.strftime('%Y%m%d_%H%M%S')}.bak"
    try:
        _docker_backup(filename)
        cfg = load_backup_config()
        cfg["lastBackup"] = now.isoformat()
        save_backup_config(cfg)
        return {"success": True, "filename": filename, "createdAt": now.isoformat()}
    except Exception as e:
        raise HTTPException(500, f"备份失败: {str(e)}")

@app.get("/api/backup/list")
def list_backups():
    files = []
    for f in sorted(glob.glob(os.path.join(BACKUP_DIR, "*.bak")), key=os.path.getmtime, reverse=True):
        fname = os.path.basename(f)
        files.append({
            "filename": fname,
            "size": os.path.getsize(f),
            "createdAt": datetime.fromtimestamp(os.path.getmtime(f), tz=timezone.utc).isoformat()
        })
    return files

@app.get("/api/backup/download/{filename}")
def download_backup(filename: str):
    filepath = os.path.join(BACKUP_DIR, filename)
    if not os.path.exists(filepath):
        raise HTTPException(404, "备份文件不存在")
    return FileResponse(filepath, filename=filename, media_type="application/octet-stream")

@app.delete("/api/backup/{filename}")
def delete_backup(filename: str):
    filepath = os.path.join(BACKUP_DIR, filename)
    if os.path.exists(filepath):
        os.remove(filepath)
    return {"success": True}

class BackupConfigBody(BaseModel):
    enabled: bool
    frequency: str = "daily"
    time: str = "03:00"

@app.get("/api/backup/config")
def get_backup_config():
    return load_backup_config()

@app.post("/api/backup/config")
def set_backup_config(body: BackupConfigBody):
    cfg = load_backup_config()
    cfg["enabled"] = body.enabled
    cfg["frequency"] = body.frequency
    cfg["time"] = body.time
    save_backup_config(cfg)
    return {"success": True}

# Background backup scheduler
def backup_scheduler():
    while True:
        try:
            cfg = load_backup_config()
            if cfg.get("enabled"):
                now = datetime.now()
                parts = cfg.get("time", "03:00").split(":")
                hour, minute = int(parts[0]), int(parts[1]) if len(parts) > 1 else 0
                last = cfg.get("lastBackup")
                should_run = False
                if not last:
                    should_run = True
                else:
                    last_dt = datetime.fromisoformat(last)
                    freq = cfg.get("frequency", "daily")
                    if freq == "daily":
                        if (now - last_dt).total_seconds() >= 86400 and now.hour == hour and now.minute == minute:
                            should_run = True
                    elif freq == "weekly":
                        if (now - last_dt).total_seconds() >= 604800 and now.hour == hour and now.minute == minute:
                            should_run = True
                if should_run:
                    try:
                        filename = f"novel_backup_{now.strftime('%Y%m%d_%H%M%S')}.bak"
                        _docker_backup(filename)
                        cfg["lastBackup"] = now.isoformat()
                        save_backup_config(cfg)
                        # Keep only last 10 backups
                        all_backups = sorted(glob.glob(os.path.join(BACKUP_DIR, "novel_backup_*.bak")), key=os.path.getmtime)
                        for old in all_backups[:-10]:
                            os.remove(old)
                    except:
                        pass
        except:
            pass
        time.sleep(60)

# Start scheduler on app startup
@app.on_event("startup")
def start_scheduler():
    t = threading.Thread(target=backup_scheduler, daemon=True)
    t.start()


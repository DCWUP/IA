require('dotenv').config();
const express = require('express');
const sql = require('mssql');
const path = require('path');

const app = express();
app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

const dbConfig = {
    server: process.env.DB_SERVER,
    database: process.env.DB_NAME,
    user: process.env.DB_USER,
    password: process.env.DB_PASSWORD,
    options: {
        encrypt: false,
        trustServerCertificate: true
    }
};

async function getConnection() {
    return await sql.connect(dbConfig);
}

app.get('/api/employees', async (req, res) => {
    try {
        const pool = await getConnection();
        const result = await pool.request().query('SELECT * FROM Employees');
        res.json(result.recordset);
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

app.get('/api/employees/:id', async (req, res) => {
    try {
        const pool = await getConnection();
        const result = await pool.request()
            .input('id', sql.Int, req.params.id)
            .query('SELECT * FROM Employees WHERE Id = @id');
        res.json(result.recordset[0] || null);
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

app.post('/api/employees', async (req, res) => {
    try {
        const { Name, Department, Salary, HireDate } = req.body;
        const pool = await getConnection();
        const result = await pool.request()
            .input('Name', sql.NVarChar, Name)
            .input('Department', sql.NVarChar, Department)
            .input('Salary', sql.Decimal, Salary)
            .input('HireDate', sql.Date, HireDate)
            .query('INSERT INTO Employees (Name, Department, Salary, HireDate) VALUES (@Name, @Department, @Salary, @HireDate); SELECT SCOPE_IDENTITY() AS Id');
        res.json({ id: result.recordset[0].Id, ...req.body });
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

app.put('/api/employees/:id', async (req, res) => {
    try {
        const { Name, Department, Salary, HireDate } = req.body;
        const pool = await getConnection();
        await pool.request()
            .input('id', sql.Int, req.params.id)
            .input('Name', sql.NVarChar, Name)
            .input('Department', sql.NVarChar, Department)
            .input('Salary', sql.Decimal, Salary)
            .input('HireDate', sql.Date, HireDate)
            .query('UPDATE Employees SET Name=@Name, Department=@Department, Salary=@Salary, HireDate=@HireDate WHERE Id=@id');
        res.json({ id: req.params.id, ...req.body });
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

app.delete('/api/employees/:id', async (req, res) => {
    try {
        const pool = await getConnection();
        await pool.request()
            .input('id', sql.Int, req.params.id)
            .query('DELETE FROM Employees WHERE Id=@id');
        res.json({ success: true });
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

// ============================================================
// Novel Platform API
// ============================================================

// GET /api/novels - list all novels
app.get('/api/novels', async (req, res) => {
    try {
        const pool = await getConnection();
        const result = await pool.request().query('SELECT * FROM Novels ORDER BY UpdatedAt DESC');
        res.json(result.recordset);
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

// POST /api/novels - create a new novel
app.post('/api/novels', async (req, res) => {
    try {
        const { Title } = req.body;
        const pool = await getConnection();
        const result = await pool.request()
            .input('Title', sql.NVarChar, Title || '未命名小说')
            .query('INSERT INTO Novels (Title) VALUES (@Title); SELECT SCOPE_IDENTITY() AS Id');
        res.json({ id: result.recordset[0].Id });
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

// GET /api/novels/:id - get full novel with chapters and characters
app.get('/api/novels/:id', async (req, res) => {
    try {
        const pool = await getConnection();
        const novel = await pool.request()
            .input('id', sql.Int, req.params.id)
            .query('SELECT * FROM Novels WHERE Id = @id');
        if (!novel.recordset.length) return res.status(404).json({ error: 'not found' });
        const chapters = await pool.request()
            .input('id', sql.Int, req.params.id)
            .query('SELECT * FROM Chapters WHERE NovelId = @id ORDER BY SortOrder');
        const characters = await pool.request()
            .input('id', sql.Int, req.params.id)
            .query('SELECT * FROM Characters WHERE NovelId = @id ORDER BY Id');
        res.json({ ...novel.recordset[0], chapters: chapters.recordset, characters: characters.recordset });
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

// PUT /api/novels/:id - update novel title/outline
app.put('/api/novels/:id', async (req, res) => {
    try {
        const { Title, Outline } = req.body;
        const pool = await getConnection();
        await pool.request()
            .input('id', sql.Int, req.params.id)
            .input('Title', sql.NVarChar, Title)
            .input('Outline', sql.NVarChar, Outline || '')
            .query('UPDATE Novels SET Title=@Title, Outline=@Outline, UpdatedAt=GETDATE() WHERE Id=@id');
        res.json({ success: true });
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

// DELETE /api/novels/:id
app.delete('/api/novels/:id', async (req, res) => {
    try {
        const pool = await getConnection();
        await pool.request()
            .input('id', sql.Int, req.params.id)
            .query('DELETE FROM Novels WHERE Id=@id');
        res.json({ success: true });
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

// POST /api/novels/:id/sync - full sync: replaces chapters & characters
app.post('/api/novels/:id/sync', async (req, res) => {
    try {
        const { Outline, chapters, characters } = req.body;
        const novelId = req.params.id;
        const pool = await getConnection();

        // Update outline
        await pool.request()
            .input('id', sql.Int, novelId)
            .input('Outline', sql.NVarChar, Outline || '')
            .query('UPDATE Novels SET Outline=@Outline, UpdatedAt=GETDATE() WHERE Id=@id');

        // Replace chapters: delete all, re-insert
        await pool.request()
            .input('id', sql.Int, novelId)
            .query('DELETE FROM Chapters WHERE NovelId=@id');
        if (chapters && chapters.length) {
            for (let i = 0; i < chapters.length; i++) {
                await pool.request()
                    .input('NovelId', sql.Int, novelId)
                    .input('Title', sql.NVarChar, chapters[i].title || '未命名')
                    .input('Content', sql.NVarChar, chapters[i].content || '')
                    .input('SortOrder', sql.Int, i)
                    .query('INSERT INTO Chapters (NovelId, Title, Content, SortOrder) VALUES (@NovelId, @Title, @Content, @SortOrder)');
            }
        }

        // Replace characters: delete all, re-insert
        await pool.request()
            .input('id', sql.Int, novelId)
            .query('DELETE FROM Characters WHERE NovelId=@id');
        if (characters && characters.length) {
            for (const ch of characters) {
                await pool.request()
                    .input('NovelId', sql.Int, novelId)
                    .input('Name', sql.NVarChar, ch.name || '')
                    .input('Traits', sql.NVarChar, (ch.traits || []).join(', '))
                    .input('Description', sql.NVarChar, ch.desc || '')
                    .query('INSERT INTO Characters (NovelId, Name, Traits, Description) VALUES (@NovelId, @Name, @Traits, @Description)');
            }
        }

        res.json({ success: true });
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

// ============================================================
// Version API
// ============================================================

// POST /api/novels/:id/versions - create a version snapshot
app.post('/api/novels/:id/versions', async (req, res) => {
    try {
        const novelId = req.params.id;
        const { Label } = req.body;
        const pool = await getConnection();

        // Get current max version number
        const maxVer = await pool.request()
            .input('id', sql.Int, novelId)
            .query('SELECT ISNULL(MAX(VersionNumber), 0) AS MaxVer FROM Versions WHERE NovelId=@id');
        const nextVer = maxVer.recordset[0].MaxVer + 1;

        // Build snapshot
        const chapters = await pool.request()
            .input('id', sql.Int, novelId)
            .query('SELECT Title, Content, SortOrder FROM Chapters WHERE NovelId=@id ORDER BY SortOrder');
        const characters = await pool.request()
            .input('id', sql.Int, novelId)
            .query('SELECT Name, Traits, Description FROM Characters WHERE NovelId=@id ORDER BY Id');
        const novel = await pool.request()
            .input('id', sql.Int, novelId)
            .query('SELECT Outline FROM Novels WHERE Id=@id');

        const snapshot = JSON.stringify({
            outline: novel.recordset[0]?.Outline || '',
            chapters: chapters.recordset,
            characters: characters.recordset
        });

        await pool.request()
            .input('NovelId', sql.Int, novelId)
            .input('VersionNumber', sql.Int, nextVer)
            .input('Label', sql.NVarChar, Label || '')
            .input('Snapshot', sql.NVarChar, snapshot)
            .query('INSERT INTO Versions (NovelId, VersionNumber, Label, Snapshot) VALUES (@NovelId, @VersionNumber, @Label, @Snapshot)');

        res.json({ id: nextVer, versionNumber: nextVer, label: Label, createdAt: new Date().toISOString() });
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

// GET /api/novels/:id/versions - list all versions
app.get('/api/novels/:id/versions', async (req, res) => {
    try {
        const pool = await getConnection();
        const result = await pool.request()
            .input('id', sql.Int, req.params.id)
            .query('SELECT Id, VersionNumber, Label, CreatedAt FROM Versions WHERE NovelId=@id ORDER BY VersionNumber DESC');
        res.json(result.recordset);
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

// GET /api/novels/:id/versions/:vid - get full version snapshot
app.get('/api/novels/:id/versions/:vid', async (req, res) => {
    try {
        const pool = await getConnection();
        const result = await pool.request()
            .input('id', sql.Int, req.params.id)
            .input('vid', sql.Int, req.params.vid)
            .query('SELECT * FROM Versions WHERE NovelId=@id AND Id=@vid');
        if (!result.recordset.length) return res.status(404).json({ error: 'not found' });
        const ver = result.recordset[0];
        ver.Snapshot = JSON.parse(ver.Snapshot);
        res.json(ver);
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

// ============================================================
// Chapter Version API
// ============================================================

// POST /api/novels/:id/chapters/:index/versions - create chapter version
app.post('/api/novels/:id/chapters/:index/versions', async (req, res) => {
    try {
        const novelId = req.params.id;
        const chapterIndex = parseInt(req.params.index);
        const { Content, Label, Title } = req.body;
        const pool = await getConnection();

        const maxVer = await pool.request()
            .input('id', sql.Int, novelId)
            .input('idx', sql.Int, chapterIndex)
            .query('SELECT ISNULL(MAX(VersionNumber), 0) AS MaxVer FROM ChapterVersions WHERE NovelId=@id AND ChapterIndex=@idx');
        const nextVer = maxVer.recordset[0].MaxVer + 1;

        await pool.request()
            .input('NovelId', sql.Int, novelId)
            .input('ChapterIndex', sql.Int, chapterIndex)
            .input('VersionNumber', sql.Int, nextVer)
            .input('Content', sql.NVarChar, Content || '')
            .input('Label', sql.NVarChar, Label || '')
            .input('TitleSnapshot', sql.NVarChar, Title || '')
            .query('INSERT INTO ChapterVersions (NovelId, ChapterIndex, VersionNumber, Content, Label, TitleSnapshot) VALUES (@NovelId, @ChapterIndex, @VersionNumber, @Content, @Label, @TitleSnapshot)');

        res.json({ versionNumber: nextVer, label: Label, createdAt: new Date().toISOString() });
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

// GET /api/novels/:id/chapters/:index/versions - list chapter versions
app.get('/api/novels/:id/chapters/:index/versions', async (req, res) => {
    try {
        const pool = await getConnection();
        const result = await pool.request()
            .input('id', sql.Int, req.params.id)
            .input('idx', sql.Int, req.params.index)
            .query('SELECT Id, VersionNumber, Label, TitleSnapshot, CreatedAt FROM ChapterVersions WHERE NovelId=@id AND ChapterIndex=@idx ORDER BY VersionNumber DESC');
        res.json(result.recordset);
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

// GET /api/novels/:id/chapters/:index/versions/:vid - get chapter version content
app.get('/api/novels/:id/chapters/:index/versions/:vid', async (req, res) => {
    try {
        const pool = await getConnection();
        const result = await pool.request()
            .input('id', sql.Int, req.params.id)
            .input('idx', sql.Int, req.params.index)
            .input('vid', sql.Int, req.params.vid)
            .query('SELECT Id, VersionNumber, Content, Label, TitleSnapshot, CreatedAt FROM ChapterVersions WHERE NovelId=@id AND ChapterIndex=@idx AND Id=@vid');
        if (!result.recordset.length) return res.status(404).json({ error: 'not found' });
        res.json(result.recordset[0]);
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, '0.0.0.0', () => {
    console.log(`Server running at http://0.0.0.0:${PORT}`);
    console.log(`LAN access: http://<your-ip>:${PORT}`);
});

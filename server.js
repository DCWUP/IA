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

const PORT = process.env.PORT || 3000;
app.listen(PORT, '0.0.0.0', () => {
    console.log(`Server running at http://0.0.0.0:${PORT}`);
    console.log(`LAN access: http://<your-ip>:${PORT}`);
});

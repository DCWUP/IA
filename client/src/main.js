const API = '/api/employees';
let employees = [];

async function loadEmployees() {
    const res = await fetch(API);
    employees = await res.json();
    renderTable();
}

function renderTable() {
    if (employees.length === 0) {
        document.getElementById('tableContainer').innerHTML = '<p class="empty">暂无数据</p>';
        return;
    }
    const html = `
        <table>
            <thead>
                <tr>
                    <th>ID</th>
                    <th>姓名</th>
                    <th>部门</th>
                    <th>工资</th>
                    <th>入职日期</th>
                    <th>操作</th>
                </tr>
            </thead>
            <tbody>
                ${employees.map(e => `
                    <tr>
                        <td>${e.Id}</td>
                        <td>${e.Name}</td>
                        <td>${e.Department}</td>
                        <td>${e.Salary.toFixed(2)}</td>
                        <td>${new Date(e.HireDate).toLocaleDateString()}</td>
                        <td>
                            <button class="btn btn-primary" onclick="editEmployee(${e.Id})">编辑</button>
                            <button class="btn btn-danger" onclick="deleteEmployee(${e.Id})">删除</button>
                        </td>
                    </tr>
                `).join('')}
            </tbody>
        </table>
    `;
    document.getElementById('tableContainer').innerHTML = html;
}

function openModal(emp = null) {
    document.getElementById('modalTitle').textContent = emp ? '编辑员工' : '新增员工';
    document.getElementById('editId').value = emp ? emp.Id : '';
    document.getElementById('name').value = emp ? emp.Name : '';
    document.getElementById('department').value = emp ? emp.Department : '';
    document.getElementById('salary').value = emp ? emp.Salary : '';
    document.getElementById('hireDate').value = emp ? emp.HireDate.split('T')[0] : '';
    document.getElementById('modal').classList.add('active');
}

function closeModal() {
    document.getElementById('modal').classList.remove('active');
    document.getElementById('form').reset();
}

async function editEmployee(id) {
    const emp = employees.find(e => e.Id === id);
    openModal(emp);
}

async function handleSubmit(e) {
    e.preventDefault();
    const id = document.getElementById('editId').value;
    const data = {
        Name: document.getElementById('name').value,
        Department: document.getElementById('department').value,
        Salary: parseFloat(document.getElementById('salary').value),
        HireDate: document.getElementById('hireDate').value
    };
    
    if (id) {
        await fetch(`${API}/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
    } else {
        await fetch(API, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
    }
    closeModal();
    loadEmployees();
}

async function deleteEmployee(id) {
    if (confirm('确定删除该员工？')) {
        await fetch(`${API}/${id}`, { method: 'DELETE' });
        loadEmployees();
    }
}

loadEmployees();

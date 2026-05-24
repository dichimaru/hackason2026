package repository

import (
	"database/sql"

	"github.com/hackason2026/webapp-go/internal/domain"
)

type EmployeeRepo struct{ DB *sql.DB }

func (r EmployeeRepo) List() ([]domain.Employee, error) {
	rows, err := r.DB.Query(`SELECT id, name, email, department, active FROM employees ORDER BY id`)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	out := []domain.Employee{}
	for rows.Next() {
		var e domain.Employee
		if err := rows.Scan(&e.ID, &e.Name, &e.Email, &e.Department, &e.Active); err != nil {
			return nil, err
		}
		out = append(out, e)
	}
	return out, nil
}

func (r EmployeeRepo) ActiveIDs() ([]int, error) {
	rows, err := r.DB.Query(`SELECT id FROM employees WHERE active = 1`)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	ids := []int{}
	for rows.Next() {
		var id int
		if err := rows.Scan(&id); err != nil {
			return nil, err
		}
		ids = append(ids, id)
	}
	return ids, nil
}

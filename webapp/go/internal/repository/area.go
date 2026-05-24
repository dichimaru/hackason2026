package repository

import (
	"database/sql"

	"github.com/hackason2026/webapp-go/internal/domain"
)

type AreaRepo struct{ DB *sql.DB }

func (r AreaRepo) List() ([]domain.Area, error) {
	rows, err := r.DB.Query(`SELECT id, name, description FROM areas ORDER BY id`)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	out := []domain.Area{}
	for rows.Next() {
		var a domain.Area
		if err := rows.Scan(&a.ID, &a.Name, &a.Description); err != nil {
			return nil, err
		}
		out = append(out, a)
	}
	return out, nil
}

func (r AreaRepo) IDs() ([]int, error) {
	rows, err := r.DB.Query(`SELECT id FROM areas`)
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

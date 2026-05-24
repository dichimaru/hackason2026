package repository

import (
	"database/sql"
	"time"

	"github.com/hackason2026/webapp-go/internal/domain"
)

type DutyRepo struct{ DB *sql.DB }

func (r DutyRepo) List() ([]domain.Duty, error) {
	rows, err := r.DB.Query(`
		SELECT d.id, d.employee_id, e.name, d.area_id, a.name, d.scheduled_date, d.status
		FROM duties d
		JOIN employees e ON e.id = d.employee_id
		JOIN areas a     ON a.id = d.area_id
		ORDER BY d.scheduled_date, a.id`)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	out := []domain.Duty{}
	for rows.Next() {
		var d domain.Duty
		var date time.Time
		if err := rows.Scan(&d.ID, &d.EmployeeID, &d.EmployeeName, &d.AreaID, &d.AreaName, &date, &d.Status); err != nil {
			return nil, err
		}
		d.ScheduledDate = date.Format("2006-01-02")
		out = append(out, d)
	}
	return out, nil
}

// InsertBatch は1トランザクションで複数の duty を挿入する。
func (r DutyRepo) InsertBatch(items []domain.Duty) (int, error) {
	tx, err := r.DB.Begin()
	if err != nil {
		return 0, err
	}
	defer tx.Rollback()
	count := 0
	for _, d := range items {
		if _, err := tx.Exec(
			`INSERT INTO duties (employee_id, area_id, scheduled_date, status) VALUES (?, ?, ?, 'pending')`,
			d.EmployeeID, d.AreaID, d.ScheduledDate,
		); err != nil {
			return 0, err
		}
		count++
	}
	if err := tx.Commit(); err != nil {
		return 0, err
	}
	return count, nil
}

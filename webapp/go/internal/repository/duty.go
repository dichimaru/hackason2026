package repository

import (
	"gorm.io/gorm"

	"github.com/hackason2026/webapp-go/internal/domain"
)

type DutyRepo struct{ DB *gorm.DB }

// List は抽選結果一覧を、社員名・掃除場所名を埋めた API 応答の形で返す。
func (r DutyRepo) List() ([]domain.DutyView, error) {
	duties := []domain.Duty{}
	err := r.DB.
		Preload("Employee").
		Preload("Area").
		Order("scheduled_date").
		Order("task_id").
		Find(&duties).Error
	if err != nil {
		return nil, err
	}

	out := make([]domain.DutyView, 0, len(duties))
	for _, d := range duties {
		out = append(out, domain.DutyView{
			ID:            d.ID,
			EmployeeID:    d.PersonID,
			EmployeeName:  d.Employee.Name,
			AreaID:        d.TaskID,
			AreaName:      d.Area.Name,
			ScheduledDate: d.ScheduledDate.Format("2006-01-02"),
			Status:        d.Status,
		})
	}
	return out, nil
}

// InsertBatch は1トランザクションで複数の抽選結果を挿入する。
//
// Omit で関連を外しているのは、ゼロ値の Employee / Area を GORM が
// 新規レコードとして書き込もうとするのを防ぐため。
func (r DutyRepo) InsertBatch(items []domain.Duty) (int, error) {
	if len(items) == 0 {
		return 0, nil
	}
	err := r.DB.Transaction(func(tx *gorm.DB) error {
		return tx.Omit("Employee", "Area").Create(&items).Error
	})
	if err != nil {
		return 0, err
	}
	return len(items), nil
}

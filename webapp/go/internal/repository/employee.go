package repository

import (
	"gorm.io/gorm"

	"github.com/hackason2026/webapp-go/internal/domain"
)

type EmployeeRepo struct{ DB *gorm.DB }

func (r EmployeeRepo) List() ([]domain.Employee, error) {
	out := []domain.Employee{}
	if err := r.DB.Order("id").Find(&out).Error; err != nil {
		return nil, err
	}
	return out, nil
}

// ActiveIDs は当番割当の対象になる社員のIDだけを取り出す。
func (r EmployeeRepo) ActiveIDs() ([]uint, error) {
	ids := []uint{}
	err := r.DB.Model(&domain.Employee{}).Where("active = ?", true).Pluck("id", &ids).Error
	if err != nil {
		return nil, err
	}
	return ids, nil
}

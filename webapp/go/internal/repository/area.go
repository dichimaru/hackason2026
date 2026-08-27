package repository

import (
	"gorm.io/gorm"

	"github.com/hackason2026/webapp-go/internal/domain"
)

type AreaRepo struct{ DB *gorm.DB }

func (r AreaRepo) List() ([]domain.Area, error) {
	out := []domain.Area{}
	if err := r.DB.Order("id").Find(&out).Error; err != nil {
		return nil, err
	}
	return out, nil
}

func (r AreaRepo) IDs() ([]uint, error) {
	ids := []uint{}
	if err := r.DB.Model(&domain.Area{}).Order("id").Pluck("id", &ids).Error; err != nil {
		return nil, err
	}
	return ids, nil
}

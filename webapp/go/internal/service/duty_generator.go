package service

import (
	"errors"
	"math/rand"
	"time"

	"github.com/hackason2026/webapp-go/internal/domain"
	"github.com/hackason2026/webapp-go/internal/repository"
)

// DutyGenerator は翌週5営業日分の当番をシャッフル+ラウンドロビンで割り当てる。
// 公平性の強化やカレンダー連携はここを起点に拡張する。
type DutyGenerator struct {
	Employees repository.EmployeeRepo
	Areas     repository.AreaRepo
	Duties    repository.DutyRepo
}

func (g DutyGenerator) Generate() (int, error) {
	empIDs, err := g.Employees.ActiveIDs()
	if err != nil {
		return 0, err
	}
	areaIDs, err := g.Areas.IDs()
	if err != nil {
		return 0, err
	}
	if len(empIDs) == 0 || len(areaIDs) == 0 {
		return 0, errors.New("employees or areas is empty")
	}

	rnd := rand.New(rand.NewSource(time.Now().UnixNano()))
	rnd.Shuffle(len(empIDs), func(i, j int) { empIDs[i], empIDs[j] = empIDs[j], empIDs[i] })

	items := make([]domain.Duty, 0, 5*len(areaIDs))
	idx := 0
	for day := 7; day < 12; day++ {
		date := time.Now().AddDate(0, 0, day).Format("2006-01-02")
		for _, areaID := range areaIDs {
			items = append(items, domain.Duty{
				EmployeeID:    empIDs[idx%len(empIDs)],
				AreaID:        areaID,
				ScheduledDate: date,
			})
			idx++
		}
	}
	return g.Duties.InsertBatch(items)
}

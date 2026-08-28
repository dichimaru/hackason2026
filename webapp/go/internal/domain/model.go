package domain

import "time"

// Employee は person テーブルの1行。GORM のモデルと API 応答を兼ねる。
type Employee struct {
	ID         uint      `gorm:"primaryKey" json:"id"`
	Name       string    `json:"name"`
	Email      string    `json:"email"`
	Department string    `json:"department"`
	Active     bool      `json:"active"`
	CreatedAt  time.Time `json:"-"`
}

func (Employee) TableName() string { return "person" }

// Area は task テーブルを既存のエリアAPI向けに表す互換モデル。
type Area struct {
	ID          uint   `gorm:"primaryKey" json:"id"`
	Name        string `json:"name"`
	Office      string `json:"office"`
	Description string `json:"description"`
}

func (Area) TableName() string { return "task" }

// Duty は lottery_result テーブルの1行。Employee / Area は Preload で埋める。
type Duty struct {
	ID            uint      `gorm:"primaryKey"`
	PersonID      uint      `gorm:"not null" json:"-"`
	TaskID        uint      `gorm:"not null" json:"-"`
	ScheduledDate time.Time `gorm:"type:date;not null"`
	Status        string    `gorm:"not null;default:pending"`
	CreatedAt     time.Time

	Employee Employee `gorm:"foreignKey:PersonID"`
	Area     Area     `gorm:"foreignKey:TaskID"`
}

func (Duty) TableName() string { return "lottery_result" }

// DutyView は当番一覧の API 応答。社員名・エリア名を平坦に持つ。
type DutyView struct {
	ID            uint   `json:"id"`
	EmployeeID    uint   `json:"employee_id"`
	EmployeeName  string `json:"employee_name"`
	AreaID        uint   `json:"area_id"`
	AreaName      string `json:"area_name"`
	ScheduledDate string `json:"scheduled_date"`
	Status        string `json:"status"`
}

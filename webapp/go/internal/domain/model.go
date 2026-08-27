package domain

import "time"

// Employee は employees テーブルの1行。GORM のモデルと API 応答を兼ねる。
type Employee struct {
	ID         uint      `gorm:"primaryKey" json:"id"`
	Name       string    `json:"name"`
	Email      string    `json:"email"`
	Department string    `json:"department"`
	Active     bool      `json:"active"`
	CreatedAt  time.Time `json:"-"`
}

func (Employee) TableName() string { return "employees" }

// Area は areas テーブルの1行。
type Area struct {
	ID          uint   `gorm:"primaryKey" json:"id"`
	Name        string `json:"name"`
	Description string `json:"description"`
}

func (Area) TableName() string { return "areas" }

// Duty は duties テーブルの1行。Employee / Area は Preload で埋める。
type Duty struct {
	ID            uint      `gorm:"primaryKey"`
	EmployeeID    uint      `gorm:"not null"`
	AreaID        uint      `gorm:"not null"`
	ScheduledDate time.Time `gorm:"type:date;not null"`
	Status        string    `gorm:"not null;default:pending"`
	CreatedAt     time.Time

	Employee Employee `gorm:"foreignKey:EmployeeID"`
	Area     Area     `gorm:"foreignKey:AreaID"`
}

func (Duty) TableName() string { return "duties" }

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

package domain

type Employee struct {
	ID         int    `json:"id"`
	Name       string `json:"name"`
	Email      string `json:"email"`
	Department string `json:"department"`
	Active     bool   `json:"active"`
}

type Area struct {
	ID          int    `json:"id"`
	Name        string `json:"name"`
	Description string `json:"description"`
}

type Duty struct {
	ID            int    `json:"id"`
	EmployeeID    int    `json:"employee_id"`
	EmployeeName  string `json:"employee_name"`
	AreaID        int    `json:"area_id"`
	AreaName      string `json:"area_name"`
	ScheduledDate string `json:"scheduled_date"`
	Status        string `json:"status"`
}

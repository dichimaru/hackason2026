package handler

import (
	"net/http"

	"github.com/gin-gonic/gin"
	"gorm.io/gorm"

	"github.com/hackason2026/webapp-go/internal/repository"
	"github.com/hackason2026/webapp-go/internal/service"
)

type Handler struct {
	DB        *gorm.DB
	Employees repository.EmployeeRepo
	Areas     repository.AreaRepo
	Duties    repository.DutyRepo
	Generator service.DutyGenerator
}

func New(db *gorm.DB) *Handler {
	er := repository.EmployeeRepo{DB: db}
	ar := repository.AreaRepo{DB: db}
	dr := repository.DutyRepo{DB: db}
	return &Handler{
		DB:        db,
		Employees: er,
		Areas:     ar,
		Duties:    dr,
		Generator: service.DutyGenerator{Employees: er, Areas: ar, Duties: dr},
	}
}

func (h *Handler) Health(c *gin.Context) {
	conn, err := h.DB.DB()
	if err == nil {
		err = conn.Ping()
	}
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"status": "ng", "error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, gin.H{"status": "ok"})
}

func (h *Handler) ListEmployees(c *gin.Context) {
	out, err := h.Employees.List()
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, out)
}

func (h *Handler) ListAreas(c *gin.Context) {
	out, err := h.Areas.List()
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, out)
}

func (h *Handler) ListDuties(c *gin.Context) {
	out, err := h.Duties.List()
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, out)
}

func (h *Handler) GenerateDuties(c *gin.Context) {
	created, err := h.Generator.Generate()
	if err != nil {
		if err.Error() == "person or task is empty" {
			c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
			return
		}
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, gin.H{"created": created})
}
